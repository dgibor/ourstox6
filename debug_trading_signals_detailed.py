#!/usr/bin/env python3
"""
Debug Trading Signal Calculation - Detailed Analysis
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from calc_technical_scores import TechnicalScoreCalculator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_trading_signal_calculation():
    """Debug the trading signal calculation step by step"""
    
    calculator = TechnicalScoreCalculator()
    
    # Test with a few tickers
    test_tickers = ['AAPL', 'MSFT', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\n{'='*60}")
        print(f"DEBUGGING TRADING SIGNAL FOR {ticker}")
        print(f"{'='*60}")
        
        try:
            # Get technical indicators
            indicators = calculator.get_technical_indicators(ticker)
            print(f"Raw indicators for {ticker}:")
            for key, value in indicators.items():
                if value is not None:
                    print(f"  {key}: {value}")
            
            # Calculate trading signal step by step
            rsi = indicators.get('rsi_14', 50)
            macd_line = indicators.get('macd_line', 0)
            macd_signal = indicators.get('macd_signal', 0)
            stoch_k = indicators.get('stoch_k', 50)
            current_price = indicators.get('close', 0)
            nearest_support = indicators.get('nearest_support', 0)
            cci = indicators.get('cci_20', 0)
            adx = indicators.get('adx_14', 0)
            volume_sma = indicators.get('volume_sma_20', 0)
            current_volume = indicators.get('volume', 0)
            
            print(f"\nStep-by-step calculation for {ticker}:")
            
            # RSI Buy Score
            if rsi is not None:
                rsi_scaled = rsi / 10
                print(f"  RSI raw: {rsi}, scaled: {rsi_scaled}")
                if rsi_scaled < 20:
                    rsi_buy_score = 100
                elif rsi_scaled < 30:
                    rsi_buy_score = 90
                elif rsi_scaled < 40:
                    rsi_buy_score = 75
                elif rsi_scaled < 50:
                    rsi_buy_score = 60
                elif rsi_scaled < 60:
                    rsi_buy_score = 50
                elif rsi_scaled < 70:
                    rsi_buy_score = 40
                elif rsi_scaled < 80:
                    rsi_buy_score = 25
                elif rsi_scaled < 90:
                    rsi_buy_score = 10
                else:
                    rsi_buy_score = 0
                print(f"  RSI buy score: {rsi_buy_score}")
            else:
                rsi_buy_score = 50
                print(f"  RSI buy score: {rsi_buy_score} (default)")
            
            # MACD Buy Score
            if (macd_line is not None and macd_signal is not None):
                macd_diff = macd_line - macd_signal
                macd_diff_scaled = macd_diff / 100
                print(f"  MACD diff raw: {macd_diff}, scaled: {macd_diff_scaled}")
                if macd_diff_scaled > 5:
                    macd_buy_score = 100
                elif macd_diff_scaled > 2:
                    macd_buy_score = 80
                elif macd_diff_scaled > 0.5:
                    macd_buy_score = 65
                elif macd_diff_scaled > -0.5:
                    macd_buy_score = 50
                elif macd_diff_scaled > -2:
                    macd_buy_score = 35
                elif macd_diff_scaled > -5:
                    macd_buy_score = 20
                else:
                    macd_buy_score = 0
                print(f"  MACD buy score: {macd_buy_score}")
            else:
                macd_buy_score = 50
                print(f"  MACD buy score: {macd_buy_score} (default)")
            
            # Stochastic Buy Score
            if stoch_k is not None:
                stoch_scaled = stoch_k / 10
                print(f"  Stochastic raw: {stoch_k}, scaled: {stoch_scaled}")
                if stoch_scaled < 10:
                    stoch_buy_score = 100
                elif stoch_scaled < 20:
                    stoch_buy_score = 90
                elif stoch_scaled < 30:
                    stoch_buy_score = 75
                elif stoch_scaled < 50:
                    stoch_buy_score = 60
                elif stoch_scaled < 70:
                    stoch_buy_score = 50
                elif stoch_scaled < 80:
                    stoch_buy_score = 40
                elif stoch_scaled < 90:
                    stoch_buy_score = 25
                else:
                    stoch_buy_score = 10
                print(f"  Stochastic buy score: {stoch_buy_score}")
            else:
                stoch_buy_score = 50
                print(f"  Stochastic buy score: {stoch_buy_score} (default)")
            
            # CCI Buy Score
            if cci is not None:
                cci_scaled = cci / 100
                print(f"  CCI raw: {cci}, scaled: {cci_scaled}")
                if cci_scaled < -200:
                    cci_buy_score = 100
                elif cci_scaled < -100:
                    cci_buy_score = 80
                elif cci_scaled < -50:
                    cci_buy_score = 65
                elif cci_scaled < 0:
                    cci_buy_score = 55
                elif cci_scaled < 50:
                    cci_buy_score = 50
                elif cci_scaled < 100:
                    cci_buy_score = 45
                elif cci_scaled < 200:
                    cci_buy_score = 20
                else:
                    cci_buy_score = 0
                print(f"  CCI buy score: {cci_buy_score}")
            else:
                cci_buy_score = 50
                print(f"  CCI buy score: {cci_buy_score} (default)")
            
            # Price Support Score
            if (current_price is not None and nearest_support is not None and 
                current_price > 0 and nearest_support > 0):
                support_distance = abs(current_price - nearest_support) / current_price * 100
                print(f"  Support distance: {support_distance}%")
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
                print(f"  Price support score: {price_support_score}")
            else:
                price_support_score = 50
                print(f"  Price support score: {price_support_score} (default)")
            
            # Calculate Buy Signals
            buy_signals = (
                rsi_buy_score * 0.25 +
                macd_buy_score * 0.25 +
                stoch_buy_score * 0.20 +
                cci_buy_score * 0.15 +
                price_support_score * 0.15
            )
            print(f"  Buy signals: {buy_signals}")
            
            # Sell Signals (inverse)
            sell_signals = 100 - buy_signals
            print(f"  Sell signals: {sell_signals}")
            
            # Signal Strength
            if adx is not None:
                adx_scaled = adx / 100
                print(f"  ADX raw: {adx}, scaled: {adx_scaled}")
                if adx_scaled > 40:
                    adx_strength = 100
                elif adx_scaled > 30:
                    adx_strength = 85
                elif adx_scaled > 25:
                    adx_strength = 70
                elif adx_scaled > 20:
                    adx_strength = 55
                else:
                    adx_strength = 40
                print(f"  ADX strength: {adx_strength}")
            else:
                adx_strength = 50
                print(f"  ADX strength: {adx_strength} (default)")
            
            if (volume_sma is not None and current_volume is not None and volume_sma > 0):
                volume_ratio = current_volume / volume_sma
                print(f"  Volume ratio: {volume_ratio}")
                if volume_ratio > 2.0:
                    volume_strength = 100
                elif volume_ratio > 1.5:
                    volume_strength = 85
                elif volume_ratio > 1.2:
                    volume_strength = 70
                elif volume_ratio > 0.8:
                    volume_strength = 50
                elif volume_ratio > 0.5:
                    volume_strength = 30
                else:
                    volume_strength = 15
                print(f"  Volume strength: {volume_strength}")
            else:
                volume_strength = 50
                print(f"  Volume strength: {volume_strength} (default)")
            
            signal_strength = (adx_strength * 0.6 + volume_strength * 0.4)
            print(f"  Signal strength: {signal_strength}")
            
            # Final Trading Signal
            trading_signal = (
                buy_signals * 0.40 +
                sell_signals * 0.40 +
                signal_strength * 0.20
            )
            print(f"  FINAL TRADING SIGNAL: {trading_signal}")
            
            # Verify with the actual method
            actual_signal, components = calculator.calculate_trading_signal_score(indicators)
            print(f"  ACTUAL METHOD RESULT: {actual_signal}")
            print(f"  Components: {components}")
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    debug_trading_signal_calculation() 