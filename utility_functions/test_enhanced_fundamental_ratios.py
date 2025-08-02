"""
Comprehensive test suite for enhanced fundamental ratio calculations
Covers edge cases, error scenarios, and data validation
"""

import logging
import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestDataValidator(unittest.TestCase):
    """Test data validation functionality"""
    
    def setUp(self):
        from daily_run.data_validator import FundamentalDataValidator
        self.validator = FundamentalDataValidator()
    
    def test_validate_numeric_valid_values(self):
        """Test validation of valid numeric values"""
        # Test valid integers
        self.assertEqual(self.validator.validate_numeric(100, 'test'), 100.0)
        self.assertEqual(self.validator.validate_numeric(0, 'test'), 0.0)
        
        # Test valid floats
        self.assertEqual(self.validator.validate_numeric(100.5, 'test'), 100.5)
        self.assertEqual(self.validator.validate_numeric(-50.25, 'test', allow_negative=True), -50.25)
        
        # Test valid strings
        self.assertEqual(self.validator.validate_numeric("100", 'test'), 100.0)
        self.assertEqual(self.validator.validate_numeric("100.5", 'test'), 100.5)
    
    def test_validate_numeric_invalid_values(self):
        """Test validation of invalid numeric values"""
        # Test None values
        self.assertIsNone(self.validator.validate_numeric(None, 'test'))
        
        # Test invalid strings
        self.assertIsNone(self.validator.validate_numeric("N/A", 'test'))
        self.assertIsNone(self.validator.validate_numeric("--", 'test'))
        self.assertIsNone(self.validator.validate_numeric("", 'test'))
        self.assertIsNone(self.validator.validate_numeric("abc", 'test'))
        
        # Test negative values when not allowed
        self.assertIsNone(self.validator.validate_numeric(-100, 'test', allow_negative=False))
        
        # Test invalid types
        self.assertIsNone(self.validator.validate_numeric([], 'test'))
        self.assertIsNone(self.validator.validate_numeric({}, 'test'))
    
    def test_validate_company_data_valid(self):
        """Test validation of valid company data"""
        valid_data = {
            'ticker': 'AAPL',
            'current_price': 150.0,
            'company_name': 'Apple Inc.',
            'fundamentals_last_update': date.today()
        }
        
        result = self.validator.validate_company_data(valid_data)
        self.assertEqual(result['ticker'], 'AAPL')
        self.assertEqual(result['current_price'], 150.0)
        self.assertEqual(result['company_name'], 'Apple Inc.')
    
    def test_validate_company_data_invalid(self):
        """Test validation of invalid company data"""
        # Missing required fields
        invalid_data = {'ticker': 'AAPL'}  # Missing current_price
        result = self.validator.validate_company_data(invalid_data)
        self.assertEqual(result, {})
        
        # Invalid ticker
        invalid_data = {'ticker': '', 'current_price': 150.0}
        result = self.validator.validate_company_data(invalid_data)
        self.assertEqual(result, {})
        
        # Invalid price
        invalid_data = {'ticker': 'AAPL', 'current_price': -100}
        result = self.validator.validate_company_data(invalid_data)
        self.assertEqual(result, {})
    
    def test_validate_fundamental_data(self):
        """Test validation of fundamental data"""
        valid_data = {
            'ticker': 'AAPL',
            'revenue': 394328000000,
            'net_income': 96995000000,
            'total_assets': 352755000000,
            'total_equity': 80600000000,
            'shares_outstanding': 15700000000,
            'eps_diluted': 6.84
        }
        
        result = self.validator.validate_fundamental_data(valid_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['revenue'], 394328000000.0)
        self.assertEqual(result['eps_diluted'], 6.84)

class TestEnhancedRatioCalculator(unittest.TestCase):
    """Test enhanced ratio calculator functionality"""
    
    def setUp(self):
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        self.calculator = EnhancedRatioCalculatorV5()
    
    def test_safe_division_valid(self):
        """Test safe division with valid inputs"""
        result = self.calculator._safe_division(100, 10, 'test')
        self.assertEqual(result, 10.0)
        
        result = self.calculator._safe_division(0, 10, 'test')
        self.assertEqual(result, 0.0)
    
    def test_safe_division_invalid(self):
        """Test safe division with invalid inputs"""
        # Division by zero
        result = self.calculator._safe_division(100, 0, 'test')
        self.assertIsNone(result)
        
        # None values
        result = self.calculator._safe_division(None, 10, 'test')
        self.assertIsNone(result)
        
        result = self.calculator._safe_division(100, None, 'test')
        self.assertIsNone(result)
    
    def test_calculate_valuation_ratios_valid(self):
        """Test valuation ratio calculations with valid data"""
        fundamental_data = {
            'eps_diluted': 6.84,
            'book_value_per_share': 4.25,
            'revenue': 394328000000,
            'shares_outstanding': 15700000000,
            'ebitda': 120000000000,
            'total_debt': 95000000000,
            'cash_and_equivalents': 48000000000
        }
        
        ratios = self.calculator._calculate_valuation_ratios('AAPL', fundamental_data, 150.0)
        
        self.assertIn('pe_ratio', ratios)
        self.assertIn('pb_ratio', ratios)
        self.assertIn('ps_ratio', ratios)
        self.assertIn('ev_ebitda', ratios)
        
        # Verify calculations
        self.assertAlmostEqual(ratios['pe_ratio'], 150.0 / 6.84, places=2)
        self.assertAlmostEqual(ratios['pb_ratio'], 150.0 / 4.25, places=2)
    
    def test_calculate_valuation_ratios_invalid(self):
        """Test valuation ratio calculations with invalid data"""
        # Negative EPS
        fundamental_data = {
            'eps_diluted': -6.84,
            'book_value_per_share': 4.25,
            'revenue': 394328000000,
            'shares_outstanding': 15700000000
        }
        
        ratios = self.calculator._calculate_valuation_ratios('AAPL', fundamental_data, 150.0)
        
        # Should not calculate P/E for negative EPS
        self.assertNotIn('pe_ratio', ratios)
        self.assertIn('pb_ratio', ratios)  # Should still calculate P/B
    
    def test_calculate_profitability_ratios(self):
        """Test profitability ratio calculations"""
        fundamental_data = {
            'net_income': 96995000000,
            'total_equity': 80600000000,
            'total_assets': 352755000000,
            'revenue': 394328000000,
            'gross_profit': 170782000000,
            'operating_income': 114301000000
        }
        
        ratios = self.calculator._calculate_profitability_ratios('AAPL', fundamental_data)
        
        self.assertIn('roe', ratios)
        self.assertIn('roa', ratios)
        self.assertIn('gross_margin', ratios)
        self.assertIn('operating_margin', ratios)
        self.assertIn('net_margin', ratios)
        
        # Verify ROE calculation
        expected_roe = (96995000000 / 80600000000) * 100
        self.assertAlmostEqual(ratios['roe'], expected_roe, places=2)
    
    def test_calculate_ratios_with_missing_data(self):
        """Test ratio calculations with missing data"""
        # Minimal data
        fundamental_data = {
            'revenue': 394328000000,
            'shares_outstanding': 15700000000
        }
        
        ratios = self.calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0)
        
        # Should still calculate some ratios
        self.assertGreater(len(ratios), 0)
        self.assertIn('ps_ratio', ratios)  # Should calculate P/S
    
    def test_calculate_ratios_with_historical_data(self):
        """Test ratio calculations with historical data"""
        fundamental_data = {
            'revenue': 394328000000,
            'net_income': 96995000000,
            'free_cash_flow': 90000000000
        }
        
        historical_data = {
            'revenue_previous': 365817000000,
            'net_income_previous': 90000000000,
            'free_cash_flow_previous': 80000000000
        }
        
        ratios = self.calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0, historical_data)
        
        # Should calculate growth metrics
        self.assertIn('revenue_growth_yoy', ratios)
        self.assertIn('earnings_growth_yoy', ratios)
        self.assertIn('fcf_growth_yoy', ratios)
        
        # Verify growth calculations
        expected_revenue_growth = ((394328000000 - 365817000000) / 365817000000) * 100
        self.assertAlmostEqual(ratios['revenue_growth_yoy'], expected_revenue_growth, places=2)

class TestEnhancedDailyCalculator(unittest.TestCase):
    """Test enhanced daily calculator functionality"""
    
    def setUp(self):
        from daily_run.calculate_fundamental_ratios_enhanced import EnhancedDailyFundamentalRatioCalculator
        
        # Create mock database
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
        self.calculator = EnhancedDailyFundamentalRatioCalculator(self.mock_db)
    
    def test_validate_company_data(self):
        """Test company data validation in daily calculator"""
        valid_company = {
            'ticker': 'AAPL',
            'current_price': 150.0,
            'company_name': 'Apple Inc.'
        }
        
        result = self.calculator.calculate_ratios_for_company(valid_company)
        
        # Should fail because mock database returns no data
        self.assertEqual(result['status'], 'failed')
        self.assertIn('No fundamental data available', result['error'])
    
    def test_invalid_company_data(self):
        """Test handling of invalid company data"""
        invalid_company = {
            'ticker': '',  # Invalid ticker
            'current_price': -100  # Invalid price
        }
        
        result = self.calculator.calculate_ratios_for_company(invalid_company)
        
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Invalid company data', result['error'])
    
    @patch('daily_run.calculate_fundamental_ratios_enhanced.EnhancedRatioCalculatorV5')
    def test_calculation_with_mock_data(self, mock_calculator_class):
        """Test calculation with mock data"""
        # Setup mock calculator
        mock_calculator = Mock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.calculate_all_ratios.return_value = {
            'pe_ratio': 21.93,
            'pb_ratio': 24.67,
            'roe': 120.34
        }
        
        # Setup mock database responses
        self.mock_cursor.fetchone.side_effect = [
            {'ticker': 'AAPL', 'revenue': 394328000000, 'eps_diluted': 6.84},  # Fundamental data
            None  # No historical data
        ]
        
        valid_company = {
            'ticker': 'AAPL',
            'current_price': 150.0,
            'company_name': 'Apple Inc.'
        }
        
        result = self.calculator.calculate_ratios_for_company(valid_company)
        
        # Should succeed with mock data
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['ratios_calculated'], 3)
        self.assertIn('pe_ratio', result['ratios'])

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios"""
    
    def test_division_by_zero_handling(self):
        """Test handling of division by zero scenarios"""
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        calculator = EnhancedRatioCalculatorV5()
        
        # Test with zero denominator
        fundamental_data = {
            'eps_diluted': 0,  # Zero EPS
            'book_value_per_share': 0,  # Zero book value
            'revenue': 394328000000,
            'shares_outstanding': 15700000000
        }
        
        ratios = calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0)
        
        # Should not include ratios that would cause division by zero
        self.assertNotIn('pe_ratio', ratios)
        self.assertNotIn('pb_ratio', ratios)
        # Should still calculate other ratios
        self.assertIn('ps_ratio', ratios)
    
    def test_negative_values_handling(self):
        """Test handling of negative values"""
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        calculator = EnhancedRatioCalculatorV5()
        
        fundamental_data = {
            'eps_diluted': -6.84,  # Negative EPS
            'book_value_per_share': -4.25,  # Negative book value
            'revenue': 394328000000,
            'shares_outstanding': 15700000000
        }
        
        ratios = calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0)
        
        # Should not calculate ratios with negative denominators
        self.assertNotIn('pe_ratio', ratios)
        self.assertNotIn('pb_ratio', ratios)
    
    def test_extremely_large_values(self):
        """Test handling of extremely large values"""
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        calculator = EnhancedRatioCalculatorV5()
        
        fundamental_data = {
            'eps_diluted': 1e-10,  # Very small EPS
            'book_value_per_share': 1e-10,  # Very small book value
            'revenue': 1e20,  # Very large revenue
            'shares_outstanding': 1e20  # Very large shares
        }
        
        ratios = calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0)
        
        # Should handle extreme values gracefully
        self.assertIsInstance(ratios, dict)
        # Should not crash or produce infinite values
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        from daily_run.improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
        calculator = EnhancedRatioCalculatorV5()
        
        # Minimal data
        fundamental_data = {
            'revenue': 394328000000
        }
        
        ratios = calculator.calculate_all_ratios('AAPL', fundamental_data, 150.0)
        
        # Should still calculate some ratios
        self.assertIsInstance(ratios, dict)
        # Should not crash with missing data

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    logger.info("Starting comprehensive fundamental ratio tests")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestDataValidator))
    test_suite.addTest(unittest.makeSuite(TestEnhancedRatioCalculator))
    test_suite.addTest(unittest.makeSuite(TestEnhancedDailyCalculator))
    test_suite.addTest(unittest.makeSuite(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures or result.errors:
        logger.error("❌ Some tests failed!")
        return False
    else:
        logger.info("🎉 All tests passed!")
        return True

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 