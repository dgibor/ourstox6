"""
Score Schema Manager

Handles creation and maintenance of score-related database tables.
"""

import logging
from typing import Dict, List
from ..database import DatabaseManager

logger = logging.getLogger(__name__)


class ScoreSchemaManager:
    """Manages database schema for score tables"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()
        
    def create_tables(self) -> bool:
        """Create all score-related tables if they don't exist"""
        results = {}
        
        try:
            self.db.connect()
            
            # Create optimized daily_scores table
            results['daily_scores'] = self._create_daily_scores_table()
            
            # Create sector thresholds table
            results['sector_thresholds'] = self._create_sector_thresholds_table()
            
            # Create indexes for performance
            self._create_indexes()
            
            logger.info("Score tables created successfully")
            return all(results.values())
            
        except Exception as e:
            logger.error(f"❌ Error creating score tables: {e}")
            return False
        finally:
            self.db.disconnect()
    
    def _create_daily_scores_table(self) -> bool:
        """Create optimized daily_scores table"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS daily_scores (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                calculation_date DATE NOT NULL,
                
                -- Technical Scores
                price_position_trend_score INTEGER,
                momentum_cluster_score INTEGER,
                volume_confirmation_score INTEGER,
                trend_direction_score INTEGER,
                volatility_risk_score INTEGER,
                swing_trader_score INTEGER,
                momentum_trader_score INTEGER,
                long_term_investor_score INTEGER,
                volume_ratio DECIMAL(10,4),
                
                -- Fundamental Scores
                valuation_score INTEGER,
                quality_score INTEGER,
                growth_score INTEGER,
                financial_health_score INTEGER,
                management_score INTEGER,
                moat_score INTEGER,
                risk_score INTEGER,
                conservative_investor_score INTEGER,
                garp_investor_score INTEGER,
                deep_value_investor_score INTEGER,
                sector VARCHAR(100),
                industry VARCHAR(100),
                
                -- Analyst Scores
                earnings_proximity_score INTEGER,
                earnings_surprise_score INTEGER,
                analyst_sentiment_score INTEGER,
                price_target_score INTEGER,
                revision_score INTEGER,
                composite_analyst_score INTEGER,
                
                -- Metadata
                technical_data_quality_score INTEGER,
                fundamental_data_quality_score INTEGER,
                analyst_data_quality_score INTEGER,
                technical_calculation_status VARCHAR(20),
                fundamental_calculation_status VARCHAR(20),
                analyst_calculation_status VARCHAR(20),
                technical_error_message TEXT,
                fundamental_error_message TEXT,
                analyst_error_message TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(ticker, calculation_date)
            )
            """
            self.db.execute_update(query)
            return True
            
        except Exception as e:
            logger.error(f"Error creating daily_scores table: {e}")
            return False
    

    

    
    def _create_sector_thresholds_table(self) -> bool:
        """Create sector_thresholds table"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS sector_thresholds (
                id SERIAL PRIMARY KEY,
                sector VARCHAR(50) NOT NULL,
                industry VARCHAR(50),
                
                -- Valuation Thresholds
                pe_ratio_good_threshold NUMERIC(8,4),
                pe_ratio_bad_threshold NUMERIC(8,4),
                pb_ratio_good_threshold NUMERIC(8,4),
                pb_ratio_bad_threshold NUMERIC(8,4),
                ev_ebitda_good_threshold NUMERIC(8,4),
                ev_ebitda_bad_threshold NUMERIC(8,4),
                
                -- Financial Health Thresholds
                current_ratio_good_threshold NUMERIC(8,4),
                current_ratio_bad_threshold NUMERIC(8,4),
                debt_equity_good_threshold NUMERIC(8,4),
                debt_equity_bad_threshold NUMERIC(8,4),
                altman_z_good_threshold NUMERIC(8,4),
                altman_z_bad_threshold NUMERIC(8,4),
                
                -- Quality Thresholds
                roe_good_threshold NUMERIC(8,4),
                roe_bad_threshold NUMERIC(8,4),
                roic_good_threshold NUMERIC(8,4),
                roic_bad_threshold NUMERIC(8,4),
                
                -- Growth Thresholds
                revenue_growth_good_threshold NUMERIC(8,4),
                revenue_growth_bad_threshold NUMERIC(8,4),
                earnings_growth_good_threshold NUMERIC(8,4),
                earnings_growth_bad_threshold NUMERIC(8,4),
                
                -- Metadata
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(sector, industry)
            )
            """
            self.db.execute_update(query)
            return True
            
        except Exception as e:
            logger.error(f"Error creating sector_thresholds table: {e}")
            return False
    
    def _create_indexes(self):
        """Create performance indexes for score tables"""
        try:
            # Daily Scores Indexes
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_scores_ticker_date ON daily_scores(ticker, calculation_date DESC)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_scores_date ON daily_scores(calculation_date DESC)")
            
            # Technical Score Indexes
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_swing_score ON daily_scores(swing_trader_score DESC, calculation_date DESC)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_momentum_score ON daily_scores(momentum_trader_score DESC, calculation_date DESC)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_longterm_score ON daily_scores(long_term_investor_score DESC, calculation_date DESC)")
            
            # Fundamental Score Indexes
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_conservative_score ON daily_scores(conservative_investor_score DESC, calculation_date DESC)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_garp_score ON daily_scores(garp_investor_score DESC, calculation_date DESC)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_deepvalue_score ON daily_scores(deep_value_investor_score DESC, calculation_date DESC)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_sector ON daily_scores(sector, calculation_date DESC)")
            
            # Analyst Score Indexes
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_daily_analyst_score ON daily_scores(composite_analyst_score DESC, calculation_date DESC)")
            
            # Sector Thresholds Indexes
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_sector_thresholds_sector ON sector_thresholds(sector, industry)")
            
            logger.info("Score table indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def cleanup_old_scores(self, days_to_keep: int = 100) -> Dict[str, int]:
        """Clean up old score records beyond retention period"""
        results = {}
        
        try:
            self.db.connect()
            
            # Clean up daily scores
            query = """
            DELETE FROM daily_scores 
            WHERE calculation_date < CURRENT_DATE - INTERVAL '%s days'
            """
            deleted = self.db.execute_update(query, (days_to_keep,))
            results['daily_scores'] = deleted
            
            logger.info(f"Cleaned up old scores: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error cleaning up old scores: {e}")
            return {k: 0 for k in results.keys()}
        finally:
            self.db.disconnect() 