#!/usr/bin/env python3
"""
Test reading properly scaled indicators from database
"""

import sys
sys.path.append('daily_run')

from daily_run.database import DatabaseManager

def test_database_indicators():
    """Test reading indicators with proper scaling from database"""
    
    db = DatabaseManager()
    db.connect()
    
    tickers = ['AAPL', 'CSCO', 'MSFT', 'GOOGL']
    
    print("🔍 TESTING DATABASE INDICATOR RETRIEVAL")
    print("=" * 60)
    
    for ticker in tickers:
        print(f"\n📊 {ticker}:")
        print("-" * 30)
        
        # Get latest stored indicators with proper scaling
        query = """
        SELECT date, close, 
               rsi_14, ema_20, ema_50, atr_14, adx_14, 
               bb_upper, bb_middle, bb_lower, 
               stoch_k, stoch_d, cci_20, macd_line
        FROM daily_charts 
        WHERE ticker = %s AND rsi_14 IS NOT NULL
        ORDER BY date DESC 
        LIMIT 1
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(query, (ticker,))
            result = cursor.fetchone()
        
        if result:
            # Proper scaling based on the documented convention
            close_price = result[1]  # Already in cents, convert to dollars
            rsi = result[2] / 100.0 if result[2] else None
            ema_20 = result[3] / 100.0 if result[3] else None
            ema_50 = result[4] / 100.0 if result[4] else None
            atr = result[5] / 100.0 if result[5] else None
            adx = result[6] / 100.0 if result[6] else None
            bb_upper = result[7] / 100.0 if result[7] else None
            bb_middle = result[8] / 100.0 if result[8] else None
            bb_lower = result[9] / 100.0 if result[9] else None
            stoch_k = result[10] / 100.0 if result[10] else None
            cci = result[12] / 100.0 if result[12] else None
            macd = result[13] / 100.0 if result[13] else None
            
            print(f"  Date: {result[0]}")
            print(f"  Close: ${close_price:.2f}")
            print(f"  RSI: {rsi:.1f}")
            print(f"  EMA 20: ${ema_20:.2f}")
            print(f"  EMA 50: ${ema_50:.2f}")
            print(f"  ATR: ${atr:.2f}")
            print(f"  ADX: {adx:.1f}")
            print(f"  BB Upper: ${bb_upper:.2f}")
            print(f"  BB Middle: ${bb_middle:.2f}")
            print(f"  BB Lower: ${bb_lower:.2f}")
            print(f"  Stoch %K: {stoch_k:.1f}")
            print(f"  CCI: {cci:.1f}")
            print(f"  MACD: {macd:.2f}")
            
            # Validate ranges
            issues = []
            if rsi and (rsi < 0 or rsi > 100):
                issues.append(f"RSI {rsi:.1f} out of range")
            if adx and (adx < 0 or adx > 100):
                issues.append(f"ADX {adx:.1f} out of range")
            if stoch_k and (stoch_k < 0 or stoch_k > 100):
                issues.append(f"Stoch %K {stoch_k:.1f} out of range")
            
            if issues:
                print(f"  ⚠️  Issues: {', '.join(issues)}")
            else:
                print(f"  ✅ All indicators in valid ranges")
        else:
            print(f"  ❌ No indicator data found")
    
    db.disconnect()

if __name__ == "__main__":
    test_database_indicators()
