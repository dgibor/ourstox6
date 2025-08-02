#!/usr/bin/env python3
"""
Test script to verify the fixed cron system works correctly
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TEST - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_fixed_cron_system():
    """Test the fixed cron system"""
    logger.info("🧪 Testing Fixed Cron System")
    logger.info(f"⏰ Test Time: {datetime.now()}")
    
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Add daily_run directory to path
        daily_run_dir = os.path.join(current_dir, 'daily_run')
        sys.path.insert(0, daily_run_dir)
        
        # Test 1: Import the system
        logger.info("📦 Test 1: Importing DailyTradingSystem...")
        from daily_run.daily_trading_system import DailyTradingSystem
        logger.info("✅ DailyTradingSystem imported successfully")
        
        # Test 2: Initialize the system
        logger.info("🏗️  Test 2: Initializing DailyTradingSystem...")
        trading_system = DailyTradingSystem()
        logger.info("✅ DailyTradingSystem initialized successfully")
        
        # Test 3: Check service priority
        logger.info("🔍 Test 3: Checking service priority...")
        service_order = [service[0] for service in trading_system.batch_price_processor.service_priority]
        logger.info(f"📊 Service order: {service_order}")
        
        # Check that FMP is first (as requested)
        if service_order[0] == 'FMP':
            logger.info("✅ FMP is correctly prioritized as first service")
        else:
            logger.error(f"❌ FMP is not first: {service_order[0]}")
            return False
        
        # Test 4: Run technical indicator calculation on 10 tickers
        logger.info("🔍 Test 4: Running technical indicator calculation on 10 tickers...")
        tickers = trading_system._get_active_tickers()[:10]
        logger.info(f"Testing with tickers: {tickers}")
        result = trading_system._calculate_technical_indicators(tickers)
        logger.info(f"Technical indicator calculation result: {result}")
        
        logger.info("✅ All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(f"🔍 Error Type: {type(e).__name__}")
        
        # Import traceback for better error logging
        import traceback
        logger.error("🔍 Full Traceback:")
        logger.error(traceback.format_exc())
        
        return False

if __name__ == "__main__":
    success = test_fixed_cron_system()
    sys.exit(0 if success else 1) 