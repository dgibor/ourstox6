#!/usr/bin/env python3
"""
Test Railway Deployment and Logging
Simple script to verify Railway deployment is working
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging to stdout for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - RAILWAY TEST - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_railway_environment():
    """Test Railway environment variables and paths"""
    logger.info("🚀 RAILWAY DEPLOYMENT TEST STARTED")
    logger.info(f"⏰ Test Time: {datetime.now()}")
    
    # Test environment variables
    logger.info("🔧 Environment Variables:")
    logger.info(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'NOT SET')}")
    logger.info(f"  PYTHONUNBUFFERED: {os.getenv('PYTHONUNBUFFERED', 'NOT SET')}")
    logger.info(f"  TZ: {os.getenv('TZ', 'NOT SET')}")
    logger.info(f"  RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT SET')}")
    
    # Test current directory
    cwd = os.getcwd()
    logger.info(f"📁 Current working directory: {cwd}")
    
    # List files in current directory
    logger.info("📋 Files in current directory:")
    try:
        files = os.listdir(cwd)
        for file in files[:10]:  # Show first 10 files
            logger.info(f"  - {file}")
        if len(files) > 10:
            logger.info(f"  ... and {len(files) - 10} more files")
    except Exception as e:
        logger.error(f"❌ Error listing files: {e}")
    
    # Test Python path
    logger.info("🐍 Python path:")
    for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
        logger.info(f"  {i}: {path}")
    if len(sys.path) > 5:
        logger.info(f"  ... and {len(sys.path) - 5} more paths")
    
    # Test basic imports
    logger.info("📦 Testing basic imports:")
    try:
        import psycopg2
        logger.info("✅ psycopg2 imported successfully")
    except ImportError as e:
        logger.error(f"❌ psycopg2 import failed: {e}")
    
    try:
        import pandas
        logger.info("✅ pandas imported successfully")
    except ImportError as e:
        logger.error(f"❌ pandas import failed: {e}")
    
    # Test daily_run imports
    logger.info("📦 Testing daily_run imports:")
    try:
        sys.path.append('daily_run')
        from daily_trading_system import DailyTradingSystem
        logger.info("✅ DailyTradingSystem imported successfully")
    except ImportError as e:
        logger.error(f"❌ DailyTradingSystem import failed: {e}")
        logger.error(f"🔍 Error details: {type(e).__name__}: {e}")
    
    # Test database connection
    logger.info("🗄️ Testing database connection:")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        logger.info("✅ Database connection successful")
        conn.close()
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    logger.info("✅ RAILWAY DEPLOYMENT TEST COMPLETED")
    return True

if __name__ == "__main__":
    success = test_railway_environment()
    sys.exit(0 if success else 1) 