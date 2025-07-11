"""
Technical Scorer

Calculates technical scores using existing indicators from daily_charts table
and applies logic from card_logic.csv and trader_scoring.csv files.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import date
from ..database import DatabaseManager
from .database_manager import ScoreDatabaseManager

logger = logging.getLogger(__name__)


class TechnicalScorer:
    """Calculates technical scores using existing indicators"""
    
    def __init__(self, db: DatabaseManager = None, score_db: ScoreDatabaseManager = None):
        self.db = db or DatabaseManager()
        self.score_db = score_db or ScoreDatabaseManager(db)
        
        # Load scoring logic from CSV files
        self.card_logic = self._load_card_logic()
        self.trader_weights = self._load_trader_weights()
    
    def _load_card_logic(self) -> pd.DataFrame:
        """Load card logic from CSV file"""
        try:
            # Read from logic_tables directory
            card_logic_path = "logic_tables/card_logic.csv"
            df = pd.read_csv(card_logic_path)
            logger.info(f"Loaded card logic with {len(df)} rules")
            return df
        except Exception as e:
            logger.error(f"Error loading card logic: {e}")
            return pd.DataFrame()
    
    def _load_trader_weights(self) -> pd.DataFrame:
        """Load trader scoring weights from CSV file"""
        try:
            # Read from logic_tables directory
            weights_path = "logic_tables/trader_scoring.csv"
            df = pd.read_csv(weights_path)
            logger.info(f"Loaded trader weights with {len(df)} rules")
            return df
        except Exception as e:
            logger.error(f"Error loading trader weights: {e}")
            return pd.DataFrame()
    
    def get_latest_indicators(self, ticker: str) -> Optional[Dict]:
        """Get latest technical indicators from daily_charts table"""
        try:
            query = """
            SELECT 
                date, close, volume,
                rsi_14, stoch_k, cci_20, macd_line, macd_signal, macd_histogram,
                ema_20, ema_50, ema_100, atr_14, adx_14,
                bb_upper, bb_middle, bb_lower, vwap,
                nearest_support, nearest_resistance, support_strength, resistance_strength
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query, (ticker,))
            if not result:
                return None
            
            row = result[0]
            return {
                'date': row[0],
                'close': float(row[1]) / 100.0,  # Convert from cents
                'volume': row[2],
                'rsi_14': row[3],
                'stoch_k': row[4],
                'cci_20': row[5],
                'macd_line': row[6],
                'macd_signal': row[7],
                'macd_histogram': row[8],
                'ema_20': row[9] / 100.0 if row[9] else None,
                'ema_50': row[10] / 100.0 if row[10] else None,
                'ema_100': row[11] / 100.0 if row[11] else None,
                'atr_14': row[12] / 100.0 if row[12] else None,
                'adx_14': row[13],
                'bb_upper': row[14] / 100.0 if row[14] else None,
                'bb_middle': row[15] / 100.0 if row[15] else None,
                'bb_lower': row[16] / 100.0 if row[16] else None,
                'vwap': row[17] / 100.0 if row[17] else None,
                'nearest_support': row[18] / 100.0 if row[18] else None,
                'nearest_resistance': row[19] / 100.0 if row[19] else None,
                'support_strength': row[20],
                'resistance_strength': row[21]
            }
            
        except Exception as e:
            logger.error(f"Error getting indicators for {ticker}: {e}")
            return None
    
    def get_volume_data(self, ticker: str) -> Optional[Dict]:
        """Get volume data for volume ratio calculation"""
        try:
            query = """
            SELECT volume, date
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 20
            """
            
            results = self.db.execute_query(query, (ticker,))
            if len(results) < 10:
                return None
            
            volumes = [row[0] for row in results if row[0] is not None]
            if not volumes:
                return None
            
            current_volume = volumes[0]
            avg_volume = sum(volumes[1:10]) / len(volumes[1:10])  # 10-day average excluding today
            
            return {
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1.0
            }
            
        except Exception as e:
            logger.error(f"Error getting volume data for {ticker}: {e}")
            return None
    
    def calculate_signal_strengths(self, indicators: Dict) -> Dict:
        """Calculate signal strengths (1-5) for each card using card logic"""
        signals = {}
        missing = []
        try:
            # Extract key values for logic evaluation
            close = indicators.get('close', 0)
            rsi = indicators.get('rsi_14', 50)
            stoch = indicators.get('stoch_k', 50)
            cci = indicators.get('cci_20', 0)
            ema_20 = indicators.get('ema_20', close)
            ema_50 = indicators.get('ema_50', close)
            ema_100 = indicators.get('ema_100', close)
            atr = indicators.get('atr_14', 0)
            adx = indicators.get('adx_14', 25)
            volume_ratio = indicators.get('volume_ratio', 1.0)
            support = indicators.get('nearest_support', close * 0.95)
            resistance = indicators.get('nearest_resistance', close * 1.05)

            # Check for missing indicators
            for name, val in [('close', close), ('rsi_14', rsi), ('stoch_k', stoch), ('cci_20', cci),
                              ('ema_20', ema_20), ('ema_50', ema_50), ('ema_100', ema_100),
                              ('atr_14', atr), ('adx_14', adx), ('volume_ratio', volume_ratio),
                              ('nearest_support', support), ('nearest_resistance', resistance)]:
                if val is None:
                    missing.append(name)

            # If any required indicator is missing, log and skip those signals
            if missing:
                logger.warning(f"Missing indicators for signal calculation: {missing}")

            # Only do comparisons if all required are present
            def safe_gt(a, b):
                return a is not None and b is not None and a > b
            def safe_lt(a, b):
                return a is not None and b is not None and a < b
            def safe_abs(a):
                return abs(a) if a is not None else None

            trend_up = safe_gt(ema_20, ema_50) and safe_gt(ema_50, ema_100)
            golden_cross = safe_gt(ema_20, ema_50) and safe_gt(ema_50, ema_100)
            death_cross = safe_lt(ema_20, ema_50) and safe_lt(ema_50, ema_100)
            macd_bullish = safe_gt(indicators.get('macd_line'), indicators.get('macd_signal'))
            macd_bearish = safe_lt(indicators.get('macd_line'), indicators.get('macd_signal'))
            at_resistance = (safe_abs(close - resistance) is not None and atr and safe_abs(close - resistance) < (atr * 0.5)) if atr else False
            at_support = (safe_abs(close - support) is not None and atr and safe_abs(close - support) < (atr * 0.5)) if atr else False
            distance_to_resistance = ((resistance - close) / atr) if (atr and resistance is not None and close is not None) else 10
            momentum_bearish = (rsi is not None and rsi > 70) or (stoch is not None and stoch > 80) or (cci is not None and cci > 100)
            extreme_overbought_all = (rsi is not None and rsi > 80) and (stoch is not None and stoch > 90) and (cci is not None and cci > 150)
            bb_upper = indicators.get('bb_upper')
            bb_lower = indicators.get('bb_lower')
            bb_squeeze = (bb_upper is not None and bb_lower is not None and atr and (bb_upper - bb_lower) < atr) if atr else False
            bb_expansion = (bb_upper is not None and bb_lower is not None and atr and (bb_upper - bb_lower) > atr * 2) if atr else False

            # Calculate ATR percentile (simplified)
            atr_percentile = 50  # Default to middle range

            # Evaluate each card
            for _, row in self.card_logic.iterrows():
                card_name = row['Card_Name']
                condition_logic = row['Condition_Logic']
                signal_strength = row['Signal_Strength']

                # Evaluate condition logic (skip if any required variable is None)
                try:
                    condition_met = self._evaluate_condition(condition_logic, locals())
                except Exception as e:
                    logger.warning(f"Skipping card {card_name} due to missing data: {e}")
                    continue

                if condition_met:
                    signals[card_name.lower().replace(' ', '_') + '_score'] = signal_strength
                    break  # Use first matching condition

            # Ensure all signals have values (default to 3 if not calculated)
            required_signals = [
                'price_position_trend_score',
                'momentum_cluster_score', 
                'volume_confirmation_score',
                'trend_direction_score',
                'volatility_risk_score'
            ]

            for signal in required_signals:
                if signal not in signals:
                    signals[signal] = 3  # Default neutral score

            return signals

        except Exception as e:
            logger.error(f"Error calculating signal strengths: {e}")
            return {
                'price_position_trend_score': 3,
                'momentum_cluster_score': 3,
                'volume_confirmation_score': 3,
                'trend_direction_score': 3,
                'volatility_risk_score': 3
            }
    
    def _evaluate_condition(self, condition_logic: str, variables: Dict) -> bool:
        """Evaluate condition logic string against variables"""
        try:
            # Start with False - only return True if conditions are explicitly met
            conditions_met = 0
            total_conditions = 0
            
            # Check for trend conditions
            if 'trend_up' in condition_logic:
                total_conditions += 1
                if variables.get('trend_up', False):
                    conditions_met += 1
            if 'golden_cross' in condition_logic:
                total_conditions += 1
                if variables.get('golden_cross', False):
                    conditions_met += 1
            if 'death_cross' in condition_logic:
                total_conditions += 1
                if variables.get('death_cross', False):
                    conditions_met += 1
            if 'trend_down' in condition_logic:
                total_conditions += 1
                if variables.get('trend_down', False):
                    conditions_met += 1
            
            # Check for MACD conditions
            if 'macd_bullish' in condition_logic:
                total_conditions += 1
                if variables.get('macd_bullish', False):
                    conditions_met += 1
            if 'macd_bearish' in condition_logic:
                total_conditions += 1
                if variables.get('macd_bearish', False):
                    conditions_met += 1
            if 'macd_bullish_cross' in condition_logic:
                total_conditions += 1
                # Simplified check - would need more complex logic for actual cross detection
                if variables.get('macd_bullish', False):
                    conditions_met += 1
            
            # Check for position conditions
            if 'at_resistance' in condition_logic:
                total_conditions += 1
                if variables.get('at_resistance', False):
                    conditions_met += 1
            if 'at_support' in condition_logic:
                total_conditions += 1
                if variables.get('at_support', False):
                    conditions_met += 1
            
            # Check for momentum conditions
            if 'momentum_bearish' in condition_logic:
                total_conditions += 1
                if variables.get('momentum_bearish', False):
                    conditions_met += 1
            if 'extreme_overbought_all' in condition_logic:
                total_conditions += 1
                if variables.get('extreme_overbought_all', False):
                    conditions_met += 1
            
            # Check for Bollinger Band conditions
            if 'bb_squeeze' in condition_logic:
                total_conditions += 1
                if variables.get('bb_squeeze', False):
                    conditions_met += 1
            if 'bb_expansion' in condition_logic:
                total_conditions += 1
                if variables.get('bb_expansion', False):
                    conditions_met += 1
            
            # Check for price vs EMA conditions
            if 'ema20_above_ema50' in condition_logic:
                total_conditions += 1
                ema_20 = variables.get('ema_20')
                ema_50 = variables.get('ema_50')
                if ema_20 is not None and ema_50 is not None and ema_20 > ema_50:
                    conditions_met += 1
            if 'price_above_ema50' in condition_logic:
                total_conditions += 1
                close = variables.get('close')
                ema_50 = variables.get('ema_50')
                if close is not None and ema_50 is not None and close > ema_50:
                    conditions_met += 1
            if 'price_below_ema50' in condition_logic:
                total_conditions += 1
                close = variables.get('close')
                ema_50 = variables.get('ema_50')
                if close is not None and ema_50 is not None and close < ema_50:
                    conditions_met += 1
            if 'price_rising' in condition_logic:
                total_conditions += 1
                # Simplified - would need price history for actual rising check
                if variables.get('trend_up', False):
                    conditions_met += 1
            
            # Check RSI conditions
            rsi = variables.get('rsi', 50)
            if 'rsi < 40' in condition_logic:
                total_conditions += 1
                if rsi is not None and rsi < 40:
                    conditions_met += 1
            if 'rsi < 50' in condition_logic:
                total_conditions += 1
                if rsi is not None and rsi < 50:
                    conditions_met += 1
            if 'rsi > 70' in condition_logic:
                total_conditions += 1
                if rsi is not None and rsi > 70:
                    conditions_met += 1
            if 'rsi > 80' in condition_logic:
                total_conditions += 1
                if rsi is not None and rsi > 80:
                    conditions_met += 1
            if 'rsi 45-65' in condition_logic:
                total_conditions += 1
                if rsi is not None and 45 <= rsi <= 65:
                    conditions_met += 1
            
            # Check stochastic conditions
            stoch = variables.get('stoch', 50)
            if 'stoch < 30' in condition_logic:
                total_conditions += 1
                if stoch is not None and stoch < 30:
                    conditions_met += 1
            if 'stoch < 50' in condition_logic:
                total_conditions += 1
                if stoch is not None and stoch < 50:
                    conditions_met += 1
            if 'stoch > 80' in condition_logic:
                total_conditions += 1
                if stoch is not None and stoch > 80:
                    conditions_met += 1
            if 'stoch > 90' in condition_logic:
                total_conditions += 1
                if stoch is not None and stoch > 90:
                    conditions_met += 1
            if 'stoch 40-70' in condition_logic:
                total_conditions += 1
                if stoch is not None and 40 <= stoch <= 70:
                    conditions_met += 1
            
            # Check CCI conditions
            cci = variables.get('cci', 0)
            if 'cci < -50' in condition_logic:
                total_conditions += 1
                if cci is not None and cci < -50:
                    conditions_met += 1
            if 'cci < 0' in condition_logic:
                total_conditions += 1
                if cci is not None and cci < 0:
                    conditions_met += 1
            if 'cci > 100' in condition_logic:
                total_conditions += 1
                if cci is not None and cci > 100:
                    conditions_met += 1
            if 'cci > 150' in condition_logic:
                total_conditions += 1
                if cci is not None and cci > 150:
                    conditions_met += 1
            
            # Check volume conditions
            volume_ratio = variables.get('volume_ratio', 1.0)
            if 'volume_ratio > 2.0' in condition_logic:
                total_conditions += 1
                if volume_ratio is not None and volume_ratio > 2.0:
                    conditions_met += 1
            if 'volume_ratio > 1.5' in condition_logic:
                total_conditions += 1
                if volume_ratio is not None and volume_ratio > 1.5:
                    conditions_met += 1
            if 'volume_ratio > 1.2' in condition_logic:
                total_conditions += 1
                if volume_ratio is not None and volume_ratio > 1.2:
                    conditions_met += 1
            if 'volume_ratio < 0.8' in condition_logic:
                total_conditions += 1
                if volume_ratio is not None and volume_ratio < 0.8:
                    conditions_met += 1
            if 'volume_ratio < 0.7' in condition_logic:
                total_conditions += 1
                if volume_ratio is not None and volume_ratio < 0.7:
                    conditions_met += 1
            if 'volume_ratio < 0.5' in condition_logic:
                total_conditions += 1
                if volume_ratio is not None and volume_ratio < 0.5:
                    conditions_met += 1
            if 'volume_ratio 0.8-1.2' in condition_logic:
                total_conditions += 1
                if volume_ratio is not None and 0.8 <= volume_ratio <= 1.2:
                    conditions_met += 1
            
            # Check ADX conditions
            adx = variables.get('adx', 25)
            if 'adx > 30' in condition_logic:
                total_conditions += 1
                if adx is not None and adx > 30:
                    conditions_met += 1
            if 'adx > 25' in condition_logic:
                total_conditions += 1
                if adx is not None and adx > 25:
                    conditions_met += 1
            if 'adx < 20' in condition_logic:
                total_conditions += 1
                if adx is not None and adx < 20:
                    conditions_met += 1
            if 'adx 20-25' in condition_logic:
                total_conditions += 1
                if adx is not None and 20 <= adx <= 25:
                    conditions_met += 1
            
            # Check distance conditions
            distance_to_resistance = variables.get('distance_to_resistance', 10)
            if 'distance_to_resistance > 4*atr' in condition_logic:
                total_conditions += 1
                if distance_to_resistance is not None and distance_to_resistance > 4:
                    conditions_met += 1
            if 'distance_to_resistance > 2*atr' in condition_logic:
                total_conditions += 1
                if distance_to_resistance is not None and distance_to_resistance > 2:
                    conditions_met += 1
            if 'distance_to_resistance <= 2*atr' in condition_logic:
                total_conditions += 1
                if distance_to_resistance is not None and distance_to_resistance <= 2:
                    conditions_met += 1
            if 'distance_to_resistance <= 1*atr' in condition_logic:
                total_conditions += 1
                if distance_to_resistance is not None and distance_to_resistance <= 1:
                    conditions_met += 1
            
            # Check ATR percentile conditions
            atr_percentile = variables.get('atr_percentile', 50)
            if 'atr_percentile < 30' in condition_logic:
                total_conditions += 1
                if atr_percentile is not None and atr_percentile < 30:
                    conditions_met += 1
            if 'atr_percentile < 50' in condition_logic:
                total_conditions += 1
                if atr_percentile is not None and atr_percentile < 50:
                    conditions_met += 1
            if 'atr_percentile 50-75' in condition_logic:
                total_conditions += 1
                if atr_percentile is not None and 50 <= atr_percentile <= 75:
                    conditions_met += 1
            if 'atr_percentile > 75' in condition_logic:
                total_conditions += 1
                if atr_percentile is not None and atr_percentile > 75:
                    conditions_met += 1
            if 'atr_percentile > 90' in condition_logic:
                total_conditions += 1
                if atr_percentile is not None and atr_percentile > 90:
                    conditions_met += 1
            
            # Check for OBV conditions (simplified)
            if 'obv_rising' in condition_logic:
                total_conditions += 1
                # Simplified - would need OBV data
                conditions_met += 1  # Assume true for now
            
            # Check for VWAP conditions (simplified)
            if 'price_above_vwap' in condition_logic:
                total_conditions += 1
                # Simplified - would need VWAP data
                conditions_met += 1  # Assume true for now
            
            # Only return True if ALL conditions in the logic are met
            if total_conditions == 0:
                return False  # No conditions to check, so return False
            else:
                return conditions_met == total_conditions
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def calculate_composite_scores(self, signal_strengths: Dict) -> Dict:
        """Calculate composite scores for different trader types"""
        composite_scores = {}
        
        try:
            # Map signal strengths to component names
            component_mapping = {
                'price_position_trend_score': 'Price_Position_Trend',
                'momentum_cluster_score': 'Momentum_Cluster',
                'volume_confirmation_score': 'Volume_Confirmation',
                'trend_direction_score': 'Trend_Direction',
                'volatility_risk_score': 'Volatility_Risk'
            }
            
            # Calculate scores for each trader type
            trader_types = ['Swing_Trader', 'Momentum_Trader', 'Long_Term_Investor']
            
            for trader_type in trader_types:
                total_score = 0
                total_weight = 0
                
                # Get weights for this trader type
                trader_weights = self.trader_weights[
                    self.trader_weights['Trader_Type'] == trader_type
                ]
                
                for _, weight_row in trader_weights.iterrows():
                    component = weight_row['Component']
                    weight = weight_row['Weight_Percentage']
                    score_modifier = weight_row['Score_Modifier']
                    
                    # Find corresponding signal strength
                    for signal_key, component_name in component_mapping.items():
                        if component_name == component:
                            signal_strength = signal_strengths.get(signal_key, 3)
                            # Convert 1-5 scale to 0-100 scale
                            score_100 = (signal_strength - 1) * 25
                            # Apply weight and modifier
                            weighted_score = score_100 * weight * score_modifier
                            total_score += weighted_score
                            total_weight += weight
                            break
                
                # Calculate final score
                if total_weight > 0:
                    final_score = int(total_score / total_weight)
                    final_score = max(0, min(100, final_score))  # Clamp to 0-100
                else:
                    final_score = 50  # Default neutral score
                
                composite_scores[f'{trader_type.lower().replace("_", "_")}_score'] = final_score
            
            return composite_scores
            
        except Exception as e:
            logger.error(f"Error calculating composite scores: {e}")
            return {
                'swing_trader_score': 50,
                'momentum_trader_score': 50,
                'long_term_investor_score': 50
            }
    
    def calculate_data_quality_score(self, indicators: Dict) -> int:
        """Calculate data quality score based on available indicators"""
        try:
            required_indicators = [
                'rsi_14', 'stoch_k', 'cci_20', 'macd_line', 'ema_20', 
                'ema_50', 'ema_100', 'atr_14', 'adx_14'
            ]
            
            available_count = 0
            for indicator in required_indicators:
                if indicators.get(indicator) is not None:
                    available_count += 1
            
            # Calculate percentage
            quality_score = int((available_count / len(required_indicators)) * 100)
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating data quality score: {e}")
            return 50
    
    def calculate_technical_score(self, ticker: str, calculation_date: date) -> Dict:
        """Calculate complete technical score for a ticker"""
        try:
            # Get latest indicators
            indicators = self.get_latest_indicators(ticker)
            if not indicators:
                return {
                    'calculation_status': 'failed',
                    'error_message': 'No indicator data available',
                    'data_quality_score': 0
                }
            
            # Get volume data
            volume_data = self.get_volume_data(ticker)
            if volume_data:
                indicators['volume_ratio'] = volume_data['volume_ratio']
            else:
                indicators['volume_ratio'] = 1.0
            
            # Calculate signal strengths
            signal_strengths = self.calculate_signal_strengths(indicators)
            
            # Calculate composite scores
            composite_scores = self.calculate_composite_scores(signal_strengths)
            
            # Calculate data quality score
            data_quality_score = self.calculate_data_quality_score(indicators)
            
            # Determine calculation status
            if data_quality_score >= 80:
                calculation_status = 'success'
            elif data_quality_score >= 50:
                calculation_status = 'partial'
            else:
                calculation_status = 'failed'
            
            # Compile final result
            result = {
                **signal_strengths,
                **composite_scores,
                'volume_ratio': indicators.get('volume_ratio', 1.0),
                'data_quality_score': data_quality_score,
                'calculation_status': calculation_status,
                'error_message': None
            }
            
            logger.info(f"Calculated technical score for {ticker}: {composite_scores}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating technical score for {ticker}: {e}")
            return {
                'calculation_status': 'failed',
                'error_message': str(e),
                'data_quality_score': 0
            }
    
    def process_ticker(self, ticker: str, calculation_date: date) -> bool:
        """Process a single ticker and store the result"""
        try:
            # Calculate score
            score_data = self.calculate_technical_score(ticker, calculation_date)
            
            # Store in database
            success = self.score_db.store_technical_score(ticker, calculation_date, score_data)
            
            if success:
                logger.info(f"Stored technical score for {ticker}")
            else:
                logger.error(f"Failed to store technical score for {ticker}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing technical score for {ticker}: {e}")
            return False 