#!/usr/bin/env python3
"""
Simple test using only the cleanest recent data
"""

import sys
sys.path.append('daily_run')
sys.path.append('daily_run/indicators')

import pandas as pd
import numpy as np
from daily_run.database import DatabaseManager

def simple_clean_test():
    """Test with minimal clean data approach"""
    
    db = DatabaseManager()
    db.connect()
    
    # Chart reference values
    chart_values = {
        'AAPL': {'rsi': 55.41, 'adx': 23.22, 'atr': 5.44, 'cci': 13.91},
        'NVDA': {'rsi': 69.09, 'adx': 44.62, 'atr': 4.33, 'cci': 102.39}
    }
    
    print("🔍 SIMPLE CLEAN DATA TEST")
    print("=" * 50)
    
    for ticker in ['AAPL', 'NVDA']:
        print(f"\n📊 {ticker}:")
        print("-" * 30)
        
        # Get the most recent clean data
        query = """
        SELECT date, close, high, low, open, volume
        FROM daily_charts 
        WHERE ticker = %s 
        ORDER BY date DESC 
        LIMIT 20
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(query, (ticker,))
            results = cursor.fetchall()
        
        if not results or len(results) < 10:
            print(f"❌ Insufficient data")
            continue
        
        # Convert to clean format - use only recent data where prices are reasonable
        clean_data = []
        for row in results:
            close = float(row[1])
            high = float(row[2]) 
            low = float(row[3])
            open_price = float(row[4])
            
            # Only include data where prices are in reasonable ranges (dollars, not cents)
            if 50 <= close <= 500:  # Reasonable stock price range
                clean_data.append({
                    'date': row[0],
                    'close': close,
                    'high': high,
                    'low': low,
                    'open': open_price,
                    'volume': row[5] if row[5] else 1000000
                })
        
        print(f"  Clean data points: {len(clean_data)}")
        
        if len(clean_data) < 8:
            print(f"  ❌ Not enough clean data for calculations")
            continue
        
        # Convert to DataFrame
        df = pd.DataFrame(clean_data)
        df = df.sort_values('date')
        
        print(f"  Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
        
        chart_ref = chart_values[ticker]
        
        # Try RSI with available data (even if less than 14 days)
        print(f"\n  🔍 RSI Test:")
        try:
            from rsi import calculate_rsi
            
            # Try with whatever data we have
            closes = df['close']
            for window in [min(len(closes)-1, 14), min(len(closes)-1, 10), min(len(closes)-1, 7)]:
                if window >= 3:
                    rsi_result = calculate_rsi(closes, window=window)
                    if rsi_result is not None and len(rsi_result) > 0:
                        rsi_val = rsi_result.iloc[-1]
                        if pd.notna(rsi_val) and 0 <= rsi_val <= 100:
                            diff = abs(rsi_val - chart_ref['rsi'])
                            print(f"    RSI-{window}: {rsi_val:.2f} (chart: {chart_ref['rsi']:.2f}, diff: {diff:.2f})")
        except Exception as e:
            print(f"    RSI error: {e}")
        
        # Try ATR 
        print(f"\n  🔍 ATR Test:")
        try:
            from atr import calculate_atr
            
            if len(df) >= 3:
                atr_result = calculate_atr(df['high'], df['low'], df['close'], window=min(len(df)-1, 14))
                if atr_result is not None and len(atr_result) > 0:
                    atr_val = atr_result.iloc[-1]
                    if pd.notna(atr_val) and atr_val > 0:
                        diff = abs(atr_val - chart_ref['atr'])
                        print(f"    ATR: {atr_val:.2f} (chart: {chart_ref['atr']:.2f}, diff: {diff:.2f})")
        except Exception as e:
            print(f"    ATR error: {e}")
        
        # Show the actual clean data we're working with
        print(f"\n  📋 Recent clean prices:")
        for i, row in df.tail(5).iterrows():
            print(f"    {row['date']}: ${row['close']:.2f}")
    
    print(f"\n🎯 ANALYSIS:")
    print("- Using only recent data where prices are in reasonable ranges ($50-$500)")
    print("- Limited to what we can calculate with available clean data")
    print("- This shows if the core issue is data corruption vs algorithm problems")
    
    db.disconnect()

if __name__ == "__main__":
    simple_clean_test()
