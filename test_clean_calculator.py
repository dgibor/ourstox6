#!/usr/bin/env python3
"""
Test the clean indicator calculator against chart values
"""

import sys
sys.path.append('daily_run')
sys.path.append('utility_functions')

from daily_run.database import DatabaseManager
from clean_indicator_calculator import CleanIndicatorCalculator

def test_clean_calculator():
    """Test clean calculator against chart values"""
    
    db = DatabaseManager()
    db.connect()
    
    calculator = CleanIndicatorCalculator()
    
    # Chart reference values from the images
    chart_values = {
        'AAPL': {'rsi_14': 55.41, 'adx_14': 23.22, 'atr_14': 5.44, 'cci_20': 13.91},
        'NVDA': {'rsi_14': 69.09, 'adx_14': 44.62, 'atr_14': 4.33, 'cci_20': 102.39},
        'SPY': {'rsi_14': 65.16, 'adx_14': 25.57, 'atr_14': 5.90, 'cci_20': 82.77}
    }
    
    print("🔍 TESTING CLEAN INDICATOR CALCULATOR")
    print("=" * 60)
    
    for ticker in ['AAPL', 'NVDA']:  # SPY has no data
        print(f"\n📊 {ticker} VALIDATION:")
        print("-" * 40)
        
        # Get price data
        price_data = db.get_price_data_for_technicals(ticker, days=60)
        
        if not price_data or len(price_data) < 10:
            print(f"❌ {ticker}: Insufficient price data")
            continue
        
        # Calculate with clean algorithm
        indicators = calculator.calculate_clean_indicators(ticker, price_data)
        
        if not indicators:
            print(f"❌ {ticker}: Failed to calculate indicators")
            continue
        
        # Compare with chart values
        chart_refs = chart_values[ticker]
        
        print(f"✅ {ticker}: Calculated {len(indicators)} indicators")
        
        comparisons = []
        for indicator, chart_value in chart_refs.items():
            if indicator in indicators:
                our_value = indicators[indicator]
                diff = abs(our_value - chart_value)
                percent_diff = (diff / chart_value) * 100 if chart_value != 0 else 0
                
                if percent_diff <= 5:
                    status = "🎯 EXCELLENT"
                elif percent_diff <= 10:
                    status = "✅ GOOD"  
                elif percent_diff <= 20:
                    status = "⚠️  ACCEPTABLE"
                else:
                    status = "❌ POOR"
                
                comparisons.append((indicator, chart_value, our_value, diff, percent_diff, status))
                print(f"  {indicator.upper():8}: Chart={chart_value:6.2f} | Clean={our_value:6.2f} | Diff={diff:5.2f} ({percent_diff:4.1f}%) {status}")
            else:
                print(f"  {indicator.upper():8}: Chart={chart_value:6.2f} | Clean=MISSING")
        
        # Calculate accuracy
        good_comparisons = sum(1 for _, _, _, _, percent_diff, _ in comparisons if percent_diff <= 10)
        total_comparisons = len(comparisons)
        
        if total_comparisons > 0:
            accuracy = (good_comparisons / total_comparisons) * 100
            print(f"\n  📊 Accuracy: {good_comparisons}/{total_comparisons} ({accuracy:.1f}%)")
        
        # Show additional calculated indicators
        print(f"\n  📋 Additional indicators:")
        additional = ['ema_20', 'ema_50', 'bb_upper', 'bb_lower', 'macd_line', 'stoch_k']
        for ind in additional:
            if ind in indicators:
                print(f"    {ind}: {indicators[ind]:.2f}")
    
    print(f"\n🎯 CLEAN CALCULATOR TEST COMPLETE")
    print("=" * 60)
    print("📊 This uses:")
    print("- Aggressive data corruption removal")
    print("- Synthetic historical data extension")
    print("- Original indicator algorithms (not modified versions)")
    print("- Clean recent data only")
    
    db.disconnect()

if __name__ == "__main__":
    test_clean_calculator()
