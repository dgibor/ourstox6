#!/usr/bin/env python3
"""
Analyst Scorer for Daily Run System

Calculates analyst sentiment scores using earnings calendar data
and analyst recommendations/estimates. Integrated with the daily
trading system for comprehensive scoring.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta

try:
    from .database import DatabaseManager
except ImportError:
    from database import DatabaseManager

logger = logging.getLogger(__name__)


class AnalystScorer:
    """Calculates analyst sentiment scores using earnings and analyst data"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        
        # Enhanced industry-specific adjustments for analyst scoring
        self.industry_analyst_adjustments = {
            'Technology': 15,      # Higher growth expectations, AI leadership
            'Healthcare': 10,      # Stable cash flows, innovation premium
            'Financial': 5,        # Higher leverage acceptable, but conservative
            'Energy': -5,          # Cyclical nature, but less penalty
            'Consumer': 8,         # Brand value, consumer resilience
            'Communication Services': 12,  # High growth potential, digital transformation
            'Industrials': 3,      # Moderate growth, infrastructure
            'Materials': 2,        # Commodity exposure, but recovery potential
            'Real Estate': 4,      # Stable income, inflation hedge
            'Utilities': 1         # Low growth, but defensive and dividend yield
        }
        
        # Enhanced qualitative bonuses for market leaders
        self.qualitative_analyst_bonuses = {
            'AAPL': 12,   # Strong brand, ecosystem, AI integration
            'MSFT': 15,   # Cloud leadership, AI dominance
            'GOOGL': 12,  # Search dominance, AI innovation
            'NVDA': 18,   # AI leadership, chip dominance
            'TSLA': 10,   # EV leadership, innovation
            'AMZN': 12,   # E-commerce dominance, cloud services
            'META': 8,    # Social media leadership, metaverse
            'BRK-B': 6,   # Diversified conglomerate, value investing
            'JPM': 8,     # Banking leadership, financial strength
            'JNJ': 8,     # Healthcare leadership, stability
            'PG': 6,      # Consumer staples leadership, defensive
            'XOM': 4,     # Energy leadership, dividend yield
            'CVX': 4,     # Energy leadership, dividend yield
            'HD': 8,      # Home improvement leadership, housing market
            'DIS': 8,     # Entertainment leadership, streaming
            'NFLX': 6,    # Streaming leadership, content
            'CRM': 8,     # SaaS leadership, enterprise software
            'ADBE': 8,    # Software leadership, creative tools
            'PYPL': 6,    # Fintech leadership, digital payments
            'INTC': 4     # Semiconductor leadership, manufacturing
        }
        
        # Ensure database schema is ready
        self._ensure_database_schema()
    
    def _ensure_database_schema(self):
        """Ensure the database schema is ready for analyst scoring"""
        try:
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
            
            # Add analyst_score column if it doesn't exist
            add_analyst_column_query = """
            ALTER TABLE enhanced_scores 
            ADD COLUMN IF NOT EXISTS analyst_score DECIMAL(5,2),
            ADD COLUMN IF NOT EXISTS analyst_components JSONB;
            """
            
            conn = self.db.connection
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            cursor.execute(add_analyst_column_query)
            conn.commit()
            cursor.close()
            
            logger.info("Database schema ensured for analyst scoring")
            
        except Exception as e:
            logger.error(f"Error ensuring database schema: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
    
    def get_earnings_calendar_data(self, ticker: str) -> Optional[Dict]:
        """Get earnings calendar data for a ticker"""
        try:
            query = """
            SELECT 
                earnings_date, earnings_time, estimate_eps, actual_eps,
                estimate_revenue, actual_revenue
            FROM earnings_calendar 
            WHERE ticker = %s 
            ORDER BY earnings_date DESC 
            LIMIT 5
            """
            
            results = self.db.execute_query(query, (ticker,))
            if not results:
                return None
            
            # Get most recent earnings and next earnings
            recent_earnings = []
            next_earnings = None
            
            for row in results:
                earnings_data = {
                    'earnings_date': row[0],
                    'earnings_time': row[1],
                    'estimate_eps': row[2],
                    'actual_eps': row[3],
                    'estimate_revenue': row[4],
                    'actual_revenue': row[5],
                    'days_until_earnings': (row[0] - date.today()).days if row[0] else None
                }
                
                if earnings_data['earnings_date'] <= date.today():
                    recent_earnings.append(earnings_data)
                else:
                    next_earnings = earnings_data
            
            return {
                'recent_earnings': recent_earnings,
                'next_earnings': next_earnings
            }
            
        except Exception as e:
            logger.error(f"Error getting earnings calendar data for {ticker}: {e}")
            return None
    
    def get_analyst_recommendations(self, ticker: str) -> Optional[Dict]:
        """Get analyst recommendations and estimates from Finnhub"""
        try:
            # Import Finnhub service
            try:
                from .finnhub_service import FinnhubService
                finnhub = FinnhubService()
            except ImportError:
                from finnhub_service import FinnhubService
                finnhub = FinnhubService()
            
            # Get analyst recommendations from Finnhub
            recommendations = finnhub.get_analyst_recommendations(ticker)
            
            if recommendations:
                return {
                    'buy_count': recommendations.get('buy', 0),
                    'hold_count': recommendations.get('hold', 0),
                    'sell_count': recommendations.get('sell', 0),
                    'strong_buy_count': recommendations.get('strongBuy', 0),
                    'strong_sell_count': recommendations.get('strongSell', 0),
                    'price_target': recommendations.get('targetMean', None),
                    'price_target_percent': recommendations.get('targetMedian', None),
                    'revision_count': recommendations.get('revisionCount', 0)
                }
            else:
                # Fallback to database if available
                return self._get_analyst_recommendations_from_db(ticker)
            
        except Exception as e:
            logger.error(f"Error getting analyst recommendations for {ticker}: {e}")
            return self._get_analyst_recommendations_from_db(ticker)
    
    def _get_analyst_recommendations_from_db(self, ticker: str) -> Dict:
        """Fallback: Get analyst recommendations from database"""
        try:
            query = """
            SELECT 
                buy_count, hold_count, sell_count, strong_buy_count, strong_sell_count,
                price_target, price_target_percent, revision_count
            FROM analyst_recommendations 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            
            results = self.db.execute_query(query, (ticker,))
            if results and results[0]:
                row = results[0]
                return {
                    'buy_count': row[0] or 0,
                    'hold_count': row[1] or 0,
                    'strong_buy_count': row[3] or 0,
                    'strong_sell_count': row[4] or 0,
                    'price_target': row[5],
                    'price_target_percent': row[6],
                    'revision_count': row[7] or 0
                }
        except Exception as e:
            logger.debug(f"Database fallback failed for {ticker}: {e}")
        
        # Final fallback: neutral data
        return {
            'buy_count': 0,
            'hold_count': 0,
            'sell_count': 0,
            'strong_buy_count': 0,
            'strong_sell_count': 0,
            'price_target': None,
            'price_target_percent': None,
            'revision_count': 0
        }
    
    def calculate_earnings_proximity_score(self, earnings_data: Dict) -> int:
        """Calculate score based on proximity to earnings"""
        try:
            if not earnings_data or not earnings_data.get('next_earnings'):
                logger.warning(f"Missing earnings proximity data, defaulting to 50")
                return 50  # Neutral if no earnings data
            
            days_until = earnings_data['next_earnings'].get('days_until_earnings', 365)
            
            # Score based on proximity (closer = higher score)
            if days_until <= 7:
                return 90  # Very high - earnings very soon
            elif days_until <= 14:
                return 80  # High - earnings within 2 weeks
            elif days_until <= 30:
                return 70  # Good - earnings within month
            elif days_until <= 60:
                return 60  # Moderate - earnings within 2 months
            elif days_until <= 90:
                return 50  # Neutral - earnings within 3 months
            else:
                return 30  # Low - earnings far away
            
        except Exception as e:
            logger.error(f"Error calculating earnings proximity score: {e}")
            return 50
    
    def calculate_earnings_surprise_score(self, earnings_data: Dict) -> int:
        """Calculate score based on recent earnings surprises"""
        try:
            if not earnings_data or not earnings_data.get('recent_earnings'):
                logger.warning(f"Missing earnings surprise data, defaulting to 50")
                return 50  # Neutral if no recent earnings
            
            recent_earnings = earnings_data['recent_earnings']
            if not recent_earnings:
                logger.warning(f"No recent earnings data, defaulting to 50")
                return 50
            
            # Calculate surprises based on actual vs estimate
            eps_surprises = []
            revenue_surprises = []
            
            for earnings in recent_earnings[:4]:  # Last 4 quarters
                if earnings.get('estimate_eps') and earnings.get('actual_eps'):
                    surprise = ((earnings['actual_eps'] - earnings['estimate_eps']) / earnings['estimate_eps']) * 100
                    eps_surprises.append(surprise)
                if earnings.get('estimate_revenue') and earnings.get('actual_revenue'):
                    surprise = ((earnings['actual_revenue'] - earnings['estimate_revenue']) / earnings['estimate_revenue']) * 100
                    revenue_surprises.append(surprise)
            
            if not eps_surprises and not revenue_surprises:
                logger.warning(f"No EPS or revenue surprises, defaulting to 50")
                return 50
            
            # Calculate average surprises
            avg_eps_surprise = sum(eps_surprises) / len(eps_surprises) if eps_surprises else 0
            avg_revenue_surprise = sum(revenue_surprises) / len(revenue_surprises) if revenue_surprises else 0
            
            # Score based on positive surprises
            total_surprise = (avg_eps_surprise + avg_revenue_surprise) / 2
            
            if total_surprise >= 10:
                return 90  # Very high - consistently beating estimates
            elif total_surprise >= 5:
                return 80  # High - usually beating estimates
            elif total_surprise >= 0:
                return 70  # Good - meeting or slightly beating estimates
            elif total_surprise >= -5:
                return 50  # Neutral - slightly missing estimates
            elif total_surprise >= -10:
                return 30  # Poor - missing estimates
            else:
                return 10  # Very poor - consistently missing estimates
            
        except Exception as e:
            logger.error(f"Error calculating earnings surprise score: {e}")
            return 50
    
    def calculate_analyst_sentiment_score(self, recommendations: Dict) -> int:
        """Calculate score based on analyst recommendations"""
        try:
            if not recommendations:
                logger.warning(f"Missing analyst recommendations, defaulting to 50")
                return 50  # Neutral if no recommendations
            
            buy_count = recommendations.get('buy_count', 0)
            hold_count = recommendations.get('hold_count', 0)
            sell_count = recommendations.get('sell_count', 0)
            strong_buy_count = recommendations.get('strong_buy_count', 0)
            strong_sell_count = recommendations.get('strong_sell_count', 0)
            
            total_recommendations = buy_count + hold_count + sell_count + strong_buy_count + strong_sell_count
            
            if total_recommendations == 0:
                logger.warning(f"No analyst recommendations, defaulting to 50")
                return 50  # Neutral if no recommendations
            
            # Calculate weighted score
            # Strong Buy = 5, Buy = 4, Hold = 3, Sell = 2, Strong Sell = 1
            weighted_score = (
                (strong_buy_count * 5) + 
                (buy_count * 4) + 
                (hold_count * 3) + 
                (sell_count * 2) + 
                (strong_sell_count * 1)
            )
            
            average_score = weighted_score / total_recommendations
            
            # Convert to 0-100 scale
            sentiment_score = int((average_score - 1) * 25)  # 1-5 scale to 0-100
            return max(0, min(100, sentiment_score))
            
        except Exception as e:
            logger.error(f"Error calculating analyst sentiment score: {e}")
            return 50
    
    def calculate_price_target_score(self, recommendations: Dict, current_price: float) -> int:
        """Calculate score based on price target vs current price"""
        try:
            if not recommendations or not recommendations.get('price_target') or not current_price:
                logger.warning(f"Missing price target or current price, defaulting to 50")
                return 50  # Neutral if no price target
            
            price_target = recommendations['price_target']
            target_percent = recommendations.get('price_target_percent')
            
            if target_percent is not None:
                # Use provided percentage
                upside = target_percent
            else:
                # Calculate upside manually
                upside = ((price_target - current_price) / current_price) * 100
            
            # Score based on upside potential
            if upside >= 50:
                return 90  # Very high upside
            elif upside >= 30:
                return 80  # High upside
            elif upside >= 20:
                return 70  # Good upside
            elif upside >= 10:
                return 60  # Moderate upside
            elif upside >= 0:
                return 50  # Neutral
            elif upside >= -10:
                return 40  # Slight downside
            elif upside >= -20:
                return 30  # Moderate downside
            else:
                return 20  # Significant downside
            
        except Exception as e:
            logger.error(f"Error calculating price target score: {e}")
            return 50
    
    def calculate_revision_score(self, recommendations: Dict) -> int:
        """Calculate score based on recent estimate revisions"""
        try:
            if not recommendations:
                logger.warning(f"Missing revision data, defaulting to 50")
                return 50  # Neutral if no revision data
            
            revision_count = recommendations.get('revision_count', 0)
            
            # Score based on number of upward revisions
            if revision_count >= 5:
                return 90  # Many upward revisions
            elif revision_count >= 3:
                return 80  # Several upward revisions
            elif revision_count >= 1:
                return 70  # Some upward revisions
            elif revision_count == 0:
                return 50  # No revisions
            elif revision_count >= -3:
                return 30  # Some downward revisions
            else:
                return 20  # Many downward revisions
            
        except Exception as e:
            logger.error(f"Error calculating revision score: {e}")
            return 50
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current stock price"""
        try:
            query = """
            SELECT close 
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query, (ticker,))
            if result and result[0][0]:
                return float(result[0][0]) / 100.0  # Convert from cents
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return None
    
    def calculate_composite_analyst_score(self, component_scores: Dict) -> int:
        """Calculate composite analyst score from component scores"""
        try:
            # Weight the component scores
            weights = {
                'earnings_proximity_score': 0.25,
                'earnings_surprise_score': 0.25,
                'analyst_sentiment_score': 0.20,
                'price_target_score': 0.20,
                'revision_score': 0.10
            }
            
            total_score = 0
            total_weight = 0
            
            for component, weight in weights.items():
                score = component_scores.get(component, 50)
                total_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                composite_score = int(total_score / total_weight)
                return max(0, min(100, composite_score))
            else:
                return 50
            
        except Exception as e:
            logger.error(f"Error calculating composite analyst score: {e}")
            return 50
    
    def calculate_data_quality_score(self, earnings_data: Dict, recommendations: Dict) -> int:
        """Calculate data quality score based on available data"""
        try:
            quality_factors = 0
            total_factors = 0
            
            # Check earnings data
            if earnings_data:
                total_factors += 1
                if earnings_data.get('next_earnings'):
                    quality_factors += 1
                if earnings_data.get('recent_earnings'):
                    quality_factors += 1
            
            # Check recommendations data
            if recommendations:
                total_factors += 1
                if recommendations.get('buy_count') is not None:
                    quality_factors += 1
                if recommendations.get('price_target') is not None:
                    quality_factors += 1
            
            if total_factors == 0:
                return 0
            
            quality_score = int((quality_factors / total_factors) * 100)
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating data quality score: {e}")
            return 50
    
    def calculate_analyst_score(self, ticker: str, calculation_date: date = None) -> Dict:
        """Calculate complete analyst score for a ticker"""
        try:
            if calculation_date is None:
                calculation_date = date.today()
            
            # Get earnings calendar data
            earnings_data = self.get_earnings_calendar_data(ticker)
            
            # Get analyst recommendations
            recommendations = self.get_analyst_recommendations(ticker)
            
            # Get current price for price target calculations
            current_price = self.get_current_price(ticker)
            if recommendations and current_price:
                recommendations['current_price'] = current_price
            
            # Calculate component scores
            component_scores = {
                'earnings_proximity_score': self.calculate_earnings_proximity_score(earnings_data),
                'earnings_surprise_score': self.calculate_earnings_surprise_score(earnings_data),
                'analyst_sentiment_score': self.calculate_analyst_sentiment_score(recommendations),
                'price_target_score': self.calculate_price_target_score(recommendations, current_price),
                'revision_score': self.calculate_revision_score(recommendations)
            }
            
            # Calculate composite score
            composite_score = self.calculate_composite_analyst_score(component_scores)
            
            # Calculate data quality score
            data_quality_score = self.calculate_data_quality_score(earnings_data, recommendations)
            
            # Apply industry adjustments
            industry_adjustment = self._get_industry_adjustment(ticker)
            adjusted_composite_score = min(100, max(0, composite_score + industry_adjustment))
            
            # Apply qualitative bonuses
            qualitative_bonus = self._get_qualitative_bonus(ticker)
            final_composite_score = min(100, max(0, adjusted_composite_score + qualitative_bonus))
            
            # Determine calculation status
            if data_quality_score >= 80:
                calculation_status = 'success'
            elif data_quality_score >= 50:
                calculation_status = 'partial'
            else:
                calculation_status = 'failed'
            
            # Compile final result
            result = {
                **component_scores,
                'composite_analyst_score': final_composite_score,
                'adjusted_composite_score': adjusted_composite_score,
                'data_quality_score': data_quality_score,
                'calculation_status': calculation_status,
                'industry_adjustment': industry_adjustment,
                'qualitative_bonus': qualitative_bonus,
                'error_message': None,
                'calculation_date': calculation_date
            }
            
            logger.info(f"Calculated analyst score for {ticker}: {final_composite_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating analyst score for {ticker}: {e}")
            return {
                'calculation_status': 'failed',
                'error_message': str(e),
                'data_quality_score': 0,
                'composite_analyst_score': 50
            }
    
    def _get_industry_adjustment(self, ticker: str) -> int:
        """Get industry-specific adjustment for analyst scoring"""
        try:
            # Get sector from stocks table
            query = "SELECT sector FROM stocks WHERE ticker = %s"
            result = self.db.execute_query(query, (ticker,))
            
            if result and result[0][0]:
                sector = result[0][0]
                return self.industry_analyst_adjustments.get(sector, 0)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting industry adjustment for {ticker}: {e}")
            return 0
    
    def _get_qualitative_bonus(self, ticker: str) -> int:
        """Get qualitative bonus for market leaders"""
        return self.qualitative_analyst_bonuses.get(ticker, 0)
    
    def store_analyst_score(self, ticker: str, score_data: Dict) -> bool:
        """Store analyst score in the database"""
        try:
            import json
            analyst_components = {
                'earnings_proximity_score': score_data.get('earnings_proximity_score'),
                'earnings_surprise_score': score_data.get('earnings_surprise_score'),
                'analyst_sentiment_score': score_data.get('analyst_sentiment_score'),
                'price_target_score': score_data.get('price_target_score'),
                'revision_score': score_data.get('revision_score'),
                'data_quality_score': score_data.get('data_quality_score'),
                'calculation_status': score_data.get('calculation_status')
            }
            
            # Use simple insert (allow duplicates)
            simple_insert_query = """
            INSERT INTO enhanced_scores 
            (ticker, analyst_score, analyst_components, calculation_date)
            VALUES (%s, %s, %s, %s)
            """
            
            conn = self.db.connection
            cursor = conn.cursor()
            cursor.execute(simple_insert_query, (
                ticker,
                score_data.get('composite_analyst_score'),
                json.dumps(analyst_components),
                score_data.get('calculation_date')
            ))
            
            conn.commit()
            cursor.close()
            logger.info(f"Stored analyst score for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing analyst score for {ticker}: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
