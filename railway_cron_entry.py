#!/usr/bin/env python3
"""
Railway Cron Entry Point for Daily Trading System

This script is specifically designed for Railway deployments.
It handles path issues and provides better error reporting.
Enhanced version with better Railway compatibility.
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
    
    # List all environment variables for debugging
    logger.info("🔍 Environment variables:")
    for key, value in os.environ.items():
        if key in ['PYTHONPATH', 'WORKDIR', 'PWD', 'HOME']:
            logger.info(f"  {key}: {value}")
    
    # Check if we're in the expected Railway directory
    expected_dirs = ['/app', '/workspace', cwd]
    for expected_dir in expected_dirs:
        if os.path.exists(expected_dir):
            logger.info(f"✅ Found directory: {expected_dir}")
            if expected_dir not in sys.path:
                sys.path.insert(0, expected_dir)
                logger.info(f"✅ Added {expected_dir} to Python path")
    
    # Add daily_run directory to path
    daily_run_dir = os.path.join(cwd, 'daily_run')
    if os.path.exists(daily_run_dir) and daily_run_dir not in sys.path:
        sys.path.insert(0, daily_run_dir)
        logger.info(f"✅ Added {daily_run_dir} to Python path")
    
    # Add utility_functions directory to path
    utility_dir = os.path.join(cwd, 'utility_functions')
    if os.path.exists(utility_dir) and utility_dir not in sys.path:
        sys.path.insert(0, utility_dir)
        logger.info(f"✅ Added {utility_dir} to Python path")
    
    # List all files in current directory
    logger.info("📋 All files in current directory:")
    try:
        for file in os.listdir(cwd):
            logger.info(f"  - {file}")
    except Exception as e:
        logger.error(f"❌ Error listing directory: {e}")
    
    # Check if daily_run directory exists and list its contents
    if os.path.exists(daily_run_dir):
        logger.info(f"📋 Files in {daily_run_dir}:")
        try:
            for file in os.listdir(daily_run_dir):
                logger.info(f"  - {file}")
        except Exception as e:
            logger.error(f"❌ Error listing daily_run directory: {e}")
    else:
        logger.warning(f"⚠️ daily_run directory not found at {daily_run_dir}")
    
    # Log Python path
    logger.info("📋 Current Python path:")
    for path in sys.path:
        logger.info(f"  - {path}")

def main():
    """Run the daily trading system once and exit"""
    logger.info("🚀 RAILWAY CRON-ONLY DAILY TRADING SYSTEM STARTED")
    logger.info(f"⏰ Execution Time: {datetime.now()}")
    
    try:
        # Setup paths first
        setup_paths()
        
        # Try to import the daily trading system
        logger.info("📦 Attempting to import DailyTradingSystem...")
        
        DailyTradingSystem = None
        
        # Try multiple import strategies
        import_strategies = [
            ("daily_run.daily_trading_system", "DailyTradingSystem"),
            ("daily_trading_system", "DailyTradingSystem"),
            ("daily_run.daily_trading_system", "DailyTradingSystem")
        ]
        
        for module_path, class_name in import_strategies:
            try:
                if "." in module_path:
                    # Handle module.submodule imports
                    module_parts = module_path.split(".")
                    module = __import__(module_parts[0])
                    for part in module_parts[1:]:
                        module = getattr(module, part)
                    DailyTradingSystem = getattr(module, class_name)
                else:
                    # Handle direct imports
                    module = __import__(module_path)
                    DailyTradingSystem = getattr(module, class_name)
                
                logger.info(f"✅ DailyTradingSystem imported successfully from {module_path}")
                break
                
            except ImportError as e:
                logger.warning(f"⚠️ Failed to import from {module_path}: {e}")
                continue
            except AttributeError as e:
                logger.warning(f"⚠️ Failed to get {class_name} from {module_path}: {e}")
                continue
        
        if DailyTradingSystem is None:
            raise ImportError("Could not import DailyTradingSystem from any available source")
        
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