"""
Score Orchestrator

Main orchestrator that coordinates technical, fundamental, and analyst scoring
processes. Manages the overall scoring workflow and handles prioritization.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from daily_run.database import DatabaseManager
from daily_run.score_calculator.database_manager import ScoreDatabaseManager
from daily_run.score_calculator.technical_scorer import TechnicalScorer
from daily_run.score_calculator.fundamental_scorer import FundamentalScorer
from daily_run.score_calculator.analyst_scorer import AnalystScorer
import re

logger = logging.getLogger(__name__)


class ScoreOrchestrator:
    """Main orchestrator for the scoring system"""
    
    def __init__(self, db: DatabaseManager = None, max_workers: int = 4):
        self.db = db or DatabaseManager()
        self.score_db = ScoreDatabaseManager(self.db)
        self.max_workers = max_workers
        
        # Initialize scorers
        self.technical_scorer = TechnicalScorer(self.db, self.score_db)
        self.fundamental_scorer = FundamentalScorer(self.db, self.score_db)
        self.analyst_scorer = AnalystScorer(self.db, self.score_db)
        
        # Statistics tracking
        self.stats = {
            'total_tickers': 0,
            'technical_success': 0,
            'fundamental_success': 0,
            'analyst_success': 0,
            'technical_failed': 0,
            'fundamental_failed': 0,
            'analyst_failed': 0,
            'start_time': None,
            'end_time': None
        }
    
    def get_prioritized_tickers(self, max_tickers: int = 1000) -> list:
        """Get a prioritized list of tickers for scoring (simple version)"""
        try:
            query = "SELECT ticker FROM stocks ORDER BY ticker LIMIT %s"
            result = self.db.execute_query(query, (max_tickers,))
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting prioritized tickers: {e}")
            return []
    
    def check_existing_scores(self, ticker: str, calculation_date: date) -> Dict:
        """Check if scores already exist for a ticker on a given date"""
        try:
            query = """
            SELECT 
                technical_calculation_status,
                fundamental_calculation_status,
                analyst_calculation_status
            FROM daily_scores 
            WHERE ticker = %s AND calculation_date = %s
            """
            
            result = self.db.execute_query(query, (ticker, calculation_date))
            if not result:
                return {
                    'technical_exists': False,
                    'fundamental_exists': False,
                    'analyst_exists': False
                }
            
            row = result[0]
            return {
                'technical_exists': row[0] == 'success',
                'fundamental_exists': row[1] == 'success',
                'analyst_exists': row[2] == 'success'
            }
            
        except Exception as e:
            logger.error(f"Error checking existing scores for {ticker}: {e}")
            return {
                'technical_exists': False,
                'fundamental_exists': False,
                'analyst_exists': False
            }
    
    def process_single_ticker(self, ticker: str, calculation_date: date, 
                            force_recalculate: bool = False) -> Dict:
        """Process all scores for a single ticker"""
        try:
            result = {
                'ticker': ticker,
                'technical_success': False,
                'fundamental_success': False,
                'analyst_success': False,
                'errors': []
            }
            
            # Check existing scores
            existing_scores = self.check_existing_scores(ticker, calculation_date)
            
            # Process technical score
            if force_recalculate or not existing_scores['technical_exists']:
                try:
                    success = self.technical_scorer.process_ticker(ticker, calculation_date)
                    result['technical_success'] = success
                    if success:
                        self.stats['technical_success'] += 1
                    else:
                        self.stats['technical_failed'] += 1
                        result['errors'].append('Technical scoring failed')
                except Exception as e:
                    logger.error(f"Error in technical scoring for {ticker}: {e}")
                    result['errors'].append(f'Technical scoring error: {str(e)}')
                    self.stats['technical_failed'] += 1
            else:
                logger.debug(f"Technical score already exists for {ticker}")
            
            # Process fundamental score
            if force_recalculate or not existing_scores['fundamental_exists']:
                try:
                    success = self.fundamental_scorer.process_ticker(ticker, calculation_date)
                    result['fundamental_success'] = success
                    if success:
                        self.stats['fundamental_success'] += 1
                    else:
                        self.stats['fundamental_failed'] += 1
                        result['errors'].append('Fundamental scoring failed')
                except Exception as e:
                    logger.error(f"Error in fundamental scoring for {ticker}: {e}")
                    result['errors'].append(f'Fundamental scoring error: {str(e)}')
                    self.stats['fundamental_failed'] += 1
            else:
                logger.debug(f"Fundamental score already exists for {ticker}")
            
            # Process analyst score
            if force_recalculate or not existing_scores['analyst_exists']:
                try:
                    success = self.analyst_scorer.process_ticker(ticker, calculation_date)
                    result['analyst_success'] = success
                    if success:
                        self.stats['analyst_success'] += 1
                    else:
                        self.stats['analyst_failed'] += 1
                        result['errors'].append('Analyst scoring failed')
                except Exception as e:
                    logger.error(f"Error in analyst scoring for {ticker}: {e}")
                    result['errors'].append(f'Analyst scoring error: {str(e)}')
                    self.stats['analyst_failed'] += 1
            else:
                logger.debug(f"Analyst score already exists for {ticker}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {e}")
            return {
                'ticker': ticker,
                'technical_success': False,
                'fundamental_success': False,
                'analyst_success': False,
                'errors': [f'Processing error: {str(e)}']
            }
    
    def run_scoring_batch(self, tickers: List[str], calculation_date: date,
                         force_recalculate: bool = False, max_time_hours: int = 3) -> Dict:
        """Run scoring for a batch of tickers with time limit"""
        try:
            self.stats['start_time'] = datetime.now()
            self.stats['total_tickers'] = len(tickers)
            
            logger.info(f"Starting scoring batch for {len(tickers)} tickers")
            logger.info(f"Max execution time: {max_time_hours} hours")
            
            max_time_seconds = max_time_hours * 3600
            start_time = time.time()
            
            results = []
            processed_count = 0
            
            # Process tickers in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_ticker = {
                    executor.submit(self.process_single_ticker, ticker, calculation_date, force_recalculate): ticker
                    for ticker in tickers
                }
                
                # Process completed tasks
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        processed_count += 1
                        
                        # Log progress
                        if processed_count % 50 == 0:
                            elapsed = time.time() - start_time
                            rate = processed_count / elapsed if elapsed > 0 else 0
                            remaining = len(tickers) - processed_count
                            eta = remaining / rate if rate > 0 else 0
                            
                            logger.info(f"Progress: {processed_count}/{len(tickers)} "
                                      f"({processed_count/len(tickers)*100:.1f}%) "
                                      f"Rate: {rate:.1f} tickers/sec "
                                      f"ETA: {eta/60:.1f} minutes")
                        
                        # Check time limit
                        if time.time() - start_time > max_time_seconds:
                            logger.warning(f"Time limit reached ({max_time_hours} hours). "
                                         f"Processed {processed_count}/{len(tickers)} tickers")
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing future for {ticker}: {e}")
                        results.append({
                            'ticker': ticker,
                            'technical_success': False,
                            'fundamental_success': False,
                            'analyst_success': False,
                            'errors': [f'Future processing error: {str(e)}']
                        })
            
            self.stats['end_time'] = datetime.now()
            
            # Compile summary
            summary = self._compile_batch_summary(results)
            summary['execution_time'] = time.time() - start_time
            summary['processed_count'] = processed_count
            summary['total_count'] = len(tickers)
            
            logger.info(f"Batch completed. Summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error in scoring batch: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'total_count': len(tickers)
            }
    
    def _compile_batch_summary(self, results: List[Dict]) -> Dict:
        """Compile summary statistics from batch results"""
        try:
            total_tickers = len(results)
            technical_success = sum(1 for r in results if r['technical_success'])
            fundamental_success = sum(1 for r in results if r['fundamental_success'])
            analyst_success = sum(1 for r in results if r['analyst_success'])
            
            all_success = sum(1 for r in results 
                            if r['technical_success'] and r['fundamental_success'] and r['analyst_success'])
            
            failed_tickers = [r['ticker'] for r in results if r['errors']]
            
            return {
                'success': True,
                'total_tickers': total_tickers,
                'technical_success_rate': technical_success / total_tickers if total_tickers > 0 else 0,
                'fundamental_success_rate': fundamental_success / total_tickers if total_tickers > 0 else 0,
                'analyst_success_rate': analyst_success / total_tickers if total_tickers > 0 else 0,
                'all_scores_success_rate': all_success / total_tickers if total_tickers > 0 else 0,
                'failed_tickers': failed_tickers,
                'failed_count': len(failed_tickers)
            }
            
        except Exception as e:
            logger.error(f"Error compiling batch summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_old_scores(self, days_to_keep: int = 100) -> bool:
        """Clean up scores older than specified days"""
        try:
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            
            query = """
            DELETE FROM daily_scores 
            WHERE calculation_date < %s
            """
            
            result = self.db.execute_query(query, (cutoff_date,))
            deleted_count = self.db.cursor.rowcount
            
            logger.info(f"Cleaned up {deleted_count} old score records (older than {cutoff_date})")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old scores: {e}")
            return False
    
    def get_scoring_status(self) -> Dict:
        """Get current scoring system status"""
        try:
            # Get recent scoring statistics
            query = """
            SELECT 
                calculation_date,
                COUNT(*) as total_records,
                SUM(CASE WHEN technical_calculation_status = 'success' THEN 1 ELSE 0 END) as technical_success,
                SUM(CASE WHEN fundamental_calculation_status = 'success' THEN 1 ELSE 0 END) as fundamental_success,
                SUM(CASE WHEN analyst_calculation_status = 'success' THEN 1 ELSE 0 END) as analyst_success
            FROM daily_scores 
            WHERE calculation_date >= %s
            GROUP BY calculation_date
            ORDER BY calculation_date DESC
            LIMIT 7
            """
            
            week_ago = date.today() - timedelta(days=7)
            results = self.db.execute_query(query, (week_ago,))
            
            daily_stats = []
            for row in results:
                daily_stats.append({
                    'date': row[0],
                    'total_records': row[1],
                    'technical_success': row[2],
                    'fundamental_success': row[3],
                    'analyst_success': row[4]
                })
            
            # Get total active tickers
            ticker_query = "SELECT COUNT(*) FROM stocks"
            ticker_result = self.db.execute_query(ticker_query)
            total_active_tickers = ticker_result[0][0] if ticker_result else 0
            
            return {
                'system_status': 'operational',
                'total_active_tickers': total_active_tickers,
                'daily_stats': daily_stats,
                'current_stats': self.stats
            }
            
        except Exception as e:
            logger.error(f"Error getting scoring status: {e}")
            return {
                'system_status': 'error',
                'error': str(e)
            }
    
    def run_daily_scoring(self, max_tickers: int = 1000, max_time_hours: int = 3,
                         force_recalculate: bool = False) -> Dict:
        """Main method to run daily scoring process"""
        try:
            logger.info("Starting daily scoring process")
            
            # Get prioritized tickers
            tickers = self.get_prioritized_tickers(max_tickers)
            if not tickers:
                return {
                    'success': False,
                    'error': 'No tickers found for scoring'
                }
            
            # Set calculation date to today
            calculation_date = date.today()
            
            # Run scoring batch
            batch_result = self.run_scoring_batch(
                tickers, calculation_date, force_recalculate, max_time_hours
            )
            
            # Cleanup old scores
            cleanup_success = self.cleanup_old_scores()
            
            # Get final status
            status = self.get_scoring_status()
            
            return {
                'success': True,
                'batch_result': batch_result,
                'cleanup_success': cleanup_success,
                'system_status': status
            }
            
        except Exception as e:
            logger.error(f"Error in daily scoring: {e}")
            return {
                'success': False,
                'error': str(e)
            } 