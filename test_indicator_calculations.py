#!/usr/bin/env python3
"""
Test technical indicator calculations to verify they produce reasonable values
"""

import sys
sys.path.append('daily_run')
sys.path.append('utility_functions')

from daily_run.database import DatabaseManager
from comprehensive_technical_indicators_fix import ComprehensiveTechnicalCalculator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_indicator_calculations():
    """Test indicator calculations for a few known tickers"""
    
    # Test tickers with different price ranges and volumes
    test_tickers = ['AAPL', 'CSCO', 'MSFT', 'SPY', 'GOOGL']
    
    db = DatabaseManager()
    db.connect()
    
    calculator = ComprehensiveTechnicalCalculator()
    
    print("🔍 TESTING TECHNICAL INDICATOR CALCULATIONS")
    print("=" * 60)
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}:")
        print("-" * 30)
        
        try:
            # Get price data
            price_data = db.get_price_data_for_technicals(ticker, days=60)
            
            if not price_data or len(price_data) < 20:
                print(f"❌ {ticker}: Insufficient price data ({len(price_data) if price_data else 0} days)")
                continue
            
            # Calculate indicators
            indicators = calculator.calculate_all_indicators(ticker, price_data)
            
            if not indicators:
                print(f"❌ {ticker}: Failed to calculate indicators")
                continue
            print(f"✅ {ticker}: Calculated {len(indicators)} indicators")
            
            # Check key indicators for reasonable ranges
            checks_passed = 0
            total_checks = 0
            
            # RSI should be 0-100
            if 'rsi_14' in indicators:
                rsi = indicators['rsi_14']
                total_checks += 1
                if 0 <= rsi <= 100:
                    print(f"   ✅ RSI: {rsi:.1f} (valid range 0-100)")
                    checks_passed += 1
                else:
                    print(f"   ❌ RSI: {rsi:.1f} (invalid - should be 0-100)")
            
            # ADX should be 0-100
            if 'adx_14' in indicators:
                adx = indicators['adx_14']
                total_checks += 1
                if 0 <= adx <= 100:
                    print(f"   ✅ ADX: {adx:.1f} (valid range 0-100)")
                    checks_passed += 1
                else:
                    print(f"   ❌ ADX: {adx:.1f} (invalid - should be 0-100)")
            
            # ATR should be positive and reasonable
            if 'atr_14' in indicators:
                atr = indicators['atr_14']
                total_checks += 1
                if atr > 0 and atr < 100:  # Reasonable for most stocks
                    print(f"   ✅ ATR: {atr:.2f} (positive and reasonable)")
                    checks_passed += 1
                else:
                    print(f"   ❌ ATR: {atr:.2f} (should be positive and < 100)")
            
            # MACD should be reasonable relative to price
            if 'macd_line' in indicators:
                macd = indicators['macd_line']
                current_price = price_data[-1]['close'] if price_data else 100
                total_checks += 1
                if abs(macd) < current_price * 0.5:  # MACD shouldn't be more than 50% of price
                    print(f"   ✅ MACD: {macd:.2f} (reasonable vs price {current_price:.2f})")
                    checks_passed += 1
                else:
                    print(f"   ❌ MACD: {macd:.2f} (too large vs price {current_price:.2f})")
            
            # Bollinger Bands should be ordered: lower < middle < upper
            if all(x in indicators for x in ['bb_lower', 'bb_middle', 'bb_upper']):
                bb_lower = indicators['bb_lower']
                bb_middle = indicators['bb_middle']
                bb_upper = indicators['bb_upper']
                total_checks += 1
                if bb_lower < bb_middle < bb_upper:
                    print(f"   ✅ Bollinger Bands: {bb_lower:.2f} < {bb_middle:.2f} < {bb_upper:.2f}")
                    checks_passed += 1
                else:
                    print(f"   ❌ Bollinger Bands: {bb_lower:.2f}, {bb_middle:.2f}, {bb_upper:.2f} (wrong order)")
            
            # OBV should be large (volume accumulation)
            if 'obv' in indicators:
                obv = indicators['obv']
                total_checks += 1
                if abs(obv) > 1000:  # OBV should accumulate to meaningful values
                    print(f"   ✅ OBV: {obv:,.0f} (substantial volume accumulation)")
                    checks_passed += 1
                else:
                    print(f"   ❌ OBV: {obv:,.0f} (too small for volume accumulation)")
            
            # VPT should also be substantial
            if 'vpt' in indicators:
                vpt = indicators['vpt']
                total_checks += 1
                if abs(vpt) > 100:  # VPT should be meaningful
                    print(f"   ✅ VPT: {vpt:,.0f} (substantial price-volume trend)")
                    checks_passed += 1
                else:
                    print(f"   ❌ VPT: {vpt:,.0f} (too small)")
            
            # CCI should be reasonable (-300 to +300 typical range)
            if 'cci_20' in indicators:
                cci = indicators['cci_20']
                total_checks += 1
                if -500 <= cci <= 500:  # Extended range to be safe
                    print(f"   ✅ CCI: {cci:.1f} (reasonable range)")
                    checks_passed += 1
                else:
                    print(f"   ❌ CCI: {cci:.1f} (extreme value)")
            
            print(f"   📊 Overall: {checks_passed}/{total_checks} checks passed ({checks_passed/total_checks*100:.1f}%)")
            
            # Show some additional indicators for reference
            other_indicators = ['ema_20', 'ema_50', 'stoch_k', 'williams_r']
            print(f"   📋 Other indicators:")
            for ind in other_indicators:
                if ind in indicators:
                    print(f"      {ind}: {indicators[ind]:.2f}")
            
        except Exception as e:
            print(f"❌ {ticker}: Error calculating indicators: {e}")
            import traceback
            traceback.print_exc()
    
    db.disconnect()
    print("\n" + "=" * 60)
    print("🎯 INDICATOR CALCULATION TEST COMPLETED")

if __name__ == "__main__":
    test_indicator_calculations()
