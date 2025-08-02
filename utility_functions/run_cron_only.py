#!/usr/bin/env python3
"""
Cron-Only Entry Point for Daily Trading System

This script runs the daily trading system once and exits.
Used for Railway deployments that only need scheduled data processing.
"""

import os
import sys
import logging
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CRON ONLY - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    """Run the daily trading system once and exit"""
    logger.info("🚀 CRON-ONLY DAILY TRADING SYSTEM STARTED")
    logger.info(f"⏰ Execution Time: {datetime.now()}")
    logger.info("📁 Working Directory: %s", os.getcwd())
    
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Add daily_run directory to path
        daily_run_dir = os.path.join(current_dir, 'daily_run')
        sys.path.insert(0, daily_run_dir)
        
        # Import and run the daily trading system
        from daily_run.daily_trading_system import DailyTradingSystem
        
        logger.info("✅ DailyTradingSystem imported successfully")
        
        # Initialize and run
        trading_system = DailyTradingSystem()
        logger.info("✅ DailyTradingSystem initialized successfully")
        
        # Run the daily process
        logger.info("🚀 Starting daily trading process...")
        result = trading_system.run_daily_trading_process()
        
        # Log results
        if result:
            logger.info("📈 DAILY TRADING PROCESS COMPLETED SUCCESSFULLY")
            logger.info("📊 Results Summary:")
            for key, value in result.items():
                if isinstance(value, dict):
                    logger.info(f"  {key}: {len(value)} items")
                else:
                    logger.info(f"  {key}: {value}")
        else:
            logger.warning("⚠️  Daily trading process returned no results")
        
        logger.info("✅ CRON-ONLY JOB COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        logger.error(f"❌ CRON-ONLY JOB FAILED: {e}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        
        # Import traceback for better error logging
        import traceback
        logger.error("🔍 Full Traceback:")
        logger.error(traceback.format_exc())
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 