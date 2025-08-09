#!/usr/bin/env python3
"""
Fix historical data corruption that's affecting technical indicator calculations
"""

import sys
sys.path.append('daily_run')

import pandas as pd
import numpy as np
from daily_run.database import DatabaseManager

def clean_historical_price_data(df):
    """Aggressively clean historical price data to remove scaling artifacts"""
    
    print(f"🔧 CLEANING DATA: {len(df)} rows")
    
    # Sort by date to ensure chronological order
    df = df.sort_values('date')
    
    # Show initial price range
    close_prices = df['close'].copy()
    print(f"  Initial close range: ${close_prices.min():.2f} to ${close_prices.max():.2f}")
    
    # Detect and fix obvious scaling issues
    # Rule 1: If price jumps more than 50x in one day, it's a scaling error
    price_ratios = close_prices.pct_change().abs()
    extreme_jumps = price_ratios > 5.0  # 500% change
    
    if extreme_jumps.any():
        print(f"  🚨 Found {extreme_jumps.sum()} extreme price jumps")
        
        # Fix by finding the most common price range and normalizing to it
        price_groups = []
        
        # Group prices by magnitude (cents vs dollars)
        for price in close_prices:
            if price < 10:
                price_groups.append(price * 100)  # Convert dollars to cents
            elif price > 1000:
                price_groups.append(price / 100)  # Convert cents to dollars  
            else:
                price_groups.append(price)  # Keep as-is
        
        # Find the median range to determine target scaling
        median_price = np.median(price_groups)
        
        # Apply consistent scaling
        if median_price > 500:  # Target is cents, convert all to cents
            for i in range(len(df)):
                if df.iloc[i]['close'] < 10:
                    for col in ['open', 'high', 'low', 'close']:
                        df.iloc[i, df.columns.get_loc(col)] *= 100
        else:  # Target is dollars, convert all to dollars
            for i in range(len(df)):
                if df.iloc[i]['close'] > 1000:
                    for col in ['open', 'high', 'low', 'close']:
                        df.iloc[i, df.columns.get_loc(col)] /= 100
    
    # Rule 2: Remove days where OHLC relationships are impossible
    # (e.g., close > high, close < low)
    invalid_rows = (
        (df['close'] > df['high']) | 
        (df['close'] < df['low']) | 
        (df['open'] > df['high']) | 
        (df['open'] < df['low'])
    )
    
    if invalid_rows.any():
        print(f"  🗑️  Removing {invalid_rows.sum()} rows with invalid OHLC relationships")
        df = df[~invalid_rows]
    
    # Rule 3: Remove outlier days (price changes > 30% are very rare)
    daily_changes = df['close'].pct_change().abs()
    outlier_days = daily_changes > 0.30
    
    if outlier_days.any():
        print(f"  🗑️  Removing {outlier_days.sum()} outlier days (>30% price change)")
        df = df[~outlier_days]
    
    # Final validation
    final_close = df['close'].copy()
    print(f"  Final close range: ${final_close.min():.2f} to ${final_close.max():.2f}")
    print(f"  Final data rows: {len(df)}")
    
    return df

def test_cleaned_indicators():
    """Test indicators with cleaned historical data"""
    
    db = DatabaseManager()
    db.connect()
    
    tickers = ['AAPL', 'NVDA']
    
    for ticker in tickers:
        print(f"\n🔍 TESTING {ticker} WITH CLEANED DATA:")
        print("=" * 50)
        
        # Get raw historical data
        price_data = db.get_price_data_for_technicals(ticker, days=30)
        
        if not price_data or len(price_data) < 20:
            print(f"❌ Insufficient data for {ticker}")
            continue
        
        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['close'])
        
        # Clean the historical data
        df_cleaned = clean_historical_price_data(df)
        
        if len(df_cleaned) < 14:
            print(f"❌ Not enough clean data for indicators")
            continue
        
        # Calculate indicators with clean data
        print(f"\n📊 CALCULATING INDICATORS:")
        
        # RSI with clean data
        sys.path.append('daily_run/indicators')
        from rsi import calculate_rsi
        
        recent_closes = df_cleaned['close'].tail(14)
        rsi_result = calculate_rsi(recent_closes)
        if rsi_result is not None and len(rsi_result) > 0:
            clean_rsi = rsi_result.iloc[-1]
            print(f"  RSI (clean): {clean_rsi:.2f}")
        
        # ATR with clean data
        from atr import calculate_atr
        
        if len(df_cleaned) >= 14:
            atr_result = calculate_atr(df_cleaned['high'], df_cleaned['low'], df_cleaned['close'])
            if atr_result is not None and len(atr_result) > 0:
                clean_atr = atr_result.iloc[-1]
                print(f"  ATR (clean): {clean_atr:.2f}")
        
        # ADX with original algorithm (not the fixed-value robust version)
        from adx import calculate_adx
        
        if len(df_cleaned) >= 28:
            adx_result = calculate_adx(df_cleaned['high'], df_cleaned['low'], df_cleaned['close'])
            if adx_result is not None and len(adx_result) > 0:
                clean_adx = adx_result.iloc[-1]
                print(f"  ADX (clean): {clean_adx:.2f}")
        
        # CCI with clean data
        from cci import calculate_cci
        
        if len(df_cleaned) >= 20:
            cci_result = calculate_cci(df_cleaned['high'], df_cleaned['low'], df_cleaned['close'])
            if cci_result is not None and len(cci_result) > 0:
                clean_cci = cci_result.iloc[-1]
                print(f"  CCI (clean): {clean_cci:.2f}")
    
    db.disconnect()

if __name__ == "__main__":
    test_cleaned_indicators()
