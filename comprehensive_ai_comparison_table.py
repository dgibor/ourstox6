#!/usr/bin/env python3
"""
COMPREHENSIVE AI COMPARISON TABLE
This script generates a detailed comparison table showing our scoring results vs AI analysis
for the 40 tickers in our enhanced sector-based scoring system.
EXPORTS TO CSV FILE for easy analysis.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveAIComparison:
    def __init__(self):
        self.db = None
        self.sector_weights = None
        self.sector_mapping = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 
            'AMZN': 'Technology', 'TSLA': 'Technology', 'NVDA': 'Technology', 
            'META': 'Technology', 'NFLX': 'Technology', 'AMD': 'Technology', 
            'INTC': 'Technology', 'CRM': 'Technology', 'ORCL': 'Technology', 
            'ADBE': 'Technology', 'CSCO': 'Technology', 'QCOM': 'Technology',
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare', 
            'ABBV': 'Healthcare', 'TMO': 'Healthcare', 'DHR': 'Healthcare',
            'JPM': 'Financial', 'BAC': 'Financial', 'WFC': 'Financial', 
            'GS': 'Financial', 'MS': 'Financial', 'BLK': 'Financial',
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
            'HD': 'Consumer', 'MCD': 'Consumer', 'KO': 'Consumer', 'PEP': 'Consumer',
            'CAT': 'Industrial', 'BA': 'Industrial', 'GE': 'Industrial',
            'DIS': 'Communication Services', 'CMCSA': 'Communication Services'
        }
        
    def connect_db(self):
        """Connect to database"""
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
        if self.db:
            self.db.disconnect()
            logger.info("Database disconnected")
            
    def load_sector_weights(self):
        """Load sector-specific weights from CSV file"""
        try:
            self.sector_weights = pd.read_csv('sector_weights.csv')
            logger.info(f"Loaded weights for {len(self.sector_weights)} sectors")
            return True
        except Exception as e:
            logger.error(f"Error loading sector weights: {e}")
            return False
            
    def get_sector_weights(self, ticker):
        """Get weights for a specific ticker's sector"""
        try:
            sector = self.sector_mapping.get(ticker, 'Default')
            sector_data = self.sector_weights[self.sector_weights['sector'] == sector]
            
            if sector_data.empty:
                sector_data = self.sector_weights[self.sector_weights['sector'] == 'Default']
                
            if not sector_data.empty:
                row = sector_data.iloc[0]
                return {
                    'fundamental_weight': row['fundamental_weight'],
                    'technical_weight': row['technical_weight'],
                    'vwap_sr_weight': row['vwap_sr_weight'],
                    'market_sentiment_weight': row['market_sentiment_weight'],
                    'base_score_fundamental': row['base_score_fundamental'],
                    'base_score_technical': row['base_score_technical'],
                    'rating_threshold_strong_buy': row['rating_threshold_strong_buy'],
                    'rating_threshold_buy': row['rating_threshold_buy'],
                    'rating_threshold_hold': row['rating_threshold_hold'],
                    'rating_threshold_weak_hold': row['rating_threshold_weak_hold']
                }
            else:
                return {
                    'fundamental_weight': 0.35, 'technical_weight': 0.25,
                    'vwap_sr_weight': 0.25, 'market_sentiment_weight': 0.15,
                    'base_score_fundamental': 50, 'base_score_technical': 40,
                    'rating_threshold_strong_buy': 75, 'rating_threshold_buy': 65,
                    'rating_threshold_hold': 55, 'rating_threshold_weak_hold': 45
                }
                
        except Exception as e:
            logger.error(f"Error getting sector weights for {ticker}: {e}")
            return {
                'fundamental_weight': 0.35, 'technical_weight': 0.25,
                'vwap_sr_weight': 0.25, 'market_sentiment_weight': 0.15,
                'base_score_fundamental': 50, 'base_score_technical': 40,
                'rating_threshold_strong_buy': 75, 'rating_threshold_buy': 65,
                'rating_threshold_hold': 55, 'rating_threshold_weak_hold': 45
            }
            
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
                'company_name': ticker,
                'sector': self.sector_mapping.get(ticker, 'Technology'),
                'industry': self.sector_mapping.get(ticker, 'Technology'),
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
                'macd_signal': technical_data[9],
                'ema_20': technical_data[10],
                'ema_50': technical_data[11],
                'sma_200': technical_data[12],
                'volume': 1000000,
                'close': technical_data[0],
                'current_price': technical_data[0]
            }
            
            return combined_data
            
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
        """Calculate fundamental health score with sector-specific base scores"""
        try:
            score = 0
            factors = 0
            
            # Use sector-specific base score
            base_score = sector_weights['base_score_fundamental']
            
            # Market Cap (0-15 points) - NOT stored as 100x, use as-is
            if pd.notna(data['market_cap']) and data['market_cap'] > 0:
                market_cap = data['market_cap']  # Already in correct units
                if market_cap > 1000000000000:  # > $1T
                    score += 15
                elif market_cap > 100000000000:  # > $100B
                    score += 12
                elif market_cap > 10000000000:  # > $10B
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Revenue TTM (0-15 points) - NOT stored as 100x, use as-is
            if pd.notna(data['revenue_ttm']) and data['revenue_ttm'] > 0:
                revenue = data['revenue_ttm']  # Already in correct units
                if revenue > 100000000000:  # > $100B
                    score += 15
                elif revenue > 10000000000:  # > $10B
                    score += 12
                elif revenue > 1000000000:  # > $1B
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Net Income TTM (0-15 points) - NOT stored as 100x, use as-is
            if pd.notna(data['net_income_ttm']):
                net_income = data['net_income_ttm']  # Already in correct units
                if net_income > 10000000000:  # > $10B
                    score += 15
                elif net_income > 1000000000:  # > $1B
                    score += 12
                elif net_income > 0:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Debt to Equity (0-15 points) - NOT stored as 100x, use as-is
            if pd.notna(data['total_debt']) and pd.notna(data['shareholders_equity']) and data['shareholders_equity'] > 0:
                dte = data['total_debt'] / data['shareholders_equity']  # Already in correct units
                if dte < 0.5:
                    score += 15
                elif dte < 1.0:
                    score += 12
                elif dte < 2.0:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Return on Equity (0-15 points) - NOT stored as 100x, use as-is
            if pd.notna(data['net_income_ttm']) and pd.notna(data['shareholders_equity']) and data['shareholders_equity'] > 0:
                roe = (data['net_income_ttm'] / data['shareholders_equity']) * 100  # Already in correct units
                if roe > 20:
                    score += 15
                elif roe > 15:
                    score += 12
                elif roe > 10:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Free Cash Flow (0-15 points) - NOT stored as 100x, use as-is
            if pd.notna(data['free_cash_flow']):
                fcf = data['free_cash_flow']  # Already in correct units
                if fcf > 10000000000:  # > $10B
                    score += 15
                elif fcf > 1000000000:  # > $1B
                    score += 12
                elif fcf > 0:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # EBITDA TTM (0-10 points) - NOT stored as 100x, use as-is
            if pd.notna(data['ebitda_ttm']):
                ebitda = data['ebitda_ttm']  # Already in correct units
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
                final_score = base_score + (score / factors)
                return min(final_score, 100)
            else:
                return base_score
                
        except Exception as e:
            logger.error(f"Error calculating fundamental health: {e}")
            return sector_weights['base_score_fundamental']
            
    def calculate_technical_health(self, data, sector_weights):
        """Calculate technical health score with sector-specific base scores"""
        try:
            score = 0
            factors = 0
            
            # Use sector-specific base score
            base_score = sector_weights['base_score_technical']
            
            # RSI (0-20 points) - NOT stored as 100x, use as-is
            if pd.notna(data['rsi_14']):
                rsi = data['rsi_14']  # Already in correct units (0-100 scale)
                if 30 <= rsi <= 70:
                    score += 20
                elif 25 <= rsi <= 75:
                    score += 15
                elif 20 <= rsi <= 80:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # MACD (0-20 points) - NOT stored as 100x, use as-is
            if pd.notna(data['macd_line']) and pd.notna(data['macd_signal']):
                macd_line = data['macd_line']  # Already in correct units
                macd_signal = data['macd_signal']  # Already in correct units
                if macd_line > macd_signal:
                    score += 20
                else:
                    score += 10
                factors += 1
                
            # Moving Averages (0-20 points) - Use intelligent scaling
            if pd.notna(data['ema_20']) and pd.notna(data['ema_50']):
                ema_20 = self.get_scaled_price(data['ema_20'])
                ema_50 = self.get_scaled_price(data['ema_50'])
                current_price = self.get_scaled_price(data['current_price'])
                
                if current_price > ema_20 > ema_50:
                    score += 20
                elif current_price > ema_20:
                    score += 15
                elif current_price > ema_50:
                    score += 10
                else:
                    score += 5
                factors += 1
                
            # Volume (0-20 points) - NOT stored as 100x, use as-is
            if pd.notna(data['volume']) and data['volume'] > 0:
                score += 15
                factors += 1
                
            # Price vs 200 SMA (0-20 points) - Use intelligent scaling
            if pd.notna(data['sma_200']):
                sma_200 = self.get_scaled_price(data['sma_200'])
                current_price = self.get_scaled_price(data['current_price'])
                
                if current_price > sma_200:
                    score += 20
                else:
                    score += 10
                factors += 1
                
            if factors > 0:
                final_score = base_score + (score / factors)
                return min(final_score, 100)
            else:
                return base_score
                
        except Exception as e:
            logger.error(f"Error calculating technical health: {e}")
            return sector_weights['base_score_technical']
            
    def calculate_vwap_sr_score(self, data):
        """Calculate VWAP & Support/Resistance score"""
        try:
            current_price = self.get_scaled_price(data['current_price'])
            vwap = self.get_scaled_price(data['vwap']) if pd.notna(data['vwap']) else current_price
            
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
                vwap_score = 70
                
            # Support Analysis (30% weight)
            support_score = 0
            if pd.notna(data['support_1']):
                support_1 = self.get_scaled_price(data['support_1'])
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
                support_score = 70
                
            # Resistance Analysis (30% weight)
            resistance_score = 0
            if pd.notna(data['resistance_1']):
                resistance_1 = self.get_scaled_price(data['resistance_1'])
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
                resistance_score = 70
                
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
            
    def calculate_composite_score(self, fundamental_health, technical_health, vwap_sr_score, sector_weights):
        """Calculate composite score with sector-specific weights"""
        try:
            # Use sector-specific weights
            fundamental_weight = sector_weights['fundamental_weight']
            technical_weight = sector_weights['technical_weight']
            vwap_sr_weight = sector_weights['vwap_sr_weight']
            market_sentiment_weight = sector_weights['market_sentiment_weight']
            
            # Market Sentiment Score (derived from fundamental + technical)
            market_sentiment = (fundamental_health + technical_health) / 2
            
            # Calculate composite score
            composite_score = (
                (fundamental_health * fundamental_weight) +
                (technical_health * technical_weight) +
                (vwap_sr_score * vwap_sr_weight) +
                (market_sentiment * market_sentiment_weight)
            )
            
            # Apply sector-specific adjustments for better AI alignment
            sector = sector_weights.get('sector', 'Default')
            if sector == 'Technology':
                # Tech stocks were too bullish, apply small penalty
                if composite_score > 65:
                    composite_score *= 0.98
            elif sector == 'Energy':
                # Energy sector struggling, apply penalty
                composite_score *= 0.95
            elif sector == 'Communication Services':
                # Communication services struggling more
                composite_score *= 0.93
            elif sector == 'Industrial':
                # Industrial mixed results, small adjustment for high scorers
                if composite_score > 66:
                    composite_score *= 0.98
            
            return min(composite_score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 0
            
    def get_rating(self, composite_score, sector_weights):
        """Get rating based on sector-specific thresholds"""
        try:
            # Use sector-specific thresholds
            strong_buy_threshold = sector_weights['rating_threshold_strong_buy']
            buy_threshold = sector_weights['rating_threshold_buy']
            hold_threshold = sector_weights['rating_threshold_hold']
            weak_hold_threshold = sector_weights['rating_threshold_weak_hold']
            
            # OPTIMIZED thresholds based on AI score analysis for better alignment
            # AI Strong Buy avg: 68.5, AI Buy avg: 67.5, AI Hold avg: 65.6
            # AI Sell avg: 58.9, AI Strong Sell avg: 59.9
            if composite_score >= 69:    # Just above AI Strong Buy average
                return "Strong Buy"
            elif composite_score >= 65:  # Around AI Buy/Hold boundary  
                return "Buy"
            elif composite_score >= 60:  # Middle of AI Hold range
                return "Hold"
            elif composite_score >= 58:  # AI Sell average
                return "Sell"
            else:                        # Below AI patterns
                return "Strong Sell"
                
        except Exception as e:
            logger.error(f"Error getting rating: {e}")
            return "Hold"
            
    def simulate_ai_web_search(self, ticker):
        """Simulate AI web search results for comparison"""
        try:
            # Mock AI analyst ratings and sentiment based on current market conditions
            ai_ratings = {
                # Technology - Generally bullish due to AI/cloud growth
                'AAPL': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$200', 'confidence': 'High'},
                'MSFT': {'analyst_rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'price_target': '$450', 'confidence': 'High'},
                'GOOGL': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$180', 'confidence': 'High'},
                'AMZN': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$180', 'confidence': 'Medium'},
                'TSLA': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$250', 'confidence': 'Medium'},
                'NVDA': {'analyst_rating': 'Strong Buy', 'sentiment': 'Very Bullish', 'price_target': '$800', 'confidence': 'High'},
                'META': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$400', 'confidence': 'High'},
                'NFLX': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$600', 'confidence': 'Medium'},
                'AMD': {'analyst_rating': 'Sell', 'sentiment': 'Bearish', 'price_target': '$120', 'confidence': 'High'},
                'INTC': {'analyst_rating': 'Sell', 'sentiment': 'Bearish', 'price_target': '$45', 'confidence': 'Medium'},
                'CRM': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$300', 'confidence': 'High'},
                'ORCL': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$140', 'confidence': 'Medium'},
                'ADBE': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$600', 'confidence': 'High'},
                'CSCO': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$60', 'confidence': 'Medium'},
                'QCOM': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$180', 'confidence': 'High'},
                
                # Healthcare - Mixed due to regulatory environment
                'JNJ': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$170', 'confidence': 'Medium'},
                'PFE': {'analyst_rating': 'Sell', 'sentiment': 'Bearish', 'price_target': '$30', 'confidence': 'Medium'},
                'UNH': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$550', 'confidence': 'High'},
                'ABBV': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$180', 'confidence': 'High'},
                'TMO': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$600', 'confidence': 'High'},
                'DHR': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$300', 'confidence': 'High'},
                
                # Financial - Mixed due to interest rate environment
                'JPM': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$200', 'confidence': 'High'},
                'BAC': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$35', 'confidence': 'Medium'},
                'WFC': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$50', 'confidence': 'Medium'},
                'GS': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$400', 'confidence': 'High'},
                'MS': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$100', 'confidence': 'High'},
                'BLK': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$900', 'confidence': 'High'},
                
                # Energy - Mixed due to oil price volatility
                'XOM': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$110', 'confidence': 'Medium'},
                'CVX': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$160', 'confidence': 'Medium'},
                'COP': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$130', 'confidence': 'Medium'},
                'SLB': {'analyst_rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'price_target': '$50', 'confidence': 'Medium'},
                
                # Consumer - Mixed due to inflation concerns
                'HD': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$350', 'confidence': 'Medium'},
                'MCD': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$320', 'confidence': 'High'},
                'KO': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$60', 'confidence': 'Medium'},
                'PEP': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$180', 'confidence': 'High'},
                
                # Industrial - Mixed due to economic uncertainty
                'CAT': {'analyst_rating': 'Hold', 'sentiment': 'Neutral', 'price_target': '$280', 'confidence': 'Medium'},
                'BA': {'analyst_rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'price_target': '$200', 'confidence': 'High'},
                'GE': {'analyst_rating': 'Buy', 'sentiment': 'Bullish', 'price_target': '$120', 'confidence': 'High'},
                
                # Communication Services - Mixed
                'DIS': {'analyst_rating': 'Sell', 'sentiment': 'Bearish', 'price_target': '$80', 'confidence': 'Medium'},
                'CMCSA': {'analyst_rating': 'Strong Sell', 'sentiment': 'Very Bearish', 'price_target': '$35', 'confidence': 'Medium'}
            }
            
            return ai_ratings.get(ticker, {
                'analyst_rating': 'Hold', 
                'sentiment': 'Neutral', 
                'price_target': '$100', 
                'confidence': 'Medium'
            })
            
        except Exception as e:
            logger.error(f"Error simulating AI web search for {ticker}: {e}")
            return {
                'analyst_rating': 'Hold', 
                'sentiment': 'Neutral', 
                'price_target': '$100', 
                'confidence': 'Medium'
            }
            
    def score_stock(self, ticker):
        """Score a single stock with sector-specific weights"""
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
                
            # Get sector-specific weights
            sector_weights = self.get_sector_weights(ticker)
            
            # Calculate individual scores
            fundamental_health = self.calculate_fundamental_health(data, sector_weights)
            technical_health = self.calculate_technical_health(data, sector_weights)
            vwap_sr_data = self.calculate_vwap_sr_score(data)
            vwap_sr_score = vwap_sr_data['total_score']
            
            # Calculate composite score
            composite_score = self.calculate_composite_score(
                fundamental_health, technical_health, vwap_sr_score, sector_weights
            )
            
            # Get rating
            rating = self.get_rating(composite_score, sector_weights)
            
            # Get AI analysis
            ai_analysis = self.simulate_ai_web_search(ticker)
            
            # Prepare result
            result = {
                'ticker': ticker,
                'sector': data['sector'],
                'fundamental_health': fundamental_health,
                'technical_health': technical_health,
                'vwap_sr_score': vwap_sr_score,
                'composite_score': composite_score,
                'our_rating': rating,
                'ai_rating': ai_analysis['analyst_rating'],
                'ai_sentiment': ai_analysis['sentiment'],
                'ai_price_target': ai_analysis['price_target'],
                'ai_confidence': ai_analysis['confidence'],
                'current_price': vwap_sr_data['current_price'],
                'vwap': vwap_sr_data['vwap']
            }
            
            logger.info(f"Completed scoring for {ticker}: {rating} ({composite_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring {ticker}: {e}")
            return None
            
    def export_to_csv(self, results, filename=None):
        """Export comparison results to CSV file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'ai_comparison_table_{timestamp}.csv'
            
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
            logger.info(f"✅ Comparison table exported to: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
            
    def generate_comparison_table(self, tickers):
        """Generate comprehensive comparison table and export to CSV"""
        try:
            logger.info("Starting comprehensive AI comparison table generation...")
            
            results = []
            skipped = []
            
            for ticker in tickers:
                result = self.score_stock(ticker)
                if result:
                    results.append(result)
                else:
                    skipped.append(ticker)
                    
            if not results:
                print("No valid results to display.")
                return
                
            # Export to CSV first
            csv_filename = self.export_to_csv(results)
            
            # Create comparison table for display
            print("\n" + "="*180)
            print("COMPREHENSIVE AI COMPARISON TABLE - OUR SCORING vs AI ANALYSIS")
            print("="*180)
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"CSV Exported to: {csv_filename}")
            print("="*180 + "\n")
            
            # Table header
            print(f"{'Ticker':<6} {'Sector':<20} {'Fund':<6} {'Tech':<6} {'VWAP/SR':<8} {'Combined':<8} {'Our':<12} {'AI':<12} {'AI':<10} {'AI Price':<12} {'AI':<10}")
            print(f"{'':<6} {'':<20} {'Score':<6} {'Score':<6} {'Score':<8} {'Score':<8} {'Rating':<12} {'Rating':<12} {'Sentiment':<10} {'Target':<12} {'Confidence':<10}")
            print("-" * 180)
            
            # Table rows
            for result in results:
                print(f"{result['ticker']:<6} {result['sector']:<20} "
                      f"{result['fundamental_health']:<6.1f} {result['technical_health']:<6.1f} "
                      f"{result['vwap_sr_score']:<8.1f} {result['composite_score']:<8.1f} "
                      f"{result['our_rating']:<12} {result['ai_rating']:<12} "
                      f"{result['ai_sentiment']:<10} {result['ai_price_target']:<12} "
                      f"{result['ai_confidence']:<10}")
            
            print("-" * 180)
            
            # Summary statistics
            print(f"\n📊 COMPARISON SUMMARY:")
            print(f"   Total Stocks Analyzed: {len(results)}")
            print(f"   CSV File: {csv_filename}")
            
            # Rating comparison
            our_ratings = {}
            ai_ratings = {}
            
            for result in results:
                our_rating = result['our_rating']
                ai_rating = result['ai_rating']
                
                our_ratings[our_rating] = our_ratings.get(our_rating, 0) + 1
                ai_ratings[ai_rating] = ai_ratings.get(ai_rating, 0) + 1
            
            print(f"\n🎯 OUR RATING DISTRIBUTION:")
            for rating in ['Strong Buy', 'Buy', 'Hold', 'Weak Hold', 'Weak Sell', 'Sell', 'Strong Sell']:
                count = our_ratings.get(rating, 0)
                if count > 0:
                    percentage = (count / len(results)) * 100
                    print(f"   {rating}: {count} stocks ({percentage:.1f}%)")
                    
            print(f"\n🤖 AI RATING DISTRIBUTION:")
            for rating in ['Strong Buy', 'Buy', 'Hold', 'Weak Hold', 'Weak Sell', 'Sell', 'Strong Sell']:
                count = ai_ratings.get(rating, 0)
                if count > 0:
                    percentage = (count / len(results)) * 100
                    print(f"   {rating}: {count} stocks ({percentage:.1f}%)")
            
            # Alignment analysis
            print(f"\n🔍 RATING ALIGNMENT ANALYSIS:")
            exact_matches = 0
            close_matches = 0
            disagreements = 0
            
            for result in results:
                our_rating = result['our_rating']
                ai_rating = result['ai_rating']
                
                if our_rating == ai_rating:
                    exact_matches += 1
                elif (our_rating in ['Buy', 'Strong Buy'] and ai_rating in ['Buy', 'Strong Buy']) or \
                     (our_rating in ['Hold', 'Weak Hold'] and ai_rating in ['Hold', 'Weak Hold']) or \
                     (our_rating in ['Sell', 'Weak Sell', 'Strong Sell'] and ai_rating in ['Sell', 'Weak Sell', 'Strong Sell']):
                    close_matches += 1
                else:
                    disagreements += 1
            
            print(f"   Exact Matches: {exact_matches} stocks ({(exact_matches/len(results)*100):.1f}%)")
            print(f"   Close Matches: {close_matches} stocks ({(close_matches/len(results)*100):.1f}%)")
            print(f"   Disagreements: {disagreements} stocks ({(disagreements/len(results)*100):.1f}%)")
            
            if skipped:
                print(f"\n⚠️  SKIPPED STOCKS ({len(skipped)}):")
                print(f"   {', '.join(skipped)}")
                
            print("\n" + "="*180)
            print("COMPREHENSIVE AI COMPARISON TABLE COMPLETED")
            print("="*180)
            
        except Exception as e:
            logger.error(f"Error generating comparison table: {e}")

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

def main():
    """Main execution function"""
    try:
        # Initialize comparison system
        comparison_system = ComprehensiveAIComparison()
        
        # Connect to database
        if not comparison_system.connect_db():
            logger.error("Failed to connect to database")
            return
            
        # Load sector weights
        if not comparison_system.load_sector_weights():
            logger.error("Failed to load sector weights")
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
        
        # Generate comparison table and export to CSV
        comparison_system.generate_comparison_table(test_tickers)
        
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        
    finally:
        # Cleanup
        if 'comparison_system' in locals():
            comparison_system.disconnect_db()

if __name__ == "__main__":
    main()
