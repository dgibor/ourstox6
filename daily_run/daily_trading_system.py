"""
Daily Trading System

Comprehensive system that runs daily after market close to:
1. Check if it was a trading day
2. Update daily_charts with batch price commands (100 stocks per call)
3. Calculate fundamentals and technical indicators
4. Populate historical data with remaining API calls
5. Remove delisted stocks
"""

import logging
import time
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor
from batch_price_processor import BatchPriceProcessor
from earnings_based_fundamental_processor import EarningsBasedFundamentalProcessor
from enhanced_service_factory import EnhancedServiceFactory
from check_market_schedule import check_market_open_today, should_run_daily_process

logger = logging.getLogger(__name__)


class DailyTradingSystem:
    """
    Comprehensive daily trading system that handles all post-market operations.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.db = DatabaseManager()
        self.error_handler = ErrorHandler("daily_trading_system")
        self.monitoring = SystemMonitor()
        
        # Initialize processors
        self.batch_price_processor = BatchPriceProcessor(
            db=self.db,
            max_batch_size=100,  # 100 stocks per API call
            max_workers=5,
            delay_between_batches=1.0
        )
        
        self.earnings_processor = EarningsBasedFundamentalProcessor(
            db=self.db,
            max_workers=5,
            earnings_window_days=7
        )
        
        # Initialize service factory
        self.service_factory = EnhancedServiceFactory()
        
        # Performance tracking
        self.start_time = None
        self.metrics = {}
        self.api_calls_used = 0
        self.max_api_calls_per_day = 1000  # Conservative limit
        
    def run_daily_trading_process(self, force_run: bool = False) -> Dict:
        """
        Main entry point for daily trading process.
        
        Args:
            force_run: Force run even if market was closed
            
        Returns:
            Dictionary with complete processing results
        """
        self.start_time = time.time()
        logger.info("🚀 Starting Daily Trading System")
        
        try:
            # Step 1: Check if it was a trading day
            trading_day_result = self._check_trading_day(force_run)
            
            if not trading_day_result['was_trading_day'] and not force_run:
                logger.info("📈 Market was closed today - running historical data population only")
                historical_result = self._populate_historical_data()
                delisted_result = self._remove_delisted_stocks()
                
                return self._compile_results({
                    'trading_day_check': trading_day_result,
                    'historical_data': historical_result,
                    'delisted_removal': delisted_result
                })
            
            # Step 2: Update daily prices (only on trading days)
            price_result = self._update_daily_prices()
            
            # Step 3: Calculate fundamentals and technical indicators
            fundamental_result = self._calculate_fundamentals_and_technicals()
            
            # Step 4: Populate historical data with remaining API calls
            historical_result = self._populate_historical_data()
            
            # Step 5: Remove delisted stocks
            delisted_result = self._remove_delisted_stocks()
            
            # Compile final results
            results = self._compile_results({
                'trading_day_check': trading_day_result,
                'daily_prices': price_result,
                'fundamentals_technicals': fundamental_result,
                'historical_data': historical_result,
                'delisted_removal': delisted_result
            })
            
            logger.info("✅ Daily Trading System completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"❌ Daily trading process failed: {e}")
            self.error_handler.handle_error(
                "Daily trading process failed", e, ErrorSeverity.CRITICAL
            )
            return self._get_error_results(e)
    
    def _check_trading_day(self, force_run: bool = False) -> Dict:
        """
        Check if today was a trading day.
        
        Args:
            force_run: Force run even if market was closed
            
        Returns:
            Dictionary with trading day status
        """
        logger.info("📊 Checking if today was a trading day")
        
        try:
            if force_run:
                return {
                    'was_trading_day': True,
                    'reason': 'forced_run',
                    'market_details': None
                }
            
            # Check market schedule
            should_run, reason = should_run_daily_process()
            market_open, message, details = check_market_open_today()
            
            result = {
                'was_trading_day': market_open,
                'reason': reason,
                'market_details': details,
                'should_run': should_run
            }
            
            if market_open:
                logger.info(f"✅ Trading day confirmed: {message}")
            else:
                logger.info(f"❌ Not a trading day: {message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking trading day: {e}")
            return {
                'was_trading_day': False,
                'reason': 'error',
                'error': str(e)
            }
    
    def _update_daily_prices(self) -> Dict:
        """
        Update daily_charts table with latest prices using batch processing.
        """
        logger.info("💰 Updating daily prices with batch processing")
        
        try:
            start_time = time.time()
            
            # Get all active tickers
            tickers = self._get_active_tickers()
            logger.info(f"Processing {len(tickers)} active tickers")
            
            # Process batch prices (100 stocks per API call)
            price_data = self.batch_price_processor.process_batch_prices(tickers)
            
            processing_time = time.time() - start_time
            api_calls_used = (len(tickers) + 99) // 100  # 100 per call
            self.api_calls_used += api_calls_used
            
            result = {
                'phase': 'daily_price_update',
                'total_tickers': len(tickers),
                'successful_updates': len(price_data),
                'failed_updates': len(tickers) - len(price_data),
                'success_rate': len(price_data) / len(tickers) if tickers else 0,
                'processing_time': processing_time,
                'api_calls_used': api_calls_used,
                'data_stored_in': 'daily_charts'
            }
            
            logger.info(f"✅ Daily prices updated: {result['successful_updates']}/{result['total_tickers']} successful")
            logger.info(f"📊 API calls used: {api_calls_used}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating daily prices: {e}")
            self.error_handler.handle_error(
                "Daily price update failed", e, ErrorSeverity.HIGH
            )
            return {
                'phase': 'daily_price_update',
                'error': str(e),
                'successful_updates': 0,
                'failed_updates': 0
            }
    
    def _calculate_fundamentals_and_technicals(self) -> Dict:
        """
        Calculate fundamentals and technical indicators for all tickers.
        """
        logger.info("📈 Calculating fundamentals and technical indicators")
        
        try:
            start_time = time.time()
            
            # Get tickers with recent price data
            tickers = self._get_tickers_with_recent_prices()
            logger.info(f"Calculating for {len(tickers)} tickers with recent prices")
            
            # Calculate fundamentals (earnings-based)
            fundamental_result = self.earnings_processor.process_earnings_based_updates(tickers)
            
            # Calculate technical indicators
            technical_result = self._calculate_technical_indicators(tickers)
            
            processing_time = time.time() - start_time
            
            result = {
                'phase': 'fundamentals_and_technicals',
                'total_tickers': len(tickers),
                'fundamentals': {
                    'candidates': fundamental_result.get('candidates_found', 0),
                    'successful': fundamental_result.get('successful_updates', 0),
                    'failed': fundamental_result.get('failed_updates', 0)
                },
                'technicals': {
                    'successful': technical_result.get('successful_calculations', 0),
                    'failed': technical_result.get('failed_calculations', 0)
                },
                'processing_time': processing_time
            }
            
            logger.info(f"✅ Fundamentals and technicals calculated")
            logger.info(f"📊 Fundamentals: {result['fundamentals']['successful']} successful")
            logger.info(f"📊 Technicals: {result['technicals']['successful']} successful")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating fundamentals and technicals: {e}")
            self.error_handler.handle_error(
                "Fundamentals and technicals calculation failed", e, ErrorSeverity.HIGH
            )
            return {
                'phase': 'fundamentals_and_technicals',
                'error': str(e),
                'successful_updates': 0
            }
    
    def _calculate_technical_indicators(self, tickers: List[str]) -> Dict:
        """
        Calculate technical indicators for tickers.
        """
        try:
            successful = 0
            failed = 0
            
            for ticker in tickers:
                try:
                    # Get price data for technical calculations
                    price_data = self._get_price_data_for_technicals(ticker)
                    if not price_data:
                        failed += 1
                        continue
                    
                    # Calculate technical indicators
                    indicators = self._calculate_single_ticker_technicals(ticker, price_data)
                    if indicators:
                        self._store_technical_indicators(ticker, indicators)
                        successful += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to calculate technicals for {ticker}: {e}")
                    failed += 1
            
            return {
                'successful_calculations': successful,
                'failed_calculations': failed
            }
            
        except Exception as e:
            logger.error(f"Error in technical indicators calculation: {e}")
            return {'successful_calculations': 0, 'failed_calculations': len(tickers)}
    
    def _get_price_data_for_technicals(self, ticker: str) -> Optional[List]:
        """
        Get price data for technical indicator calculations.
        """
        try:
            query = """
            SELECT date, open_price, high_price, low_price, close_price, volume
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 100
            """
            results = self.db.execute_query(query, (ticker,))
            return results if results else None
            
        except Exception as e:
            logger.error(f"Error getting price data for {ticker}: {e}")
            return None
    
    def _calculate_single_ticker_technicals(self, ticker: str, price_data: List) -> Optional[Dict]:
        """
        Calculate technical indicators for a single ticker.
        """
        try:
            # Convert price data to proper format
            df = pd.DataFrame(price_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Convert prices from cents to dollars
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                df[col] = df[col] / 100.0
            
            # Calculate indicators (simplified version)
            indicators = {}
            
            # RSI
            if len(df) >= 14:
                try:
                    from indicators.rsi import calculate_rsi
                    indicators['rsi_14'] = calculate_rsi(df['close']).iloc[-1]
                except:
                    pass
            
            # EMA
            if len(df) >= 20:
                try:
                    from indicators.ema import calculate_ema
                    indicators['ema_20'] = calculate_ema(df['close'], 20).iloc[-1]
                    indicators['ema_50'] = calculate_ema(df['close'], 50).iloc[-1]
                except:
                    pass
            
            # MACD
            if len(df) >= 26:
                try:
                    from indicators.macd import calculate_macd
                    macd_line, signal_line, histogram = calculate_macd(df['close'])
                    indicators['macd_line'] = macd_line.iloc[-1]
                    indicators['macd_signal'] = signal_line.iloc[-1]
                    indicators['macd_histogram'] = histogram.iloc[-1]
                except:
                    pass
            
            return indicators if indicators else None
            
        except Exception as e:
            logger.error(f"Error calculating technicals for {ticker}: {e}")
            return None
    
    def _store_technical_indicators(self, ticker: str, indicators: Dict):
        """
        Store technical indicators in database.
        """
        try:
            # Update daily_charts table with technical indicators
            update_fields = []
            values = []
            
            for indicator, value in indicators.items():
                if value is not None:
                    update_fields.append(f"{indicator} = %s")
                    values.append(value)
            
            if update_fields:
                values.append(ticker)
                values.append(date.today())
                
                query = f"""
                UPDATE daily_charts 
                SET {', '.join(update_fields)}
                WHERE ticker = %s AND date = %s
                """
                
                self.db.execute_update(query, tuple(values))
                
        except Exception as e:
            logger.error(f"Error storing technical indicators for {ticker}: {e}")
    
    def _populate_historical_data(self) -> Dict:
        """
        Populate historical data with remaining API calls.
        """
        logger.info("📚 Populating historical data with remaining API calls")
        
        try:
            start_time = time.time()
            
            # Calculate remaining API calls
            remaining_calls = self.max_api_calls_per_day - self.api_calls_used
            logger.info(f"Remaining API calls: {remaining_calls}")
            
            if remaining_calls <= 0:
                logger.warning("No API calls remaining for historical data")
                return {
                    'phase': 'historical_data_population',
                    'status': 'skipped',
                    'reason': 'no_api_calls_remaining',
                    'api_calls_used': 0
                }
            
            # Get tickers needing historical data
            tickers_needing_history = self._get_tickers_needing_historical_data()
            logger.info(f"Found {len(tickers_needing_history)} tickers needing historical data")
            
            # Prioritize tickers with least historical data
            prioritized_tickers = self._prioritize_historical_tickers(tickers_needing_history)
            
            # Process historical data within API limit
            successful_updates = 0
            api_calls_used = 0
            
            for ticker in prioritized_tickers:
                if api_calls_used >= remaining_calls:
                    logger.info(f"API call limit reached after {api_calls_used} calls")
                    break
                
                try:
                    # Get historical data (100+ days)
                    historical_result = self._get_historical_data(ticker)
                    if historical_result['success']:
                        successful_updates += 1
                        api_calls_used += historical_result['api_calls']
                    else:
                        logger.warning(f"Failed to get historical data for {ticker}")
                        
                except Exception as e:
                    logger.error(f"Error getting historical data for {ticker}: {e}")
            
            processing_time = time.time() - start_time
            self.api_calls_used += api_calls_used
            
            result = {
                'phase': 'historical_data_population',
                'total_tickers_available': len(prioritized_tickers),
                'successful_updates': successful_updates,
                'api_calls_used': api_calls_used,
                'processing_time': processing_time
            }
            
            logger.info(f"✅ Historical data populated: {successful_updates} tickers updated")
            logger.info(f"📊 API calls used for history: {api_calls_used}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error populating historical data: {e}")
            self.error_handler.handle_error(
                "Historical data population failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'historical_data_population',
                'error': str(e),
                'successful_updates': 0
            }
    
    def _get_tickers_needing_historical_data(self) -> List[str]:
        """
        Get tickers that need historical data population.
        """
        try:
            # Get tickers with insufficient historical data
            query = """
            SELECT ticker FROM stocks 
            WHERE is_active = true 
            AND ticker IN (
                SELECT ticker FROM daily_charts 
                GROUP BY ticker 
                HAVING COUNT(*) < 100
            )
            ORDER BY ticker
            """
            results = self.db.execute_query(query)
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting tickers needing historical data: {e}")
            return []
    
    def _prioritize_historical_tickers(self, tickers: List[str]) -> List[str]:
        """
        Prioritize tickers based on amount of historical data.
        """
        try:
            prioritized = []
            
            for ticker in tickers:
                # Get current historical data count
                query = "SELECT COUNT(*) as count FROM daily_charts WHERE ticker = %s"
                result = self.db.execute_query(query, (ticker,))
                count = result[0][0] if result else 0
                
                # Prioritize tickers with least data
                prioritized.append((ticker, count))
            
            # Sort by data count (ascending)
            prioritized.sort(key=lambda x: x[1])
            return [ticker for ticker, count in prioritized]
            
        except Exception as e:
            logger.error(f"Error prioritizing historical tickers: {e}")
            return tickers
    
    def _get_historical_data(self, ticker: str) -> Dict:
        """
        Get historical data for a ticker (100+ days).
        """
        try:
            # Use service factory to get historical data
            service = self.service_factory.get_service('yahoo_finance')
            historical_data = service.get_historical_data(ticker, days=100)
            
            if historical_data:
                # Store historical data
                self._store_historical_data(ticker, historical_data)
                return {
                    'success': True,
                    'api_calls': 1,  # One API call per ticker
                    'data_points': len(historical_data)
                }
            else:
                return {
                    'success': False,
                    'api_calls': 1,
                    'data_points': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting historical data for {ticker}: {e}")
            return {
                'success': False,
                'api_calls': 1,
                'data_points': 0,
                'error': str(e)
            }
    
    def _store_historical_data(self, ticker: str, historical_data: List):
        """
        Store historical data in daily_charts table.
        """
        try:
            for data_point in historical_data:
                query = """
                INSERT INTO daily_charts (
                    ticker, date, open_price, high_price, low_price, 
                    close_price, volume, data_source, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (ticker, date) DO NOTHING
                """
                
                values = (
                    ticker,
                    data_point['date'],
                    data_point['open'],
                    data_point['high'],
                    data_point['low'],
                    data_point['close'],
                    data_point['volume'],
                    'historical_api'
                )
                
                self.db.execute_update(query, values)
                
        except Exception as e:
            logger.error(f"Error storing historical data for {ticker}: {e}")
    
    def _remove_delisted_stocks(self) -> Dict:
        """
        Remove delisted stocks from the database.
        """
        logger.info("🗑️ Removing delisted stocks")
        
        try:
            start_time = time.time()
            
            # Get all active tickers
            active_tickers = self._get_active_tickers()
            logger.info(f"Checking {len(active_tickers)} active tickers for delisting")
            
            delisted_tickers = []
            
            for ticker in active_tickers:
                try:
                    # Check if ticker is still valid
                    if self._is_ticker_delisted(ticker):
                        delisted_tickers.append(ticker)
                        
                except Exception as e:
                    logger.warning(f"Error checking delisting status for {ticker}: {e}")
            
            # Remove delisted tickers
            removed_count = 0
            for ticker in delisted_tickers:
                try:
                    self._remove_delisted_ticker(ticker)
                    removed_count += 1
                    logger.info(f"Removed delisted ticker: {ticker}")
                    
                except Exception as e:
                    logger.error(f"Error removing delisted ticker {ticker}: {e}")
            
            processing_time = time.time() - start_time
            
            result = {
                'phase': 'delisted_removal',
                'total_checked': len(active_tickers),
                'delisted_found': len(delisted_tickers),
                'successfully_removed': removed_count,
                'processing_time': processing_time
            }
            
            logger.info(f"✅ Delisted stocks removed: {removed_count} tickers")
            
            return result
            
        except Exception as e:
            logger.error(f"Error removing delisted stocks: {e}")
            self.error_handler.handle_error(
                "Delisted stock removal failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'delisted_removal',
                'error': str(e),
                'successfully_removed': 0
            }
    
    def _is_ticker_delisted(self, ticker: str) -> bool:
        """
        Check if a ticker is delisted.
        """
        try:
            # Try to get current price data
            service = self.service_factory.get_service('yahoo_finance')
            current_data = service.get_current_price(ticker)
            
            # If no data or price is 0, likely delisted
            if not current_data or current_data.get('price', 0) == 0:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking delisting for {ticker}: {e}")
            return False
    
    def _remove_delisted_ticker(self, ticker: str):
        """
        Remove a delisted ticker from the database.
        """
        try:
            # Mark as inactive in stocks table
            query = "UPDATE stocks SET is_active = false WHERE ticker = %s"
            self.db.execute_update(query, (ticker,))
            
            # Note: Keep historical data for reference
            
        except Exception as e:
            logger.error(f"Error removing delisted ticker {ticker}: {e}")
    
    def _get_active_tickers(self) -> List[str]:
        """
        Get list of active tickers from database.
        """
        try:
            return self.db.get_tickers('stocks', active_only=True)
        except Exception as e:
            logger.error(f"Error getting active tickers: {e}")
            return []
    
    def _get_tickers_with_recent_prices(self) -> List[str]:
        """
        Get tickers with recent price data.
        """
        try:
            today = date.today()
            query = """
            SELECT DISTINCT ticker FROM daily_charts 
            WHERE date = %s AND ticker IN (
                SELECT ticker FROM stocks WHERE is_active = true
            )
            """
            results = self.db.execute_query(query, (today,))
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting tickers with recent prices: {e}")
            return []
    
    def _compile_results(self, phase_results: Dict) -> Dict:
        """
        Compile final results from all phases.
        """
        total_time = time.time() - self.start_time
        
        results = {
            'system': 'daily_trading_system',
            'version': '1.0',
            'timestamp': datetime.now(),
            'total_processing_time': total_time,
            'total_api_calls_used': self.api_calls_used,
            'max_api_calls_per_day': self.max_api_calls_per_day,
            'api_calls_remaining': self.max_api_calls_per_day - self.api_calls_used,
            'phases': phase_results,
            'summary': self._generate_summary(phase_results)
        }
        
        return results
    
    def _generate_summary(self, phase_results: Dict) -> Dict:
        """
        Generate summary of all phases.
        """
        summary = {
            'trading_day': phase_results.get('trading_day_check', {}).get('was_trading_day', False),
            'daily_prices_updated': phase_results.get('daily_prices', {}).get('successful_updates', 0),
            'fundamentals_updated': phase_results.get('fundamentals_technicals', {}).get('fundamentals', {}).get('successful', 0),
            'technicals_calculated': phase_results.get('fundamentals_technicals', {}).get('technicals', {}).get('successful', 0),
            'historical_data_updated': phase_results.get('historical_data', {}).get('successful_updates', 0),
            'delisted_removed': phase_results.get('delisted_removal', {}).get('successfully_removed', 0)
        }
        
        return summary
    
    def _get_error_results(self, error: Exception) -> Dict:
        """
        Get error results when processing fails.
        """
        return {
            'system': 'daily_trading_system',
            'status': 'error',
            'error': str(error),
            'timestamp': datetime.now(),
            'total_processing_time': time.time() - self.start_time if self.start_time else 0
        }


def main():
    """Main entry point for daily trading system."""
    parser = argparse.ArgumentParser(description='Daily Trading System')
    parser.add_argument('--force', action='store_true', help='Force run even if market was closed')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/daily_trading.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Initialize and run system
    system = DailyTradingSystem()
    
    try:
        logger.info("🚀 Starting Daily Trading System")
        logger.info(f"Force run: {args.force}")
        logger.info(f"Test mode: {args.test}")
        
        # Run the daily trading process
        results = system.run_daily_trading_process(force_run=args.force)
        
        # Print summary
        print("\n" + "="*60)
        print("DAILY TRADING SYSTEM RESULTS")
        print("="*60)
        print(f"System: {results['system']} v{results['version']}")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Processing time: {results['total_processing_time']:.2f}s")
        print(f"API calls used: {results['total_api_calls_used']}/{results['max_api_calls_per_day']}")
        
        print(f"\nSUMMARY:")
        summary = results['summary']
        print(f"Trading day: {'Yes' if summary['trading_day'] else 'No'}")
        print(f"Daily prices updated: {summary['daily_prices_updated']}")
        print(f"Fundamentals updated: {summary['fundamentals_updated']}")
        print(f"Technicals calculated: {summary['technicals_calculated']}")
        print(f"Historical data updated: {summary['historical_data_updated']}")
        print(f"Delisted stocks removed: {summary['delisted_removed']}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"❌ Daily trading system failed: {e}")
        print(f"Error: {e}")
    finally:
        system.db.disconnect()


if __name__ == "__main__":
    main() 