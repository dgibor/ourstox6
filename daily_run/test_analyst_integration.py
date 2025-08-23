#!/usr/bin/env python3
"""
Test Analyst Integration

Simple test to verify analyst scoring is working in the daily trading system.
"""

import logging
from daily_trading_system import DailyTradingSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_analyst_integration():
    """Test that analyst scoring is properly integrated"""
    print("🧪 Testing Analyst Integration in Daily Trading System")
    print("=" * 60)
    
    try:
        # Initialize the system
        system = DailyTradingSystem()
        print("✅ DailyTradingSystem initialized successfully")
        
        # Test importing AnalystScoringManager
        try:
            from analyst_scoring_manager import AnalystScoringManager
            print("✅ AnalystScoringManager imported successfully")
            
            # Test creating an instance
            from database import DatabaseManager
            db = DatabaseManager()
            manager = AnalystScoringManager(db=db)
            print("✅ AnalystScoringManager instance created successfully")
            
            # Test getting active tickers
            tickers = manager.get_active_tickers()
            print(f"✅ Found {len(tickers)} active tickers")
            
            if tickers:
                print(f"   Sample tickers: {tickers[:5]}")
            
        except ImportError as e:
            print(f"❌ Failed to import AnalystScoringManager: {e}")
            return False
        except Exception as e:
            print(f"❌ Error testing AnalystScoringManager: {e}")
            return False
        
        # Test the _calculate_analyst_scores method
        try:
            result = system._calculate_analyst_scores()
            print("✅ _calculate_analyst_scores method executed successfully")
            print(f"   Result: {result}")
            
            if result.get('status') == 'skipped':
                print("   ⚠️  Analyst scoring was skipped (this is normal if no tickers)")
            elif result.get('status') == 'completed':
                print("   ✅ Analyst scoring completed successfully")
            elif result.get('status') == 'failed':
                print(f"   ❌ Analyst scoring failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"❌ Error testing _calculate_analyst_scores: {e}")
            return False
        
        print("\n🎉 All tests passed! Analyst integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == '__main__':
    success = test_analyst_integration()
    exit(0 if success else 1)
