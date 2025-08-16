#!/usr/bin/env python3
"""
DECISIVE Stock Scoring System with VWAP & Support/Resistance
Provides stronger Buy/Sell signals instead of weak holds
Better alignment with AI analyst recommendations
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

class DecisiveStockScorer:
    """Decisive stock scorer with stronger Buy/Sell signals"""
    
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
                    market_cap, revenue_ttm, net_income_ttm, total_assets, total_debt,
                    shareholders_equity, current_assets, current_liabilities, operating_income,
                    cash_and_equivalents, free_cash_flow, shares_outstanding, diluted_eps_ttm,
                    book_value_per_share, ebitda_ttm, enterprise_value
                FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            
            fundamental_data = cursor.fetchone()
            
            # Get technical data
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
        """Calculate fundamental health score (0-100) - MORE DECISIVE"""
        try:
            score = 0
            factors = 0
            
            # Market Cap - More decisive scoring
            if fundamental.get('market_cap') and fundamental['market_cap'] > 0:
                market_cap_b = float(fundamental['market_cap']) / 1e9
                if market_cap_b >= 100:  # Large cap
                    score += 25  # Excellent stability
                elif market_cap_b >= 10:  # Mid cap
                    score += 20  # Good growth potential
                elif market_cap_b >= 1:  # Small cap
                    score += 15  # Higher risk/reward
                else:  # Micro cap
                    score += 10  # Speculative
                factors += 1
            
            # Profitability - More decisive
            if fundamental.get('net_income_ttm') and fundamental['net_income_ttm'] > 0:
                score += 30  # Strong positive signal
                factors += 1
            elif fundamental.get('net_income_ttm') is not None:
                score += 5   # Negative signal
                factors += 1
            
            # Debt to Equity - More decisive
            if (fundamental.get('total_debt') and fundamental.get('shareholders_equity') and 
                fundamental['shareholders_equity'] > 0):
                de = float(fundamental['total_debt']) / float(fundamental['shareholders_equity'])
                if de <= 0.3:
                    score += 25  # Excellent
                elif de <= 0.5:
                    score += 20  # Good
                elif de <= 1.0:
                    score += 15  # Acceptable
                elif de <= 2.0:
                    score += 10  # Concerning
                else:
                    score += 5   # High risk
                factors += 1
            
            # Current Ratio - More decisive
            if (fundamental.get('current_assets') and fundamental.get('current_liabilities') and 
                fundamental['current_liabilities'] > 0):
                cr = float(fundamental['current_assets']) / float(fundamental['current_liabilities'])
                if cr >= 2.0:
                    score += 25  # Excellent
                elif cr >= 1.5:
                    score += 20  # Good
                elif cr >= 1.0:
                    score += 15  # Acceptable
                elif cr >= 0.8:
                    score += 10  # Concerning
                else:
                    score += 5   # High risk
                factors += 1
            
            # Return on Equity - More decisive
            if (fundamental.get('net_income_ttm') and fundamental.get('shareholders_equity') and 
                fundamental['shareholders_equity'] > 0):
                roe = float(fundamental['net_income_ttm']) / float(fundamental['shareholders_equity'])
                if roe >= 0.20:
                    score += 30  # Exceptional
                elif roe >= 0.15:
                    score += 25  # Excellent
                elif roe >= 0.10:
                    score += 20  # Good
                elif roe >= 0.05:
                    score += 15  # Acceptable
                elif roe >= 0.02:
                    score += 10  # Poor
                else:
                    score += 5   # Very poor
                factors += 1
            
            # Additional factors - More decisive
            if fundamental.get('revenue_ttm') and fundamental['revenue_ttm'] > 0:
                score += 15  # Revenue presence
                factors += 1
            
            if fundamental.get('free_cash_flow') and fundamental['free_cash_flow'] > 0:
                score += 20  # Strong cash flow
                factors += 1
            
            final_score = score / factors if factors > 0 else 50.0
            
            # More decisive scoring - wider range
            if final_score >= 80:
                return 95.0  # Boost excellent scores
            elif final_score >= 70:
                return 85.0  # Boost good scores
            elif final_score >= 60:
                return 75.0  # Boost acceptable scores
            elif final_score >= 50:
                return 65.0  # Boost poor scores
            else:
                return 35.0  # Penalize very poor scores
            
        except Exception as e:
            logger.error(f"Error calculating fundamental health: {e}")
            return 50.0
    
    def calculate_technical_health(self, technical: Dict, price_history: List) -> float:
        """Calculate technical health score (0-100) - MORE DECISIVE"""
        try:
            score = 0
            factors = 0
            
            # Price momentum - More decisive
            current_price = technical['close'] / 100.0
            if len(price_history) > 1:
                prev_price = price_history[1][0] / 100.0
                if prev_price > 0:
                    momentum = (current_price - prev_price) / prev_price
                    if momentum > 0.08:  # Strong uptrend
                        score += 35  # Very bullish
                    elif momentum > 0.05:
                        score += 30  # Bullish
                    elif momentum > 0.02:
                        score += 25  # Moderately bullish
                    elif momentum > -0.02:
                        score += 20  # Sideways
                    elif momentum > -0.05:
                        score += 15  # Moderately bearish
                    elif momentum > -0.08:
                        score += 10  # Bearish
                    else:
                        score += 5   # Very bearish
                    factors += 1
            
            # RSI - More decisive
            if technical.get('rsi') is not None:
                rsi = technical['rsi']
                if 40 <= rsi <= 60:
                    score += 30  # Neutral (good)
                elif 30 <= rsi <= 70:
                    score += 25  # Acceptable range
                elif 20 <= rsi <= 80:
                    score += 20  # Extended range
                elif 10 <= rsi <= 90:
                    score += 15  # Extreme levels
                else:
                    score += 10  # Very extreme
                factors += 1
            
            # Moving Averages - More decisive
            if (technical.get('sma_20') and technical.get('sma_50') and 
                technical.get('sma_200')):
                
                sma_20 = technical['sma_20'] / 100.0
                sma_50 = technical['sma_50'] / 100.0
                sma_200 = technical['sma_200'] / 100.0
                
                # Golden Cross (20 > 50 > 200)
                if sma_20 > sma_50 > sma_200:
                    score += 35  # Very bullish
                # Bullish alignment (20 > 50)
                elif sma_20 > sma_50:
                    score += 30  # Bullish
                # Neutral
                elif abs(sma_20 - sma_50) / sma_50 < 0.03:
                    score += 25  # Sideways
                # Bearish
                else:
                    score += 15  # Downtrend
                factors += 1
            
            # MACD - More decisive
            if technical.get('macd') is not None:
                macd = technical['macd']
                if macd > 0:
                    score += 30  # Bullish
                else:
                    score += 15  # Bearish
                factors += 1
            
            final_score = score / factors if factors > 0 else 50.0
            
            # More decisive technical scoring
            if final_score >= 80:
                return 90.0  # Boost excellent technical scores
            elif final_score >= 70:
                return 80.0  # Boost good technical scores
            elif final_score >= 60:
                return 70.0  # Boost acceptable technical scores
            elif final_score >= 50:
                return 60.0  # Boost poor technical scores
            else:
                return 40.0  # Penalize very poor technical scores
            
        except Exception as e:
            logger.error(f"Error calculating technical health: {e}")
            return 50.0
    
    def calculate_vwap_sr_score(self, technical: Dict) -> Tuple[float, Dict]:
        """Calculate VWAP & Support/Resistance score (0-100) - MORE DECISIVE"""
        try:
            current_price = technical['close'] / 100.0
            vwap = technical.get('vwap')
            if vwap and not pd.isna(vwap):
                vwap = vwap / 100.0
            else:
                vwap = current_price
            
            # VWAP Analysis (40% weight) - More decisive
            vwap_score = 0
            if vwap > 0:
                price_vs_vwap = current_price / vwap
                if price_vs_vwap >= 1.15:  # Price 15%+ above VWAP
                    vwap_score = 100  # Very bullish
                elif price_vs_vwap >= 1.10:  # Price 10%+ above VWAP
                    vwap_score = 90   # Bullish
                elif price_vs_vwap >= 1.05:  # Price 5%+ above VWAP
                    vwap_score = 80   # Moderately bullish
                elif price_vs_vwap >= 1.0:  # Price at or above VWAP
                    vwap_score = 70   # Neutral
                elif price_vs_vwap >= 0.95:  # Price within 5% of VWAP
                    vwap_score = 60   # Slightly bearish
                elif price_vs_vwap >= 0.90:  # Price 10% below VWAP
                    vwap_score = 40   # Bearish
                else:  # Price significantly below VWAP
                    vwap_score = 20   # Very bearish
            
            # Support Analysis (30% weight) - More decisive
            support_score = 0
            support_1 = technical.get('support_1')
            support_2 = technical.get('support_2')
            support_3 = technical.get('support_3')
            
            if support_1 and not pd.isna(support_1):
                support_1 = support_1 / 100.0
                support_2 = support_2 / 100.0 if support_2 else support_1
                support_3 = support_3 / 100.0 if support_3 else support_2
                
                supports = [s for s in [support_1, support_2, support_3] if s and not pd.isna(s)]
                if supports:
                    closest_support = min(supports, key=lambda x: abs(current_price - x))
                    distance_to_support = abs(current_price - closest_support) / closest_support
                    
                    if distance_to_support <= 0.01:  # Within 1% of support
                        support_score = 100  # Very strong support
                    elif distance_to_support <= 0.03:  # Within 3% of support
                        support_score = 90   # Strong support
                    elif distance_to_support <= 0.05:  # Within 5% of support
                        support_score = 80   # Good support
                    elif distance_to_support <= 0.10:  # Within 10% of support
                        support_score = 70   # Moderate support
                    elif distance_to_support <= 0.15:  # Within 15% of support
                        support_score = 50   # Weak support
                    else:  # Far from support
                        support_score = 30   # No support nearby
            
            # Resistance Analysis (30% weight) - More decisive
            resistance_score = 0
            resistance_1 = technical.get('resistance_1')
            resistance_2 = technical.get('resistance_2')
            resistance_3 = technical.get('resistance_3')
            
            if resistance_1 and not pd.isna(resistance_1):
                resistance_1 = resistance_1 / 100.0
                resistance_2 = resistance_2 / 100.0 if resistance_2 else resistance_1
                resistance_3 = resistance_3 / 100.0 if resistance_3 else resistance_2
                
                resistances = [r for r in [resistance_1, resistance_2, resistance_3] if r and not pd.isna(r)]
                if resistances:
                    closest_resistance = min(resistances, key=lambda x: abs(current_price - x))
                    distance_to_resistance = abs(current_price - closest_resistance) / closest_resistance
                    
                    if distance_to_resistance <= 0.01:  # Within 1% of resistance
                        resistance_score = 10   # Very close to resistance (very bearish)
                    elif distance_to_resistance <= 0.03:  # Within 3% of resistance
                        resistance_score = 20   # Close to resistance (bearish)
                    elif distance_to_resistance <= 0.05:  # Within 5% of resistance
                        resistance_score = 30   # Near resistance
                    elif distance_to_resistance <= 0.10:  # Within 10% of resistance
                        resistance_score = 50   # Moderate distance
                    elif distance_to_resistance <= 0.15:  # Within 15% of resistance
                        resistance_score = 70   # Good distance
                    else:  # Far from resistance (bullish)
                        resistance_score = 100  # Clear path to resistance
            
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
        """Calculate composite score with DECISIVE weights"""
        try:
            fundamental = scores.get('fundamental_health', 50)
            technical = scores.get('technical_health', 50)
            vwap_sr = scores.get('vwap_sr', 50)
            
            # DECISIVE WEIGHTS - More emphasis on technical factors
            # Fundamental: 30% - Important but not overwhelming
            # Technical: 30% - Equal weight for momentum and trends
            # VWAP & S/R: 40% - Heavy emphasis on technical levels for decisiveness
            
            composite = (fundamental * 0.30) + (technical * 0.30) + (vwap_sr * 0.40)
            
            return composite
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 50.0
    
    def get_rating(self, score: float) -> str:
        """Get rating based on score - MORE DECISIVE THRESHOLDS"""
        if score >= 85:
            return "Strong Buy"
        elif score >= 75:
            return "Buy"
        elif score >= 65:
            return "Hold"
        elif score >= 55:
            return "Weak Hold"
        elif score >= 45:
            return "Weak Sell"
        elif score >= 35:
            return "Sell"
        else:
            return "Strong Sell"
    
    def score_stock(self, ticker: str) -> Dict:
        """Score a single stock"""
        try:
            logger.info(f"Scoring stock: {ticker}")
            
            stock_data = self.get_stock_data(ticker)
            if not stock_data:
                logger.warning(f"No data found for {ticker}")
                return {}
            
            fundamental_health = self.calculate_fundamental_health(stock_data['fundamental'])
            technical_health = self.calculate_technical_health(stock_data['technical'], stock_data['price_history'])
            vwap_sr_score, vwap_breakdown = self.calculate_vwap_sr_score(stock_data['technical'])
            
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
        """Test the decisive scoring system"""
        if not test_tickers:
            # 20 tickers distributed across various sectors
            test_tickers = [
                # Technology
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'AMD', 'INTC',
                # Consumer Discretionary
                'TSLA', 'NFLX', 'HD', 'MCD',
                # Healthcare
                'JNJ', 'PFE', 'UNH',
                # Financial
                'JPM', 'BAC', 'WFC',
                # Energy
                'XOM', 'CVX'
            ]
        
        results = []
        
        for ticker in test_tickers:
            result = self.score_stock(ticker)
            if result:
                results.append(result)
        
        # Display results
        print("=" * 100)
        print("DECISIVE STOCK SCORING SYSTEM RESULTS - 20 TICKERS ACROSS VARIOUS SECTORS")
        print("=" * 100)
        
        # Group by rating for better analysis
        rating_groups = {}
        for result in results:
            rating = result['rating']
            if rating not in rating_groups:
                rating_groups[rating] = []
            rating_groups[rating].append(result)
        
        # Display by rating groups
        for rating in ['Strong Buy', 'Buy', 'Hold', 'Weak Hold', 'Weak Sell', 'Sell', 'Strong Sell']:
            if rating in rating_groups:
                print(f"\n{'='*80}")
                print(f"{rating.upper()} RATINGS ({len(rating_groups[rating])} stocks)")
                print(f"{'='*80}")
                
                for result in rating_groups[rating]:
                    print(f"\n{result['ticker']}:")
                    print(f"  Composite Score: {result['composite_score']:.2f}/100")
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
        
        # Summary statistics
        print(f"\n{'='*100}")
        print("SCORING SYSTEM SUMMARY")
        print(f"{'='*100}")
        
        total_stocks = len(results)
        rating_counts = {rating: len(rating_groups.get(rating, [])) for rating in 
                        ['Strong Buy', 'Buy', 'Hold', 'Weak Hold', 'Weak Sell', 'Sell', 'Strong Sell']}
        
        print(f"\n📊 RATING DISTRIBUTION:")
        for rating, count in rating_counts.items():
            percentage = (count / total_stocks) * 100 if total_stocks > 0 else 0
            print(f"   {rating}: {count} stocks ({percentage:.1f}%)")
        
        # Market outlook analysis
        bullish_ratings = rating_counts['Strong Buy'] + rating_counts['Buy'] + rating_counts['Hold']
        neutral_ratings = rating_counts['Weak Hold']
        bearish_ratings = rating_counts['Weak Sell'] + rating_counts['Sell'] + rating_counts['Strong Sell']
        
        print(f"\n🎯 MARKET OUTLOOK ANALYSIS:")
        print(f"   Total Stocks Analyzed: {total_stocks}")
        print(f"   Bullish Ratings: {bullish_ratings} ({bullish_ratings/total_stocks*100:.1f}%)")
        print(f"   Neutral Ratings: {neutral_ratings} ({neutral_ratings/total_stocks*100:.1f}%)")
        print(f"   Bearish Ratings: {bearish_ratings} ({bearish_ratings/total_stocks*100:.1f}%)")
        
        print(f"\n✅ DECISIVE SYSTEM ASSESSMENT:")
        if bullish_ratings > bearish_ratings:
            print(f"   System shows a BULLISH bias - {bullish_ratings} vs {bearish_ratings} bearish")
        elif bearish_ratings > bullish_ratings:
            print(f"   System shows a BEARISH bias - {bearish_ratings} vs {bullish_ratings} bullish")
        else:
            print(f"   System shows a NEUTRAL bias - balanced outlook")
        
        print(f"\n🔍 KEY IMPROVEMENTS:")
        print(f"   • More decisive scoring thresholds (85+ for Strong Buy)")
        print(f"   • Enhanced VWAP & S/R weight (40% of total score)")
        print(f"   • Wider scoring ranges for better differentiation")
        print(f"   • Technical factors given equal weight to fundamentals")
        
        print(f"\n{'='*100}")
        print("DECISIVE SCORING COMPLETED")
        print(f"{'='*100}")

def main():
    """Main function to test decisive scoring"""
    scorer = DecisiveStockScorer()
    
    if not scorer.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting DECISIVE stock scoring test...")
        scorer.test_scoring_system()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        scorer.disconnect_db()

if __name__ == "__main__":
    main()
