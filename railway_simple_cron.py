#!/usr/bin/env python3
"""
Simple Railway Cron Entry Point
Direct execution without complex path detection
"""

import os
import sys
import logging
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SIMPLE CRON - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    """Simple cron job that runs the daily trading system"""
    logger.info("🚀 SIMPLE RAILWAY CRON STARTED")
    logger.info(f"⏰ Execution Time: {datetime.now()}")
    
    try:
        # Add current directory to Python path
        current_dir = os.getcwd()
        logger.info(f"📁 Current directory: {current_dir}")
        
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            logger.info(f"✅ Added {current_dir} to Python path")
        
        # List files in current directory
        logger.info("📋 Files in current directory:")
        for file in os.listdir(current_dir):
            logger.info(f"  - {file}")
        
        # Try to import and run the daily trading system
        logger.info("📦 Attempting to import DailyTradingSystem...")
        
        try:
            # Try importing from daily_run first
            from daily_run.daily_trading_system import DailyTradingSystem
            logger.info("✅ DailyTradingSystem imported from daily_run")
        except ImportError:
            try:
                # Try direct import
                from daily_trading_system import DailyTradingSystem
                logger.info("✅ DailyTradingSystem imported directly")
            except ImportError as e:
                logger.error(f"❌ Failed to import DailyTradingSystem: {e}")
                raise
        
        # Initialize and run
        logger.info("🔧 Initializing DailyTradingSystem...")
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
        
        logger.info("✅ SIMPLE CRON JOB COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        logger.error(f"❌ SIMPLE CRON JOB FAILED: {e}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        
        # Import traceback for better error logging
        import traceback
        logger.error("🔍 Full Traceback:")
        logger.error(traceback.format_exc())
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
