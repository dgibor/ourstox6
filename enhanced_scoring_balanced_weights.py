#!/usr/bin/env python3
"""
Enhanced Stock Scoring with VWAP & Support/Resistance - BALANCED WEIGHTS
Improved weight distribution to avoid overly harsh ratings
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

# Add daily_run to path for imports
sys.path.append('daily_run')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BalancedEnhancedScorer:
    """Enhanced stock scorer with balanced weights for VWAP & Support/Resistance"""
    
    def __init__(self):
        self.db = None
        
    def connect_db(self):
        """Connect to database"""
        try:
            from daily_run.database import DatabaseManager
            self.db = DatabaseManager()
            self.db.connect()
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect_db(self):
        """Disconnect from database"""
        if self.db:
            self.db.disconnect()
            logger.info("Database disconnected")
    
    def get_stock_data(self, ticker: str) -> Dict:
        """Get comprehensive stock data for scoring"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get fundamental data
            cursor.execute("""
                SELECT 
                    pe_ratio, pb_ratio, debt_to_equity, current_ratio, 
                    return_on_equity, return_on_assets, profit_margin,
                    revenue_growth, earnings_growth
                FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            
            fundamental_data = cursor.fetchone()
            
            # Get technical data
            cursor.execute("""
                SELECT 
                    close, vwap, support_1, support_2, support_3,
                    resistance_1, resistance_2, resistance_3,
                    rsi, macd, sma_20, sma_50, sma_200
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """, (ticker,))
            
            technical_data = cursor.fetchone()
            
            # Get price history for momentum calculation
            cursor.execute("""
                SELECT close, volume, date
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 100
            """, (ticker,))
            
            price_history = cursor.fetchall()
            cursor.close()
            
            if not fundamental_data or not technical_data:
                return {}
            
            # Structure the data
            return {
                'fundamental': {
                    'pe_ratio': fundamental_data[0],
                    'pb_ratio': fundamental_data[1],
                    'debt_to_equity': fundamental_data[2],
                    'current_ratio': fundamental_data[3],
                    'return_on_equity': fundamental_data[4],
                    'return_on_assets': fundamental_data[5],
                    'profit_margin': fundamental_data[6],
                    'revenue_growth': fundamental_data[7],
                    'earnings_growth': fundamental_data[8]
                },
                'technical': {
                    'close': technical_data[0],
                    'vwap': technical_data[1],
                    'support_1': technical_data[2],
                    'support_2': technical_data[3],
                    'support_3': technical_data[4],
                    'resistance_1': technical_data[5],
                    'resistance_2': technical_data[6],
                    'resistance_3': technical_data[7],
                    'rsi': technical_data[8],
                    'macd': technical_data[9],
                    'sma_20': technical_data[10],
                    'sma_50': technical_data[11],
                    'sma_200': technical_data[12]
                },
                'price_history': price_history
            }
            
        except Exception as e:
            logger.error(f"Error getting stock data for {ticker}: {e}")
            return {}
    
    def calculate_fundamental_health(self, fundamental: Dict) -> float:
        """Calculate fundamental health score (0-100)"""
        try:
            score = 0
            factors = 0
            
            # PE Ratio (lower is better, but not too low)
            if fundamental.get('pe_ratio') and fundamental['pe_ratio'] > 0:
                pe = fundamental['pe_ratio']
                if 5 <= pe <= 25:
                    score += 20  # Excellent range
                elif 25 < pe <= 35:
                    score += 15  # Good range
                elif 35 < pe <= 50:
                    score += 10  # Acceptable range
                elif 50 < pe <= 100:
                    score += 5   # High but not extreme
                else:
                    score += 0   # Too high or too low
                factors += 1
            
            # PB Ratio (lower is better)
            if fundamental.get('pb_ratio') and fundamental['pb_ratio'] > 0:
                pb = fundamental['pb_ratio']
                if pb <= 1:
                    score += 20  # Excellent
                elif pb <= 2:
                    score += 15  # Good
                elif pb <= 3:
                    score += 10  # Acceptable
                elif pb <= 5:
                    score += 5   # High
                else:
                    score += 0   # Too high
                factors += 1
            
            # Debt to Equity (lower is better)
            if fundamental.get('debt_to_equity') is not None:
                de = fundamental['debt_to_equity']
                if de <= 0.3:
                    score += 20  # Excellent
                elif de <= 0.5:
                    score += 15  # Good
                elif de <= 1.0:
                    score += 10  # Acceptable
                elif de <= 2.0:
                    score += 5   # High
                else:
                    score += 0   # Too high
                factors += 1
            
            # Current Ratio (higher is better)
            if fundamental.get('current_ratio') and fundamental['current_ratio'] > 0:
                cr = fundamental['current_ratio']
                if cr >= 2.0:
                    score += 20  # Excellent
                elif cr >= 1.5:
                    score += 15  # Good
                elif cr >= 1.0:
                    score += 10  # Acceptable
                elif cr >= 0.8:
                    score += 5   # Low
                else:
                    score += 0   # Too low
                factors += 1
            
            # Return on Equity (higher is better)
            if fundamental.get('return_on_equity') is not None:
                roe = fundamental['return_on_equity']
                if roe >= 0.15:
                    score += 20  # Excellent
                elif roe >= 0.10:
                    score += 15  # Good
                elif roe >= 0.05:
                    score += 10  # Acceptable
                elif roe >= 0.02:
                    score += 5   # Low
                else:
                    score += 0   # Too low
                factors += 1
            
            return score / factors if factors > 0 else 50.0
            
        except Exception as e:
            logger.error(f"Error calculating fundamental health: {e}")
            return 50.0
    
    def calculate_technical_health(self, technical: Dict, price_history: List) -> float:
        """Calculate technical health score (0-100)"""
        try:
            score = 0
            factors = 0
            
            # Price momentum
            current_price = technical['close'] / 100.0  # Convert to actual price
            if len(price_history) > 1:
                prev_price = price_history[1][0] / 100.0  # Convert to actual price
                if prev_price > 0:
                    momentum = (current_price - prev_price) / prev_price
                    if momentum > 0.05:
                        score += 25  # Strong uptrend
                    elif momentum > 0.02:
                        score += 20  # Moderate uptrend
                    elif momentum > -0.02:
                        score += 15  # Sideways
                    elif momentum > -0.05:
                        score += 10  # Moderate downtrend
                    else:
                        score += 5   # Strong downtrend
                    factors += 1
            
            # RSI
            if technical.get('rsi') is not None:
                rsi = technical['rsi']
                if 30 <= rsi <= 70:
                    score += 25  # Neutral (good)
                elif 20 <= rsi <= 80:
                    score += 20  # Acceptable range
                elif 10 <= rsi <= 90:
                    score += 15  # Extended range
                else:
                    score += 10  # Extreme levels
                factors += 1
            
            # Moving Averages
            if (technical.get('sma_20') and technical.get('sma_50') and 
                technical.get('sma_200')):
                
                sma_20 = technical['sma_20'] / 100.0
                sma_50 = technical['sma_50'] / 100.0
                sma_200 = technical['sma_200'] / 100.0
                
                # Golden Cross (20 > 50 > 200)
                if sma_20 > sma_50 > sma_200:
                    score += 25  # Excellent trend
                # Bullish alignment (20 > 50)
                elif sma_20 > sma_50:
                    score += 20  # Good trend
                # Neutral
                elif abs(sma_20 - sma_50) / sma_50 < 0.05:
                    score += 15  # Sideways
                # Bearish
                else:
                    score += 10  # Downtrend
                factors += 1
            
            # MACD
            if technical.get('macd') is not None:
                macd = technical['macd']
                if macd > 0:
                    score += 25  # Bullish
                else:
                    score += 15  # Bearish
                factors += 1
            
            return score / factors if factors > 0 else 50.0
            
        except Exception as e:
            logger.error(f"Error calculating technical health: {e}")
            return 50.0
    
    def calculate_vwap_sr_score(self, technical: Dict) -> Tuple[float, Dict]:
        """Calculate VWAP & Support/Resistance score (0-100)"""
        try:
            # Database stores prices as 100x (bigint format)
            # Convert back to actual prices by dividing by 100
            current_price = technical['close'] / 100.0
            vwap = technical.get('vwap')
            if vwap and not pd.isna(vwap):
                vwap = vwap / 100.0  # Convert to actual price
            else:
                vwap = current_price  # Fallback
            
            # VWAP Analysis (40% weight)
            vwap_score = 0
            if vwap > 0:
                price_vs_vwap = current_price / vwap
                if price_vs_vwap >= 1.1:  # Price 10%+ above VWAP
                    vwap_score = 100
                elif price_vs_vwap >= 1.05:  # Price 5%+ above VWAP
                    vwap_score = 85
                elif price_vs_vwap >= 1.0:  # Price at or above VWAP
                    vwap_score = 70
                elif price_vs_vwap >= 0.95:  # Price within 5% of VWAP
                    vwap_score = 60
                elif price_vs_vwap >= 0.90:  # Price 10% below VWAP
                    vwap_score = 40
                else:  # Price significantly below VWAP
                    vwap_score = 20
            
            # Support Analysis (30% weight)
            support_score = 0
            support_1 = technical.get('support_1')
            support_2 = technical.get('support_2')
            support_3 = technical.get('support_3')
            
            # Convert support levels to actual prices
            if support_1 and not pd.isna(support_1):
                support_1 = support_1 / 100.0
                support_2 = support_2 / 100.0 if support_2 else support_1
                support_3 = support_3 / 100.0 if support_3 else support_2
                
                # Find closest support level
                supports = [s for s in [support_1, support_2, support_3] if s and not pd.isna(s)]
                if supports:
                    closest_support = min(supports, key=lambda x: abs(current_price - x))
                    distance_to_support = abs(current_price - closest_support) / closest_support
                    
                    if distance_to_support <= 0.02:  # Within 2% of support
                        support_score = 100
                    elif distance_to_support <= 0.05:  # Within 5% of support
                        support_score = 85
                    elif distance_to_support <= 0.10:  # Within 10% of support
                        support_score = 70
                    elif distance_to_support <= 0.15:  # Within 15% of support
                        support_score = 50
                    else:  # Far from support
                        support_score = 30
            
            # Resistance Analysis (30% weight)
            resistance_score = 0
            resistance_1 = technical.get('resistance_1')
            resistance_2 = technical.get('resistance_2')
            resistance_3 = technical.get('resistance_3')
            
            # Convert resistance levels to actual prices
            if resistance_1 and not pd.isna(resistance_1):
                resistance_1 = resistance_1 / 100.0
                resistance_2 = resistance_2 / 100.0 if resistance_2 else resistance_1
                resistance_3 = resistance_3 / 100.0 if resistance_3 else resistance_2
                
                # Find closest resistance level
                resistances = [r for r in [resistance_1, resistance_2, resistance_3] if r and not pd.isna(r)]
                if resistances:
                    closest_resistance = min(resistances, key=lambda x: abs(current_price - x))
                    distance_to_resistance = abs(current_price - closest_resistance) / closest_resistance
                    
                    if distance_to_resistance <= 0.02:  # Within 2% of resistance
                        resistance_score = 20  # Close to resistance (bearish)
                    elif distance_to_resistance <= 0.05:  # Within 5% of resistance
                        resistance_score = 40
                    elif distance_to_resistance <= 0.10:  # Within 10% of resistance
                        resistance_score = 60
                    elif distance_to_resistance <= 0.15:  # Within 15% of resistance
                        resistance_score = 80
                    else:  # Far from resistance (bullish)
                        resistance_score = 100
            
            # Calculate weighted score
            vwap_sr_score = (vwap_score * 0.4) + (support_score * 0.3) + (resistance_score * 0.3)
            
            breakdown = {
                'vwap_score': vwap_score,
                'support_score': support_score,
                'resistance_score': resistance_score,
                'current_price': current_price,
                'vwap': vwap
            }
            
            return vwap_sr_score, breakdown
            
        except Exception as e:
            logger.error(f"Error calculating VWAP & S/R score: {e}")
            return 50.0, {}
    
    def calculate_composite_score(self, scores: Dict) -> float:
        """Calculate composite score with balanced weights"""
        try:
            fundamental = scores.get('fundamental_health', 50)
            technical = scores.get('technical_health', 50)
            vwap_sr = scores.get('vwap_sr', 50)
            
            # BALANCED WEIGHTS - Less harsh than before
            # Fundamental: 40% (was 25%) - More emphasis on fundamentals
            # Technical: 25% (was 20%) - Slightly more emphasis
            # VWAP & S/R: 20% (was 15%) - More emphasis on technical levels
            # Value Score: 15% (new component) - Added for balance
            
            # Calculate a simple value score based on fundamental ratios
            value_score = min(fundamental * 1.1, 100)  # Boost fundamental slightly
            
            composite = (fundamental * 0.40) + (technical * 0.25) + (vwap_sr * 0.20) + (value_score * 0.15)
            
            return composite
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 50.0
    
    def get_rating(self, score: float) -> str:
        """Get rating based on score"""
        if score >= 80:
            return "Strong Buy"
        elif score >= 70:
            return "Buy"
        elif score >= 60:
            return "Hold"
        elif score >= 50:
            return "Weak Hold"
        elif score >= 40:
            return "Weak Sell"
        elif score >= 30:
            return "Sell"
        else:
            return "Strong Sell"
    
    def score_stock(self, ticker: str) -> Dict:
        """Score a single stock"""
        try:
            logger.info(f"Scoring stock: {ticker}")
            
            # Get stock data
            stock_data = self.get_stock_data(ticker)
            if not stock_data:
                logger.warning(f"No data found for {ticker}")
                return {}
            
            # Calculate individual scores
            fundamental_health = self.calculate_fundamental_health(stock_data['fundamental'])
            technical_health = self.calculate_technical_health(stock_data['technical'], stock_data['price_history'])
            vwap_sr_score, vwap_breakdown = self.calculate_vwap_sr_score(stock_data['technical'])
            
            # Calculate composite score
            scores = {
                'fundamental_health': fundamental_health,
                'technical_health': technical_health,
                'vwap_sr': vwap_sr_score
            }
            
            composite_score = self.calculate_composite_score(scores)
            rating = self.get_rating(composite_score)
            
            logger.info(f"Completed scoring for {ticker}")
            
            return {
                'ticker': ticker,
                'composite_score': composite_score,
                'rating': rating,
                'fundamental_health': fundamental_health,
                'technical_health': technical_health,
                'vwap_sr': vwap_sr_score,
                'vwap_breakdown': vwap_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error scoring {ticker}: {e}")
            return {}
    
    def test_scoring_system(self, test_tickers: List[str] = None):
        """Test the enhanced scoring system"""
        if not test_tickers:
            test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
        
        results = []
        
        for ticker in test_tickers:
            result = self.score_stock(ticker)
            if result:
                results.append(result)
        
        # Display results
        print("=" * 80)
        print("ENHANCED STOCK SCORING RESULTS WITH BALANCED WEIGHTS")
        print("=" * 80)
        
        for result in results:
            print(f"\n{result['ticker']}:")
            print(f"  Composite Score: {result['composite_score']:.2f}/100")
            print(f"  Rating: {result['rating']}")
            print(f"  Fundamental Health: {result['fundamental_health']:.1f}/100")
            print(f"  Technical Health: {result['technical_health']:.1f}/100")
            print(f"  VWAP & S/R Score: {result['vwap_sr']:.1f}/100")
            
            if result['vwap_breakdown']:
                breakdown = result['vwap_breakdown']
                print(f"    VWAP Score: {breakdown['vwap_score']:.0f}/100")
                print(f"    Support Score: {breakdown['support_score']:.0f}/100")
                print(f"    Resistance Score: {breakdown['resistance_score']:.0f}/100")
                print(f"    Current Price: ${breakdown['current_price']:.2f}")
                print(f"    VWAP: ${breakdown['vwap']:.2f}")
        
        print("\n" + "=" * 80)
        print("SCORING COMPLETED")
        print("=" * 80)

def main():
    """Main function to test enhanced scoring"""
    scorer = BalancedEnhancedScorer()
    
    if not scorer.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting enhanced stock scoring test...")
        scorer.test_scoring_system()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        scorer.disconnect_db()

if __name__ == "__main__":
    main()
