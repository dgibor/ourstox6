#!/usr/bin/env python3
"""
Test the comprehensive calculator directly to debug RSI issue
"""

import sys
sys.path.append('daily_run')
sys.path.append('utility_functions')

from daily_run.database import DatabaseManager
import pandas as pd

def test_comprehensive_calculator():
    """Test the comprehensive calculator step by step"""
    
    db = DatabaseManager()
    db.connect()
    
    # Get raw price data for AAPL exactly as the comprehensive calculator does
    price_data = db.get_price_data_for_technicals('AAPL', days=60)
    
    if not price_data:
        print("❌ No price data found")
        return
    
    print("🔍 COMPREHENSIVE CALCULATOR DEBUG")
    print("=" * 50)
    
    # Step 1: Prepare data exactly as comprehensive calculator does
    print("📊 Step 1: Data preparation")
    df = pd.DataFrame(price_data)
    print(f"  Raw data rows: {len(df)}")
    
    # Convert columns to numeric
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows with NaN values in price columns
    df = df.dropna(subset=['close'])
    print(f"  After cleaning: {len(df)} rows")
    
    # Show last few closes
    print(f"  Last 5 closes: {df['close'].tail(5).tolist()}")
    
    # Step 2: RSI calculation exactly as comprehensive calculator does
    print(f"\n📈 Step 2: RSI calculation")
    if len(df) >= 14:
        # Import exactly as the comprehensive calculator does
        sys.path.append('daily_run/indicators')
        from rsi import calculate_rsi
        
        rsi_result = calculate_rsi(df['close'])
        print(f"  RSI result type: {type(rsi_result)}")
        print(f"  RSI result length: {len(rsi_result) if rsi_result is not None else 'None'}")
        
        if rsi_result is not None and len(rsi_result) > 0:
            latest_rsi = rsi_result.iloc[-1]
            print(f"  Latest RSI raw: {latest_rsi}")
            print(f"  Is not NaN: {pd.notna(latest_rsi)}")
            print(f"  Is not zero: {latest_rsi != 0}")
            
            if pd.notna(latest_rsi) and latest_rsi != 0:
                final_rsi = float(latest_rsi)
                print(f"  ✅ Final RSI: {final_rsi}")
            else:
                print(f"  ❌ RSI filtered out by validation")
        else:
            print(f"  ❌ RSI calculation failed")
    else:
        print(f"  ❌ Insufficient data for RSI ({len(df)} < 14)")
    
    # Step 3: Compare with direct comprehensive calculator
    print(f"\n🔧 Step 3: Using actual comprehensive calculator")
    from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator
    
    calculator = ComprehensiveTechnicalCalculator()
    indicators = calculator.calculate_all_indicators('AAPL', price_data)
    
    if indicators and 'rsi_14' in indicators:
        print(f"  ✅ Comprehensive calculator RSI: {indicators['rsi_14']}")
    else:
        print(f"  ❌ Comprehensive calculator failed to calculate RSI")
        print(f"  Available indicators: {list(indicators.keys()) if indicators else 'None'}")
    
    db.disconnect()

if __name__ == "__main__":
    test_comprehensive_calculator()
