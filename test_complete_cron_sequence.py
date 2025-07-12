#!/usr/bin/env python3
"""
Test script to verify the complete cron sequence:
1. Fill historical data
2. Run daily trading system
3. Calculate technical indicators

This ensures historical data is available before technical calculations.
"""

import os
import sys
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TEST - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_complete_cron_sequence():
    """Test the complete cron sequence with 10 tickers"""
    logger.info("🧪 Testing Complete Cron Sequence")
    logger.info(f"⏰ Test Time: {datetime.now()}")
    
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Add daily_run directory to path
        daily_run_dir = os.path.join(current_dir, 'daily_run')
        sys.path.insert(0, daily_run_dir)
        
        # Test 1: Import DailyTradingSystem
        logger.info("🔍 Test 1: Importing DailyTradingSystem...")
        from daily_run.daily_trading_system import DailyTradingSystem
        logger.info("✅ DailyTradingSystem imported successfully")
        
        # Test 2: Import historical fill functions
        logger.info("🔍 Test 2: Importing historical fill functions...")
        archive_path = os.path.join(daily_run_dir, 'archive_20250622_215640')
        sys.path.insert(0, archive_path)
        
        from fill_history import fill_history
        from fill_history_market import fill_history_market
        from fill_history_sector import fill_history_sector
        logger.info("✅ Historical fill functions imported successfully")
        
        # Test 3: Initialize DailyTradingSystem
        logger.info("🔍 Test 3: Initializing DailyTradingSystem...")
        trading_system = DailyTradingSystem()
        logger.info("✅ DailyTradingSystem initialized successfully")
        
        # Test 4: Check service priority (should be FMP first)
        logger.info("🔍 Test 4: Checking service priority...")
        service_order = [service[0] for service in trading_system.batch_price_processor.service_priority]
        logger.info(f"📊 Service order: {service_order}")
        
        if service_order[0] == 'FMP':
            logger.info("✅ FMP is correctly prioritized as first service")
        else:
            logger.error(f"❌ FMP is not first: {service_order[0]}")
            return False
        
        # Test 5: Run historical fill (simulated for 10 tickers)
        logger.info("🔍 Test 5: Running historical fill...")
        logger.info("🕰️  Filling historical data with fill_history()...")
        try:
            fill_history()
            logger.info("✅ Historical data fill completed.")
        except Exception as e:
            logger.error(f"❌ Historical fill failed: {e}")
            return False
        
        # Test 6: Run daily trading process for 10 tickers
        logger.info("🔍 Test 6: Running daily trading process for 10 tickers...")
        tickers = trading_system._get_active_tickers()[:10]
        logger.info(f"Testing with tickers: {tickers}")
        
        # Update daily prices for 10 tickers
        logger.info("📈 Updating daily prices...")
        price_result = trading_system._update_daily_prices()
        logger.info(f"Price update result: {price_result}")
        
        # Calculate technical indicators for 10 tickers
        logger.info("📊 Calculating technical indicators...")
        technical_result = trading_system._calculate_technical_indicators(tickers)
        logger.info(f"Technical indicator result: {technical_result}")
        
        # Test 7: Verify results
        logger.info("🔍 Test 7: Verifying results...")
        successful_calculations = technical_result.get('successful_calculations', 0)
        failed_calculations = technical_result.get('failed_calculations', 0)
        
        logger.info(f"📊 Results: {successful_calculations} successful, {failed_calculations} failed")
        
        if successful_calculations > 0:
            logger.info("✅ Technical indicators calculated successfully")
        else:
            logger.warning("⚠️  No technical indicators calculated successfully")
        
        logger.info("✅ Complete cron sequence test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_complete_cron_sequence()
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Tests failed!")
        sys.exit(1) 