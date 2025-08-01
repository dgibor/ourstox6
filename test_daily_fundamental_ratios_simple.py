"""
Simplified test for daily fundamental ratio calculation
"""

import logging
import sys
import os
from datetime import datetime, date, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_improved_ratio_calculator():
    """Test the improved ratio calculator directly"""
    
    logger.info("Testing Improved Ratio Calculator")
    
    try:
        # Import the calculator
        from daily_run.improved_ratio_calculator_v5 import ImprovedRatioCalculatorV5
        
        # Create calculator
        calculator = ImprovedRatioCalculatorV5()
        
        # Test data for AAPL
        fundamental_data = {
            'ticker': 'AAPL',
            'report_date': date.today(),
            'period_type': 'annual',
            'revenue': 394328000000,
            'gross_profit': 170782000000,
            'operating_income': 114301000000,
            'net_income': 96995000000,
            'ebitda': 120000000000,
            'eps_diluted': 6.84,
            'book_value_per_share': 4.25,
            'total_assets': 352755000000,
            'total_debt': 95000000000,
            'total_equity': 80600000000,
            'cash_and_equivalents': 48000000000,
            'operating_cash_flow': 110000000000,
            'free_cash_flow': 90000000000,
            'shares_outstanding': 15700000000,
            'current_price': 150.0
        }
        
        historical_data = {
            'revenue_previous': 365817000000,
            'total_assets_previous': 346747000000,
            'inventory_previous': 4946000000,
            'accounts_receivable_previous': 29508000000,
            'retained_earnings_previous': 50000000000
        }
        
        # Calculate ratios
        ratios = calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0, historical_data)
        
        # Verify ratios were calculated
        assert ratios is not None, "Expected ratios to be calculated"
        assert len(ratios) > 0, "Expected at least one ratio"
        
        # Check key ratios
        assert 'pe_ratio' in ratios, "Expected P/E ratio"
        assert 'pb_ratio' in ratios, "Expected P/B ratio"
        assert 'roe' in ratios, "Expected ROE"
        assert 'roa' in ratios, "Expected ROA"
        
        logger.info(f"✓ Calculated {len(ratios)} ratios successfully")
        logger.info(f"Sample ratios: P/E={ratios.get('pe_ratio'):.2f}, P/B={ratios.get('pb_ratio'):.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_daily_calculator_structure():
    """Test the daily calculator structure without database"""
    
    logger.info("Testing Daily Calculator Structure")
    
    try:
        # Import the daily calculator
        from daily_run.calculate_fundamental_ratios import DailyFundamentalRatioCalculator
        
        # Create a mock database
        class MockDB:
            def cursor(self, cursor_factory=None):
                return MockCursor()
            def commit(self):
                pass
            def rollback(self):
                pass
        
        class MockCursor:
            def execute(self, query, params=None):
                pass
            def fetchall(self):
                return []
            def fetchone(self):
                return None
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Create calculator
        calculator = DailyFundamentalRatioCalculator(MockDB())
        
        # Test that methods exist
        assert hasattr(calculator, 'get_companies_needing_ratio_updates'), "Missing method"
        assert hasattr(calculator, 'get_latest_fundamental_data'), "Missing method"
        assert hasattr(calculator, 'calculate_ratios_for_company'), "Missing method"
        assert hasattr(calculator, 'process_all_companies'), "Missing method"
        
        logger.info("✓ Daily calculator structure test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting simplified tests")
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Improved ratio calculator
    if test_improved_ratio_calculator():
        tests_passed += 1
    
    # Test 2: Daily calculator structure
    if test_daily_calculator_structure():
        tests_passed += 1
    
    logger.info(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.error("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 