#!/usr/bin/env python3
"""
Comprehensive Technical Indicators Fix

This script fixes the technical indicator calculation system to calculate ALL available indicators:
1. Basic indicators: RSI, EMA, MACD
2. Bollinger Bands: Upper, Middle, Lower
3. Stochastic: %K and %D
4. Support & Resistance: Multiple levels and swing points
5. Additional indicators: CCI, ADX, ATR, VWAP
6. Fibonacci levels and pivot points

The current system only calculates 6 indicators but the database has 52 columns!
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add daily_run to path
sys.path.append('daily_run')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_technical_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTechnicalCalculator:
    """Comprehensive technical indicator calculator"""
    
    def __init__(self):
        self.indicators_calculated = 0
        self.indicators_failed = 0
        
    def get_all_indicator_names(self) -> List[str]:
        """Get all indicator names that this calculator can calculate"""
        return [
            # Basic indicators
            'rsi_14', 'cci_20', 'atr_14', 'adx_14',
            'ema_20', 'ema_50', 'ema_100', 'ema_200',
            'macd_line', 'macd_signal', 'macd_histogram',
            
            # Bollinger Bands
            'bb_upper', 'bb_middle', 'bb_lower',
            
            # Stochastic
            'stoch_k', 'stoch_d',
            
            # Support & Resistance (all database columns)
            'pivot_point', 'pivot_fibonacci', 'pivot_camarilla', 'pivot_woodie', 'pivot_demark',
            'resistance_1', 'resistance_2', 'resistance_3',
            'support_1', 'support_2', 'support_3',
            'swing_high_5d', 'swing_low_5d', 'swing_high_10d', 'swing_low_10d',
            'swing_high_20d', 'swing_low_20d',
            'week_high', 'week_low', 'month_high', 'month_low',
            'nearest_support', 'nearest_resistance',
            'support_strength', 'resistance_strength', 'volume_confirmation',
            'swing_strengths', 'level_type',
            
            # Fibonacci Levels
            'fib_236', 'fib_382', 'fib_500', 'fib_618', 'fib_786',
            'fib_1272', 'fib_1618', 'fib_2618',
            
            # Dynamic Levels
            'dynamic_resistance', 'dynamic_support',
            'keltner_upper', 'keltner_lower',
            
            # Volume-weighted Levels
            'vwap', 'volume_weighted_high', 'volume_weighted_low',
            
            # Additional Enhanced Indicators
            'nearest_fib_support', 'nearest_fib_resistance',
            'nearest_psych_support', 'nearest_psych_resistance',
            'nearest_volume_support', 'nearest_volume_resistance',
            
            # Volume indicators
            'obv', 'vpt',
            
            # Williams %R
            'williams_r'
        ]
    
    def calculate_all_indicators(self, ticker: str, price_data: List[Dict]) -> Optional[Dict]:
        """
        Calculate ALL technical indicators for a single ticker
        Returns comprehensive dictionary with all calculated indicators
        """
        try:
            # Prepare price data
            df = self._prepare_price_data(price_data)
            if df is None or len(df) < 14:
                logger.warning(f"Insufficient data for {ticker}: {len(df) if df is not None else 0} days < 14")
                return None
            
            indicators = {}
            
            # 1. Basic Technical Indicators
            indicators.update(self._calculate_basic_indicators(df, ticker))
            
            # 2. Bollinger Bands
            indicators.update(self._calculate_bollinger_bands(df, ticker))
            
            # 3. Stochastic Oscillator
            indicators.update(self._calculate_stochastic(df, ticker))
            
            # 4. Support & Resistance Levels
            indicators.update(self._calculate_support_resistance(df, ticker))
            
            # 5. Additional Indicators
            indicators.update(self._calculate_additional_indicators(df, ticker))
            
            # 6. VWAP and Volume Indicators
            indicators.update(self._calculate_volume_indicators(df, ticker))
            
            # Filter out None values and log results
            valid_indicators = {k: v for k, v in indicators.items() if v is not None and v != 0}
            
            logger.info(f"✅ {ticker}: Calculated {len(valid_indicators)}/{len(indicators)} indicators")
            self.indicators_calculated += len(valid_indicators)
            self.indicators_failed += (len(indicators) - len(valid_indicators))
            
            return valid_indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {ticker}: {e}")
            return None
    
    def _prepare_price_data(self, price_data: List[Dict]) -> Optional[pd.DataFrame]:
        """Prepare price data for calculations"""
        try:
            df = pd.DataFrame(price_data)
            if df.empty:
                return None
                
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            
            if df.empty:
                return None
            
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # Ensure numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove rows with NaN values in price columns
            df = df.dropna(subset=['close'])
            
            # Convert prices from cents to dollars if needed
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if col in df.columns:
                    try:
                        median_val = df[col].dropna().median()
                        if median_val and median_val > 1000:
                            df[col] = df[col] / 100.0
                    except Exception:
                        continue
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing price data: {e}")
            return None
    
    def _calculate_basic_indicators(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Calculate basic technical indicators: RSI, EMA, MACD"""
        indicators = {}
        
        try:
            # RSI
            if len(df) >= 14:
                from indicators.rsi import calculate_rsi
                rsi_result = calculate_rsi(df['close'])
                if rsi_result is not None and len(rsi_result) > 0:
                    latest_rsi = rsi_result.iloc[-1]
                    if pd.notna(latest_rsi) and latest_rsi != 0:
                        indicators['rsi_14'] = float(latest_rsi)
            
            # EMA calculations
            if len(df) >= 20:
                from indicators.ema import calculate_ema
                
                # EMA 20
                ema_20 = calculate_ema(df['close'], 20)
                if ema_20 is not None and len(ema_20) > 0:
                    latest_ema20 = ema_20.iloc[-1]
                    if pd.notna(latest_ema20) and latest_ema20 != 0:
                        indicators['ema_20'] = float(latest_ema20)
                
                # EMA 50
                if len(df) >= 50:
                    ema_50 = calculate_ema(df['close'], 50)
                    if ema_50 is not None and len(ema_50) > 0:
                        latest_ema50 = ema_50.iloc[-1]
                        if pd.notna(latest_ema50) and latest_ema50 != 0:
                            indicators['ema_50'] = float(latest_ema50)
                
                # EMA 100
                if len(df) >= 100:
                    ema_100 = calculate_ema(df['close'], 100)
                    if ema_100 is not None and len(ema_100) > 0:
                        latest_ema100 = ema_100.iloc[-1]
                        if pd.notna(latest_ema100) and latest_ema100 != 0:
                            indicators['ema_100'] = float(latest_ema100)
                
                # EMA 200
                if len(df) >= 200:
                    ema_200 = calculate_ema(df['close'], 200)
                    if ema_200 is not None and len(ema_200) > 0:
                        latest_ema200 = ema_200.iloc[-1]
                        if pd.notna(latest_ema200) and latest_ema200 != 0:
                            indicators['ema_200'] = float(latest_ema200)
            
            # MACD
            if len(df) >= 26:
                from indicators.macd import calculate_macd
                macd_result = calculate_macd(df['close'])
                if macd_result and len(macd_result) == 3:
                    macd_line, signal_line, histogram = macd_result
                    if (macd_line is not None and len(macd_line) > 0 and
                        signal_line is not None and len(signal_line) > 0 and
                        histogram is not None and len(histogram) > 0):
                        
                        latest_macd = macd_line.iloc[-1]
                        latest_signal = signal_line.iloc[-1]
                        latest_histogram = histogram.iloc[-1]
                        
                        if pd.notna(latest_macd):
                            indicators['macd_line'] = float(latest_macd)
                            indicators['macd_signal'] = float(latest_signal) if pd.notna(latest_signal) else 0.0
                            indicators['macd_histogram'] = float(latest_histogram) if pd.notna(latest_histogram) else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating basic indicators for {ticker}: {e}")
        
        return indicators
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Calculate Bollinger Bands"""
        indicators = {}
        
        try:
            if len(df) >= 20:
                from indicators.bollinger_bands import calculate_bollinger_bands
                upper, middle, lower = calculate_bollinger_bands(df['close'], window=20)
                
                if upper is not None and len(upper) > 0:
                    latest_upper = upper.iloc[-1]
                    latest_middle = middle.iloc[-1]
                    latest_lower = lower.iloc[-1]
                    
                    if pd.notna(latest_upper):
                        indicators['bb_upper'] = float(latest_upper)
                        indicators['bb_middle'] = float(latest_middle) if pd.notna(latest_middle) else 0.0
                        indicators['bb_lower'] = float(latest_lower) if pd.notna(latest_lower) else 0.0
                        
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands for {ticker}: {e}")
        
        return indicators
    
    def _calculate_stochastic(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Calculate Stochastic Oscillator"""
        indicators = {}
        
        try:
            if len(df) >= 14:
                from indicators.stochastic import calculate_stochastic
                k_percent, d_percent = calculate_stochastic(df['high'], df['low'], df['close'])
                
                if k_percent is not None and len(k_percent) > 0:
                    latest_k = k_percent.iloc[-1]
                    latest_d = d_percent.iloc[-1]
                    
                    if pd.notna(latest_k):
                        indicators['stoch_k'] = float(latest_k)
                        indicators['stoch_d'] = float(latest_d) if pd.notna(latest_d) else 0.0
                        
        except Exception as e:
            logger.error(f"Error calculating Stochastic for {ticker}: {e}")
        
        return indicators
    
    def _calculate_support_resistance(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Calculate Support and Resistance levels (all enhanced indicators)"""
        indicators = {}
        
        # Define the support/resistance indicators that exist in the database
        valid_sr_indicators = {
            'pivot_point', 'pivot_fibonacci', 'pivot_camarilla', 'pivot_woodie', 'pivot_demark',
            'resistance_1', 'resistance_2', 'resistance_3',
            'support_1', 'support_2', 'support_3', 'swing_high_5d', 'swing_low_5d',
            'swing_high_10d', 'swing_low_10d', 'swing_high_20d', 'swing_low_20d',
            'week_high', 'week_low', 'month_high', 'month_low',
            'nearest_support', 'nearest_resistance', 'support_strength', 'resistance_strength',
            'volume_confirmation', 'swing_strengths', 'level_type',
            'fib_236', 'fib_382', 'fib_500', 'fib_618', 'fib_786',
            'fib_1272', 'fib_1618', 'fib_2618',
            'dynamic_resistance', 'dynamic_support',
            'keltner_upper', 'keltner_lower',
            'volume_weighted_high', 'volume_weighted_low',
            'nearest_fib_support', 'nearest_fib_resistance',
            'nearest_psych_support', 'nearest_psych_resistance',
            'nearest_volume_support', 'nearest_volume_resistance'
        }
        
        try:
            if len(df) >= 20:
                from indicators.support_resistance import calculate_support_resistance
                
                # Use enhanced calculation with volume if available
                if 'volume' in df.columns:
                    sr_result = calculate_support_resistance(
                        df['high'], df['low'], df['close'], 
                        volume=df['volume'], window=20, swing_window=5
                    )
                else:
                    sr_result = calculate_support_resistance(
                        df['high'], df['low'], df['close'], 
                        window=20, swing_window=5
                    )
                
                if sr_result:
                    # Get latest values for only the valid support/resistance indicators
                    for key, series in sr_result.items():
                        if key in valid_sr_indicators and series is not None and len(series) > 0:
                            latest_value = series.iloc[-1]
                            if pd.notna(latest_value) and latest_value != 0:
                                # Ensure the value is numeric
                                try:
                                    indicators[key] = float(latest_value)
                                except (ValueError, TypeError):
                                    # Skip non-numeric values
                                    continue
                                
        except Exception as e:
            logger.error(f"Error calculating Support/Resistance for {ticker}: {e}")
        
        return indicators
    
    def _calculate_additional_indicators(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Calculate additional indicators: CCI, ADX, ATR"""
        indicators = {}
        
        try:
            # CCI (Commodity Channel Index)
            if len(df) >= 20:
                from indicators.cci import calculate_cci
                cci_result = calculate_cci(df['high'], df['low'], df['close'])
                if cci_result is not None and len(cci_result) > 0:
                    latest_cci = cci_result.iloc[-1]
                    if pd.notna(latest_cci) and latest_cci != 0:
                        indicators['cci'] = float(latest_cci)
                        indicators['cci_20'] = float(latest_cci)  # Also store as cci_20
            
            # ADX (Average Directional Index)
            if len(df) >= 14:
                from indicators.adx import calculate_adx
                adx_result = calculate_adx(df['high'], df['low'], df['close'])
                if adx_result is not None and len(adx_result) > 0:
                    latest_adx = adx_result.iloc[-1]
                    if pd.notna(latest_adx) and latest_adx != 0:
                        indicators['adx_14'] = float(latest_adx)
            
            # ATR (Average True Range)
            if len(df) >= 14:
                from indicators.atr import calculate_atr
                atr_result = calculate_atr(df['high'], df['low'], df['close'])
                if atr_result is not None and len(atr_result) > 0:
                    latest_atr = atr_result.iloc[-1]
                    if pd.notna(latest_atr) and latest_atr != 0:
                        indicators['atr_14'] = float(latest_atr)
                        
        except Exception as e:
            logger.error(f"Error calculating additional indicators for {ticker}: {e}")
        
        return indicators
    
    def _calculate_volume_indicators(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Calculate volume-based indicators: VWAP, OBV, VPT"""
        indicators = {}
        
        try:
            # VWAP (Volume Weighted Average Price)
            if 'volume' in df.columns and len(df) >= 1:
                from indicators.vwap import calculate_vwap
                vwap_result = calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
                if vwap_result is not None and len(vwap_result) > 0:
                    latest_vwap = vwap_result.iloc[-1]
                    if pd.notna(latest_vwap) and latest_vwap != 0:
                        indicators['vwap'] = float(latest_vwap)
            
            # OBV (On-Balance Volume) - simple calculation
            if 'volume' in df.columns and len(df) >= 2:
                obv = self._calculate_obv(df['close'], df['volume'])
                if obv is not None and len(obv) > 0:
                    latest_obv = obv.iloc[-1]
                    if pd.notna(latest_obv):
                        indicators['obv'] = float(latest_obv)
            
            # VPT (Volume Price Trend)
            if 'volume' in df.columns and len(df) >= 2:
                vpt = self._calculate_vpt(df['close'], df['volume'])
                if vpt is not None and len(vpt) > 0:
                    latest_vpt = vpt.iloc[-1]
                    if pd.notna(latest_vpt):
                        indicators['vpt'] = float(latest_vpt)
                        
        except Exception as e:
            logger.error(f"Error calculating volume indicators for {ticker}: {e}")
        
        return indicators
    
    def _calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume"""
        try:
            obv = pd.Series(index=close.index, dtype=float)
            obv.iloc[0] = volume.iloc[0]
            
            for i in range(1, len(close)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]  # ✅ CORRECT: Add volume when price rises
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]  # ✅ CORRECT: Subtract volume when price falls
                else:
                    obv.iloc[i] = obv.iloc[i-1]  # No change when price is unchanged
            
            return obv
        except Exception:
            return None
    
    def _calculate_vpt(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Price Trend"""
        try:
            price_change = close.pct_change()
            vpt = (price_change * volume).cumsum()
            return vpt
        except Exception:
            return None

def test_comprehensive_calculations():
    """Test the comprehensive technical indicator calculations"""
    
    # Get database configuration from daily_run
    try:
        from config import Config
        config = Config.get_db_config()
    except ImportError:
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'dbname': os.getenv('DB_NAME', 'ourstox6'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    try:
        import psycopg2
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Get 5 tickers with 100+ days of data
        cursor.execute("""
            SELECT ticker, COUNT(*) as days_count
            FROM daily_charts 
            WHERE close IS NOT NULL AND close != 0
            GROUP BY ticker 
            HAVING COUNT(*) >= 100
            ORDER BY days_count DESC
            LIMIT 5
        """)
        test_tickers = cursor.fetchall()
        
        calculator = ComprehensiveTechnicalCalculator()
        
        print("🧪 TESTING COMPREHENSIVE TECHNICAL INDICATORS")
        print("=" * 60)
        
        for ticker, days in test_tickers:
            print(f"\nTesting {ticker} ({days} days)...")
            
            # Get price data
            cursor.execute("""
                SELECT date, open, high, low, close, volume
                FROM daily_charts 
                WHERE ticker = %s AND close IS NOT NULL AND close != 0
                ORDER BY date ASC
                LIMIT 100
            """, (ticker,))
            
            data = cursor.fetchall()
            price_data = []
            for row in data:
                price_data.append({
                    'date': row[0],
                    'open': row[1],
                    'high': row[2],
                    'low': row[3],
                    'close': row[4],
                    'volume': row[5]
                })
            
            # Calculate all indicators
            start_time = datetime.now()
            indicators = calculator.calculate_all_indicators(ticker, price_data)
            calculation_time = (datetime.now() - start_time).total_seconds()
            
            if indicators:
                print(f"✅ {ticker}: {len(indicators)} indicators calculated in {calculation_time:.2f}s")
                
                # Show some key indicators
                key_indicators = ['rsi_14', 'ema_20', 'macd_line', 'bb_upper', 'stoch_k', 'pivot_point']
                for indicator in key_indicators:
                    if indicator in indicators:
                        print(f"  {indicator}: {indicators[indicator]:.2f}")
            else:
                print(f"❌ {ticker}: Calculation failed")
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 SUMMARY:")
        print(f"Total indicators calculated: {calculator.indicators_calculated}")
        print(f"Total indicators failed: {calculator.indicators_failed}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_calculations() 