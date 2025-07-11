"""
Score Database Manager

Handles database operations for score tables including storage, retrieval, and data management.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from ..database import DatabaseManager

logger = logging.getLogger(__name__)


class ScoreDatabaseManager:
    """Manages database operations for score tables"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
    
    def store_technical_score(self, ticker: str, calculation_date: date, score_data: Dict) -> bool:
        """Store technical score data"""
        try:
            query = """
            INSERT INTO daily_scores (
                ticker, calculation_date, 
                price_position_trend_score, momentum_cluster_score,
                volume_confirmation_score, trend_direction_score, volatility_risk_score,
                swing_trader_score, momentum_trader_score, long_term_investor_score,
                volume_ratio, technical_data_quality_score, technical_calculation_status, 
                technical_error_message
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (ticker, calculation_date) 
            DO UPDATE SET
                price_position_trend_score = EXCLUDED.price_position_trend_score,
                momentum_cluster_score = EXCLUDED.momentum_cluster_score,
                volume_confirmation_score = EXCLUDED.volume_confirmation_score,
                trend_direction_score = EXCLUDED.trend_direction_score,
                volatility_risk_score = EXCLUDED.volatility_risk_score,
                swing_trader_score = EXCLUDED.swing_trader_score,
                momentum_trader_score = EXCLUDED.momentum_trader_score,
                long_term_investor_score = EXCLUDED.long_term_investor_score,
                volume_ratio = EXCLUDED.volume_ratio,
                technical_data_quality_score = EXCLUDED.technical_data_quality_score,
                technical_calculation_status = EXCLUDED.technical_calculation_status,
                technical_error_message = EXCLUDED.technical_error_message,
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = (
                ticker, calculation_date,
                score_data.get('price_position_trend_score'),
                score_data.get('momentum_cluster_score'),
                score_data.get('volume_confirmation_score'),
                score_data.get('trend_direction_score'),
                score_data.get('volatility_risk_score'),
                score_data.get('swing_trader_score'),
                score_data.get('momentum_trader_score'),
                score_data.get('long_term_investor_score'),
                score_data.get('volume_ratio'),
                score_data.get('data_quality_score'),
                score_data.get('calculation_status'),
                score_data.get('error_message')
            )
            
            self.db.execute_update(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error storing technical score for {ticker}: {e}")
            return False
    
    def store_fundamental_score(self, ticker: str, calculation_date: date, score_data: Dict) -> bool:
        """Store fundamental score data"""
        try:
            query = """
            INSERT INTO daily_scores (
                ticker, calculation_date, 
                valuation_score, quality_score, growth_score, financial_health_score,
                management_score, moat_score, risk_score,
                conservative_investor_score, garp_investor_score, deep_value_investor_score,
                sector, industry, fundamental_data_quality_score, fundamental_calculation_status, 
                fundamental_error_message
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (ticker, calculation_date) 
            DO UPDATE SET
                valuation_score = EXCLUDED.valuation_score,
                quality_score = EXCLUDED.quality_score,
                growth_score = EXCLUDED.growth_score,
                financial_health_score = EXCLUDED.financial_health_score,
                management_score = EXCLUDED.management_score,
                moat_score = EXCLUDED.moat_score,
                risk_score = EXCLUDED.risk_score,
                conservative_investor_score = EXCLUDED.conservative_investor_score,
                garp_investor_score = EXCLUDED.garp_investor_score,
                deep_value_investor_score = EXCLUDED.deep_value_investor_score,
                sector = EXCLUDED.sector,
                industry = EXCLUDED.industry,
                fundamental_data_quality_score = EXCLUDED.fundamental_data_quality_score,
                fundamental_calculation_status = EXCLUDED.fundamental_calculation_status,
                fundamental_error_message = EXCLUDED.fundamental_error_message,
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = (
                ticker, calculation_date,
                score_data.get('valuation_score'),
                score_data.get('quality_score'),
                score_data.get('growth_score'),
                score_data.get('financial_health_score'),
                score_data.get('management_score'),
                score_data.get('moat_score'),
                score_data.get('risk_score'),
                score_data.get('conservative_investor_score'),
                score_data.get('garp_investor_score'),
                score_data.get('deep_value_investor_score'),
                score_data.get('sector'),
                score_data.get('industry'),
                score_data.get('data_quality_score'),
                score_data.get('calculation_status'),
                score_data.get('error_message')
            )
            
            self.db.execute_update(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error storing fundamental score for {ticker}: {e}")
            return False
    
    def store_analyst_score(self, ticker: str, calculation_date: date, score_data: Dict) -> bool:
        """Store analyst score data"""
        try:
            query = """
            INSERT INTO daily_scores (
                ticker, calculation_date, 
                earnings_proximity_score, earnings_surprise_score, analyst_sentiment_score,
                price_target_score, revision_score, composite_analyst_score,
                analyst_data_quality_score, analyst_calculation_status, analyst_error_message
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (ticker, calculation_date) 
            DO UPDATE SET
                earnings_proximity_score = EXCLUDED.earnings_proximity_score,
                earnings_surprise_score = EXCLUDED.earnings_surprise_score,
                analyst_sentiment_score = EXCLUDED.analyst_sentiment_score,
                price_target_score = EXCLUDED.price_target_score,
                revision_score = EXCLUDED.revision_score,
                composite_analyst_score = EXCLUDED.composite_analyst_score,
                analyst_data_quality_score = EXCLUDED.analyst_data_quality_score,
                analyst_calculation_status = EXCLUDED.analyst_calculation_status,
                analyst_error_message = EXCLUDED.analyst_error_message,
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = (
                ticker, calculation_date,
                score_data.get('earnings_proximity_score'),
                score_data.get('earnings_surprise_score'),
                score_data.get('analyst_sentiment_score'),
                score_data.get('price_target_score'),
                score_data.get('revision_score'),
                score_data.get('composite_analyst_score'),
                score_data.get('data_quality_score'),
                score_data.get('calculation_status'),
                score_data.get('error_message')
            )
            
            self.db.execute_update(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error storing analyst score for {ticker}: {e}")
            return False
    
    def get_previous_technical_score(self, ticker: str, calculation_date: date) -> Optional[Dict]:
        """Get the most recent technical score before the given date"""
        try:
            query = """
            SELECT * FROM daily_scores 
            WHERE ticker = %s AND calculation_date < %s
            ORDER BY calculation_date DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query, (ticker, calculation_date))
            if result:
                return dict(zip([col[0] for col in self.db.cursor.description], result[0]))
            return None
            
        except Exception as e:
            logger.error(f"Error getting previous technical score for {ticker}: {e}")
            return None
    
    def get_previous_fundamental_score(self, ticker: str, calculation_date: date) -> Optional[Dict]:
        """Get the most recent fundamental score before the given date"""
        try:
            query = """
            SELECT * FROM daily_scores 
            WHERE ticker = %s AND calculation_date < %s
            ORDER BY calculation_date DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query, (ticker, calculation_date))
            if result:
                return dict(zip([col[0] for col in self.db.cursor.description], result[0]))
            return None
            
        except Exception as e:
            logger.error(f"Error getting previous fundamental score for {ticker}: {e}")
            return None
    
    def get_previous_analyst_score(self, ticker: str, calculation_date: date) -> Optional[Dict]:
        """Get the most recent analyst score before the given date"""
        try:
            query = """
            SELECT * FROM daily_scores 
            WHERE ticker = %s AND calculation_date < %s
            ORDER BY calculation_date DESC 
            LIMIT 1
            """
            
            result = self.db.execute_query(query, (ticker, calculation_date))
            if result:
                return dict(zip([col[0] for col in self.db.cursor.description], result[0]))
            return None
            
        except Exception as e:
            logger.error(f"Error getting previous analyst score for {ticker}: {e}")
            return None
    
    def get_stocks_with_earnings_soon(self, days_ahead: int = 30) -> List[Tuple[str, date]]:
        """Get stocks with earnings coming up soon"""
        try:
            query = """
            SELECT ticker, next_earnings_date 
            FROM stocks 
            WHERE next_earnings_date IS NOT NULL 
            AND next_earnings_date <= CURRENT_DATE + INTERVAL '%s days'
            ORDER BY next_earnings_date ASC
            """
            
            results = self.db.execute_query(query, (days_ahead,))
            return [(row[0], row[1]) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting stocks with earnings soon: {e}")
            return []
    
    def get_all_active_tickers(self) -> List[str]:
        """Get all active tickers from stocks table"""
        try:
            query = "SELECT ticker FROM stocks WHERE active = true ORDER BY ticker"
            results = self.db.execute_query(query)
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting active tickers: {e}")
            return []
    
    def get_score_summary(self, calculation_date: date) -> Dict:
        """Get summary of scores calculated for a given date"""
        try:
            summary = {}
            
            # Combined scores summary from daily_scores table
            query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN technical_calculation_status = 'success' THEN 1 END) as technical_successful,
                COUNT(CASE WHEN fundamental_calculation_status = 'success' THEN 1 END) as fundamental_successful,
                COUNT(CASE WHEN analyst_calculation_status = 'success' THEN 1 END) as analyst_successful,
                AVG(swing_trader_score) as avg_swing_score,
                AVG(momentum_trader_score) as avg_momentum_score,
                AVG(long_term_investor_score) as avg_longterm_score,
                AVG(conservative_investor_score) as avg_conservative_score,
                AVG(garp_investor_score) as avg_garp_score,
                AVG(deep_value_investor_score) as avg_deepvalue_score,
                AVG(composite_analyst_score) as avg_analyst_score
            FROM daily_scores 
            WHERE calculation_date = %s
            """
            result = self.db.execute_query(query, (calculation_date,))
            if result:
                summary['combined'] = dict(zip([
                    'total', 'technical_successful', 'fundamental_successful', 'analyst_successful',
                    'avg_swing_score', 'avg_momentum_score', 'avg_longterm_score',
                    'avg_conservative_score', 'avg_garp_score', 'avg_deepvalue_score', 'avg_analyst_score'
                ], result[0]))
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting score summary: {e}")
            return {} 