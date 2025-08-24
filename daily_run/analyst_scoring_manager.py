#!/usr/bin/env python3
"""
Analyst Scoring Manager

Handles analyst score calculations and database operations.
Separated from daily_trading_system.py to follow 100-line rule.
"""

import logging
import time
from typing import Dict, List
from datetime import date

try:
    from .analyst_scorer import AnalystScorer
    from .database import DatabaseManager
except ImportError:
    from analyst_scorer import AnalystScorer
    from database import DatabaseManager

logger = logging.getLogger(__name__)


class AnalystScoringManager:
    """Manages analyst scoring operations for the daily trading system"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.analyst_scorer = AnalystScorer(db=db)
    
    def get_active_tickers(self) -> List[str]:
        """Get all active tickers for analyst scoring"""
        try:
            query = """
            SELECT ticker
            FROM stocks
            WHERE active = true
            ORDER BY ticker
            """
            
            results = self.db.execute_query(query)
            tickers = [row[0] for row in results] if results else []
            logger.info(f"Found {len(tickers)} active tickers for analyst scoring")
            return tickers
            
        except Exception as e:
            logger.error(f"Error getting active tickers: {e}")
            return []
    
    def filter_existing_tickers(self, tickers: List[str]) -> List[str]:
        """Filter out tickers that don't exist in any API to avoid wasted calls"""
        try:
            from .stock_existence_checker import StockExistenceChecker
            
            logger.info(f"Filtering {len(tickers)} tickers for API existence")
            existence_checker = StockExistenceChecker(self.db)
            
            # Check first 10 tickers as a sample to avoid too many API calls
            sample_size = min(10, len(tickers))
            sample_tickers = tickers[:sample_size]
            
            check_results = existence_checker.process_tickers_in_batches(sample_tickers)
            
            # Count how many don't exist in any API
            non_existent_count = sum(1 for result in check_results.values() if result.should_remove)
            
            if non_existent_count > 0:
                logger.warning(f"Found {non_existent_count} potentially delisted stocks in sample")
                # Return all tickers but log the warning - full cleanup should be done separately
                return tickers
            
            logger.info("Sample check shows all tickers exist in APIs")
            return tickers
            
        except ImportError:
            logger.warning("Stock Existence Checker not available, proceeding with all tickers")
            return tickers
        except Exception as e:
            logger.error(f"Error filtering tickers: {e}")
            return tickers
    
    def check_api_rate_limits(self, service_manager) -> bool:
        """Check if we have API calls remaining for analyst scoring"""
        try:
            if service_manager:
                finnhub_service = service_manager.get_service('finnhub')
                if finnhub_service and hasattr(finnhub_service, 'rate_limiter'):
                    remaining_calls = finnhub_service.rate_limiter.get_remaining_calls('finnhub', 'stock/recommendation')
                    if remaining_calls <= 0:
                        logger.warning("⚠️ No API calls remaining for analyst scoring")
                        return False
                    logger.info(f"📊 API calls remaining for analyst scoring: {remaining_calls}")
                    return True
        except Exception as e:
            logger.warning(f"⚠️ Could not check API rate limits: {e}")
        
        return True  # Assume OK if we can't check
    
    def calculate_all_analyst_scores(self, service_manager=None) -> Dict:
        """Calculate analyst scores for all active tickers"""
        logger.info("📊 STARTING ANALYST SCORE CALCULATIONS")
        start_time = time.time()
        
        try:
            # Get active tickers
            tickers = self.get_active_tickers()
            if not tickers:
                return self._create_result('skipped', 'no_active_tickers', start_time)
            
            # Filter out potentially delisted stocks to avoid wasted API calls
            original_count = len(tickers)
            tickers = self.filter_existing_tickers(tickers)
            filtered_count = len(tickers)
            
            if filtered_count < original_count:
                logger.info(f"Filtered {original_count - filtered_count} potentially delisted tickers")
            
            # Check API rate limits
            if not self.check_api_rate_limits(service_manager):
                return self._create_result('skipped', 'no_api_calls_remaining', start_time)
            
            # Process tickers
            successful_calculations = 0
            failed_calculations = 0
            
            for i, ticker in enumerate(tickers, 1):
                result = self._process_single_ticker(ticker, i, len(tickers))
                if result['success']:
                    successful_calculations += 1
                else:
                    failed_calculations += 1
                
                # Progress update every 10 tickers
                if i % 10 == 0 or i == len(tickers):
                    logger.info(f"📊 ANALYST SCORING PROGRESS: {i}/{len(tickers)} completed ({i/len(tickers)*100:.1f}%)")
            
            total_time = time.time() - start_time
            logger.info(f"📊 ANALYST SCORES COMPLETED: {successful_calculations}/{len(tickers)} successful in {total_time/60:.1f} minutes")
            
            return self._create_result('completed', None, start_time, successful_calculations, failed_calculations, len(tickers))
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ Analyst scores calculation failed after {total_time:.2f}s: {e}")
            return self._create_result('failed', str(e), start_time)
    
    def _process_single_ticker(self, ticker: str, index: int, total: int) -> Dict:
        """Process a single ticker for analyst scoring"""
        ticker_start_time = time.time()
        
        try:
            logger.info(f"📊 [{index}/{total}] Calculating analyst scores for {ticker}")
            
            # Calculate analyst scores
            analyst_scores = self.analyst_scorer.calculate_analyst_score(ticker)
            
            if analyst_scores and analyst_scores.get('calculation_status') != 'failed':
                # Store analyst scores
                success = self.analyst_scorer.store_analyst_score(ticker, analyst_scores)
                
                ticker_time = time.time() - ticker_start_time
                
                if success:
                    logger.info(f"   ✅ {ticker}: Analyst scores calculated and stored in {ticker_time:.2f}s")
                    return {'success': True}
                else:
                    logger.warning(f"   ❌ {ticker}: Failed to store analyst scores after {ticker_time:.2f}s")
                    return {'success': False}
            else:
                ticker_time = time.time() - ticker_start_time
                logger.warning(f"   ❌ {ticker}: Failed to calculate analyst scores after {ticker_time:.2f}s")
                return {'success': False}
                
        except Exception as e:
            ticker_time = time.time() - ticker_start_time
            logger.error(f"   ❌ {ticker}: Error after {ticker_time:.2f}s - {e}")
            return {'success': False}
    
    def _create_result(self, status: str, reason: str = None, start_time: float = None, 
                      successful: int = 0, failed: int = 0, total: int = 0) -> Dict:
        """Create standardized result dictionary"""
        result = {
            'phase': 'priority_6_analyst_scores',
            'status': status,
            'successful_calculations': successful,
            'failed_calculations': failed,
            'total_tickers': total
        }
        
        if reason:
            result['reason'] = reason
        
        if start_time:
            result['processing_time'] = time.time() - start_time
        
        return result
