#!/usr/bin/env python3
"""
Technical Analysis Scoring System
Calculates technical scores based on 43 technical indicators and stores in database
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

class TechnicalScoreCalculator:
    """
    Calculates technical analysis scores based on 43 technical indicators
    """
    
    def __init__(self):
        self.db_connection = None
        self.calculation_batch_id = f"tech_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def get_database_connection(self):
        """Get database connection"""
        if not self.db_connection or self.db_connection.closed:
            try:
                self.db_connection = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', '5432'),
                    database=os.getenv('DB_NAME', 'ourstox6'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD'),
                    cursor_factory=RealDictCursor
                )
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
        return self.db_connection
    
    def get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """
        Get technical indicators from daily_charts table
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                    SELECT 
                        rsi_14, ema_20, ema_50, ema_100, ema_200,
                        macd_line, macd_signal, macd_histogram,
                        bb_upper, bb_middle, bb_lower,
                        stoch_k, stoch_d,
                        cci_20, atr_14, vwap,
                        obv, vpt,
                        pivot_point, resistance_1, resistance_2, resistance_3,
                        support_1, support_2, support_3,
                        swing_high_5d, swing_low_5d, swing_high_10d, swing_low_10d,
                        swing_high_20d, swing_low_20d,
                        week_high, week_low, month_high, month_low,
                        nearest_support, nearest_resistance,
                        support_strength, resistance_strength,
                        adx_14,
                        close, volume
                    FROM daily_charts 
                    WHERE ticker = %s 
                    ORDER BY date DESC 
                    LIMIT 1
                    """
                    cursor.execute(query, (ticker,))
                    result = cursor.fetchone()
                    
                    if result:
                        return dict(result)
                    else:
                        logger.warning(f"No technical data found for {ticker}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting technical indicators for {ticker}: {e}")
            return {}
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for ticker"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT close FROM daily_charts WHERE ticker = %s ORDER BY date DESC LIMIT 1"
                    cursor.execute(query, (ticker,))
                    result = cursor.fetchone()
                    return result['close'] if result else None
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return None
    
    def calculate_trend_strength_component(self, indicators: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Trend Strength Component (0-100)
        Components: EMA Alignment (30%), Price vs EMAs (25%), ADX (25%), MACD (20%)
        """
        components = {}
        
        # EMA Alignment (30% weight) - More granular scoring
        ema_20 = indicators.get('ema_20', None)
        ema_50 = indicators.get('ema_50', None)
        ema_200 = indicators.get('ema_200', None)
        
        if all(x is not None for x in [ema_20, ema_50, ema_200]) and all(x > 0 for x in [ema_20, ema_50, ema_200]):
            # Check if EMAs are aligned (bullish: 20 > 50 > 200)
            if ema_20 > ema_50 > ema_200:
                ema_alignment_score = 100  # Perfect bullish alignment
            elif ema_20 > ema_50 and ema_50 > ema_200 * 0.98:  # Strong bullish
                ema_alignment_score = 90
            elif ema_20 > ema_50 and ema_50 > ema_200 * 0.95:  # Moderate bullish
                ema_alignment_score = 75
            elif ema_20 > ema_50:  # Weak bullish
                ema_alignment_score = 60
            elif ema_20 < ema_50 < ema_200:
                ema_alignment_score = 0  # Perfect bearish alignment
            elif ema_20 < ema_50 and ema_50 < ema_200 * 1.02:  # Strong bearish
                ema_alignment_score = 10
            elif ema_20 < ema_50 and ema_50 < ema_200 * 1.05:  # Moderate bearish
                ema_alignment_score = 25
            elif ema_20 < ema_50:  # Weak bearish
                ema_alignment_score = 40
            else:  # Mixed signals
                ema_alignment_score = 50
        else:
            ema_alignment_score = 50
        
        components['ema_alignment'] = ema_alignment_score
        
        # Price vs EMAs (25% weight) - More nuanced
        current_price = indicators.get('close', None)
        if current_price is not None and ema_20 is not None and ema_50 is not None and ema_200 is not None:
            if current_price > 0 and ema_20 > 0 and ema_50 > 0 and ema_200 > 0:
                price_vs_ema20 = (current_price / ema_20 - 1) * 100
                price_vs_ema50 = (current_price / ema_50 - 1) * 100
                price_vs_ema200 = (current_price / ema_200 - 1) * 100
                
                # Calculate average position relative to EMAs
                avg_position = (price_vs_ema20 + price_vs_ema50 + price_vs_ema200) / 3
                
                if avg_position > 5:  # Strongly above EMAs
                    price_vs_emas_score = 100
                elif avg_position > 2:  # Above EMAs
                    price_vs_emas_score = 85
                elif avg_position > 0:  # Slightly above EMAs
                    price_vs_emas_score = 70
                elif avg_position > -2:  # Near EMAs
                    price_vs_emas_score = 50
                elif avg_position > -5:  # Below EMAs
                    price_vs_emas_score = 30
                elif avg_position > -10:  # Well below EMAs
                    price_vs_emas_score = 15
                else:  # Far below EMAs
                    price_vs_emas_score = 0
            else:
                price_vs_emas_score = 50
        else:
            price_vs_emas_score = 50
        
        components['price_vs_emas'] = price_vs_emas_score
        
        # ADX (25% weight) - More granular scoring
        adx = indicators.get('adx_14', None)
        if adx is not None and adx > 0:
            # Scale down ADX (divide by ~100)
            adx_scaled = adx / 100
            if adx_scaled > 40:  # Very strong trend
                adx_score = 100
            elif adx_scaled > 30:  # Strong trend
                adx_score = 85
            elif adx_scaled > 25:  # Moderate trend
                adx_score = 70
            elif adx_scaled > 20:  # Weak trend
                adx_score = 55
            elif adx_scaled > 15:  # Very weak trend
                adx_score = 40
            elif adx_scaled > 10:  # No trend
                adx_score = 25
            else:  # Choppy market
                adx_score = 10
        else:
            adx_score = 50
        
        components['adx'] = adx_score
        
        # MACD (20% weight) - More nuanced
        macd_line = indicators.get('macd_line', None)
        macd_signal = indicators.get('macd_signal', None)
        macd_histogram = indicators.get('macd_histogram', None)
        
        if all(x is not None for x in [macd_line, macd_signal, macd_histogram]):
            # Check MACD line vs signal
            if macd_line > macd_signal:
                macd_trend = 1  # Bullish
            else:
                macd_trend = -1  # Bearish
            
            # Check histogram strength
            hist_abs = abs(macd_histogram)
            if hist_abs > 3000:  # Very strong
                hist_strength = 100
            elif hist_abs > 1500:  # Strong
                hist_strength = 80
            elif hist_abs > 500:  # Moderate
                hist_strength = 60
            elif hist_abs > 100:  # Weak
                hist_strength = 40
            else:  # Very weak
                hist_strength = 20
            
            # Combine trend and strength
            if macd_trend > 0:  # Bullish
                macd_score = hist_strength
            else:  # Bearish
                macd_score = 100 - hist_strength
        else:
            macd_score = 50
        
        components['macd'] = macd_score
        
        # Calculate weighted average
        trend_strength = (
            ema_alignment_score * 0.30 +
            price_vs_emas_score * 0.25 +
            adx_score * 0.25 +
            macd_score * 0.20
        )
        
        return trend_strength, components
    
    def calculate_momentum_component(self, indicators: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Momentum Component (0-100)
        Components: RSI Momentum (30%), Stochastic Momentum (25%), CCI Momentum (25%), MACD Histogram (20%)
        """
        components = {}
        
        # RSI Momentum (30% weight) - Handle scaled data
        rsi = indicators.get('rsi_14', None)
        if rsi is not None and rsi > 0:
            # Scale down RSI to normal range (divide by ~10)
            rsi_scaled = rsi / 10
            if 45 <= rsi_scaled <= 55:  # Neutral zone
                rsi_score = 100
            elif 40 <= rsi_scaled <= 45 or 55 <= rsi_scaled <= 60:  # Good momentum
                rsi_score = 85
            elif 35 <= rsi_scaled <= 40 or 60 <= rsi_scaled <= 65:  # Moderate momentum
                rsi_score = 70
            elif 30 <= rsi_scaled <= 35 or 65 <= rsi_scaled <= 70:  # Weak momentum
                rsi_score = 55
            elif 25 <= rsi_scaled <= 30 or 70 <= rsi_scaled <= 75:  # Poor momentum
                rsi_score = 40
            elif 20 <= rsi_scaled <= 25 or 75 <= rsi_scaled <= 80:  # Very poor momentum
                rsi_score = 25
            else:  # Extreme levels
                rsi_score = 10
        else:
            rsi_score = 50
        
        components['rsi_momentum'] = rsi_score
        
        # Stochastic Momentum (25% weight) - Handle scaled data
        stoch_k = indicators.get('stoch_k', None)
        if stoch_k is not None and stoch_k >= 0:
            # Scale down Stochastic (divide by ~10)
            stoch_scaled = stoch_k / 10
            if 40 <= stoch_scaled <= 60:  # Neutral zone
                stoch_score = 100
            elif 30 <= stoch_scaled <= 40 or 60 <= stoch_scaled <= 70:  # Good momentum
                stoch_score = 85
            elif 20 <= stoch_scaled <= 30 or 70 <= stoch_scaled <= 80:  # Moderate momentum
                stoch_score = 70
            elif 15 <= stoch_scaled <= 20 or 80 <= stoch_scaled <= 85:  # Weak momentum
                stoch_score = 55
            elif 10 <= stoch_scaled <= 15 or 85 <= stoch_scaled <= 90:  # Poor momentum
                stoch_score = 40
            elif 5 <= stoch_scaled <= 10 or 90 <= stoch_scaled <= 95:  # Very poor momentum
                stoch_score = 25
            else:  # Extreme levels
                stoch_score = 10
        else:
            stoch_score = 50
        
        components['stochastic_momentum'] = stoch_score
        
        # CCI Momentum (25% weight) - Handle scaled data
        cci = indicators.get('cci_20', None)
        if cci is not None:
            # Scale down CCI (divide by ~100)
            cci_scaled = cci / 100
            if -50 <= cci_scaled <= 50:  # Neutral zone
                cci_score = 100
            elif -100 <= cci_scaled <= -50 or 50 <= cci_scaled <= 100:  # Good momentum
                cci_score = 85
            elif -150 <= cci_scaled <= -100 or 100 <= cci_scaled <= 150:  # Moderate momentum
                cci_score = 70
            elif -200 <= cci_scaled <= -150 or 150 <= cci_scaled <= 200:  # Weak momentum
                cci_score = 55
            elif -250 <= cci_scaled <= -200 or 200 <= cci_scaled <= 250:  # Poor momentum
                cci_score = 40
            elif -300 <= cci_scaled <= -250 or 250 <= cci_scaled <= 300:  # Very poor momentum
                cci_score = 25
            else:  # Extreme levels
                cci_score = 10
        else:
            cci_score = 50
        
        components['cci_momentum'] = cci_score
        
        # MACD Histogram (20% weight) - Handle scaled data
        macd_histogram = indicators.get('macd_histogram', None)
        if macd_histogram is not None:
            # Scale down MACD histogram (divide by ~100)
            hist_scaled = macd_histogram / 100
            if abs(hist_scaled) < 0.01:  # Very small histogram (neutral)
                macd_hist_score = 100
            elif 0.01 <= hist_scaled <= 0.05:  # Small positive
                macd_hist_score = 85
            elif 0.05 < hist_scaled <= 0.15:  # Moderate positive
                macd_hist_score = 70
            elif 0.15 < hist_scaled <= 0.3:  # Strong positive
                macd_hist_score = 55
            elif hist_scaled > 0.3:  # Very strong positive
                macd_hist_score = 40
            elif -0.05 <= hist_scaled < -0.01:  # Small negative
                macd_hist_score = 75
            elif -0.15 <= hist_scaled < -0.05:  # Moderate negative
                macd_hist_score = 60
            elif -0.3 <= hist_scaled < -0.15:  # Strong negative
                macd_hist_score = 45
            else:  # Very strong negative
                macd_hist_score = 30
        else:
            macd_hist_score = 50
        
        components['macd_histogram'] = macd_hist_score
        
        # Calculate weighted average
        momentum = (
            rsi_score * 0.30 +
            stoch_score * 0.25 +
            cci_score * 0.25 +
            macd_hist_score * 0.20
        )
        
        return momentum, components
    
    def calculate_support_resistance_component(self, indicators: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Support/Resistance Component (0-100)
        Components: Price vs Support/Resistance (40%), Support Strength (30%), Resistance Distance (30%)
        """
        components = {}
        
        current_price = indicators.get('close', None)
        nearest_support = indicators.get('nearest_support', None)
        nearest_resistance = indicators.get('nearest_resistance', None)
        support_strength = indicators.get('support_strength', None)
        
        # Price vs Support/Resistance (40% weight)
        if (current_price is not None and nearest_support is not None and 
            nearest_resistance is not None and current_price > 0 and 
            nearest_support > 0 and nearest_resistance > 0):
            support_distance = abs(current_price - nearest_support)
            resistance_distance = abs(current_price - nearest_resistance)
            
            if support_distance < resistance_distance * 0.5:  # Price near strong support
                price_vs_sr_score = 100
            elif support_distance < resistance_distance:  # Price between support/resistance
                price_vs_sr_score = 80
            elif support_distance < resistance_distance * 1.5:  # Price near weak support
                price_vs_sr_score = 60
            elif resistance_distance < support_distance * 0.5:  # Price near resistance
                price_vs_sr_score = 40
            else:  # Price breaking support
                price_vs_sr_score = 20
        else:
            price_vs_sr_score = 50
        
        components['price_vs_support_resistance'] = price_vs_sr_score
        
        # Support Strength (30% weight)
        if support_strength is not None and support_strength > 0:
            if support_strength > 80:  # Strong support
                support_strength_score = 100
            elif support_strength > 60:  # Moderate support
                support_strength_score = 80
            elif support_strength > 40:  # Weak support
                support_strength_score = 60
            elif support_strength > 20:  # No clear support
                support_strength_score = 40
            else:  # Support broken
                support_strength_score = 20
        else:
            support_strength_score = 50
        
        components['support_strength'] = support_strength_score
        
        # Resistance Distance (30% weight)
        if (current_price is not None and nearest_resistance is not None and 
            current_price > 0 and nearest_resistance > 0):
            distance_pct = (nearest_resistance - current_price) / current_price * 100
            if distance_pct > 20:  # Resistance far above
                resistance_distance_score = 100
            elif distance_pct > 10:  # Resistance moderately above
                resistance_distance_score = 80
            elif distance_pct > 5:  # Resistance close above
                resistance_distance_score = 60
            elif distance_pct > 2:  # Resistance very close
                resistance_distance_score = 40
            else:  # At resistance level
                resistance_distance_score = 20
        else:
            resistance_distance_score = 50
        
        components['resistance_distance'] = resistance_distance_score
        
        # Calculate weighted average
        support_resistance = (
            price_vs_sr_score * 0.40 +
            support_strength_score * 0.30 +
            resistance_distance_score * 0.30
        )
        
        return support_resistance, components
    
    def calculate_volume_confirmation_component(self, indicators: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Volume Confirmation Component (0-100)
        Components: OBV Trend (40%), VWAP Position (35%), Volume Trend (25%)
        """
        components = {}
        
        # OBV Trend (40% weight) - Simplified for now
        obv = indicators.get('obv', None)
        if obv is not None and obv != 0:
            # For now, assume stable OBV if we have data
            obv_score = 80
        else:
            obv_score = 50
        
        components['obv_trend'] = obv_score
        
        # VWAP Position (35% weight)
        current_price = indicators.get('close', None)
        vwap = indicators.get('vwap', None)
        
        if (current_price is not None and vwap is not None and 
            current_price > 0 and vwap > 0):
            vwap_diff = (current_price - vwap) / vwap * 100
            if abs(vwap_diff) < 1:  # Price near VWAP
                vwap_score = 100
            elif abs(vwap_diff) < 3:  # Price close to VWAP
                vwap_score = 80
            elif abs(vwap_diff) < 5:  # Price moderately away from VWAP
                vwap_score = 60
            elif abs(vwap_diff) < 10:  # Price far from VWAP
                vwap_score = 40
            else:  # Price very far from VWAP
                vwap_score = 20
        else:
            vwap_score = 50
        
        components['vwap_position'] = vwap_score
        
        # Volume Trend (25% weight) - Simplified
        volume = indicators.get('volume', None)
        if volume is not None and volume > 0:
            # For now, assume good volume if we have data
            volume_score = 70
        else:
            volume_score = 50
        
        components['volume_trend'] = volume_score
        
        # Calculate weighted average
        volume_confirmation = (
            obv_score * 0.40 +
            vwap_score * 0.35 +
            volume_score * 0.25
        )
        
        return volume_confirmation, components
    
    def calculate_trading_signal_score(self, indicators: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Trading Signal Score (0-100)
        Components: Buy Signals (60%), Signal Strength (40%)
        """
        components = {}
        
        # Buy Signals Component (60% weight)
        rsi = indicators.get('rsi_14', 50)
        macd_line = indicators.get('macd_line', 0)
        macd_signal = indicators.get('macd_signal', 0)
        stoch_k = indicators.get('stoch_k', 50)
        current_price = indicators.get('close', 0)
        nearest_support = indicators.get('nearest_support', 0)
        cci = indicators.get('cci_20', 0)
        
        # RSI Buy Signals - Handle scaled data (values are ~100x larger)
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
        
        # MACD Buy Signals - Handle scaled data
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
        
        # Stochastic Buy Signals - Handle scaled data
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
        
        # CCI Buy Signals - Handle scaled data
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
        
        # Price vs Support - More nuanced
        if (current_price is not None and nearest_support is not None and 
            current_price > 0 and nearest_support > 0):
            support_distance = abs(current_price - nearest_support) / current_price * 100
            if support_distance < 1:  # At strong support
                price_support_score = 100
            elif support_distance < 3:  # Near support
                price_support_score = 85
            elif support_distance < 5:  # Moderately near support
                price_support_score = 70
            elif support_distance < 10:  # Neutral
                price_support_score = 50
            elif support_distance < 15:  # Far from support
                price_support_score = 30
            else:  # Very far from support
                price_support_score = 15
        else:
            price_support_score = 50
        
        # Calculate Buy Signals Component with equal weights
        buy_signals = (
            rsi_buy_score * 0.25 +
            macd_buy_score * 0.25 +
            stoch_buy_score * 0.20 +
            cci_buy_score * 0.15 +
            price_support_score * 0.15
        )
        
        components['buy_signals'] = buy_signals
        
        # Signal Strength (40% weight) - Based on ADX and volume
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
        
        # Volume strength
        if (volume_sma is not None and current_volume is not None and 
            volume_sma > 0):
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
        
        # Combined signal strength
        signal_strength = (adx_strength * 0.6 + volume_strength * 0.4)
        components['signal_strength'] = signal_strength
        
        # Calculate Trading Signal Score - FIXED FORMULA
        # Now buy_signals directly contributes to the final score
        trading_signal = (
            buy_signals * 0.60 +
            signal_strength * 0.40
        )
        
        return trading_signal, components
    
    def calculate_risk_assessment_score(self, indicators: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Risk Assessment Score (0-100, higher = more risk)
        Components: Volatility Risk (35%), Trend Reversal Risk (30%), Support Breakdown Risk (20%), Volume Risk (15%)
        """
        components = {}
        
        # Volatility Risk Component (35% weight)
        atr = indicators.get('atr_14', 0)
        current_price = indicators.get('close', 0)
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        
        # ATR Volatility
        if atr and current_price:
            atr_pct = (atr / current_price) * 100
            if atr_pct < 2:
                atr_risk = 0
            elif atr_pct < 5:
                atr_risk = 25
            elif atr_pct < 10:
                atr_risk = 50
            elif atr_pct < 15:
                atr_risk = 75
            else:
                atr_risk = 100
        else:
            atr_risk = 50
        
        # Bollinger Band Width
        if bb_upper and bb_lower and current_price:
            bb_width = ((bb_upper - bb_lower) / current_price) * 100
            if bb_width < 10:
                bb_risk = 0
            elif bb_width < 20:
                bb_risk = 25
            elif bb_width < 30:
                bb_risk = 50
            elif bb_width < 40:
                bb_risk = 75
            else:
                bb_risk = 100
        else:
            bb_risk = 50
        
        # Price vs Bollinger Bands
        if current_price and bb_upper and bb_lower:
            if bb_lower <= current_price <= bb_upper:
                bb_position_risk = 0
            elif current_price < bb_lower or current_price > bb_upper:
                bb_position_risk = 75
            else:
                bb_position_risk = 25
        else:
            bb_position_risk = 50
        
        volatility_risk = (
            atr_risk * 0.40 +
            bb_risk * 0.35 +
            bb_position_risk * 0.25
        )
        
        components['volatility_risk'] = volatility_risk
        
        # Trend Reversal Risk (30% weight) - Simplified
        rsi = indicators.get('rsi_14', 50)
        if rsi > 70 or rsi < 30:
            reversal_risk = 75
        elif rsi > 60 or rsi < 40:
            reversal_risk = 50
        else:
            reversal_risk = 25
        
        components['trend_reversal_risk'] = reversal_risk
        
        # Support Breakdown Risk (20% weight)
        current_price = indicators.get('close', 0)
        nearest_support = indicators.get('nearest_support', 0)
        
        if current_price and nearest_support:
            support_distance = (current_price - nearest_support) / current_price * 100
            if support_distance > 10:
                support_risk = 0
            elif support_distance > 5:
                support_risk = 25
            elif support_distance > 2:
                support_risk = 50
            elif support_distance > 0:
                support_risk = 75
            else:
                support_risk = 100
        else:
            support_risk = 50
        
        components['support_breakdown_risk'] = support_risk
        
        # Volume Risk (15% weight) - Simplified
        volume = indicators.get('volume', 0)
        if volume:
            volume_risk = 25  # Assume stable volume
        else:
            volume_risk = 75  # Missing volume data
        
        components['volume_risk'] = volume_risk
        
        # Calculate Risk Assessment Score
        risk_score = (
            volatility_risk * 0.35 +
            reversal_risk * 0.30 +
            support_risk * 0.20 +
            volume_risk * 0.15
        )
        
        return risk_score, components
    
    def get_grade_from_score(self, score: float) -> str:
        """
        Convert score to grade based on 5-level scale
        """
        if score >= 80:
            return 'Strong Buy'
        elif score >= 65:
            return 'Buy'
        elif score >= 50:
            return 'Neutral'
        elif score >= 35:
            return 'Sell'
        else:
            return 'Strong Sell'
    
    def get_trading_signal_rating(self, score: float) -> str:
        """Convert trading signal score to rating"""
        if score >= 80:
            return 'Strong Buy'
        elif score >= 60:
            return 'Buy'
        elif score >= 40:
            return 'Neutral'
        elif score >= 20:
            return 'Sell'
        else:
            return 'Strong Sell'
    
    def get_risk_level(self, score: float) -> str:
        """
        Convert risk score to risk level (inverted: lower score = lower risk)
        """
        if score <= 25:
            return 'Very Low'
        elif score <= 40:
            return 'Low'
        elif score <= 60:
            return 'Medium'
        elif score <= 75:
            return 'High'
        else:
            return 'Very High'
    
    def detect_technical_alerts(self, indicators: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Detect technical red and yellow flags"""
        red_flags = []
        yellow_flags = []
        
        # Red Flags
        rsi = indicators.get('rsi_14', 50)
        if rsi > 80 or rsi < 20:
            red_flags.append(f"RSI at extreme levels ({rsi:.1f})")
        
        atr = indicators.get('atr_14', 0)
        current_price = indicators.get('close', 0)
        if atr and current_price and (atr / current_price) * 100 > 15:
            red_flags.append("Extremely high volatility (ATR > 15%)")
        
        # Yellow Flags
        if rsi > 70 or rsi < 30:
            yellow_flags.append(f"RSI approaching extremes ({rsi:.1f})")
        
        if atr and current_price and (atr / current_price) * 100 > 10:
            yellow_flags.append("High volatility (ATR > 10%)")
        
        return red_flags, yellow_flags
    
    def calculate_technical_scores(self, ticker: str) -> Dict[str, Any]:
        """
        Calculate all technical scores for a ticker
        """
        logger.info(f"Calculating technical scores for {ticker}")
        
        # Get technical indicators
        indicators = self.get_technical_indicators(ticker)
        if not indicators:
            logger.warning(f"No technical data available for {ticker}")
            return {}
        
        # Calculate Technical Health Score
        trend_strength, trend_components = self.calculate_trend_strength_component(indicators)
        momentum, momentum_components = self.calculate_momentum_component(indicators)
        support_resistance, sr_components = self.calculate_support_resistance_component(indicators)
        volume_confirmation, volume_components = self.calculate_volume_confirmation_component(indicators)
        
        technical_health_score = (
            trend_strength * 0.35 +
            momentum * 0.25 +
            support_resistance * 0.25 +
            volume_confirmation * 0.15
        )
        
        # Apply 5-level normalization
        technical_health_normalized = self.normalize_score_to_5_levels(technical_health_score, 'technical_health')
        
        # Calculate Trading Signal Score
        trading_signal_score, trading_components = self.calculate_trading_signal_score(indicators)
        trading_signal_normalized = self.normalize_score_to_5_levels(trading_signal_score, 'trading_signal')
        
        # Calculate Risk Assessment Score
        risk_score, risk_components = self.calculate_risk_assessment_score(indicators)
        risk_normalized = self.normalize_score_to_5_levels(risk_score, 'technical_risk')
        
        # Detect alerts
        red_flags, yellow_flags = self.detect_technical_alerts(indicators)
        
        # Compile results
        results = {
            'ticker': ticker,
            'technical_health_score': round(technical_health_score, 2),
            'technical_health_normalized': technical_health_normalized['normalized_score'],
            'technical_health_grade': technical_health_normalized['grade'],
            'technical_health_description': technical_health_normalized['description'],
            'technical_health_components': {
                'trend_strength': round(trend_strength, 2),
                'momentum': round(momentum, 2),
                'support_resistance': sr_components,
                'volume_confirmation': round(volume_confirmation, 2),
                'components': {
                    'trend': trend_components,
                    'momentum': momentum_components,
                    'support_resistance': sr_components,
                    'volume': volume_components
                }
            },
            'trading_signal_score': round(trading_signal_score, 2),
            'trading_signal_normalized': trading_signal_normalized['normalized_score'],
            'trading_signal_rating': trading_signal_normalized['grade'],
            'trading_signal_description': trading_signal_normalized['description'],
            'trading_signal_components': trading_components,
            'technical_risk_score': round(risk_score, 2),
            'technical_risk_normalized': risk_normalized['normalized_score'],
            'technical_risk_level': risk_normalized['grade'],
            'technical_risk_description': risk_normalized['description'],
            'technical_risk_components': risk_components,
            'technical_red_flags': red_flags,
            'technical_yellow_flags': yellow_flags,
            'indicators_used': list(indicators.keys())
        }
        
        logger.info(f"Technical scores calculated for {ticker}: Health={technical_health_score:.1f}, Signal={trading_signal_score:.1f}, Risk={risk_score:.1f}")
        
        return results
    
    def store_technical_scores(self, ticker: str, scores: Dict[str, Any], 
                             fundamental_scores: Dict[str, Any] = None) -> bool:
        """
        Store technical scores in database using direct SQL INSERT/UPDATE
        """
        try:
            # Use actual fundamental scores if provided, otherwise use defaults
            if not fundamental_scores:
                fundamental_scores = {
                    'fundamental_health_score': 50.0,
                    'fundamental_health_grade': 'Neutral',
                    'fundamental_health_description': 'No fundamental data available',
                    'fundamental_risk_score': 50.0,
                    'fundamental_risk_level': 'Medium',  # Use correct constraint value
                    'fundamental_risk_description': 'No fundamental data available',
                    'value_investment_score': 50.0,
                    'value_rating': 'Neutral',
                    'value_investment_description': 'No fundamental data available',
                    'fundamental_red_flags': [],
                    'fundamental_yellow_flags': []
                }
            
            # Calculate overall score (simple average for now)
            overall_score = (
                scores['technical_health_score'] + 
                fundamental_scores['fundamental_health_score']
            ) / 2
            overall_grade = self.get_grade_from_score(overall_score)
            
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    # First, try to update existing record
                    update_query = """
                    UPDATE company_scores_current SET
                        fundamental_health_score = %s,
                        fundamental_health_grade = %s,
                        fundamental_health_description = %s,
                        fundamental_risk_score = %s,
                        fundamental_risk_level = %s,
                        fundamental_risk_description = %s,
                        value_investment_score = %s,
                        value_rating = %s,
                        value_investment_description = %s,
                        technical_health_score = %s,
                        technical_health_grade = %s,
                        technical_health_description = %s,
                        trading_signal_score = %s,
                        trading_signal_rating = %s,
                        trading_signal_description = %s,
                        technical_risk_score = %s,
                        technical_risk_level = %s,
                        technical_risk_description = %s,
                        overall_score = %s,
                        overall_grade = %s,
                        overall_description = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ticker = %s
                    """
                    
                    cursor.execute(update_query, (
                        fundamental_scores['fundamental_health_score'],
                        fundamental_scores['fundamental_health_grade'],
                        fundamental_scores.get('fundamental_health_description', 'No description available'),
                        fundamental_scores['fundamental_risk_score'],
                        fundamental_scores['fundamental_risk_level'],
                        fundamental_scores.get('fundamental_risk_description', 'No description available'),
                        fundamental_scores['value_investment_score'],
                        fundamental_scores['value_rating'],
                        fundamental_scores.get('value_investment_description', 'No description available'),
                        scores['technical_health_score'],
                        scores['technical_health_grade'],
                        scores.get('technical_health_description', 'No description available'),
                        scores['trading_signal_score'],
                        scores['trading_signal_rating'],
                        scores.get('trading_signal_description', 'No description available'),
                        scores['technical_risk_score'],
                        scores['technical_risk_level'],
                        scores.get('technical_risk_description', 'No description available'),
                        overall_score,
                        overall_grade,
                        f"Overall score: {overall_score:.1f} - {overall_grade}",
                        ticker
                    ))
                    
                    # If no rows were updated, insert new record
                    if cursor.rowcount == 0:
                        insert_query = """
                        INSERT INTO company_scores_current (
                            ticker, fundamental_health_score, fundamental_health_grade, 
                            fundamental_health_description, fundamental_risk_score, 
                            fundamental_risk_level, fundamental_risk_description,
                            value_investment_score, value_rating, value_investment_description,
                            technical_health_score, technical_health_grade, 
                            technical_health_description, trading_signal_score, 
                            trading_signal_rating, trading_signal_description,
                            technical_risk_score, technical_risk_level, 
                            technical_risk_description, overall_score, overall_grade,
                            overall_description, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        """
                        
                        cursor.execute(insert_query, (
                            ticker,
                            fundamental_scores['fundamental_health_score'],
                            fundamental_scores['fundamental_health_grade'],
                            fundamental_scores.get('fundamental_health_description', 'No description available'),
                            fundamental_scores['fundamental_risk_score'],
                            fundamental_scores['fundamental_risk_level'],
                            fundamental_scores.get('fundamental_risk_description', 'No description available'),
                            fundamental_scores['value_investment_score'],
                            fundamental_scores['value_rating'],
                            fundamental_scores.get('value_investment_description', 'No description available'),
                            scores['technical_health_score'],
                            scores['technical_health_grade'],
                            scores.get('technical_health_description', 'No description available'),
                            scores['trading_signal_score'],
                            scores['trading_signal_rating'],
                            scores.get('trading_signal_description', 'No description available'),
                            scores['technical_risk_score'],
                            scores['technical_risk_level'],
                            scores.get('technical_risk_description', 'No description available'),
                            overall_score,
                            overall_grade,
                            f"Overall score: {overall_score:.1f} - {overall_grade}"
                        ))
                    
                    # Also insert into historical table
                    historical_query = """
                    INSERT INTO company_scores_historical (
                        ticker, calculation_date, fundamental_health_score, fundamental_health_grade, 
                        fundamental_health_description, fundamental_risk_score, 
                        fundamental_risk_level, fundamental_risk_description,
                        value_investment_score, value_rating, value_investment_description,
                        technical_health_score, technical_health_grade, 
                        technical_health_description, trading_signal_score, 
                        trading_signal_rating, trading_signal_description,
                        technical_risk_score, technical_risk_level, 
                        technical_risk_description, overall_score, overall_grade,
                        overall_description, created_at
                    ) VALUES (
                        %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT (ticker, calculation_date) DO UPDATE SET
                        fundamental_health_score = EXCLUDED.fundamental_health_score,
                        fundamental_health_grade = EXCLUDED.fundamental_health_grade,
                        fundamental_health_description = EXCLUDED.fundamental_health_description,
                        fundamental_risk_score = EXCLUDED.fundamental_risk_score,
                        fundamental_risk_level = EXCLUDED.fundamental_risk_level,
                        fundamental_risk_description = EXCLUDED.fundamental_risk_description,
                        value_investment_score = EXCLUDED.value_investment_score,
                        value_rating = EXCLUDED.value_rating,
                        value_investment_description = EXCLUDED.value_investment_description,
                        technical_health_score = EXCLUDED.technical_health_score,
                        technical_health_grade = EXCLUDED.technical_health_grade,
                        technical_health_description = EXCLUDED.technical_health_description,
                        trading_signal_score = EXCLUDED.trading_signal_score,
                        trading_signal_rating = EXCLUDED.trading_signal_rating,
                        trading_signal_description = EXCLUDED.trading_signal_description,
                        technical_risk_score = EXCLUDED.technical_risk_score,
                        technical_risk_level = EXCLUDED.technical_risk_level,
                        technical_risk_description = EXCLUDED.technical_risk_description,
                        overall_score = EXCLUDED.overall_score,
                        overall_grade = EXCLUDED.overall_grade,
                        overall_description = EXCLUDED.overall_description,
                        created_at = EXCLUDED.created_at
                    """
                    
                    cursor.execute(historical_query, (
                        ticker,
                        fundamental_scores['fundamental_health_score'],
                        fundamental_scores['fundamental_health_grade'],
                        fundamental_scores.get('fundamental_health_description', 'No description available'),
                        fundamental_scores['fundamental_risk_score'],
                        fundamental_scores['fundamental_risk_level'],
                        fundamental_scores.get('fundamental_risk_description', 'No description available'),
                        fundamental_scores['value_investment_score'],
                        fundamental_scores['value_rating'],
                        fundamental_scores.get('value_investment_description', 'No description available'),
                        scores['technical_health_score'],
                        scores['technical_health_grade'],
                        scores.get('technical_health_description', 'No description available'),
                        scores['trading_signal_score'],
                        scores['trading_signal_rating'],
                        scores.get('trading_signal_description', 'No description available'),
                        scores['technical_risk_score'],
                        scores['technical_risk_level'],
                        scores.get('technical_risk_description', 'No description available'),
                        overall_score,
                        overall_grade,
                        f"Overall score: {overall_score:.1f} - {overall_grade}"
                    ))
                    
                    conn.commit()
                    logger.info(f"Technical scores stored for {ticker}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error storing technical scores for {ticker}: {e}")
            return False
    
    def calculate_scores_for_tickers(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Calculate technical scores for multiple tickers
        """
        results = {
            'successful': [],
            'failed': [],
            'summary': {}
        }
        
        start_time = time.time()
        
        for ticker in tickers:
            try:
                scores = self.calculate_technical_scores(ticker)
                if scores:
                    # Store in database
                    if self.store_technical_scores(ticker, scores):
                        results['successful'].append({
                            'ticker': ticker,
                            'scores': scores
                        })
                    else:
                        results['failed'].append(ticker)
                else:
                    results['failed'].append(ticker)
                    
            except Exception as e:
                logger.error(f"Error calculating scores for {ticker}: {e}")
                results['failed'].append(ticker)
        
        # Calculate summary
        total_time = time.time() - start_time
        results['summary'] = {
            'total_tickers': len(tickers),
            'successful': len(results['successful']),
            'failed': len(results['failed']),
            'success_rate': len(results['successful']) / len(tickers) * 100,
            'total_time_seconds': round(total_time, 2),
            'average_time_per_ticker': round(total_time / len(tickers), 3)
        }
        
        return results

    def normalize_score_to_5_levels(self, score, score_type):
        """
        Normalize a 0-100 score to 5 levels: Strong Sell (1), Sell (2), Neutral (3), Buy (4), Strong Buy (5)
        
        Args:
            score (float): Score from 0-100
            score_type (str): Type of score for specific thresholds
            
        Returns:
            dict: Contains normalized_score (1-5), grade (string), and description
        """
        if score is None:
            return {
                'normalized_score': 3,
                'grade': 'Neutral',
                'description': 'Insufficient data for assessment'
            }
        
        # Different thresholds for different score types
        if score_type == 'technical_health':
            # Higher scores are better for technical health
            if score >= 80:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Excellent technical health'}
            elif score >= 65:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Good technical health'}
            elif score >= 45:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Average technical health'}
            elif score >= 25:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Poor technical health'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very poor technical health'}
        
        elif score_type == 'trading_signal':
            # Higher scores are better for trading signals
            if score >= 75:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Strong buy signal'}
            elif score >= 60:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Buy signal'}
            elif score >= 40:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Neutral signal'}
            elif score >= 25:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Sell signal'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Strong sell signal'}
        
        elif score_type == 'technical_risk':
            # Lower scores are better for technical risk (less risk = better)
            if score <= 25:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Very low technical risk'}
            elif score <= 40:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Low technical risk'}
            elif score <= 60:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Moderate technical risk'}
            elif score <= 80:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'High technical risk'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very high technical risk'}
        
        else:
            # Default normalization
            if score >= 80:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Excellent'}
            elif score >= 60:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Good'}
            elif score >= 40:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Average'}
            elif score >= 20:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Poor'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very poor'}

def main():
    """Main function for testing"""
    calculator = TechnicalScoreCalculator()
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
    
    print("🧪 Testing Technical Score Calculator")
    print("=" * 50)
    
    results = calculator.calculate_scores_for_tickers(test_tickers)
    
    print(f"\n📊 Results Summary:")
    print(f"Total tickers: {results['summary']['total_tickers']}")
    print(f"Successful: {results['summary']['successful']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Success rate: {results['summary']['success_rate']:.1f}%")
    print(f"Total time: {results['summary']['total_time_seconds']}s")
    print(f"Average time per ticker: {results['summary']['average_time_per_ticker']}s")
    
    print(f"\n✅ Successful Calculations:")
    for result in results['successful']:
        ticker = result['ticker']
        scores = result['scores']
        print(f"  {ticker}: Health={scores['technical_health_score']:.1f} ({scores['technical_health_grade']}), "
              f"Signal={scores['trading_signal_score']:.1f} ({scores['trading_signal_rating']}), "
              f"Risk={scores['technical_risk_score']:.1f} ({scores['technical_risk_level']})")
    
    if results['failed']:
        print(f"\n❌ Failed Calculations:")
        for ticker in results['failed']:
            print(f"  {ticker}")

if __name__ == "__main__":
    main() 