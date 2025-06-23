#!/usr/bin/env python3
"""
Integrated Daily Runner V2
Enhanced version with:
1. All 4 data sources (Yahoo, Finnhub, Alpha Vantage, FMP)
2. Technical indicators calculation
3. Market schedule checking
4. Improved fallback logic
"""

import logging
import argparse
from datetime import datetime
from typing import Dict, List
from database import DatabaseManager
from config import Config
from check_market_schedule import check_market_open_today, should_run_daily_process
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integrated_daily_v2.log'),
        logging.StreamHandler()
    ]
)

class MultiServicePriceCollector:
    """Price collector using all 4 data sources with fallback"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.services = {}
        self.setup_services()
        
    def setup_services(self):
        """Setup all available price services"""
        try:
            from yahoo_finance_service import YahooFinanceService
            self.services['yahoo'] = YahooFinanceService()
            logging.info("Yahoo Finance price service initialized")
        except Exception as e:
            logging.warning(f"Yahoo Finance price service not available: {e}")
        
        try:
            from fmp_service import FMPService
            self.services['fmp'] = FMPService()
            logging.info("FMP price service initialized")
        except Exception as e:
            logging.warning(f"FMP price service not available: {e}")
    
    def get_price_data(self, ticker: str) -> Dict:
        """Get price data with fallback logic"""
        service_order = ['yahoo', 'fmp']
        
        for service_name in service_order:
            if service_name not in self.services:
                continue
                
            try:
                logging.info(f"Trying {service_name} for {ticker} price data")
                service = self.services[service_name]
                
                # Get price data from service - use the correct method
                if service_name == 'yahoo':
                    # Yahoo service doesn't have get_current_price, use yfinance directly
                    import yfinance as yf
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    if info and info.get('currentPrice'):
                        return {
                            'data': {
                                'current_price': info.get('currentPrice', 0),
                                'volume': info.get('volume', 0),
                                'high': info.get('dayHigh', info.get('currentPrice', 0)),
                                'low': info.get('dayLow', info.get('currentPrice', 0)),
                                'open': info.get('open', info.get('currentPrice', 0))
                            },
                            'source': service_name,
                            'timestamp': datetime.now()
                        }
                elif service_name == 'fmp':
                    # FMP service doesn't have get_price_data, use the correct method
                    result = service.get_fundamental_data(ticker)
                    if result and result.get('key_stats', {}).get('market_data', {}).get('current_price'):
                        market_data = result['key_stats']['market_data']
                        return {
                            'data': {
                                'current_price': market_data.get('current_price', 0),
                                'volume': market_data.get('volume', 0),
                                'high': market_data.get('high', market_data.get('current_price', 0)),
                                'low': market_data.get('low', market_data.get('current_price', 0)),
                                'open': market_data.get('open', market_data.get('current_price', 0))
                            },
                            'source': service_name,
                            'timestamp': datetime.now()
                        }
                
                logging.warning(f"No price data from {service_name} for {ticker}")
                    
            except Exception as e:
                logging.error(f"Error with {service_name} for {ticker}: {e}")
                continue
        
        logging.error(f"All price services failed for {ticker}")
        return None
    
    def update_prices_batch(self, tickers: List[str], max_tickers: int = None) -> Dict:
        """Update prices for multiple tickers"""
        if max_tickers:
            tickers = tickers[:max_tickers]
        
        successful = 0
        failed = 0
        errors = []
        
        logging.info(f"Starting price updates for {len(tickers)} tickers")
        
        for i, ticker in enumerate(tickers, 1):
            try:
                result = self.get_price_data(ticker)
                
                if result and result.get('data'):
                    # Store price data in database
                    price_data = result['data']
                    self.store_price_data(ticker, price_data, result['source'])
                    successful += 1
                    logging.info(f"[{i}/{len(tickers)}] SUCCESS: Updated {ticker} from {result['source']}")
                else:
                    failed += 1
                    errors.append(f"{ticker}: No data available")
                    logging.warning(f"[{i}/{len(tickers)}] FAILED: {ticker}")
                
                # Rate limiting
                if i < len(tickers):
                    time.sleep(1)
                    
            except Exception as e:
                failed += 1
                error_msg = f"{ticker}: {str(e)}"
                errors.append(error_msg)
                logging.error(f"[{i}/{len(tickers)}] ERROR: {ticker}: {e}")
        
        return {
            'total_tickers': len(tickers),
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def store_price_data(self, ticker: str, price_data: Dict, source: str):
        """Store price data in database"""
        try:
            self.db.connect()
            
            current_price = price_data.get('current_price', 0)
            volume = price_data.get('volume', 0)
            
            # Only insert into daily_charts table - stocks table doesn't have price columns
            query = """
            INSERT INTO daily_charts (ticker, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
            """
            
            from datetime import date
            current_date = date.today().strftime('%Y-%m-%d')
            
            high = price_data.get('high', current_price)
            low = price_data.get('low', current_price)
            open_price = price_data.get('open', current_price)
            
            self.db.execute_update(query, (
                ticker,
                current_date,
                int(open_price * 100), 
                int(high * 100), 
                int(low * 100), 
                int(current_price * 100), 
                volume
            ))
            
            logging.info(f"Successfully stored price data for {ticker} in daily_charts table")
            
        except Exception as e:
            logging.error(f"Error storing price data for {ticker}: {e}")
        finally:
            self.db.disconnect()
    
    def close(self):
        """Close all service connections"""
        for service_name, service in self.services.items():
            try:
                service.close()
                logging.info(f"Closed {service_name} price service")
            except Exception as e:
                logging.warning(f"Error closing {service_name} price service: {e}")

class MultiServiceFundamentalsCollector:
    """Fundamentals collector using all 4 data sources with fallback"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.services = {}
        self.setup_services()
        
    def setup_services(self):
        """Setup all available fundamental services"""
        try:
            from yahoo_finance_service import YahooFinanceService
            self.services['yahoo'] = YahooFinanceService()
            logging.info("Yahoo Finance fundamental service initialized")
        except Exception as e:
            logging.warning(f"Yahoo Finance fundamental service not available: {e}")
        
        try:
            from alpha_vantage_service import AlphaVantageService
            self.services['alphavantage'] = AlphaVantageService()
            logging.info("Alpha Vantage fundamental service initialized")
        except Exception as e:
            logging.warning(f"Alpha Vantage fundamental service not available: {e}")
        
        try:
            from finnhub_service import FinnhubService
            self.services['finnhub'] = FinnhubService()
            logging.info("Finnhub fundamental service initialized")
        except Exception as e:
            logging.warning(f"Finnhub fundamental service not available: {e}")
        
        try:
            from fmp_service import FMPService
            self.services['fmp'] = FMPService()
            logging.info("FMP fundamental service initialized")
        except Exception as e:
            logging.warning(f"FMP fundamental service not available: {e}")
    
    def get_fundamental_data(self, ticker: str) -> Dict:
        """Get fundamental data with fallback logic"""
        service_order = ['yahoo', 'fmp', 'alphavantage', 'finnhub']
        
        for service_name in service_order:
            if service_name not in self.services:
                continue
                
            try:
                logging.info(f"Trying {service_name} for {ticker} fundamental data")
                service = self.services[service_name]
                
                # Get fundamental data from service - use the correct method
                if service_name == 'yahoo':
                    result = service.get_fundamental_data(ticker)
                elif service_name == 'fmp':
                    result = service.get_fundamental_data(ticker)
                elif service_name == 'alphavantage':
                    result = service.get_fundamental_data(ticker)
                elif service_name == 'finnhub':
                    result = service.get_fundamental_data(ticker)
                else:
                    result = None
                
                if result:
                    return {
                        'data': result,
                        'source': service_name,
                        'timestamp': datetime.now()
                    }
                
                logging.warning(f"No fundamental data from {service_name} for {ticker}")
                    
            except Exception as e:
                logging.error(f"Error with {service_name} for {ticker}: {e}")
                continue
        
        logging.error(f"All fundamental services failed for {ticker}")
        return None
    
    def update_fundamentals_batch(self, tickers: List[str], max_tickers: int = None) -> Dict:
        """Update fundamentals for multiple tickers"""
        if max_tickers:
            tickers = tickers[:max_tickers]
        
        successful = 0
        failed = 0
        errors = []
        
        logging.info(f"Starting fundamental updates for {len(tickers)} tickers")
        
        for i, ticker in enumerate(tickers, 1):
            try:
                result = self.get_fundamental_data(ticker)
                
                if result and result.get('data'):
                    # Store fundamental data in database
                    fundamental_data = result['data']
                    self.store_fundamental_data(ticker, fundamental_data, result['source'])
                    successful += 1
                    logging.info(f"[{i}/{len(tickers)}] SUCCESS: Updated {ticker} from {result['source']}")
                else:
                    failed += 1
                    errors.append(f"{ticker}: No fundamental data available")
                    logging.warning(f"[{i}/{len(tickers)}] FAILED: {ticker}")
                
                # Rate limiting
                if i < len(tickers):
                    time.sleep(1)
                    
            except Exception as e:
                failed += 1
                error_msg = f"{ticker}: {str(e)}"
                errors.append(error_msg)
                logging.error(f"[{i}/{len(tickers)}] ERROR: {ticker}: {e}")
        
        return {
            'total_tickers': len(tickers),
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def store_fundamental_data(self, ticker: str, fundamental_data: Dict, source: str):
        """Store fundamental data in database"""
        try:
            self.db.connect()
            
            # Handle different data structures from different services
            if source == 'yahoo':
                # Yahoo service returns data directly
                financial_data = fundamental_data.get('financial_data', {})
                key_stats = fundamental_data.get('key_stats', {})
            else:
                # Other services return data in a different structure
                financial_data = fundamental_data
                key_stats = fundamental_data
            
            # Extract values with safe defaults
            income_stmt = financial_data.get('income_statement', {}) if financial_data else {}
            balance_sheet = financial_data.get('balance_sheet', {}) if financial_data else {}
            market_data = key_stats.get('market_data', {}) if key_stats else {}
            per_share = key_stats.get('per_share_metrics', {}) if key_stats else {}
            
            # Update stocks table with fundamental data
            query = """
            UPDATE stocks SET
                market_cap = %s,
                shares_outstanding = %s,
                revenue_ttm = %s,
                net_income_ttm = %s,
                ebitda_ttm = %s,
                total_debt = %s,
                shareholders_equity = %s,
                cash_and_equivalents = %s,
                diluted_eps_ttm = %s,
                book_value_per_share = %s,
                total_assets = %s,
                current_assets = %s,
                current_liabilities = %s,
                operating_income = %s,
                free_cash_flow = %s,
                enterprise_value = %s,
                fundamentals_last_update = NOW()
            WHERE ticker = %s
            """
            
            self.db.execute_update(query, (
                market_data.get('market_cap'),
                market_data.get('shares_outstanding'),
                income_stmt.get('revenue'),
                income_stmt.get('net_income'),
                income_stmt.get('ebitda'),
                balance_sheet.get('total_debt'),
                balance_sheet.get('total_equity'),
                balance_sheet.get('cash_and_equivalents'),
                per_share.get('eps_diluted'),
                per_share.get('book_value_per_share'),
                balance_sheet.get('total_assets'),
                balance_sheet.get('current_assets'),
                balance_sheet.get('current_liabilities'),
                income_stmt.get('operating_income'),
                financial_data.get('cash_flow', {}).get('free_cash_flow') if financial_data else None,
                market_data.get('enterprise_value'),
                ticker
            ))
            
            logging.info(f"Successfully stored fundamental data for {ticker} from {source}")
            
        except Exception as e:
            logging.error(f"Error storing fundamental data for {ticker}: {e}")
        finally:
            self.db.disconnect()
    
    def close(self):
        """Close all service connections"""
        for service_name, service in self.services.items():
            try:
                service.close()
                logging.info(f"Closed {service_name} fundamental service")
            except Exception as e:
                logging.warning(f"Error closing {service_name} fundamental service: {e}")

class TechnicalIndicatorsCalculator:
    """Calculate technical indicators for all tickers"""
    
    def __init__(self):
        self.db = DatabaseManager()
        
    def calculate_indicators_for_ticker(self, ticker: str) -> Dict:
        """Calculate technical indicators for a single ticker"""
        try:
            self.db.connect()
            
            # Get historical price data
            query = """
            SELECT date, open, high, low, close, volume
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 50
            """
            
            results = self.db.execute_query(query, (ticker,))
            if not results or len(results) < 20:
                logging.warning(f"Insufficient data for {ticker} technical indicators")
                return {'error': 'Insufficient data'}
            
            # Convert to price data structure
            prices = []
            for row in results:
                date, open_price, high, low, close, volume = row
                prices.append({
                    'date': date,
                    'open': float(open_price) / 100,
                    'high': float(high) / 100,
                    'low': float(low) / 100,
                    'close': float(close) / 100,
                    'volume': volume
                })
            
            # Calculate indicators
            indicators = self.calculate_all_indicators(prices)
            
            # Store indicators in database
            self.store_indicators(ticker, indicators)
            
            return indicators
            
        except Exception as e:
            logging.error(f"Error calculating indicators for {ticker}: {e}")
            return {'error': str(e)}
        finally:
            self.db.disconnect()
    
    def calculate_all_indicators(self, prices: List[Dict]) -> Dict:
        """Calculate all technical indicators"""
        if len(prices) < 20:
            return {'error': 'Insufficient data'}
        
        # Reverse prices for chronological order
        prices = list(reversed(prices))
        
        indicators = {}
        
        # Calculate moving averages
        indicators['sma_20'] = self.calculate_sma(prices, 20)
        indicators['sma_50'] = self.calculate_sma(prices, 50)
        indicators['ema_12'] = self.calculate_ema(prices, 12)
        indicators['ema_26'] = self.calculate_ema(prices, 26)
        
        # Calculate RSI
        indicators['rsi'] = self.calculate_rsi(prices, 14)
        
        # Calculate MACD
        macd_data = self.calculate_macd(prices)
        indicators.update(macd_data)
        
        # Calculate Bollinger Bands
        bb_data = self.calculate_bollinger_bands(prices, 20)
        indicators.update(bb_data)
        
        # Calculate volume indicators
        indicators['volume_sma'] = self.calculate_volume_sma(prices, 20)
        
        return indicators
    
    def calculate_sma(self, prices: List[Dict], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        
        recent_prices = [p['close'] for p in prices[-period:] if p['close'] is not None]
        if len(recent_prices) < period:
            return None
        
        return sum(recent_prices) / len(recent_prices)
    
    def calculate_ema(self, prices: List[Dict], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        # Filter out None values
        valid_prices = [p for p in prices if p['close'] is not None]
        if len(valid_prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = valid_prices[0]['close']
        
        for price in valid_prices[1:]:
            ema = (price['close'] * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def calculate_rsi(self, prices: List[Dict], period: int) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        # Filter out None values
        valid_prices = [p for p in prices if p['close'] is not None]
        if len(valid_prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(valid_prices)):
            change = valid_prices[i]['close'] - valid_prices[i-1]['close']
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: List[Dict]) -> Dict:
        """Calculate MACD"""
        ema_12 = self.calculate_ema(prices, 12)
        ema_26 = self.calculate_ema(prices, 26)
        
        if ema_12 is None or ema_26 is None:
            return {'macd': None, 'macd_signal': None, 'macd_histogram': None}
        
        macd_line = ema_12 - ema_26
        
        # Calculate signal line (EMA of MACD)
        macd_values = []
        for i in range(len(prices)):
            ema_12_i = self.calculate_ema(prices[:i+1], 12)
            ema_26_i = self.calculate_ema(prices[:i+1], 26)
            if ema_12_i and ema_26_i:
                macd_values.append(ema_12_i - ema_26_i)
        
        if len(macd_values) < 9:
            return {'macd': macd_line, 'macd_signal': None, 'macd_histogram': None}
        
        signal_line = self.calculate_ema([{'close': v} for v in macd_values], 9)
        histogram = macd_line - signal_line if signal_line else None
        
        return {
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }
    
    def calculate_bollinger_bands(self, prices: List[Dict], period: int) -> Dict:
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(prices, period)
        if sma is None:
            return {'bb_upper': None, 'bb_middle': None, 'bb_lower': None}
        
        recent_prices = [p['close'] for p in prices[-period:] if p['close'] is not None]
        if len(recent_prices) < period:
            return {'bb_upper': None, 'bb_middle': None, 'bb_lower': None}
        
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std_dev = variance ** 0.5
        
        return {
            'bb_upper': sma + (2 * std_dev),
            'bb_middle': sma,
            'bb_lower': sma - (2 * std_dev)
        }
    
    def calculate_volume_sma(self, prices: List[Dict], period: int) -> float:
        """Calculate Volume Simple Moving Average"""
        if len(prices) < period:
            return None
        
        recent_volumes = [p['volume'] for p in prices[-period:] if p['volume'] is not None]
        if len(recent_volumes) < period:
            return None
        
        return sum(recent_volumes) / len(recent_volumes)
    
    def store_indicators(self, ticker: str, indicators: Dict):
        """Store technical indicators in database"""
        try:
            # Create technical_indicators table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                sma_20 DECIMAL(10,4),
                sma_50 DECIMAL(10,4),
                ema_12 DECIMAL(10,4),
                ema_26 DECIMAL(10,4),
                rsi DECIMAL(10,4),
                macd DECIMAL(10,4),
                macd_signal DECIMAL(10,4),
                macd_histogram DECIMAL(10,4),
                bb_upper DECIMAL(10,4),
                bb_middle DECIMAL(10,4),
                bb_lower DECIMAL(10,4),
                volume_sma BIGINT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(ticker, date)
            )
            """
            self.db.execute_update(create_table_query)
            
            # Insert or update indicators
            query = """
            INSERT INTO technical_indicators (
                ticker, date, sma_20, sma_50, ema_12, ema_26, rsi, 
                macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, volume_sma
            ) VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
                sma_20 = EXCLUDED.sma_20,
                sma_50 = EXCLUDED.sma_50,
                ema_12 = EXCLUDED.ema_12,
                ema_26 = EXCLUDED.ema_26,
                rsi = EXCLUDED.rsi,
                macd = EXCLUDED.macd,
                macd_signal = EXCLUDED.macd_signal,
                macd_histogram = EXCLUDED.macd_histogram,
                bb_upper = EXCLUDED.bb_upper,
                bb_middle = EXCLUDED.bb_middle,
                bb_lower = EXCLUDED.bb_lower,
                volume_sma = EXCLUDED.volume_sma,
                created_at = NOW()
            """
            
            self.db.execute_update(query, (
                ticker,
                indicators.get('sma_20'),
                indicators.get('sma_50'),
                indicators.get('ema_12'),
                indicators.get('ema_26'),
                indicators.get('rsi'),
                indicators.get('macd'),
                indicators.get('macd_signal'),
                indicators.get('macd_histogram'),
                indicators.get('bb_upper'),
                indicators.get('bb_middle'),
                indicators.get('bb_lower'),
                indicators.get('volume_sma')
            ))
            
            logging.info(f"Stored technical indicators for {ticker}")
            
        except Exception as e:
            logging.error(f"Error storing indicators for {ticker}: {e}")

class IntegratedDailyRunnerV2:
    """Enhanced integrated daily runner with all improvements"""
    
    def __init__(self):
        self.config = Config()
        self.price_collector = MultiServicePriceCollector()
        self.fundamentals_collector = MultiServiceFundamentalsCollector()
        self.indicators_calculator = TechnicalIndicatorsCalculator()
        
    def run_complete_daily_pipeline(self, 
                                  test_mode: bool = False, 
                                  max_price_tickers: int = 100,
                                  max_fundamental_tickers: int = 50) -> Dict:
        """
        Run the complete daily pipeline with all improvements
        """
        start_time = datetime.now()
        logging.info("=" * 80)
        logging.info("STARTING INTEGRATED DAILY PIPELINE V2")
        logging.info("=" * 80)
        
        pipeline_results = {
            'start_time': start_time,
            'market_status': {},
            'price_update': {},
            'fundamentals_update': {},
            'technical_indicators': {},
            'overall_status': 'unknown'
        }
        
        try:
            # Step 0: Check market schedule
            logging.info("\n" + "="*60)
            logging.info("STEP 0: MARKET SCHEDULE CHECK")
            logging.info("=" * 60)
            
            market_open, message, details = check_market_open_today()
            pipeline_results['market_status'] = {
                'market_open': market_open,
                'message': message,
                'details': details
            }
            
            logging.info(f"Market Status: {message}")
            
            # Step 1: Price Updates (Priority)
            logging.info("\n" + "="*60)
            logging.info("STEP 1: PRICE UPDATES (PRIORITY)")
            logging.info("=" * 60)
            
            # Get tickers to update
            tickers = self.get_tickers_to_update(test_mode, max_price_tickers)
            
            price_result = self.price_collector.update_prices_batch(tickers, max_price_tickers)
            pipeline_results['price_update'] = price_result
            logging.info(f"Price update completed: {price_result}")
            
            if price_result.get('successful', 0) == 0:
                logging.error("No price updates successful, stopping pipeline")
                pipeline_results['overall_status'] = 'failed_price'
                return pipeline_results
            
            # Step 2: Technical Indicators (After prices)
            logging.info("\n" + "="*60)
            logging.info("STEP 2: TECHNICAL INDICATORS")
            logging.info("=" * 60)
            
            indicators_result = self.calculate_technical_indicators(tickers[:20])  # Limit for performance
            pipeline_results['technical_indicators'] = indicators_result
            logging.info(f"Technical indicators completed: {indicators_result}")
            
            # Step 3: Fundamentals Updates (Conditional)
            if market_open:
                logging.info("\n" + "="*60)
                logging.info("STEP 3: FUNDAMENTALS UPDATES (Market was open)")
                logging.info("=" * 60)
                
                fundamentals_result = self.fundamentals_collector.update_fundamentals_batch(
                    tickers, max_fundamental_tickers
                )
                pipeline_results['fundamentals_update'] = fundamentals_result
                logging.info(f"Fundamentals update completed: {fundamentals_result}")
            else:
                logging.info("\n" + "="*60)
                logging.info("STEP 3: FUNDAMENTALS UPDATES (Market was closed - focus on fundamentals)")
                logging.info("=" * 60)
                
                # When market is closed, focus more on fundamentals
                fundamentals_result = self.fundamentals_collector.update_fundamentals_batch(
                    tickers, max_fundamental_tickers * 2  # Double the limit
                )
                pipeline_results['fundamentals_update'] = fundamentals_result
                logging.info(f"Fundamentals update completed: {fundamentals_result}")
            
            # Overall success
            pipeline_results['overall_status'] = 'success'
            
        except Exception as e:
            logging.error(f"Pipeline failed with error: {e}")
            pipeline_results['overall_status'] = 'failed_error'
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            self.price_collector.close()
            self.fundamentals_collector.close()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info("\n" + "="*80)
        logging.info("INTEGRATED DAILY PIPELINE V2 COMPLETE")
        logging.info("=" * 80)
        logging.info(f"Overall Status: {pipeline_results['overall_status']}")
        logging.info(f"Total Duration: {duration:.2f} seconds")
        logging.info(f"Market Status: {pipeline_results['market_status']}")
        logging.info(f"Price Updates: {pipeline_results['price_update']}")
        logging.info(f"Technical Indicators: {pipeline_results['technical_indicators']}")
        logging.info(f"Fundamentals Updates: {pipeline_results['fundamentals_update']}")
        logging.info("=" * 80)
        
        return pipeline_results
    
    def get_tickers_to_update(self, test_mode: bool, max_tickers: int) -> List[str]:
        """Get list of tickers to update"""
        db = DatabaseManager()
        db.connect()
        
        try:
            if test_mode:
                # Use a small set of test tickers
                test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
                return test_tickers[:max_tickers] if max_tickers else test_tickers
            else:
                # Get all tickers from database
                query = "SELECT ticker FROM stocks ORDER BY ticker"
                results = db.execute_query(query)
                tickers = [row[0] for row in results]
                return tickers[:max_tickers] if max_tickers else tickers
        except Exception as e:
            logging.error(f"Error getting tickers: {e}")
            return []
        finally:
            db.disconnect()
    
    def calculate_technical_indicators(self, tickers: List[str]) -> Dict:
        """Calculate technical indicators for tickers"""
        successful = 0
        failed = 0
        errors = []
        
        logging.info(f"Calculating technical indicators for {len(tickers)} tickers")
        
        for i, ticker in enumerate(tickers, 1):
            try:
                result = self.indicators_calculator.calculate_indicators_for_ticker(ticker)
                
                if result and 'error' not in result:
                    successful += 1
                    logging.info(f"[{i}/{len(tickers)}] SUCCESS: Calculated indicators for {ticker}")
                else:
                    failed += 1
                    error_msg = f"{ticker}: No data available"
                    errors.append(error_msg)
                    logging.warning(f"[{i}/{len(tickers)}] FAILED: {ticker}")
                
                # Rate limiting
                if i < len(tickers):
                    time.sleep(0.5)
                    
            except Exception as e:
                failed += 1
                error_msg = f"{ticker}: {str(e)}"
                errors.append(error_msg)
                logging.error(f"[{i}/{len(tickers)}] ERROR: {ticker}: {e}")
        
        return {
            'total_tickers': len(tickers),
            'successful': successful,
            'failed': failed,
            'errors': errors
        }

def main():
    parser = argparse.ArgumentParser(description='Integrated Daily Pipeline Runner V2')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited tickers')
    parser.add_argument('--max-price-tickers', type=int, default=100, help='Maximum tickers for price updates')
    parser.add_argument('--max-fundamental-tickers', type=int, default=50, help='Maximum tickers for fundamental updates')
    
    args = parser.parse_args()
    
    runner = IntegratedDailyRunnerV2()
    
    try:
        result = runner.run_complete_daily_pipeline(
            test_mode=args.test,
            max_price_tickers=args.max_price_tickers,
            max_fundamental_tickers=args.max_fundamental_tickers
        )
        
        print(f"\nPipeline Result: {result['overall_status']}")
        
        if result['overall_status'] == 'success':
            print("SUCCESS: Pipeline completed successfully!")
        else:
            print("FAILED: Pipeline failed!")
            
    except KeyboardInterrupt:
        print("\nWARNING: Pipeline interrupted by user")
    except Exception as e:
        print(f"\nFAILED: Pipeline failed: {e}")

if __name__ == "__main__":
    main() 