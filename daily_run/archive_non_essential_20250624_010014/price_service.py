#!/usr/bin/env python3
"""
Consolidated price service for all ticker types
"""

import yfinance as yf
import pandas as pd
import requests
import time
from typing import Dict, List, Tuple, Optional, Any
from ratelimit import limits, sleep_and_retry
from base_service import BaseService
from config import Config
from exceptions import ServiceError, RateLimitError, DataNotFoundError
from apiratelimiter import APIRateLimiter

class YahooPriceService(BaseService):
    """Yahoo Finance price service"""
    
    def __init__(self):
        super().__init__('yahoo')
    
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get price data from Yahoo Finance"""
        if not self.validate_ticker(ticker):
            raise ServiceError('yahoo', f"Invalid ticker: {ticker}", ticker)
        
        try:
            data = yf.download(ticker, period="1d", progress=False)
            
            if data.empty:
                raise DataNotFoundError('yahoo', ticker)
            
            row = data.iloc[-1]
            
            # Check for NaN values
            if any(pd.isna(row[field]) for field in ['Open', 'High', 'Low', 'Close']):
                raise DataNotFoundError('yahoo', ticker)
            
            return {
                'open': int(round(row['Open'] * 100)),
                'high': int(round(row['High'] * 100)),
                'low': int(round(row['Low'] * 100)),
                'close': int(round(row['Close'] * 100)),
                'volume': int(row['Volume']) if not pd.isna(row['Volume']) else None
            }
            
        except Exception as e:
            error_str = str(e).lower()
            # Check for various rate limit error patterns
            if any(pattern in error_str for pattern in ['rate limit', 'yfratelimiterror', 'too many requests']):
                raise RateLimitError('yahoo', ticker)
            else:
                raise ServiceError('yahoo', str(e), ticker)

class AlphaVantagePriceService(BaseService):
    """Alpha Vantage price service"""
    
    def __init__(self):
        super().__init__('alpha_vantage')
    
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get price data from Alpha Vantage"""
        if not self.validate_ticker(ticker):
            raise ServiceError('alpha_vantage', f"Invalid ticker: {ticker}", ticker)
        
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for rate limit or demo key message
                if 'Information' in data:
                    info = data['Information']
                    if 'rate limit' in info.lower() or 'demo' in info.lower() or '5 calls per minute' in info:
                        raise RateLimitError('alpha_vantage', ticker)
                
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    return {
                        'open': int(round(float(quote.get('02. open', 0)) * 100)),
                        'high': int(round(float(quote.get('03. high', 0)) * 100)),
                        'low': int(round(float(quote.get('04. low', 0)) * 100)),
                        'close': int(round(float(quote.get('05. price', 0)) * 100)),
                        'volume': int(quote.get('06. volume', 0)) if quote.get('06. volume') else None
                    }
            
            raise DataNotFoundError('alpha_vantage', ticker)
            
        except Exception as e:
            if 'rate limit' in str(e).lower():
                raise RateLimitError('alpha_vantage', ticker)
            else:
                raise ServiceError('alpha_vantage', str(e), ticker)

class FinnhubPriceService(BaseService):
    """Finnhub price service"""
    
    def __init__(self):
        super().__init__('finnhub')
    
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get price data from Finnhub"""
        if not self.validate_ticker(ticker):
            raise ServiceError('finnhub', f"Invalid ticker: {ticker}", ticker)
        
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'c' in data and data['c'] > 0:
                    return {
                        'open': int(round(data.get('o', 0) * 100)),
                        'high': int(round(data.get('h', 0) * 100)),
                        'low': int(round(data.get('l', 0) * 100)),
                        'close': int(round(data['c'] * 100)),
                        'volume': int(data.get('v', 0)) if data.get('v') else None
                    }
            
            raise DataNotFoundError('finnhub', ticker)
            
        except Exception as e:
            if 'rate limit' in str(e).lower():
                raise RateLimitError('finnhub', ticker)
            else:
                raise ServiceError('finnhub', str(e), ticker)

class FMPPriceService(BaseService):
    """Financial Modeling Prep price service"""
    
    def __init__(self):
        super().__init__('fmp')
    
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get price data from FMP"""
        if not self.validate_ticker(ticker):
            raise ServiceError('fmp', f"Invalid ticker: {ticker}", ticker)
        
        try:
            url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    quote = data[0]
                    return {
                        'open': int(round(quote.get('open', 0) * 100)),
                        'high': int(round(quote.get('dayHigh', 0) * 100)),
                        'low': int(round(quote.get('dayLow', 0) * 100)),
                        'close': int(round(quote.get('price', 0) * 100)),
                        'volume': int(quote.get('volume', 0)) if quote.get('volume') else None
                    }
            
            raise DataNotFoundError('fmp', ticker)
            
        except Exception as e:
            if 'rate limit' in str(e).lower():
                raise RateLimitError('fmp', ticker)
            else:
                raise ServiceError('fmp', str(e), ticker)

class PriceCollector:
    """Consolidated price collector for all ticker types"""
    
    def __init__(self, target_table: str = 'stocks'):
        """Initialize price collector"""
        self.target_table = target_table
        self.services = {
            'yahoo': YahooPriceService(),
            'alpha_vantage': AlphaVantagePriceService(),
            'finnhub': FinnhubPriceService(),
            'fmp': FMPPriceService()
        }
        # Updated service order to include Alpha Vantage
        self.service_order = ['yahoo', 'alpha_vantage', 'finnhub', 'fmp']
        self.batch_size = Config.BATCH_SIZE
    
    def get_tickers(self) -> List[str]:
        """Get tickers based on target table"""
        from database import DatabaseManager
        
        db = DatabaseManager()
        try:
            if self.target_table == 'stocks':
                return db.get_tickers('stocks')
            elif self.target_table == 'market_etf':
                return db.get_tickers('market_etf')
            else:
                raise ValueError(f"Unknown target table: {self.target_table}")
        finally:
            db.disconnect()
    
    def get_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get current prices for a list of tickers"""
        prices_data, _ = self.collect_prices_batch(tickers)
        return prices_data
    
    def get_sector_prices(self, sector: str = None) -> Dict[str, Dict]:
        """Get prices for sector ETFs or sector stocks"""
        from database import DatabaseManager
        
        db = DatabaseManager()
        try:
            if sector:
                # Get sector-specific tickers
                query = "SELECT ticker FROM stocks WHERE sector = %s"
                results = db.execute_query(query, (sector,))
                tickers = [row[0] for row in results]
            else:
                # Get all sector ETFs
                tickers = db.get_tickers('market_etf')
            
            return self.get_prices(tickers)
        finally:
            db.disconnect()
    
    def get_market_prices(self) -> Dict[str, Dict]:
        """Get prices for all market tickers"""
        tickers = self.get_tickers()
        return self.get_prices(tickers)
    
    def get_history(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical price data for a ticker"""
        try:
            data = yf.download(ticker, period=period, progress=False)
            if not data.empty:
                return data
            return None
        except Exception as e:
            print(f"Error getting history for {ticker}: {e}")
            return None
    
    def collect_prices_batch(self, tickers: List[str]) -> Tuple[Dict[str, Dict], List[str]]:
        """Collect prices for a batch of tickers with fallback and exponential backoff"""
        prices_data = {}
        failed_tickers = []
        global_cooldown = 0
        max_backoff = 60  # seconds
        backoff = 2
        
        for ticker in tickers:
            ticker_data = None
            rate_limited = False
            
            # Try each service in order
            for service_name in self.service_order:
                try:
                    service = self.services[service_name]
                    # Use APIRateLimiter for all rate limiting
                    if hasattr(service, 'api_limiter'):
                        if not service.api_limiter.check_limit(service_name, 'price'):
                            rate_limited = True
                            continue
                    ticker_data = service.get_data(ticker)
                    if ticker_data:
                        prices_data[ticker] = ticker_data
                        break
                except RateLimitError:
                    rate_limited = True
                    continue
                except Exception as e:
                    service.log_request(ticker, False, str(e))
                    continue
            
            if not ticker_data:
                failed_tickers.append(ticker)
                if rate_limited:
                    # Exponential backoff if all providers are rate limited
                    print(f"All providers rate limited for {ticker}, backing off for {backoff}s...")
                    import time
                    time.sleep(backoff)
                    global_cooldown += backoff
                    backoff = min(backoff * 2, max_backoff)
                else:
                    backoff = 2  # Reset backoff if not rate limited
        
        if global_cooldown > 0:
            print(f"Global cooldown applied: {global_cooldown}s")
        
        return prices_data, failed_tickers
    
    def _try_batch_requests(self, tickers: List[str]) -> Dict[str, Dict]:
        """Try to get prices for multiple tickers in batch requests"""
        batch_prices = {}
        
        # FMP supports batch quotes
        try:
            fmp_batch = self._get_fmp_batch_quotes(tickers)
            batch_prices.update(fmp_batch)
        except Exception as e:
            print(f"FMP batch request failed: {e}")
        
        # Alpha Vantage supports batch quotes (but limited)
        try:
            av_batch = self._get_alpha_vantage_batch_quotes(tickers[:5])  # Limit to 5 due to rate limits
            batch_prices.update(av_batch)
        except Exception as e:
            print(f"Alpha Vantage batch request failed: {e}")
        
        return batch_prices
    
    def _get_fmp_batch_quotes(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch quotes from FMP"""
        if not tickers:
            return {}
        
        try:
            # FMP supports comma-separated tickers
            ticker_list = ','.join(tickers)
            url = f"https://financialmodelingprep.com/api/v3/quote/{ticker_list}?apikey={self.services['fmp'].api_key}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list):
                    batch_prices = {}
                    for quote in data:
                        if quote.get('symbol'):
                            batch_prices[quote['symbol']] = {
                                'open': int(round(quote.get('open', 0) * 100)),
                                'high': int(round(quote.get('dayHigh', 0) * 100)),
                                'low': int(round(quote.get('dayLow', 0) * 100)),
                                'close': int(round(quote.get('price', 0) * 100)),
                                'volume': int(quote.get('volume', 0)) if quote.get('volume') else None
                            }
                    return batch_prices
            
            return {}
            
        except Exception as e:
            print(f"FMP batch request error: {e}")
            return {}
    
    def _get_alpha_vantage_batch_quotes(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch quotes from Alpha Vantage (limited due to rate limits)"""
        if not tickers:
            return {}
        
        batch_prices = {}
        
        for ticker in tickers:
            try:
                # Use the individual Alpha Vantage service
                service = self.services['alpha_vantage']
                data = service.get_data(ticker)
                if data:
                    batch_prices[ticker] = data
                
            except Exception as e:
                print(f"Alpha Vantage batch request error for {ticker}: {e}")
                continue
        
        return batch_prices
    
    def collect_all_prices(self) -> Tuple[Dict[str, Dict], List[str]]:
        """Collect prices for all tickers"""
        tickers = self.get_tickers()
        all_prices = {}
        all_failed = []
        
        # Process in batches
        for i in range(0, len(tickers), self.batch_size):
            batch = tickers[i:i + self.batch_size]
            prices, failed = self.collect_prices_batch(batch)
            
            all_prices.update(prices)
            all_failed.extend(failed)
            
            # Rate limiting delay between batches
            time.sleep(2)
        
        return all_prices, all_failed
    
    def update_database(self, prices_data: Dict[str, Dict]) -> int:
        """Update database with collected prices"""
        from database import DatabaseManager
        
        db = DatabaseManager()
        updated_count = 0
        
        try:
            for ticker, price_data in prices_data.items():
                # Always use daily_charts table for price data, regardless of target_table
                db.update_price_data(ticker, price_data, 'daily_charts')
                updated_count += 1
        finally:
            db.disconnect()
        
        return updated_count
    
    def run(self) -> Dict[str, Any]:
        """Run complete price collection process"""
        print(f"Starting price collection for {self.target_table}")
        
        # Collect prices
        prices_data, failed_tickers = self.collect_all_prices()
        
        # Update database
        updated_count = self.update_database(prices_data)
        
        results = {
            'target_table': self.target_table,
            'total_tickers': len(prices_data) + len(failed_tickers),
            'successful': len(prices_data),
            'failed': len(failed_tickers),
            'updated_in_db': updated_count,
            'failed_tickers': failed_tickers
        }
        
        print(f"Price collection completed: {results['successful']}/{results['total_tickers']} successful")
        return results
    
    def close(self):
        """Close all service connections"""
        for service in self.services.values():
            service.close()

def test_price_service():
    """Test price service functionality"""
    print("Testing Price Service")
    print("=" * 30)
    
    # Test individual services
    yahoo = YahooPriceService()
    try:
        data = yahoo.get_data('AAPL')
        print(f"Yahoo AAPL: ${data['close']/100:.2f}")
    except Exception as e:
        print(f"Yahoo error: {e}")
    
    # Test price collector
    collector = PriceCollector('stocks')
    try:
        # Test with small batch
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        prices, failed = collector.collect_prices_batch(test_tickers)
        print(f"Batch test: {len(prices)} successful, {len(failed)} failed")
        
        # Test get_prices method
        prices_data = collector.get_prices(test_tickers)
        print(f"get_prices test: {len(prices_data)} successful")
        
        # Test get_history method
        history = collector.get_history('AAPL', '1mo')
        if history is not None:
            print(f"History test: {len(history)} days of data")
        
    except Exception as e:
        print(f"Collector error: {e}")
    finally:
        collector.close()
    
    print("Price service test completed")

if __name__ == "__main__":
    test_price_service() 