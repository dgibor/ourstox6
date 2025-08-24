#!/usr/bin/env python3
"""
Test script to verify the enhanced Finnhub fallback system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))

def test_finnhub_fallback():
    """Test the enhanced Finnhub fallback system"""
    print("🧪 Testing Enhanced Finnhub Fallback System")
    print("=" * 50)
    
    try:
        from finnhub_multi_account_manager import FinnhubMultiAccountManager
        
        # Initialize the manager
        print("🔧 Initializing FinnhubMultiAccountManager...")
        manager = FinnhubMultiAccountManager()
        
        # Test account status
        print("\n📊 Account Status:")
        status = manager.get_account_status()
        for account_id, account_status in status.items():
            print(f"  Account {account_id + 1}: {account_status['status']} "
                  f"(Minute: {account_status['remaining_minute']}, Daily: {account_status['remaining_daily']})")
        
        # Test fallback summary
        print("\n🏥 Account Health Summary:")
        health = manager.get_fallback_summary()
        for account_id, health_info in health['account_health'].items():
            print(f"  Account {account_id + 1}: {health_info['status']} "
                  f"(Score: {health_info['health_score']})")
        
        # Test a simple API call to see fallback in action
        print("\n🔍 Testing API call with fallback...")
        test_ticker = "AAPL"
        
        # Test analyst recommendations
        print(f"  Testing analyst recommendations for {test_ticker}...")
        result = manager.get_analyst_recommendations(test_ticker)
        if result:
            print(f"  ✅ Success! Got data from API")
        else:
            print(f"  ⚠️  No data returned (this might be normal for some tickers)")
        
        # Test quote data
        print(f"  Testing quote data for {test_ticker}...")
        result = manager.get_quote(test_ticker)
        if result:
            print(f"  ✅ Success! Got quote data")
        else:
            print(f"  ⚠️  No quote data returned")
        
        # Show final usage
        print("\n📈 Final Usage Summary:")
        final_health = manager.get_fallback_summary()
        print(f"  Total calls: {final_health['total_calls']}")
        for account_id, calls in final_health['calls_per_account'].items():
            print(f"  Account {account_id + 1}: {calls} calls")
        
        # Clean up
        manager.close()
        print("\n✅ Test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_finnhub_fallback()
    exit(0 if success else 1)
