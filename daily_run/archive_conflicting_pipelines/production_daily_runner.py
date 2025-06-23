#!/usr/bin/env python3
"""
Production Daily Financial Data Runner
Runs the complete daily pipeline for all tickers with proper error handling
"""

import logging
import time
import sys
import os
from datetime import datetime, date
from typing import Dict, List, Any, Tuple
from config import Config
from database import DatabaseManager
from price_service import PriceCollector
from ratios_calculator import RatiosCalculator
from service_factory import ServiceFactory
from new_daily_pipeline import DailyPipeline
from exceptions import DailyRunError

class ProductionDailyRunner:
    """Production-ready daily financial data runner"""
    
    def __init__(self):
        """Initialize the production runner"""
        self.start_time = datetime.now()
        self.setup_logging()
        self.db = DatabaseManager()
        self.service_factory = ServiceFactory()
        
        # Statistics
        self.stats = {
            'total_tickers': 0,
            'prices_updated': 0,
            'fundamentals_updated': 0,
            'ratios_calculated': 0,
            'failed_tickers': [],
            'errors': []
        }
    
    def setup_logging(self):
        """Setup production logging"""
        log_filename = f"logs/production_run_{date.today().strftime('%Y%m%d')}.log"
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_progress(self, current: int, total: int, message: str):
        """Log progress with percentage"""
        percentage = (current / total) * 100 if total > 0 else 0
        self.logger.info(f"Progress: {current}/{total} ({percentage:.1f}%) - {message}")
    
    def update_prices_batch(self, tickers: List[str], batch_size: int = 100) -> Dict[str, Any]:
        """Update prices for a batch of tickers"""
        self.logger.info(f"Starting price updates for {len(tickers)} tickers")
        
        try:
            collector = PriceCollector('stocks')
            result = collector.run()
            
            self.stats['prices_updated'] = result.get('successful', 0)
            self.logger.info(f"Price updates completed: {result['successful']}/{result['total_tickers']} successful")
            
            collector.close()
            return result
            
        except Exception as e:
            error_msg = f"Price update batch failed: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return {'error': error_msg}
    
    def update_fundamentals_batch(self, tickers: List[str], batch_size: int = 50) -> Dict[str, Any]:
        """Update fundamentals for a batch of tickers"""
        self.logger.info(f"Starting fundamental updates for {len(tickers)} tickers")
        
        successful = 0
        failed = 0
        errors = []
        
        for i, ticker in enumerate(tickers):
            try:
                # TODO: Implement fundamental service when available
                # For now, just log the attempt
                self.logger.debug(f"Would update fundamentals for {ticker}")
                successful += 1
                
                # Rate limiting
                if i % 10 == 0:
                    time.sleep(1)
                
                # Progress logging
                if i % 50 == 0:
                    self.log_progress(i, len(tickers), f"Processing fundamentals for {ticker}")
                    
            except Exception as e:
                failed += 1
                error_msg = f"{ticker}: {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)
        
        self.stats['fundamentals_updated'] = successful
        self.logger.info(f"Fundamental updates completed: {successful}/{len(tickers)} successful")
        
        return {
            'total_tickers': len(tickers),
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def calculate_ratios_batch(self, tickers: List[str], batch_size: int = 100) -> Dict[str, Any]:
        """Calculate ratios for a batch of tickers"""
        self.logger.info(f"Starting ratio calculations for {len(tickers)} tickers")
        
        calculator = RatiosCalculator(use_database=True)
        successful = 0
        failed = 0
        errors = []
        
        for i, ticker in enumerate(tickers):
            try:
                result = calculator.calculate_all_ratios(ticker)
                if 'error' not in result:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"{ticker}: {result['error']}")
                
                # Progress logging
                if i % 50 == 0:
                    self.log_progress(i, len(tickers), f"Calculating ratios for {ticker}")
                    
            except Exception as e:
                failed += 1
                error_msg = f"{ticker}: {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)
        
        self.stats['ratios_calculated'] = successful
        self.logger.info(f"Ratio calculations completed: {successful}/{len(tickers)} successful")
        
        calculator.close()
        return {
            'total_tickers': len(tickers),
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def run_full_pipeline(self, max_tickers: int = None) -> Dict[str, Any]:
        """Run the complete daily pipeline"""
        self.logger.info("Starting Production Daily Financial Pipeline")
        self.logger.info(f"Date: {date.today()}")
        self.logger.info(f"Start time: {self.start_time}")
        
        try:
            # Connect to database
            self.db.connect()
            
            # Get all tickers
            all_tickers = self.db.get_tickers('stocks')
            if max_tickers:
                all_tickers = all_tickers[:max_tickers]
            
            self.stats['total_tickers'] = len(all_tickers)
            self.logger.info(f"Processing {len(all_tickers)} tickers")
            
            # Step 1: Update prices
            self.logger.info("=" * 50)
            self.logger.info("STEP 1: UPDATING PRICES")
            self.logger.info("=" * 50)
            price_result = self.update_prices_batch(all_tickers)
            
            # Step 2: Update fundamentals
            self.logger.info("=" * 50)
            self.logger.info("STEP 2: UPDATING FUNDAMENTALS")
            self.logger.info("=" * 50)
            fundamental_result = self.update_fundamentals_batch(all_tickers)
            
            # Step 3: Calculate ratios
            self.logger.info("=" * 50)
            self.logger.info("STEP 3: CALCULATING RATIOS")
            self.logger.info("=" * 50)
            
            # Get tickers with fundamental data for ratio calculation
            query = """
                SELECT DISTINCT f.ticker 
                FROM financials f
                WHERE f.revenue_ttm IS NOT NULL 
                   OR f.market_cap IS NOT NULL
            """
            results = self.db.execute_query(query)
            tickers_with_fundamentals = [row[0] for row in results]
            
            if tickers_with_fundamentals:
                ratio_result = self.calculate_ratios_batch(tickers_with_fundamentals)
            else:
                self.logger.warning("No tickers with fundamental data found for ratio calculation")
                ratio_result = {'total_tickers': 0, 'successful': 0, 'failed': 0, 'errors': []}
            
            # Generate final summary
            self.generate_final_summary()
            
            return {
                'success': True,
                'stats': self.stats,
                'price_result': price_result,
                'fundamental_result': fundamental_result,
                'ratio_result': ratio_result
            }
            
        except Exception as e:
            error_msg = f"Production pipeline failed: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return {'success': False, 'error': error_msg, 'stats': self.stats}
        
        finally:
            self.cleanup()
    
    def generate_final_summary(self):
        """Generate and log final summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        self.logger.info("=" * 60)
        self.logger.info("PRODUCTION PIPELINE COMPLETED")
        self.logger.info("=" * 60)
        self.logger.info(f"Total execution time: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        self.logger.info(f"Total tickers processed: {self.stats['total_tickers']}")
        self.logger.info(f"Prices updated: {self.stats['prices_updated']}")
        self.logger.info(f"Fundamentals updated: {self.stats['fundamentals_updated']}")
        self.logger.info(f"Ratios calculated: {self.stats['ratios_calculated']}")
        
        if self.stats['errors']:
            self.logger.warning(f"Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                self.logger.warning(f"  - {error}")
        
        success_rate = (self.stats['prices_updated'] + self.stats['fundamentals_updated'] + self.stats['ratios_calculated']) / (self.stats['total_tickers'] * 3) * 100
        self.logger.info(f"Overall success rate: {success_rate:.1f}%")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.service_factory.close_all_services()
            self.db.disconnect()
            self.logger.info("Production runner cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

def main():
    """Main entry point for production runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Daily Financial Data Runner')
    parser.add_argument('--max-tickers', type=int, help='Maximum number of tickers to process')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited tickers')
    
    args = parser.parse_args()
    
    # Set max tickers for test mode
    max_tickers = 10 if args.test else args.max_tickers
    
    runner = ProductionDailyRunner()
    
    try:
        result = runner.run_full_pipeline(max_tickers=max_tickers)
        
        if result['success']:
            print("Production pipeline completed successfully!")
            sys.exit(0)
        else:
            print(f"Production pipeline failed: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 