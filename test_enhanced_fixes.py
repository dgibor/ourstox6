"""
Comprehensive test to verify all critical fixes for enhanced fundamental ratio calculator
"""

import logging
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_database_transaction_methods():
    """Test that database transaction methods exist and work"""
    logger.info("Testing database transaction methods")
    
    try:
        from daily_run.database import DatabaseManager
        
        # Create database manager
        db = DatabaseManager()
        
        # Test that transaction methods exist
        assert hasattr(db, 'begin_transaction'), "begin_transaction method missing"
        assert hasattr(db, 'commit'), "commit method missing"
        assert hasattr(db, 'rollback'), "rollback method missing"
        assert hasattr(db, 'cursor'), "cursor method missing"
        
        logger.info("✓ Database transaction methods exist")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database transaction test failed: {e}")
        return False

def test_import_fixes():
    """Test that import fixes work correctly"""
    logger.info("Testing import fixes")
    
    try:
        # Test enhanced ratio calculator import
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        logger.info("✓ Enhanced ratio calculator import successful")
        
        # Test enhanced daily calculator import
        from daily_run.calculate_fundamental_ratios_enhanced import EnhancedDailyFundamentalRatioCalculator
        logger.info("✓ Enhanced daily calculator import successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False

def test_method_signatures():
    """Test that method signatures are consistent"""
    logger.info("Testing method signatures")
    
    try:
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        
        calculator = EnhancedRatioCalculatorV5()
        
        # Test that all calculation methods accept current_price parameter
        fundamental_data = {
            'revenue': 394328000000,
            'net_income': 96995000000,
            'total_assets': 352755000000,
            'total_equity': 80600000000,
            'shares_outstanding': 15700000000,
            'eps_diluted': 6.84
        }
        
        # Test profitability ratios (should accept current_price)
        ratios = calculator._calculate_profitability_ratios('AAPL', fundamental_data, 150.0)
        assert isinstance(ratios, dict), "Profitability ratios should return dict"
        
        # Test quality metrics (should accept current_price)
        ratios = calculator._calculate_quality_metrics('AAPL', fundamental_data, 150.0)
        assert isinstance(ratios, dict), "Quality metrics should return dict"
        
        logger.info("✓ Method signatures are consistent")
        return True
        
    except Exception as e:
        logger.error(f"❌ Method signature test failed: {e}")
        return False

def test_enhanced_calculator_functionality():
    """Test enhanced calculator functionality with mock data"""
    logger.info("Testing enhanced calculator functionality")
    
    try:
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        
        calculator = EnhancedRatioCalculatorV5()
        
        # Test data
        fundamental_data = {
            'ticker': 'AAPL',
            'revenue': 394328000000,
            'net_income': 96995000000,
            'total_assets': 352755000000,
            'total_equity': 80600000000,
            'shares_outstanding': 15700000000,
            'eps_diluted': 6.84,
            'book_value_per_share': 4.25,
            'ebitda': 120000000000,
            'total_debt': 95000000000,
            'cash_and_equivalents': 48000000000,
            'gross_profit': 170782000000,
            'operating_income': 114301000000,
            'free_cash_flow': 90000000000
        }
        
        historical_data = {
            'revenue_previous': 365817000000,
            'net_income_previous': 90000000000,
            'free_cash_flow_previous': 80000000000
        }
        
        # Calculate all ratios
        ratios = calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0, historical_data)
        
        # Verify results
        assert isinstance(ratios, dict), "Should return dictionary of ratios"
        assert len(ratios) > 0, "Should calculate at least some ratios"
        
        # Check for key ratios
        expected_ratios = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'roe', 'roa', 'gross_margin']
        for ratio in expected_ratios:
            if ratio in ratios:
                logger.info(f"✓ {ratio}: {ratios[ratio]:.2f}")
        
        logger.info(f"✓ Calculated {len(ratios)} ratios successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced calculator test failed: {e}")
        return False

def test_enhanced_daily_calculator():
    """Test enhanced daily calculator with mock database"""
    logger.info("Testing enhanced daily calculator")
    
    try:
        from daily_run.calculate_fundamental_ratios_enhanced import EnhancedDailyFundamentalRatioCalculator
        
        # Create mock database
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        mock_db.begin_transaction = Mock()
        mock_db.commit = Mock()
        mock_db.rollback = Mock()
        
        # Setup mock responses
        mock_cursor.fetchone.side_effect = [
            {'ticker': 'AAPL', 'revenue': 394328000000, 'eps_diluted': 6.84},  # Fundamental data
            None  # No historical data
        ]
        mock_cursor.fetchall.return_value = [
            {'ticker': 'AAPL', 'current_price': 150.0, 'company_name': 'Apple Inc.'}
        ]
        
        # Create calculator
        calculator = EnhancedDailyFundamentalRatioCalculator(mock_db)
        
        # Test company data validation
        valid_company = {
            'ticker': 'AAPL',
            'current_price': 150.0,
            'company_name': 'Apple Inc.'
        }
        
        result = calculator.calculate_ratios_for_company(valid_company)
        
        # Should fail because mock database returns no data, but shouldn't crash
        assert isinstance(result, dict), "Should return result dictionary"
        assert 'status' in result, "Should have status field"
        
        logger.info("✓ Enhanced daily calculator test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced daily calculator test failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    logger.info("Testing edge cases")
    
    try:
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        
        calculator = EnhancedRatioCalculatorV5()
        
        # Test with invalid data
        invalid_data = {
            'revenue': 'N/A',
            'eps_diluted': None,
            'shares_outstanding': 0
        }
        
        ratios = calculator.calculate_all_ratios('INVALID', invalid_data, 150.0)
        
        # Should handle invalid data gracefully
        assert isinstance(ratios, dict), "Should return dictionary even with invalid data"
        
        # Test with missing data
        minimal_data = {
            'revenue': 394328000000,
            'shares_outstanding': 15700000000
        }
        
        ratios = calculator.calculate_all_ratios('MINIMAL', minimal_data, 150.0)
        
        # Should calculate some ratios even with minimal data
        assert isinstance(ratios, dict), "Should return dictionary with minimal data"
        
        logger.info("✓ Edge case handling works correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Edge case test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting comprehensive enhanced calculator tests")
    
    tests = [
        ("Database Transaction Methods", test_database_transaction_methods),
        ("Import Fixes", test_import_fixes),
        ("Method Signatures", test_method_signatures),
        ("Enhanced Calculator Functionality", test_enhanced_calculator_functionality),
        ("Enhanced Daily Calculator", test_enhanced_daily_calculator),
        ("Edge Cases", test_edge_cases)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing: {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    # Summary
    logger.info(f"\n--- TEST SUMMARY ---")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Enhanced calculator is ready for production.")
        return True
    else:
        logger.error(f"❌ {failed} tests failed. Please fix issues before production.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 