#!/usr/bin/env python3
"""
Analyst Scorer

Calculates comprehensive analyst scores based on earnings data, analyst recommendations,
price targets, and other market indicators.
"""

import logging
import json
from typing import Dict, Optional, List
from datetime import date, datetime, timedelta

# Use absolute imports for better compatibility
from database import DatabaseManager

logger = logging.getLogger(__name__)


class AnalystScorer:
    """Calculates analyst scores for stocks based on multiple data sources"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        
        # Industry-specific adjustments for analyst scoring
        self.industry_analyst_adjustments = {
            'Technology': 5,      # Tech stocks get slight boost
            'Healthcare': 3,      # Healthcare gets moderate boost
            'Financial Services': -2,  # Financials get slight penalty
            'Energy': -3,         # Energy gets moderate penalty
            'Consumer Cyclical': 1,    # Consumer discretionary gets slight boost
            'Consumer Defensive': 2,   # Consumer staples get slight boost
            'Industrials': 0,     # Industrials neutral
            'Basic Materials': -1,     # Materials get slight penalty
            'Real Estate': -2,    # Real estate gets slight penalty
            'Utilities': 1,       # Utilities get slight boost
            'Communication Services': 2,  # Communications get slight boost
        }
        
        # Qualitative bonuses for market leaders and strong companies
        self.qualitative_analyst_bonuses = {
            'AAPL': 12,   # Apple - strong brand, consistent performance
            'MSFT': 10,   # Microsoft - cloud leader, strong fundamentals
            'GOOGL': 8,   # Google - search monopoly, strong ad business
            'AMZN': 8,    # Amazon - e-commerce leader, AWS growth
            'NVDA': 10,   # NVIDIA - AI chip leader, strong growth
            'TSLA': 6,    # Tesla - EV leader, innovative
            'META': 6,    # Meta - social media leader
            'BRK.A': 8,   # Berkshire Hathaway - strong management
            'JPM': 4,     # JPMorgan - strong banking franchise
            'V': 6,       # Visa - payment processing leader
        }
        
        # REMOVED: self._ensure_database_schema() - No database creation needed
    
    def get_earnings_calendar_data(self, ticker: str) -> Optional[Dict]:
        """Get earnings calendar data for a ticker using multi-account system"""
        try:
            # Try to get from multi-account Finnhub first
            try:
                from finnhub_multi_account_manager import FinnhubMultiAccountManager
                finnhub_manager = FinnhubMultiAccountManager()
                earnings_data = finnhub_manager.get_earnings_calendar(ticker)
                finnhub_manager.close()
                
                if earnings_data:
                    return {'earnings_calendar': earnings_data}
            except ImportError:
                pass
            
            # Fallback to single API key if multi-account not available
            try:
                from finnhub_service import FinnhubService
                finnhub = FinnhubService()
                earnings_data = finnhub.get_earnings_calendar(ticker)
                if earnings_data:
                    return {'earnings_calendar': earnings_data}
            except ImportError:
                pass
            
            # Fallback to database
            query = """
            SELECT next_earnings_date, sector
            FROM stocks 
            WHERE ticker = %s
            """
            results = self.db.execute_query(query, (ticker,))
            if results and results[0]:
                next_earnings = results[0][0]
                sector = results[0][1]
                
                if next_earnings:
                    days_until = (next_earnings - date.today()).days
                    return {
                        'next_earnings': {
                            'date': next_earnings,
                            'days_until_earnings': days_until
                        },
                        'sector': sector
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting earnings calendar data for {ticker}: {e}")
            return None
    
    def get_analyst_recommendations(self, ticker: str) -> Optional[Dict]:
        """Get analyst recommendations and estimates from Finnhub using multi-account system"""
        try:
            # Try to get from multi-account Finnhub system first
            try:
                from finnhub_multi_account_manager import FinnhubMultiAccountManager
                finnhub_manager = FinnhubMultiAccountManager()
                recommendations = finnhub_manager.get_analyst_recommendations(ticker)
                finnhub_manager.close()
                
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
                    return self._get_analyst_recommendations_from_db(ticker)
            except ImportError:
                # Fallback to single API key if multi-account not available
                try:
                    from finnhub_service import FinnhubService
                    finnhub = FinnhubService()
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
                        return self._get_analyst_recommendations_from_db(ticker)
                except ImportError:
                    return self._get_analyst_recommendations_from_db(ticker)
        except Exception as e:
            logger.error(f"Error getting analyst recommendations for {ticker}: {e}")
            return self._get_analyst_recommendations_from_db(ticker)
    
    def _get_analyst_recommendations_from_db(self, ticker: str) -> Dict:
        """Fallback: Get analyst recommendations from database using correct table names"""
        try:
            # First check if the required tables exist
            table_check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'analyst_rating_trends'
            );
            """
            
            table_exists = self.db.execute_query(table_check_query)
            if not table_exists or not table_exists[0][0]:
                logger.debug(f"analyst_rating_trends table does not exist for {ticker}")
                return self._get_default_recommendations()
            
            # Get analyst ratings from analyst_rating_trends table
            ratings_query = """
            SELECT 
                strong_buy_count, buy_count, hold_count, sell_count, strong_sell_count,
                total_analysts, consensus_rating, consensus_score
            FROM analyst_rating_trends 
            WHERE ticker = %s 
            ORDER BY period_date DESC 
            LIMIT 1
            """
            
            ratings_results = self.db.execute_query(ratings_query, (ticker,))
            
            # Get price targets from analyst_targets table
            targets_query = """
            SELECT 
                avg_target_price, high_target_price, low_target_price, num_analysts,
                upside_potential, confidence_level
            FROM analyst_targets 
            WHERE ticker = %s
            """
            
            targets_results = self.db.execute_query(targets_query, (ticker,))
            
            # Combine the data
            result = {
                'buy_count': 0,
                'hold_count': 0,
                'sell_count': 0,
                'strong_buy_count': 0,
                'strong_sell_count': 0,
                'price_target': None,
                'price_target_percent': None,
                'revision_count': 0
            }
            
            # Extract ratings data
            if ratings_results and ratings_results[0]:
                row = ratings_results[0]
                result.update({
                    'strong_buy_count': row[0] or 0,
                    'buy_count': row[1] or 0,
                    'hold_count': row[2] or 0,
                    'sell_count': row[3] or 0,
                    'strong_sell_count': row[4] or 0,
                    'revision_count': row[5] or 0  # total_analysts as revision count
                })
            
            # Extract targets data
            if targets_results and targets_results[0]:
                row = targets_results[0]
                result.update({
                    'price_target': row[0],  # avg_target_price
                    'price_target_percent': row[4]  # upside_potential
                })
            
            return result
            
        except Exception as e:
            logger.debug(f"Database fallback failed for {ticker}: {e}")
            return self._get_default_recommendations()
    
    def _get_default_recommendations(self) -> Dict:
        """Return default neutral recommendations when database access fails"""
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
            if not earnings_data or not earnings_data.get('earnings_calendar'):
                logger.warning(f"Missing earnings surprise data, defaulting to 50")
                return 50
            
            # For now, return neutral score since we don't have historical surprise data
            # In a real implementation, this would analyze actual vs expected earnings
            logger.warning(f"No recent earnings data, defaulting to 50")
            return 50
            
        except Exception as e:
            logger.error(f"Error calculating earnings surprise score: {e}")
            return 50
    
    def calculate_analyst_sentiment_score(self, recommendations: Dict) -> int:
        """Calculate score based on analyst recommendations"""
        try:
            if not recommendations:
                logger.warning(f"Missing analyst recommendations, defaulting to 50")
                return 50
            
            buy_count = recommendations.get('buy_count', 0)
            hold_count = recommendations.get('hold_count', 0)
            sell_count = recommendations.get('sell_count', 0)
            strong_buy_count = recommendations.get('strong_buy_count', 0)
            strong_sell_count = recommendations.get('strong_sell_count', 0)
            
            if buy_count == 0 and hold_count == 0 and sell_count == 0:
                logger.warning(f"No analyst recommendations, defaulting to 50")
                return 50
            
            # Calculate weighted score
            total_recommendations = buy_count + hold_count + sell_count + strong_buy_count + strong_sell_count
            
            if total_recommendations == 0:
                return 50
            
            # Weight strong buy/sell more heavily
            weighted_score = (
                (strong_buy_count * 2) + buy_count - sell_count - (strong_sell_count * 2)
            ) / total_recommendations
            
            # Convert to 0-100 scale
            score = 50 + (weighted_score * 25)
            return max(0, min(100, int(score)))
            
        except Exception as e:
            logger.error(f"Error calculating analyst sentiment score: {e}")
            return 50
    
    def calculate_price_target_score(self, recommendations: Dict, current_price: float) -> int:
        """Calculate score based on price target vs current price"""
        try:
            if not recommendations or not current_price:
                logger.warning(f"Missing price target or current price, defaulting to 50")
                return 50
            
            price_target = recommendations.get('price_target')
            if not price_target:
                return 50
            
            # Calculate upside potential
            upside = (price_target - current_price) / current_price
            
            # Score based on upside potential
            if upside >= 0.5:
                return 90  # Very high upside
            elif upside >= 0.3:
                return 80  # High upside
            elif upside >= 0.2:
                return 70  # Good upside
            elif upside >= 0.1:
                return 60  # Moderate upside
            elif upside >= 0:
                return 50  # Neutral
            elif upside >= -0.1:
                return 40  # Slight downside
            elif upside >= -0.2:
                return 30  # Moderate downside
            else:
                return 20  # Significant downside
            
        except Exception as e:
            logger.error(f"Error calculating price target score: {e}")
            return 50
    
    def calculate_revision_score(self, recommendations: Dict) -> int:
        """Calculate score based on estimate revisions"""
        try:
            if not recommendations:
                logger.warning(f"Missing revision data, defaulting to 50")
                return 50
            
            revision_count = recommendations.get('revision_count', 0)
            
            # Score based on revision activity (more revisions = more analyst interest)
            if revision_count >= 10:
                return 90  # Very high analyst interest
            elif revision_count >= 7:
                return 80  # High analyst interest
            elif revision_count >= 5:
                return 70  # Good analyst interest
            elif revision_count >= 3:
                return 60  # Moderate analyst interest
            elif revision_count >= 1:
                return 50  # Some analyst interest
            else:
                return 40  # Low analyst interest
            
        except Exception as e:
            logger.error(f"Error calculating revision score: {e}")
            return 50
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        try:
            # First check if the daily_charts table exists
            table_check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'daily_charts'
            );
            """
            
            table_exists = self.db.execute_query(table_check_query)
            if not table_exists or not table_exists[0][0]:
                logger.debug(f"daily_charts table does not exist for {ticker}")
                return None
            
            # Try to get from daily_charts table (which actually exists)
            query = """
            SELECT close 
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            results = self.db.execute_query(query, (ticker,))
            if results and results[0]:
                return float(results[0][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return None
    
    def calculate_composite_analyst_score(self, component_scores: Dict) -> int:
        """Calculate composite analyst score from component scores"""
        try:
            # Weight the component scores
            weights = {
                'earnings_proximity': 0.25,
                'earnings_surprise': 0.20,
                'analyst_sentiment': 0.25,
                'price_target': 0.20,
                'revision': 0.10
            }
            
            composite_score = 0
            for component, weight in weights.items():
                score = component_scores.get(component, 50)
                composite_score += score * weight
            
            return int(composite_score)
            
        except Exception as e:
            logger.error(f"Error calculating composite analyst score: {e}")
            return 50
    
    def calculate_data_quality_score(self, earnings_data: Dict, recommendations: Dict) -> int:
        """Calculate data quality score based on available data"""
        try:
            quality_score = 0
            max_score = 100
            
            # Earnings data quality
            if earnings_data and earnings_data.get('next_earnings'):
                quality_score += 30
            elif earnings_data:
                quality_score += 15
            
            # Recommendations quality
            if recommendations:
                rec_count = sum([
                    recommendations.get('buy_count', 0),
                    recommendations.get('hold_count', 0),
                    recommendations.get('sell_count', 0)
                ])
                if rec_count > 0:
                    quality_score += 40
                elif recommendations.get('price_target'):
                    quality_score += 20
            
            # Price data quality
            if earnings_data and earnings_data.get('sector'):
                quality_score += 30
            
            return min(max_score, quality_score)
            
        except Exception as e:
            logger.error(f"Error calculating data quality score: {e}")
            return 0
    
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
                'industry_adjustment': score_data.get('industry_adjustment'),
                'qualitative_bonus': score_data.get('qualitative_bonus'),
                'data_quality_score': score_data.get('data_quality_score')
            }
            
            # Check if record already exists
            check_query = "SELECT id FROM enhanced_scores WHERE ticker = %s ORDER BY calculation_date DESC LIMIT 1"
            existing = self.db.execute_query(check_query, (ticker,))
            
            if existing:
                # Update existing record
                update_query = """
                UPDATE enhanced_scores 
                SET analyst_score = %s, analyst_components = %s, calculation_date = %s
                WHERE ticker = %s AND calculation_date = (
                    SELECT MAX(calculation_date) FROM enhanced_scores WHERE ticker = %s
                )
                """
                self.db.execute_query(update_query, (
                    score_data.get('composite_analyst_score'),
                    json.dumps(analyst_components),
                    datetime.now(),
                    ticker,
                    ticker
                ))
            else:
                # Insert new record
                insert_query = """
                INSERT INTO enhanced_scores (
                    ticker, analyst_score, analyst_components, calculation_date
                ) VALUES (%s, %s, %s, %s)
                """
                self.db.execute_query(insert_query, (
                    ticker,
                    score_data.get('composite_analyst_score'),
                    json.dumps(analyst_components),
                    datetime.now()
                ))
            
            logger.info(f"Stored analyst score for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing analyst score for {ticker}: {e}")
            return False
