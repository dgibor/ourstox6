#!/usr/bin/env python3
"""
Optimized Batch Processor for Financial Data Collection
Uses advanced rate limiting and batch processing for maximum efficiency
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from common_imports import setup_logging
from database import DatabaseManager
from optimized_fmp_service import OptimizedFMPService
from advanced_rate_limiter import get_advanced_rate_limiter
from config import Config

# Setup logging
setup_logging('optimized_batch_processor')
logger = logging.getLogger(__name__)

class OptimizedBatchProcessor:
    """
    Optimized batch processor for financial data collection
    Maximizes efficiency with FMP Starter membership (1000 calls/day)
    """
    
    def __init__(self):
        """Initialize the optimized batch processor"""
        self.db = DatabaseManager()
        self.fmp_service = OptimizedFMPService()
        self.rate_limiter = get_advanced_rate_limiter()
        
        # Processing configuration
        self.max_workers = 3  # Conservative concurrency
        self.batch_size = 100  # FMP batch size
        self.delay_between_batches = 0.2  # 200ms between batches
        
        # Progress tracking
        self.total_tickers = 0
        self.processed_tickers = 0
        self.successful_tickers = 0
        self.failed_tickers = 0
        self.start_time = None
        
        logger.info("Optimized Batch Processor initialized")
    
    def get_tickers_to_process(self, limit: int = None) -> List[str]:
        """
        Get list of tickers that need fundamental data updates
        
        Args:
            limit: Maximum number of tickers to process (None for all)
            
        Returns:
            List of ticker symbols
        """
        try:
            # Get tickers from stocks table
            query = """
                SELECT ticker FROM stocks 
                WHERE ticker IS NOT NULL 
                ORDER BY market_cap DESC NULLS LAST
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.db.execute_query(query)
            
            if result:
                tickers = [row[0] for row in result if row[0]]
                logger.info(f"Found {len(tickers)} tickers to process")
                return tickers
            else:
                logger.warning("No tickers found in stocks table")
                return []
                
        except Exception as e:
            logger.error(f"Error getting tickers to process: {e}")
            return []
    
    def get_tickers_needing_updates(self, days_old: int = 1) -> List[str]:
        """
        Get tickers that need fundamental data updates
        
        Args:
            days_old: Consider data stale if older than this many days
            
        Returns:
            List of ticker symbols needing updates
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            query = """
                SELECT DISTINCT s.ticker 
                FROM stocks s
                LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
                WHERE s.ticker IS NOT NULL
                AND (cf.ticker IS NULL OR cf.last_updated < %s)
                ORDER BY s.market_cap DESC NULLS LAST
            """
            
            result = self.db.execute_query(query, (cutoff_date,))
            
            if result:
                tickers = [row[0] for row in result if row[0]]
                logger.info(f"Found {len(tickers)} tickers needing updates (data older than {days_old} days)")
                return tickers
            else:
                logger.info("No tickers need updates")
                return []
                
        except Exception as e:
            logger.error(f"Error getting tickers needing updates: {e}")
            return []
    
    def process_all_tickers(self, limit: int = None, force_update: bool = False) -> Dict[str, Any]:
        """
        Process all tickers with optimized batch processing
        
        Args:
            limit: Maximum number of tickers to process
            force_update: Force update even if data is recent
            
        Returns:
            Processing results summary
        """
        logger.info("🚀 Starting optimized batch processing")
        
        self.start_time = time.time()
        
        # Get tickers to process
        if force_update:
            tickers = self.get_tickers_to_process(limit)
        else:
            tickers = self.get_tickers_needing_updates()
            if limit:
                tickers = tickers[:limit]
        
        self.total_tickers = len(tickers)
        
        if not tickers:
            logger.info("No tickers to process")
            return self._get_empty_results()
        
        logger.info(f"Processing {self.total_tickers} tickers with optimized batch processing")
        
        # Check FMP quota before starting
        fmp_usage = self.rate_limiter.get_usage_summary('fmp')
        if fmp_usage.get('fmp', {}).get('daily_used', 0) >= 900:  # 90% of 1000
            logger.warning("FMP daily quota nearly exhausted, consider processing fewer tickers")
        
        # Process in optimized batches
        results = self._process_batches(tickers)
        
        # Final summary
        processing_time = time.time() - self.start_time
        results['processing_time'] = processing_time
        results['efficiency_metrics'] = self._calculate_efficiency_metrics()
        
        logger.info("✅ Optimized batch processing completed")
        logger.info(f"  - Total tickers: {self.total_tickers}")
        logger.info(f"  - Successful: {self.successful_tickers}")
        logger.info(f"  - Failed: {self.failed_tickers}")
        logger.info(f"  - Processing time: {processing_time:.2f}s")
        logger.info(f"  - Efficiency: {results['efficiency_metrics']}")
        
        return results
    
    def _process_batches(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Process tickers in optimized batches
        
        Args:
            tickers: List of tickers to process
            
        Returns:
            Processing results
        """
        results = {
            'successful': [],
            'failed': [],
            'batches_processed': 0,
            'api_calls_used': 0,
            'quota_usage': {}
        }
        
        # Create optimized batches
        batches = self.rate_limiter.optimize_batch_requests('fmp', tickers)
        
        logger.info(f"Created {len(batches)} optimized batches")
        
        for i, batch in enumerate(batches):
            try:
                logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch)} tickers)")
                
                # Process batch with FMP service
                batch_results = self.fmp_service.process_tickers_batch(batch)
                
                # Update counters
                self.processed_tickers += len(batch)
                self.successful_tickers += len(batch_results['successful'])
                self.failed_tickers += len(batch_results['failed'])
                
                # Update results
                results['successful'].extend(list(batch_results['successful'].keys()))
                results['failed'].extend(batch_results['failed'])
                results['batches_processed'] += 1
                
                # Update quota usage
                if 'fmp' in batch_results.get('usage_summary', {}):
                    results['quota_usage'] = batch_results['usage_summary']
                
                # Progress logging
                progress = (self.processed_tickers / self.total_tickers) * 100
                logger.info(f"Progress: {progress:.1f}% ({self.processed_tickers}/{self.total_tickers})")
                
                # Check if we're approaching quota limits
                fmp_usage = self.rate_limiter.get_usage_summary('fmp')
                if fmp_usage.get('fmp', {}).get('usage_percentage', 0) >= 0.95:
                    logger.warning("FMP quota at 95%, stopping batch processing")
                    break
                
                # Delay between batches
                if i < len(batches) - 1:
                    time.sleep(self.delay_between_batches)
                
            except Exception as e:
                logger.error(f"Error processing batch {i+1}: {e}")
                results['failed'].extend(batch)
                self.failed_tickers += len(batch)
                continue
        
        return results
    
    def _calculate_efficiency_metrics(self) -> Dict[str, Any]:
        """Calculate processing efficiency metrics"""
        if self.total_tickers == 0:
            return {}
        
        processing_time = time.time() - self.start_time
        
        # Get FMP usage
        fmp_usage = self.rate_limiter.get_usage_summary('fmp')
        fmp_data = fmp_usage.get('fmp', {})
        
        # Calculate metrics
        success_rate = (self.successful_tickers / self.total_tickers) * 100
        tickers_per_minute = (self.total_tickers / processing_time) * 60
        api_calls_per_ticker = fmp_data.get('daily_used', 0) / max(self.total_tickers, 1)
        quota_efficiency = (fmp_data.get('daily_used', 0) / fmp_data.get('daily_limit', 1000)) * 100
        
        return {
            'success_rate_percent': success_rate,
            'tickers_per_minute': tickers_per_minute,
            'api_calls_per_ticker': api_calls_per_ticker,
            'quota_efficiency_percent': quota_efficiency,
            'processing_time_seconds': processing_time,
            'total_tickers': self.total_tickers,
            'successful_tickers': self.successful_tickers,
            'failed_tickers': self.failed_tickers
        }
    
    def _get_empty_results(self) -> Dict[str, Any]:
        """Get empty results structure"""
        return {
            'successful': [],
            'failed': [],
            'batches_processed': 0,
            'api_calls_used': 0,
            'quota_usage': {},
            'processing_time': 0,
            'efficiency_metrics': {}
        }
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get current processing summary"""
        return {
            'total_tickers': self.total_tickers,
            'processed_tickers': self.processed_tickers,
            'successful_tickers': self.successful_tickers,
            'failed_tickers': self.failed_tickers,
            'progress_percent': (self.processed_tickers / max(self.total_tickers, 1)) * 100,
            'processing_time': time.time() - self.start_time if self.start_time else 0,
            'fmp_usage': self.rate_limiter.get_usage_summary('fmp'),
            'alerts': self.rate_limiter.get_alerts('fmp')
        }
    
    def reset_counters(self):
        """Reset processing counters"""
        self.total_tickers = 0
        self.processed_tickers = 0
        self.successful_tickers = 0
        self.failed_tickers = 0
        self.start_time = None
        logger.info("Processing counters reset")

def test_optimized_batch_processor():
    """Test the optimized batch processor"""
    print("🧪 Testing Optimized Batch Processor")
    print("=" * 50)
    
    try:
        processor = OptimizedBatchProcessor()
        
        # Test with a small batch
        print("Testing with 10 tickers...")
        results = processor.process_all_tickers(limit=10, force_update=True)
        
        print(f"\nResults:")
        print(f"  - Successful: {len(results['successful'])}")
        print(f"  - Failed: {len(results['failed'])}")
        print(f"  - Batches processed: {results['batches_processed']}")
        print(f"  - Processing time: {results['processing_time']:.2f}s")
        
        # Show efficiency metrics
        efficiency = results.get('efficiency_metrics', {})
        if efficiency:
            print(f"\nEfficiency Metrics:")
            for key, value in efficiency.items():
                if isinstance(value, float):
                    print(f"  - {key}: {value:.2f}")
                else:
                    print(f"  - {key}: {value}")
        
        # Show FMP usage
        fmp_usage = results.get('quota_usage', {}).get('fmp', {})
        if fmp_usage:
            print(f"\nFMP Usage:")
            for key, value in fmp_usage.items():
                print(f"  - {key}: {value}")
        
        print("\n✅ Optimized Batch Processor test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def run_optimized_batch_processing():
    """Run optimized batch processing for all tickers"""
    print("🚀 Starting Optimized Batch Processing")
    print("=" * 50)
    
    try:
        processor = OptimizedBatchProcessor()
        
        # Get current FMP usage
        fmp_usage = processor.rate_limiter.get_usage_summary('fmp')
        print(f"Current FMP usage: {fmp_usage}")
        
        # Process all tickers
        results = processor.process_all_tickers(force_update=False)
        
        # Print summary
        print(f"\n📊 Processing Summary:")
        print(f"  - Total tickers: {results.get('efficiency_metrics', {}).get('total_tickers', 0)}")
        print(f"  - Successful: {len(results['successful'])}")
        print(f"  - Failed: {len(results['failed'])}")
        print(f"  - Processing time: {results['processing_time']:.2f}s")
        
        # Show efficiency
        efficiency = results.get('efficiency_metrics', {})
        if efficiency:
            print(f"  - Success rate: {efficiency.get('success_rate_percent', 0):.1f}%")
            print(f"  - Tickers per minute: {efficiency.get('tickers_per_minute', 0):.1f}")
            print(f"  - Quota efficiency: {efficiency.get('quota_efficiency_percent', 0):.1f}%")
        
        # Show alerts
        alerts = processor.rate_limiter.get_alerts('fmp')
        if alerts:
            print(f"\n⚠️ Alerts:")
            for alert in alerts:
                print(f"  - {alert['alert_type']}: {alert['message']}")
        
        print("\n✅ Optimized batch processing completed")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_optimized_batch_processor()
    else:
        run_optimized_batch_processing() 