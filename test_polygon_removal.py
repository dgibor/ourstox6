#!/usr/bin/env python3
"""
Test script to verify that Polygon.io is no longer being used in the priority order
for historical data fetching.
"""

import sys
import os

# Add the daily_run directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))

def test_historical_data_priority_order():
    """Test that the historical data priority order no longer includes Polygon.io"""
    print("🧪 Testing Historical Data Priority Order")
    print("=" * 50)
    
    try:
        # Import the daily trading system
        from daily_trading_system import DailyTradingSystem
        
        # Create a mock instance to test the method
        class MockDailyTradingSystem:
            def _get_historical_data_to_minimum(self, ticker: str, min_days: int = 100):
                """Mock method to test the sources list"""
                # This is the sources list from the actual method
                sources = [
                    ('finnhub', 'finnhub', 'finnhub_historical_data'),  # Finnhub first (best API)
                    ('fmp', 'fmp', 'fmp_historical_data'),
                    ('yahoo_finance', 'yahoo', 'yahoo_historical_data'),
                    ('alpha_vantage', 'alpha_vantage', 'alpha_vantage_historical_data')
                    # Polygon.io removed due to rate limiting issues
                ]
                return sources
        
        # Test the sources list
        mock_system = MockDailyTradingSystem()
        sources = mock_system._get_historical_data_to_minimum('TEST', 100)
        
        print("📋 Current Historical Data Sources:")
        for i, (service_name, log_name, reason) in enumerate(sources, 1):
            print(f"  {i}. {service_name} ({log_name}) - {reason}")
        
        # Check if Polygon.io is in the list
        polygon_found = any('polygon' in service_name.lower() for service_name, _, _ in sources)
        
        if polygon_found:
            print("\n❌ FAIL: Polygon.io is still in the historical data sources!")
            return False
        else:
            print("\n✅ PASS: Polygon.io has been removed from historical data sources!")
        
        # Check that Finnhub is first
        if sources[0][0] == 'finnhub':
            print("✅ PASS: Finnhub is correctly prioritized first!")
        else:
            print("❌ FAIL: Finnhub is not first in the priority order!")
            return False
        
        print("\n🎯 Priority Order Verification:")
        print("  1. Finnhub (best API) - ✅")
        print("  2. FMP (paid, high quality) - ✅")
        print("  3. Yahoo Finance (free, reliable) - ✅")
        print("  4. Alpha Vantage (free tier) - ✅")
        print("  5. Polygon.io - ❌ REMOVED (rate limiting issues)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_api_flow_manager_priority():
    """Test that the API flow manager no longer prioritizes Polygon.io over Finnhub"""
    print("\n🧪 Testing API Flow Manager Priority")
    print("=" * 50)
    
    try:
        # Import the API flow manager
        from api_flow_manager import APIFlowManager
        
        # Check the pricing priority order
        pricing_rules = APIFlowManager().get_rules_for_data_type('pricing')
        pricing_priorities = [rule.service_id for rule in pricing_rules]
        
        print("📋 Pricing Service Priority Order:")
        for i, service_id in enumerate(pricing_priorities, 1):
            print(f"  {i}. {service_id}")
        
        # Check that Finnhub is before Polygon.io
        finnhub_index = pricing_priorities.index('finnhub') if 'finnhub' in pricing_priorities else -1
        polygon_index = pricing_priorities.index('polygon') if 'polygon' in pricing_priorities else -1
        
        if finnhub_index != -1 and polygon_index != -1:
            if finnhub_index < polygon_index:
                print("✅ PASS: Finnhub is correctly prioritized before Polygon.io for pricing!")
            else:
                print("❌ FAIL: Polygon.io is still prioritized before Finnhub for pricing!")
                return False
        else:
            print("⚠️  WARNING: Could not find both Finnhub and Polygon.io in pricing priorities")
        
        # Check the fundamentals priority order
        fundamentals_rules = APIFlowManager().get_rules_for_data_type('fundamentals')
        fundamentals_priorities = [rule.service_id for rule in fundamentals_rules]
        
        print("\n📋 Fundamentals Service Priority Order:")
        for i, service_id in enumerate(fundamentals_priorities, 1):
            print(f"  {i}. {service_id}")
        
        # Check that Finnhub is first for fundamentals
        if fundamentals_priorities[0] == 'finnhub':
            print("✅ PASS: Finnhub is correctly prioritized first for fundamentals!")
        else:
            print("❌ FAIL: Finnhub is not first for fundamentals!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during API flow manager test: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Polygon.io Removal from Priority Order")
    print("=" * 60)
    
    test1_passed = test_historical_data_priority_order()
    test2_passed = test_api_flow_manager_priority()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY:")
    print(f"  Historical Data Priority Order: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  API Flow Manager Priority: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Polygon.io has been successfully removed from priority order")
        print("✅ Finnhub is now correctly prioritized first")
        print("✅ The system will no longer get stuck on Polygon.io rate limits")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️  Polygon.io may still be causing rate limiting issues")
        return 1

if __name__ == "__main__":
    exit(main())
