#!/usr/bin/env python3
"""
Test single ticker fundamental data collection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daily_run.enhanced_multi_service_fundamental_manager import EnhancedMultiServiceFundamentalManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_ticker():
    """Test fundamental data collection for a single ticker"""
    
    ticker = 'IBM'
    
    print(f"🧪 TESTING SINGLE TICKER: {ticker}")
    print("=" * 50)
    
    manager = EnhancedMultiServiceFundamentalManager()
    
    try:
        # Get fundamental data
        result = manager.get_fundamental_data_with_fallback(ticker)
        
        print(f"\n📊 RESULTS FOR {ticker}:")
        print(f"Primary source: {result.primary_source}")
        print(f"Fallback sources: {result.fallback_sources_used}")
        print(f"Success rate: {result.success_rate:.1%}")
        print(f"Fields collected: {len(result.data)}")
        print(f"Missing fields: {result.missing_fields}")
        
        # Store the data
        if result.data:
            print(f"\n💾 Storing data...")
            storage_success = manager.store_fundamental_data(result)
            print(f"Storage result: {'✅ Success' if storage_success else '❌ Failed'}")
        else:
            print(f"\n❌ No data to store")
    
    finally:
        manager.close()

if __name__ == "__main__":
    test_single_ticker() 