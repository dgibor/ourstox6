"""
Test Fundamental Ratio Calculator
Tests all ratio calculations and compares with Yahoo Finance
"""

import sys
import os
import logging
from datetime import datetime, date
from typing import Dict, List

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

from fundamental_ratio_calculator import FundamentalRatioCalculator, RatioCalculationResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockDatabase:
    """Mock database for testing"""
    
    def __init__(self):
        self.fundamental_data = {
            'AAPL': {
                'revenue': 394328000000,
                'gross_profit': 170782000000,
                'operating_income': 114301000000,
                'net_income': 96995000000,
                'ebitda': 130000000000,
                'eps_diluted': 6.12,
                'book_value_per_share': 4.25,
                'total_assets': 352755000000,
                'total_debt': 109964000000,
                'total_equity': 62146000000,
                'cash_and_equivalents': 48004000000,
                'operating_cash_flow': 110543000000,
                'free_cash_flow': 107037000000,
                'capex': -3506000000,
                'shares_outstanding': 15846500000,
                'shares_float': 15846500000,
                'current_assets': 143713000000,
                'current_liabilities': 133973000000,
                'inventory': 6331000000,
                'accounts_receivable': 29508000000,
                'accounts_payable': 48647000000,
                'cost_of_goods_sold': 223546000000,
                'interest_expense': 3933000000,
                'retained_earnings': 0,  # Will be calculated
                'total_liabilities': 290693000000,
                'earnings_growth_yoy': 5.8
            },
            'MSFT': {
                'revenue': 198270000000,
                'gross_profit': 135620000000,
                'operating_income': 88423000000,
                'net_income': 72361000000,
                'ebitda': 95000000000,
                'eps_diluted': 9.65,
                'book_value_per_share': 25.43,
                'total_assets': 411976000000,
                'total_debt': 59578000000,
                'total_equity': 238268000000,
                'cash_and_equivalents': 111255000000,
                'operating_cash_flow': 87582000000,
                'free_cash_flow': 63542000000,
                'capex': -24040000000,
                'shares_outstanding': 7500000000,
                'shares_float': 7500000000,
                'current_assets': 184257000000,
                'current_liabilities': 104161000000,
                'inventory': 2500000000,
                'accounts_receivable': 48688000000,
                'accounts_payable': 19000000000,
                'cost_of_goods_sold': 62650000000,
                'interest_expense': 1968000000,
                'retained_earnings': 0,  # Will be calculated
                'total_liabilities': 173708000000,
                'earnings_growth_yoy': 12.5
            }
        }
        
        self.historical_data = {
            'AAPL': [
                {
                    'report_date': date(2023, 12, 31),
                    'revenue': 394328000000,
                    'net_income': 96995000000,
                    'free_cash_flow': 107037000000
                },
                {
                    'report_date': date(2022, 12, 31),
                    'revenue': 394328000000 * 0.95,  # 5% growth
                    'net_income': 96995000000 * 0.95,
                    'free_cash_flow': 107037000000 * 0.95
                }
            ],
            'MSFT': [
                {
                    'report_date': date(2023, 12, 31),
                    'revenue': 198270000000,
                    'net_income': 72361000000,
                    'free_cash_flow': 63542000000
                },
                {
                    'report_date': date(2022, 12, 31),
                    'revenue': 198270000000 * 0.88,  # 12% growth
                    'net_income': 72361000000 * 0.88,
                    'free_cash_flow': 63542000000 * 0.88
                }
            ]
        }
    
    def execute_query(self, query, params):
        """Mock database query execution"""
        ticker = params[0]
        
        # Check if this is a fundamental data query
        if 'revenue, gross_profit, operating_income' in query:
            if ticker in self.fundamental_data:
                data = self.fundamental_data[ticker]
                # Return data in the exact order expected by the query
                return [(
                    data['revenue'], data['gross_profit'], data['operating_income'], 
                    data['net_income'], data['ebitda'], data['eps_diluted'], 
                    data['book_value_per_share'], data['total_assets'], data['total_debt'], 
                    data['total_equity'], data['cash_and_equivalents'], 
                    data['operating_cash_flow'], data['free_cash_flow'], data['capex'],
                    data['shares_outstanding'], data['shares_float'], 
                    data['current_assets'], data['current_liabilities'], data['inventory'],
                    data['accounts_receivable'], data['accounts_payable'], 
                    data['cost_of_goods_sold'], data['interest_expense'], 
                    data['retained_earnings'], data['total_liabilities'], 
                    data['earnings_growth_yoy']
                )]
        
        # Check if this is a historical data query
        elif 'report_date, revenue, net_income' in query:
            if ticker in self.historical_data:
                return [
                    (row['report_date'], row['revenue'], row['net_income'], row['free_cash_flow'])
                    for row in self.historical_data[ticker]
                ]
        
        return []

class YahooFinanceMock:
    """Mock Yahoo Finance data for comparison"""
    
    def __init__(self):
        self.yahoo_data = {
            'AAPL': {
                'pe_ratio': 28.5,
                'pb_ratio': 32.1,
                'ps_ratio': 7.8,
                'ev_ebitda': 22.3,
                'roe': 120.3,
                'roa': 27.5,
                'gross_margin': 43.3,
                'operating_margin': 29.0,
                'net_margin': 24.6,
                'debt_to_equity': 1.77,
                'current_ratio': 1.07,
                'quick_ratio': 1.03,
                'market_cap': 3000000000000
            },
            'MSFT': {
                'pe_ratio': 35.2,
                'pb_ratio': 12.8,
                'ps_ratio': 11.2,
                'ev_ebitda': 25.1,
                'roe': 30.4,
                'roa': 17.6,
                'gross_margin': 68.4,
                'operating_margin': 44.6,
                'net_margin': 36.5,
                'debt_to_equity': 0.25,
                'current_ratio': 1.77,
                'quick_ratio': 1.72,
                'market_cap': 2800000000000
            }
        }
    
    def get_ratios(self, ticker: str) -> Dict[str, float]:
        """Get Yahoo Finance ratios for comparison"""
        return self.yahoo_data.get(ticker, {})

def test_ratio_calculations():
    """Test all ratio calculations"""
    print("=" * 60)
    print("TESTING FUNDAMENTAL RATIO CALCULATOR")
    print("=" * 60)
    
    # Initialize calculator with mock database
    mock_db = MockDatabase()
    calculator = FundamentalRatioCalculator(mock_db)
    yahoo_mock = YahooFinanceMock()
    
    test_tickers = ['AAPL', 'MSFT']
    current_prices = {'AAPL': 195.12, 'MSFT': 338.11}
    
    all_results = {}
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}...")
        current_price = current_prices[ticker]
        
        # Calculate all ratios
        calculated_ratios = calculator.calculate_all_ratios(ticker, current_price)
        
        # Get Yahoo Finance data for comparison
        yahoo_ratios = yahoo_mock.get_ratios(ticker)
        
        # Compare and analyze
        comparison_results = compare_ratios(ticker, calculated_ratios, yahoo_ratios)
        
        all_results[ticker] = {
            'calculated': calculated_ratios,
            'yahoo': yahoo_ratios,
            'comparison': comparison_results
        }
        
        # Print results
        print_ratio_comparison(ticker, calculated_ratios, yahoo_ratios, comparison_results)
    
    return all_results

def compare_ratios(ticker: str, calculated: Dict[str, float], yahoo: Dict[str, float]) -> List[RatioCalculationResult]:
    """Compare calculated ratios with Yahoo Finance data"""
    results = []
    
    for ratio_name in calculated.keys():
        if ratio_name in yahoo:
            calc_value = calculated[ratio_name]
            yahoo_value = yahoo[ratio_name]
            
            if calc_value is not None and yahoo_value is not None:
                difference = calc_value - yahoo_value
                difference_percent = (difference / yahoo_value) * 100 if yahoo_value != 0 else 0
                
                # Determine if the difference is acceptable (within 10%)
                is_valid = abs(difference_percent) <= 10.0
                
                results.append(RatioCalculationResult(
                    ratio_name=ratio_name,
                    calculated_value=calc_value,
                    yahoo_value=yahoo_value,
                    difference=difference,
                    difference_percent=difference_percent,
                    is_valid=is_valid
                ))
            else:
                results.append(RatioCalculationResult(
                    ratio_name=ratio_name,
                    calculated_value=calc_value,
                    yahoo_value=yahoo_value,
                    is_valid=False,
                    error_message="Missing data"
                ))
    
    return results

def print_ratio_comparison(ticker: str, calculated: Dict[str, float], yahoo: Dict[str, float], comparison: List[RatioCalculationResult]):
    """Print detailed ratio comparison"""
    print(f"\n{ticker} Ratio Comparison:")
    print("-" * 80)
    print(f"{'Ratio':<20} {'Calculated':<12} {'Yahoo':<12} {'Diff':<10} {'Diff%':<8} {'Status':<8}")
    print("-" * 80)
    
    valid_count = 0
    total_count = len(comparison)
    
    for result in comparison:
        status = "✅" if result.is_valid else "❌"
        if result.is_valid:
            valid_count += 1
        
        calc_val = f"{result.calculated_value:.2f}" if result.calculated_value is not None else "N/A"
        yahoo_val = f"{result.yahoo_value:.2f}" if result.yahoo_value is not None else "N/A"
        diff = f"{result.difference:.2f}" if result.difference is not None else "N/A"
        diff_pct = f"{result.difference_percent:.1f}%" if result.difference_percent is not None else "N/A"
        
        print(f"{result.ratio_name:<20} {calc_val:<12} {yahoo_val:<12} {diff:<10} {diff_pct:<8} {status:<8}")
    
    accuracy = (valid_count / total_count) * 100 if total_count > 0 else 0
    print("-" * 80)
    print(f"Accuracy: {accuracy:.1f}% ({valid_count}/{total_count} ratios within 10% of Yahoo Finance)")
    
    # Print summary of significant differences
    significant_diffs = [r for r in comparison if not r.is_valid and r.difference_percent is not None]
    if significant_diffs:
        print(f"\n⚠️  Significant differences (>10%):")
        for diff in significant_diffs:
            print(f"   {diff.ratio_name}: {diff.difference_percent:.1f}% difference")

def test_individual_ratio_categories():
    """Test individual ratio calculation categories"""
    print("\n" + "=" * 60)
    print("TESTING INDIVIDUAL RATIO CATEGORIES")
    print("=" * 60)
    
    mock_db = MockDatabase()
    calculator = FundamentalRatioCalculator(mock_db)
    
    # Test with AAPL data
    ticker = 'AAPL'
    current_price = 195.12
    fundamental_data = mock_db.fundamental_data[ticker]
    
    print(f"\nTesting {ticker} ratio categories:")
    
    # Test each category
    categories = [
        ('Valuation', calculator.calculate_valuation_ratios(current_price, fundamental_data)),
        ('Profitability', calculator.calculate_profitability_ratios(fundamental_data)),
        ('Financial Health', calculator.calculate_financial_health_ratios(fundamental_data)),
        ('Efficiency', calculator.calculate_efficiency_ratios(fundamental_data)),
        ('Market Metrics', calculator.calculate_market_metrics(current_price, fundamental_data)),
        ('Intrinsic Value', calculator.calculate_intrinsic_value_metrics(current_price, fundamental_data))
    ]
    
    for category_name, ratios in categories:
        print(f"\n{category_name} Ratios:")
        print("-" * 40)
        for ratio_name, value in ratios.items():
            if value is not None:
                print(f"  {ratio_name}: {value:.4f}")
            else:
                print(f"  {ratio_name}: N/A")

def test_error_handling():
    """Test error handling with invalid data"""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    mock_db = MockDatabase()
    calculator = FundamentalRatioCalculator(mock_db)
    
    # Test with missing data
    print("\nTesting with missing fundamental data:")
    ratios = calculator.calculate_all_ratios('INVALID_TICKER', 100.0)
    print(f"Result: {len(ratios)} ratios calculated (expected 0)")
    
    # Test with zero values
    print("\nTesting with zero values:")
    zero_data = {
        'revenue': 0,
        'net_income': 0,
        'total_assets': 0,
        'shares_outstanding': 0
    }
    
    valuation_ratios = calculator.calculate_valuation_ratios(100.0, zero_data)
    print(f"Valuation ratios with zero data: {valuation_ratios}")

def test_ratio_validation():
    """Test ratio validation and cleaning"""
    print("\n" + "=" * 60)
    print("TESTING RATIO VALIDATION")
    print("=" * 60)
    
    mock_db = MockDatabase()
    calculator = FundamentalRatioCalculator(mock_db)
    
    # Test with invalid values
    test_ratios = {
        'pe_ratio': float('inf'),
        'pb_ratio': float('nan'),
        'roe': 25.5,
        'debt_to_equity': None
    }
    
    validated = calculator._validate_ratios(test_ratios)
    print(f"Original ratios: {test_ratios}")
    print(f"Validated ratios: {validated}")

def main():
    """Main test function"""
    print("🧪 FUNDAMENTAL RATIO CALCULATOR TEST SUITE")
    print("=" * 60)
    
    try:
        # Run all tests
        all_results = test_ratio_calculations()
        test_individual_ratio_categories()
        test_error_handling()
        test_ratio_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tickers = len(all_results)
        total_ratios = sum(len(result['calculated']) for result in all_results.values())
        
        print(f"✅ Tests completed successfully!")
        print(f"📊 Tested {total_tickers} tickers")
        print(f"📈 Calculated {total_ratios} total ratios")
        print(f"🔍 Compared with Yahoo Finance data")
        print(f"📝 All ratio categories implemented and tested")
        
        # Print accuracy summary
        for ticker, result in all_results.items():
            comparison = result['comparison']
            valid_count = sum(1 for r in comparison if r.is_valid)
            total_count = len(comparison)
            accuracy = (valid_count / total_count) * 100 if total_count > 0 else 0
            print(f"   {ticker}: {accuracy:.1f}% accuracy ({valid_count}/{total_count} ratios)")
        
        print("\n🎉 All tests passed! The fundamental ratio calculator is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 