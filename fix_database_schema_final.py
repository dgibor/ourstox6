import os
import psycopg2
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def fix_database_schema():
    """Fix database schema by dropping and recreating scoring tables with correct constraints"""
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        logger.info("Starting database schema fix...")
        
        # Step 1: Drop materialized views that depend on scoring tables
        logger.info("Dropping materialized views...")
        cursor.execute("""
            DROP MATERIALIZED VIEW IF EXISTS screener_summary_view CASCADE;
        """)
        cursor.execute("""
            DROP MATERIALIZED VIEW IF EXISTS score_trends_view CASCADE;
        """)
        cursor.execute("""
            DROP MATERIALIZED VIEW IF EXISTS screener_filters_view CASCADE;
        """)
        cursor.execute("""
            DROP MATERIALIZED VIEW IF EXISTS dashboard_metrics_view CASCADE;
        """)
        
        # Step 2: Drop existing scoring tables
        logger.info("Dropping existing scoring tables...")
        cursor.execute("DROP TABLE IF EXISTS company_scores_current CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS company_scores_historical CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS score_calculation_logs CASCADE;")
        
        # Step 3: Recreate tables with correct constraints
        logger.info("Creating company_scores_current table...")
        cursor.execute("""
            CREATE TABLE company_scores_current (
                -- Primary Key
                ticker VARCHAR(10) PRIMARY KEY,
                
                -- Calculation Metadata
                date_calculated DATE NOT NULL,
                calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_freshness_hours INTEGER,
                
                -- Fundamental Health Scores
                fundamental_health_score DECIMAL(5,2) CHECK (fundamental_health_score >= 0 AND fundamental_health_score <= 100),
                fundamental_health_grade VARCHAR(20) CHECK (fundamental_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                fundamental_health_components JSONB,
                fundamental_health_description TEXT,
                
                -- Risk Assessment Scores
                fundamental_risk_score DECIMAL(5,2) CHECK (fundamental_risk_score >= 0 AND fundamental_risk_score <= 100),
                fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                fundamental_risk_components JSONB,
                fundamental_risk_description TEXT,
                
                -- Value Investment Scores
                value_investment_score DECIMAL(5,2) CHECK (value_investment_score >= 0 AND value_investment_score <= 100),
                value_rating VARCHAR(20) CHECK (value_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                value_components JSONB,
                value_investment_description TEXT,
                
                -- Technical Health Scores
                technical_health_score DECIMAL(5,2) CHECK (technical_health_score >= 0 AND technical_health_score <= 100),
                technical_health_grade VARCHAR(20) CHECK (technical_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                technical_health_components JSONB,
                technical_health_description TEXT,
                
                -- Trading Signal Scores
                trading_signal_score DECIMAL(5,2) CHECK (trading_signal_score >= 0 AND trading_signal_score <= 100),
                trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                trading_signal_components JSONB,
                trading_signal_description TEXT,
                
                -- Technical Risk Scores
                technical_risk_score DECIMAL(5,2) CHECK (technical_risk_score >= 0 AND technical_risk_score <= 100),
                technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                technical_risk_components JSONB,
                technical_risk_description TEXT,
                
                -- Trend Analysis
                fundamental_health_trend VARCHAR(20) CHECK (fundamental_health_trend IN ('improving', 'stable', 'declining')),
                technical_health_trend VARCHAR(20) CHECK (technical_health_trend IN ('improving', 'stable', 'declining')),
                trading_signal_trend VARCHAR(20) CHECK (trading_signal_trend IN ('improving', 'stable', 'declining')),
                
                -- Period Changes
                fundamental_health_change_3m DECIMAL(5,2),
                fundamental_health_change_6m DECIMAL(5,2),
                fundamental_health_change_1y DECIMAL(5,2),
                technical_health_change_3m DECIMAL(5,2),
                technical_health_change_6m DECIMAL(5,2),
                technical_health_change_1y DECIMAL(5,2),
                trading_signal_change_3m DECIMAL(5,2),
                trading_signal_change_6m DECIMAL(5,2),
                trading_signal_change_1y DECIMAL(5,2),
                
                -- Alert System
                fundamental_red_flags JSONB,
                fundamental_yellow_flags JSONB,
                technical_red_flags JSONB,
                technical_yellow_flags JSONB,
                
                -- Composite Scores
                overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
                overall_grade VARCHAR(20) CHECK (overall_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                overall_description TEXT,
                
                -- Data Quality Metrics
                data_confidence DECIMAL(5,2) CHECK (data_confidence >= 0 AND data_confidence <= 100),
                missing_metrics_count INTEGER,
                data_warnings JSONB,
                
                -- Metadata
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Foreign Key
                CONSTRAINT fk_company_scores_stocks FOREIGN KEY (ticker) REFERENCES stocks(ticker)
            );
        """)
        
        logger.info("Creating company_scores_historical table...")
        cursor.execute("""
            CREATE TABLE company_scores_historical (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                date_calculated DATE NOT NULL,
                
                -- Fundamental Scores
                fundamental_health_score DECIMAL(5,2),
                fundamental_health_grade VARCHAR(20) CHECK (fundamental_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                fundamental_risk_score DECIMAL(5,2),
                fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                value_investment_score DECIMAL(5,2),
                value_rating VARCHAR(20) CHECK (value_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                
                -- Technical Scores
                technical_health_score DECIMAL(5,2),
                technical_health_grade VARCHAR(20) CHECK (technical_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                trading_signal_score DECIMAL(5,2),
                trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                technical_risk_score DECIMAL(5,2),
                technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                
                -- Overall Score
                overall_score DECIMAL(5,2),
                overall_grade VARCHAR(20) CHECK (overall_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                
                -- Data Quality
                data_confidence DECIMAL(5,2),
                missing_metrics_count INTEGER,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                UNIQUE(ticker, date_calculated),
                CONSTRAINT fk_historical_scores_stocks FOREIGN KEY (ticker) REFERENCES stocks(ticker)
            );
        """)
        
        logger.info("Creating score_calculation_logs table...")
        cursor.execute("""
            CREATE TABLE score_calculation_logs (
                id SERIAL PRIMARY KEY,
                calculation_date DATE NOT NULL,
                calculation_batch_id VARCHAR(50),
                
                -- Processing Statistics
                total_tickers_processed INTEGER,
                successful_calculations INTEGER,
                failed_calculations INTEGER,
                skipped_calculations INTEGER,
                
                -- Performance Metrics
                calculation_duration_seconds DECIMAL(8,2),
                average_calculation_time_per_ticker DECIMAL(6,3),
                
                -- Data Quality Metrics
                tickers_with_missing_fundamental_data INTEGER,
                tickers_with_missing_technical_data INTEGER,
                tickers_with_incomplete_ratios INTEGER,
                
                -- Error Tracking
                error_summary JSONB,
                warning_summary JSONB,
                
                -- System Information
                system_version VARCHAR(20),
                calculation_version VARCHAR(20),
                
                -- Metadata
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Step 4: Create indexes for performance
        logger.info("Creating indexes...")
        cursor.execute("CREATE INDEX idx_company_scores_current_date ON company_scores_current(date_calculated);")
        cursor.execute("CREATE INDEX idx_company_scores_fundamental_health ON company_scores_current(fundamental_health_score DESC);")
        cursor.execute("CREATE INDEX idx_company_scores_technical_health ON company_scores_current(technical_health_score DESC);")
        cursor.execute("CREATE INDEX idx_company_scores_overall ON company_scores_current(overall_score DESC);")
        cursor.execute("CREATE INDEX idx_company_scores_risk ON company_scores_current(fundamental_risk_score ASC);")
        
        cursor.execute("CREATE INDEX idx_company_scores_historical_ticker_date ON company_scores_historical(ticker, date_calculated);")
        cursor.execute("CREATE INDEX idx_score_logs_date ON score_calculation_logs(calculation_date);")
        
        # Step 5: Create materialized views
        logger.info("Creating materialized views...")
        cursor.execute("""
            CREATE MATERIALIZED VIEW screener_summary_view AS
            SELECT 
                ticker,
                fundamental_health_score,
                fundamental_health_grade,
                technical_health_score,
                technical_health_grade,
                overall_score,
                overall_grade,
                fundamental_risk_level,
                technical_risk_level,
                data_confidence,
                date_calculated
            FROM company_scores_current
            WHERE date_calculated = (SELECT MAX(date_calculated) FROM company_scores_current);
        """)
        
        cursor.execute("""
            CREATE MATERIALIZED VIEW score_trends_view AS
            SELECT 
                ticker,
                date_calculated,
                fundamental_health_score,
                technical_health_score,
                overall_score
            FROM company_scores_historical
            ORDER BY ticker, date_calculated DESC;
        """)
        
        # Commit changes
        conn.commit()
        logger.info("Database schema fix completed successfully!")
        
        # Verify the fix
        logger.info("Verifying constraints...")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = 'company_scores_current'::regclass 
            AND conname LIKE '%technical_risk_level%';
        """)
        
        constraints = cursor.fetchall()
        for constraint in constraints:
            logger.info(f"Constraint: {constraint[0]}")
            logger.info(f"Definition: {constraint[1]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print("✅ Database schema fix completed successfully!")
    else:
        print("❌ Database schema fix failed!") 