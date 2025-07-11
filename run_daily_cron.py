#!/usr/bin/env python3
"""
Railway Cron Entry Point for Daily Trading System

This script is specifically designed to run the daily trading system
from Railway's cron job environment, handling path setup and logging.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add daily_run directory to path
daily_run_dir = os.path.join(current_dir, 'daily_run')
sys.path.insert(0, daily_run_dir)

def setup_railway_logging(is_backup=False):
    """Setup logging for Railway environment"""
    job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
    log_format = f'%(asctime)s - Railway {job_type} - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),  # Railway captures stdout
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info(f"🚀 RAILWAY {job_type} JOB STARTED")
    logger.info(f"⏰ Execution Time: {datetime.now()}")
    logger.info(f"📁 Working Directory: {os.getcwd()}")
    logger.info(f"🐍 Python Path: {sys.path[:3]}")  # First 3 paths
    
    # Log environment variables
    logger.info("🌍 Environment Variables:")
    env_vars = ['PYTHONPATH', 'TZ', 'DB_HOST', 'DB_NAME', 'FMP_API_KEY']
    for var in env_vars:
        value = os.getenv(var, 'Not Set')
        if 'API_KEY' in var and value != 'Not Set':
            value = f"{value[:8]}..." if len(value) > 8 else "Set"
        logger.info(f"  {var}: {value}")
    
    logger.info("=" * 60)
    
    return logger

def run_daily_trading_system(is_backup=False):
    """Run the daily trading system with Railway-specific setup"""
    logger = setup_railway_logging(is_backup)
    
    try:
        # Check if this is a backup job and primary already ran
        if is_backup:
            logger.info("🔄 This is a backup cron job - checking if primary already succeeded...")
            # You could add logic here to check if the primary job already completed successfully
            # For now, we'll just log and continue
            logger.info("⏭️  Proceeding with backup execution...")
        
        # Import and run the daily trading system
        logger.info("📊 Importing Daily Trading System...")
        
        # Try to import from daily_run directory
        try:
            from daily_run.daily_trading_system import DailyTradingSystem
            logger.info("✅ Successfully imported DailyTradingSystem")
        except ImportError as e:
            logger.error(f"❌ Failed to import DailyTradingSystem: {e}")
            logger.info("🔄 Trying alternative import path...")
            
            # Alternative import method
            import importlib.util
            module_path = os.path.join(daily_run_dir, 'daily_trading_system.py')
            if os.path.exists(module_path):
                spec = importlib.util.spec_from_file_location("daily_trading_system", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                DailyTradingSystem = module.DailyTradingSystem
                logger.info("✅ Successfully imported using alternative method")
            else:
                raise ImportError(f"Cannot find daily_trading_system.py at {module_path}")
        
        # Initialize and run the system
        logger.info("🏗️  Initializing Daily Trading System...")
        trading_system = DailyTradingSystem()
        
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
        
        job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
        logger.info("=" * 60)
        logger.info(f"✅ RAILWAY {job_type} JOB COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
        logger.error("=" * 60)
        logger.error(f"❌ RAILWAY {job_type} JOB FAILED")
        logger.error(f"🚨 Error: {str(e)}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        
        # Log additional debug info
        logger.error("🔧 Debug Information:")
        logger.error(f"  Current Directory: {os.getcwd()}")
        logger.error(f"  Python Version: {sys.version}")
        logger.error(f"  Available Files: {os.listdir('.')[:10]}")  # First 10 files
        
        if os.path.exists('daily_run'):
            logger.error(f"  Daily Run Files: {os.listdir('daily_run')[:10]}")
        else:
            logger.error("  daily_run directory not found!")
        
        # Import traceback for better error logging
        import traceback
        logger.error("🔍 Full Traceback:")
        logger.error(traceback.format_exc())
        
        logger.error("=" * 60)
        
        # Re-raise the exception so Railway knows the job failed
        raise

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Railway Daily Trading System Cron Job')
    parser.add_argument('--backup', action='store_true', help='Run as backup cron job')
    args = parser.parse_args()
    
    try:
        run_daily_trading_system(is_backup=args.backup)
        sys.exit(0)
    except Exception as e:
        sys.exit(1) 