#!/usr/bin/env python3
"""
Complete fix for database schema for scoring tables
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_schema_complete():
    """Complete fix for the schema by dropping views, altering columns, and recreating views"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # Step 1: Drop materialized views that depend on the columns
        print("Step 1: Dropping materialized views...")
        drop_queries = [
            "DROP MATERIALIZED VIEW IF EXISTS screener_summary_view CASCADE;",
            "DROP MATERIALIZED VIEW IF EXISTS score_trends_view CASCADE;"
        ]
        
        for query in drop_queries:
            try:
                cursor.execute(query)
                print(f"✅ Executed: {query}")
            except Exception as e:
                print(f"⚠️  Warning for {query}: {e}")
        
        # Step 2: Alter columns in current table
        print("\nStep 2: Fixing company_scores_current table...")
        alter_queries = [
            "ALTER TABLE company_scores_current ALTER COLUMN fundamental_health_grade TYPE VARCHAR(20);",
            "ALTER TABLE company_scores_current ALTER COLUMN technical_health_grade TYPE VARCHAR(20);",
            "ALTER TABLE company_scores_current ALTER COLUMN overall_grade TYPE VARCHAR(20);"
        ]
        
        for query in alter_queries:
            try:
                cursor.execute(query)
                print(f"✅ Executed: {query}")
            except Exception as e:
                print(f"⚠️  Warning for {query}: {e}")
        
        # Step 3: Alter columns in historical table
        print("\nStep 3: Fixing company_scores_historical table...")
        alter_queries = [
            "ALTER TABLE company_scores_historical ALTER COLUMN fundamental_health_grade TYPE VARCHAR(20);",
            "ALTER TABLE company_scores_historical ALTER COLUMN technical_health_grade TYPE VARCHAR(20);",
            "ALTER TABLE company_scores_historical ALTER COLUMN overall_grade TYPE VARCHAR(20);"
        ]
        
        for query in alter_queries:
            try:
                cursor.execute(query)
                print(f"✅ Executed: {query}")
            except Exception as e:
                print(f"⚠️  Warning for {query}: {e}")
        
        # Step 4: Update check constraints
        print("\nStep 4: Updating check constraints...")
        constraint_queries = [
            "ALTER TABLE company_scores_current DROP CONSTRAINT IF EXISTS company_scores_current_fundamental_health_grade_check;",
            "ALTER TABLE company_scores_current ADD CONSTRAINT company_scores_current_fundamental_health_grade_check CHECK (fundamental_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'));",
            "ALTER TABLE company_scores_current DROP CONSTRAINT IF EXISTS company_scores_current_technical_health_grade_check;",
            "ALTER TABLE company_scores_current ADD CONSTRAINT company_scores_current_technical_health_grade_check CHECK (technical_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'));",
            "ALTER TABLE company_scores_current DROP CONSTRAINT IF EXISTS company_scores_current_overall_grade_check;",
            "ALTER TABLE company_scores_current ADD CONSTRAINT company_scores_current_overall_grade_check CHECK (overall_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'));",
            "ALTER TABLE company_scores_historical DROP CONSTRAINT IF EXISTS company_scores_historical_fundamental_health_grade_check;",
            "ALTER TABLE company_scores_historical ADD CONSTRAINT company_scores_historical_fundamental_health_grade_check CHECK (fundamental_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'));",
            "ALTER TABLE company_scores_historical DROP CONSTRAINT IF EXISTS company_scores_historical_technical_health_grade_check;",
            "ALTER TABLE company_scores_historical ADD CONSTRAINT company_scores_historical_technical_health_grade_check CHECK (technical_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'));",
            "ALTER TABLE company_scores_historical DROP CONSTRAINT IF EXISTS company_scores_historical_overall_grade_check;",
            "ALTER TABLE company_scores_historical ADD CONSTRAINT company_scores_historical_overall_grade_check CHECK (overall_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell'));"
        ]
        
        for query in constraint_queries:
            try:
                cursor.execute(query)
                print(f"✅ Executed: {query}")
            except Exception as e:
                print(f"⚠️  Warning for {query}: {e}")
        
        # Step 5: Recreate materialized views
        print("\nStep 5: Recreating materialized views...")
        
        # Recreate screener_summary_view
        screener_view_query = """
        CREATE MATERIALIZED VIEW screener_summary_view AS
        SELECT 
            csc.ticker,
            s.company_name,
            s.sector,
            s.market_cap,
            csc.current_price,
            csc.fundamental_health_score,
            csc.fundamental_health_grade,
            csc.fundamental_risk_score,
            csc.fundamental_risk_level,
            csc.value_investment_score,
            csc.value_rating,
            csc.technical_health_score,
            csc.technical_health_grade,
            csc.trading_signal_score,
            csc.trading_signal_rating,
            csc.technical_risk_score,
            csc.technical_risk_level,
            csc.overall_score,
            csc.overall_grade,
            csc.date_calculated,
            csc.calculation_timestamp
        FROM company_scores_current csc
        LEFT JOIN stocks s ON csc.ticker = s.ticker
        WHERE csc.fundamental_health_score IS NOT NULL
        ORDER BY csc.overall_score DESC;
        """
        
        try:
            cursor.execute(screener_view_query)
            print("✅ Recreated screener_summary_view")
        except Exception as e:
            print(f"⚠️  Warning recreating screener_summary_view: {e}")
        
        # Recreate score_trends_view
        trends_view_query = """
        CREATE MATERIALIZED VIEW score_trends_view AS
        SELECT 
            csh.ticker,
            csh.date_calculated,
            csh.fundamental_health_score,
            csh.fundamental_health_grade,
            csh.fundamental_risk_score,
            csh.fundamental_risk_level,
            csh.value_investment_score,
            csh.value_rating,
            csh.technical_health_score,
            csh.technical_health_grade,
            csh.trading_signal_score,
            csh.trading_signal_rating,
            csh.technical_risk_score,
            csh.technical_risk_level,
            csh.overall_score,
            csh.overall_grade
        FROM company_scores_historical csh
        WHERE csh.fundamental_health_score IS NOT NULL
        ORDER BY csh.ticker, csh.date_calculated DESC;
        """
        
        try:
            cursor.execute(trends_view_query)
            print("✅ Recreated score_trends_view")
        except Exception as e:
            print(f"⚠️  Warning recreating score_trends_view: {e}")
        
        # Step 6: Create indexes on materialized views
        print("\nStep 6: Creating indexes on materialized views...")
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_screener_summary_fundamental ON screener_summary_view(fundamental_health_score DESC);",
            "CREATE INDEX IF NOT EXISTS idx_screener_summary_technical ON screener_summary_view(technical_health_score DESC);",
            "CREATE INDEX IF NOT EXISTS idx_screener_summary_trading ON screener_summary_view(trading_signal_score DESC);",
            "CREATE INDEX IF NOT EXISTS idx_screener_summary_overall ON screener_summary_view(overall_score DESC);",
            "CREATE INDEX IF NOT EXISTS idx_screener_summary_sector ON screener_summary_view(sector);",
            "CREATE INDEX IF NOT EXISTS idx_screener_summary_market_cap ON screener_summary_view(market_cap DESC);",
            "CREATE INDEX IF NOT EXISTS idx_score_trends_ticker_date ON score_trends_view(ticker, date_calculated DESC);"
        ]
        
        for query in index_queries:
            try:
                cursor.execute(query)
                print(f"✅ Executed: {query}")
            except Exception as e:
                print(f"⚠️  Warning for {query}: {e}")
        
        conn.commit()
        print("\n✅ Complete schema fixes completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")

if __name__ == "__main__":
    fix_schema_complete() 