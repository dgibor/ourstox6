#!/usr/bin/env python3
"""
Main Daily Runner - Consolidated Entry Point
Uses IntegratedDailyRunnerV2 as the primary pipeline
"""

import argparse
import logging
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from integrated_daily_runner_v2 import IntegratedDailyRunnerV2
from config import Config

def setup_logging():
    """Setup logging for the main runner"""
    log_filename = f"logs/main_daily_runner_{datetime.now().strftime('%Y%m%d')}.log"
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for daily financial data pipeline"""
    parser = argparse.ArgumentParser(description='Main Daily Financial Data Pipeline')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode with limited tickers')
    parser.add_argument('--max-price-tickers', type=int, default=100, 
                       help='Maximum tickers for price updates')
    parser.add_argument('--max-fundamental-tickers', type=int, default=50, 
                       help='Maximum tickers for fundamental updates')
    parser.add_argument('--validate-config', action='store_true',
                       help='Validate configuration before running')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        runner = IntegratedDailyRunnerV2()
        result = runner.run_complete_daily_pipeline(
            test_mode=args.test,
            max_price_tickers=args.max_price_tickers,
            max_fundamental_tickers=args.max_fundamental_tickers
        )
        
        # Log final results
        logging.info("PIPELINE EXECUTION RESULTS")
        logging.info("=" * 60)
        logging.info(f"Overall Status: {result.get('overall_status', 'unknown')}")
        logging.info(f"Market Status: {result.get('market_status', {})}")
        
        price_update = result.get('price_update', {})
        logging.info(f"Price Updates: {price_update.get('successful', 0)}/{price_update.get('total_tickers', 0)} successful")
        
        fundamentals_update = result.get('fundamentals_update', {})
        logging.info(f"Fundamentals Updates: {fundamentals_update.get('successful', 0)}/{fundamentals_update.get('total_tickers', 0)} successful")
        
        technical_indicators = result.get('technical_indicators', {})
        logging.info(f"Technical Indicators: {technical_indicators.get('successful', 0)}/{technical_indicators.get('total_tickers', 0)} successful")
        
        logging.info("=" * 60)
        
        # Exit with appropriate code
        if result.get('overall_status') == 'success':
            logging.info("Pipeline completed successfully")
            sys.exit(0)
        else:
            logging.error("Pipeline completed with errors")
            sys.exit(1)
    except KeyboardInterrupt:
        logging.warning("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Pipeline failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 