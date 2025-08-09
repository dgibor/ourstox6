#!/usr/bin/env python3
"""
Detailed ADX debugging to find why it always returns 100
"""

import sys
sys.path.append('daily_run')
sys.path.append('daily_run/indicators')

import pandas as pd
import numpy as np
from daily_run.database import DatabaseManager

def debug_adx_step_by_step():
    """Debug ADX calculation step by step"""
    
    db = DatabaseManager()
    db.connect()
    
    ticker = 'AAPL'
    print(f"🔍 ADX STEP-BY-STEP DEBUG - {ticker}")
    print("=" * 50)
    
    # Get price data
    price_data = db.get_price_data_for_technicals(ticker, days=40)
    df = pd.DataFrame(price_data)
    
    # Clean and scale data
    for col in ['open', 'high', 'low', 'close']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            median_price = df[col].median()
            if median_price > 1000:
                df[col] = df[col] / 100.0
    
    df = df.dropna(subset=['close'])
    
    print(f"📊 Data: {len(df)} rows, close range ${df['close'].min():.2f}-${df['close'].max():.2f}")
    
    if len(df) < 28:
        print("❌ Insufficient data for ADX")
        return
    
    # Manual ADX calculation step by step
    high = df['high']
    low = df['low']
    close = df['close']
    window = 14
    
    print(f"\n🔍 STEP 1: True Range Calculation")
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    print(f"  TR stats: min={tr.min():.4f}, max={tr.max():.4f}, mean={tr.mean():.4f}")
    
    print(f"\n🔍 STEP 2: Directional Movement")
    up_move = high - high.shift()
    down_move = low.shift() - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)
    
    print(f"  +DM stats: min={plus_dm.min():.4f}, max={plus_dm.max():.4f}, mean={plus_dm.mean():.4f}")
    print(f"  -DM stats: min={minus_dm.min():.4f}, max={minus_dm.max():.4f}, mean={minus_dm.mean():.4f}")
    
    print(f"\n🔍 STEP 3: Wilder's Smoothing")
    
    # Manual Wilder's smoothing
    def wilder_smoothing_debug(series, period):
        smoothed = pd.Series(index=series.index, dtype=float)
        smoothed.iloc[period-1] = series.iloc[:period].sum()
        
        for i in range(period, len(series)):
            prev_smooth = smoothed.iloc[i-1]
            current_val = series.iloc[i]
            smoothed.iloc[i] = prev_smooth - (prev_smooth/period) + current_val
        
        return smoothed
    
    tr_smooth = wilder_smoothing_debug(tr, window)
    plus_dm_smooth = wilder_smoothing_debug(plus_dm, window)
    minus_dm_smooth = wilder_smoothing_debug(minus_dm, window)
    
    print(f"  TR smoothed: min={tr_smooth.min():.4f}, max={tr_smooth.max():.4f}")
    print(f"  +DM smoothed: min={plus_dm_smooth.min():.4f}, max={plus_dm_smooth.max():.4f}")
    print(f"  -DM smoothed: min={minus_dm_smooth.min():.4f}, max={minus_dm_smooth.max():.4f}")
    
    print(f"\n🔍 STEP 4: Directional Indicators")
    plus_di = 100 * (plus_dm_smooth / tr_smooth.replace(0, np.nan))
    minus_di = 100 * (minus_dm_smooth / tr_smooth.replace(0, np.nan))
    
    print(f"  +DI stats: min={plus_di.min():.2f}, max={plus_di.max():.2f}, last={plus_di.iloc[-1]:.2f}")
    print(f"  -DI stats: min={minus_di.min():.2f}, max={minus_di.max():.2f}, last={minus_di.iloc[-1]:.2f}")
    
    print(f"\n🔍 STEP 5: Directional Index (DX)")
    di_sum = plus_di + minus_di
    di_diff = abs(plus_di - minus_di)
    
    print(f"  DI sum: min={di_sum.min():.2f}, max={di_sum.max():.2f}, last={di_sum.iloc[-1]:.2f}")
    print(f"  DI diff: min={di_diff.min():.2f}, max={di_diff.max():.2f}, last={di_diff.iloc[-1]:.2f}")
    
    # Check for problematic values
    zero_sum_count = (di_sum == 0).sum()
    if zero_sum_count > 0:
        print(f"  ⚠️  WARNING: {zero_sum_count} zero DI sums detected!")
    
    dx = 100 * di_diff / di_sum.replace(0, np.nan)
    print(f"  DX stats: min={dx.min():.2f}, max={dx.max():.2f}, last={dx.iloc[-1]:.2f}")
    
    # Check if DX has extreme values
    extreme_dx_count = (dx >= 99).sum()
    if extreme_dx_count > 0:
        print(f"  ⚠️  WARNING: {extreme_dx_count} extreme DX values (≥99)!")
    
    print(f"\n🔍 STEP 6: Final ADX")
    adx = wilder_smoothing_debug(dx, window)
    
    print(f"  ADX stats: min={adx.min():.2f}, max={adx.max():.2f}, last={adx.iloc[-1]:.2f}")
    print(f"  Last 5 ADX: {adx.tail(5).tolist()}")
    
    # Compare with library function
    print(f"\n🔍 LIBRARY ADX COMPARISON:")
    from adx import calculate_adx
    lib_adx = calculate_adx(high, low, close)
    if lib_adx is not None and len(lib_adx) > 0:
        print(f"  Library ADX: {lib_adx.iloc[-1]:.2f}")
        print(f"  Last 5 library ADX: {lib_adx.tail(5).tolist()}")
    
    db.disconnect()

if __name__ == "__main__":
    debug_adx_step_by_step()
