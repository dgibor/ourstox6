#!/usr/bin/env python3
"""
Improved Historical Data Backfill System

This script addresses the issues with the current historical data backfill:
1. API call limitations - runs independently with dedicated API allocation
2. Inefficient processing - implements batch processing
3. Poor error handling - comprehensive error handling and retry logic
4. No progress tracking - detailed progress monitoring and reporting
"""

import os
import sys
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add daily_run to path
sys.path.append('daily_run')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_historical_backfill.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedHistoricalDataBackfill:
    """Improved historical data backfill system"""
    
    def __init__(self, max_api_calls: int = 1000, batch_size: int = 50):
        self.max_api_calls = max_api_calls
        self.batch_size = batch_size
        self.api_calls_used = 0
        self.successful_updates = 0
        self.failed_updates = 0
        self.progress_file = Path("logs/historical_backfill_progress.json")
        self.progress_file.parent.mkdir(exist_ok=True)
        
        # Initialize database connection
        try:
            from database import DatabaseManager
            self.db = DatabaseManager()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def get_tickers_needing_historical_data(self, min_days: int = 100) -> List[str]:
        """Get tickers that need more historical data"""
        query = """
        SELECT s.ticker
        FROM stocks s
        LEFT JOIN (
            SELECT ticker, COUNT(*) as day_count
            FROM daily_charts
            GROUP BY ticker
        ) dc ON s.ticker = dc.ticker
        WHERE s.ticker IS NOT NULL
        AND (dc.day_count IS NULL OR dc.day_count < %s)
        ORDER BY COALESCE(dc.day_count, 0) ASC
        """
        
        results = self.db.execute_query(query, (min_days,))
        tickers = [row[0] for row in results]
        logger.info(f"Found {len(tickers)} tickers needing historical data")
        return tickers
    
    def get_current_days_for_ticker(self, ticker: str) -> int:
        """Get current number of days for a ticker"""
        query = "SELECT COUNT(*) FROM daily_charts WHERE ticker = %s"
        result = self.db.fetch_one(query, (ticker,))
        return result[0] if result else 0
    
    def fetch_historical_data_from_service(self, ticker: str, service_name: str, days_needed: int) -> Optional[List[Dict]]:
        """Fetch historical data from a specific service"""
        try:
            # Import service manager
            from enhanced_multi_service_manager import EnhancedMultiServiceManager
            service_manager = EnhancedMultiServiceManager()
            
            # Get service
            service = service_manager.get_service(service_name)
            if not service or not hasattr(service, 'get_historical_data'):
                logger.warning(f"Service {service_name} not available for {ticker}")
                return None
            
            # Fetch data
            historical_data = service.get_historical_data(ticker, days=days_needed)
            if historical_data and len(historical_data) > 0:
                logger.debug(f"Fetched {len(historical_data)} days from {service_name} for {ticker}")
                return historical_data
            else:
                logger.debug(f"No data returned from {service_name} for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from {service_name} for {ticker}: {e}")
            return None
    
    def store_historical_data(self, ticker: str, historical_data: List[Dict]) -> bool:
        """Store historical data in database"""
        try:
            if not historical_data:
                return False
            
            # Prepare data for batch insert
            values = []
            for data in historical_data:
                values.append((
                    ticker,
                    data.get('date'),
                    data.get('open'),
                    data.get('high'),
                    data.get('low'),
                    data.get('close'),
                    data.get('volume')
                ))
            
            # Batch insert
            query = """
            INSERT INTO daily_charts (ticker, date, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
            """
            
            rows_affected = self.db.execute_values(query, values)
            logger.debug(f"Stored {rows_affected} records for {ticker}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error storing historical data for {ticker}: {e}")
            return False
    
    def process_single_ticker(self, ticker: str, min_days: int = 100) -> Dict:
        """Process a single ticker with multiple service fallbacks"""
        result = {
            'ticker': ticker,
            'success': False,
            'days_before': 0,
            'days_after': 0,
            'days_added': 0,
            'api_calls': 0,
            'services_tried': [],
            'error': None
        }
        
        try:
            # Check current days
            current_days = self.get_current_days_for_ticker(ticker)
            result['days_before'] = current_days
            
            if current_days >= min_days:
                result['success'] = True
                result['days_after'] = current_days
                result['reason'] = 'sufficient_data_exists'
                return result
            
            # Calculate days needed
            days_needed = min_days - current_days + 20  # Add buffer
            
            # Try services in order of preference
            services = [
                ('yahoo_finance', 'Yahoo Finance'),
                ('fmp', 'FMP'),
                ('polygon', 'Polygon'),
                ('finnhub', 'Finnhub'),
                ('alpha_vantage', 'Alpha Vantage')
            ]
            
            for service_name, service_display in services:
                if self.api_calls_used >= self.max_api_calls:
                    result['error'] = 'api_limit_reached'
                    break
                
                result['services_tried'].append(service_name)
                result['api_calls'] += 1
                self.api_calls_used += 1
                
                logger.debug(f"Trying {service_display} for {ticker}")
                
                # Fetch data
                historical_data = self.fetch_historical_data_from_service(ticker, service_name, days_needed)
                
                if historical_data:
                    # Store data
                    if self.store_historical_data(ticker, historical_data):
                        # Check new count
                        new_days = self.get_current_days_for_ticker(ticker)
                        result['days_after'] = new_days
                        result['days_added'] = new_days - current_days
                        
                        if new_days >= min_days:
                            result['success'] = True
                            result['reason'] = f'data_fetched_from_{service_name}'
                            logger.info(f"✅ {ticker}: Added {result['days_added']} days from {service_display} (now {new_days} days)")
                            return result
                        else:
                            logger.debug(f"⚠️ {ticker}: Added {result['days_added']} days from {service_display}, still need {min_days - new_days} more")
                    else:
                        logger.warning(f"Failed to store data from {service_display} for {ticker}")
                else:
                    logger.debug(f"No data from {service_display} for {ticker}")
            
            # If we get here, all services failed or insufficient data
            if result['days_after'] > current_days:
                result['reason'] = 'partial_success'
                logger.warning(f"⚠️ {ticker}: Partial success - added {result['days_added']} days, still need {min_days - result['days_after']} more")
            else:
                result['reason'] = 'all_services_failed'
                logger.error(f"❌ {ticker}: All services failed")
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error processing {ticker}: {e}")
            return result
    
    def process_batch(self, tickers: List[str], min_days: int = 100) -> List[Dict]:
        """Process a batch of tickers"""
        results = []
        
        logger.info(f"Processing batch of {len(tickers)} tickers")
        
        for i, ticker in enumerate(tickers, 1):
            if self.api_calls_used >= self.max_api_calls:
                logger.warning(f"API limit reached after {self.api_calls_used} calls")
                break
            
            logger.info(f"Processing {i}/{len(tickers)}: {ticker}")
            
            result = self.process_single_ticker(ticker, min_days)
            results.append(result)
            
            if result['success']:
                self.successful_updates += 1
            else:
                self.failed_updates += 1
            
            # Add small delay to avoid rate limiting
            time.sleep(0.1)
        
        return results
    
    def save_progress(self, results: List[Dict]):
        """Save progress to file"""
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'api_calls_used': self.api_calls_used,
            'successful_updates': self.successful_updates,
            'failed_updates': self.failed_updates,
            'results': results
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def run_backfill(self, min_days: int = 100) -> Dict:
        """Run the complete historical data backfill"""
        start_time = time.time()
        
        logger.info("🚀 Starting Improved Historical Data Backfill")
        logger.info(f"API Call Limit: {self.max_api_calls}")
        logger.info(f"Batch Size: {self.batch_size}")
        logger.info(f"Minimum Days Required: {min_days}")
        
        try:
            # Get tickers needing historical data
            tickers = self.get_tickers_needing_historical_data(min_days)
            
            if not tickers:
                logger.info("No tickers need historical data backfill")
                return {
                    'status': 'completed',
                    'reason': 'no_tickers_need_backfill',
                    'processing_time': time.time() - start_time
                }
            
            # Process in batches
            all_results = []
            batch_num = 0
            
            for i in range(0, len(tickers), self.batch_size):
                if self.api_calls_used >= self.max_api_calls:
                    logger.warning("API limit reached, stopping backfill")
                    break
                
                batch_num += 1
                batch = tickers[i:i + self.batch_size]
                
                logger.info(f"Processing batch {batch_num} ({len(batch)} tickers)")
                
                batch_results = self.process_batch(batch, min_days)
                all_results.extend(batch_results)
                
                # Save progress after each batch
                self.save_progress(all_results)
                
                # Progress summary
                successful_in_batch = sum(1 for r in batch_results if r['success'])
                logger.info(f"Batch {batch_num} complete: {successful_in_batch}/{len(batch)} successful")
                logger.info(f"Total progress: {self.successful_updates} successful, {self.failed_updates} failed")
                logger.info(f"API calls used: {self.api_calls_used}/{self.max_api_calls}")
            
            # Final summary
            processing_time = time.time() - start_time
            
            summary = {
                'status': 'completed',
                'total_tickers_processed': len(all_results),
                'successful_updates': self.successful_updates,
                'failed_updates': self.failed_updates,
                'api_calls_used': self.api_calls_used,
                'processing_time': processing_time,
                'batches_processed': batch_num,
                'success_rate': (self.successful_updates / len(all_results) * 100) if all_results else 0
            }
            
            logger.info("=" * 60)
            logger.info("📊 HISTORICAL DATA BACKFILL SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total tickers processed: {len(all_results)}")
            logger.info(f"Successful updates: {self.successful_updates}")
            logger.info(f"Failed updates: {self.failed_updates}")
            logger.info(f"Success rate: {summary['success_rate']:.1f}%")
            logger.info(f"API calls used: {self.api_calls_used}")
            logger.info(f"Processing time: {processing_time:.1f} seconds")
            logger.info(f"Batches processed: {batch_num}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in historical data backfill: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - start_time
            }

def main():
    """Main function"""
    # Configuration
    max_api_calls = 1000  # Adjust based on your API limits
    batch_size = 50
    min_days = 100
    
    # Run backfill
    backfill = ImprovedHistoricalDataBackfill(max_api_calls, batch_size)
    result = backfill.run_backfill(min_days)
    
    # Print final result
    print("\n" + "="*60)
    print("IMPROVED HISTORICAL DATA BACKFILL COMPLETE")
    print("="*60)
    print(f"Status: {result['status']}")
    if result['status'] == 'completed':
        print(f"Success Rate: {result['success_rate']:.1f}%")
        print(f"API Calls Used: {result['api_calls_used']}")
        print(f"Processing Time: {result['processing_time']:.1f} seconds")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main() 