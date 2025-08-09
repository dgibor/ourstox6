#!/usr/bin/env python3
"""
Final fix: Use stored indicators with proper scaling + clean calculations for missing ones
"""

import sys
sys.path.append('daily_run')

from daily_run.database import DatabaseManager

def get_properly_scaled_stored_indicators():
    """Get stored indicators with proper scaling and compare to charts"""
    
    db = DatabaseManager()
    db.connect()
    
    # Chart reference values
    chart_values = {
        'AAPL': {'rsi': 55.41, 'adx': 23.22, 'atr': 5.44, 'cci': 13.91},
        'NVDA': {'rsi': 69.09, 'adx': 44.62, 'atr': 4.33, 'cci': 102.39}
    }
    
    print("🔍 TESTING STORED INDICATORS WITH PROPER SCALING")
    print("=" * 60)
    
    for ticker in ['AAPL', 'NVDA']:
        print(f"\n📊 {ticker}:")
        print("-" * 40)
        
        # Get latest stored indicators
        query = """
        SELECT date, close, rsi_14, adx_14, atr_14, cci_20,
               ema_20, ema_50, bb_upper, bb_lower, stoch_k, macd_line
        FROM daily_charts 
        WHERE ticker = %s AND rsi_14 IS NOT NULL
        ORDER BY date DESC 
        LIMIT 1
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(query, (ticker,))
            result = cursor.fetchone()
        
        if not result:
            print(f"❌ No stored indicators found")
            continue
        
        # Apply CORRECT scaling for indicators
        # Based on the specifications, indicators are stored * 100
        stored_indicators = {
            'rsi_14': result[2] / 100.0 if result[2] else None,
            'adx_14': result[3] / 100.0 if result[3] else None,
            'atr_14': result[4] / 100.0 if result[4] else None,
            'cci_20': result[5] / 100.0 if result[5] else None,
            'ema_20': result[6] / 100.0 if result[6] else None,
            'ema_50': result[7] / 100.0 if result[7] else None,
            'bb_upper': result[8] / 100.0 if result[8] else None,
            'bb_lower': result[9] / 100.0 if result[9] else None,
            'stoch_k': result[10] / 100.0 if result[10] else None,
            'macd_line': result[11] / 100.0 if result[11] else None
        }
        
        close_price = result[1]
        chart_ref = chart_values[ticker]
        
        print(f"Date: {result[0]}")
        print(f"Close: ${close_price:.2f}")
        print(f"\n📊 STORED vs CHART COMPARISON:")
        
        # Compare key indicators
        comparisons = [
            ('RSI', stored_indicators['rsi_14'], chart_ref['rsi']),
            ('ADX', stored_indicators['adx_14'], chart_ref['adx']),
            ('ATR', stored_indicators['atr_14'], chart_ref['atr']),
            ('CCI', stored_indicators['cci_20'], chart_ref['cci'])
        ]
        
        accurate_count = 0
        total_count = 0
        
        for name, stored_val, chart_val in comparisons:
            if stored_val is not None:
                diff = abs(stored_val - chart_val)
                percent_diff = (diff / chart_val) * 100 if chart_val != 0 else 0
                
                if percent_diff <= 10:
                    status = "✅ GOOD"
                    accurate_count += 1
                elif percent_diff <= 20:
                    status = "⚠️  OK"
                else:
                    status = "❌ POOR"
                
                total_count += 1
                print(f"  {name:3}: Stored={stored_val:6.2f} | Chart={chart_val:6.2f} | Diff={diff:5.2f} ({percent_diff:4.1f}%) {status}")
            else:
                print(f"  {name:3}: Stored=None     | Chart={chart_val:6.2f}")
        
        print(f"\n📊 Accuracy: {accurate_count}/{total_count} ({(accurate_count/total_count)*100:.1f}%)")
        
        # Show other indicators
        print(f"\n📋 Other stored indicators:")
        others = ['ema_20', 'ema_50', 'bb_upper', 'bb_lower', 'stoch_k', 'macd_line']
        for ind in others:
            if stored_indicators[ind] is not None:
                print(f"  {ind}: {stored_indicators[ind]:.2f}")
    
    print(f"\n🎯 CONCLUSION:")
    print("=" * 60)
    print("📊 If stored indicators are closer to chart values,")
    print("   then our calculation algorithms need adjustment.")
    print("📊 If our fresh calculations are closer,")
    print("   then we should use the comprehensive calculator.")
    print("📊 The goal is to match the professional trading platform values.")
    
    db.disconnect()

if __name__ == "__main__":
    get_properly_scaled_stored_indicators()
