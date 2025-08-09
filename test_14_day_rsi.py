#!/usr/bin/env python3
"""
Test RSI calculation with exactly 14 days of data
"""

import sys
sys.path.append('daily_run')
sys.path.append('utility_functions')

from daily_run.database import DatabaseManager
from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator

def test_14_day_rsi():
    """Test RSI calculation with exactly 14 days"""
    
    db = DatabaseManager()
    db.connect()
    
    # Get exactly 14 days of data for AAPL
    price_data = db.get_price_data_for_technicals('AAPL', days=14)
    
    if not price_data or len(price_data) < 14:
        print(f"❌ Insufficient data: {len(price_data) if price_data else 0} days")
        db.disconnect()
        return
    
    print("🔍 14-DAY RSI TEST")
    print("=" * 40)
    print(f"📊 Data points: {len(price_data)}")
    
    # Show the closing prices
    closes = [float(row['close']) for row in price_data]
    print(f"📈 Price range: ${closes[0]:.2f} to ${closes[-1]:.2f}")
    print(f"📊 Last 5 closes: {[f'${c:.2f}' for c in closes[-5:]]}")
    
    # Test with comprehensive calculator
    calculator = ComprehensiveTechnicalCalculator()
    indicators = calculator.calculate_all_indicators('AAPL', price_data)
    
    if indicators and 'rsi_14' in indicators:
        rsi_value = indicators['rsi_14']
        print(f"\n✅ RSI (14-day): {rsi_value:.2f}")
        
        # Validate RSI range
        if 0 <= rsi_value <= 100:
            if rsi_value < 30:
                print(f"📉 Oversold territory (< 30)")
            elif rsi_value > 70:
                print(f"📈 Overbought territory (> 70)")
            else:
                print(f"📊 Neutral territory (30-70)")
        else:
            print(f"❌ Invalid RSI range! Should be 0-100")
    else:
        print(f"❌ RSI calculation failed")
        print(f"Available indicators: {list(indicators.keys()) if indicators else 'None'}")
    
    # Compare with different data lengths
    print(f"\n🔍 COMPARISON WITH DIFFERENT DATA LENGTHS:")
    
    for days in [15, 20, 30]:
        price_data_extended = db.get_price_data_for_technicals('AAPL', days=days)
        if price_data_extended and len(price_data_extended) >= 14:
            indicators_extended = calculator.calculate_all_indicators('AAPL', price_data_extended)
            if indicators_extended and 'rsi_14' in indicators_extended:
                rsi_extended = indicators_extended['rsi_14']
                print(f"  {days}-day data: RSI = {rsi_extended:.2f}")
    
    db.disconnect()

if __name__ == "__main__":
    test_14_day_rsi()
