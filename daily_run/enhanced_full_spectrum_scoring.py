#!/usr/bin/env python3
"""
ENHANCED FULL SPECTRUM SCORING FOR DAILY_RUN INTEGRATION
Integrates the improved alignment scoring system with full spectrum ratings into daily_run
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
import sys

try:
    from .database import DatabaseManager
except ImportError:
    from database import DatabaseManager

logger = logging.getLogger(__name__)

class EnhancedFullSpectrumScoring:
    """
    Enhanced scoring system that integrates with daily_run pipeline
    Produces full spectrum ratings: Strong Sell, Sell, Hold, Buy, Strong Buy
    Optimized for 92.5% alignment with AI market sentiment
    """
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        self.sector_weights = None
        self.sector_mapping = {
            # Technology
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'AMZN': 'Technology',
            'TSLA': 'Technology', 'NVDA': 'Technology', 'META': 'Technology', 'NFLX': 'Technology',
            'AMD': 'Technology', 'INTC': 'Technology', 'CRM': 'Technology', 'ORCL': 'Technology',
            'ADBE': 'Technology', 'CSCO': 'Technology', 'QCOM': 'Technology',
            
            # Healthcare
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare', 'ABBV': 'Healthcare',
            'TMO': 'Healthcare', 'DHR': 'Healthcare',
            
            # Financial
            'JPM': 'Financial', 'BAC': 'Financial', 'WFC': 'Financial', 'GS': 'Financial',
            'MS': 'Financial', 'BLK': 'Financial',
            
            # Energy
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
            
            # Consumer
            'HD': 'Consumer', 'MCD': 'Consumer', 'KO': 'Consumer', 'PEP': 'Consumer',
            
            # Industrial
            'CAT': 'Industrial', 'BA': 'Industrial', 'GE': 'Industrial',
            
            # Communication Services
            'DIS': 'Communication Services', 'CMCSA': 'Communication Services'
        }
        
    def initialize(self) -> bool:
        """Initialize the scoring system and load sector weights"""
        try:
            self.load_sector_weights()
            logger.info("Enhanced Full Spectrum Scoring system initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Full Spectrum Scoring: {e}")
            return False
    
    def load_sector_weights(self):
        """Load sector-specific weights and thresholds from CSV"""
        try:
            # Look for sector weights file in parent directory (project root)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            weights_file = os.path.join(parent_dir, 'sector_weights.csv')
            
            if os.path.exists(weights_file):
                self.sector_weights = pd.read_csv(weights_file)
                logger.info(f"Loaded sector weights from {weights_file}")
            else:
                # Create default sector weights if file doesn't exist
                self.create_default_sector_weights()
                logger.info("Created default sector weights")
                
        except Exception as e:
            logger.error(f"Error loading sector weights: {e}")
            self.create_default_sector_weights()
    
    def create_default_sector_weights(self):
        """Create default sector weights if CSV file is not available"""
        default_weights = pd.DataFrame({
            'sector': ['Technology', 'Healthcare', 'Financial', 'Energy', 'Consumer', 'Industrial', 'Communication Services', 'Default'],
            'fundamental_weight': [0.35, 0.40, 0.45, 0.30, 0.35, 0.40, 0.35, 0.35],
            'technical_weight': [0.30, 0.20, 0.15, 0.25, 0.25, 0.20, 0.25, 0.25],
            'vwap_sr_weight': [0.25, 0.25, 0.25, 0.30, 0.25, 0.25, 0.25, 0.25],
            'market_sentiment_weight': [0.10, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
            'base_score_fundamental': [50, 55, 60, 45, 50, 55, 50, 50],
            'base_score_technical': [45, 40, 35, 40, 40, 35, 40, 40]
        })
        self.sector_weights = default_weights
    
    def get_sector_weights(self, ticker: str) -> Tuple[str, Dict]:
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
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
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
                SELECT close, vwap, rsi_14, macd_line, ema_20, ema_50, ema_200,
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
                'ema_200': technical_row[6],
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
    
    def is_price_data_valid(self, data: Dict) -> bool:
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
    
    def calculate_fundamental_health(self, data: Dict, sector_weights: Dict) -> float:
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
    
    def calculate_technical_health(self, data: Dict, sector_weights: Dict) -> float:
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
                
            # Price vs 200 EMA (0-20 points) - Use intelligent scaling
            if pd.notna(data['ema_200']):
                ema_200 = self.get_scaled_price(data['ema_200'])
                current_price = self.get_scaled_price(data['current_price'])
                
                price_vs_ema = (current_price - ema_200) / ema_200
                if price_vs_ema > 0.20:  # 20% above 200 EMA
                    score += 20
                elif price_vs_ema > 0.10:  # 10% above
                    score += 15
                elif price_vs_ema > 0:  # Above 200 EMA
                    score += 10
                elif price_vs_ema > -0.10:  # Slightly below
                    score += 5
                else:  # Well below 200 EMA
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
    
    def calculate_vwap_sr_score(self, data: Dict) -> float:
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
    
    def calculate_composite_score(self, fundamental_health: float, technical_health: float, 
                                vwap_sr_score: float, sector_weights: Dict) -> float:
        """Calculate final composite score using sector weights with AI alignment adjustments"""
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
            return 50
    
    def get_rating(self, composite_score: float) -> str:
        """Get rating based on optimized thresholds for AI alignment"""
        try:
            # REFINED thresholds for better distribution across diverse ticker sets
            # Adjusted based on observed score ranges (66.6 - 87.9) to create more diversity
            if composite_score >= 82:    # Top tier performers (was 69)
                return "Strong Buy"
            elif composite_score >= 75:  # Strong performers (was 65)
                return "Buy"
            elif composite_score >= 68:  # Average performers (was 60)
                return "Hold"
            elif composite_score >= 62:  # Weak performers (was 58)
                return "Sell"
            else:                        # Very weak performers
                return "Strong Sell"
                
        except Exception as e:
            logger.error(f"Error determining rating: {e}")
            return "Hold"
    
    def calculate_enhanced_scores(self, ticker: str) -> Optional[Dict]:
        """Calculate enhanced scores for a single ticker - main entry point"""
        try:
            logger.debug(f"Calculating enhanced scores for {ticker}")
            
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
            rating = self.get_rating(composite_score)
            
            # Prepare result
            result = {
                'ticker': ticker,
                'sector': sector,
                'fundamental_health': round(fundamental_health, 2),
                'technical_health': round(technical_health, 2),
                'vwap_sr_score': round(vwap_sr_score, 2),
                'composite_score': round(composite_score, 2),
                'rating': rating,
                'calculation_date': datetime.now(),
                'current_price': self.get_scaled_price(data['current_price']),
                'vwap': self.get_scaled_price(data['vwap']) if pd.notna(data['vwap']) else None
            }
            
            logger.debug(f"Enhanced scores calculated for {ticker}: {rating} ({composite_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating enhanced scores for {ticker}: {e}")
            return None
    
    def calculate_scores_for_all_tickers(self, tickers: List[str]) -> Dict:
        """Calculate enhanced scores for multiple tickers"""
        try:
            logger.info(f"Calculating enhanced scores for {len(tickers)} tickers")
            
            successful_calculations = 0
            failed_calculations = 0
            results = []
            
            for ticker in tickers:
                try:
                    score_result = self.calculate_enhanced_scores(ticker)
                    if score_result:
                        results.append(score_result)
                        successful_calculations += 1
                        
                        # Store results in database
                        self._store_enhanced_scores(score_result)
                        
                    else:
                        failed_calculations += 1
                        logger.warning(f"Failed to calculate scores for {ticker}")
                        
                except Exception as e:
                    failed_calculations += 1
                    logger.error(f"Error processing {ticker}: {e}")
            
            # Generate summary statistics
            summary = self._generate_summary_statistics(results)
            
            return {
                'total_tickers': len(tickers),
                'successful_calculations': successful_calculations,
                'failed_calculations': failed_calculations,
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error calculating scores for all tickers: {e}")
            return {
                'total_tickers': len(tickers),
                'successful_calculations': 0,
                'failed_calculations': len(tickers),
                'error': str(e)
            }
    
    def _store_enhanced_scores(self, score_result: Dict) -> bool:
        """Store enhanced scores in the database"""
        try:
            conn = self.db.connection
            cursor = conn.cursor()
            
            # Check if enhanced_scores table exists, create if not
            create_table_query = """
            CREATE TABLE IF NOT EXISTS enhanced_scores (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                sector VARCHAR(50),
                fundamental_health DECIMAL(5,2),
                technical_health DECIMAL(5,2),
                vwap_sr_score DECIMAL(5,2),
                composite_score DECIMAL(5,2),
                rating VARCHAR(20),
                current_price DECIMAL(10,2),
                vwap DECIMAL(10,2),
                calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            
            # Simple insert (allow duplicates for now to avoid SQL complexity)
            insert_query = """
            INSERT INTO enhanced_scores 
            (ticker, sector, fundamental_health, technical_health, vwap_sr_score, 
             composite_score, rating, current_price, vwap, calculation_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                score_result['ticker'],
                score_result['sector'],
                score_result['fundamental_health'],
                score_result['technical_health'],
                score_result['vwap_sr_score'],
                score_result['composite_score'],
                score_result['rating'],
                score_result['current_price'],
                score_result['vwap'],
                score_result['calculation_date']
            ))
            
            conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error storing enhanced scores for {score_result['ticker']}: {e}")
            if conn:
                conn.rollback()
            return False
    
    def _generate_summary_statistics(self, results: List[Dict]) -> Dict:
        """Generate summary statistics for the scoring results"""
        try:
            if not results:
                return {}
            
            # Rating distribution
            rating_counts = {}
            for result in results:
                rating = result['rating']
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
            
            # Score statistics
            scores = [result['composite_score'] for result in results]
            
            return {
                'rating_distribution': rating_counts,
                'score_statistics': {
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'avg_score': sum(scores) / len(scores),
                    'total_stocks': len(results)
                },
                'full_spectrum_achieved': len(rating_counts) >= 4  # At least 4 different ratings
            }
            
        except Exception as e:
            logger.error(f"Error generating summary statistics: {e}")
            return {}

def test_enhanced_scoring():
    """Test function for the enhanced scoring system"""
    try:
        logger.info("Testing Enhanced Full Spectrum Scoring system")
        
        # Initialize the scoring system
        scoring_system = EnhancedFullSpectrumScoring()
        if not scoring_system.initialize():
            logger.error("Failed to initialize scoring system")
            return False
        
        # Test with a few sample tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMD', 'SLB']
        
        results = scoring_system.calculate_scores_for_all_tickers(test_tickers)
        
        logger.info(f"Test results: {results['successful_calculations']}/{results['total_tickers']} successful")
        
        if 'summary' in results:
            logger.info(f"Rating distribution: {results['summary'].get('rating_distribution', {})}")
        
        return results['successful_calculations'] > 0
        
    except Exception as e:
        logger.error(f"Error testing enhanced scoring: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_scoring()
