#!/usr/bin/env python3
"""
FINAL Enhanced Stock Scoring with VWAP & Support/Resistance - OPTIMIZED
Better fundamental scoring and balanced weights for realistic ratings
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

class FinalOptimizedScorer:
    """Final optimized stock scorer with better fundamental scoring"""
    
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
        """Get comprehensive stock data for scoring using correct column names"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get fundamental data from stocks table (using actual column names)
            cursor.execute("""
                SELECT 
                    market_cap, revenue_ttm, net_income_ttm, total_assets, total_debt,
                    shareholders_equity, current_assets, current_liabilities, operating_income,
                    cash_and_equivalents, free_cash_flow, shares_outstanding, diluted_eps_ttm,
                    book_value_per_share, ebitda_ttm, enterprise_value
                FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            
            fundamental_data = cursor.fetchone()
            
            # Get technical data from daily_charts table (using actual column names)
            cursor.execute("""
                SELECT 
                    close, vwap, support_1, support_2, support_3,
                    resistance_1, resistance_2, resistance_3,
                    rsi_14, macd_line, ema_20, ema_50, ema_200
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
                    'market_cap': fundamental_data[0],
                    'revenue_ttm': fundamental_data[1],
                    'net_income_ttm': fundamental_data[2],
                    'total_assets': fundamental_data[3],
                    'total_debt': fundamental_data[4],
                    'shareholders_equity': fundamental_data[5],
                    'current_assets': fundamental_data[6],
                    'current_liabilities': fundamental_data[7],
                    'operating_income': fundamental_data[8],
                    'cash_and_equivalents': fundamental_data[9],
                    'free_cash_flow': fundamental_data[10],
                    'shares_outstanding': fundamental_data[11],
                    'diluted_eps_ttm': fundamental_data[12],
                    'book_value_per_share': fundamental_data[13],
                    'ebitda_ttm': fundamental_data[14],
                    'enterprise_value': fundamental_data[15]
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
        """Calculate fundamental health score (0-100) with better scoring logic"""
        try:
            score = 0
            factors = 0
            
            # Base score for having fundamental data (encourages data completeness)
            base_score = 30
            score += base_score
            factors += 1
            
            # Market Cap (higher is generally better for stability)
            if fundamental.get('market_cap') and fundamental['market_cap'] > 0:
                market_cap_b = float(fundamental['market_cap']) / 1e9  # Convert to billions
                if market_cap_b >= 100:  # Large cap
                    score += 15
                elif market_cap_b >= 10:  # Mid cap
                    score += 12
                elif market_cap_b >= 1:  # Small cap
                    score += 10
                else:  # Micro cap
                    score += 8
                factors += 1
            
            # Profitability (Net Income) - More lenient scoring
            if fundamental.get('net_income_ttm') and fundamental['net_income_ttm'] > 0:
                score += 20  # Profitable company
                factors += 1
            elif fundamental.get('net_income_ttm') is not None:
                score += 10   # Unprofitable but data available (more lenient)
                factors += 1
            
            # Debt to Equity (lower is better) - More lenient scoring
            if (fundamental.get('total_debt') and fundamental.get('shareholders_equity') and 
                fundamental['shareholders_equity'] > 0):
                de = float(fundamental['total_debt']) / float(fundamental['shareholders_equity'])
                if de <= 0.3:
                    score += 15  # Excellent
                elif de <= 0.5:
                    score += 12  # Good
                elif de <= 1.0:
                    score += 10  # Acceptable
                elif de <= 2.0:
                    score += 8   # High but acceptable
                else:
                    score += 5   # Too high but still scored
                factors += 1
            
            # Current Ratio (higher is better) - More lenient scoring
            if (fundamental.get('current_assets') and fundamental.get('current_liabilities') and 
                fundamental['current_liabilities'] > 0):
                cr = float(fundamental['current_assets']) / float(fundamental['current_liabilities'])
                if cr >= 2.0:
                    score += 15  # Excellent
                elif cr >= 1.5:
                    score += 12  # Good
                elif cr >= 1.0:
                    score += 10  # Acceptable
                elif cr >= 0.8:
                    score += 8   # Low but acceptable
                else:
                    score += 5   # Too low but still scored
                factors += 1
            
            # Return on Equity (higher is better) - More lenient scoring
            if (fundamental.get('net_income_ttm') and fundamental.get('shareholders_equity') and 
                fundamental['shareholders_equity'] > 0):
                roe = float(fundamental['net_income_ttm']) / float(fundamental['shareholders_equity'])
                if roe >= 0.15:
                    score += 15  # Excellent
                elif roe >= 0.10:
                    score += 12  # Good
                elif roe >= 0.05:
                    score += 10  # Acceptable
                elif roe >= 0.02:
                    score += 8   # Low but acceptable
                else:
                    score += 5   # Very low but still scored
                factors += 1
            
            # Revenue Growth (if available)
            if fundamental.get('revenue_ttm') and fundamental['revenue_ttm'] > 0:
                score += 10  # Bonus for having revenue data
                factors += 1
            
            # Free Cash Flow (if available)
            if fundamental.get('free_cash_flow') and fundamental['free_cash_flow'] > 0:
                score += 10  # Bonus for positive free cash flow
                factors += 1
            
            final_score = score / factors if factors > 0 else 50.0
            
            # Ensure minimum score of 40 for companies with data
            return max(final_score, 40.0)
            
        except Exception as e:
            logger.error(f"Error calculating fundamental health: {e}")
            return 50.0
    
    def calculate_technical_health(self, technical: Dict, price_history: List) -> float:
        """Calculate technical health score (0-100) with better scoring"""
        try:
            score = 0
            factors = 0
            
            # Base score for having technical data
            base_score = 25
            score += base_score
            factors += 1
            
            # Price momentum
            current_price = technical['close'] / 100.0  # Convert to actual price
            if len(price_history) > 1:
                prev_price = price_history[1][0] / 100.0  # Convert to actual price
                if prev_price > 0:
                    momentum = (current_price - prev_price) / prev_price
                    if momentum > 0.05:
                        score += 20  # Strong uptrend
                    elif momentum > 0.02:
                        score += 18  # Moderate uptrend
                    elif momentum > -0.02:
                        score += 15  # Sideways
                    elif momentum > -0.05:
                        score += 12  # Moderate downtrend
                    else:
                        score += 10  # Strong downtrend
                    factors += 1
            
            # RSI
            if technical.get('rsi') is not None:
                rsi = technical['rsi']
                if 30 <= rsi <= 70:
                    score += 20  # Neutral (good)
                elif 20 <= rsi <= 80:
                    score += 18  # Acceptable range
                elif 10 <= rsi <= 90:
                    score += 15  # Extended range
                else:
                    score += 12  # Extreme levels
                factors += 1
            
            # Moving Averages
            if (technical.get('sma_20') and technical.get('sma_50') and 
                technical.get('sma_200')):
                
                sma_20 = technical['sma_20'] / 100.0
                sma_50 = technical['sma_50'] / 100.0
                sma_200 = technical['sma_200'] / 100.0
                
                # Golden Cross (20 > 50 > 200)
                if sma_20 > sma_50 > sma_200:
                    score += 20  # Excellent trend
                # Bullish alignment (20 > 50)
                elif sma_20 > sma_50:
                    score += 18  # Good trend
                # Neutral
                elif abs(sma_20 - sma_50) / sma_50 < 0.05:
                    score += 15  # Sideways
                # Bearish
                else:
                    score += 12  # Downtrend
                factors += 1
            
            # MACD
            if technical.get('macd') is not None:
                macd = technical['macd']
                if macd > 0:
                    score += 20  # Bullish
                else:
                    score += 15  # Bearish
                factors += 1
            
            final_score = score / factors if factors > 0 else 50.0
            
            # Ensure minimum score of 35 for companies with technical data
            return max(final_score, 35.0)
            
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
        """Calculate composite score with FINAL OPTIMIZED weights"""
        try:
            fundamental = scores.get('fundamental_health', 50)
            technical = scores.get('technical_health', 50)
            vwap_sr = scores.get('vwap_sr', 50)
            
            # FINAL OPTIMIZED WEIGHTS - Balanced for realistic ratings
            # Fundamental: 35% - Strong emphasis on fundamentals
            # Technical: 25% - Balanced technical analysis
            # VWAP & S/R: 25% - Strong emphasis on technical levels
            # Market Sentiment: 15% - Additional factor for balance
            
            # Calculate market sentiment based on technical and VWAP scores
            market_sentiment = (technical + vwap_sr) / 2
            
            composite = (fundamental * 0.35) + (technical * 0.25) + (vwap_sr * 0.25) + (market_sentiment * 0.15)
            
            return composite
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 50.0
    
    def get_rating(self, score: float) -> str:
        """Get rating based on score with more balanced thresholds"""
        if score >= 75:
            return "Strong Buy"
        elif score >= 65:
            return "Buy"
        elif score >= 55:
            return "Hold"
        elif score >= 45:
            return "Weak Hold"
        elif score >= 35:
            return "Weak Sell"
        elif score >= 25:
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
        print("FINAL ENHANCED STOCK SCORING RESULTS - OPTIMIZED WEIGHTS & SCORING")
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
        print("FINAL SCORING COMPLETED")
        print("=" * 80)

def main():
    """Main function to test enhanced scoring"""
    scorer = FinalOptimizedScorer()
    
    if not scorer.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting FINAL enhanced stock scoring test...")
        scorer.test_scoring_system()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        scorer.disconnect_db()

if __name__ == "__main__":
    main()
