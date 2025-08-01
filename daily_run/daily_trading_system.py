"""
Daily Trading System

Comprehensive system that runs daily after market close following this priority schema:

PRIORITY 1 (Most Important): 
- If it was a trading day: Get price data for all stocks, update daily_charts, calculate technical indicators
- If market was closed: Skip to Priority 2

PRIORITY 2: 
- Update fundamental information for companies with earnings announcements that day
- Calculate fundamental ratios based on updated stock prices

PRIORITY 3: 
- Update historical prices until at least 100 days of data for every company
- Uses remaining API calls after priorities 1 and 2

PRIORITY 4: 
- Fill missing fundamental data for companies
- Uses any remaining API calls after priorities 1, 2, and 3

The system respects API rate limits and prioritizes the most time-sensitive operations first.
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
        
        Follows the exact priority schema:
        1. (Most important) Get price data for trading day, calculate technical indicators (if trading day)
        2. Update fundamental information for companies with earnings announcements that day
        3. Update historical prices until at least 100 days of data for every company
        4. Fill missing fundamental data for companies
        
        Args:
            force_run: Force run even if market was closed
            
        Returns:
            Dictionary with complete processing results
        """
        self.start_time = time.time()
        logger.info("🚀 Starting Daily Trading System - Priority-Based Schema")
        logger.info("📋 STEP-BY-STEP EXECUTION LOG:")
        
        try:
            # Check if it was a trading day
            logger.info("🔍 STEP 1: Checking if today was a trading day...")
            trading_day_result = self._check_trading_day(force_run)
            logger.info(f"✅ Trading day check completed: {trading_day_result['was_trading_day']}")
            
            # PRIORITY 1: Get price data for trading day, calculate technical indicators
            if trading_day_result['was_trading_day'] or force_run:
                logger.info("📈 PRIORITY 1: Processing trading day - updating prices and technical indicators")
                logger.info("💰 STEP 2: Starting stock price updates...")
                
                # Step 1a: Update daily prices for all stocks
                price_result = self._update_daily_prices()
                logger.info("✅ Stock price updates completed")
                
                logger.info("📈 STEP 3: Starting technical indicator calculations...")
                # Step 1b: Calculate technical indicators based on updated prices
                technical_result = self._calculate_technical_indicators_priority1()
                logger.info("✅ Technical indicator calculations completed")
                
                priority1_result = {
                    'daily_prices': price_result,
                    'technical_indicators': technical_result
                }
            else:
                logger.info("📈 PRIORITY 1: Market was closed - skipping to Priority 2")
                priority1_result = {
                    'status': 'skipped',
                    'reason': 'market_closed'
                }
            
            # PRIORITY 2: Update fundamental information for companies with earnings announcements
            logger.info("📊 PRIORITY 2: Updating fundamentals for companies with earnings announcements")
            logger.info("📊 STEP 4: Starting earnings-based fundamental updates...")
            earnings_fundamentals_result = self._update_earnings_announcement_fundamentals()
            logger.info("✅ Earnings-based fundamental updates completed")
            
            # PRIORITY 3: Update historical prices until 100+ days for every company
            logger.info("📚 PRIORITY 3: Updating historical prices (100+ days minimum)")
            logger.info("📚 STEP 5: Starting historical data updates...")
            historical_result = self._ensure_minimum_historical_data()
            logger.info("✅ Historical data updates completed")
            
            # PRIORITY 4: Fill missing fundamental data for companies
            logger.info("🔍 PRIORITY 4: Filling missing fundamental data")
            logger.info("🔍 STEP 6: Starting missing fundamental data fill...")
            missing_fundamentals_result = self._fill_missing_fundamental_data()
            logger.info("✅ Missing fundamental data fill completed")
            
            # Cleanup: Remove delisted stocks to prevent future API errors
            logger.info("🧹 STEP 7: Starting cleanup of delisted stocks...")
            cleanup_result = self._cleanup_delisted_stocks()
            logger.info("✅ Cleanup of delisted stocks completed")
            
            # Compile final results
            logger.info("📊 STEP 8: Compiling final results...")
            results = self._compile_results({
                'trading_day_check': trading_day_result,
                'priority_1_trading_day': priority1_result,
                'priority_2_earnings_fundamentals': earnings_fundamentals_result,
                'priority_3_historical_data': historical_result,
                'priority_4_missing_fundamentals': missing_fundamentals_result,
                'cleanup_delisted_stocks': cleanup_result
            })
            
            logger.info("✅ Daily Trading System completed successfully - All priorities processed")
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

    def _get_tickers_needing_price_updates(self) -> List[str]:
        """Get tickers that don't have today's price data"""
        try:
            query = """
            SELECT s.ticker 
            FROM stocks s
            LEFT JOIN daily_charts dc ON s.ticker = dc.ticker 
                AND dc.date = CURRENT_DATE::date
            WHERE s.ticker IS NOT NULL
                AND dc.ticker IS NULL
            """
            results = self.db.execute_query(query)
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting tickers needing price updates: {e}")
            # Fallback to all active tickers if query fails
            return self._get_active_tickers()

    def _update_daily_prices(self) -> Dict:
        """
        Update daily_charts table with latest prices using batch processing.
        Only processes tickers that don't already have today's data.
        """
        logger.info("💰 Updating daily prices with batch processing")
        
        try:
            start_time = time.time()
            
            # Get only tickers that need price updates
            tickers_needing_updates = self._get_tickers_needing_price_updates()
            logger.info(f"Processing {len(tickers_needing_updates)} tickers needing price updates")
            
            if not tickers_needing_updates:
                logger.info("✅ All tickers already have today's price data - skipping price updates")
                return {
                    'phase': 'daily_price_update',
                    'status': 'skipped',
                    'reason': 'all_tickers_up_to_date',
                    'total_tickers': 0,
                    'successful_updates': 0,
                    'failed_updates': 0,
                    'processing_time': time.time() - start_time,
                    'api_calls_used': 0,
                    'data_stored_in': 'daily_charts'
                }
            
            # Process batch prices (100 stocks per API call)
            price_data = self.batch_price_processor.process_batch_prices(tickers_needing_updates)
            
            processing_time = time.time() - start_time
            api_calls_used = (len(tickers_needing_updates) + 99) // 100  # 100 per call
            self.api_calls_used += api_calls_used
            
            result = {
                'phase': 'daily_price_update',
                'total_tickers': len(tickers_needing_updates),
                'successful_updates': len(price_data),
                'failed_updates': len(tickers_needing_updates) - len(price_data),
                'success_rate': len(price_data) / len(tickers_needing_updates) if tickers_needing_updates else 0,
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

    def _calculate_technical_indicators_priority1(self) -> Dict:
        """
        PRIORITY 1: Calculate technical indicators based on updated price data.
        This is called immediately after price updates on trading days.
        """
        logger.info("📈 PRIORITY 1: Calculating technical indicators for all stocks")
        
        try:
            start_time = time.time()
            
            # Get all active tickers (since we just updated prices for all)
            tickers = self._get_active_tickers()
            logger.info(f"Calculating technical indicators for {len(tickers)} tickers")
            
            # Calculate technical indicators for all tickers
            technical_result = self._calculate_technical_indicators(tickers)
            
            processing_time = time.time() - start_time
            
            result = {
                'phase': 'priority_1_technical_indicators',
                'total_tickers': len(tickers),
                'successful_calculations': technical_result.get('successful_calculations', 0),
                'failed_calculations': technical_result.get('failed_calculations', 0),
                'historical_fetches': technical_result.get('historical_fetches', 0),
                'processing_time': processing_time
            }
            
            logger.info(f"✅ PRIORITY 1: Technical indicators completed - {result['successful_calculations']}/{result['total_tickers']} successful")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Priority 1 technical indicators: {e}")
            self.error_handler.handle_error(
                "Priority 1 technical indicators failed", e, ErrorSeverity.HIGH
            )
            return {
                'phase': 'priority_1_technical_indicators',
                'error': str(e),
                'successful_calculations': 0,
                'failed_calculations': 0
            }

    def _update_earnings_announcement_fundamentals(self) -> Dict:
        """
        PRIORITY 2: Update fundamental information for companies with earnings announcements that day.
        Calculate fundamental ratios based on updated stock prices.
        """
        logger.info("📊 PRIORITY 2: Processing earnings announcements and fundamental updates")
        
        try:
            start_time = time.time()
            
            # Get companies with earnings announcements today
            earnings_tickers = self._get_earnings_announcement_tickers()
            logger.info(f"Found {len(earnings_tickers)} companies with earnings announcements")
            
            if not earnings_tickers:
                logger.info("No earnings announcements today - skipping fundamental updates")
                return {
                    'phase': 'priority_2_earnings_fundamentals',
                    'status': 'skipped',
                    'reason': 'no_earnings_announcements',
                    'processing_time': time.time() - start_time
                }
            
            # Update fundamental data for earnings announcement companies
            successful_updates = 0
            failed_updates = 0
            api_calls_used = 0
            
            for ticker in earnings_tickers:
                if self.api_calls_used >= self.max_api_calls_per_day:
                    logger.warning(f"API call limit reached after processing {successful_updates} earnings tickers")
                    break
                
                try:
                    # Update fundamental data
                    fundamental_success = self._update_single_ticker_fundamentals(ticker)
                    
                    if fundamental_success:
                        # Calculate fundamental ratios based on updated price
                        self._calculate_fundamental_ratios(ticker)
                        successful_updates += 1
                        api_calls_used += 1
                        logger.debug(f"Updated fundamentals and ratios for {ticker}")
                    else:
                        failed_updates += 1
                        logger.warning(f"Failed to update fundamentals for {ticker}")
                        
                except Exception as e:
                    logger.error(f"Error updating earnings fundamentals for {ticker}: {e}")
                    failed_updates += 1
            
            self.api_calls_used += api_calls_used
            processing_time = time.time() - start_time
            
            result = {
                'phase': 'priority_2_earnings_fundamentals',
                'earnings_announcements_found': len(earnings_tickers),
                'successful_updates': successful_updates,
                'failed_updates': failed_updates,
                'api_calls_used': api_calls_used,
                'processing_time': processing_time
            }
            
            logger.info(f"✅ PRIORITY 2: Earnings fundamentals completed - {successful_updates}/{len(earnings_tickers)} successful")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Priority 2 earnings fundamentals: {e}")
            self.error_handler.handle_error(
                "Priority 2 earnings fundamentals failed", e, ErrorSeverity.HIGH
            )
            return {
                'phase': 'priority_2_earnings_fundamentals',
                'error': str(e),
                'successful_updates': 0,
                'failed_updates': 0
            }

    def _ensure_minimum_historical_data(self) -> Dict:
        """
        PRIORITY 3: Update historical prices until at least 100 days of data for every company.
        Uses remaining API calls after priorities 1 and 2 with optimized batch processing.
        """
        logger.info("📚 PRIORITY 3: Ensuring minimum 100 days of historical data")
        
        try:
            start_time = time.time()
            
            # Calculate remaining API calls
            remaining_calls = self.max_api_calls_per_day - self.api_calls_used
            logger.info(f"Remaining API calls for historical data: {remaining_calls}")
            
            if remaining_calls <= 0:
                logger.warning("No API calls remaining for historical data")
                return {
                    'phase': 'priority_3_historical_data',
                    'status': 'skipped',
                    'reason': 'no_api_calls_remaining',
                    'processing_time': time.time() - start_time
                }
            
            # Get tickers that need historical data to reach 100+ days
            tickers_needing_history = self._get_tickers_needing_100_days_history()
            logger.info(f"Found {len(tickers_needing_history)} tickers needing historical data")
            
            # Optimize processing based on available API calls
            successful_updates = 0
            failed_updates = 0
            api_calls_used = 0
            
            # Process tickers in batches to optimize API usage
            batch_size = min(50, remaining_calls)  # Process up to 50 tickers at once
            ticker_batches = [tickers_needing_history[i:i + batch_size] 
                            for i in range(0, len(tickers_needing_history), batch_size)]
            
            for batch_num, ticker_batch in enumerate(ticker_batches):
                if api_calls_used >= remaining_calls:
                    logger.info(f"API call limit reached after {api_calls_used} calls")
                    break
                
                logger.info(f"Processing historical data batch {batch_num + 1}/{len(ticker_batches)} ({len(ticker_batch)} tickers)")
                
                for ticker in ticker_batch:
                    if api_calls_used >= remaining_calls:
                        break
                    
                    try:
                        # Get historical data to ensure 100+ days
                        history_result = self._get_historical_data_to_minimum(ticker, min_days=100)
                        if history_result['success']:
                            successful_updates += 1
                            api_calls_used += history_result['api_calls']
                            logger.debug(f"Updated historical data for {ticker} - {history_result['days_added']} days added ({history_result.get('reason', 'unknown')})")
                        else:
                            failed_updates += 1
                            logger.debug(f"Failed to get historical data for {ticker}: {history_result.get('error', 'unknown error')}")
                            
                    except Exception as e:
                        logger.error(f"Error getting historical data for {ticker}: {e}")
                        failed_updates += 1
                        api_calls_used += 1  # Count failed attempts
                
                # Add small delay between batches to avoid rate limiting
                if batch_num < len(ticker_batches) - 1 and api_calls_used < remaining_calls:
                    time.sleep(0.5)
            
            self.api_calls_used += api_calls_used
            processing_time = time.time() - start_time
            
            result = {
                'phase': 'priority_3_historical_data',
                'tickers_needing_history': len(tickers_needing_history),
                'successful_updates': successful_updates,
                'failed_updates': failed_updates,
                'api_calls_used': api_calls_used,
                'processing_time': processing_time,
                'batches_processed': len(ticker_batches)
            }
            
            logger.info(f"✅ PRIORITY 3: Historical data completed - {successful_updates} tickers updated")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Priority 3 historical data: {e}")
            self.error_handler.handle_error(
                "Priority 3 historical data failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'priority_3_historical_data',
                'error': str(e),
                'successful_updates': 0,
                'failed_updates': 0
            }

    def _fill_missing_fundamental_data(self) -> Dict:
        """
        PRIORITY 4: Fill missing fundamental data for companies.
        Uses any remaining API calls after priorities 1, 2, and 3.
        """
        logger.info("🔍 PRIORITY 4: Filling missing fundamental data")
        
        try:
            start_time = time.time()
            
            # Calculate remaining API calls
            remaining_calls = self.max_api_calls_per_day - self.api_calls_used
            logger.info(f"Remaining API calls for missing fundamentals: {remaining_calls}")
            
            if remaining_calls <= 0:
                logger.warning("No API calls remaining for missing fundamentals")
                return {
                    'phase': 'priority_4_missing_fundamentals',
                    'status': 'skipped',
                    'reason': 'no_api_calls_remaining',
                    'processing_time': time.time() - start_time
                }
            
            # Get tickers with missing fundamental data
            tickers_missing_fundamentals = self._get_tickers_missing_fundamental_data()
            logger.info(f"Found {len(tickers_missing_fundamentals)} tickers with missing fundamental data")
            
            # Process missing fundamentals within API limit
            successful_updates = 0
            failed_updates = 0
            api_calls_used = 0
            
            for ticker in tickers_missing_fundamentals:
                if api_calls_used >= remaining_calls:
                    logger.info(f"API call limit reached after {api_calls_used} calls")
                    break
                
                try:
                    # Fill missing fundamental data
                    fundamental_success = self._update_single_ticker_fundamentals(ticker)
                    
                    if fundamental_success:
                        # Calculate ratios for newly filled data
                        self._calculate_fundamental_ratios(ticker)
                        successful_updates += 1
                        api_calls_used += 1
                        logger.debug(f"Filled missing fundamentals for {ticker}")
                    else:
                        failed_updates += 1
                        logger.warning(f"Failed to fill fundamentals for {ticker}")
                        
                except Exception as e:
                    logger.error(f"Error filling fundamentals for {ticker}: {e}")
                    failed_updates += 1
            
            self.api_calls_used += api_calls_used
            processing_time = time.time() - start_time
            
            result = {
                'phase': 'priority_4_missing_fundamentals',
                'tickers_missing_data': len(tickers_missing_fundamentals),
                'successful_updates': successful_updates,
                'failed_updates': failed_updates,
                'api_calls_used': api_calls_used,
                'processing_time': processing_time
            }
            
            logger.info(f"✅ PRIORITY 4: Missing fundamentals completed - {successful_updates} tickers updated")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Priority 4 missing fundamentals: {e}")
            self.error_handler.handle_error(
                "Priority 4 missing fundamentals failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'priority_4_missing_fundamentals',
                'error': str(e),
                'successful_updates': 0,
                'failed_updates': 0
            }

    def _calculate_technical_indicators(self, tickers: List[str]) -> Dict:
        """
        Calculate technical indicators for tickers with robust error handling.
        Fetches historical data when needed to ensure sufficient data for calculations.
        """
        try:
            successful = 0
            failed = 0
            historical_fetches = 0
            
            logger.info(f"Starting technical indicator calculations for {len(tickers)} tickers")
            
            for ticker in tickers:
                try:
                    # Get price data for technical calculations
                    price_data = self.db.get_price_data_for_technicals(ticker)
                    
                    # Check if we have enough data for technical indicators (minimum 100 days for reliable calculations)
                    if not price_data or len(price_data) < 100:
                        # Check if we have enough API calls remaining for historical data
                        remaining_calls = self.max_api_calls_per_day - self.api_calls_used
                        if remaining_calls > 0:
                            logger.info(f"Insufficient data for {ticker}: {len(price_data) if price_data else 0} days, fetching historical data (API calls remaining: {remaining_calls})")
                            
                            # Fetch historical data to ensure minimum 200 days for better reliability
                            historical_result = self._get_historical_data_to_minimum(ticker, min_days=200)
                            if historical_result.get('success'):
                                historical_fetches += 1
                                # Get updated price data after fetching historical data
                                price_data = self.db.get_price_data_for_technicals(ticker)
                                logger.info(f"Fetched historical data for {ticker}: now have {len(price_data) if price_data else 0} days")
                            else:
                                logger.warning(f"Failed to fetch historical data for {ticker}")
                        else:
                            logger.warning(f"Insufficient data for {ticker} but no API calls remaining for historical fetch")
                    
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
            
            logger.info(f"Technical indicators completed: {successful} successful, {failed} failed, {historical_fetches} historical fetches")
            
            return {
                'successful_calculations': successful,
                'failed_calculations': failed,
                'historical_fetches': historical_fetches
            }
            
        except Exception as e:
            logger.error(f"Error in technical indicators calculation: {e}")
            # Return safe counts even if the main process fails
            return {'successful_calculations': 0, 'failed_calculations': len(tickers), 'historical_fetches': 0}

    def _cleanup_delisted_stocks(self) -> Dict:
        """
        Clean up delisted stocks that are causing API errors.
        This helps reduce wasted API calls on non-existent stocks.
        """
        logger.info("🧹 Cleaning up delisted stocks")
        
        try:
            start_time = time.time()
            
            # Get list of stocks that consistently fail
            delisted_candidates = [
                'PLT', 'REP', 'SBA', 'SCG', 'SDE', 'SOUP', 'STO', 'SYNC', 'TCB', 
                'TES', 'TEV', 'TIF', 'TII', 'TOT', 'TXR', 'ZA', 'ZE', 'BRK.B', 'SNE'
            ]
            
            removed_count = 0
            for ticker in delisted_candidates:
                try:
                    # Check if ticker exists in stocks table
                    query = "SELECT COUNT(*) FROM stocks WHERE ticker = %s"
                    result = self.db.fetch_one(query, (ticker,))
                    
                    if result and result[0] > 0:
                        # Remove from stocks table
                        delete_query = "DELETE FROM stocks WHERE ticker = %s"
                        self.db.execute_update(delete_query, (ticker,))
                        
                        # Remove from daily_charts table
                        delete_charts_query = "DELETE FROM daily_charts WHERE ticker = %s"
                        self.db.execute_update(delete_charts_query, (ticker,))
                        
                        logger.info(f"Removed delisted stock: {ticker}")
                        removed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error removing delisted stock {ticker}: {e}")
                    continue
            
            result = {
                'phase': 'cleanup_delisted_stocks',
                'candidates_checked': len(delisted_candidates),
                'removed_count': removed_count,
                'processing_time': time.time() - start_time
            }
            
            logger.info(f"✅ Cleanup completed - {removed_count} delisted stocks removed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in delisted stocks cleanup: {e}")
            self.error_handler.handle_error(
                "Delisted stocks cleanup failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'cleanup_delisted_stocks',
                'error': str(e),
                'removed_count': 0
            }

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
        Calculate ALL technical indicators for a single ticker using comprehensive calculator.
        Returns comprehensive dictionary with all calculated indicators.
        """
        start_time = time.time()
        
        try:
            # Import the comprehensive calculator
            import sys
            sys.path.append('utility_functions')
            from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator
            
            # Create calculator instance
            calculator = ComprehensiveTechnicalCalculator()
            
            # Calculate all indicators
            indicators = calculator.calculate_all_indicators(ticker, price_data)
            
            calculation_time = time.time() - start_time
            
            if indicators:
                logger.info(f"Calculated {len(indicators)} technical indicators for {ticker} in {calculation_time:.2f}s")
                
                # Monitor performance and alert on slow calculations
                if calculation_time > 5.0:  # Alert if calculation takes > 5 seconds
                    logger.warning(f"Slow calculation for {ticker}: {calculation_time:.2f}s")
                elif calculation_time > 10.0:  # Critical alert if > 10 seconds
                    logger.error(f"Critical slow calculation for {ticker}: {calculation_time:.2f}s")
                
                # Track performance metrics
                self.metrics[f'{ticker}_calculation_time'] = calculation_time
                self.metrics[f'{ticker}_indicators_calculated'] = len(indicators)
                
                return indicators
            else:
                logger.warning(f"No technical indicators calculated for {ticker} in {calculation_time:.2f}s")
                return None
                
        except Exception as e:
            calculation_time = time.time() - start_time
            logger.error(f"Error calculating technical indicators for {ticker} after {calculation_time:.2f}s: {e}")
            return None

    def _get_zero_indicators_dict(self) -> Dict[str, float]:
        """
        Get a dictionary of all technical indicators set to zero.
        This ensures consistent database updates even when calculations fail.
        """
        try:
            # Import the comprehensive calculator to get all indicator names
            import sys
            sys.path.append('utility_functions')
            from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator
            
            calculator = ComprehensiveTechnicalCalculator()
            all_indicators = calculator.get_all_indicator_names()
            
            # Create zero dictionary for all indicators
            return {indicator: 0.0 for indicator in all_indicators}
            
        except Exception as e:
            logger.error(f"Error getting zero indicators dictionary: {e}")
            # Fallback to basic indicators if import fails
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

    def get_technical_data_quality_score(self, ticker: str) -> float:
        """
        Calculate technical data quality score (0-1) based on ALL indicator completeness and validity.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Quality score between 0 and 1
        """
        try:
            # Import the comprehensive calculator to get all indicator names
            import sys
            sys.path.append('utility_functions')
            from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator
            
            calculator = ComprehensiveTechnicalCalculator()
            all_indicators = calculator.get_all_indicator_names()
            
            # Build dynamic query for all indicators
            indicator_list = ', '.join(all_indicators)
            query = f"""
            SELECT {indicator_list}
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            
            result = self.db.fetch_one(query, (ticker,))
            if not result:
                return 0.0
            
            # Count valid indicators (non-zero, non-null values)
            valid_count = 0
            total_indicators = len(result)
            
            for value in result:
                if value is not None and value != 0 and not pd.isna(value):
                    valid_count += 1
            
            quality_score = valid_count / total_indicators if total_indicators > 0 else 0.0
            
            logger.debug(f"Technical data quality score for {ticker}: {quality_score:.2f} ({valid_count}/{total_indicators} valid)")
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating technical data quality score for {ticker}: {e}")
            # Fallback to basic indicators if import fails
            try:
                fallback_query = """
                SELECT rsi_14, ema_20, ema_50, macd_line, macd_signal, macd_histogram,
                       bb_upper, bb_middle, bb_lower, atr_14, cci_20, stoch_k, stoch_d
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
                """
                
                result = self.db.fetch_one(fallback_query, (ticker,))
                if not result:
                    return 0.0
                
                valid_count = sum(1 for value in result if value is not None and value != 0 and not pd.isna(value))
                total_indicators = len(result)
                
                return valid_count / total_indicators if total_indicators > 0 else 0.0
                
            except Exception as fallback_error:
                logger.error(f"Fallback quality score calculation failed for {ticker}: {fallback_error}")
                return 0.0

    def get_technical_data_quality_summary(self) -> Dict[str, Any]:
        """
        Get a summary of technical data quality across all tickers based on ALL indicators.
        
        Returns:
            Dictionary with quality statistics
        """
        try:
            # Import the comprehensive calculator to get all indicator names
            import sys
            sys.path.append('utility_functions')
            from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator
            
            calculator = ComprehensiveTechnicalCalculator()
            all_indicators = calculator.get_all_indicator_names()
            
            # Build dynamic query for all indicators
            indicator_checks = []
            for indicator in all_indicators:
                indicator_checks.append(f"COUNT(CASE WHEN {indicator} > 0 THEN 1 END) as {indicator}_valid")
            
            indicator_list = ', '.join(indicator_checks)
            query = f"""
            SELECT ticker, {indicator_list}, COUNT(*) as total_records
            FROM daily_charts 
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY ticker
            """
            
            results = self.db.execute_query(query)
            if not results:
                return {'total_tickers': 0, 'average_quality': 0.0}
            
            quality_scores = []
            for row in results:
                ticker = row[0]
                total_records = row[-1]  # Last column is total_records
                indicator_values = row[1:-1]  # All columns except ticker and total_records
                
                if total_records > 0:
                    # Calculate quality score for this ticker
                    valid_indicators = sum(indicator_values)
                    quality_score = valid_indicators / (total_records * len(all_indicators))
                    quality_scores.append(quality_score)
            
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                high_quality_count = sum(1 for score in quality_scores if score >= 0.8)
                low_quality_count = sum(1 for score in quality_scores if score < 0.5)
                
                return {
                    'total_tickers': len(quality_scores),
                    'average_quality': avg_quality,
                    'high_quality_count': high_quality_count,
                    'low_quality_count': low_quality_count,
                    'quality_distribution': {
                        'excellent': sum(1 for score in quality_scores if score >= 0.9),
                        'good': sum(1 for score in quality_scores if 0.7 <= score < 0.9),
                        'fair': sum(1 for score in quality_scores if 0.5 <= score < 0.7),
                        'poor': sum(1 for score in quality_scores if score < 0.5)
                    }
                }
            else:
                return {'total_tickers': 0, 'average_quality': 0.0}
                
        except Exception as e:
            logger.error(f"Error calculating technical data quality summary: {e}")
            # Fallback to basic indicators if import fails
            try:
                fallback_query = """
                SELECT ticker, 
                       COUNT(CASE WHEN rsi_14 > 0 THEN 1 END) as rsi_valid,
                       COUNT(CASE WHEN ema_20 > 0 THEN 1 END) as ema_20_valid,
                       COUNT(CASE WHEN ema_50 > 0 THEN 1 END) as ema_50_valid,
                       COUNT(CASE WHEN macd_line != 0 THEN 1 END) as macd_valid,
                       COUNT(*) as total_records
                FROM daily_charts 
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY ticker
                """
                
                results = self.db.execute_query(fallback_query)
                if not results:
                    return {'total_tickers': 0, 'average_quality': 0.0}
                
                quality_scores = []
                for row in results:
                    ticker, rsi_valid, ema_20_valid, ema_50_valid, macd_valid, total_records = row
                    
                    if total_records > 0:
                        valid_indicators = sum([rsi_valid, ema_20_valid, ema_50_valid, macd_valid])
                        quality_score = valid_indicators / (total_records * 4)
                        quality_scores.append(quality_score)
                
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    return {
                        'total_tickers': len(quality_scores),
                        'average_quality': avg_quality,
                        'note': 'Fallback calculation using basic indicators only'
                    }
                else:
                    return {'total_tickers': 0, 'average_quality': 0.0}
                    
            except Exception as fallback_error:
                logger.error(f"Fallback quality summary calculation failed: {fallback_error}")
                return {'total_tickers': 0, 'average_quality': 0.0, 'error': str(e)}

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
                        logger.debug(f"Failed to get historical data for {ticker}")
                        
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

    def _get_earnings_announcement_tickers(self) -> List[str]:
        """
        Get tickers that have earnings announcements today.
        This should check earnings calendar data.
        """
        try:
            # First, try to get earnings announcements from earnings calendar
            if hasattr(self, 'earnings_calendar') and self.earnings_calendar:
                try:
                    today = date.today().strftime('%Y-%m-%d')
                    earnings_today = self.earnings_calendar.get_earnings_for_date(today)
                    if earnings_today:
                        return [ticker for ticker in earnings_today if ticker]
                except Exception as e:
                    logger.warning(f"Error getting earnings from calendar service: {e}")
            
            # Fallback: Check earnings_calendar table if it exists
            try:
                query = """
                SELECT DISTINCT ticker 
                FROM earnings_calendar 
                WHERE earnings_date = CURRENT_DATE 
                AND ticker IS NOT NULL
                ORDER BY ticker
                """
                results = self.db.execute_query(query)
                tickers = [row[0] for row in results]
                if tickers:
                    logger.info(f"Found {len(tickers)} earnings announcements in database")
                    return tickers
            except Exception as e:
                logger.debug(f"No earnings_calendar table or error: {e}")
            
            # Final fallback: Return empty list (no earnings announcements)
            logger.info("No earnings announcements found for today")
            return []
            
        except Exception as e:
            logger.error(f"Error getting earnings announcement tickers: {e}")
            return []

    def _get_tickers_needing_100_days_history(self) -> List[str]:
        """
        Get tickers that need historical data to reach at least 100 days.
        """
        try:
            query = """
            SELECT 
                s.ticker,
                COUNT(dc.date) as current_days
            FROM stocks s
            LEFT JOIN daily_charts dc ON s.ticker = dc.ticker
            GROUP BY s.ticker
            HAVING COUNT(dc.date) < 100
            ORDER BY COUNT(dc.date) ASC, s.ticker
            """
            results = self.db.execute_query(query)
            tickers = [row[0] for row in results]
            logger.info(f"Found {len(tickers)} tickers needing more historical data")
            return tickers
        except Exception as e:
            logger.error(f"Error getting tickers needing 100 days history: {e}")
            return []

    def _get_tickers_missing_fundamental_data(self) -> List[str]:
        """
        Get tickers that are missing fundamental data.
        """
        try:
            query = """
            SELECT DISTINCT s.ticker
            FROM stocks s
            LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.ticker IS NULL 
               OR cf.revenue IS NULL 
               OR cf.net_income IS NULL
               OR cf.total_assets IS NULL
            ORDER BY s.ticker
            """
            results = self.db.execute_query(query)
            tickers = [row[0] for row in results]
            logger.info(f"Found {len(tickers)} tickers missing fundamental data")
            return tickers
        except Exception as e:
            logger.error(f"Error getting tickers missing fundamental data: {e}")
            return []

    def _get_historical_data_to_minimum(self, ticker: str, min_days: int = 100) -> Dict:
        """
        Get historical data for a ticker to ensure minimum days requirement using all available sources.
        Fallback order: FMP → Yahoo → Polygon → Finnhub → AlphaVantage
        Logs/report sources tried, days fetched, and final status.
        """
        import json
        from pathlib import Path
        report_path = Path("logs/historical_data_fetch_report.json")
        if not hasattr(self, '_historical_fetch_report'):
            self._historical_fetch_report = {}
        report = self._historical_fetch_report
        result = {
            'ticker': ticker,
            'sources_tried': [],
            'days_before': 0,
            'days_after': 0,
            'status': 'fail',
            'details': []
        }
        try:
            # Check current days available
            current_days_query = """
            SELECT COUNT(*) 
            FROM daily_charts 
            WHERE ticker = %s
            """
            current_result = self.db.execute_query(current_days_query, (ticker,))
            current_days = current_result[0][0] if current_result else 0
            result['days_before'] = current_days
            if current_days >= min_days:
                result['status'] = 'success'
                result['days_after'] = current_days
                report[ticker] = result
                json.dump(report, open(report_path, 'w'), indent=2)
                return {
                    'success': True,
                    'api_calls': 0,
                    'days_added': 0,
                    'reason': 'sufficient_data_exists'
                }
            days_needed = min_days - current_days + 20
            sources = [
                ('fmp', 'fmp', 'fmp_historical_data'),
                ('yahoo_finance', 'yahoo', 'yahoo_historical_data'),
                ('polygon', 'polygon', 'polygon_historical_data'),
                ('finnhub', 'finnhub', 'finnhub_historical_data'),
                ('alpha_vantage', 'alpha_vantage', 'alpha_vantage_historical_data')
            ]
            for service_name, log_name, reason in sources:
                try:
                    service = self.service_manager.get_service(service_name)
                    if service and hasattr(service, 'get_historical_data'):
                        historical_data = service.get_historical_data(ticker, days=days_needed)
                        days_fetched = len(historical_data) if historical_data else 0
                        result['sources_tried'].append({
                            'source': log_name,
                            'days_fetched': days_fetched
                        })
                        if historical_data:
                            self._store_historical_data(ticker, historical_data)
                            # Re-check days after storing
                            new_result = self.db.execute_query(current_days_query, (ticker,))
                            new_days = new_result[0][0] if new_result else 0
                            result['days_after'] = new_days
                            if new_days >= min_days:
                                result['status'] = 'success'
                                result['details'].append(f"Fetched {days_fetched} days from {log_name}")
                                report[ticker] = result
                                json.dump(report, open(report_path, 'w'), indent=2)
                                return {
                                    'success': True,
                                    'api_calls': 1,
                                    'days_added': days_fetched,
                                    'total_days_now': new_days,
                                    'reason': reason
                                }
                            else:
                                result['details'].append(f"Fetched {days_fetched} days from {log_name}, still insufficient")
                        else:
                            result['details'].append(f"No data from {log_name}")
                    else:
                        result['details'].append(f"Service {log_name} not available or missing get_historical_data")
                except Exception as e:
                    result['details'].append(f"{log_name} error: {e}")
            # If we get here, all sources failed or not enough data
            result['status'] = 'partial' if result['days_after'] > 0 else 'fail'
            report[ticker] = result
            json.dump(report, open(report_path, 'w'), indent=2)
            return {
                'success': False,
                'api_calls': len(sources),
                'days_added': result['days_after'] - result['days_before'],
                'error': 'not_enough_data',
                'report': result
            }
        except Exception as e:
            result['details'].append(f"fatal error: {e}")
            report[ticker] = result
            json.dump(report, open(report_path, 'w'), indent=2)
            return {
                'success': False,
                'api_calls': 1,
                'days_added': 0,
                'error': str(e),
                'report': result
            }

    def _batch_fetch_historical_data(self, tickers: List[str], min_days: int = 200) -> Dict:
        """
        Fetch historical data for multiple tickers in batches for better performance.
        
        Args:
            tickers: List of ticker symbols
            min_days: Minimum days of historical data required
            
        Returns:
            Dictionary with batch processing results
        """
        try:
            batch_size = 10  # Process 10 tickers at a time
            total_successful = 0
            total_failed = 0
            total_api_calls = 0
            
            logger.info(f"Starting batch historical data fetch for {len(tickers)} tickers (batch size: {batch_size})")
            
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: {batch}")
                
                batch_successful = 0
                batch_failed = 0
                batch_api_calls = 0
                
                for ticker in batch:
                    try:
                        # Check if we have enough API calls remaining
                        remaining_calls = self.max_api_calls_per_day - self.api_calls_used
                        if remaining_calls <= 0:
                            logger.warning(f"No API calls remaining, stopping batch processing")
                            break
                        
                        # Get historical data for this ticker
                        result = self._get_historical_data_to_minimum(ticker, min_days)
                        
                        if result.get('success'):
                            batch_successful += 1
                            total_successful += 1
                        else:
                            batch_failed += 1
                            total_failed += 1
                        
                        batch_api_calls += result.get('api_calls', 0)
                        total_api_calls += result.get('api_calls', 0)
                        
                        # Small delay between tickers to respect rate limits
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error processing {ticker} in batch: {e}")
                        batch_failed += 1
                        total_failed += 1
                
                # Update API call counter
                self.api_calls_used += batch_api_calls
                
                logger.info(f"Batch {i//batch_size + 1} completed: {batch_successful} successful, {batch_failed} failed, {batch_api_calls} API calls")
                
                # Delay between batches to respect rate limits
                if i + batch_size < len(tickers):
                    time.sleep(1.0)
            
            result = {
                'total_tickers': len(tickers),
                'successful_fetches': total_successful,
                'failed_fetches': total_failed,
                'total_api_calls': total_api_calls,
                'success_rate': total_successful / len(tickers) if tickers else 0.0
            }
            
            logger.info(f"Batch historical data fetch completed: {total_successful}/{len(tickers)} successful ({result['success_rate']:.1%})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in batch historical data fetch: {e}")
            return {
                'total_tickers': len(tickers),
                'successful_fetches': 0,
                'failed_fetches': len(tickers),
                'total_api_calls': 0,
                'success_rate': 0.0,
                'error': str(e)
            }

    def _update_single_ticker_fundamentals(self, ticker: str) -> bool:
        """
        Update fundamental data for a single ticker using multi-service approach.
        """
        try:
            # Use the multi-service manager to get fundamental data
            service = self.service_manager.get_service('fmp')  # Prefer FMP for fundamentals
            fundamental_data = service.get_fundamental_data(ticker)
            
            if fundamental_data:
                # Store fundamental data in database
                self._store_fundamental_data(ticker, fundamental_data)
                logger.debug(f"Successfully updated fundamentals for {ticker}")
                return True
            else:
                logger.warning(f"No fundamental data returned for {ticker}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating fundamentals for {ticker}: {e}")
            return False

    def _store_fundamental_data(self, ticker: str, fundamental_data: Dict):
        """
        Store fundamental data in the company_fundamentals table.
        """
        try:
            # Extract key fundamental metrics
            revenue = fundamental_data.get('revenue', 0) or 0
            net_income = fundamental_data.get('netIncome', 0) or 0
            total_assets = fundamental_data.get('totalAssets', 0) or 0
            total_debt = fundamental_data.get('totalDebt', 0) or 0
            shares_outstanding = fundamental_data.get('sharesOutstanding', 0) or 0
            
            # Update or insert fundamental data
            query = """
            INSERT INTO company_fundamentals (
                ticker, report_date, period_type, revenue, net_income, total_assets, 
                total_debt, shares_outstanding, data_source, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
            ON CONFLICT (ticker) DO UPDATE SET
                report_date = EXCLUDED.report_date,
                period_type = EXCLUDED.period_type,
                revenue = EXCLUDED.revenue,
                net_income = EXCLUDED.net_income,
                total_assets = EXCLUDED.total_assets,
                total_debt = EXCLUDED.total_debt,
                shares_outstanding = EXCLUDED.shares_outstanding,
                data_source = EXCLUDED.data_source,
                last_updated = EXCLUDED.last_updated
            """
            
            from datetime import date
            report_date = date.today()
            period_type = 'ttm'
            data_source = 'daily_system'
            
            values = (ticker, report_date, period_type, revenue, net_income, total_assets, total_debt, shares_outstanding, data_source)
            self.db.execute_update(query, values)
            logger.debug(f"Stored fundamental data for {ticker}")
            
        except Exception as e:
            logger.error(f"Error storing fundamental data for {ticker}: {e}")

    def _calculate_fundamental_ratios(self, ticker: str):
        """
        Calculate fundamental ratios based on current stock price and fundamental data.
        """
        try:
            # Get current stock price
            price_query = """
            SELECT close 
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            price_result = self.db.execute_query(price_query, (ticker,))
            
            if not price_result:
                logger.warning(f"No recent price data for {ticker} - cannot calculate ratios")
                return
                
            current_price = float(price_result[0][0])
            
            # Get fundamental data
            fundamental_query = """
            SELECT revenue, net_income, total_assets, total_debt, shares_outstanding
            FROM company_fundamentals 
            WHERE ticker = %s
            """
            fundamental_result = self.db.execute_query(fundamental_query, (ticker,))
            
            if not fundamental_result:
                logger.warning(f"No fundamental data for {ticker} - cannot calculate ratios")
                return
                
            revenue, net_income, total_assets, total_debt, shares_outstanding = fundamental_result[0]
            
            # Calculate ratios using safe_divide (assuming it exists)
            try:
                from data_validator import safe_divide
            except ImportError:
                # Fallback safe divide function
                def safe_divide(a, b, default=0.0):
                    try:
                        if b == 0 or b is None:
                            return default
                        return float(a) / float(b)
                    except (TypeError, ValueError, ZeroDivisionError):
                        return default
            
            # Calculate key ratios
            market_cap = current_price * shares_outstanding if shares_outstanding else 0
            pe_ratio = safe_divide(current_price, (net_income / shares_outstanding) if shares_outstanding else 0)
            pb_ratio = safe_divide(market_cap, total_assets)
            ps_ratio = safe_divide(market_cap, revenue)
            debt_to_equity = safe_divide(total_debt, (total_assets - total_debt))
            
            # Store calculated ratios
            ratio_query = """
            UPDATE company_fundamentals SET
                price_to_earnings = %s,
                price_to_book = %s,
                price_to_sales = %s,
                debt_to_equity_ratio = %s,
                market_cap = %s
            WHERE ticker = %s
            """
            
            ratio_values = (pe_ratio, pb_ratio, ps_ratio, debt_to_equity, market_cap, ticker)
            self.db.execute_update(ratio_query, ratio_values)
            
            logger.debug(f"Calculated and stored ratios for {ticker}: PE={pe_ratio:.2f}, PB={pb_ratio:.2f}, PS={ps_ratio:.2f}")
            
        except Exception as e:
            logger.error(f"Error calculating fundamental ratios for {ticker}: {e}")

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

    def remove_delisted_stock(self, ticker: str) -> bool:
        """
        Remove a delisted stock from the database, respecting foreign key constraints.
        Deletes from company_fundamentals before stocks.
        """
        try:
            # Delete from company_fundamentals first
            delete_fundamentals = "DELETE FROM company_fundamentals WHERE ticker = %s"
            self.db.execute_query(delete_fundamentals, (ticker,))
            # Then delete from stocks
            delete_stock = "DELETE FROM stocks WHERE ticker = %s"
            self.db.execute_query(delete_stock, (ticker,))
            logger.info(f"Successfully removed delisted stock {ticker} from company_fundamentals and stocks.")
            return True
        except Exception as e:
            logger.error(f"Error removing delisted stock {ticker}: {e}")
            return False


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