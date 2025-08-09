#!/usr/bin/env python3
"""
Technical Analysis Scoring System - Enhanced Version
Improved calculations for better differentiation and accuracy
"""

import os
import sys
import json
import logging
import time
import math
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add daily_run to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedTechnicalScoreCalculator:
    """
    Enhanced technical analysis scoring with improved calculations and differentiation
    """
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.db_connection = None
        self.calculation_batch_id = f"enhanced_tech_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def get_db_connection(self):
        """Get database connection"""
        if not self.db_connection or self.db_connection.closed:
            try:
                self.db_connection = psycopg2.connect(**self.db_config)
                self.db_connection.autocommit = True
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                return None
        return self.db_connection
    
    def clean_price_data(self, prices: List[float]) -> List[float]:
        """Clean price data by removing extreme outliers"""
        if len(prices) < 5:
            return prices
        
        # Calculate median and typical range
        sorted_prices = sorted(prices)
        median = sorted_prices[len(sorted_prices) // 2]
        
        # Remove prices that are more than 50% different from median
        # This should catch the scaling issues and extreme outliers
        cleaned = []
        for price in prices:
            if price > 0 and abs(price - median) / median < 0.5:
                cleaned.append(price)
            elif len(cleaned) > 0:
                # Replace outlier with last good price to maintain sequence
                cleaned.append(cleaned[-1])
        
        return cleaned if len(cleaned) >= len(prices) * 0.7 else prices  # Use original if too much data lost
    
    def calculate_enhanced_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Enhanced RSI calculation with better smoothing and validation
        """
        if len(prices) < period + 5:  # Need extra data for stability
            return 50.0  # Neutral default
        
        # Calculate price changes
        deltas = []
        for i in range(1, len(prices)):
            delta = prices[i] - prices[i-1]
            deltas.append(delta)
        
        if not deltas:
            return 50.0
        
        # Separate gains and losses
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]
        
        # Use Wilder's smoothing method (more stable)
        # Initial SMA for first calculation
        if len(gains) >= period:
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period
            
            # Apply Wilder's smoothing for subsequent values
            for i in range(period, len(gains)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        else:
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
        
        # Calculate RSI with better edge case handling
        if avg_loss == 0:
            return 90.0 if avg_gain > 0 else 50.0  # Not extreme 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Ensure RSI is within valid range and apply bounds
        rsi = max(5.0, min(95.0, rsi))  # Constrain to 5-95 for realism
        
        return rsi
    
    def calculate_enhanced_ema(self, prices: List[float], period: int) -> float:
        """
        Enhanced EMA calculation with better initialization
        """
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
        
        # Start with SMA for better initialization
        sma = sum(prices[:period]) / period
        ema = sma
        
        # Apply EMA formula with proper smoothing constant
        alpha = 2.0 / (period + 1)
        for i in range(period, len(prices)):
            ema = alpha * prices[i] + (1 - alpha) * ema
        
        return ema
    
    def calculate_enhanced_macd(self, prices: List[float]) -> Tuple[float, float, float]:
        """
        Enhanced MACD calculation with proper signal line
        """
        if len(prices) < 34:  # Need 26 + 9 - 1
            return 0.0, 0.0, 0.0
        
        # Calculate EMAs
        ema_12 = self.calculate_enhanced_ema(prices, 12)
        ema_26 = self.calculate_enhanced_ema(prices, 26)
        
        # MACD line
        macd_line = ema_12 - ema_26
        
        # For proper signal line, we need MACD history
        # Simplified but more accurate approach
        macd_values = []
        if len(prices) >= 34:
            # Calculate MACD for last 9 periods to get signal
            for i in range(26, len(prices)):
                ema12_i = self.calculate_enhanced_ema(prices[:i+1], 12)
                ema26_i = self.calculate_enhanced_ema(prices[:i+1], 26)
                macd_values.append(ema12_i - ema26_i)
            
            # Signal line is 9-period EMA of MACD
            if len(macd_values) >= 9:
                signal_line = self.calculate_enhanced_ema(macd_values, 9)
            else:
                signal_line = sum(macd_values) / len(macd_values)
        else:
            signal_line = macd_line * 0.8  # Fallback
        
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_enhanced_bollinger_bands(self, prices: List[float], period: int = 20, std_multiplier: float = 2.0) -> Tuple[float, float, float]:
        """
        Enhanced Bollinger Bands with adaptive standard deviation
        """
        if len(prices) < period:
            current_price = prices[-1] if prices else 0
            return current_price * 1.02, current_price, current_price * 0.98
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / len(recent_prices)
        
        # Calculate standard deviation with Bessel's correction
        variance = sum((price - sma) ** 2 for price in recent_prices) / (len(recent_prices) - 1)
        std_dev = math.sqrt(variance)
        
        # Adaptive standard deviation multiplier based on volatility
        volatility = std_dev / sma if sma > 0 else 0
        if volatility > 0.05:  # High volatility
            std_multiplier = 2.2
        elif volatility < 0.02:  # Low volatility
            std_multiplier = 1.8
        else:
            std_multiplier = 2.0
        
        upper_band = sma + (std_dev * std_multiplier)
        lower_band = sma - (std_dev * std_multiplier)
        
        return upper_band, sma, lower_band
    
    def calculate_enhanced_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """
        Enhanced ATR calculation with better smoothing
        """
        if len(highs) < period + 1:
            return 0.02  # Default 2% volatility
        
        true_ranges = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        if not true_ranges:
            return 0.02
        
        # Use Wilder's smoothing for ATR
        if len(true_ranges) >= period:
            atr = sum(true_ranges[:period]) / period
            for i in range(period, len(true_ranges)):
                atr = (atr * (period - 1) + true_ranges[i]) / period
        else:
            atr = sum(true_ranges) / len(true_ranges)
        
        return atr
    
    def calculate_enhanced_adx(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """
        Enhanced ADX calculation with proper DX smoothing
        """
        if len(highs) < period * 2:  # Need more data for proper ADX calculation
            return 25.0
        
        # Calculate True Range and Directional Movement
        tr_list = []
        plus_dm_list = []
        minus_dm_list = []
        
        for i in range(1, len(highs)):
            # True Range
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            tr = max(tr1, tr2, tr3)
            tr_list.append(tr)
            
            # Directional Movement
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            
            plus_dm = high_diff if high_diff > low_diff and high_diff > 0 else 0
            minus_dm = low_diff if low_diff > high_diff and low_diff > 0 else 0
            
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)
        
        if len(tr_list) < period:
            return 25.0
        
        # Calculate smoothed values and DX series
        dx_series = []
        
        # Initial smoothed values (simple average for first period)
        tr_smooth = sum(tr_list[:period]) / period
        plus_dm_smooth = sum(plus_dm_list[:period]) / period
        minus_dm_smooth = sum(minus_dm_list[:period]) / period
        
        # Calculate DX for each period
        for i in range(period - 1, len(tr_list)):
            if i >= period:
                # Wilder's smoothing: EMA with alpha = 1/period
                tr_smooth = (tr_smooth * (period - 1) + tr_list[i]) / period
                plus_dm_smooth = (plus_dm_smooth * (period - 1) + plus_dm_list[i]) / period
                minus_dm_smooth = (minus_dm_smooth * (period - 1) + minus_dm_list[i]) / period
            
            # Calculate DI+ and DI-
            plus_di = (plus_dm_smooth / tr_smooth) * 100 if tr_smooth > 0 else 0
            minus_di = (minus_dm_smooth / tr_smooth) * 100 if tr_smooth > 0 else 0
            
            # Calculate DX
            di_sum = plus_di + minus_di
            if di_sum > 0:
                dx = abs(plus_di - minus_di) / di_sum * 100
                dx_series.append(dx)
        
        if not dx_series:
            return 25.0
        
        # ADX is the smoothed average of DX values
        if len(dx_series) >= period:
            # Take the last 'period' DX values and smooth them
            recent_dx = dx_series[-period:]
            adx = sum(recent_dx) / len(recent_dx)
        else:
            # If not enough DX values, use what we have
            adx = sum(dx_series) / len(dx_series)
        
        return min(100.0, max(0.0, adx))
    
    def calculate_cci(self, highs: List[float], lows: List[float], closes: List[float], period: int = 20) -> float:
        """
        Calculate Commodity Channel Index (CCI)
        CCI = (Typical Price - SMA of Typical Price) / (0.015 * Mean Deviation)
        """
        if len(highs) < period or len(lows) < period or len(closes) < period:
            return 0.0
        
        # Calculate Typical Price for each period
        typical_prices = []
        for i in range(len(closes)):
            tp = (highs[i] + lows[i] + closes[i]) / 3
            typical_prices.append(tp)
        
        if len(typical_prices) < period:
            return 0.0
        
        # Calculate SMA of Typical Price for the period
        recent_tp = typical_prices[-period:]
        sma_tp = sum(recent_tp) / period
        
        # Calculate Mean Deviation
        mean_deviation = sum(abs(tp - sma_tp) for tp in recent_tp) / period
        
        # Calculate CCI
        if mean_deviation == 0:
            return 0.0
        
        current_tp = typical_prices[-1]
        cci = (current_tp - sma_tp) / (0.15 * mean_deviation)
        
        return cci
    
    def get_enhanced_technical_data(self, ticker: str) -> Optional[Dict]:
        """Get technical indicators data with enhanced calculations"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            
            # Get comprehensive historical data
            query = """
            SELECT 
                close, high, low, volume, date
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 100
            """
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (ticker,))
                results = cursor.fetchall()
                
                if results and len(results) >= 50:  # Need more data for enhanced calculations
                    # Convert to lists, handling None values and data corruption
                    prices = []
                    highs = []
                    lows = []
                    volumes = []
                    
                    for row in results:
                        if row['close'] is not None and row['high'] is not None and row['low'] is not None:
                            close_price = float(row['close'])
                            high_price = float(row['high'])
                            low_price = float(row['low'])
                            
                            # Fix mixed scaling issue - if price > 1000, divide by 100
                            if close_price > 1000:
                                close_price = close_price / 100
                                high_price = high_price / 100
                                low_price = low_price / 100
                            
                            prices.append(close_price)
                            highs.append(high_price)
                            lows.append(low_price)
                            
                            if row['volume'] is not None:
                                volumes.append(float(row['volume']))
                            else:
                                volumes.append(0)
                    
                    # Ensure we have valid data
                    if not prices or len(prices) < 30:
                        logger.warning(f"Insufficient valid price data for {ticker}")
                        return None
                    
                    # Reverse to get chronological order
                    prices.reverse()
                    highs.reverse()
                    lows.reverse()
                    volumes.reverse()
                    
                    # Clean data: remove extreme outliers that would corrupt RSI
                    cleaned_prices = self.clean_price_data(prices)
                    cleaned_highs = self.clean_price_data(highs)
                    cleaned_lows = self.clean_price_data(lows)
                    
                    if len(cleaned_prices) < 30:
                        logger.warning(f"Insufficient clean price data for {ticker}")
                        return None
                    
                    # Use cleaned data
                    prices = cleaned_prices
                    highs = cleaned_highs  
                    lows = cleaned_lows
                    
                    # Current values
                    current_price = prices[-1]
                    current_high = highs[-1]
                    current_low = lows[-1]
                    current_volume = volumes[-1]
                    
                    # Calculate enhanced technical indicators
                    rsi = self.calculate_enhanced_rsi(prices, 14)
                    
                    # Multiple EMAs for comprehensive trend analysis
                    ema_9 = self.calculate_enhanced_ema(prices, 9)
                    ema_20 = self.calculate_enhanced_ema(prices, 20)
                    ema_50 = self.calculate_enhanced_ema(prices, 50)
                    ema_200 = self.calculate_enhanced_ema(prices, 200) if len(prices) >= 200 else ema_50
                    
                    # Enhanced MACD
                    macd_line, macd_signal, macd_histogram = self.calculate_enhanced_macd(prices)
                    
                    # Enhanced Bollinger Bands
                    bb_upper, bb_middle, bb_lower = self.calculate_enhanced_bollinger_bands(prices, 20)
                    
                    # Enhanced ATR
                    atr = self.calculate_enhanced_atr(highs, lows, prices, 14)
                    
                    # Enhanced ADX
                    adx = self.calculate_enhanced_adx(highs, lows, prices, 14)
                    
                    # CCI (Commodity Channel Index)
                    cci = self.calculate_cci(highs, lows, prices, 20)
                    
                    # Stochastic Oscillator
                    stoch_k, stoch_d = self.calculate_stochastic(highs, lows, prices, 14)
                    
                    # Volume indicators
                    avg_volume_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else current_volume
                    volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0
                    
                    # Price performance metrics
                    price_change_1d = (prices[-1] - prices[-2]) / prices[-2] * 100 if len(prices) >= 2 else 0
                    price_change_5d = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) >= 6 else 0
                    price_change_20d = (prices[-1] - prices[-21]) / prices[-21] * 100 if len(prices) >= 21 else 0
                    
                    # Volatility metrics
                    price_volatility = (atr / current_price) * 100 if current_price > 0 else 2
                    
                    # Create comprehensive data dictionary
                    enhanced_data = {
                        'close': current_price,
                        'high': current_high,
                        'low': current_low,
                        'volume': current_volume,
                        
                        # Enhanced indicators
                        'rsi_14': rsi,
                        'ema_9': ema_9,
                        'ema_20': ema_20,
                        'ema_50': ema_50,
                        'ema_200': ema_200,
                        'macd_line': macd_line,
                        'macd_signal': macd_signal,
                        'macd_histogram': macd_histogram,
                        'bb_upper': bb_upper,
                        'bb_middle': bb_middle,
                        'bb_lower': bb_lower,
                        'atr_14': atr,
                        'stoch_k': stoch_k,
                        'stoch_d': stoch_d,
                        'adx_14': adx,
                        'cci_20': cci,
                        
                        # Volume metrics
                        'avg_volume_20': avg_volume_20,
                        'volume_ratio': volume_ratio,
                        
                        # Performance metrics
                        'price_change_1d': price_change_1d,
                        'price_change_5d': price_change_5d,
                        'price_change_20d': price_change_20d,
                        'price_volatility': price_volatility,
                        
                        # Historical data for component calculations
                        'price_history': prices[-30:],  # Last 30 prices
                        'volume_history': volumes[-30:],  # Last 30 volumes
                        'high_history': highs[-30:],  # Last 30 highs
                        'low_history': lows[-30:]  # Last 30 lows
                    }
                    
                    return enhanced_data
                else:
                    logger.warning(f"Insufficient technical data found for {ticker}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting enhanced technical data for {ticker}: {e}")
            return None
    
    def calculate_stochastic(self, highs: List[float], lows: List[float], prices: List[float], k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
        """
        Enhanced Stochastic Oscillator calculation
        """
        if len(prices) < k_period:
            return 50.0, 50.0
        
        # Calculate %K
        recent_high = max(highs[-k_period:])
        recent_low = min(lows[-k_period:])
        current_price = prices[-1]
        
        if recent_high == recent_low:
            stoch_k = 50.0
        else:
            stoch_k = ((current_price - recent_low) / (recent_high - recent_low)) * 100
        
        # Calculate %D as SMA of %K
        # For simplicity, using current %K, but in full implementation would use %K history
        stoch_d = stoch_k  # Simplified
        
        return max(0.0, min(100.0, stoch_k)), max(0.0, min(100.0, stoch_d))
    
    def calculate_enhanced_trend_strength(self, data: Dict) -> Tuple[float, Dict]:
        """Enhanced trend strength calculation with better differentiation"""
        try:
            current_price = data.get('close', 0)
            ema_9 = data.get('ema_9', current_price)
            ema_20 = data.get('ema_20', current_price)
            ema_50 = data.get('ema_50', current_price)
            ema_200 = data.get('ema_200', current_price)
            adx = data.get('adx_14', 25)
            macd_line = data.get('macd_line', 0)
            macd_signal = data.get('macd_signal', 0)
            price_change_5d = data.get('price_change_5d', 0)
            price_change_20d = data.get('price_change_20d', 0)
            
            # EMA Alignment Score (0-100) - More sophisticated
            ema_alignment = 50
            if ema_9 > ema_20 > ema_50 > ema_200:
                ema_alignment = 100  # Perfect bullish alignment
            elif ema_9 > ema_20 > ema_50:
                ema_alignment = 85   # Strong bullish
            elif ema_9 > ema_20:
                ema_alignment = 70   # Moderate bullish
            elif current_price > ema_20:
                ema_alignment = 60   # Weak bullish
            elif current_price < ema_20 and ema_20 < ema_50:
                ema_alignment = 30   # Weak bearish
            elif ema_9 < ema_20 < ema_50:
                ema_alignment = 15   # Moderate bearish
            elif ema_9 < ema_20 < ema_50 < ema_200:
                ema_alignment = 0    # Perfect bearish alignment
            else:
                ema_alignment = 50   # Sideways
            
            # Price Position Score (0-100) - Enhanced
            price_position = 50
            price_vs_ema20 = (current_price - ema_20) / ema_20 * 100 if ema_20 > 0 else 0
            
            if price_vs_ema20 > 10:
                price_position = 95   # Well above EMA20
            elif price_vs_ema20 > 5:
                price_position = 85   # Above EMA20
            elif price_vs_ema20 > 2:
                price_position = 75   # Slightly above EMA20
            elif price_vs_ema20 > 0:
                price_position = 65   # Just above EMA20
            elif price_vs_ema20 > -2:
                price_position = 35   # Just below EMA20
            elif price_vs_ema20 > -5:
                price_position = 25   # Below EMA20
            elif price_vs_ema20 > -10:
                price_position = 15   # Well below EMA20
            else:
                price_position = 5    # Far below EMA20
            
            # ADX Trend Strength (0-100) - Enhanced interpretation
            adx_score = 50
            if adx > 50:
                adx_score = 95   # Very strong trend
            elif adx > 40:
                adx_score = 85   # Strong trend
            elif adx > 30:
                adx_score = 75   # Moderate trend
            elif adx > 25:
                adx_score = 65   # Weak trend
            elif adx > 20:
                adx_score = 55   # Very weak trend
            else:
                adx_score = 40   # No clear trend
            
            # MACD Momentum (0-100) - Enhanced
            macd_score = 50
            if macd_line > 0 and macd_signal > 0 and macd_line > macd_signal:
                macd_score = 95   # Strong bullish momentum
            elif macd_line > macd_signal and macd_line > 0:
                macd_score = 85   # Bullish momentum
            elif macd_line > macd_signal:
                macd_score = 70   # Improving momentum
            elif macd_line == macd_signal:
                macd_score = 50   # Neutral momentum
            elif macd_line < macd_signal and macd_line < 0:
                macd_score = 30   # Declining momentum
            elif macd_line < 0 and macd_signal < 0 and macd_line < macd_signal:
                macd_score = 15   # Bearish momentum
            else:
                macd_score = 5    # Strong bearish momentum
            
            # Price Performance Score (0-100) - New enhanced component
            performance_score = 50
            if price_change_20d > 20:
                performance_score = 95   # Excellent 20-day performance
            elif price_change_20d > 10:
                performance_score = 85   # Strong performance
            elif price_change_20d > 5:
                performance_score = 75   # Good performance
            elif price_change_20d > 0:
                performance_score = 65   # Positive performance
            elif price_change_20d > -5:
                performance_score = 35   # Slight decline
            elif price_change_20d > -10:
                performance_score = 25   # Moderate decline
            elif price_change_20d > -20:
                performance_score = 15   # Poor performance
            else:
                performance_score = 5    # Very poor performance
            
            # Calculate weighted trend strength
            trend_strength = (
                ema_alignment * 0.25 +
                price_position * 0.25 +
                adx_score * 0.20 +
                macd_score * 0.15 +
                performance_score * 0.15
            )
            
            components = {
                'ema_alignment': round(ema_alignment, 1),
                'price_position': round(price_position, 1),
                'adx_strength': round(adx_score, 1),
                'macd_momentum': round(macd_score, 1),
                'performance': round(performance_score, 1)
            }
            
            return trend_strength, components
            
        except Exception as e:
            logger.error(f"Error calculating enhanced trend strength: {e}")
            return 50.0, {}
    
    def calculate_enhanced_momentum(self, data: Dict) -> Tuple[float, Dict]:
        """Enhanced momentum calculation with better RSI interpretation"""
        try:
            rsi = data.get('rsi_14', 50)
            stoch_k = data.get('stoch_k', 50)
            stoch_d = data.get('stoch_d', 50)
            price_change_1d = data.get('price_change_1d', 0)
            price_change_5d = data.get('price_change_5d', 0)
            macd_histogram = data.get('macd_histogram', 0)
            
            # Enhanced RSI Score (0-100) - More realistic interpretation
            rsi_score = 50
            if rsi >= 70:
                rsi_score = 20   # Overbought (potential reversal)
            elif rsi >= 60:
                rsi_score = 60   # Strong bullish
            elif rsi >= 55:
                rsi_score = 80   # Bullish
            elif rsi >= 50:
                rsi_score = 90   # Moderately bullish
            elif rsi >= 45:
                rsi_score = 70   # Neutral-bullish
            elif rsi >= 40:
                rsi_score = 60   # Neutral
            elif rsi >= 35:
                rsi_score = 50   # Neutral-bearish
            elif rsi >= 30:
                rsi_score = 40   # Bearish
            elif rsi >= 20:
                rsi_score = 60   # Oversold (potential bounce)
            else:
                rsi_score = 80   # Very oversold (strong bounce potential)
            
            # Stochastic Score (0-100) - Enhanced
            stoch_score = 50
            if stoch_k > 80 and stoch_d > 80:
                stoch_score = 25   # Overbought
            elif stoch_k > 60:
                stoch_score = 75   # Bullish zone
            elif stoch_k > 40:
                stoch_score = 85   # Neutral-bullish
            elif stoch_k > 20:
                stoch_score = 75   # Neutral-bearish
            else:
                stoch_score = 25   # Oversold
            
            # Short-term Price Momentum (0-100)
            short_momentum = 50
            if price_change_1d > 3:
                short_momentum = 95   # Strong daily gain
            elif price_change_1d > 1:
                short_momentum = 80   # Good daily gain
            elif price_change_1d > 0:
                short_momentum = 65   # Positive day
            elif price_change_1d > -1:
                short_momentum = 35   # Slight decline
            elif price_change_1d > -3:
                short_momentum = 20   # Moderate decline
            else:
                short_momentum = 5    # Strong decline
            
            # Medium-term Price Momentum (0-100)
            medium_momentum = 50
            if price_change_5d > 5:
                medium_momentum = 95   # Strong 5-day gain
            elif price_change_5d > 2:
                medium_momentum = 80   # Good 5-day gain
            elif price_change_5d > 0:
                medium_momentum = 65   # Positive 5-day
            elif price_change_5d > -2:
                medium_momentum = 35   # Slight 5-day decline
            elif price_change_5d > -5:
                medium_momentum = 20   # Moderate 5-day decline
            else:
                medium_momentum = 5    # Strong 5-day decline
            
            # MACD Histogram Momentum (0-100)
            macd_momentum = 50
            if macd_histogram > 0.1:
                macd_momentum = 85   # Strong positive momentum
            elif macd_histogram > 0:
                macd_momentum = 70   # Positive momentum
            elif macd_histogram > -0.1:
                macd_momentum = 30   # Weak negative momentum
            else:
                macd_momentum = 15   # Strong negative momentum
            
            # Calculate weighted momentum
            momentum = (
                rsi_score * 0.30 +
                stoch_score * 0.20 +
                short_momentum * 0.20 +
                medium_momentum * 0.20 +
                macd_momentum * 0.10
            )
            
            components = {
                'rsi': round(rsi_score, 1),
                'stochastic': round(stoch_score, 1),
                'short_momentum': round(short_momentum, 1),
                'medium_momentum': round(medium_momentum, 1),
                'macd_histogram': round(macd_momentum, 1)
            }
            
            return momentum, components
            
        except Exception as e:
            logger.error(f"Error calculating enhanced momentum: {e}")
            return 50.0, {}
    
    def calculate_enhanced_support_resistance(self, data: Dict) -> Tuple[float, Dict]:
        """Enhanced support/resistance calculation with proper differentiation"""
        try:
            current_price = data.get('close', 0)
            bb_upper = data.get('bb_upper', 0)
            bb_middle = data.get('bb_middle', 0)
            bb_lower = data.get('bb_lower', 0)
            atr = data.get('atr_14', 0)
            price_volatility = data.get('price_volatility', 2)
            high_history = data.get('high_history', [])
            low_history = data.get('low_history', [])
            price_history = data.get('price_history', [])
            
            # Bollinger Band Position (0-100) - Enhanced with better differentiation
            bb_position_score = 50
            if bb_upper > bb_lower and bb_upper > 0 and bb_lower > 0:
                bb_range = bb_upper - bb_lower
                if bb_range > 0:
                    position = (current_price - bb_lower) / bb_range
                    
                    if position > 0.95:
                        bb_position_score = 10   # Very close to upper band (resistance)
                    elif position > 0.85:
                        bb_position_score = 25   # Near upper band
                    elif position > 0.70:
                        bb_position_score = 45   # Upper portion
                    elif position > 0.55:
                        bb_position_score = 70   # Upper middle
                    elif position > 0.45:
                        bb_position_score = 85   # Center (ideal)
                    elif position > 0.30:
                        bb_position_score = 70   # Lower middle
                    elif position > 0.15:
                        bb_position_score = 45   # Lower portion
                    elif position > 0.05:
                        bb_position_score = 25   # Near lower band
                    else:
                        bb_position_score = 10   # Very close to lower band (support)
            
            # Volatility-based Support/Resistance Strength (0-100)
            volatility_score = 50
            if price_volatility < 1:
                volatility_score = 95   # Very low volatility = strong S/R
            elif price_volatility < 2:
                volatility_score = 85   # Low volatility = good S/R
            elif price_volatility < 3:
                volatility_score = 70   # Moderate volatility
            elif price_volatility < 5:
                volatility_score = 50   # Normal volatility
            elif price_volatility < 8:
                volatility_score = 30   # High volatility = weak S/R
            else:
                volatility_score = 15   # Very high volatility = very weak S/R
            
            # Price Range Analysis (0-100) - Enhanced with actual price data
            range_score = 50
            if len(price_history) >= 20:
                recent_high = max(price_history[-20:])
                recent_low = min(price_history[-20:])
                range_size = (recent_high - recent_low) / recent_low * 100 if recent_low > 0 else 10
                
                current_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
                
                if range_size < 5:
                    range_score = 90   # Very tight range
                elif range_size < 10:
                    range_score = 80   # Tight range
                elif range_size < 15:
                    range_score = 70   # Normal range
                elif range_size < 25:
                    range_score = 60   # Wide range
                else:
                    range_score = 40   # Very wide range
                
                # Adjust based on position in range
                if current_position > 0.8 or current_position < 0.2:
                    range_score *= 0.8  # Penalize extreme positions
            
            # Support/Resistance Level Quality (0-100) - New component
            sr_quality = 50
            if len(high_history) >= 10 and len(low_history) >= 10:
                # Count how many times price approached but didn't break key levels
                resistance_touches = 0
                support_touches = 0
                
                recent_high = max(high_history[-10:])
                recent_low = min(low_history[-10:])
                
                tolerance = (recent_high - recent_low) * 0.02  # 2% tolerance
                
                for i, (high, low) in enumerate(zip(high_history[-10:], low_history[-10:])):
                    if abs(high - recent_high) < tolerance:
                        resistance_touches += 1
                    if abs(low - recent_low) < tolerance:
                        support_touches += 1
                
                # More touches = stronger S/R levels
                total_touches = resistance_touches + support_touches
                if total_touches >= 4:
                    sr_quality = 90
                elif total_touches >= 3:
                    sr_quality = 80
                elif total_touches >= 2:
                    sr_quality = 70
                elif total_touches >= 1:
                    sr_quality = 60
                else:
                    sr_quality = 40
            
            # Calculate weighted support/resistance score
            support_resistance = (
                bb_position_score * 0.30 +
                volatility_score * 0.25 +
                range_score * 0.25 +
                sr_quality * 0.20
            )
            
            components = {
                'bb_position': round(bb_position_score, 1),
                'volatility': round(volatility_score, 1),
                'price_range': round(range_score, 1),
                'sr_quality': round(sr_quality, 1)
            }
            
            return support_resistance, components
            
        except Exception as e:
            logger.error(f"Error calculating enhanced support/resistance: {e}")
            return 50.0, {}
    
    def calculate_enhanced_volume(self, data: Dict) -> Tuple[float, Dict]:
        """Enhanced volume analysis with better metrics"""
        try:
            current_volume = data.get('volume', 0)
            avg_volume_20 = data.get('avg_volume_20', current_volume)
            volume_ratio = data.get('volume_ratio', 1.0)
            volume_history = data.get('volume_history', [])
            price_history = data.get('price_history', [])
            price_change_1d = data.get('price_change_1d', 0)
            
            # Volume vs Average (0-100) - Enhanced
            volume_vs_avg = 50
            if volume_ratio > 3.0:
                volume_vs_avg = 95   # Exceptional volume
            elif volume_ratio > 2.0:
                volume_vs_avg = 85   # Very high volume
            elif volume_ratio > 1.5:
                volume_vs_avg = 75   # High volume
            elif volume_ratio > 1.2:
                volume_vs_avg = 65   # Above average
            elif volume_ratio > 0.8:
                volume_vs_avg = 55   # Normal volume
            elif volume_ratio > 0.5:
                volume_vs_avg = 35   # Below average
            elif volume_ratio > 0.3:
                volume_vs_avg = 25   # Low volume
            else:
                volume_vs_avg = 15   # Very low volume
            
            # Volume Trend (0-100) - Enhanced
            volume_trend = 50
            if len(volume_history) >= 5:
                recent_volumes = volume_history[-5:]
                volume_changes = []
                for i in range(1, len(recent_volumes)):
                    if recent_volumes[i-1] > 0:
                        change = (recent_volumes[i] - recent_volumes[i-1]) / recent_volumes[i-1]
                        volume_changes.append(change)
                
                if volume_changes:
                    avg_volume_change = sum(volume_changes) / len(volume_changes)
                    if avg_volume_change > 0.2:
                        volume_trend = 90   # Strong increasing trend
                    elif avg_volume_change > 0.1:
                        volume_trend = 75   # Moderate increasing trend
                    elif avg_volume_change > 0:
                        volume_trend = 60   # Slight increasing trend
                    elif avg_volume_change > -0.1:
                        volume_trend = 40   # Slight decreasing trend
                    elif avg_volume_change > -0.2:
                        volume_trend = 25   # Moderate decreasing trend
                    else:
                        volume_trend = 10   # Strong decreasing trend
            
            # Price-Volume Relationship (0-100) - Enhanced
            price_volume_relationship = 50
            if price_change_1d > 0 and volume_ratio > 1.2:
                price_volume_relationship = 90   # Price up with high volume (bullish)
            elif price_change_1d > 0 and volume_ratio > 0.8:
                price_volume_relationship = 70   # Price up with normal volume
            elif price_change_1d > 0:
                price_volume_relationship = 50   # Price up with low volume (weak)
            elif price_change_1d < 0 and volume_ratio > 1.2:
                price_volume_relationship = 20   # Price down with high volume (bearish)
            elif price_change_1d < 0 and volume_ratio > 0.8:
                price_volume_relationship = 40   # Price down with normal volume
            else:
                price_volume_relationship = 60   # Price down with low volume (not too bad)
            
            # Volume Distribution (0-100) - New component
            volume_distribution = 50
            if len(volume_history) >= 20:
                sorted_volumes = sorted(volume_history[-20:])
                median_volume = sorted_volumes[len(sorted_volumes)//2]
                
                # Check where current volume falls in distribution
                percentile = sum(1 for v in sorted_volumes if v <= current_volume) / len(sorted_volumes)
                
                if percentile >= 0.9:
                    volume_distribution = 95   # Top 10% volume
                elif percentile >= 0.8:
                    volume_distribution = 85   # Top 20% volume
                elif percentile >= 0.6:
                    volume_distribution = 70   # Above median
                elif percentile >= 0.4:
                    volume_distribution = 60   # Around median
                elif percentile >= 0.2:
                    volume_distribution = 40   # Below median
                else:
                    volume_distribution = 25   # Bottom 20% volume
            
            # Calculate weighted volume score
            volume_score = (
                volume_vs_avg * 0.30 +
                volume_trend * 0.25 +
                price_volume_relationship * 0.25 +
                volume_distribution * 0.20
            )
            
            components = {
                'volume_vs_avg': round(volume_vs_avg, 1),
                'volume_trend': round(volume_trend, 1),
                'price_volume_rel': round(price_volume_relationship, 1),
                'volume_distribution': round(volume_distribution, 1)
            }
            
            return volume_score, components
            
        except Exception as e:
            logger.error(f"Error calculating enhanced volume: {e}")
            return 50.0, {}
    
    def normalize_enhanced_score(self, score: float, score_type: str = 'default') -> Tuple[str, str, float]:
        """Enhanced score normalization with adjusted thresholds"""
        # Adjusted thresholds for better distribution
        if score_type == 'technical_health':
            if score >= 75:
                normalized = 5.0  # Strong Buy
                grade = 'Strong Buy'
                level = 'Excellent'
            elif score >= 65:
                normalized = 4.0  # Buy
                grade = 'Buy'
                level = 'Good'
            elif score >= 45:
                normalized = 3.0  # Neutral
                grade = 'Neutral'
                level = 'Average'
            elif score >= 30:
                normalized = 2.0  # Sell
                grade = 'Sell'
                level = 'Poor'
            else:
                normalized = 1.0  # Strong Sell
                grade = 'Strong Sell'
                level = 'Very Poor'
        elif score_type == 'trading_signal':
            if score >= 70:
                normalized = 5.0  # Strong Buy
                grade = 'Strong Buy'
                level = 'Excellent'
            elif score >= 60:
                normalized = 4.0  # Buy
                grade = 'Buy'
                level = 'Good'
            elif score >= 40:
                normalized = 3.0  # Neutral
                grade = 'Neutral'
                level = 'Average'
            elif score >= 25:
                normalized = 2.0  # Sell
                grade = 'Sell'
                level = 'Poor'
            else:
                normalized = 1.0  # Strong Sell
                grade = 'Strong Sell'
                level = 'Very Poor'
        else:  # default
            if score >= 80:
                normalized = 5.0
                grade = 'Strong Buy'
                level = 'Excellent'
            elif score >= 65:
                normalized = 4.0
                grade = 'Buy'
                level = 'Good'
            elif score >= 40:
                normalized = 3.0
                grade = 'Neutral'
                level = 'Average'
            elif score >= 20:
                normalized = 2.0
                grade = 'Sell'
                level = 'Poor'
            else:
                normalized = 1.0
                grade = 'Strong Sell'
                level = 'Very Poor'
        
        return grade, level, normalized
    
    def calculate_enhanced_technical_scores(self, ticker: str) -> Dict[str, Any]:
        """Calculate enhanced technical scores with improved algorithms"""
        logger.info(f"Calculating enhanced technical scores for {ticker}")
        
        # Get enhanced technical data
        data = self.get_enhanced_technical_data(ticker)
        if not data:
            logger.warning(f"No enhanced technical data available for {ticker}")
            return {}
        
        try:
            # Calculate enhanced components
            trend_strength, trend_components = self.calculate_enhanced_trend_strength(data)
            momentum, momentum_components = self.calculate_enhanced_momentum(data)
            support_resistance, sr_components = self.calculate_enhanced_support_resistance(data)
            volume_score, volume_components = self.calculate_enhanced_volume(data)
            
            # Calculate Enhanced Technical Health Score
            technical_health_score = (
                trend_strength * 0.35 +
                momentum * 0.30 +
                support_resistance * 0.20 +
                volume_score * 0.15
            )
            
            # Calculate Enhanced Trading Signal Score
            trading_signal_score = (
                trend_strength * 0.40 +
                momentum * 0.25 +
                support_resistance * 0.20 +
                volume_score * 0.15
            )
            
            # Apply minimal context adjustment (reduced for better differentiation)
            price_adjustment = 0
            current_price = data.get('close', 0)
            if current_price > 500:
                price_adjustment = 0.5
            elif current_price > 200:
                price_adjustment = 0.25
            
            technical_health_score = min(100, technical_health_score + price_adjustment)
            trading_signal_score = min(100, trading_signal_score + price_adjustment)
            
            # Calculate Technical Risk Score
            technical_risk_score = max(0, 100 - technical_health_score)
            
            # Normalize scores
            health_grade, health_level, health_normalized = self.normalize_enhanced_score(technical_health_score, 'technical_health')
            signal_grade, signal_level, signal_normalized = self.normalize_enhanced_score(trading_signal_score, 'trading_signal')
            risk_grade, risk_level, risk_normalized = self.normalize_enhanced_score(technical_risk_score)
            
            # Compile enhanced results
            score_data = {
                'ticker': ticker,
                'calculation_date': datetime.now().isoformat(),
                'batch_id': self.calculation_batch_id,
                
                # Main scores
                'technical_health_score': round(technical_health_score, 2),
                'technical_health_grade': health_grade,
                'technical_health_level': health_level,
                'technical_health_normalized': health_normalized,
                
                'trading_signal_score': round(trading_signal_score, 2),
                'trading_signal_grade': signal_grade,
                'trading_signal_level': signal_level,
                'trading_signal_normalized': signal_normalized,
                
                'technical_risk_score': round(technical_risk_score, 2),
                'technical_risk_grade': risk_grade,
                'technical_risk_level': risk_level,
                'technical_risk_normalized': risk_normalized,
                
                # Component scores
                'trend_strength': round(trend_strength, 2),
                'momentum': round(momentum, 2),
                'support_resistance': round(support_resistance, 2),
                'volume_score': round(volume_score, 2),
                
                # Component details
                'trend_components': trend_components,
                'momentum_components': momentum_components,
                'sr_components': sr_components,
                'volume_components': volume_components,
                
                # Enhanced technical data
                'technical_data': {
                    'current_price': data.get('close', 0),
                    'current_volume': data.get('volume', 0),
                    'rsi_14': round(data.get('rsi_14', 0), 2),
                    'adx_14': round(data.get('adx_14', 0), 2),
                    'atr_14': round(data.get('atr_14', 0), 4),
                    'cci_20': round(data.get('cci_20', 0), 2),
                    'ema_20': round(data.get('ema_20', 0), 2),
                    'macd_line': round(data.get('macd_line', 0), 4),
                    'bb_position': round(((data.get('close', 0) - data.get('bb_lower', 0)) / (data.get('bb_upper', 0) - data.get('bb_lower', 0))) * 100 if data.get('bb_upper', 0) != data.get('bb_lower', 0) and data.get('bb_upper', 0) > 0 else 50, 1),
                    'volume_ratio': round(data.get('volume_ratio', 1.0), 2),
                    'price_change_5d': round(data.get('price_change_5d', 0), 2),
                    'price_volatility': round(data.get('price_volatility', 0), 2)
                }
            }
            
            logger.info(f"Calculated enhanced technical scores for {ticker}: Health={technical_health_score:.1f}, Signal={trading_signal_score:.1f}")
            return score_data
            
        except Exception as e:
            logger.error(f"Error calculating enhanced technical scores for {ticker}: {e}")
            return {}
