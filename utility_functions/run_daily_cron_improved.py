#!/usr/bin/env python3
"""
Improved Railway Cron Entry Point for Daily Trading System

This script provides enhanced error handling, detailed logging, and step-by-step
execution tracking to help identify exactly where the cron job fails.
"""

import os
import sys
import logging
import argparse
import traceback
from datetime import datetime

def setup_enhanced_logging(is_backup=False):
    """Setup enhanced logging for Railway environment"""
    job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
    
    # Create a more detailed log format
    log_format = f'%(asctime)s - Railway {job_type} - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),  # Railway captures stdout
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Log startup information
    logger.info("=" * 80)
    logger.info(f"🚀 RAILWAY {job_type} JOB STARTED")
    logger.info(f"⏰ Execution Time: {datetime.now()}")
    logger.info(f"📁 Working Directory: {os.getcwd()}")
    logger.info(f"🐍 Python Version: {sys.version}")
    logger.info(f"🐍 Python Executable: {sys.executable}")
    logger.info(f"🐍 Python Path (first 5): {sys.path[:5]}")
    
    # Log environment variables
    logger.info("🌍 Environment Variables:")
    env_vars = [
        'PYTHONPATH', 'TZ', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT',
        'FMP_API_KEY', 'ALPHA_VANTAGE_API_KEY', 'FINNHUB_API_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'Not Set')
        if 'PASSWORD' in var or 'KEY' in var:
            if value != 'Not Set':
                value = f"{value[:8]}..." if len(value) > 8 else "Set"
        logger.info(f"  {var}: {value}")
    
    logger.info("=" * 80)
    
    return logger

def check_prerequisites(logger):
    """Check all prerequisites before running the system"""
    logger.info("🔍 STEP 1: CHECKING PREREQUISITES")
    logger.info("-" * 50)
    
    # Check if we're in the right directory
    current_dir = os.getcwd()
    logger.info(f"📁 Current directory: {current_dir}")
    
    # Check if daily_run directory exists
    daily_run_path = os.path.join(current_dir, 'daily_run')
    if os.path.exists(daily_run_path):
        logger.info(f"✅ daily_run directory found: {daily_run_path}")
    else:
        logger.error(f"❌ daily_run directory not found: {daily_run_path}")
        return False
    
    # Check if key files exist
    key_files = [
        'daily_run/daily_trading_system.py',
        'daily_run/common_imports.py',
        'daily_run/database.py',
        'requirements.txt'
    ]
    
    for file_path in key_files:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_path}: Exists")
        else:
            logger.error(f"❌ {file_path}: MISSING")
            return False
    
    logger.info("✅ All prerequisites met")
    return True

def setup_python_path(logger):
    """Setup Python path for imports"""
    logger.info("🔍 STEP 2: SETTING UP PYTHON PATH")
    logger.info("-" * 50)
    
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        logger.info(f"✅ Added current directory to path: {current_dir}")
        
        # Add daily_run directory to path
        daily_run_dir = os.path.join(current_dir, 'daily_run')
        sys.path.insert(0, daily_run_dir)
        logger.info(f"✅ Added daily_run directory to path: {daily_run_dir}")
        
        # Log final path
        logger.info(f"🐍 Final Python path (first 5): {sys.path[:5]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Python path: {e}")
        return False

def test_database_connection(logger):
    """Test database connection"""
    logger.info("🔍 STEP 3: TESTING DATABASE CONNECTION")
    logger.info("-" * 50)
    
    try:
        import psycopg2
        from psycopg2 import OperationalError
        
        # Check environment variables
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
        
        logger.info("✅ Database environment variables configured")
        
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
        logger.info("✅ Database connection test passed")
        return True
        
    except ImportError as e:
        logger.error(f"❌ psycopg2 not available: {e}")
        return False
    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Database test error: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def test_imports(logger):
    """Test importing key modules"""
    logger.info("🔍 STEP 4: TESTING IMPORTS")
    logger.info("-" * 50)
    
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
    
    failed_imports = []
    
    for module_path, item_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[item_name])
            getattr(module, item_name)
            logger.info(f"✅ {module_path}.{item_name}: Imported successfully")
        except ImportError as e:
            logger.error(f"❌ {module_path}.{item_name}: Import failed - {e}")
            failed_imports.append(f"{module_path}.{item_name}")
        except AttributeError as e:
            logger.error(f"❌ {module_path}.{item_name}: Attribute not found - {e}")
            failed_imports.append(f"{module_path}.{item_name}")
        except Exception as e:
            logger.error(f"❌ {module_path}.{item_name}: Unexpected error - {e}")
            failed_imports.append(f"{module_path}.{item_name}")
    
    if failed_imports:
        logger.error(f"❌ Failed imports: {failed_imports}")
        return False
    
    logger.info("✅ All imports successful")
    return True

def initialize_trading_system(logger):
    """Initialize the daily trading system"""
    logger.info("🔍 STEP 5: INITIALIZING TRADING SYSTEM")
    logger.info("-" * 50)
    
    try:
        from daily_run.daily_trading_system import DailyTradingSystem
        
        logger.info("✅ DailyTradingSystem imported successfully")
        
        # Try to initialize
        trading_system = DailyTradingSystem()
        logger.info("✅ DailyTradingSystem initialized successfully")
        
        # Test basic attributes
        if hasattr(trading_system, 'db'):
            logger.info("✅ Database manager available")
        else:
            logger.error("❌ Database manager not available")
            
        if hasattr(trading_system, 'error_handler'):
            logger.info("✅ Error handler available")
        else:
            logger.error("❌ Error handler not available")
            
        if hasattr(trading_system, 'batch_price_processor'):
            logger.info("✅ Batch price processor available")
        else:
            logger.error("❌ Batch price processor not available")
        
        return trading_system
        
    except Exception as e:
        logger.error(f"❌ DailyTradingSystem initialization failed: {e}")
        logger.error(f"🔍 Full traceback:")
        logger.error(traceback.format_exc())
        return None

def run_trading_process(logger, trading_system):
    """Run the actual trading process"""
    logger.info("🔍 STEP 6: RUNNING TRADING PROCESS")
    logger.info("-" * 50)
    
    try:
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
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Daily trading process failed: {e}")
        logger.error(f"🔍 Full traceback:")
        logger.error(traceback.format_exc())
        return False

def run_daily_trading_system_improved(is_backup=False):
    """Run the daily trading system with enhanced error handling"""
    logger = setup_enhanced_logging(is_backup)
    
    try:
        # Step 1: Check prerequisites
        if not check_prerequisites(logger):
            raise Exception("Prerequisites check failed")
        
        # Step 2: Setup Python path
        if not setup_python_path(logger):
            raise Exception("Python path setup failed")
        
        # Step 3: Test database connection
        if not test_database_connection(logger):
            raise Exception("Database connection test failed")
        
        # Step 4: Test imports
        if not test_imports(logger):
            raise Exception("Import test failed")
        
        # Step 5: Initialize trading system
        trading_system = initialize_trading_system(logger)
        if not trading_system:
            raise Exception("Trading system initialization failed")
        
        # Step 6: Run trading process
        if not run_trading_process(logger, trading_system):
            raise Exception("Trading process execution failed")
        
        # Success
        job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
        logger.info("=" * 80)
        logger.info(f"✅ RAILWAY {job_type} JOB COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
        logger.error("=" * 80)
        logger.error(f"❌ RAILWAY {job_type} JOB FAILED")
        logger.error(f"🚨 Error: {str(e)}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        logger.error("🔍 Full Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        # Re-raise the exception so Railway knows the job failed
        raise

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Improved Railway Daily Trading System Cron Job')
    parser.add_argument('--backup', action='store_true', help='Run as backup cron job')
    args = parser.parse_args()
    
    try:
        run_daily_trading_system_improved(is_backup=args.backup)
        sys.exit(0)
    except Exception as e:
        sys.exit(1) 