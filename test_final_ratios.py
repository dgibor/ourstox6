#!/usr/bin/env python3
"""
Final test script to verify all fixes are working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Load environment variables
load_dotenv()

def test_final_ratios():
    """Test the final financial ratios with all fixes applied"""
    print("🧮 Final Test - Financial Ratios Calculator")
    print("=" * 50)
    
    # Import the updated calculator
    from daily_run.financial_ratios_calculator import FinancialRatiosCalculator
    
    calculator = FinancialRatiosCalculator()
    
    test_tickers = ['AAPL', 'AMZN', 'AVGO', 'NVDA', 'XOM']
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}:")
        print("-" * 30)
        
        try:
            # Get stock data
            stock_data = calculator.get_stock_data(ticker)
            if stock_data:
                print(f"  Current Price: ${stock_data['current_price']:,.2f}" if stock_data['current_price'] else "  Current Price: None")
                print(f"  Market Cap: ${stock_data['market_cap']:,.0f}" if stock_data['market_cap'] else "  Market Cap: None")
                print(f"  Revenue TTM: ${stock_data['revenue_ttm']:,.0f}" if stock_data['revenue_ttm'] else "  Revenue TTM: None")
                print(f"  Diluted EPS TTM: {stock_data['diluted_eps_ttm']}" if stock_data['diluted_eps_ttm'] else "  Diluted EPS TTM: None")
                print(f"  Book Value per Share: {stock_data['book_value_per_share']}" if stock_data['book_value_per_share'] else "  Book Value per Share: None")
                print(f"  EBITDA TTM: ${stock_data['ebitda_ttm']:,.0f}" if stock_data['ebitda_ttm'] else "  EBITDA TTM: None")
                
                # Calculate ratios
                ratios = calculator.calculate_all_ratios(ticker)
                if ratios:
                    print(f"\n  📈 Calculated Ratios:")
                    for ratio_name, ratio_data in ratios.items():
                        value = ratio_data['value']
                        flag = ratio_data['quality_flag']
                        if value is not None:
                            print(f"    {ratio_name.upper()}: {value:.2f} ({flag})")
                        else:
                            print(f"    {ratio_name.upper()}: {flag}")
                else:
                    print(f"  ❌ Could not calculate ratios")
            else:
                print(f"  ❌ No stock data available")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    calculator.close()
    
    print(f"\n✅ Final test completed!")

if __name__ == "__main__":
    test_final_ratios() 