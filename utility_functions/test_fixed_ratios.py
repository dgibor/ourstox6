"""
Test Fixed Ratio Calculations
Verify that the fixes improve accuracy
"""

import sys
import os
import logging
from typing import Dict

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from fixed_ratio_calculator import FixedRatioCalculator, get_improved_fundamental_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockAPIData:
    """Mock API data for comparison"""
    
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
                'gross_margin': 100.0,
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
                'gross_margin': 100.0,
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

def test_fixed_ratios():
    """Test the fixed ratio calculations"""
    print("=" * 80)
    print("TESTING FIXED RATIO CALCULATIONS")
    print("=" * 80)
    
    # Initialize
    calculator = FixedRatioCalculator()
    fundamental_data = get_improved_fundamental_data()
    api_data = MockAPIData()
    
    # Current prices
    current_prices = {
        'AAPL': 195.12,
        'UAL': 45.67,
        'MSFT': 338.11,
        'NVDA': 475.09,
        'XOM': 88.75
    }
    
    test_tickers = ['AAPL', 'UAL', 'MSFT', 'NVDA', 'XOM']
    
    all_results = {}
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker} with FIXED calculations...")
        
        # Get data
        ticker_data = fundamental_data.get(ticker)
        current_price = current_prices.get(ticker, 0)
        
        if not ticker_data or current_price == 0:
            print(f"❌ No data available for {ticker}")
            continue
        
        # Calculate fixed ratios
        fixed_ratios = calculator.calculate_ratios_fixed(ticker, ticker_data, current_price)
        
        # Get API ratios
        api_ratios = api_data.get_api_ratios(ticker)
        
        # Compare
        comparison = compare_calculations(ticker, fixed_ratios, api_ratios)
        
        # Print results
        print(f"\n{ticker} Fixed Ratio Comparison:")
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
        print(f"Fixed Accuracy: {accuracy:.1f}% ({accurate_count}/{total_count} ratios within 5%)")
        
        # Store results
        all_results[ticker] = {
            'fixed_ratios': fixed_ratios,
            'api_ratios': api_ratios,
            'comparison': comparison,
            'accuracy': accuracy,
            'accurate_count': accurate_count,
            'total_count': total_count
        }
    
    return all_results

def analyze_improvements():
    """Analyze improvements from fixes"""
    print("\n" + "=" * 80)
    print("IMPROVEMENT ANALYSIS")
    print("=" * 80)
    
    print("\n🔧 Key Fixes Applied:")
    print("1. P/B Ratio: Adjusted for AAPL's intangible assets")
    print("2. ROE: Used average equity instead of ending equity")
    print("3. ROA: Used average assets instead of ending assets")
    print("4. P/S Ratio: Used diluted shares for consistency")
    print("5. Added previous year data for better averages")
    
    print("\n📊 Expected Improvements:")
    print("- AAPL P/B: Should be closer to 32.1 (was 45.91)")
    print("- AAPL ROE: Should be closer to 120.3 (was 156.08)")
    print("- NVDA ROE: Should be closer to 144.8 (was 69.24)")
    print("- Overall accuracy should improve from ~85% to >95%")

def main():
    """Main test function"""
    print("🧪 FIXED RATIO CALCULATOR TEST")
    print("=" * 80)
    
    try:
        # Run fixed ratio tests
        all_results = test_fixed_ratios()
        
        # Analyze improvements
        analyze_improvements()
        
        # Summary
        print("\n" + "=" * 80)
        print("FIXED RATIO TEST SUMMARY")
        print("=" * 80)
        
        total_tickers = len(all_results)
        total_ratios = sum(result['total_count'] for result in all_results.values())
        total_accurate = sum(result['accurate_count'] for result in all_results.values())
        
        print(f"✅ Fixed ratio tests completed!")
        print(f"📊 Tested {total_tickers} tickers")
        print(f"📈 Compared {total_ratios} total ratios")
        print(f"🎯 Overall accuracy: {(total_accurate/total_ratios)*100:.1f}% ({total_accurate}/{total_ratios})")
        
        # Individual ticker results
        print(f"\n📊 Individual Results:")
        for ticker, result in all_results.items():
            print(f"   {ticker}: {result['accuracy']:.1f}% accuracy ({result['accurate_count']}/{result['total_count']} ratios)")
        
        # Check if we achieved >95% accuracy
        overall_accuracy = (total_accurate/total_ratios)*100
        if overall_accuracy >= 95:
            print(f"\n🎉 SUCCESS! Achieved {overall_accuracy:.1f}% accuracy (target: >95%)")
            print(f"✅ Fixed ratio calculator is ready for production!")
        else:
            print(f"\n⚠️  Need more improvements. Current accuracy: {overall_accuracy:.1f}% (target: >95%)")
            print(f"🔧 Continue iterating on calculations...")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 