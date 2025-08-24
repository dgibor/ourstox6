#!/usr/bin/env python3
"""
Test script to verify the enhanced analyst fallback system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))

def test_enhanced_analyst_fallback():
    """Test the enhanced analyst fallback system"""
    print("🧪 Testing Enhanced Analyst Fallback System")
    print("=" * 60)
    
    try:
        from analyst_scorer import AnalystScorer
        
        # Initialize the analyst scorer
        print("🔧 Initializing AnalystScorer...")
        scorer = AnalystScorer()
        print("✅ AnalystScorer initialized successfully")
        
        # Test the enhanced fallback system
        print("\n🔍 Testing Enhanced Fallback System...")
        
        # Test with a well-known ticker
        test_ticker = "AAPL"
        print(f"\n📊 Testing analyst recommendations for {test_ticker}...")
        
        recommendations = scorer.get_analyst_recommendations(test_ticker)
        
        if recommendations:
            print(f"✅ Successfully retrieved analyst data for {test_ticker}")
            print(f"  Data source: {recommendations.get('data_source', 'unknown')}")
            print(f"  Buy count: {recommendations.get('buy_count', 0)}")
            print(f"  Hold count: {recommendations.get('hold_count', 0)}")
            print(f"  Sell count: {recommendations.get('sell_count', 0)}")
            print(f"  Strong buy: {recommendations.get('strong_buy_count', 0)}")
            print(f"  Strong sell: {recommendations.get('strong_sell_count', 0)}")
            print(f"  Price target: {recommendations.get('price_target', 'N/A')}")
            print(f"  Revision count: {recommendations.get('revision_count', 0)}")
        else:
            print(f"⚠️  No analyst data returned for {test_ticker}")
        
        # Test with another ticker
        test_ticker2 = "MSFT"
        print(f"\n📊 Testing analyst recommendations for {test_ticker2}...")
        
        recommendations2 = scorer.get_analyst_recommendations(test_ticker2)
        
        if recommendations2:
            print(f"✅ Successfully retrieved analyst data for {test_ticker2}")
            print(f"  Data source: {recommendations2.get('data_source', 'unknown')}")
            print(f"  Buy count: {recommendations2.get('buy_count', 0)}")
            print(f"  Hold count: {recommendations2.get('hold_count', 0)}")
            print(f"  Sell count: {recommendations2.get('sell_count', 0)}")
        else:
            print(f"⚠️  No analyst data returned for {test_ticker2}")
        
        # Test the individual methods
        print("\n🔍 Testing Individual Fallback Methods...")
        
        # Test multi-account method
        print("  Testing _try_finnhub_multi_account...")
        try:
            result = scorer._try_finnhub_multi_account("AAPL")
            if result:
                print(f"    ✅ Multi-account method returned data: {result.get('data_source', 'unknown')}")
            else:
                print(f"    ⚠️  Multi-account method returned no data")
        except Exception as e:
            print(f"    ❌ Multi-account method failed: {e}")
        
        # Test single account method
        print("  Testing _try_finnhub_single_account...")
        try:
            result = scorer._try_finnhub_single_account("AAPL")
            if result:
                print(f"    ✅ Single account method returned data: {result.get('data_source', 'unknown')}")
            else:
                print(f"    ⚠️  Single account method returned no data")
        except Exception as e:
            print(f"    ❌ Single account method failed: {e}")
        
        # Test database fallback
        print("  Testing _get_analyst_recommendations_from_db...")
        try:
            result = scorer._get_analyst_recommendations_from_db("AAPL")
            if result:
                print(f"    ✅ Database fallback returned data: {result.get('data_source', 'unknown')}")
            else:
                print(f"    ⚠️  Database fallback returned no data")
        except Exception as e:
            print(f"    ❌ Database fallback failed: {e}")
        
        # Test default recommendations
        print("  Testing _get_default_recommendations...")
        try:
            result = scorer._get_default_recommendations()
            if result:
                print(f"    ✅ Default recommendations returned: {result.get('data_source', 'unknown')}")
            else:
                print(f"    ❌ Default recommendations failed")
        except Exception as e:
            print(f"    ❌ Default recommendations failed: {e}")
        
        print("\n✅ Enhanced Analyst Fallback System Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_analyst_fallback()
    exit(0 if success else 1)
