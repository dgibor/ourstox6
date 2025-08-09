#!/usr/bin/env python3
"""
Properly fix indicator calculations by creating a clean dataset
"""

import sys
sys.path.append('daily_run')
sys.path.append('daily_run/indicators')

import pandas as pd
import numpy as np
from daily_run.database import DatabaseManager

def create_clean_price_series(raw_data):
    """Create a clean price series by removing scaling artifacts"""
    
    df = pd.DataFrame(raw_data)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['close']).sort_values('date')
    
    print(f"📊 Raw data: {len(df)} rows, close range ${df['close'].min():.2f} to ${df['close'].max():.2f}")
    
    # Strategy: Use only the most recent data where prices are consistent
    # Look for the most recent continuous period with reasonable prices
    
    closes = df['close'].values
    
    # Find the cutoff point where prices become reasonable
    # Work backwards from the most recent data
    cutoff_idx = len(closes)
    
    for i in range(len(closes) - 1, 0, -1):
        current_price = closes[i]
        prev_price = closes[i-1]
        
        # If we see a jump bigger than 50x, this is where corruption starts
        if current_price / prev_price > 50 or prev_price / current_price > 50:
            cutoff_idx = i
            break
    
    # Take only the clean recent data
    clean_df = df.iloc[cutoff_idx:].copy()
    
    # If the recent data is in cents (all > 1000), convert to dollars
    if clean_df['close'].median() > 1000:
        for col in ['open', 'high', 'low', 'close']:
            if col in clean_df.columns:
                clean_df[col] = clean_df[col] / 100.0
    
    print(f"✅ Clean data: {len(clean_df)} rows, close range ${clean_df['close'].min():.2f} to ${clean_df['close'].max():.2f}")
    
    return clean_df

def test_with_clean_calculations():
    """Test indicators with properly cleaned data"""
    
    db = DatabaseManager()
    db.connect()
    
    # Chart reference values
    chart_values = {
        'AAPL': {'rsi': 55.41, 'adx': 23.22, 'atr': 5.44, 'cci': 13.91},
        'NVDA': {'rsi': 69.09, 'adx': 44.62, 'atr': 4.33, 'cci': 102.39}
    }
    
    for ticker in ['AAPL', 'NVDA']:
        print(f"\n🔍 {ticker} - CLEAN CALCULATION TEST:")
        print("=" * 50)
        
        # Get more data to ensure we have enough after cleaning
        raw_data = db.get_price_data_for_technicals(ticker, days=60)
        
        if not raw_data or len(raw_data) < 30:
            print(f"❌ Insufficient raw data")
            continue
        
        # Create clean dataset
        clean_df = create_clean_price_series(raw_data)
        
        if len(clean_df) < 20:
            print(f"❌ Not enough clean data")
            continue
        
        chart_ref = chart_values[ticker]
        
        # Test RSI with different periods to see what matches
        print(f"\n📊 RSI ANALYSIS:")
        from rsi import calculate_rsi
        
        for period in [14, 10, 7]:
            if len(clean_df) >= period:
                recent_closes = clean_df['close'].tail(period)
                rsi_result = calculate_rsi(recent_closes, window=period)
                if rsi_result is not None and len(rsi_result) > 0:
                    rsi_val = rsi_result.iloc[-1]
                    diff = abs(rsi_val - chart_ref['rsi'])
                    print(f"  RSI-{period}: {rsi_val:.2f} (chart: {chart_ref['rsi']:.2f}, diff: {diff:.2f})")
        
        # Test ATR
        print(f"\n📊 ATR ANALYSIS:")
        from atr import calculate_atr
        
        if len(clean_df) >= 14:
            atr_result = calculate_atr(clean_df['high'], clean_df['low'], clean_df['close'])
            if atr_result is not None and len(atr_result) > 0:
                atr_val = atr_result.iloc[-1]
                diff = abs(atr_val - chart_ref['atr'])
                print(f"  ATR-14: {atr_val:.2f} (chart: {chart_ref['atr']:.2f}, diff: {diff:.2f})")
        
        # Test ADX (use original, not robust version)
        print(f"\n📊 ADX ANALYSIS:")
        from adx import calculate_adx
        
        if len(clean_df) >= 28:
            adx_result = calculate_adx(clean_df['high'], clean_df['low'], clean_df['close'])
            if adx_result is not None and len(adx_result) > 0:
                adx_val = adx_result.iloc[-1]
                # Check if it's the clipped 100 value or a real calculation
                if adx_val >= 99.9:
                    print(f"  ADX-14: {adx_val:.2f} (CLIPPED - algorithm issue)")
                else:
                    diff = abs(adx_val - chart_ref['adx'])
                    print(f"  ADX-14: {adx_val:.2f} (chart: {chart_ref['adx']:.2f}, diff: {diff:.2f})")
        
        # Test CCI with different periods
        print(f"\n📊 CCI ANALYSIS:")
        from cci import calculate_cci
        
        for period in [20, 14, 10]:
            if len(clean_df) >= period:
                cci_result = calculate_cci(clean_df['high'], clean_df['low'], clean_df['close'], period)
                if cci_result is not None and len(cci_result) > 0:
                    cci_val = cci_result.iloc[-1]
                    diff = abs(cci_val - chart_ref['cci'])
                    print(f"  CCI-{period}: {cci_val:.2f} (chart: {chart_ref['cci']:.2f}, diff: {diff:.2f})")
        
        # Show price statistics
        print(f"\n📋 PRICE STATS:")
        print(f"  Latest close: ${clean_df['close'].iloc[-1]:.2f}")
        print(f"  14-day range: ${clean_df['close'].tail(14).min():.2f} to ${clean_df['close'].tail(14).max():.2f}")
        print(f"  14-day volatility: {clean_df['close'].tail(14).std():.2f}")
    
    db.disconnect()

if __name__ == "__main__":
    test_with_clean_calculations()
