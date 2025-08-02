#!/usr/bin/env python3
"""
Simplified test version of Railway Daily Trading System Cron Job
This version will definitely produce output to test Railway logging
"""

import os
import sys
import logging
from datetime import datetime

def main():
    """Main test function"""
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - TEST CRON - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Step 1: Basic startup
    logger.info("=" * 60)
    logger.info("🚀 RAILWAY CRON TEST STARTED")
    logger.info(f"⏰ Time: {datetime.now()}")
    logger.info(f"📁 Directory: {os.getcwd()}")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    
    # Step 2: Check environment
    logger.info("🔍 Checking environment variables:")
    env_vars = ['PYTHONPATH', 'TZ', 'DB_HOST', 'DB_NAME', 'FMP_API_KEY']
    for var in env_vars:
        value = os.getenv(var, 'NOT SET')
        if var == 'FMP_API_KEY':
            value = 'SET' if value != 'NOT SET' else 'NOT SET'
        logger.info(f"   {var}: {value}")
    
    # Step 3: Check file system
    logger.info("📂 Checking file system:")
    logger.info(f"   Current files: {len(os.listdir('.'))}")
    if os.path.exists('daily_run'):
        logger.info(f"   daily_run files: {len(os.listdir('daily_run'))}")
    else:
        logger.info("   ❌ daily_run directory not found")
    
    # Step 4: Test imports
    logger.info("📦 Testing imports:")
    try:
        sys.path.insert(0, 'daily_run')
        from daily_trading_system import DailyTradingSystem
        logger.info("   ✅ DailyTradingSystem imported")
    except Exception as e:
        logger.error(f"   ❌ DailyTradingSystem import failed: {e}")
    
    try:
        sys.path.insert(0, 'daily_run/archive_20250622_215640')
        from fill_history import fill_history
        logger.info("   ✅ fill_history imported")
    except Exception as e:
        logger.error(f"   ❌ fill_history import failed: {e}")
    
    # Step 5: Test database connection
    logger.info("🗄️ Testing database connection:")
    try:
        from daily_run.config import Config
        db_config = Config.get_db_config()
        logger.info(f"   ✅ Database config loaded: {db_config['host']}:{db_config['port']}")
    except Exception as e:
        logger.error(f"   ❌ Database config failed: {e}")
    
    # Step 6: Completion
    logger.info("✅ RAILWAY CRON TEST COMPLETED")
    logger.info("=" * 60)
    
    # Force flush
    sys.stdout.flush()

if __name__ == "__main__":
    main() 