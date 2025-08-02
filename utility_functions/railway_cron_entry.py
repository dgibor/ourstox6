#!/usr/bin/env python3
"""
Railway Cron Entry Point for Daily Trading System

This script is specifically designed for Railway deployments.
It handles path issues and provides better error reporting.
"""

import os
import sys
import logging
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - RAILWAY CRON - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def setup_paths():
    """Setup Python paths for Railway deployment"""
    logger.info("🔧 Setting up Python paths...")
    
    # Get the current working directory
    cwd = os.getcwd()
    logger.info(f"📁 Current working directory: {cwd}")
    
    # Add current directory to Python path
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
        logger.info(f"✅ Added {cwd} to Python path")
    
    # Add daily_run directory to path
    daily_run_dir = os.path.join(cwd, 'daily_run')
    if os.path.exists(daily_run_dir) and daily_run_dir not in sys.path:
        sys.path.insert(0, daily_run_dir)
        logger.info(f"✅ Added {daily_run_dir} to Python path")
    
    # List all Python files in current directory
    logger.info("📋 Python files in current directory:")
    for file in os.listdir(cwd):
        if file.endswith('.py'):
            logger.info(f"  - {file}")
    
    # Check if daily_run directory exists and list its contents
    if os.path.exists(daily_run_dir):
        logger.info(f"📋 Python files in {daily_run_dir}:")
        for file in os.listdir(daily_run_dir):
            if file.endswith('.py'):
                logger.info(f"  - {file}")

def main():
    """Run the daily trading system once and exit"""
    logger.info("🚀 RAILWAY CRON-ONLY DAILY TRADING SYSTEM STARTED")
    logger.info(f"⏰ Execution Time: {datetime.now()}")
    
    try:
        # Setup paths first
        setup_paths()
        
        # Try to import the daily trading system
        logger.info("📦 Attempting to import DailyTradingSystem...")
        
        try:
            from daily_run.daily_trading_system import DailyTradingSystem
            logger.info("✅ DailyTradingSystem imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import DailyTradingSystem: {e}")
            logger.error("🔍 Trying alternative import paths...")
            
            # Try direct import
            try:
                from daily_trading_system import DailyTradingSystem
                logger.info("✅ DailyTradingSystem imported via direct import")
            except ImportError as e2:
                logger.error(f"❌ Direct import also failed: {e2}")
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
        
        logger.info("✅ RAILWAY CRON-ONLY JOB COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        logger.error(f"❌ RAILWAY CRON-ONLY JOB FAILED: {e}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        
        # Import traceback for better error logging
        import traceback
        logger.error("🔍 Full Traceback:")
        logger.error(traceback.format_exc())
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 