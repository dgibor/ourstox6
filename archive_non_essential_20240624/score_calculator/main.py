"""
Main Entry Point for Score Calculator

This script provides the main interface for running the scoring system.
It can be run independently or integrated into the daily run pipeline.
"""

import logging
import argparse
import sys
from datetime import date
from typing import Optional

from ..database import DatabaseManager
from .score_orchestrator import ScoreOrchestrator
from .schema_manager import ScoreSchemaManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/score_calculator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def setup_database() -> bool:
    """Setup database schema and tables"""
    try:
        logger.info("Setting up database schema...")
        
        db = DatabaseManager()
        schema_manager = ScoreSchemaManager(db)
        
        # Create tables if they don't exist
        success = schema_manager.create_tables()
        
        if success:
            logger.info("Database schema setup completed")
        else:
            logger.error("Database schema setup failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False


def run_scoring(max_tickers: int = 1000, max_time_hours: int = 3, 
                force_recalculate: bool = False, ticker: Optional[str] = None) -> bool:
    """Run the scoring process"""
    try:
        logger.info("Starting scoring process...")
        
        # Initialize orchestrator
        orchestrator = ScoreOrchestrator()
        
        if ticker:
            # Process single ticker
            logger.info(f"Processing single ticker: {ticker}")
            calculation_date = date.today()
            result = orchestrator.process_single_ticker(ticker, calculation_date, force_recalculate)
            
            if result['technical_success'] or result['fundamental_success'] or result['analyst_success']:
                logger.info(f"Successfully processed {ticker}")
                return True
            else:
                logger.error(f"Failed to process {ticker}: {result['errors']}")
                return False
        else:
            # Run full daily scoring
            result = orchestrator.run_daily_scoring(max_tickers, max_time_hours, force_recalculate)
            
            if result['success']:
                batch_result = result['batch_result']
                logger.info(f"Daily scoring completed successfully")
                logger.info(f"   Processed: {batch_result['processed_count']}/{batch_result['total_count']} tickers")
                logger.info(f"   Technical success rate: {batch_result['technical_success_rate']:.1%}")
                logger.info(f"   Fundamental success rate: {batch_result['fundamental_success_rate']:.1%}")
                logger.info(f"   Analyst success rate: {batch_result['analyst_success_rate']:.1%}")
                return True
            else:
                logger.error(f"Daily scoring failed: {result.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"Error in scoring process: {e}")
        return False


def get_system_status() -> bool:
    """Get and display system status"""
    try:
        logger.info("Getting system status...")
        
        orchestrator = ScoreOrchestrator()
        status = orchestrator.get_scoring_status()
        
        if status['system_status'] == 'operational':
            logger.info("System Status: Operational")
            logger.info(f"   Total active tickers: {status['total_active_tickers']}")
            
            if status['daily_stats']:
                latest = status['daily_stats'][0]
                logger.info(f"   Latest daily stats ({latest['date']}):")
                logger.info(f"     Total records: {latest['total_records']}")
                logger.info(f"     Technical success: {latest['technical_success']}")
                logger.info(f"     Fundamental success: {latest['fundamental_success']}")
                logger.info(f"     Analyst success: {latest['analyst_success']}")
            
            return True
        else:
            logger.error(f"System Status: {status['system_status']}")
            if 'error' in status:
                logger.error(f"   Error: {status['error']}")
            return False
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Stock Score Calculator')
    parser.add_argument('--setup', action='store_true', 
                       help='Setup database schema and tables')
    parser.add_argument('--run', action='store_true',
                       help='Run the scoring process')
    parser.add_argument('--status', action='store_true',
                       help='Get system status')
    parser.add_argument('--max-tickers', type=int, default=1000,
                       help='Maximum number of tickers to process (default: 1000)')
    parser.add_argument('--max-time', type=int, default=3,
                       help='Maximum execution time in hours (default: 3)')
    parser.add_argument('--force', action='store_true',
                       help='Force recalculation of existing scores')
    parser.add_argument('--ticker', type=str,
                       help='Process single ticker only')
    
    args = parser.parse_args()
    
    # If no specific action specified, default to run
    if not any([args.setup, args.run, args.status]):
        args.run = True
    
    success = True
    
    # Setup database if requested
    if args.setup:
        success = setup_database()
    
    # Get status if requested
    if args.status and success:
        success = get_system_status()
    
    # Run scoring if requested
    if args.run and success:
        success = run_scoring(
            max_tickers=args.max_tickers,
            max_time_hours=args.max_time,
            force_recalculate=args.force,
            ticker=args.ticker
        )
    
    if success:
        logger.info("All operations completed successfully")
        sys.exit(0)
    else:
        logger.error("Some operations failed")
        sys.exit(1)


if __name__ == '__main__':
    main() 