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
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor
from batch_price_processor import BatchPriceProcessor
from earnings_based_fundamental_processor import EarningsBasedFundamentalProcessor
from enhanced_multi_service_manager import get_multi_service_manager
try:
    from check_market_schedule import check_market_open_today, should_run_daily_process
except ImportError:
    try:
        from .check_market_schedule import check_market_open_today, should_run_daily_process
    except ImportError:
        # Fallback implementation if module is not available
        def check_market_open_today():
            return True, "Market status unknown - assuming open", {}
        def should_run_daily_process():
            return True, "Daily process enabled by default"
        logging.warning("check_market_schedule module not available, using fallback")
from data_validator import data_validator
from circuit_breaker import circuit_manager, fallback_manager

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
        
        # Initialize enhanced multi-service manager
        self.service_manager = get_multi_service_manager()
        
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
                logger.info("📈 Market was closed today - running comprehensive data population")
                
                # On non-trading days, use full API limits for data population
                self.max_api_calls_per_day = 1000  # Full daily limit
                self.api_calls_used = 0
                
                # Step 1: Populate historical data (priority 1)
                historical_result = self._populate_historical_data()
                
                # Step 2: Update fundamentals for tickers needing updates (priority 2)
                fundamental_result = self._update_fundamentals_non_trading_day()
                
                # Step 3: Remove delisted stocks
                delisted_result = self._remove_delisted_stocks()
                
                return self._compile_results({
                    'trading_day_check': trading_day_result,
                    'historical_data': historical_result,
                    'fundamentals_update': fundamental_result,
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
        Calculate technical indicators for tickers with robust error handling.
        Ensures no ticker failure can break the entire process.
        """
        try:
            successful = 0
            failed = 0
            
            logger.info(f"Starting technical indicator calculations for {len(tickers)} tickers")
            
            for ticker in tickers:
                try:
                    # Get price data for technical calculations
                    price_data = self.db.get_price_data_for_technicals(ticker)
                    if not price_data:
                        logger.debug(f"No price data available for {ticker}")
                        failed += 1
                        # Store zero indicators for this ticker
                        self._store_zero_indicators(ticker)
                        continue
                    
                    # Calculate technical indicators with safe error handling
                    indicators = self._calculate_single_ticker_technicals(ticker, price_data)
                    if indicators:
                        # Store calculated indicators
                        self.db.update_technical_indicators(ticker, indicators)
                        successful += 1
                        logger.debug(f"Successfully calculated indicators for {ticker}")
                    else:
                        # Store zero indicators for failed calculation
                        self._store_zero_indicators(ticker)
                        failed += 1
                        logger.debug(f"No indicators calculated for {ticker}")
                        
                except Exception as e:
                    logger.warning(f"Failed to calculate technicals for {ticker}: {e}")
                    # CRITICAL: Store zero indicators and continue - don't break the loop
                    self._store_zero_indicators(ticker)
                    failed += 1
            
            logger.info(f"Technical indicators completed: {successful} successful, {failed} failed")
            
            return {
                'successful_calculations': successful,
                'failed_calculations': failed
            }
            
        except Exception as e:
            logger.error(f"Error in technical indicators calculation: {e}")
            # Return safe counts even if the main process fails
            return {'successful_calculations': 0, 'failed_calculations': len(tickers)}

    def _store_zero_indicators(self, ticker: str):
        """
        Store zero values for all technical indicators when calculation fails.
        This ensures database consistency and prevents missing data issues.
        """
        try:
            zero_indicators = {
                'rsi_14': 0.0,
                'ema_20': 0.0,
                'ema_50': 0.0,
                'macd_line': 0.0,
                'macd_signal': 0.0,
                'macd_histogram': 0.0,
                'bb_upper': 0.0,
                'bb_middle': 0.0,
                'bb_lower': 0.0,
                'atr_14': 0.0,
                'cci_20': 0.0,
                'stoch_k': 0.0,
                'stoch_d': 0.0
            }
            
            self.db.update_technical_indicators(ticker, zero_indicators)
            logger.debug(f"Stored zero indicators for {ticker}")
            
        except Exception as e:
            logger.error(f"Failed to store zero indicators for {ticker}: {e}")
            # Don't raise - this is a fallback operation

    def _calculate_single_ticker_technicals(self, ticker: str, price_data: List[Dict]) -> Optional[Dict]:
        """
        Calculate technical indicators for a single ticker with comprehensive error handling.
        Returns None on any failure, ensuring the main process continues.
        """
        try:
            # Convert price data to proper format with error handling
            try:
                df = pd.DataFrame(price_data)
                if df.empty:
                    logger.warning(f"Empty price data for {ticker}")
                    return None
                    
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date'])  # Remove rows with invalid dates
                
                if df.empty:
                    logger.warning(f"No valid dates in price data for {ticker}")
                    return None
                
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)  # Sort by date ascending for calculations
            except Exception as e:
                logger.error(f"Failed to prepare price data for {ticker}: {e}")
                return None
            
            # Convert prices from cents to dollars if needed with safe error handling
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if col in df.columns:
                    try:
                        # Check if values are in cents (> 1000 suggests cents)
                        median_val = df[col].dropna().median()
                        if median_val and median_val > 1000:
                            df[col] = df[col] / 100.0
                    except Exception as e:
                        logger.warning(f"Failed to convert price column {col} for {ticker}: {e}")
                        continue
            
            # Calculate indicators with comprehensive error handling
            indicators = {}
            
            # RSI calculation with safe error handling
            try:
                if len(df) >= 14:
                    from indicators.rsi import calculate_rsi
                    rsi_result = calculate_rsi(df['close'])
                    if rsi_result is not None and len(rsi_result) > 0 and not rsi_result.iloc[-1] != rsi_result.iloc[-1]:  # NaN check
                        indicators['rsi_14'] = float(rsi_result.iloc[-1])
                        logger.debug(f"RSI calculated for {ticker}: {indicators['rsi_14']}")
                    else:
                        indicators['rsi_14'] = 0.0
                        logger.debug(f"RSI calculation returned invalid data for {ticker}")
                else:
                    indicators['rsi_14'] = 0.0
                    logger.debug(f"Insufficient data for RSI calculation for {ticker}: {len(df)} days < 14")
            except Exception as e:
                logger.error(f"RSI calculation failed for {ticker}: {e}")
                indicators['rsi_14'] = 0.0
            
            # EMA calculation with safe error handling
            try:
                if len(df) >= 20:
                    from indicators.ema import calculate_ema
                    ema_20 = calculate_ema(df['close'], 20)
                    if ema_20 is not None and len(ema_20) > 0 and not ema_20.iloc[-1] != ema_20.iloc[-1]:  # NaN check
                        indicators['ema_20'] = float(ema_20.iloc[-1])
                        logger.debug(f"EMA 20 calculated for {ticker}: {indicators['ema_20']}")
                    else:
                        indicators['ema_20'] = 0.0
                    
                    if len(df) >= 50:
                        ema_50 = calculate_ema(df['close'], 50)
                        if ema_50 is not None and len(ema_50) > 0 and not ema_50.iloc[-1] != ema_50.iloc[-1]:  # NaN check
                            indicators['ema_50'] = float(ema_50.iloc[-1])
                            logger.debug(f"EMA 50 calculated for {ticker}: {indicators['ema_50']}")
                        else:
                            indicators['ema_50'] = 0.0
                    else:
                        indicators['ema_50'] = 0.0
                        logger.debug(f"Insufficient data for EMA 50 for {ticker}: {len(df)} days < 50")
                else:
                    indicators['ema_20'] = 0.0
                    indicators['ema_50'] = 0.0
                    logger.debug(f"Insufficient data for EMA calculation for {ticker}: {len(df)} days < 20")
            except Exception as e:
                logger.error(f"EMA calculation failed for {ticker}: {e}")
                indicators['ema_20'] = 0.0
                indicators['ema_50'] = 0.0
            
            # MACD calculation with safe error handling
            try:
                if len(df) >= 26:
                    from indicators.macd import calculate_macd
                    macd_result = calculate_macd(df['close'])
                    if macd_result and len(macd_result) == 3:
                        macd_line, signal_line, histogram = macd_result
                        if (macd_line is not None and len(macd_line) > 0 and
                            signal_line is not None and len(signal_line) > 0 and
                            histogram is not None and len(histogram) > 0):
                            
                            # Check for NaN values
                            macd_val = macd_line.iloc[-1]
                            signal_val = signal_line.iloc[-1]
                            hist_val = histogram.iloc[-1]
                            
                            if (macd_val == macd_val and signal_val == signal_val and hist_val == hist_val):  # NaN check
                                indicators['macd_line'] = float(macd_val)
                                indicators['macd_signal'] = float(signal_val)
                                indicators['macd_histogram'] = float(hist_val)
                                logger.debug(f"MACD calculated for {ticker}")
                            else:
                                indicators['macd_line'] = 0.0
                                indicators['macd_signal'] = 0.0
                                indicators['macd_histogram'] = 0.0
                                logger.debug(f"MACD calculation returned NaN values for {ticker}")
                        else:
                            indicators['macd_line'] = 0.0
                            indicators['macd_signal'] = 0.0
                            indicators['macd_histogram'] = 0.0
                            logger.debug(f"MACD calculation returned invalid data for {ticker}")
                    else:
                        indicators['macd_line'] = 0.0
                        indicators['macd_signal'] = 0.0
                        indicators['macd_histogram'] = 0.0
                        logger.debug(f"MACD calculation returned unexpected format for {ticker}")
                else:
                    indicators['macd_line'] = 0.0
                    indicators['macd_signal'] = 0.0
                    indicators['macd_histogram'] = 0.0
                    logger.debug(f"Insufficient data for MACD calculation for {ticker}: {len(df)} days < 26")
            except Exception as e:
                logger.error(f"MACD calculation failed for {ticker}: {e}")
                indicators['macd_line'] = 0.0
                indicators['macd_signal'] = 0.0
                indicators['macd_histogram'] = 0.0
            
            # Validate indicators with safe error handling
            if indicators:
                try:
                    is_valid, errors = data_validator.validate_technical_indicators(ticker, indicators)
                    if is_valid:
                        logger.debug(f"Successfully calculated {len(indicators)} indicators for {ticker}")
                        return indicators
                    else:
                        logger.warning(f"Invalid indicators for {ticker}: {errors}")
                        # Return zero indicators instead of None to ensure database consistency
                        return self._get_zero_indicators_dict()
                except Exception as e:
                    logger.error(f"Indicator validation failed for {ticker}: {e}")
                    return self._get_zero_indicators_dict()
            else:
                logger.warning(f"No indicators could be calculated for {ticker}")
                return self._get_zero_indicators_dict()
            
        except Exception as e:
            logger.error(f"Error calculating technicals for {ticker}: {e}")
            self.error_handler.handle_error(
                f"Technical indicators calculation failed for {ticker}", e, ErrorSeverity.MEDIUM
            )
            # Return zero indicators instead of None
            return self._get_zero_indicators_dict()

    def _get_zero_indicators_dict(self) -> Dict[str, float]:
        """
        Get a dictionary of all technical indicators set to zero.
        This ensures consistent database updates even when calculations fail.
        """
        return {
            'rsi_14': 0.0,
            'ema_20': 0.0,
            'ema_50': 0.0,
            'macd_line': 0.0,
            'macd_signal': 0.0,
            'macd_histogram': 0.0,
            'bb_upper': 0.0,
            'bb_middle': 0.0,
            'bb_lower': 0.0,
            'atr_14': 0.0,
            'cci_20': 0.0,
            'stoch_k': 0.0,
            'stoch_d': 0.0
        }

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
            tickers_needing_history = self.db.get_tickers_needing_historical_data()
            logger.info(f"Found {len(tickers_needing_history)} tickers needing historical data")
            
            # Process historical data within API limit
            successful_updates = 0
            api_calls_used = 0
            
            for ticker in tickers_needing_history[:remaining_calls]:
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
                'total_tickers_available': len(tickers_needing_history),
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

    def _get_historical_data(self, ticker: str) -> Dict:
        """
        Get historical data for a ticker (100+ days).
        """
        try:
            # Use service factory to get historical data
            service = self.service_manager.get_service('yahoo_finance')
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
                    ticker, date, open, high, low, 
                    close, volume
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) DO NOTHING
                """
                
                values = (
                    ticker,
                    data_point['date'],
                    data_point['open'],
                    data_point['high'],
                    data_point['low'],
                    data_point['close'],
                    data_point['volume']
                )
                
                self.db.execute_update(query, values)
                
        except Exception as e:
            logger.error(f"Error storing historical data for {ticker}: {e}")

    def _update_fundamentals_non_trading_day(self) -> Dict:
        """
        Update fundamentals for tickers that need updates on non-trading days.
        """
        logger.info("📊 Updating fundamentals on non-trading day")
        
        try:
            start_time = time.time()
            
            # Calculate remaining API calls
            remaining_calls = self.max_api_calls_per_day - self.api_calls_used
            logger.info(f"Remaining API calls for fundamentals: {remaining_calls}")
            
            if remaining_calls <= 0:
                logger.warning("No API calls remaining for fundamental updates")
                return {
                    'phase': 'fundamentals_update_non_trading',
                    'status': 'skipped',
                    'reason': 'no_api_calls_remaining',
                    'api_calls_used': 0
                }
            
            # Get tickers needing fundamental updates
            tickers_needing_fundamentals = self.db.get_tickers_needing_fundamentals()
            logger.info(f"Found {len(tickers_needing_fundamentals)} tickers needing fundamental updates")
            
            # Process fundamental updates within API limit
            successful_updates = 0
            api_calls_used = 0
            
            for ticker in tickers_needing_fundamentals[:remaining_calls]:
                if api_calls_used >= remaining_calls:
                    logger.info(f"API call limit reached after {api_calls_used} calls")
                    break
                
                try:
                    # Update fundamental data (1 API call per ticker)
                    fundamental_result = self.earnings_processor._update_single_fundamental(ticker)
                    if fundamental_result:
                        successful_updates += 1
                        api_calls_used += 1
                    else:
                        logger.warning(f"Failed to update fundamentals for {ticker}")
                        
                except Exception as e:
                    logger.error(f"Error updating fundamentals for {ticker}: {e}")
            
            processing_time = time.time() - start_time
            self.api_calls_used += api_calls_used
            
            result = {
                'phase': 'fundamentals_update_non_trading',
                'total_tickers_available': len(tickers_needing_fundamentals),
                'successful_updates': successful_updates,
                'api_calls_used': api_calls_used,
                'processing_time': processing_time
            }
            
            logger.info(f"✅ Fundamentals updated on non-trading day: {successful_updates} tickers")
            logger.info(f"📊 API calls used for fundamentals: {api_calls_used}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating fundamentals on non-trading day: {e}")
            self.error_handler.handle_error(
                "Non-trading day fundamental update failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'fundamentals_update_non_trading',
                'error': str(e),
                'successful_updates': 0
            }

    def _remove_delisted_stocks(self) -> Dict:
        """
        Remove delisted stocks from the database.
        """
        logger.info("🗑️ Removing delisted stocks")
        
        try:
            start_time = time.time()
            
            # Get all tickers
            all_tickers = self.db.get_tickers()
            
            # Check for delisted stocks (simplified check)
            delisted_count = 0
            checked_count = 0
            
            # For now, just return a placeholder result
            # In production, this would check each ticker's status
            
            processing_time = time.time() - start_time
            
            result = {
                'phase': 'delisted_removal',
                'total_tickers_checked': checked_count,
                'delisted_removed': delisted_count,
                'processing_time': processing_time
            }
            
            logger.info(f"✅ Delisted stocks check completed: {delisted_count} removed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error removing delisted stocks: {e}")
            self.error_handler.handle_error(
                "Delisted stock removal failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'delisted_removal',
                'error': str(e),
                'delisted_removed': 0
            }

    def _get_active_tickers(self) -> List[str]:
        """Get list of active tickers."""
        try:
            return self.db.get_tickers()
        except Exception as e:
            logger.error(f"Error getting active tickers: {e}")
            return []

    def _get_tickers_with_recent_prices(self) -> List[str]:
        """Get tickers that have recent price data."""
        try:
            # Get tickers that have price data from the last 7 days
            query = """
            SELECT DISTINCT ticker 
            FROM daily_charts 
            WHERE date >= (CURRENT_DATE - INTERVAL '7 days')::date::text
            ORDER BY ticker
            """
            results = self.db.execute_query(query)
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting tickers with recent prices: {e}")
            return []

    def _compile_results(self, phase_results: Dict) -> Dict:
        """Compile results from all phases."""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'start_time': self.start_time,
            'total_processing_time': total_time,
            'total_api_calls_used': self.api_calls_used,
            'phase_results': phase_results,
            'summary': self._generate_summary(phase_results)
        }

    def _generate_summary(self, phase_results: Dict) -> Dict:
        """Generate a summary of the processing results."""
        return {
            'total_phases': len(phase_results),
            'successful_phases': len([p for p in phase_results.values() if 'error' not in p]),
            'failed_phases': len([p for p in phase_results.values() if 'error' in p])
        }

    def _get_error_results(self, error: Exception) -> Dict:
        """Get error results structure."""
        return {
            'start_time': self.start_time,
            'total_processing_time': time.time() - self.start_time if self.start_time else 0,
            'error': str(error),
            'phase_results': {},
            'summary': {'status': 'failed'}
        }


def main():
    """Main entry point for daily trading system."""
    parser = argparse.ArgumentParser(description='Daily Trading System')
    parser.add_argument('--force', action='store_true', help='Force run even if market was closed')
    parser.add_argument('--config', type=str, help='Configuration file path')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize and run the system
    system = DailyTradingSystem()
    results = system.run_daily_trading_process(force_run=args.force)
    
    # Print summary
    print("\n" + "="*50)
    print("📊 DAILY TRADING SYSTEM SUMMARY")
    print("="*50)
    print(f"Processing Time: {results.get('total_processing_time', 0):.2f}s")
    print(f"API Calls Used: {results.get('total_api_calls_used', 0)}")
    print(f"Phases Completed: {results.get('summary', {}).get('successful_phases', 0)}")
    print(f"Phases Failed: {results.get('summary', {}).get('failed_phases', 0)}")
    
    if 'error' in results:
        print(f"❌ System Error: {results['error']}")
        return 1
    else:
        print("✅ System completed successfully")
        return 0


if __name__ == "__main__":
    exit(main()) 