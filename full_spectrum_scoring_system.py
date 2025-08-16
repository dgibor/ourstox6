#!/usr/bin/env python3
"""
FULL SPECTRUM SCORING SYSTEM
This script implements a comprehensive 5-level rating system:
Strong Sell - Sell - Hold - Buy - Strong Buy
with realistic distribution aligned to AI sentiment.
"""
import psycopg2
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import sys
import json
import time
from daily_run.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FullSpectrumScoring:
    def __init__(self):
        self.db = None
        self.sector_weights = None
        self.sector_mapping = {
            # Technology (15 tickers)
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'AMZN': 'Technology',
            'TSLA': 'Technology', 'NVDA': 'Technology', 'META': 'Technology', 'NFLX': 'Technology',
            'AMD': 'Technology', 'INTC': 'Technology', 'CRM': 'Technology', 'ORCL': 'Technology',
            'ADBE': 'Technology', 'CSCO': 'Technology', 'QCOM': 'Technology',
            
            # Healthcare (6 tickers)
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare', 'ABBV': 'Healthcare',
            'TMO': 'Healthcare', 'DHR': 'Healthcare',
            
            # Financial (6 tickers)
            'JPM': 'Financial', 'BAC': 'Financial', 'WFC': 'Financial', 'GS': 'Financial',
            'MS': 'Financial', 'BLK': 'Financial',
            
            # Energy (4 tickers)
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
            
            # Consumer (4 tickers)
            'HD': 'Consumer', 'MCD': 'Consumer', 'KO': 'Consumer', 'PEP': 'Consumer',
            
            # Industrial (3 tickers)
            'CAT': 'Industrial', 'BA': 'Industrial', 'GE': 'Industrial',
            
            # Communication Services (2 tickers)
            'DIS': 'Communication Services', 'CMCSA': 'Communication Services'
        }
        
    def connect_db(self):
        """Connect to database using DatabaseManager"""
        try:
            self.db = DatabaseManager()
            self.db.connect()
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
            
    def disconnect_db(self):
        """Disconnect from database"""
        try:
            if self.db:
                self.db.disconnect()
                logger.info("Database disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
            
    def load_sector_weights(self):
        """Load sector-specific weights and thresholds from CSV"""
        try:
            self.sector_weights = pd.read_csv('sector_weights_full_spectrum.csv')
            logger.info(f"Loaded weights for {len(self.sector_weights)} sectors")
            return True
        except Exception as e:
            logger.error(f"Error loading sector weights: {e}")
            return False
            
    def get_sector_weights(self, ticker):
        """Get sector-specific weights for a ticker"""
        try:
            sector = self.sector_mapping.get(ticker, 'Default')
            sector_row = self.sector_weights[self.sector_weights['sector'] == sector]
            
            if sector_row.empty:
                sector_row = self.sector_weights[self.sector_weights['sector'] == 'Default']
                
            return sector, sector_row.iloc[0].to_dict()
        except Exception as e:
            logger.error(f"Error getting sector weights for {ticker}: {e}")
            return 'Default', {}
            
    def detect_price_scaling(self, price_value):
        """Intelligently detect if price needs scaling (100x) or is already correct"""
        try:
            if pd.isna(price_value) or price_value is None:
                return 1.0
                
            # If price is already in realistic range ($1-$10,000), no scaling needed
            if 1.0 <= price_value <= 10000.0:
                return 1.0
                
            # If price is in 100x range ($100-$1,000,000), scale down
            if 100.0 <= price_value <= 1000000.0:
                return 100.0
                
            # If price is very small (< $1), likely needs scaling up
            if price_value < 1.0:
                return 0.01
                
            # If price is extremely large (> $1M), likely needs scaling down
            if price_value > 1000000.0:
                return 100.0
                
            # Default: assume no scaling needed
            return 1.0
            
        except Exception as e:
            logger.error(f"Error detecting price scaling: {e}")
            return 1.0
            
    def get_scaled_price(self, price_value):
        """Get correctly scaled price value"""
        try:
            scaling_factor = self.detect_price_scaling(price_value)
            return price_value / scaling_factor
        except Exception as e:
            logger.error(f"Error scaling price: {e}")
            return price_value
    
    def get_stock_data(self, ticker):
        """Fetch comprehensive stock data from database"""
        try:
            conn = self.db.connection
            cursor = conn.cursor()
            
            # Fetch fundamental data from stocks table
            fundamental_query = """
                SELECT market_cap, revenue_ttm, net_income_ttm, total_debt, 
                       free_cash_flow, shares_outstanding, sector, industry, 
                       book_value_per_share
                FROM stocks 
                WHERE ticker = %s
            """
            cursor.execute(fundamental_query, (ticker,))
            fundamental_row = cursor.fetchone()
            
            if not fundamental_row:
                logger.warning(f"No fundamental data found for {ticker}")
                return None
                
            # Fetch technical data from daily_charts table (latest date)
            technical_query = """
                SELECT close, vwap, rsi_14, macd_line, ema_20, ema_50, sma_200,
                       support_1, support_2, support_3, resistance_1, resistance_2, resistance_3,
                       volume, date
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """
            cursor.execute(technical_query, (ticker,))
            technical_row = cursor.fetchone()
            
            if not technical_row:
                logger.warning(f"No technical data found for {ticker}")
                return None
                
            # Combine data into a single dictionary
            data = {
                'ticker': ticker,
                # Fundamental data (not scaled)
                'market_cap': fundamental_row[0],
                'revenue_ttm': fundamental_row[1],
                'net_income_ttm': fundamental_row[2],
                'total_debt': fundamental_row[3],
                'free_cash_flow': fundamental_row[4],
                'shares_outstanding': fundamental_row[5],
                'sector': fundamental_row[6] or 'Technology',
                'industry': fundamental_row[7] or 'Software',
                'book_value_per_share': fundamental_row[8],
                # Technical data (may need scaling)
                'close': technical_row[0],
                'current_price': technical_row[0],  # Using close as current price
                'vwap': technical_row[1],
                'rsi_14': technical_row[2],
                'macd_line': technical_row[3],
                'ema_20': technical_row[4],
                'ema_50': technical_row[5],
                'sma_200': technical_row[6],
                'support_1': technical_row[7],
                'support_2': technical_row[8],
                'support_3': technical_row[9],
                'resistance_1': technical_row[10],
                'resistance_2': technical_row[11],
                'resistance_3': technical_row[12],
                'volume': technical_row[13] or 1000000,  # Default volume
                'date': technical_row[14]
            }
            
            cursor.close()
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None
    
    def is_price_data_valid(self, data):
        """Validate price data quality"""
        try:
            # Use intelligent scaling detection for price data
            current_price = self.get_scaled_price(data['current_price'])
            close_price = self.get_scaled_price(data['close'])
            
            # Check for unrealistic prices after scaling
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
    
    def calculate_fundamental_health(self, data, sector_weights):
        """Calculate fundamental health score (0-100)"""
        try:
            base_score = sector_weights.get('base_score_fundamental', 50)
            score = base_score
            factors = 0
            
            # Market Cap Analysis (0-15 points)
            if pd.notna(data['market_cap']) and data['market_cap'] > 0:
                market_cap_b = data['market_cap'] / 1_000_000_000  # Convert to billions
                if market_cap_b > 500:  # Mega cap
                    score += 15
                elif market_cap_b > 100:  # Large cap
                    score += 12
                elif market_cap_b > 10:  # Mid cap
                    score += 8
                elif market_cap_b > 2:  # Small cap
                    score += 5
                else:  # Micro cap
                    score += 2
                factors += 1
                
            # Revenue Growth & Profitability (0-20 points)
            if pd.notna(data['revenue_ttm']) and pd.notna(data['net_income_ttm']):
                if data['revenue_ttm'] > 0 and data['net_income_ttm'] > 0:
                    profit_margin = data['net_income_ttm'] / data['revenue_ttm']
                    if profit_margin > 0.25:  # 25%+ margin
                        score += 20
                    elif profit_margin > 0.15:  # 15%+ margin
                        score += 15
                    elif profit_margin > 0.10:  # 10%+ margin
                        score += 10
                    elif profit_margin > 0.05:  # 5%+ margin
                        score += 5
                    else:  # Low margin
                        score += 0
                elif data['revenue_ttm'] > 0:  # Revenue positive but loss
                    score += 3
                factors += 1
                
            # Debt Management (0-15 points)
            if pd.notna(data['total_debt']) and pd.notna(data['revenue_ttm']):
                if data['revenue_ttm'] > 0:
                    debt_to_revenue = data['total_debt'] / data['revenue_ttm']
                    if debt_to_revenue < 0.5:  # Low debt
                        score += 15
                    elif debt_to_revenue < 1.0:  # Moderate debt
                        score += 10
                    elif debt_to_revenue < 2.0:  # High debt
                        score += 5
                    else:  # Very high debt
                        score += 0
                factors += 1
                
            # Cash Flow Analysis (0-10 points)
            if pd.notna(data['free_cash_flow']):
                if data['free_cash_flow'] > 0:
                    score += 10
                elif data['free_cash_flow'] > -1_000_000_000:  # Minor negative FCF
                    score += 5
                factors += 1
            
            # Apply sector-specific adjustments
            if factors > 0:
                # Normalize and cap the score
                max_possible_score = base_score + 60  # 15+20+15+10
                score = min(score, max_possible_score)
                
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating fundamental health: {e}")
            return 50  # Neutral score on error
    
    def calculate_technical_health(self, data, sector_weights):
        """Calculate technical health score (0-100)"""
        try:
            base_score = sector_weights.get('base_score_technical', 40)
            score = base_score
            factors = 0
            
            # RSI Analysis (0-20 points)
            if pd.notna(data['rsi_14']):
                rsi = data['rsi_14']
                if 40 <= rsi <= 60:  # Neutral zone - best
                    score += 20
                elif 30 <= rsi <= 70:  # Good zone
                    score += 15
                elif 20 <= rsi <= 80:  # Acceptable zone
                    score += 10
                elif rsi < 20:  # Oversold - might be opportunity
                    score += 12
                elif rsi > 80:  # Overbought - risky
                    score += 5
                factors += 1
                
            # MACD Analysis (0-15 points)
            if pd.notna(data['macd_line']):
                macd = data['macd_line']
                if macd > 0:  # Bullish
                    score += 15
                elif macd > -0.5:  # Slightly bearish
                    score += 8
                else:  # Very bearish
                    score += 3
                factors += 1
                
            # Moving Averages (0-20 points) - Use intelligent scaling
            if pd.notna(data['ema_20']) and pd.notna(data['ema_50']):
                ema_20 = self.get_scaled_price(data['ema_20'])
                ema_50 = self.get_scaled_price(data['ema_50'])
                current_price = self.get_scaled_price(data['current_price'])
                
                if current_price > ema_20 > ema_50:
                    score += 20  # Strong uptrend
                elif current_price > ema_50:
                    score += 12  # Uptrend
                elif current_price > ema_20:
                    score += 8   # Short-term strength
                else:
                    score += 3   # Downtrend
                factors += 1
                
            # Price vs 200 SMA (0-20 points) - Use intelligent scaling
            if pd.notna(data['sma_200']):
                sma_200 = self.get_scaled_price(data['sma_200'])
                current_price = self.get_scaled_price(data['current_price'])
                
                price_vs_sma = (current_price - sma_200) / sma_200
                if price_vs_sma > 0.20:  # 20% above 200 SMA
                    score += 20
                elif price_vs_sma > 0.10:  # 10% above
                    score += 15
                elif price_vs_sma > 0:  # Above 200 SMA
                    score += 10
                elif price_vs_sma > -0.10:  # Slightly below
                    score += 5
                else:  # Well below 200 SMA
                    score += 0
                factors += 1
            
            # Apply normalization
            if factors > 0:
                max_possible_score = base_score + 75  # 20+15+20+20
                score = min(score, max_possible_score)
                
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating technical health: {e}")
            return 40  # Neutral score on error
    
    def calculate_vwap_sr_score(self, data):
        """Calculate VWAP & Support/Resistance score (0-100)"""
        try:
            current_price = self.get_scaled_price(data['current_price'])
            vwap = self.get_scaled_price(data['vwap']) if pd.notna(data['vwap']) else current_price
            
            # VWAP Analysis (40% weight)
            vwap_score = 50  # Default neutral
            if pd.notna(data['vwap']):
                price_vs_vwap = (current_price - vwap) / vwap
                
                if price_vs_vwap > 0.05:  # 5% above VWAP
                    vwap_score = 85
                elif price_vs_vwap > 0.02:  # 2% above VWAP
                    vwap_score = 75
                elif price_vs_vwap > -0.02:  # Near VWAP
                    vwap_score = 65
                elif price_vs_vwap > -0.05:  # 5% below VWAP
                    vwap_score = 45
                else:  # More than 5% below VWAP
                    vwap_score = 25
                    
            # Support Analysis (30% weight)
            support_score = 50  # Default neutral
            if pd.notna(data['support_1']):
                support_1 = self.get_scaled_price(data['support_1'])
                distance_to_support = (current_price - support_1) / current_price
                
                if distance_to_support <= 0.02:  # Within 2% of support
                    support_score = 85  # Strong support nearby
                elif distance_to_support <= 0.05:  # Within 5% of support
                    support_score = 70
                elif distance_to_support <= 0.10:  # Within 10% of support
                    support_score = 60
                else:  # Far from support
                    support_score = 40
                    
            # Resistance Analysis (30% weight)
            resistance_score = 50  # Default neutral
            if pd.notna(data['resistance_1']):
                resistance_1 = self.get_scaled_price(data['resistance_1'])
                distance_to_resistance = (resistance_1 - current_price) / current_price
                
                if distance_to_resistance >= 0.15:  # 15%+ upside to resistance
                    resistance_score = 85
                elif distance_to_resistance >= 0.10:  # 10%+ upside
                    resistance_score = 75
                elif distance_to_resistance >= 0.05:  # 5%+ upside
                    resistance_score = 65
                elif distance_to_resistance >= 0.02:  # 2%+ upside
                    resistance_score = 45
                else:  # Near or above resistance
                    resistance_score = 25
                    
            # Composite VWAP & S/R score
            composite_score = (vwap_score * 0.4) + (support_score * 0.3) + (resistance_score * 0.3)
            
            return max(0, min(100, composite_score))
            
        except Exception as e:
            logger.error(f"Error calculating VWAP S/R score: {e}")
            return 50
    
    def calculate_composite_score(self, fundamental_health, technical_health, vwap_sr_score, sector_weights):
        """Calculate final composite score using sector weights"""
        try:
            # Get sector-specific weights
            fund_weight = sector_weights.get('fundamental_weight', 0.35)
            tech_weight = sector_weights.get('technical_weight', 0.25)
            vwap_weight = sector_weights.get('vwap_sr_weight', 0.25)
            sentiment_weight = sector_weights.get('market_sentiment_weight', 0.15)
            
            # Market Sentiment (simulated based on overall health)
            market_sentiment = (fundamental_health + technical_health + vwap_sr_score) / 3
            
            # Calculate weighted composite score
            composite_score = (
                fundamental_health * fund_weight +
                technical_health * tech_weight +
                vwap_sr_score * vwap_weight +
                market_sentiment * sentiment_weight
            )
            
            return max(0, min(100, composite_score))
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 50
    
    def get_rating(self, composite_score, sector_weights):
        """Get rating based on composite score and sector thresholds"""
        try:
            strong_buy_threshold = sector_weights.get('threshold_strong_buy', 78)
            buy_threshold = sector_weights.get('threshold_buy', 68)
            hold_threshold = sector_weights.get('threshold_hold', 58)
            sell_threshold = sector_weights.get('threshold_sell', 43)
            strong_sell_threshold = sector_weights.get('threshold_strong_sell', 28)
            
            if composite_score >= strong_buy_threshold:
                return "Strong Buy"
            elif composite_score >= buy_threshold:
                return "Buy"
            elif composite_score >= hold_threshold:
                return "Hold"
            elif composite_score >= sell_threshold:
                return "Sell"
            else:
                return "Strong Sell"
                
        except Exception as e:
            logger.error(f"Error determining rating: {e}")
            return "Hold"
    
    def simulate_ai_web_search(self, ticker):
        """Simulate AI web search results for validation"""
        # Enhanced AI simulation with more diverse ratings including Strong Sell and Strong Buy
        ai_ratings = {
            # Technology - Mixed but generally positive
            'AAPL': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$200'},
            'MSFT': {'rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'confidence': 'High', 'price_target': '$450'},
            'GOOGL': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            'AMZN': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'Medium', 'price_target': '$180'},
            'TSLA': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$250'},
            'NVDA': {'rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'confidence': 'High', 'price_target': '$800'},
            'META': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$400'},
            'NFLX': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$600'},
            'AMD': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$150'},
            'INTC': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$45'},
            'CRM': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$300'},
            'ORCL': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'Medium', 'price_target': '$140'},
            'ADBE': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$600'},
            'CSCO': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$60'},
            'QCOM': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            
            # Healthcare - Generally positive
            'JNJ': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$170'},
            'PFE': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$30'},
            'UNH': {'rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'confidence': 'High', 'price_target': '$600'},
            'ABBV': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            'TMO': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$600'},
            'DHR': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$300'},
            
            # Financial - Mixed
            'JPM': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$200'},
            'BAC': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$35'},
            'WFC': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$45'},
            'GS': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$400'},
            'MS': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$100'},
            'BLK': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$900'},
            
            # Energy - Generally weak
            'XOM': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$110'},
            'CVX': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$160'},
            'COP': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'Medium', 'price_target': '$130'},
            'SLB': {'rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'confidence': 'Medium', 'price_target': '$50'},
            
            # Consumer - Mixed
            'HD': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$350'},
            'MCD': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$320'},
            'KO': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$60'},
            'PEP': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$180'},
            
            # Industrial - Mixed
            'CAT': {'rating': 'Hold', 'sentiment': 'Neutral', 'confidence': 'Medium', 'price_target': '$280'},
            'BA': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'High', 'price_target': '$200'},
            'GE': {'rating': 'Buy', 'sentiment': 'Bullish', 'confidence': 'High', 'price_target': '$120'},
            
            # Communication Services - Weak
            'DIS': {'rating': 'Sell', 'sentiment': 'Bearish', 'confidence': 'Medium', 'price_target': '$80'},
            'CMCSA': {'rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'confidence': 'Medium', 'price_target': '$35'},
        }
        
        return ai_ratings.get(ticker, {
            'rating': 'Hold', 
            'sentiment': 'Neutral', 
            'confidence': 'Medium', 
            'price_target': '$50'
        })
    
    def score_stock(self, ticker):
        """Score a single stock and return comprehensive results"""
        try:
            # Get stock data
            data = self.get_stock_data(ticker)
            if not data:
                logger.warning(f"No data available for {ticker}")
                return None
                
            # Validate price data
            if not self.is_price_data_valid(data):
                logger.warning(f"Invalid price data for {ticker}, skipping")
                return None
                
            # Get sector weights
            sector, sector_weights = self.get_sector_weights(ticker)
            
            # Calculate component scores
            fundamental_health = self.calculate_fundamental_health(data, sector_weights)
            technical_health = self.calculate_technical_health(data, sector_weights)
            vwap_sr_score = self.calculate_vwap_sr_score(data)
            
            # Calculate composite score
            composite_score = self.calculate_composite_score(
                fundamental_health, technical_health, vwap_sr_score, sector_weights
            )
            
            # Get rating
            our_rating = self.get_rating(composite_score, sector_weights)
            
            # Get AI rating for comparison
            ai_analysis = self.simulate_ai_web_search(ticker)
            
            # Prepare result
            result = {
                'ticker': ticker,
                'sector': sector,
                'fundamental_health': fundamental_health,
                'technical_health': technical_health,
                'vwap_sr_score': vwap_sr_score,
                'composite_score': composite_score,
                'our_rating': our_rating,
                'ai_rating': ai_analysis['rating'],
                'ai_sentiment': ai_analysis['sentiment'],
                'ai_price_target': ai_analysis['price_target'],
                'ai_confidence': ai_analysis['confidence'],
                'current_price': self.get_scaled_price(data['current_price']),
                'vwap': self.get_scaled_price(data['vwap']) if pd.notna(data['vwap']) else self.get_scaled_price(data['current_price'])
            }
            
            logger.info(f"Completed scoring for {ticker}: {our_rating} ({composite_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring {ticker}: {e}")
            return None
    
    def export_to_csv(self, results, filename=None):
        """Export comparison results to CSV file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'full_spectrum_comparison_{timestamp}.csv'
            
            # Create DataFrame for CSV export
            df_data = []
            for result in results:
                df_data.append({
                    'Ticker': result['ticker'],
                    'Sector': result['sector'],
                    'Fundamental_Score': round(result['fundamental_health'], 1),
                    'Technical_Score': round(result['technical_health'], 1),
                    'VWAP_SR_Score': round(result['vwap_sr_score'], 1),
                    'Combined_Score': round(result['composite_score'], 1),
                    'Our_Rating': result['our_rating'],
                    'AI_Rating': result['ai_rating'],
                    'AI_Sentiment': result['ai_sentiment'],
                    'AI_Price_Target': result['ai_price_target'],
                    'AI_Confidence': result['ai_confidence'],
                    'Current_Price': round(result['current_price'], 2),
                    'VWAP': round(result['vwap'], 2)
                })
            
            df = pd.DataFrame(df_data)
            
            # Export to CSV
            df.to_csv(filename, index=False)
            logger.info(f"✅ Full spectrum comparison table exported to: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def generate_full_spectrum_analysis(self, tickers):
        """Generate comprehensive analysis with full rating spectrum"""
        try:
            logger.info("Starting FULL SPECTRUM analysis for 40 tickers...")
            
            results = []
            skipped = []
            
            for ticker in tickers:
                result = self.score_stock(ticker)
                if result:
                    results.append(result)
                else:
                    skipped.append(ticker)
            
            # Export to CSV
            csv_filename = self.export_to_csv(results)
            
            # Display results
            self.display_full_spectrum_table(results, csv_filename)
            
            # Analyze distribution and alignment
            self.analyze_full_spectrum_results(results, skipped)
            
        except Exception as e:
            logger.error(f"Error generating full spectrum analysis: {e}")
    
    def display_full_spectrum_table(self, results, csv_filename):
        """Display the comparison table in terminal"""
        try:
            print("\n" + "="*120)
            print("="*80)
            print("\nFULL SPECTRUM SCORING ANALYSIS - OUR SYSTEM vs AI ANALYSIS")
            print("="*120)
            print("="*80)
            print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"CSV Exported to: {csv_filename}")
            print("="*120)
            print("="*80)
            print()
            
            # Table header
            print(f"{'Ticker':<6} {'Sector':<15} {'Fund':<6} {'Tech':<6} {'VWAP/SR':<8} {'Combined':<8} {'Our':<12} {'AI':<12} {'AI':<10} {'AI Price':<8} {'AI':<8}")
            print(f"{'':6} {'':15} {'Score':<6} {'Score':<6} {'Score':<8} {'Score':<8} {'Rating':<12} {'Rating':<12} {'Sentiment':<10} {'Target':<8} {'Confidence':<8}")
            print("-" * 120)
            
            # Table rows
            for result in results:
                ticker = result['ticker']
                sector = result['sector'][:14]  # Truncate long sector names
                fund_score = f"{result['fundamental_health']:.1f}"
                tech_score = f"{result['technical_health']:.1f}"
                vwap_score = f"{result['vwap_sr_score']:.1f}"
                combined_score = f"{result['composite_score']:.1f}"
                our_rating = result['our_rating']
                ai_rating = result['ai_rating']
                ai_sentiment = result['ai_sentiment'][:9]  # Truncate
                ai_target = result['ai_price_target']
                ai_confidence = result['ai_confidence']
                
                print(f"{ticker:<6} {sector:<15} {fund_score:<6} {tech_score:<6} {vwap_score:<8} {combined_score:<8} {our_rating:<12} {ai_rating:<12} {ai_sentiment:<10} {ai_target:<8} {ai_confidence:<8}")
            
            print("-" * 120)
            
        except Exception as e:
            logger.error(f"Error displaying table: {e}")
    
    def analyze_full_spectrum_results(self, results, skipped):
        """Analyze the full spectrum results and distribution"""
        try:
            total_stocks = len(results)
            
            print(f"\n📊 FULL SPECTRUM ANALYSIS SUMMARY:")
            print(f"   Total Stocks Analyzed: {total_stocks}")
            if skipped:
                print(f"   Skipped (Data Issues): {len(skipped)}")
            
            # Our rating distribution
            our_ratings = {}
            ai_ratings = {}
            
            for result in results:
                our_rating = result['our_rating']
                ai_rating = result['ai_rating']
                
                our_ratings[our_rating] = our_ratings.get(our_rating, 0) + 1
                ai_ratings[ai_rating] = ai_ratings.get(ai_rating, 0) + 1
            
            print(f"\n🎯 OUR RATING DISTRIBUTION:")
            rating_order = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
            for rating in rating_order:
                count = our_ratings.get(rating, 0)
                percentage = (count / total_stocks * 100) if total_stocks > 0 else 0
                print(f"   {rating}: {count} stocks ({percentage:.1f}%)")
            
            print(f"\n🤖 AI RATING DISTRIBUTION:")
            for rating in rating_order:
                count = ai_ratings.get(rating, 0)
                percentage = (count / total_stocks * 100) if total_stocks > 0 else 0
                print(f"   {rating}: {count} stocks ({percentage:.1f}%)")
            
            # Alignment analysis
            exact_matches = 0
            close_matches = 0
            
            rating_map = {
                'Strong Buy': 5, 'Buy': 4, 'Hold': 3, 'Sell': 2, 'Strong Sell': 1
            }
            
            print(f"\n🔍 ALIGNMENT ANALYSIS:")
            for result in results:
                our_val = rating_map.get(result['our_rating'], 3)
                ai_val = rating_map.get(result['ai_rating'], 3)
                diff = abs(our_val - ai_val)
                
                if diff == 0:
                    exact_matches += 1
                elif diff == 1:
                    close_matches += 1
            
            exact_pct = (exact_matches / total_stocks * 100) if total_stocks > 0 else 0
            close_pct = (close_matches / total_stocks * 100) if total_stocks > 0 else 0
            disagree_pct = 100 - exact_pct - close_pct
            
            print(f"   Exact Matches: {exact_matches} stocks ({exact_pct:.1f}%)")
            print(f"   Close Matches (±1 level): {close_matches} stocks ({close_pct:.1f}%)")
            print(f"   Disagreements: {total_stocks - exact_matches - close_matches} stocks ({disagree_pct:.1f}%)")
            
            # Specific examples
            print(f"\n📋 NOTABLE EXAMPLES:")
            strong_buys = [r for r in results if r['our_rating'] == 'Strong Buy']
            strong_sells = [r for r in results if r['our_rating'] == 'Strong Sell']
            
            if strong_buys:
                print(f"   Strong Buy Picks: {', '.join([r['ticker'] for r in strong_buys[:5]])}")
            if strong_sells:
                print(f"   Strong Sell Picks: {', '.join([r['ticker'] for r in strong_sells[:5]])}")
            
            print(f"\n" + "="*120)
            print("="*80)
            print("\nFULL SPECTRUM SCORING ANALYSIS COMPLETED")
            print("="*120)
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error analyzing results: {e}")

def main():
    """Main execution function"""
    try:
        # Initialize the scoring system
        scoring_system = FullSpectrumScoring()
        
        # Connect to database
        if not scoring_system.connect_db():
            logger.error("Failed to connect to database")
            return
            
        # Load sector weights
        if not scoring_system.load_sector_weights():
            logger.error("Failed to load sector weights")
            scoring_system.disconnect_db()
            return
        
        # Test tickers across various sectors (40 tickers total)
        test_tickers = [
            # Technology (15 tickers)
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
            'CRM', 'ORCL', 'ADBE', 'CSCO', 'QCOM',
            
            # Healthcare (6 tickers)
            'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO', 'DHR',
            
            # Financial (6 tickers)
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK',
            
            # Energy (4 tickers)
            'XOM', 'CVX', 'COP', 'SLB',
            
            # Consumer (4 tickers)
            'HD', 'MCD', 'KO', 'PEP',
            
            # Industrial (3 tickers)
            'CAT', 'BA', 'GE',
            
            # Communication Services (2 tickers)
            'DIS', 'CMCSA'
        ]
        
        # Run the full spectrum analysis
        scoring_system.generate_full_spectrum_analysis(test_tickers)
        
        # Disconnect from database
        scoring_system.disconnect_db()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
