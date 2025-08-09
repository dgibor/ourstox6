#!/usr/bin/env python3
"""
Debug indicator scaling - compare fresh calculations vs database stored values
"""

import sys
sys.path.append('daily_run')
sys.path.append('utility_functions')

from daily_run.database import DatabaseManager
from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator

def debug_indicator_scaling():
    """Debug indicator scaling comparison"""
    
    db = DatabaseManager()
    db.connect()
    
    ticker = 'AAPL'
    print(f"🔍 INDICATOR SCALING DEBUG - {ticker}")
    print("=" * 60)
    
    # 1. Get fresh calculations from comprehensive calculator
    price_data = db.get_price_data_for_technicals(ticker, days=60)
    calculator = ComprehensiveTechnicalCalculator()
    fresh_indicators = calculator.calculate_all_indicators(ticker, price_data)
    
    # 2. Get stored values from database (properly scaled)
    query = """
    SELECT close, rsi_14, ema_20, ema_50, atr_14, bb_upper, bb_middle, bb_lower, adx_14, stoch_k
    FROM daily_charts 
    WHERE ticker = %s 
    ORDER BY date DESC 
    LIMIT 1
    """
    
    with db.get_cursor() as cursor:
        cursor.execute(query, (ticker,))
        result = cursor.fetchone()
    
    if result:
        # Apply proper scaling for stored values
        stored_data = {
            'close_stored': result[0],
            'rsi_14_stored': result[1] / 100.0 if result[1] else None,
            'ema_20_stored': result[2] / 100.0 if result[2] else None,
            'ema_50_stored': result[3] / 100.0 if result[3] else None,
            'atr_14_stored': result[4] / 100.0 if result[4] else None,
            'bb_upper_stored': result[5] / 100.0 if result[5] else None,
            'bb_middle_stored': result[6] / 100.0 if result[6] else None,
            'bb_lower_stored': result[7] / 100.0 if result[7] else None,
            'adx_14_stored': result[8] / 100.0 if result[8] else None,
            'stoch_k_stored': result[9] / 100.0 if result[9] else None,
        }
        
        print("📊 COMPARISON: Fresh vs Stored (with proper scaling)")
        print("-" * 60)
        
        # Compare key indicators
        comparisons = [
            ('RSI', fresh_indicators.get('rsi_14'), stored_data['rsi_14_stored']),
            ('EMA 20', fresh_indicators.get('ema_20'), stored_data['ema_20_stored']),
            ('EMA 50', fresh_indicators.get('ema_50'), stored_data['ema_50_stored']),
            ('ATR', fresh_indicators.get('atr_14'), stored_data['atr_14_stored']),
            ('BB Upper', fresh_indicators.get('bb_upper'), stored_data['bb_upper_stored']),
            ('ADX', fresh_indicators.get('adx_14'), stored_data['adx_14_stored']),
            ('Stoch %K', fresh_indicators.get('stoch_k'), stored_data['stoch_k_stored']),
        ]
        
        for name, fresh, stored in comparisons:
            if fresh is not None and stored is not None:
                diff = abs(fresh - stored)
                status = "✅" if diff < 1.0 else "❌"
                print(f"{status} {name:10}: Fresh={fresh:8.2f} | Stored={stored:8.2f} | Diff={diff:6.2f}")
            elif fresh is not None:
                print(f"🔍 {name:10}: Fresh={fresh:8.2f} | Stored=None")
            elif stored is not None:
                print(f"🔍 {name:10}: Fresh=None     | Stored={stored:8.2f}")
            else:
                print(f"❌ {name:10}: Both None")
        
        print(f"\n📋 Close price: {stored_data['close_stored']}")
        print(f"📋 Total fresh indicators: {len(fresh_indicators) if fresh_indicators else 0}")
    
    db.disconnect()

if __name__ == "__main__":
    debug_indicator_scaling()
