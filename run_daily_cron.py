#!/usr/bin/env python3
"""
Railway Daily Trading System Cron Job
Enhanced with detailed step-by-step logging
"""

import os
import sys
import logging
import argparse
from datetime import datetime

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

def run_daily_trading_system(is_backup=False):
    """Run the daily trading system with enhanced logging"""
    try:
        # Setup logging
        setup_railway_logging(is_backup)
        
        job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 80)
        logger.info(f"🚀 RAILWAY {job_type} JOB STARTED")
        logger.info(f"⏰ Execution Time: {datetime.now()}")
        logger.info(f"📁 Working Directory: {os.getcwd()}")
        logger.info(f"🐍 Python Path: {sys.path[:3]}")  # Show first 3 paths
        logger.info("🌍 Environment Variables:")
        logger.info(f"  PYTHONPATH: {os.getenv('PYTHONPATH', 'NOT SET')}")
        logger.info(f"  TZ: {os.getenv('TZ', 'NOT SET')}")
        logger.info(f"  DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
        logger.info(f"  DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
        logger.info(f"  FMP_API_KEY: {'SET' if os.getenv('FMP_API_KEY') else 'NOT SET'}")
        logger.info("=" * 80)
        
        # Step 1: Import and setup
        logger.info("📦 STEP 1: Importing modules and setting up system...")
        daily_run_dir = os.path.join(os.getcwd(), 'daily_run')
        
        if not os.path.exists(daily_run_dir):
            logger.error(f"❌ daily_run directory not found at {daily_run_dir}")
            return False
        
        # Add daily_run to Python path
        sys.path.insert(0, daily_run_dir)
        
        # Import the daily trading system
        try:
            from daily_trading_system import DailyTradingSystem
            logger.info("✅ DailyTradingSystem imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import DailyTradingSystem: {e}")
            # Try alternative import path
            module_path = os.path.join(daily_run_dir, 'daily_trading_system.py')
            if os.path.exists(module_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("daily_trading_system", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                DailyTradingSystem = module.DailyTradingSystem
                logger.info("✅ DailyTradingSystem imported via alternative method")
            else:
                raise ImportError(f"Cannot find daily_trading_system.py at {module_path}")
        
        # Step 2: Fill historical data
        logger.info("🕰️ STEP 2: Filling historical data BEFORE daily trading process...")
        try:
            # Add archive path to sys.path for imports
            archive_path = os.path.join(daily_run_dir, 'archive_20250622_215640')
            sys.path.insert(0, archive_path)
            
            from fill_history import fill_history
            from fill_history_market import fill_history_market
            from fill_history_sector import fill_history_sector
            
            logger.info("🕰️  Filling historical data with fill_history()...")
            fill_history()
            logger.info("✅ Historical data fill completed.")
            
            logger.info("🕰️  Filling market historical data with fill_history_market()...")
            fill_history_market()
            logger.info("✅ Market historical data fill completed.")
            
            logger.info("🕰️  Filling sector historical data with fill_history_sector()...")
            fill_history_sector()
            logger.info("✅ Sector historical data fill completed.")
            
            # Remove archive path from sys.path
            sys.path.remove(archive_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to fill historical data: {e}")
            import traceback
            logger.error(f"🔍 Historical fill error traceback: {traceback.format_exc()}")
        
        # Step 3: Initialize trading system
        logger.info("🏗️ STEP 3: Initializing Daily Trading System...")
        trading_system = DailyTradingSystem()
        logger.info("✅ Daily Trading System initialized successfully")
        
        # Step 4: Run the main process
        logger.info("🚀 STEP 4: Starting daily trading process...")
        result = trading_system.run_daily_trading_process()
        logger.info("✅ Daily trading process completed")
        
        # Step 5: Log detailed results
        logger.info("📊 STEP 5: Logging detailed results...")
        if result:
            logger.info("📈 DAILY TRADING PROCESS COMPLETED SUCCESSFULLY")
            logger.info("📊 DETAILED RESULTS SUMMARY:")
            
            # Enhanced logging for each phase
            for phase_name, phase_result in result.get('phase_results', {}).items():
                if isinstance(phase_result, dict):
                    logger.info(f"🔍 {phase_name.upper()}:")
                    
                    # Log specific metrics for each phase
                    if 'total_tickers' in phase_result:
                        logger.info(f"   • Total Tickers: {phase_result['total_tickers']}")
                    if 'successful_updates' in phase_result:
                        logger.info(f"   • Successful Updates: {phase_result['successful_updates']}")
                    if 'failed_updates' in phase_result:
                        logger.info(f"   • Failed Updates: {phase_result['failed_updates']}")
                    if 'successful_calculations' in phase_result:
                        logger.info(f"   • Successful Calculations: {phase_result['successful_calculations']}")
                    if 'failed_calculations' in phase_result:
                        logger.info(f"   • Failed Calculations: {phase_result['failed_calculations']}")
                    if 'processing_time' in phase_result:
                        logger.info(f"   • Processing Time: {phase_result['processing_time']:.2f}s")
                    if 'api_calls_used' in phase_result:
                        logger.info(f"   • API Calls Used: {phase_result['api_calls_used']}")
                    
                    # Log specific details for fundamental ratios
                    if phase_name == 'priority_4_missing_fundamentals' and 'fundamentals' in phase_result:
                        fundamentals = phase_result['fundamentals']
                        logger.info(f"   📊 Fundamental Details:")
                        logger.info(f"     - Candidates Found: {fundamentals.get('candidates', 0)}")
                        logger.info(f"     - Successful Updates: {fundamentals.get('successful', 0)}")
                        logger.info(f"     - Failed Updates: {fundamentals.get('failed', 0)}")
                    
                    # Log specific details for technical indicators
                    if phase_name == 'priority_1_trading_day' and 'technical_indicators' in phase_result:
                        technicals = phase_result['technical_indicators']
                        logger.info(f"   📈 Technical Indicator Details:")
                        logger.info(f"     - Successful Calculations: {technicals.get('successful_calculations', 0)}")
                        logger.info(f"     - Failed Calculations: {technicals.get('failed_calculations', 0)}")
                        logger.info(f"     - Historical Fetches: {technicals.get('historical_fetches', 0)}")
                    
                    # Log specific details for price updates
                    if phase_name == 'priority_1_trading_day' and 'daily_prices' in phase_result:
                        prices = phase_result['daily_prices']
                        logger.info(f"   💰 Price Update Details:")
                        logger.info(f"     - Total Tickers: {prices.get('total_tickers', 0)}")
                        logger.info(f"     - Successful Updates: {prices.get('successful_updates', 0)}")
                        logger.info(f"     - Failed Updates: {prices.get('failed_updates', 0)}")
                        logger.info(f"     - Success Rate: {prices.get('success_rate', 0):.1f}%")
                        logger.info(f"     - API Calls Used: {prices.get('api_calls_used', 0)}")
                else:
                    logger.info(f"   • {phase_name}: {phase_result}")
            
            # Log overall summary
            total_time = result.get('total_processing_time', 0)
            total_api_calls = result.get('total_api_calls_used', 0)
            logger.info(f"🎯 OVERALL SUMMARY:")
            logger.info(f"   • Total Processing Time: {total_time:.2f}s")
            logger.info(f"   • Total API Calls Used: {total_api_calls}")
            logger.info(f"   • Total Phases: {len(result.get('phase_results', {}))}")
        else:
            logger.warning("⚠️  Daily trading process returned no results")
        
        # Step 6: Final completion
        logger.info("✅ STEP 6: Cron job execution completed successfully")
        job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
        logger.info("=" * 80)
        logger.info(f"✅ RAILWAY {job_type} JOB COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        job_type = "BACKUP CRON" if is_backup else "PRIMARY CRON"
        logger = logging.getLogger(__name__)
        logger.error("=" * 80)
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
        
        logger.error("=" * 80)
        
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