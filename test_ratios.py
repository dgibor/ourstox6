#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

try:
    from daily_run.financial_ratios_calculator import FinancialRatiosCalculator
    print("Import successful!")
    
    calc = FinancialRatiosCalculator()
    print("Calculator created successfully!")
    
    # Test tickers: normal, missing data, negative EPS
    test_tickers = [
        'AAPL',      # Should have full data
        'GOOGL',     # Should have partial or full data
        'TSLA',      # Should have partial or full data
        'FAKE',      # Should not exist
    ]
    for ticker in test_tickers:
        print(f"\nTesting {ticker}:")
        ratios = calc.calculate_all_ratios(ticker)
        if ratios:
            for ratio_name, ratio_data in ratios.items():
                if isinstance(ratio_data, dict):
                    print(f"  {ratio_name}: {ratio_data.get('value')} ({ratio_data.get('quality_flag')})")
                else:
                    print(f"  {ratio_name}: {ratio_data}")
        else:
            print(f"  No ratios calculated for {ticker}")
    
    calc.close()
    print("Test completed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 