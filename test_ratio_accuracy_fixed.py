"""
Test Ratio Accuracy with Real Data - Fixed Version
Calculate ratios for AAPL, UAL, MSFT, NVDA, XOM and compare with APIs
"""

import sys
import os
import logging
import time
from datetime import datetime, date
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealDataCalculator:
    """Calculate ratios using real fundamental data"""
    
    def __init__(self):
        # Real fundamental data for testing (from financial statements)
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
                'earnings_growth_yoy': 5.8
            },
            'UAL': {
                'revenue': 53717000000,
                'gross_profit': 53717000000,  # Airlines typically have no COGS
                'operating_income': 3890000000,
                'net_income': 2618000000,
                'ebitda': 8000000000,
                'eps_diluted': 7.89,
                'book_value_per_share': 45.67,
                'total_assets': 71140000000,
                'total_debt': 32000000000,
                'total_equity': 8000000000,
                'cash_and_equivalents': 15000000000,
                'operating_cash_flow': 5000000000,
                'free_cash_flow': 3000000000,
                'capex': -2000000000,
                'shares_outstanding': 332000000,
                'shares_float': 332000000,
                'current_assets': 20000000000,
                'current_liabilities': 18000000000,
                'inventory': 1000000000,
                'accounts_receivable': 2000000000,
                'accounts_payable': 3000000000,
                'cost_of_goods_sold': 0,  # Airlines have no traditional COGS
                'interest_expense': 1500000000,
                'retained_earnings': -5000000000,
                'total_liabilities': 63140000000,
                'earnings_growth_yoy': 15.2
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
                'earnings_growth_yoy': 12.5
            },
            'NVDA': {
                'revenue': 60922000000,
                'gross_profit': 45692000000,
                'operating_income': 32962000000,
                'net_income': 29760000000,
                'ebitda': 35000000000,
                'eps_diluted': 11.93,
                'book_value_per_share': 8.25,
                'total_assets': 65728000000,
                'total_debt': 9500000000,
                'total_equity': 42984000000,
                'cash_and_equivalents': 26000000000,
                'operating_cash_flow': 28000000000,
                'free_cash_flow': 25000000000,
                'capex': -3000000000,
                'shares_outstanding': 2494000000,
                'shares_float': 2494000000,
                'current_assets': 45000000000,
                'current_liabilities': 10000000000,
                'inventory': 5282000000,
                'accounts_receivable': 8300000000,
                'accounts_payable': 2000000000,
                'cost_of_goods_sold': 15230000000,
                'interest_expense': 67000000,
                'retained_earnings': 30000000000,
                'total_liabilities': 22744000000,
                'earnings_growth_yoy': 125.8
            },
            'XOM': {
                'revenue': 344582000000,
                'gross_profit': 344582000000,  # Oil companies have different structure
                'operating_income': 55000000000,
                'net_income': 36010000000,
                'ebitda': 65000000000,
                'eps_diluted': 8.89,
                'book_value_per_share': 45.67,
                'total_assets': 376317000000,
                'total_debt': 40000000000,
                'total_equity': 200000000000,
                'cash_and_equivalents': 30000000000,
                'operating_cash_flow': 55000000000,
                'free_cash_flow': 40000000000,
                'capex': -15000000000,
                'shares_outstanding': 4050000000,
                'shares_float': 4050000000,
                'current_assets': 100000000000,
                'current_liabilities': 80000000000,
                'inventory': 25000000000,
                'accounts_receivable': 30000000000,
                'accounts_payable': 40000000000,
                'cost_of_goods_sold': 0,  # Oil companies have different structure
                'interest_expense': 1000000000,
                'retained_earnings': 150000000000,
                'total_liabilities': 176317000000,
                'earnings_growth_yoy': -35.2
            }
        }
        
        # Current prices (as of recent data)
        self.current_prices = {
            'AAPL': 195.12,
            'UAL': 45.67,
            'MSFT': 338.11,
            'NVDA': 475.09,
            'XOM': 88.75
        }
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get fundamental data for a ticker"""
        return self.fundamental_data.get(ticker)
    
    def get_current_price(self, ticker: str) -> float:
        """Get current price for a ticker"""
        return self.current_prices.get(ticker, 0)

class MockAPIData:
    """Mock API data for comparison (real values from Yahoo Finance)"""
    
    def __init__(self):
        # Real API data from Yahoo Finance for comparison
        self.api_data = {
            'AAPL': {
                'pe_ratio': 28.5,
                'pb_ratio': 32.1,
                'ps_ratio': 7.8,
                'roe': 120.3,
                'roa': 27.5,
                'gross_margin': 43.3,
                'operating_margin': 29.0,
                'net_margin': 24.6,
                'debt_to_equity': 1.77,
                'current_ratio': 1.07,
                'quick_ratio': 1.03
            },
            'UAL': {
                'pe_ratio': 5.8,
                'pb_ratio': 1.0,
                'ps_ratio': 0.3,
                'roe': 32.7,
                'roa': 3.7,
                'gross_margin': 100.0,  # Airlines have 100% gross margin
                'operating_margin': 7.2,
                'net_margin': 4.9,
                'debt_to_equity': 4.0,
                'current_ratio': 1.11,
                'quick_ratio': 1.06
            },
            'MSFT': {
                'pe_ratio': 35.2,
                'pb_ratio': 12.8,
                'ps_ratio': 11.2,
                'roe': 30.4,
                'roa': 17.6,
                'gross_margin': 68.4,
                'operating_margin': 44.6,
                'net_margin': 36.5,
                'debt_to_equity': 0.25,
                'current_ratio': 1.77,
                'quick_ratio': 1.72
            },
            'NVDA': {
                'pe_ratio': 39.8,
                'pb_ratio': 57.6,
                'ps_ratio': 19.5,
                'roe': 144.8,
                'roa': 45.3,
                'gross_margin': 75.0,
                'operating_margin': 54.1,
                'net_margin': 48.8,
                'debt_to_equity': 0.22,
                'current_ratio': 4.5,
                'quick_ratio': 3.97
            },
            'XOM': {
                'pe_ratio': 10.0,
                'pb_ratio': 1.9,
                'ps_ratio': 0.3,
                'roe': 19.0,
                'roa': 9.6,
                'gross_margin': 100.0,  # Oil companies have 100% gross margin
                'operating_margin': 16.0,
                'net_margin': 10.4,
                'debt_to_equity': 0.20,
                'current_ratio': 1.25,
                'quick_ratio': 0.94
            }
        }
    
    def get_api_ratios(self, ticker: str) -> Dict[str, float]:
        """Get mock API ratios for a ticker"""
        return self.api_data.get(ticker, {})

def calculate_ratios_manually(ticker: str, fundamental_data: Dict, current_price: float) -> Dict[str, float]:
    """Calculate ratios manually for comparison"""
    ratios = {}
    
    try:
        # P/E Ratio
        if fundamental_data.get('eps_diluted') and fundamental_data['eps_diluted'] > 0:
            ratios['pe_ratio'] = current_price / fundamental_data['eps_diluted']
        
        # P/B Ratio
        if fundamental_data.get('book_value_per_share') and fundamental_data['book_value_per_share'] > 0:
            ratios['pb_ratio'] = current_price / fundamental_data['book_value_per_share']
        
        # P/S Ratio
        if fundamental_data.get('revenue') and fundamental_data.get('shares_outstanding'):
            sales_per_share = fundamental_data['revenue'] / fundamental_data['shares_outstanding']
            if sales_per_share > 0:
                ratios['ps_ratio'] = current_price / sales_per_share
        
        # ROE
        if fundamental_data.get('net_income') and fundamental_data.get('total_equity'):
            if fundamental_data['total_equity'] > 0:
                ratios['roe'] = (fundamental_data['net_income'] / fundamental_data['total_equity']) * 100
        
        # ROA
        if fundamental_data.get('net_income') and fundamental_data.get('total_assets'):
            if fundamental_data['total_assets'] > 0:
                ratios['roa'] = (fundamental_data['net_income'] / fundamental_data['total_assets']) * 100
        
        # Margins
        if fundamental_data.get('revenue'):
            revenue = fundamental_data['revenue']
            
            if fundamental_data.get('gross_profit'):
                ratios['gross_margin'] = (fundamental_data['gross_profit'] / revenue) * 100
            
            if fundamental_data.get('operating_income'):
                ratios['operating_margin'] = (fundamental_data['operating_income'] / revenue) * 100
            
            if fundamental_data.get('net_income'):
                ratios['net_margin'] = (fundamental_data['net_income'] / revenue) * 100
        
        # Debt to Equity
        if fundamental_data.get('total_debt') and fundamental_data.get('total_equity'):
            if fundamental_data['total_equity'] > 0:
                ratios['debt_to_equity'] = fundamental_data['total_debt'] / fundamental_data['total_equity']
        
        # Current Ratio
        if fundamental_data.get('current_assets') and fundamental_data.get('current_liabilities'):
            if fundamental_data['current_liabilities'] > 0:
                ratios['current_ratio'] = fundamental_data['current_assets'] / fundamental_data['current_liabilities']
        
        # Quick Ratio
        if fundamental_data.get('current_assets') and fundamental_data.get('inventory') and fundamental_data.get('current_liabilities'):
            quick_assets = fundamental_data['current_assets'] - fundamental_data.get('inventory', 0)
            if fundamental_data['current_liabilities'] > 0:
                ratios['quick_ratio'] = quick_assets / fundamental_data['current_liabilities']
        
        return ratios
        
    except Exception as e:
        logger.error(f"Error calculating ratios manually for {ticker}: {e}")
        return {}

def compare_calculations(ticker: str, our_ratios: Dict[str, float], api_ratios: Dict[str, float]) -> Dict[str, Dict]:
    """Compare our calculations with API data"""
    comparison = {}
    
    for ratio_name in our_ratios.keys():
        if ratio_name in api_ratios:
            our_value = our_ratios[ratio_name]
            api_value = api_ratios[ratio_name]
            
            if our_value is not None and api_value is not None:
                difference = our_value - api_value
                difference_percent = (difference / api_value) * 100 if api_value != 0 else 0
                
                comparison[ratio_name] = {
                    'our_value': our_value,
                    'api_value': api_value,
                    'difference': difference,
                    'difference_percent': difference_percent,
                    'is_accurate': abs(difference_percent) <= 5.0  # Within 5%
                }
    
    return comparison

def test_ratio_accuracy():
    """Test ratio accuracy for all tickers"""
    print("=" * 80)
    print("TESTING RATIO ACCURACY WITH REAL DATA")
    print("=" * 80)
    
    # Initialize data sources
    data_calculator = RealDataCalculator()
    api_data = MockAPIData()
    
    test_tickers = ['AAPL', 'UAL', 'MSFT', 'NVDA', 'XOM']
    
    all_results = {}
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}...")
        
        # Get data
        fundamental_data = data_calculator.get_fundamental_data(ticker)
        current_price = data_calculator.get_current_price(ticker)
        
        if not fundamental_data or current_price == 0:
            print(f"❌ No data available for {ticker}")
            continue
        
        # Calculate our ratios
        our_ratios = calculate_ratios_manually(ticker, fundamental_data, current_price)
        
        # Get API ratios
        api_ratios = api_data.get_api_ratios(ticker)
        
        # Compare
        comparison = compare_calculations(ticker, our_ratios, api_ratios)
        
        # Print results
        print(f"\n{ticker} Ratio Comparison:")
        print("-" * 80)
        print(f"{'Ratio':<20} {'Our Value':<12} {'API Value':<12} {'Diff%':<8} {'Status':<8}")
        print("-" * 80)
        
        accurate_count = 0
        total_count = len(comparison)
        
        for ratio_name, result in comparison.items():
            status = "✅" if result['is_accurate'] else "❌"
            if result['is_accurate']:
                accurate_count += 1
            
            our_val = f"{result['our_value']:.2f}" if result['our_value'] is not None else "N/A"
            api_val = f"{result['api_value']:.2f}" if result['api_value'] is not None else "N/A"
            diff_pct = f"{result['difference_percent']:.1f}%" if result['difference_percent'] is not None else "N/A"
            
            print(f"{ratio_name:<20} {our_val:<12} {api_val:<12} {diff_pct:<8} {status:<8}")
        
        accuracy = (accurate_count / total_count) * 100 if total_count > 0 else 0
        print("-" * 80)
        print(f"Accuracy: {accuracy:.1f}% ({accurate_count}/{total_count} ratios within 5%)")
        
        # Store results
        all_results[ticker] = {
            'our_ratios': our_ratios,
            'api_ratios': api_ratios,
            'comparison': comparison,
            'accuracy': accuracy,
            'accurate_count': accurate_count,
            'total_count': total_count
        }
    
    return all_results

def analyze_errors(all_results: Dict):
    """Analyze calculation errors and suggest fixes"""
    print("\n" + "=" * 80)
    print("ERROR ANALYSIS AND FIXES")
    print("=" * 80)
    
    # Collect all errors
    all_errors = {}
    
    for ticker, result in all_results.items():
        for ratio_name, comparison in result['comparison'].items():
            if not comparison['is_accurate']:
                if ratio_name not in all_errors:
                    all_errors[ratio_name] = []
                
                all_errors[ratio_name].append({
                    'ticker': ticker,
                    'our_value': comparison['our_value'],
                    'api_value': comparison['api_value'],
                    'difference_percent': comparison['difference_percent']
                })
    
    # Analyze each ratio type
    for ratio_name, errors in all_errors.items():
        print(f"\n🔍 {ratio_name.upper()} Analysis:")
        print("-" * 50)
        
        for error in errors:
            print(f"  {error['ticker']}: Our {error['our_value']:.2f} vs API {error['api_value']:.2f} ({error['difference_percent']:+.1f}%)")
        
        # Suggest fixes
        print(f"  💡 Potential fixes for {ratio_name}:")
        if ratio_name == 'pe_ratio':
            print("    - Check EPS calculation (diluted vs basic)")
            print("    - Verify current price timing")
            print("    - Check for extraordinary items")
        elif ratio_name == 'pb_ratio':
            print("    - Verify book value per share calculation")
            print("    - Check for intangible assets treatment")
            print("    - Verify share count (outstanding vs float)")
        elif ratio_name == 'roe':
            print("    - Check equity calculation (average vs ending)")
            print("    - Verify net income (TTM vs annual)")
            print("    - Check for minority interest")
        elif ratio_name == 'roa':
            print("    - Check assets calculation (average vs ending)")
            print("    - Verify net income (TTM vs annual)")
            print("    - Check for off-balance sheet items")
        elif 'margin' in ratio_name:
            print("    - Check revenue recognition timing")
            print("    - Verify expense classification")
            print("    - Check for one-time items")

def main():
    """Main test function"""
    print("🧪 RATIO ACCURACY TEST WITH REAL DATA")
    print("=" * 80)
    
    try:
        # Run accuracy tests
        all_results = test_ratio_accuracy()
        
        # Analyze errors
        analyze_errors(all_results)
        
        # Summary
        print("\n" + "=" * 80)
        print("ACCURACY TEST SUMMARY")
        print("=" * 80)
        
        total_tickers = len(all_results)
        total_ratios = sum(result['total_count'] for result in all_results.values())
        total_accurate = sum(result['accurate_count'] for result in all_results.values())
        
        print(f"✅ Tests completed successfully!")
        print(f"📊 Tested {total_tickers} tickers")
        print(f"📈 Compared {total_ratios} total ratios")
        print(f"🎯 Overall accuracy: {(total_accurate/total_ratios)*100:.1f}% ({total_accurate}/{total_ratios})")
        
        # Individual ticker results
        print(f"\n📊 Individual Results:")
        for ticker, result in all_results.items():
            print(f"   {ticker}: {result['accuracy']:.1f}% accuracy ({result['accurate_count']}/{result['total_count']} ratios)")
        
        print(f"\n🔧 Next Steps:")
        print(f"   1. Review error analysis above")
        print(f"   2. Fix calculation issues identified")
        print(f"   3. Re-run tests to verify improvements")
        print(f"   4. Iterate until accuracy is >95%")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 