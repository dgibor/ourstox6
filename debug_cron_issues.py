#!/usr/bin/env python3
"""
Debug Cron Issues Script

This script helps identify the exact problems causing the Railway cron job to crash.
Run this manually to get detailed error information.
"""

import os
import sys
import logging
import traceback
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DEBUG - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables and configuration"""
    logger.info("🔍 CHECKING ENVIRONMENT VARIABLES")
    logger.info("=" * 50)
    
    critical_vars = [
        'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT',
        'FMP_API_KEY', 'ALPHA_VANTAGE_API_KEY', 'FINNHUB_API_KEY'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'KEY' in var:
                logger.info(f"✅ {var}: {'*' * min(len(value), 8)}...")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: NOT SET")
    
    logger.info(f"📁 Working Directory: {os.getcwd()}")
    logger.info(f"🐍 Python Version: {sys.version}")
    logger.info(f"🐍 Python Path: {sys.path[:3]}")

def check_dependencies():
    """Check if all required packages are installed"""
    logger.info("\n🔍 CHECKING DEPENDENCIES")
    logger.info("=" * 50)
    
    required_packages = [
        'psycopg2', 'pandas', 'numpy', 'yfinance', 'requests', 
        'python-dotenv', 'ratelimit', 'fastapi', 'uvicorn', 'pytz',
        'pandas_market_calendars', 'pydantic', 'psutil'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package}: Available")
        except ImportError as e:
            logger.error(f"❌ {package}: {e}")

def check_file_structure():
    """Check if all required files exist"""
    logger.info("\n🔍 CHECKING FILE STRUCTURE")
    logger.info("=" * 50)
    
    required_files = [
        'daily_run/daily_trading_system.py',
        'daily_run/common_imports.py',
        'daily_run/database.py',
        'daily_run/error_handler.py',
        'daily_run/monitoring.py',
        'daily_run/batch_price_processor.py',
        'daily_run/earnings_based_fundamental_processor.py',
        'daily_run/enhanced_multi_service_manager.py',
        'daily_run/check_market_schedule.py',
        'daily_run/data_validator.py',
        'daily_run/circuit_breaker.py',
        'requirements.txt',
        'railway.toml'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_path}: Exists")
        else:
            logger.error(f"❌ {file_path}: MISSING")

def test_database_connection():
    """Test database connection"""
    logger.info("\n🔍 TESTING DATABASE CONNECTION")
    logger.info("=" * 50)
    
    try:
        import psycopg2
        from psycopg2 import OperationalError
        
        db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Check if all config values are present
        missing_config = [k for k, v in db_config.items() if not v]
        if missing_config:
            logger.error(f"❌ Missing database config: {missing_config}")
            return False
        
        # Test connection
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ Database connected: {version[0]}")
        
        # Test basic table access
        cursor.execute("SELECT COUNT(*) FROM stocks;")
        count = cursor.fetchone()
        logger.info(f"✅ Stocks table accessible: {count[0]} records")
        
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Database test error: {e}")
        return False

def test_imports():
    """Test importing key modules"""
    logger.info("\n🔍 TESTING IMPORTS")
    logger.info("=" * 50)
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Add daily_run directory to path
    daily_run_dir = os.path.join(current_dir, 'daily_run')
    sys.path.insert(0, daily_run_dir)
    
    modules_to_test = [
        ('daily_run.common_imports', 'common_imports'),
        ('daily_run.database', 'DatabaseManager'),
        ('daily_run.error_handler', 'ErrorHandler'),
        ('daily_run.monitoring', 'SystemMonitor'),
        ('daily_run.batch_price_processor', 'BatchPriceProcessor'),
        ('daily_run.earnings_based_fundamental_processor', 'EarningsBasedFundamentalProcessor'),
        ('daily_run.enhanced_multi_service_manager', 'get_multi_service_manager'),
        ('daily_run.check_market_schedule', 'check_market_open_today'),
        ('daily_run.data_validator', 'data_validator'),
        ('daily_run.circuit_breaker', 'circuit_manager'),
        ('daily_run.daily_trading_system', 'DailyTradingSystem')
    ]
    
    for module_path, item_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[item_name])
            getattr(module, item_name)
            logger.info(f"✅ {module_path}.{item_name}: Imported successfully")
        except ImportError as e:
            logger.error(f"❌ {module_path}.{item_name}: Import failed - {e}")
        except AttributeError as e:
            logger.error(f"❌ {module_path}.{item_name}: Attribute not found - {e}")
        except Exception as e:
            logger.error(f"❌ {module_path}.{item_name}: Unexpected error - {e}")

def test_daily_trading_system():
    """Test initializing the daily trading system"""
    logger.info("\n🔍 TESTING DAILY TRADING SYSTEM INITIALIZATION")
    logger.info("=" * 50)
    
    try:
        # Add paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        daily_run_dir = os.path.join(current_dir, 'daily_run')
        sys.path.insert(0, current_dir)
        sys.path.insert(0, daily_run_dir)
        
        # Try to import and initialize
        from daily_run.daily_trading_system import DailyTradingSystem
        
        logger.info("✅ DailyTradingSystem imported successfully")
        
        # Try to initialize
        trading_system = DailyTradingSystem()
        logger.info("✅ DailyTradingSystem initialized successfully")
        
        # Test basic methods
        if hasattr(trading_system, 'db'):
            logger.info("✅ Database manager available")
        else:
            logger.error("❌ Database manager not available")
            
        if hasattr(trading_system, 'error_handler'):
            logger.info("✅ Error handler available")
        else:
            logger.error("❌ Error handler not available")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ DailyTradingSystem test failed: {e}")
        logger.error(f"🔍 Full traceback:")
        logger.error(traceback.format_exc())
        return False

def test_api_keys():
    """Test API key configuration"""
    logger.info("\n🔍 TESTING API KEYS")
    logger.info("=" * 50)
    
    api_keys = {
        'FMP_API_KEY': 'Financial Modeling Prep',
        'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage',
        'FINNHUB_API_KEY': 'Finnhub'
    }
    
    for key_name, service_name in api_keys.items():
        key_value = os.getenv(key_name)
        if key_value:
            logger.info(f"✅ {service_name}: Key configured ({len(key_value)} chars)")
        else:
            logger.warning(f"⚠️  {service_name}: No key configured")

def main():
    """Run all diagnostic tests"""
    logger.info("🚀 STARTING CRON DEBUG DIAGNOSTICS")
    logger.info("=" * 60)
    logger.info(f"⏰ Timestamp: {datetime.now()}")
    logger.info("=" * 60)
    
    # Run all tests
    check_environment()
    check_dependencies()
    check_file_structure()
    db_ok = test_database_connection()
    test_imports()
    system_ok = test_daily_trading_system()
    test_api_keys()
    
    # Summary
    logger.info("\n📊 DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)
    
    if db_ok and system_ok:
        logger.info("✅ All critical tests passed - cron should work")
    else:
        logger.error("❌ Critical issues found - cron will likely fail")
        
        if not db_ok:
            logger.error("  - Database connection failed")
        if not system_ok:
            logger.error("  - Daily trading system initialization failed")
    
    logger.info("\n🔧 NEXT STEPS:")
    logger.info("1. Fix any ❌ errors above")
    logger.info("2. Set missing environment variables")
    logger.info("3. Install missing dependencies")
    logger.info("4. Run this script again to verify fixes")
    logger.info("5. Test the cron job again")

if __name__ == "__main__":
    main() 