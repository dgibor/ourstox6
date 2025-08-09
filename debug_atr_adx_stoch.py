#!/usr/bin/env python3
"""
Debug ATR, ADX, and Stochastic calculations step by step
"""

import sys
sys.path.append('daily_run')
sys.path.append('daily_run/indicators')

import pandas as pd
import numpy as np
from daily_run.database import DatabaseManager

def debug_individual_indicators():
    """Debug ATR, ADX, and Stochastic calculations step by step"""
    
    db = DatabaseManager()
    db.connect()
    
    ticker = 'AAPL'
    print(f"🔍 DEBUGGING ATR, ADX, STOCHASTIC - {ticker}")
    print("=" * 60)
    
    # Get price data
    price_data = db.get_price_data_for_technicals(ticker, days=30)
    
    if not price_data:
        print("❌ No price data found")
        return
    
    # Convert to DataFrame and clean
    df = pd.DataFrame(price_data)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['close'])
    
    # Apply price scaling fix (same as comprehensive calculator)
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if col in df.columns:
            median_price = df[col].median()
            if median_price > 1000:
                print(f"Converting {col} from cents to dollars (median={median_price:.0f})")
                df[col] = df[col] / 100.0
    
    print(f"📊 Price data summary:")
    print(f"  Rows: {len(df)}")
    print(f"  Close range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
    print(f"  High range: ${df['high'].min():.2f} to ${df['high'].max():.2f}")
    print(f"  Low range: ${df['low'].min():.2f} to ${df['low'].max():.2f}")
    
    # Test RSI for comparison
    print(f"\n🔍 RSI CALCULATION (for comparison):")
    from rsi import calculate_rsi
    recent_closes = df['close'].tail(14)
    rsi_result = calculate_rsi(recent_closes)
    if rsi_result is not None and len(rsi_result) > 0:
        latest_rsi = rsi_result.iloc[-1]
        print(f"  RSI: {latest_rsi:.2f}")
    
    # Test ATR calculation
    print(f"\n🔍 ATR CALCULATION:")
    if len(df) >= 14:
        from atr import calculate_atr
        atr_result = calculate_atr(df['high'], df['low'], df['close'])
        if atr_result is not None and len(atr_result) > 0:
            latest_atr = atr_result.iloc[-1]
            print(f"  ATR: {latest_atr:.2f}")
            
            # Manual ATR validation
            tr1 = df['high'] - df['low']
            tr2 = abs(df['high'] - df['close'].shift())
            tr3 = abs(df['low'] - df['close'].shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            manual_atr = tr.rolling(window=14).mean().iloc[-1]
            print(f"  Manual ATR: {manual_atr:.2f}")
            print(f"  ATR vs RSI: {latest_atr:.2f} vs {latest_rsi:.2f} (should be very different!)")
        else:
            print(f"  ❌ ATR calculation failed")
    else:
        print(f"  ❌ Insufficient data for ATR")
    
    # Test ADX calculation
    print(f"\n🔍 ADX CALCULATION:")
    if len(df) >= 28:  # ADX needs more data
        from adx import calculate_adx
        adx_result = calculate_adx(df['high'], df['low'], df['close'])
        if adx_result is not None and len(adx_result) > 0:
            latest_adx = adx_result.iloc[-1]
            print(f"  ADX: {latest_adx:.2f}")
            
            # Check if all values are the same
            last_5_adx = adx_result.tail(5)
            if last_5_adx.nunique() <= 1:
                print(f"  ⚠️  WARNING: All recent ADX values are identical!")
                print(f"     Last 5 ADX: {last_5_adx.tolist()}")
        else:
            print(f"  ❌ ADX calculation failed")
    else:
        print(f"  ❌ Insufficient data for ADX")
    
    # Test Stochastic calculation
    print(f"\n🔍 STOCHASTIC CALCULATION:")
    if len(df) >= 14:
        from stochastic import calculate_stochastic
        stoch_k, stoch_d = calculate_stochastic(df['high'], df['low'], df['close'])
        if stoch_k is not None and len(stoch_k) > 0:
            latest_k = stoch_k.iloc[-1]
            latest_d = stoch_d.iloc[-1] if stoch_d is not None and len(stoch_d) > 0 else None
            print(f"  Stoch %K: {latest_k:.2f}")
            print(f"  Stoch %D: {latest_d:.2f}" if latest_d is not None else "  Stoch %D: None")
            
            # Manual validation
            lowest_low = df['low'].rolling(window=14).min().iloc[-1]
            highest_high = df['high'].rolling(window=14).max().iloc[-1]
            current_close = df['close'].iloc[-1]
            manual_k = 100 * ((current_close - lowest_low) / (highest_high - lowest_low))
            print(f"  Manual %K: {manual_k:.2f}")
            print(f"  Price range: ${lowest_low:.2f} to ${highest_high:.2f}")
            print(f"  Current close: ${current_close:.2f}")
        else:
            print(f"  ❌ Stochastic calculation failed")
    else:
        print(f"  ❌ Insufficient data for Stochastic")
    
    db.disconnect()

if __name__ == "__main__":
    debug_individual_indicators()
