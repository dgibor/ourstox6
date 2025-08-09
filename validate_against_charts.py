#!/usr/bin/env python3
"""
Validate our calculated indicators against the chart values shown in the images
"""

import sys
sys.path.append('daily_run')
sys.path.append('utility_functions')

from daily_run.database import DatabaseManager
from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator

def validate_against_charts():
    """Compare our calculations with chart values"""
    
    db = DatabaseManager()
    db.connect()
    
    calculator = ComprehensiveTechnicalCalculator()
    
    print("🔍 VALIDATING INDICATORS AGAINST CHART IMAGES")
    print("=" * 60)
    
    # Test tickers that appear in the charts
    test_cases = [
        {
            'ticker': 'AAPL',
            'chart_values': {
                'rsi_14': 55.41,  # From AAPL chart
                'adx_14': 23.22,  # From AAPL chart  
                'atr_14': 5.44,   # From AAPL chart
                'cci_20': 13.91   # From AAPL chart
            }
        },
        {
            'ticker': 'SPY',
            'chart_values': {
                'rsi_14': 65.16,  # From SPY chart
                'adx_14': 25.57,  # From SPY chart
                'atr_14': 5.90,   # From SPY chart
                'cci_20': 82.77   # From SPY chart
            }
        },
        {
            'ticker': 'NVDA',
            'chart_values': {
                'rsi_14': 69.09,  # From NVDA chart
                'adx_14': 44.62,  # From NVDA chart
                'atr_14': 4.33,   # From NVDA chart
                'cci_20': 102.39  # From NVDA chart
            }
        }
    ]
    
    for test_case in test_cases:
        ticker = test_case['ticker']
        chart_vals = test_case['chart_values']
        
        print(f"\n📊 {ticker} VALIDATION:")
        print("-" * 40)
        
        # Get price data and calculate indicators
        price_data = db.get_price_data_for_technicals(ticker, days=60)
        
        if not price_data or len(price_data) < 20:
            print(f"❌ {ticker}: Insufficient price data")
            continue
        
        indicators = calculator.calculate_all_indicators(ticker, price_data)
        
        if not indicators:
            print(f"❌ {ticker}: Failed to calculate indicators")
            continue
        
        print(f"✅ {ticker}: Calculated {len(indicators)} indicators")
        
        # Compare each indicator
        total_comparisons = 0
        accurate_comparisons = 0
        
        for indicator, chart_value in chart_vals.items():
            if indicator in indicators:
                our_value = indicators[indicator]
                diff = abs(our_value - chart_value)
                percent_diff = (diff / chart_value) * 100 if chart_value != 0 else 0
                
                # Determine accuracy (within 10% is good, within 5% is excellent)
                if percent_diff <= 5:
                    status = "🎯 EXCELLENT"
                    accurate_comparisons += 1
                elif percent_diff <= 10:
                    status = "✅ GOOD"
                    accurate_comparisons += 1
                elif percent_diff <= 20:
                    status = "⚠️  ACCEPTABLE"
                else:
                    status = "❌ POOR"
                
                total_comparisons += 1
                
                print(f"  {indicator.upper():8}: Chart={chart_value:6.2f} | Ours={our_value:6.2f} | Diff={diff:5.2f} ({percent_diff:4.1f}%) {status}")
            else:
                print(f"  {indicator.upper():8}: Chart={chart_value:6.2f} | Ours=MISSING")
        
        # Summary for this ticker
        if total_comparisons > 0:
            accuracy_rate = (accurate_comparisons / total_comparisons) * 100
            print(f"\n  📊 Accuracy: {accurate_comparisons}/{total_comparisons} ({accuracy_rate:.1f}%)")
        
        # Show some additional calculated indicators for reference
        print(f"\n  📋 Additional indicators:")
        additional_indicators = ['ema_20', 'ema_50', 'bb_upper', 'bb_lower', 'macd_line']
        for ind in additional_indicators:
            if ind in indicators:
                print(f"    {ind}: {indicators[ind]:.2f}")
    
    print(f"\n🎯 VALIDATION COMPLETE")
    print("=" * 60)
    print("📊 Notes:")
    print("- Chart values are from the provided trading platform images")
    print("- Differences can occur due to:")
    print("  • Different calculation periods or methods")
    print("  • Real-time vs historical data")
    print("  • Platform-specific indicator implementations")
    print("- Our indicators use standard mathematical formulas")
    print("- RSI uses exactly 14 days, ADX uses Wilder's smoothing")
    
    db.disconnect()

if __name__ == "__main__":
    validate_against_charts()
