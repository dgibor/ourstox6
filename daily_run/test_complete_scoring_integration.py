#!/usr/bin/env python3
"""
Comprehensive test script for the complete scoring system integration
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_function():
    """Test that the database function is properly installed"""
    try:
        from daily_run.database import DatabaseManager
        
        db = DatabaseManager()
        print("✅ Database connection successful")
        
        # Test if function exists
        function_exists = db.fetch_one("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_name = 'upsert_company_scores'
        """)
        
        if function_exists:
            print("✅ upsert_company_scores function is installed")
            return True
        else:
            print("❌ upsert_company_scores function is NOT installed")
            return False
            
    except Exception as e:
        print(f"❌ Database function test failed: {e}")
        return False

def test_scoring_calculators():
    """Test that scoring calculators can be imported and initialized"""
    try:
        from calc_fundamental_scores import FundamentalScoreCalculator
        from calc_technical_scores import TechnicalScoreCalculator
        
        fundamental_calc = FundamentalScoreCalculator()
        technical_calc = TechnicalScoreCalculator()
        
        print("✅ Scoring calculators imported and initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Scoring calculators test failed: {e}")
        return False

def test_daily_trading_system_integration():
    """Test the daily trading system scoring integration"""
    try:
        from daily_run.daily_trading_system import DailyTradingSystem
        
        # Initialize the system
        system = DailyTradingSystem()
        print("✅ DailyTradingSystem initialized successfully")
        
        # Test the scoring method directly
        test_tickers = ['AAPL', 'MSFT']  # Use well-known tickers with data
        
        print(f"Testing scoring calculation for {test_tickers}...")
        
        # Get tickers with complete data
        tickers_with_data = system._get_tickers_with_complete_data()
        print(f"Found {len(tickers_with_data)} tickers with complete data")
        
        if len(tickers_with_data) > 0:
            # Test with first available ticker
            test_ticker = tickers_with_data[0]
            print(f"Testing with ticker: {test_ticker}")
            
            # Test scoring calculation
            start_time = time.time()
            
            # Import scoring modules
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            from calc_fundamental_scores import FundamentalScoreCalculator
            from calc_technical_scores import TechnicalScoreCalculator
            
            fundamental_calc = FundamentalScoreCalculator()
            technical_calc = TechnicalScoreCalculator()
            
            # Calculate scores
            fundamental_scores = fundamental_calc.calculate_fundamental_scores(test_ticker)
            technical_scores = technical_calc.calculate_technical_scores(test_ticker)
            
            if fundamental_scores and technical_scores:
                print(f"✅ Score calculation successful for {test_ticker}")
                print(f"   Fundamental Health: {fundamental_scores.get('fundamental_health_score', 'N/A')}")
                print(f"   Technical Health: {technical_scores.get('technical_health_score', 'N/A')}")
                
                # Test storage
                storage_success = system._store_combined_scores(test_ticker, fundamental_scores, technical_scores)
                
                if storage_success:
                    print(f"✅ Score storage successful for {test_ticker}")
                    
                    # Verify data was stored
                    from daily_run.database import DatabaseManager
                    db = DatabaseManager()
                    
                    stored_data = db.fetch_one("""
                        SELECT fundamental_health_score, technical_health_score, overall_score
                        FROM company_scores_current
                        WHERE ticker = %s
                    """, (test_ticker,))
                    
                    if stored_data:
                        print(f"✅ Data verification successful - Scores stored in database")
                        print(f"   Stored Fundamental: {stored_data[0]}")
                        print(f"   Stored Technical: {stored_data[1]}")
                        print(f"   Stored Overall: {stored_data[2]}")
                        return True
                    else:
                        print(f"❌ Data verification failed - No data found in database")
                        return False
                else:
                    print(f"❌ Score storage failed for {test_ticker}")
                    return False
            else:
                print(f"❌ Score calculation failed for {test_ticker}")
                return False
        else:
            print("❌ No tickers with complete data found for testing")
            return False
            
    except Exception as e:
        print(f"❌ Daily trading system integration test failed: {e}")
        return False

def test_complete_workflow():
    """Test the complete scoring workflow"""
    try:
        from daily_run.daily_trading_system import DailyTradingSystem
        
        print("Testing complete scoring workflow...")
        
        # Initialize system
        system = DailyTradingSystem()
        
        # Test the scoring method
        result = system._calculate_daily_scores()
        
        print(f"Workflow result: {result}")
        
        if 'error' not in result:
            print(f"✅ Complete workflow successful")
            print(f"   Tickers processed: {result.get('tickers_processed', 0)}")
            print(f"   Successful calculations: {result.get('successful_calculations', 0)}")
            print(f"   Failed calculations: {result.get('failed_calculations', 0)}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f} seconds")
            return True
        else:
            print(f"❌ Complete workflow failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE SCORING SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Database Function Installation", test_database_function),
        ("Scoring Calculators", test_scoring_calculators),
        ("Daily Trading System Integration", test_daily_trading_system_integration),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Scoring system integration is working!")
    else:
        print("⚠️  Some tests failed - Review the issues above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

