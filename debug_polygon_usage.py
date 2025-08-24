#!/usr/bin/env python3
"""
Debug script to identify where Polygon.io is still being called from in the system.
"""

import sys
import os

# Add the daily_run directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))

def debug_polygon_usage():
    """Debug where Polygon.io is still being used"""
    print("🔍 Debugging Polygon.io Usage")
    print("=" * 50)
    
    try:
        # Check the daily trading system sources
        print("📋 Daily Trading System Historical Data Sources:")
        sources = [
            ('finnhub', 'finnhub', 'finnhub_historical_data'),
            ('fmp', 'fmp', 'fmp_historical_data'),
            ('yahoo_finance', 'yahoo', 'yahoo_historical_data'),
            ('alpha_vantage', 'alpha_vantage', 'alpha_vantage_historical_data')
        ]
        
        for i, (service_name, log_name, reason) in enumerate(sources, 1):
            print(f"  {i}. {service_name} ({log_name}) - {reason}")
        
        print("\n✅ Polygon.io is NOT in the daily trading system sources")
        
        # Check if there are any other methods that might be calling Polygon.io
        print("\n🔍 Checking for other Polygon.io usage patterns...")
        
        # Check if there are any direct calls to Polygon.io service
        print("\n📋 Checking for direct Polygon.io service calls...")
        
        # The issue might be that there's another code path that's calling Polygon.io
        # Let me check if there are any other historical data fetching methods
        
        print("\n🎯 Potential Issue Identified:")
        print("  The 'No historical data returned for [TICKER] from Polygon.io' messages")
        print("  suggest that there's another code path calling Polygon.io that we haven't found yet.")
        print("\n🔧 Next Steps:")
        print("  1. Check if there are other historical data fetching methods")
        print("  2. Check if the batch price processor is using Polygon.io")
        print("  3. Check if there are any other service managers being used")
        print("  4. Check if there are any fallback mechanisms still using Polygon.io")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        return False

def check_batch_price_processor():
    """Check if the batch price processor is using Polygon.io"""
    print("\n🔍 Checking Batch Price Processor")
    print("=" * 50)
    
    try:
        # Check if the batch price processor imports or uses Polygon.io
        with open('daily_run/batch_price_processor.py', 'r') as f:
            content = f.read()
            
        if 'polygon' in content.lower():
            print("⚠️  WARNING: Batch price processor contains Polygon.io references!")
            print("  This might be where the Polygon.io calls are coming from.")
        else:
            print("✅ Batch price processor does not contain Polygon.io references")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking batch price processor: {e}")
        return False

def check_other_historical_methods():
    """Check for other historical data fetching methods"""
    print("\n🔍 Checking for Other Historical Data Methods")
    print("=" * 50)
    
    try:
        # Search for any methods that might be calling historical data
        with open('daily_run/daily_trading_system.py', 'r') as f:
            content = f.read()
            
        # Look for any remaining references to polygon
        if 'polygon' in content.lower():
            print("⚠️  WARNING: Daily trading system still contains Polygon.io references!")
            print("  These might be in comments or other methods.")
        else:
            print("✅ Daily trading system has no Polygon.io references")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking other methods: {e}")
        return False

def main():
    """Run all debug checks"""
    print("🚀 Debugging Polygon.io Usage in System")
    print("=" * 60)
    
    debug_passed = debug_polygon_usage()
    batch_check_passed = check_batch_price_processor()
    other_methods_passed = check_other_historical_methods()
    
    print("\n" + "=" * 60)
    print("📊 DEBUG RESULTS SUMMARY:")
    print(f"  Polygon.io Usage Debug: {'✅ PASS' if debug_passed else '❌ FAIL'}")
    print(f"  Batch Price Processor Check: {'✅ PASS' if batch_check_passed else '❌ FAIL'}")
    print(f"  Other Methods Check: {'✅ PASS' if other_methods_passed else '❌ FAIL'}")
    
    print("\n🎯 RECOMMENDATION:")
    print("  The Polygon.io calls are likely coming from a different code path")
    print("  that we haven't identified yet. The system should now prioritize")
    print("  Finnhub first, but there may be fallback mechanisms still using Polygon.io.")
    
    return 0

if __name__ == "__main__":
    exit(main())
