#!/usr/bin/env python3
"""
Debug script to examine trading signal calculations
"""

import os
import sys
import logging
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import scoring calculator
from calc_technical_scores import TechnicalScoreCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_trading_signals():
    """Debug trading signal calculations for a few tickers"""
    
    calculator = TechnicalScoreCalculator()
    test_tickers = ['AAPL', 'MSFT', 'TSLA', 'NVDA']
    
    for ticker in test_tickers:
        print(f"\n{'='*60}")
        print(f"DEBUGGING TRADING SIGNALS FOR {ticker}")
        print(f"{'='*60}")
        
        # Get technical indicators
        indicators = calculator.get_technical_indicators(ticker)
        if not indicators:
            print(f"❌ No technical data for {ticker}")
            continue
        
        print(f"📊 Technical Indicators for {ticker}:")
        for key, value in indicators.items():
            if value is not None:
                print(f"   {key}: {value}")
        
        # Calculate trading signal manually
        rsi = indicators.get('rsi_14', 50)
        macd_line = indicators.get('macd_line', 0)
        macd_signal = indicators.get('macd_signal', 0)
        stoch_k = indicators.get('stoch_k', 50)
        cci = indicators.get('cci_20', 0)
        current_price = indicators.get('close', 0)
        nearest_support = indicators.get('nearest_support', 0)
        
        print(f"\n🔍 Trading Signal Components for {ticker}:")
        
        # RSI Buy Score
        if rsi is not None:
            # Scale down RSI to normal range (divide by ~10)
            rsi_scaled = rsi / 10
            if rsi_scaled < 20:  # Extremely oversold
                rsi_buy_score = 100
            elif rsi_scaled < 30:  # Oversold
                rsi_buy_score = 90
            elif rsi_scaled < 40:  # Moderately oversold
                rsi_buy_score = 75
            elif rsi_scaled < 50:  # Neutral to slightly oversold
                rsi_buy_score = 60
            elif rsi_scaled < 60:  # Neutral
                rsi_buy_score = 50
            elif rsi_scaled < 70:  # Neutral to slightly overbought
                rsi_buy_score = 40
            elif rsi_scaled < 80:  # Overbought
                rsi_buy_score = 25
            elif rsi_scaled < 90:  # Very overbought
                rsi_buy_score = 10
            else:  # Extremely overbought
                rsi_buy_score = 0
        else:
            rsi_buy_score = 50
        
        print(f"   RSI: {rsi} (scaled: {rsi_scaled if 'rsi_scaled' in locals() else 'N/A'}) → Buy Score: {rsi_buy_score}")
        
        # MACD Buy Score
        if (macd_line is not None and macd_signal is not None):
            macd_diff = macd_line - macd_signal
            # Scale down MACD difference (divide by ~100)
            macd_diff_scaled = macd_diff / 100
            if macd_diff_scaled > 5:  # Strong bullish
                macd_buy_score = 100
            elif macd_diff_scaled > 2:  # Bullish
                macd_buy_score = 80
            elif macd_diff_scaled > 0.5:  # Slightly bullish
                macd_buy_score = 65
            elif macd_diff_scaled > -0.5:  # Neutral
                macd_buy_score = 50
            elif macd_diff_scaled > -2:  # Slightly bearish
                macd_buy_score = 35
            elif macd_diff_scaled > -5:  # Bearish
                macd_buy_score = 20
            else:  # Strong bearish
                macd_buy_score = 0
        else:
            macd_buy_score = 50
        
        print(f"   MACD Diff: {macd_diff if 'macd_diff' in locals() else 'N/A'} (scaled: {macd_diff_scaled if 'macd_diff_scaled' in locals() else 'N/A'}) → Buy Score: {macd_buy_score}")
        
        # Stochastic Buy Score
        if stoch_k is not None:
            # Scale down Stochastic (divide by ~10)
            stoch_scaled = stoch_k / 10
            if stoch_scaled < 10:  # Extremely oversold
                stoch_buy_score = 100
            elif stoch_scaled < 20:  # Oversold
                stoch_buy_score = 90
            elif stoch_scaled < 30:  # Moderately oversold
                stoch_buy_score = 75
            elif stoch_scaled < 50:  # Neutral to slightly oversold
                stoch_buy_score = 60
            elif stoch_scaled < 70:  # Neutral
                stoch_buy_score = 50
            elif stoch_scaled < 80:  # Neutral to slightly overbought
                stoch_buy_score = 40
            elif stoch_scaled < 90:  # Overbought
                stoch_buy_score = 25
            else:  # Extremely overbought
                stoch_buy_score = 10
        else:
            stoch_buy_score = 50
        
        print(f"   Stochastic K: {stoch_k} (scaled: {stoch_scaled if 'stoch_scaled' in locals() else 'N/A'}) → Buy Score: {stoch_buy_score}")
        
        # CCI Buy Score
        if cci is not None:
            # Scale down CCI (divide by ~100)
            cci_scaled = cci / 100
            if cci_scaled < -200:  # Extremely oversold
                cci_buy_score = 100
            elif cci_scaled < -100:  # Oversold
                cci_buy_score = 80
            elif cci_scaled < -50:  # Moderately oversold
                cci_buy_score = 65
            elif cci_scaled < 0:  # Neutral to slightly oversold
                cci_buy_score = 55
            elif cci_scaled < 50:  # Neutral
                cci_buy_score = 50
            elif cci_scaled < 100:  # Neutral to slightly overbought
                cci_buy_score = 45
            elif cci_scaled < 200:  # Overbought
                cci_buy_score = 20
            else:  # Extremely overbought
                cci_buy_score = 0
        else:
            cci_buy_score = 50
        
        print(f"   CCI: {cci} (scaled: {cci_scaled if 'cci_scaled' in locals() else 'N/A'}) → Buy Score: {cci_buy_score}")
        
        # Price vs Support Score
        if (current_price is not None and nearest_support is not None and 
            current_price > 0 and nearest_support > 0):
            support_distance = abs(current_price - nearest_support) / current_price * 100
            if support_distance < 1:
                price_support_score = 100
            elif support_distance < 3:
                price_support_score = 85
            elif support_distance < 5:
                price_support_score = 70
            elif support_distance < 10:
                price_support_score = 50
            elif support_distance < 15:
                price_support_score = 30
            else:
                price_support_score = 15
        else:
            price_support_score = 50
        
        print(f"   Support Distance: {support_distance if 'support_distance' in locals() else 'N/A'}% → Score: {price_support_score}")
        
        # Calculate Buy Signals Component
        buy_signals = (
            rsi_buy_score * 0.25 +
            macd_buy_score * 0.25 +
            stoch_buy_score * 0.20 +
            cci_buy_score * 0.15 +
            price_support_score * 0.15
        )
        
        print(f"\n📈 Buy Signals Component: {buy_signals:.2f}")
        print(f"   RSI (25%): {rsi_buy_score * 0.25:.2f}")
        print(f"   MACD (25%): {macd_buy_score * 0.25:.2f}")
        print(f"   Stochastic (20%): {stoch_buy_score * 0.20:.2f}")
        print(f"   CCI (15%): {cci_buy_score * 0.15:.2f}")
        print(f"   Support (15%): {price_support_score * 0.15:.2f}")
        
        # Sell Signals Component
        sell_signals = 100 - buy_signals
        print(f"📉 Sell Signals Component: {sell_signals:.2f}")
        
        # Signal Strength
        adx = indicators.get('adx_14', 0)
        volume_sma = indicators.get('volume_sma_20', 0)
        current_volume = indicators.get('volume', 0)
        
        # ADX strength - Handle scaled data
        if adx is not None:
            # Scale down ADX (divide by ~100)
            adx_scaled = adx / 100
            if adx_scaled > 40:  # Very strong trend
                adx_strength = 100
            elif adx_scaled > 30:  # Strong trend
                adx_strength = 85
            elif adx_scaled > 25:  # Moderate trend
                adx_strength = 70
            elif adx_scaled > 20:  # Weak trend
                adx_strength = 55
            else:  # No trend
                adx_strength = 40
        else:
            adx_strength = 50
        
        if (volume_sma is not None and current_volume is not None and volume_sma > 0):
            volume_ratio = current_volume / volume_sma
            if volume_ratio > 2.0:  # Very high volume
                volume_strength = 100
            elif volume_ratio > 1.5:  # High volume
                volume_strength = 85
            elif volume_ratio > 1.2:  # Above average volume
                volume_strength = 70
            elif volume_ratio > 0.8:  # Average volume
                volume_strength = 50
            elif volume_ratio > 0.5:  # Below average volume
                volume_strength = 30
            else:  # Low volume
                volume_strength = 15
        else:
            volume_strength = 50
        
        signal_strength = (adx_strength * 0.6 + volume_strength * 0.4)
        print(f"💪 Signal Strength: {signal_strength:.2f}")
        print(f"   ADX Strength (60%): {adx_strength * 0.6:.2f} (ADX: {adx}, scaled: {adx_scaled if 'adx_scaled' in locals() else 'N/A'})")
        print(f"   Volume Strength (40%): {volume_strength * 0.4:.2f}")
        
        # Final Trading Signal Score
        trading_signal = (
            buy_signals * 0.40 +
            sell_signals * 0.40 +
            signal_strength * 0.20
        )
        
        print(f"\n🎯 FINAL TRADING SIGNAL SCORE: {trading_signal:.2f}")
        print(f"   Buy Signals (40%): {buy_signals * 0.40:.2f}")
        print(f"   Sell Signals (40%): {sell_signals * 0.40:.2f}")
        print(f"   Signal Strength (20%): {signal_strength * 0.20:.2f}")

if __name__ == "__main__":
    debug_trading_signals() 