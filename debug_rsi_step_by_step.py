#!/usr/bin/env python3
"""
Debug RSI calculation step by step
"""

import sys
sys.path.append('daily_run')
sys.path.append('daily_run/indicators')

import pandas as pd
import numpy as np
from daily_run.database import DatabaseManager

def debug_rsi_calculation():
    """Debug RSI calculation step by step"""
    
    db = DatabaseManager()
    db.connect()
    
    # Get raw price data for AAPL
    price_data = db.get_price_data_for_technicals('AAPL', days=30)
    
    if not price_data:
        print("❌ No price data found")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(price_data)
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    
    print("🔍 STEP-BY-STEP RSI DEBUG")
    print("=" * 50)
    
    # Show last 10 closing prices
    print("📊 Last 10 closing prices:")
    closes = df['close'].tail(15)
    for i, price in enumerate(closes):
        print(f"  Day {i+1}: {price}")
    
    # Calculate price differences
    print(f"\n📈 Price differences:")
    delta = closes.diff()
    for i, diff in enumerate(delta[1:], 1):
        print(f"  Day {i}: {diff:.2f}")
    
    # Calculate gains and losses
    print(f"\n💹 Gains and losses (14-day average):")
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    print(f"  Gain series last 5: {gain.tail(5).tolist()}")
    print(f"  Loss series last 5: {loss.tail(5).tolist()}")
    
    latest_gain = gain.iloc[-1]
    latest_loss = loss.iloc[-1]
    print(f"  Latest average gain: {latest_gain:.4f}")
    print(f"  Latest average loss: {latest_loss:.4f}")
    
    # Calculate RS and RSI
    print(f"\n🎯 RSI calculation:")
    if latest_loss > 0:
        rs = latest_gain / latest_loss
        rsi = 100 - (100 / (1 + rs))
        print(f"  RS (gain/loss): {rs:.4f}")
        print(f"  RSI: {rsi:.2f}")
    else:
        print(f"  ❌ Latest loss is zero - cannot calculate RSI")
    
    # Compare with manual calculation using actual RSI function
    print(f"\n🔍 Using actual RSI function:")
    from rsi import calculate_rsi
    rsi_result = calculate_rsi(closes)
    if rsi_result is not None and len(rsi_result) > 0:
        actual_rsi = rsi_result.iloc[-1]
        print(f"  Function RSI: {actual_rsi:.2f}")
    else:
        print("  ❌ RSI function failed")
    
    # Check data quality
    print(f"\n📋 Data quality check:")
    print(f"  Price range: {closes.min():.2f} to {closes.max():.2f}")
    print(f"  Price volatility: {closes.std():.2f}")
    print(f"  Non-null prices: {closes.count()}/{len(closes)}")
    
    # Check if the problem is data uniformity
    recent_closes = closes.tail(5)
    if recent_closes.nunique() <= 1:
        print(f"  ⚠️  WARNING: Recent prices are identical - this breaks RSI!")
        print(f"     Last 5 prices: {recent_closes.tolist()}")
    
    db.disconnect()

if __name__ == "__main__":
    debug_rsi_calculation()
