#!/usr/bin/env python3
"""
BALANCED REALISTIC STOCK SCORING SYSTEM
This script is designed to produce realistic distributions of Buy, Hold, and Weak Hold ratings
by using moderate base scores and balanced weights that align with market reality.
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BalancedRealisticScoring:
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
            
    def get_stock_data(self, ticker):
        """Fetch comprehensive stock data for scoring"""
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
            cursor.close()
            
            if not fundamental_data or not technical_data:
                logger.warning(f"No data found for {ticker}")
                return None
                
            # Combine data into a single row-like object
            combined_data = {
                'ticker': ticker,
                'company_name': ticker,  # We'll use ticker as company name for now
                'sector': 'Technology',  # Default sector
                'industry': 'Technology',  # Default industry
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
                'enterprise_value': fundamental_data[15],
                'vwap': technical_data[1],
                'support_1': technical_data[2],
                'support_2': technical_data[3],
                'support_3': technical_data[4],
                'resistance_1': technical_data[5],
                'resistance_2': technical_data[6],
                'resistance_3': technical_data[7],
                'rsi_14': technical_data[8],
                'macd_line': technical_data[9],
                'macd_signal': technical_data[9],  # Use same as macd_line for now
                'ema_20': technical_data[10],
                'ema_50': technical_data[11],
                'sma_200': technical_data[12],
                'volume': 1000000,  # Default volume
                'close': technical_data[0],
                'current_price': technical_data[0]  # Use close as current price
            }
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None
            
    def is_price_data_valid(self, data):
        """Validate price data quality"""
        try:
            current_price = data['current_price'] / 100.0
            close_price = data['close'] / 100.0
            
            # Check for unrealistic prices
            if current_price < 1.0 or current_price > 10000.0:
                logger.warning(f"Price data for {data['ticker']} appears corrupted: ${current_price:.2f}")
                return False
                
            if close_price < 1.0 or close_price > 10000.0:
                logger.warning(f"Price data for {data['ticker']} appears corrupted: ${close_price:.2f}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating price data for {data['ticker']}: {e}")
            return False
            
    def calculate_fundamental_health(self, data):
        """Calculate fundamental health score with BALANCED base scores"""
        try:
            score = 0
            factors = 0
            
            # BALANCED BASE SCORE - Start with 45 instead of 70
            base_score = 45
            
            # Market Cap (0-15 points)
            if pd.notna(data['market_cap']) and data['market_cap'] > 0:
                market_cap = data['market_cap']
                if market_cap > 1000000000000:  # > $1T
                    score += 15
                elif market_cap > 100000000000:  # > $100B
                    score += 12
                elif market_cap > 10000000000:  # > $10B
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Revenue TTM (0-15 points)
            if pd.notna(data['revenue_ttm']) and data['revenue_ttm'] > 0:
                revenue = data['revenue_ttm']
                if revenue > 100000000000:  # > $100B
                    score += 15
                elif revenue > 10000000000:  # > $10B
                    score += 12
                elif revenue > 1000000000:  # > $1B
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Net Income TTM (0-15 points)
            if pd.notna(data['net_income_ttm']):
                net_income = data['net_income_ttm']
                if net_income > 10000000000:  # > $10B
                    score += 15
                elif net_income > 1000000000:  # > $1B
                    score += 12
                elif net_income > 0:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Debt to Equity (0-15 points)
            if pd.notna(data['total_debt']) and pd.notna(data['shareholders_equity']) and data['shareholders_equity'] > 0:
                dte = data['total_debt'] / data['shareholders_equity']
                if dte < 0.5:
                    score += 15
                elif dte < 1.0:
                    score += 12
                elif dte < 2.0:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Return on Equity (0-15 points)
            if pd.notna(data['net_income_ttm']) and pd.notna(data['shareholders_equity']) and data['shareholders_equity'] > 0:
                roe = (data['net_income_ttm'] / data['shareholders_equity']) * 100
                if roe > 20:
                    score += 15
                elif roe > 15:
                    score += 12
                elif roe > 10:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Free Cash Flow (0-15 points)
            if pd.notna(data['free_cash_flow']):
                fcf = data['free_cash_flow']
                if fcf > 10000000000:  # > $10B
                    score += 15
                elif fcf > 1000000000:  # > $1B
                    score += 12
                elif fcf > 0:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # EBITDA TTM (0-10 points)
            if pd.notna(data['ebitda_ttm']):
                ebitda = data['ebitda_ttm']
                if ebitda > 10000000000:  # > $10B
                    score += 10
                elif ebitda > 1000000000:  # > $1B
                    score += 8
                elif ebitda > 0:
                    score += 5
                else:
                    score += 0
                factors += 1
                
            if factors > 0:
                # BALANCED: Add base score to calculated score
                final_score = base_score + (score / factors)
                return min(final_score, 100)
            else:
                # BALANCED: Return base score even with no data
                return base_score
                
        except Exception as e:
            logger.error(f"Error calculating fundamental health: {e}")
            return 45  # BALANCED: Return base score on error
            
    def calculate_technical_health(self, data):
        """Calculate technical health score with BALANCED base scores"""
        try:
            score = 0
            factors = 0
            
            # BALANCED BASE SCORE - Start with 40 instead of 65
            base_score = 40
            
            # RSI (0-20 points)
            if pd.notna(data['rsi_14']):
                rsi = data['rsi_14']
                if 30 <= rsi <= 70:
                    score += 20
                elif 25 <= rsi <= 75:
                    score += 15
                elif 20 <= rsi <= 80:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # MACD (0-20 points)
            if pd.notna(data['macd_line']) and pd.notna(data['macd_signal']):
                macd_line = data['macd_line']
                macd_signal = data['macd_signal']
                if macd_line > macd_signal:
                    score += 20
                else:
                    score += 10
                factors += 1
                
            # Moving Averages (0-20 points)
            if pd.notna(data['ema_20']) and pd.notna(data['ema_50']):
                ema_20 = data['ema_20'] / 100.0
                ema_50 = data['ema_50'] / 100.0
                current_price = data['current_price'] / 100.0
                
                if current_price > ema_20 > ema_50:
                    score += 20
                elif current_price > ema_20:
                    score += 15
                elif current_price > ema_50:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Volume (0-20 points)
            if pd.notna(data['volume']) and data['volume'] > 0:
                # Assume moderate volume is good
                score += 15
                factors += 1
                
            # Price vs 200 SMA (0-20 points)
            if pd.notna(data['sma_200']):
                sma_200 = data['sma_200'] / 100.0
                current_price = data['current_price'] / 100.0
                
                if current_price > sma_200:
                    score += 20
                else:
                    score += 10
                factors += 1
                
            if factors > 0:
                # BALANCED: Add base score to calculated score
                final_score = base_score + (score / factors)
                return min(final_score, 100)
            else:
                # BALANCED: Return base score even with no data
                return base_score
                
        except Exception as e:
            logger.error(f"Error calculating technical health: {e}")
            return 40  # BALANCED: Return base score on error
            
    def calculate_vwap_sr_score(self, data):
        """Calculate VWAP & Support/Resistance score"""
        try:
            current_price = data['current_price'] / 100.0
            vwap = data['vwap'] / 100.0 if pd.notna(data['vwap']) else current_price
            
            # VWAP Analysis (40% weight)
            vwap_score = 0
            if pd.notna(data['vwap']):
                price_vs_vwap = current_price / vwap
                if price_vs_vwap > 1.05:  # Price 5% above VWAP
                    vwap_score = 100
                elif price_vs_vwap > 1.02:  # Price 2% above VWAP
                    vwap_score = 85
                elif price_vs_vwap > 0.98:  # Price near VWAP
                    vwap_score = 70
                elif price_vs_vwap > 0.95:  # Price 2% below VWAP
                    vwap_score = 50
                else:  # Price significantly below VWAP
                    vwap_score = 30
            else:
                vwap_score = 70  # Neutral if no VWAP data
                
            # Support Analysis (30% weight)
            support_score = 0
            if pd.notna(data['support_1']):
                support_1 = data['support_1'] / 100.0
                distance_to_support = (current_price - support_1) / current_price
                
                if distance_to_support <= 0.02:  # Within 2% of support
                    support_score = 100
                elif distance_to_support <= 0.05:  # Within 5% of support
                    support_score = 85
                elif distance_to_support <= 0.10:  # Within 10% of support
                    support_score = 70
                elif distance_to_support <= 0.15:  # Within 15% of support
                    support_score = 50
                else:  # More than 15% above support
                    support_score = 30
            else:
                support_score = 70  # Neutral if no support data
                
            # Resistance Analysis (30% weight)
            resistance_score = 0
            if pd.notna(data['resistance_1']):
                resistance_1 = data['resistance_1'] / 100.0
                distance_to_resistance = (resistance_1 - current_price) / current_price
                
                if distance_to_resistance <= 0.02:  # Within 2% of resistance
                    resistance_score = 20
                elif distance_to_resistance <= 0.05:  # Within 5% of resistance
                    resistance_score = 40
                elif distance_to_resistance <= 0.10:  # Within 10% of resistance
                    resistance_score = 60
                elif distance_to_resistance <= 0.15:  # Within 15% of resistance
                    resistance_score = 80
                else:  # More than 15% below resistance
                    resistance_score = 100
            else:
                resistance_score = 70  # Neutral if no resistance data
                
            # Calculate weighted score
            vwap_sr_score = (vwap_score * 0.4) + (support_score * 0.3) + (resistance_score * 0.3)
            
            return {
                'total_score': vwap_sr_score,
                'vwap_score': vwap_score,
                'support_score': support_score,
                'resistance_score': resistance_score,
                'current_price': current_price,
                'vwap': vwap
            }
            
        except Exception as e:
            logger.error(f"Error calculating VWAP & S/R score: {e}")
            return {
                'total_score': 70,
                'vwap_score': 70,
                'support_score': 70,
                'resistance_score': 70,
                'current_price': 0,
                'vwap': 0
            }
            
    def calculate_composite_score(self, fundamental_health, technical_health, vwap_sr_score):
        """Calculate composite score with BALANCED weights"""
        try:
            # BALANCED WEIGHTS designed to produce realistic distributions
            fundamental_weight = 0.30      # 30%
            technical_weight = 0.25        # 25%
            vwap_sr_weight = 0.30         # 30% - Balanced emphasis
            market_sentiment_weight = 0.15 # 15% - Reduced component
            
            # Market Sentiment Score (derived from fundamental + technical)
            market_sentiment = (fundamental_health + technical_health) / 2
            
            # Calculate composite score
            composite_score = (
                (fundamental_health * fundamental_weight) +
                (technical_health * technical_weight) +
                (vwap_sr_score * vwap_sr_weight) +
                (market_sentiment * market_sentiment_weight)
            )
            
            return min(composite_score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 0
            
    def get_rating(self, composite_score):
        """Get rating based on BALANCED thresholds"""
        try:
            if composite_score >= 80:
                return "Strong Buy"
            elif composite_score >= 70:
                return "Buy"
            elif composite_score >= 60:
                return "Hold"
            elif composite_score >= 50:
                return "Weak Hold"
            elif composite_score >= 40:
                return "Weak Sell"
            elif composite_score >= 30:
                return "Sell"
            else:
                return "Strong Sell"
                
        except Exception as e:
            logger.error(f"Error getting rating: {e}")
            return "Hold"
            
    def score_stock(self, ticker):
        """Score a single stock"""
        try:
            logger.info(f"Scoring stock: {ticker}")
            
            # Get stock data
            data = self.get_stock_data(ticker)
            if data is None:
                logger.warning(f"Skipping {ticker} due to missing data")
                return None
                
            # Validate price data
            if not self.is_price_data_valid(data):
                logger.warning(f"Skipping {ticker} due to data quality issues")
                return None
                
            # Calculate individual scores
            fundamental_health = self.calculate_fundamental_health(data)
            technical_health = self.calculate_technical_health(data)
            vwap_sr_data = self.calculate_vwap_sr_score(data)
            vwap_sr_score = vwap_sr_data['total_score']
            
            # Calculate composite score
            composite_score = self.calculate_composite_score(
                fundamental_health, technical_health, vwap_sr_score
            )
            
            # Get rating
            rating = self.get_rating(composite_score)
            
            # Prepare result
            result = {
                'ticker': ticker,
                'company_name': data['company_name'],
                'sector': data['sector'],
                'composite_score': composite_score,
                'rating': rating,
                'fundamental_health': fundamental_health,
                'technical_health': technical_health,
                'vwap_sr_score': vwap_sr_score,
                'vwap_data': vwap_sr_data
            }
            
            logger.info(f"Completed scoring for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring {ticker}: {e}")
            return None
            
    def run_scoring_test(self, tickers):
        """Run scoring test on multiple tickers"""
        try:
            logger.info("Starting BALANCED REALISTIC stock scoring test...")
            
            results = []
            skipped = []
            
            for ticker in tickers:
                result = self.score_stock(ticker)
                if result:
                    results.append(result)
                else:
                    skipped.append(ticker)
                    
            # Analyze results
            self.analyze_results(results, skipped)
            
        except Exception as e:
            logger.error(f"Error running scoring test: {e}")
            
    def analyze_results(self, results, skipped):
        """Analyze and display scoring results"""
        try:
            print("\n" + "="*100)
            print("BALANCED REALISTIC STOCK SCORING SYSTEM RESULTS - VALID DATA STOCKS ONLY")
            print("="*100 + "\n")
            
            if not results:
                print("No valid results to display.")
                return
                
            # Group by rating
            ratings = {}
            for result in results:
                rating = result['rating']
                if rating not in ratings:
                    ratings[rating] = []
                ratings[rating].append(result)
                
            # Display results by rating
            for rating in ['Strong Buy', 'Buy', 'Hold', 'Weak Hold', 'Weak Sell', 'Sell', 'Strong Sell']:
                if rating in ratings:
                    print("="*80)
                    print(f"{rating.upper()} RATINGS ({len(ratings[rating])} stocks)")
                    print("="*80 + "\n")
                    
                    for result in ratings[rating]:
                        print(f"{result['ticker']}:")
                        print(f"  Composite Score: {result['composite_score']:.2f}/100")
                        print(f"  Fundamental Health: {result['fundamental_health']:.1f}/100")
                        print(f"  Technical Health: {result['technical_health']:.1f}/100")
                        print(f"  VWAP & S/R Score: {result['vwap_sr_score']:.1f}/100")
                        print(f"    VWAP Score: {result['vwap_data']['vwap_score']:.0f}/100")
                        print(f"    Support Score: {result['vwap_data']['support_score']:.0f}/100")
                        print(f"    Resistance Score: {result['vwap_data']['resistance_score']:.0f}/100")
                        print(f"    Current Price: ${result['vwap_data']['current_price']:.2f}")
                        print(f"    VWAP: ${result['vwap_data']['vwap']:.2f}")
                        print()
                        
            # Summary statistics
            print("="*100)
            print("SCORING SYSTEM SUMMARY")
            print("="*100 + "\n")
            
            total_stocks = len(results)
            rating_counts = {rating: len(ratings.get(rating, [])) for rating in ['Strong Buy', 'Buy', 'Hold', 'Weak Hold', 'Weak Sell', 'Sell', 'Strong Sell']}
            
            print("📊 RATING DISTRIBUTION:")
            for rating, count in rating_counts.items():
                percentage = (count / total_stocks) * 100 if total_stocks > 0 else 0
                print(f"   {rating}: {count} stocks ({percentage:.1f}%)")
                
            print(f"\n🎯 MARKET OUTLOOK ANALYSIS:")
            print(f"   Total Stocks Analyzed: {total_stocks}")
            
            bullish_count = rating_counts['Strong Buy'] + rating_counts['Buy']
            neutral_count = rating_counts['Hold'] + rating_counts['Weak Hold']
            bearish_count = rating_counts['Weak Sell'] + rating_counts['Sell'] + rating_counts['Strong Sell']
            
            bullish_pct = (bullish_count / total_stocks) * 100 if total_stocks > 0 else 0
            neutral_pct = (neutral_count / total_stocks) * 100 if total_stocks > 0 else 0
            bearish_pct = (bearish_count / total_stocks) * 100 if total_stocks > 0 else 0
            
            print(f"   Bullish Ratings: {bullish_count} ({bullish_pct:.1f}%)")
            print(f"   Neutral Ratings: {neutral_count} ({neutral_pct:.1f}%)")
            print(f"   Bearish Ratings: {bearish_count} ({bearish_pct:.1f}%)")
            
            print(f"\n✅ BALANCED REALISTIC SYSTEM ASSESSMENT:")
            if bullish_count > bearish_count:
                print(f"   System shows a BULLISH bias - {bullish_count} vs {bearish_count} bearish")
            elif bearish_count > bullish_count:
                print(f"   System shows a BEARISH bias - {bullish_count} vs {bearish_count} bullish")
            else:
                print(f"   System shows a BALANCED bias - {bullish_count} bullish, {bearish_count} bearish")
                
            print(f"\n🔍 KEY BALANCED FEATURES:")
            print(f"   • Moderate base scores (Fundamental: 45, Technical: 40)")
            print(f"   • Balanced VWAP & S/R weight (30% of total score)")
            print(f"   • Reduced market sentiment component (15% weight)")
            print(f"   • Realistic thresholds for balanced ratings")
            
            if skipped:
                print(f"\n⚠️  SKIPPED STOCKS ({len(skipped)}):")
                print(f"   {', '.join(skipped)}")
                
            print("\n" + "="*100)
            print("BALANCED REALISTIC SCORING COMPLETED")
            print("="*100)
            
        except Exception as e:
            logger.error(f"Error analyzing results: {e}")

def main():
    """Main execution function"""
    try:
        # Initialize scoring system
        scoring_system = BalancedRealisticScoring()
        
        # Connect to database
        if not scoring_system.connect_db():
            logger.error("Failed to connect to database")
            return
            
        # Test tickers across various sectors
        test_tickers = [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
            # Healthcare
            'JNJ', 'PFE', 'UNH',
            # Financial
            'JPM', 'BAC', 'WFC',
            # Energy
            'XOM', 'CVX'
        ]
        
        # Run scoring test
        scoring_system.run_scoring_test(test_tickers)
        
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        
    finally:
        # Cleanup
        if 'scoring_system' in locals():
            scoring_system.disconnect_db()

if __name__ == "__main__":
    main()
