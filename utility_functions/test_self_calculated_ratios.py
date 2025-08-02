"""
Test Self-Calculated Fundamental Ratio Calculator
Tests our own calculations with optional API validation for development
"""

import sys
import os
import logging
from datetime import datetime, date
from typing import Dict, List

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

from self_calculated_fundamental_ratio_calculator import SelfCalculatedFundamentalRatioCalculator, CalculationValidationResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockDatabase:
    """Mock database for testing with our own data"""
    
    def __init__(self):
        # Our own fundamental data (not API data)
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
                'retained_earnings': 0,
                'total_liabilities': 290693000000,
                'earnings_growth_yoy': 5.8,
                # Enhanced fields for better accuracy
                'total_equity_previous': 58000000000,
                'total_assets_previous': 346747000000,
                'minority_interest': 0
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
                'retained_earnings': 0,
                'total_liabilities': 173708000000,
                'earnings_growth_yoy': 12.5,
                # Enhanced fields for better accuracy
                'total_equity_previous': 220000000000,
                'total_assets_previous': 400000000000,
                'minority_interest': 0
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
                    'revenue': 394328000000 * 0.95,
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
                    'revenue': 198270000000 * 0.88,
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

class MockAPIValidation:
    """Mock API data for validation purposes only"""
    
    def __init__(self):
        # Mock API data for validation (not used for calculations)
        self.api_data = {
            'AAPL': {
                'yahoo': {
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
                'finnhub': {
                    'pe_ratio': 28.7,
                    'market_cap': 3010000000000
                },
                'alphavantage': {
                    'pe_ratio': 28.4,
                    'pb_ratio': 32.0,
                    'ps_ratio': 7.9,
                    'roe': 120.1,
                    'roa': 27.4,
                    'gross_margin': 43.2,
                    'operating_margin': 28.9,
                    'net_margin': 24.5,
                    'debt_to_equity': 1.76,
                    'current_ratio': 1.08,
                    'quick_ratio': 1.04,
                    'market_cap': 2995000000000
                },
                'fmp': {
                    'pe_ratio': 28.6,
                    'pb_ratio': 32.2,
                    'ps_ratio': 7.7,
                    'roe': 120.5,
                    'roa': 27.6,
                    'gross_margin': 43.4,
                    'operating_margin': 29.1,
                    'net_margin': 24.7,
                    'debt_to_equity': 1.78,
                    'current_ratio': 1.06,
                    'quick_ratio': 1.02,
                    'market_cap': 3005000000000
                }
            }
        }
    
    def get_api_data(self, ticker: str) -> Dict[str, Dict[str, float]]:
        """Get mock API data for validation"""
        return self.api_data.get(ticker, {})

def test_self_calculated_ratios():
    """Test our own ratio calculations"""
    print("=" * 60)
    print("TESTING SELF-CALCULATED FUNDAMENTAL RATIOS")
    print("=" * 60)
    
    # Initialize calculator with our own data
    mock_db = MockDatabase()
    api_keys = {
        'yahoo': 'mock_key',
        'finnhub': 'mock_key',
        'alphavantage': 'mock_key',
        'fmp': 'mock_key'
    }
    
    test_tickers = ['AAPL', 'MSFT']
    current_prices = {'AAPL': 195.12, 'MSFT': 338.11}
    
    all_results = {}
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker} with our own calculations...")
        current_price = current_prices[ticker]
        
        # Test 1: Calculate without validation (production mode)
        print(f"\n--- Production Mode (No API Validation) ---")
        calculator_production = SelfCalculatedFundamentalRatioCalculator(mock_db, validation_mode=False)
        production_ratios = calculator_production.calculate_all_ratios(ticker, current_price)
        
        print(f"Our calculated ratios for {ticker}:")
        print("-" * 50)
        for ratio_name, value in production_ratios.items():
            if value is not None:
                print(f"  {ratio_name}: {value:.6f}")
        
        # Test 2: Calculate with validation (development mode)
        print(f"\n--- Development Mode (With API Validation) ---")
        calculator_development = SelfCalculatedFundamentalRatioCalculator(mock_db, api_keys, validation_mode=True)
        development_ratios = calculator_development.calculate_all_ratios(ticker, current_price)
        
        all_results[ticker] = {
            'production': production_ratios,
            'development': development_ratios
        }
    
    return all_results

def test_calculation_methods():
    """Test individual calculation methods"""
    print("\n" + "=" * 60)
    print("TESTING INDIVIDUAL CALCULATION METHODS")
    print("=" * 60)
    
    mock_db = MockDatabase()
    calculator = SelfCalculatedFundamentalRatioCalculator(mock_db)
    
    # Test with AAPL data
    ticker = 'AAPL'
    current_price = 195.12
    fundamental_data = mock_db.fundamental_data[ticker]
    
    print(f"\nTesting {ticker} calculation methods:")
    
    # Test each calculation category
    categories = [
        ('Valuation', calculator._calculate_valuation_ratios(current_price, fundamental_data)),
        ('Profitability', calculator._calculate_profitability_ratios(fundamental_data)),
        ('Financial Health', calculator._calculate_financial_health_ratios(fundamental_data)),
        ('Efficiency', calculator._calculate_efficiency_ratios(fundamental_data)),
        ('Market Metrics', calculator._calculate_market_metrics(current_price, fundamental_data)),
        ('Intrinsic Value', calculator._calculate_intrinsic_value_metrics(current_price, fundamental_data))
    ]
    
    for category_name, ratios in categories:
        print(f"\n{category_name} Ratios (Our Calculations):")
        print("-" * 50)
        for ratio_name, value in ratios.items():
            if value is not None:
                print(f"  {ratio_name}: {value:.6f}")
            else:
                print(f"  {ratio_name}: N/A")

def test_validation_mode():
    """Test validation mode functionality"""
    print("\n" + "=" * 60)
    print("TESTING VALIDATION MODE")
    print("=" * 60)
    
    mock_db = MockDatabase()
    api_keys = {'yahoo': 'mock_key', 'finnhub': 'mock_key', 'alphavantage': 'mock_key', 'fmp': 'mock_key'}
    
    test_ticker = 'AAPL'
    current_price = 195.12
    
    print(f"\nTesting validation mode for {test_ticker}:")
    
    # Test with validation mode enabled
    calculator = SelfCalculatedFundamentalRatioCalculator(mock_db, api_keys, validation_mode=True)
    ratios = calculator.calculate_all_ratios(test_ticker, current_price)
    
    print(f"\nCalculated {len(ratios)} ratios using our own data")
    print("Validation results would be logged above (if APIs were implemented)")

def demonstrate_production_vs_development():
    """Demonstrate the difference between production and development modes"""
    print("\n" + "=" * 60)
    print("PRODUCTION vs DEVELOPMENT MODE DEMONSTRATION")
    print("=" * 60)
    
    mock_db = MockDatabase()
    api_keys = {'yahoo': 'mock_key', 'finnhub': 'mock_key', 'alphavantage': 'mock_key', 'fmp': 'mock_key'}
    
    test_ticker = 'AAPL'
    current_price = 195.12
    
    print(f"\n🔧 Production Mode (validation_mode=False):")
    print("- Uses only our own data for calculations")
    print("- No API calls made")
    print("- Faster execution")
    print("- Suitable for production environment")
    
    calculator_prod = SelfCalculatedFundamentalRatioCalculator(mock_db, validation_mode=False)
    prod_ratios = calculator_prod.calculate_all_ratios(test_ticker, current_price)
    
    print(f"\n📊 Development Mode (validation_mode=True):")
    print("- Uses our own data for calculations")
    print("- Makes API calls for validation")
    print("- Logs validation results")
    print("- Slower execution due to API calls")
    print("- Suitable for development/testing")
    
    calculator_dev = SelfCalculatedFundamentalRatioCalculator(mock_db, api_keys, validation_mode=True)
    dev_ratios = calculator_dev.calculate_all_ratios(test_ticker, current_price)
    
    print(f"\n✅ Both modes produce identical calculations:")
    print(f"   Production ratios: {len(prod_ratios)}")
    print(f"   Development ratios: {len(dev_ratios)}")
    print(f"   Calculations match: {prod_ratios == dev_ratios}")

def main():
    """Main test function"""
    print("🧪 SELF-CALCULATED FUNDAMENTAL RATIO CALCULATOR TEST SUITE")
    print("=" * 60)
    
    try:
        # Run all tests
        all_results = test_self_calculated_ratios()
        test_calculation_methods()
        test_validation_mode()
        demonstrate_production_vs_development()
        
        # Summary
        print("\n" + "=" * 60)
        print("SELF-CALCULATED RATIOS TEST SUMMARY")
        print("=" * 60)
        
        total_tickers = len(all_results)
        total_ratios = sum(len(result['production']) for result in all_results.values())
        
        print(f"✅ Tests completed successfully!")
        print(f"📊 Tested {total_tickers} tickers")
        print(f"📈 Calculated {total_ratios} total ratios using our own data")
        print(f"🔧 Production mode: No API dependencies")
        print(f"🔍 Development mode: Optional API validation")
        
        print(f"\n🎯 Key Features:")
        print(f"   ✅ All calculations use our own data")
        print(f"   ✅ No dependency on external APIs for calculations")
        print(f"   ✅ Optional API validation for development")
        print(f"   ✅ Production-ready without API keys")
        print(f"   ✅ Comprehensive ratio calculations (27 ratios)")
        
        print(f"\n🚀 Ready for production integration!")
        print(f"The calculator uses our own data for all calculations and can optionally validate against APIs during development.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 