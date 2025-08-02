#!/usr/bin/env python3
"""
Complete Data Collection and Calculation Flow

This script runs the complete pipeline for 5 tickers:
1. Collect fresh price data via API calls
2. Calculate technical indicators
3. Update fundamental data
4. Update earnings calendar
5. Calculate final scores
"""

import logging
import time
import sys
import os
from datetime import date, datetime
from typing import List, Dict
import subprocess

# Add the daily_run directory to the path
sys.path.append('daily_run')

# Import from daily_run with proper path handling
from database import DatabaseManager
from batch_price_processor import BatchPriceProcessor
from earnings_based_fundamental_processor import EarningsBasedFundamentalProcessor
from earnings_calendar_service import EarningsCalendarService
from enhanced_service_factory import EnhancedServiceFactory

# Import score calculator
sys.path.append('daily_run/score_calculator')
from score_orchestrator import ScoreOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/complete_flow.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CompleteDataFlow:
    """Complete data collection and calculation flow"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.tickers = ['AAON', 'AAPL', 'AAXJ', 'ABBV', 'ABCM']
        self.start_time = time.time()
        
        # Initialize processors
        self.batch_price_processor = BatchPriceProcessor(
            db=self.db,
            max_batch_size=5,  # Process all 5 tickers in one batch
            max_workers=1,
            delay_between_batches=1.0
        )
        
        self.earnings_processor = EarningsBasedFundamentalProcessor(
            db=self.db,
            max_workers=1,
            earnings_window_days=7
        )
        self.earnings_service = EarningsCalendarService()
        self.service_factory = EnhancedServiceFactory()
        self.score_orchestrator = ScoreOrchestrator()
        
        logger.info(f"Initialized CompleteDataFlow for tickers: {self.tickers}")
    
    def run_complete_flow(self) -> Dict:
        """Run the complete data collection and calculation flow"""
        logger.info("🚀 Starting Complete Data Collection and Calculation Flow")
        
        results = {}
        
        try:
            # Step 1: Collect fresh price data
            logger.info("Step 1: Collecting fresh price data...")
            price_result = self._collect_price_data()
            results['price_data'] = price_result
            
            # Step 2: Calculate technical indicators
            logger.info("Step 2: Calculating technical indicators...")
            technical_result = self._calculate_technical_indicators()
            results['technical_indicators'] = technical_result
            
            # Step 3: Update fundamental data
            logger.info("Step 3: Updating fundamental data...")
            fundamental_result = self._update_fundamental_data()
            results['fundamental_data'] = fundamental_result
            
            # Step 4: Update earnings calendar
            logger.info("Step 4: Updating earnings calendar...")
            earnings_result = self._update_earnings_calendar()
            results['earnings_calendar'] = earnings_result
            
            # Step 5: Calculate final scores
            logger.info("Step 5: Calculating final scores...")
            scoring_result = self._calculate_final_scores()
            results['final_scores'] = scoring_result
            
            # Compile final results
            total_time = time.time() - self.start_time
            final_results = {
                'system': 'complete_data_flow',
                'timestamp': datetime.now(),
                'total_processing_time': total_time,
                'tickers_processed': self.tickers,
                'results': results,
                'summary': self._generate_summary(results)
            }
            
            logger.info("✅ Complete Data Flow finished successfully")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Complete Data Flow failed: {e}")
            return {
                'system': 'complete_data_flow',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
        finally:
            self.db.disconnect()
    
    def _collect_price_data(self) -> Dict:
        """Collect fresh price data for all tickers"""
        try:
            logger.info(f"Collecting price data for {len(self.tickers)} tickers...")
            
            # Use batch price processor to get fresh data
            price_data = self.batch_price_processor.process_batch_prices(self.tickers)
            
            successful = len([t for t in self.tickers if price_data.get(t, {}).get('success', False)])
            
            result = {
                'phase': 'price_data_collection',
                'tickers_processed': len(self.tickers),
                'successful_updates': successful,
                'failed_updates': len(self.tickers) - successful,
                'details': price_data
            }
            
            logger.info(f"Price data collection: {successful}/{len(self.tickers)} successful")
            return result
            
        except Exception as e:
            logger.error(f"Error collecting price data: {e}")
            return {
                'phase': 'price_data_collection',
                'error': str(e),
                'successful_updates': 0
            }
    
    def _calculate_technical_indicators(self) -> Dict:
        """Calculate technical indicators for all tickers using subprocess."""
        try:
            logger.info(f"Calculating technical indicators for {len(self.tickers)} tickers via subprocess...")
            
            successful = 0
            failed = 0
            details = {}
            
            for ticker in self.tickers:
                try:
                    result = subprocess.run([
                        sys.executable, 'daily_run/calc_technicals.py',
                        '--table', 'daily_charts',
                        '--ticker_col', 'ticker',
                        '--ticker', str(ticker)
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0 and 'Not enough data' not in result.stdout and 'No price data found' not in result.stdout:
                        successful += 1
                        details[ticker] = {'status': 'success', 'output': result.stdout.strip()}
                    else:
                        failed += 1
                        details[ticker] = {'status': 'failed', 'output': result.stdout.strip(), 'error': result.stderr.strip()}
                        logger.error(f"Technical calculation failed for {ticker}: {result.stdout.strip()} {result.stderr.strip()}")
                except Exception as e:
                    failed += 1
                    details[ticker] = {'status': 'failed', 'error': str(e)}
                    logger.error(f"Error running technical calculation for {ticker}: {e}")
            
            result = {
                'phase': 'technical_indicators',
                'tickers_processed': len(self.tickers),
                'successful_calculations': successful,
                'failed_calculations': failed,
                'details': details
            }
            
            logger.info(f"Technical indicators: {successful}/{len(self.tickers)} successful")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {
                'phase': 'technical_indicators',
                'error': str(e),
                'successful_calculations': 0
            }
    
    def _update_fundamental_data(self) -> Dict:
        """Update fundamental data for all tickers"""
        try:
            logger.info(f"Updating fundamental data for {len(self.tickers)} tickers...")
            
            # Use earnings-based fundamental processor
            fundamental_data = self.earnings_processor.process_tickers(self.tickers)
            
            successful = len([t for t in self.tickers if fundamental_data.get(t, {}).get('success', False)])
            
            result = {
                'phase': 'fundamental_data',
                'tickers_processed': len(self.tickers),
                'successful_updates': successful,
                'failed_updates': len(self.tickers) - successful,
                'details': fundamental_data
            }
            
            logger.info(f"Fundamental data: {successful}/{len(self.tickers)} successful")
            return result
            
        except Exception as e:
            logger.error(f"Error updating fundamental data: {e}")
            return {
                'phase': 'fundamental_data',
                'error': str(e),
                'successful_updates': 0
            }
    
    def _update_earnings_calendar(self) -> Dict:
        """Update earnings calendar for all tickers"""
        try:
            logger.info(f"Updating earnings calendar for {len(self.tickers)} tickers...")
            
            successful = 0
            failed = 0
            details = {}
            
            for ticker in self.tickers:
                try:
                    # Get earnings calendar data
                    earnings_data = self.earnings_service.get_earnings_calendar(ticker)
                    
                    if earnings_data and len(earnings_data) > 0:
                        successful += 1
                        details[ticker] = {'status': 'success', 'earnings_count': len(earnings_data)}
                    else:
                        failed += 1
                        details[ticker] = {'status': 'failed', 'error': 'No earnings data found'}
                        
                except Exception as e:
                    failed += 1
                    details[ticker] = {'status': 'failed', 'error': str(e)}
                    logger.error(f"Error updating earnings calendar for {ticker}: {e}")
            
            result = {
                'phase': 'earnings_calendar',
                'tickers_processed': len(self.tickers),
                'successful_updates': successful,
                'failed_updates': failed,
                'details': details
            }
            
            logger.info(f"Earnings calendar: {successful}/{len(self.tickers)} successful")
            return result
            
        except Exception as e:
            logger.error(f"Error updating earnings calendar: {e}")
            return {
                'phase': 'earnings_calendar',
                'error': str(e),
                'successful_updates': 0
            }
    
    def _calculate_final_scores(self) -> Dict:
        """Calculate final scores for all tickers"""
        try:
            logger.info(f"Calculating final scores for {len(self.tickers)} tickers...")
            
            successful = 0
            failed = 0
            details = {}
            
            for ticker in self.tickers:
                try:
                    # Calculate scores using the orchestrator
                    result = self.score_orchestrator.process_single_ticker(ticker, date.today(), force_recalculate=True)
                    
                    if result.get('technical_success') or result.get('fundamental_success') or result.get('analyst_success'):
                        successful += 1
                        details[ticker] = {'status': 'success', 'result': result}
                    else:
                        failed += 1
                        details[ticker] = {'status': 'failed', 'errors': result.get('errors', [])}
                        
                except Exception as e:
                    failed += 1
                    details[ticker] = {'status': 'failed', 'error': str(e)}
                    logger.error(f"Error calculating scores for {ticker}: {e}")
            
            result = {
                'phase': 'final_scores',
                'tickers_processed': len(self.tickers),
                'successful_calculations': successful,
                'failed_calculations': failed,
                'details': details
            }
            
            logger.info(f"Final scores: {successful}/{len(self.tickers)} successful")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating final scores: {e}")
            return {
                'phase': 'final_scores',
                'error': str(e),
                'successful_calculations': 0
            }
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of all phases"""
        summary = {
            'price_data_collected': results.get('price_data', {}).get('successful_updates', 0),
            'technical_indicators_calculated': results.get('technical_indicators', {}).get('successful_calculations', 0),
            'fundamental_data_updated': results.get('fundamental_data', {}).get('successful_updates', 0),
            'earnings_calendar_updated': results.get('earnings_calendar', {}).get('successful_updates', 0),
            'final_scores_calculated': results.get('final_scores', {}).get('successful_calculations', 0)
        }
        
        return summary

def main():
    """Main entry point"""
    print("🚀 Complete Data Collection and Calculation Flow")
    print("=" * 60)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Initialize and run the complete flow
    flow = CompleteDataFlow()
    results = flow.run_complete_flow()
    
    # Print results
    print("\n" + "=" * 60)
    print("COMPLETE DATA FLOW RESULTS")
    print("=" * 60)
    print(f"System: {results['system']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Processing time: {results['total_processing_time']:.2f}s")
    print(f"Tickers processed: {', '.join(results['tickers_processed'])}")
    
    if 'summary' in results:
        print(f"\nSUMMARY:")
        summary = results['summary']
        print(f"Price data collected: {summary['price_data_collected']}/5")
        print(f"Technical indicators calculated: {summary['technical_indicators_calculated']}/5")
        print(f"Fundamental data updated: {summary['fundamental_data_updated']}/5")
        print(f"Earnings calendar updated: {summary['earnings_calendar_updated']}/5")
        print(f"Final scores calculated: {summary['final_scores_calculated']}/5")
    
    if 'error' in results:
        print(f"\n❌ ERROR: {results['error']}")
    
    print("\n" + "=" * 60)
    
    # Check final scores
    print("\nFINAL SCORES CHECK:")
    print("=" * 30)
    
    try:
        db = DatabaseManager()
        tickers = ['AAON', 'AAPL', 'AAXJ', 'ABBV', 'ABCM']
        
        for ticker in tickers:
            result = db.execute_query("""
                SELECT swing_trader_score, momentum_trader_score, long_term_investor_score,
                       conservative_investor_score, garp_investor_score, deep_value_investor_score,
                       composite_analyst_score
                FROM daily_scores 
                WHERE ticker = %s 
                ORDER BY calculation_date DESC 
                LIMIT 1
            """, (ticker,))
            
            if result:
                row = result[0]
                print(f"\n{ticker}:")
                print(f"  Technical: Swing={row[0]}, Momentum={row[1]}, Long={row[2]}")
                print(f"  Fundamental: Conservative={row[3]}, GARP={row[4]}, Deep={row[5]}")
                print(f"  Analyst: {row[6]}")
            else:
                print(f"\n{ticker}: No scores found")
        
        db.disconnect()
        
    except Exception as e:
        print(f"Error checking final scores: {e}")

if __name__ == "__main__":
    main() 