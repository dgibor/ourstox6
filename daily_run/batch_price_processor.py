"""
Batch Price Processor

Handles batch price processing for up to 100 stocks per API call
and stores daily prices in the daily_charts table.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor

logger = logging.getLogger(__name__)


class BatchPriceProcessor:
    """
    Processes price data for multiple tickers in batches of up to 100 per API call.
    Stores daily prices in the daily_charts table.
    """
    
    def __init__(self, db: DatabaseManager, max_batch_size: int = 100, 
                 max_workers: int = 5, delay_between_batches: float = 1.0):
        self.db = db
        self.max_batch_size = max_batch_size
        self.max_workers = max_workers
        self.delay_between_batches = delay_between_batches
        self.error_handler = ErrorHandler("batch_price_processor")
        self.monitoring = SystemMonitor()
        
        # Initialize services
        self.yahoo_service = YahooFinanceService()
        self.alpha_vantage_service = AlphaVantageService()
        self.finnhub_service = FinnhubService()
    
    def process_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Process prices for multiple tickers using batch API calls.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to price data
        """
        start_time = time.time()
        logger.info(f"Starting batch price processing for {len(tickers)} tickers")
        
        results = {}
        total_batches = (len(tickers) + self.max_batch_size - 1) // self.max_batch_size
        
        try:
            # Split tickers into batches
            batches = [
                tickers[i:i + self.max_batch_size] 
                for i in range(0, len(tickers), self.max_batch_size)
            ]
            
            # Process batches with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_batch = {
                    executor.submit(self._process_single_batch, batch, batch_num): batch
                    for batch_num, batch in enumerate(batches, 1)
                }
                
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    batch_num = batches.index(batch) + 1
                    
                    try:
                        batch_results = future.result()
                        results.update(batch_results)
                        logger.info(f"Completed batch {batch_num}/{total_batches} with {len(batch_results)} results")
                        
                        # Rate limiting between batches
                        if batch_num < total_batches:
                            time.sleep(self.delay_between_batches)
                            
                    except Exception as e:
                        logger.error(f"Error processing batch {batch_num}: {e}")
                        self.error_handler.handle_error(
                            f"Batch price processing failed for batch {batch_num}",
                            e, ErrorSeverity.HIGH
                        )
            
            # Store results in daily_charts table
            if results:
                self.store_daily_prices(results)
            
            processing_time = time.time() - start_time
            logger.info(f"Batch price processing completed in {processing_time:.2f}s")
            logger.info(f"Successfully processed {len(results)}/{len(tickers)} tickers")
            
            # Update monitoring metrics
            self.monitoring.record_metric(
                'batch_price_processing_time', processing_time
            )
            self.monitoring.record_metric(
                'batch_price_success_rate', len(results) / len(tickers)
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Batch price processing failed: {e}")
            self.error_handler.handle_error(
                "Batch price processing failed", e, ErrorSeverity.CRITICAL
            )
            return {}
    
    def _process_single_batch(self, tickers: List[str], batch_num: int) -> Dict[str, Dict]:
        """
        Process a single batch of tickers using fallback services.
        
        Args:
            tickers: List of ticker symbols for this batch
            batch_num: Batch number for logging
            
        Returns:
            Dictionary mapping ticker to price data
        """
        logger.debug(f"Processing batch {batch_num} with {len(tickers)} tickers")
        
        # Try services in order of preference
        services = [
            ('Yahoo Finance', self._get_yahoo_batch_prices),
            ('Alpha Vantage', self._get_alpha_vantage_batch_prices),
            ('Finnhub', self._get_finnhub_batch_prices)
        ]
        
        for service_name, service_func in services:
            try:
                logger.debug(f"Trying {service_name} for batch {batch_num}")
                results = service_func(tickers)
                
                if results:
                    logger.info(f"Successfully got {len(results)} results from {service_name}")
                    return results
                    
            except Exception as e:
                logger.warning(f"{service_name} failed for batch {batch_num}: {e}")
                continue
        
        logger.error(f"All services failed for batch {batch_num}")
        return {}
    
    def _get_yahoo_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch prices from Yahoo Finance (up to 100 symbols per call)"""
        try:
            symbols = ','.join(tickers)
            url = "https://query1.finance.yahoo.com/v7/finance/quote"
            params = {
                'symbols': symbols,
                'fields': 'regularMarketPrice,regularMarketVolume,marketCap,regularMarketTime,regularMarketChange,regularMarketChangePercent'
            }
            
            response = self.yahoo_service._make_request(url, params)
            return self._parse_yahoo_batch_response(response, tickers)
            
        except Exception as e:
            logger.error(f"Yahoo Finance batch request failed: {e}")
            raise
    
    def _get_alpha_vantage_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch prices from Alpha Vantage"""
        try:
            # Alpha Vantage has a batch quote endpoint
            symbols = ','.join(tickers)
            url = f"{self.alpha_vantage_service.base_url}/query"
            params = {
                'function': 'BATCH_STOCK_QUOTES',
                'symbols': symbols,
                'apikey': self.alpha_vantage_service.api_key
            }
            
            response = self.alpha_vantage_service._make_request(url, params)
            return self._parse_alpha_vantage_batch_response(response, tickers)
            
        except Exception as e:
            logger.error(f"Alpha Vantage batch request failed: {e}")
            raise
    
    def _get_finnhub_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch prices from Finnhub"""
        try:
            # Finnhub supports multiple symbols in one call
            symbols = ','.join(tickers)
            url = f"{self.finnhub_service.base_url}/quote"
            params = {
                'symbol': symbols,
                'token': self.finnhub_service.api_key
            }
            
            response = self.finnhub_service._make_request(url, params)
            return self._parse_finnhub_batch_response(response, tickers)
            
        except Exception as e:
            logger.error(f"Finnhub batch request failed: {e}")
            raise
    
    def _parse_yahoo_batch_response(self, response: Dict, tickers: List[str]) -> Dict[str, Dict]:
        """Parse Yahoo Finance batch response"""
        results = {}
        
        try:
            quote_response = response.get('quoteResponse', {})
            quotes = quote_response.get('result', [])
            
            for quote in quotes:
                symbol = quote.get('symbol')
                if symbol in tickers:
                    results[symbol] = {
                        'close_price': quote.get('regularMarketPrice'),
                        'volume': quote.get('regularMarketVolume'),
                        'market_cap': quote.get('marketCap'),
                        'change': quote.get('regularMarketChange'),
                        'change_percent': quote.get('regularMarketChangePercent'),
                        'data_source': 'yahoo_finance',
                        'timestamp': datetime.now()
                    }
            
        except Exception as e:
            logger.error(f"Error parsing Yahoo Finance response: {e}")
        
        return results
    
    def _parse_alpha_vantage_batch_response(self, response: Dict, tickers: List[str]) -> Dict[str, Dict]:
        """Parse Alpha Vantage batch response"""
        results = {}
        
        try:
            quotes = response.get('Stock Quotes', [])
            
            for quote in quotes:
                symbol = quote.get('1. symbol')
                if symbol in tickers:
                    results[symbol] = {
                        'close_price': float(quote.get('2. price', 0)),
                        'volume': int(quote.get('3. volume', 0)),
                        'change': float(quote.get('4. change', 0)),
                        'change_percent': quote.get('5. change percent', '0%'),
                        'data_source': 'alpha_vantage',
                        'timestamp': datetime.now()
                    }
            
        except Exception as e:
            logger.error(f"Error parsing Alpha Vantage response: {e}")
        
        return results
    
    def _parse_finnhub_batch_response(self, response: Dict, tickers: List[str]) -> Dict[str, Dict]:
        """Parse Finnhub batch response"""
        results = {}
        
        try:
            # Finnhub returns array of quotes
            quotes = response if isinstance(response, list) else [response]
            
            for quote in quotes:
                symbol = quote.get('symbol')
                if symbol in tickers:
                    results[symbol] = {
                        'close_price': quote.get('c'),  # Current price
                        'volume': quote.get('v'),      # Volume
                        'change': quote.get('d'),      # Change
                        'change_percent': quote.get('dp'),  # Change percent
                        'data_source': 'finnhub',
                        'timestamp': datetime.now()
                    }
            
        except Exception as e:
            logger.error(f"Error parsing Finnhub response: {e}")
        
        return results
    
    def store_daily_prices(self, price_data: Dict[str, Dict]):
        """
        Store daily prices in the daily_charts table.
        
        Args:
            price_data: Dictionary mapping ticker to price data
        """
        if not price_data:
            logger.warning("No price data to store")
            return
        
        logger.info(f"Storing {len(price_data)} daily price records")
        
        try:
            # Prepare batch insert
            values = []
            today = date.today()
            
            for ticker, data in price_data.items():
                if data.get('close_price'):
                    values.append((
                        ticker,
                        today,
                        data.get('close_price'),  # Use close as open/high/low if not available
                        data.get('close_price'),
                        data.get('close_price'),
                        data.get('close_price'),
                        data.get('volume', 0),
                        data.get('market_cap'),
                        data.get('data_source', 'batch_api'),
                        datetime.now()
                    ))
            
            if values:
                # Batch insert with conflict resolution
                query = """
                INSERT INTO daily_charts (
                    ticker, date, open_price, high_price, low_price, 
                    close_price, volume, market_cap, data_source, created_at
                ) VALUES %s
                ON CONFLICT (ticker, date) 
                DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    market_cap = EXCLUDED.market_cap,
                    data_source = EXCLUDED.data_source,
                    updated_at = NOW()
                """
                
                # Execute batch insert
                self.db.execute_batch(query, values)
                logger.info(f"Successfully stored {len(values)} daily price records")
                
                # Update monitoring
                self.monitoring.record_metric('daily_prices_stored', len(values))
                
        except Exception as e:
            logger.error(f"Error storing daily prices: {e}")
            self.error_handler.handle_error(
                "Failed to store daily prices", e, ErrorSeverity.HIGH
            )
    
    def get_latest_daily_price(self, ticker: str) -> Optional[Dict]:
        """
        Get the latest daily price from daily_charts table.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Latest price data or None
        """
        try:
            query = """
            SELECT * FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            return self.db.fetch_one(query, (ticker,))
            
        except Exception as e:
            logger.error(f"Error getting latest daily price for {ticker}: {e}")
            return None
    
    def get_daily_prices_for_date(self, tickers: List[str], target_date: date) -> Dict[str, Dict]:
        """
        Get daily prices for specific tickers on a specific date.
        
        Args:
            tickers: List of ticker symbols
            target_date: Target date
            
        Returns:
            Dictionary mapping ticker to price data
        """
        try:
            placeholders = ','.join(['%s'] * len(tickers))
            query = """
            SELECT * FROM daily_charts 
            WHERE ticker IN ({}) AND date = %s
            """.format(placeholders)
            
            params = tickers + [target_date]
            results = self.db.fetch_all(query, params)
            
            return {row['ticker']: row for row in results}
            
        except Exception as e:
            logger.error(f"Error getting daily prices for date {target_date}: {e}")
            return {}


def main():
    """Test the batch price processor"""
    logging.basicConfig(level=logging.INFO)
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
    
    # Initialize database and processor
    db = DatabaseManager()
    processor = BatchPriceProcessor(db)
    
    try:
        # Process batch prices
        results = processor.process_batch_prices(test_tickers)
        
        print(f"\nResults: {len(results)} tickers processed")
        for ticker, data in results.items():
            print(f"{ticker}: ${data.get('close_price', 'N/A')}")
        
        # Get latest prices from database
        print("\nLatest prices from database:")
        for ticker in test_tickers:
            latest = processor.get_latest_daily_price(ticker)
            if latest:
                print(f"{ticker}: ${latest.get('close_price', 'N/A')} on {latest.get('date')}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main() 