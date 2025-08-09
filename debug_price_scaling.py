#!/usr/bin/env python3
"""
Debug price scaling issue in technical indicators
"""

import sys
sys.path.append('daily_run')

from daily_run.database import DatabaseManager

def debug_price_data():
    """Debug price data scaling issues"""
    
    db = DatabaseManager()
    db.connect()
    
    # Get raw price data for AAPL
    price_data = db.get_price_data_for_technicals('AAPL', days=10)
    
    if price_data:
        print("🔍 RAW PRICE DATA FROM DATABASE:")
        print("=" * 50)
        for i, row in enumerate(price_data[-5:]):  # Last 5 days
            print(f"Day {i+1}: Close={row['close']}, High={row['high']}, Low={row['low']}")
        
        print(f"\n📊 PRICE STATISTICS:")
        closes = [float(row['close']) for row in price_data]
        print(f"Latest close: {closes[-1]}")
        print(f"Median close: {sum(closes)/len(closes):.2f}")
        print(f"Min close: {min(closes)}")
        print(f"Max close: {max(closes)}")
        
        # Calculate price differences
        if len(closes) > 1:
            diffs = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            print(f"Typical price change: {sum(abs(d) for d in diffs)/len(diffs):.2f}")
            print(f"Max price change: {max(abs(d) for d in diffs):.2f}")
        
        # Test what happens with scaling
        print(f"\n⚠️  SCALING IMPACT:")
        test_price = closes[-1]
        print(f"Original price: {test_price}")
        if test_price > 1000:
            scaled_price = test_price / 100
            print(f"After /100 scaling: {scaled_price}")
            print(f"This means AAPL ~$228 becomes ~$228 → ~$2.28 ❌")
    
    db.disconnect()

if __name__ == "__main__":
    debug_price_data()
