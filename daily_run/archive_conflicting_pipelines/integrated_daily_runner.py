#!/usr/bin/env python3
"""
Integrated Daily Runner
Runs the complete daily pipeline:
1. Price updates (priority)
2. Fundamentals updates (only for missing/after earnings)
3. Rate limiting and error handling
"""

import logging
import argparse
from datetime import datetime
from typing import Dict
from production_daily_runner import ProductionDailyRunner
from daily_fundamentals_updater import DailyFundamentalsUpdater
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integrated_daily.log'),
        logging.StreamHandler()
    ]
)

class IntegratedDailyRunner:
    def __init__(self):
        self.config = Config()
        self.price_runner = ProductionDailyRunner()
        self.fundamentals_updater = DailyFundamentalsUpdater()
        
    def run_complete_daily_pipeline(self, 
                                  test_mode: bool = False, 
                                  max_price_tickers: int = 100,
                                  max_fundamental_tickers: int = 50) -> Dict:
        """
        Run the complete daily pipeline
        """
        start_time = datetime.now()
        logging.info("=" * 80)
        logging.info("STARTING INTEGRATED DAILY PIPELINE")
        logging.info("=" * 80)
        
        pipeline_results = {
            'start_time': start_time,
            'price_update': {},
            'fundamentals_update': {},
            'overall_status': 'unknown'
        }
        
        try:
            # Step 1: Price Updates (Priority)
            logging.info("\n" + "="*60)
            logging.info("STEP 1: PRICE UPDATES (PRIORITY)")
            logging.info("=" * 60)
            
            price_result = self.price_runner.run_full_pipeline(
                max_tickers=max_price_tickers
            )
            
            pipeline_results['price_update'] = price_result
            logging.info(f"Price update completed: {price_result}")
            
            if price_result.get('status') and price_result.get('status') != 'success':
                logging.error("Price update failed, stopping pipeline")
                pipeline_results['overall_status'] = 'failed_price'
                return pipeline_results
            
            # Step 2: Fundamentals Updates (Only missing/after earnings)
            logging.info("\n" + "="*60)
            logging.info("STEP 2: FUNDAMENTALS UPDATES")
            logging.info("=" * 60)
            
            fundamentals_result = self.fundamentals_updater.run_daily_update(
                max_tickers=max_fundamental_tickers
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
            self.fundamentals_updater.close()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info("\n" + "="*80)
        logging.info("INTEGRATED DAILY PIPELINE COMPLETE")
        logging.info("=" * 80)
        logging.info(f"Overall Status: {pipeline_results['overall_status']}")
        logging.info(f"Total Duration: {duration:.2f} seconds")
        logging.info(f"Price Updates: {pipeline_results['price_update']}")
        logging.info(f"Fundamentals Updates: {pipeline_results['fundamentals_update']}")
        logging.info("=" * 80)
        
        return pipeline_results

def main():
    parser = argparse.ArgumentParser(description='Integrated Daily Pipeline Runner')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited tickers')
    parser.add_argument('--max-price-tickers', type=int, default=100, help='Maximum tickers for price updates')
    parser.add_argument('--max-fundamental-tickers', type=int, default=50, help='Maximum tickers for fundamental updates')
    
    args = parser.parse_args()
    
    runner = IntegratedDailyRunner()
    
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
        print(f"\nERROR: Pipeline failed: {e}")

if __name__ == "__main__":
    main() 