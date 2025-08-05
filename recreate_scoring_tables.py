import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def recreate_scoring_tables():
    """Completely drop and recreate scoring tables with correct schema"""
    
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432')
    )
    
    cursor = conn.cursor()
    
    try:
        print("Dropping existing scoring tables and views...")
        
        # Drop materialized views first
        cursor.execute("""
            DROP MATERIALIZED VIEW IF EXISTS screener_summary_view CASCADE;
        """)
        
        cursor.execute("""
            DROP MATERIALIZED VIEW IF EXISTS score_trends_view CASCADE;
        """)
        
        # Drop regular views
        cursor.execute("""
            DROP VIEW IF EXISTS screener_filters_view CASCADE;
        """)
        
        cursor.execute("""
            DROP VIEW IF EXISTS dashboard_metrics_view CASCADE;
        """)
        
        # Drop functions
        cursor.execute("""
            DROP FUNCTION IF EXISTS calculate_trend_indicators CASCADE;
        """)
        
        cursor.execute("""
            DROP FUNCTION IF EXISTS upsert_company_scores CASCADE;
        """)
        
        # Drop tables
        cursor.execute("""
            DROP TABLE IF EXISTS company_scores_historical CASCADE;
        """)
        
        cursor.execute("""
            DROP TABLE IF EXISTS company_scores_current CASCADE;
        """)
        
        cursor.execute("""
            DROP TABLE IF EXISTS score_calculation_logs CASCADE;
        """)
        
        conn.commit()
        print("Successfully dropped all existing scoring objects")
        
        # Create tables with correct schema
        print("Creating tables with correct schema...")
        
        cursor.execute("""
            CREATE TABLE company_scores_current (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                calculation_date DATE NOT NULL,
                
                -- Fundamental Scores (0-100)
                fundamental_health_score DECIMAL(5,2),
                value_investment_score DECIMAL(5,2),
                fundamental_risk_score DECIMAL(5,2),
                
                -- Technical Scores (0-100)
                technical_health_score DECIMAL(5,2),
                trading_signal_score DECIMAL(5,2),
                technical_risk_score DECIMAL(5,2),
                
                -- Overall Score (0-100)
                overall_score DECIMAL(5,2),
                
                -- Grades (VARCHAR(20) for proper length)
                fundamental_health_grade VARCHAR(20) CHECK (fundamental_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                value_rating VARCHAR(20) CHECK (value_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                technical_health_grade VARCHAR(20) CHECK (technical_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                overall_grade VARCHAR(20) CHECK (overall_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                
                -- Descriptions
                fundamental_health_description TEXT,
                value_investment_description TEXT,
                fundamental_risk_description TEXT,
                technical_health_description TEXT,
                trading_signal_description TEXT,
                technical_risk_description TEXT,
                overall_description TEXT,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(ticker, calculation_date)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE company_scores_historical (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                calculation_date DATE NOT NULL,
                
                -- Fundamental Scores (0-100)
                fundamental_health_score DECIMAL(5,2),
                value_investment_score DECIMAL(5,2),
                fundamental_risk_score DECIMAL(5,2),
                
                -- Technical Scores (0-100)
                technical_health_score DECIMAL(5,2),
                trading_signal_score DECIMAL(5,2),
                technical_risk_score DECIMAL(5,2),
                
                -- Overall Score (0-100)
                overall_score DECIMAL(5,2),
                
                -- Grades (VARCHAR(20) for proper length)
                fundamental_health_grade VARCHAR(20) CHECK (fundamental_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                value_rating VARCHAR(20) CHECK (value_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                technical_health_grade VARCHAR(20) CHECK (technical_health_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
                overall_grade VARCHAR(20) CHECK (overall_grade IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy')),
                
                -- Descriptions
                fundamental_health_description TEXT,
                value_investment_description TEXT,
                fundamental_risk_description TEXT,
                technical_health_description TEXT,
                trading_signal_description TEXT,
                technical_risk_description TEXT,
                overall_description TEXT,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(ticker, calculation_date)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE score_calculation_logs (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                calculation_date DATE NOT NULL,
                score_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                error_message TEXT,
                calculation_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_company_scores_current_ticker ON company_scores_current(ticker);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_company_scores_current_date ON company_scores_current(calculation_date);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_company_scores_historical_ticker ON company_scores_historical(ticker);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_company_scores_historical_date ON company_scores_historical(calculation_date);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_score_logs_ticker ON score_calculation_logs(ticker);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_score_logs_date ON score_calculation_logs(calculation_date);
        """)
        
        conn.commit()
        print("Successfully created all scoring tables with correct schema")
        
        # Verify the schema
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'company_scores_current' 
            AND column_name IN ('fundamental_health_grade', 'technical_health_grade', 'overall_grade')
            ORDER BY column_name;
        """)
        
        results = cursor.fetchall()
        print("\nVerification of grade column lengths:")
        for row in results:
            print(f"{row[0]}: {row[1]}({row[2]})")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    recreate_scoring_tables() 