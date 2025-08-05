#!/usr/bin/env python3
"""
Fix database schema for scoring tables
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_schema():
    """Fix the schema by altering columns to VARCHAR(20)"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # Alter columns in current table
        print("Fixing company_scores_current table...")
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
        
        # Alter columns in historical table
        print("\nFixing company_scores_historical table...")
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
        
        # Update check constraints
        print("\nUpdating check constraints...")
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
        
        conn.commit()
        print("\n✅ Schema fixes completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")

if __name__ == "__main__":
    fix_schema() 