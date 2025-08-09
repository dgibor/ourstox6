#!/usr/bin/env python3
"""
Update database schema with enhanced upsert function and sentiment columns
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_database_schema():
    """Update database schema with enhanced upsert function and sentiment columns"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Read and execute the enhanced upsert function SQL
        with open('enhanced_upsert_function.sql', 'r') as f:
            sql_content = f.read()
        
        print("Executing enhanced upsert function SQL...")
        cursor.execute(sql_content)
        
        print("Enhanced upsert function created successfully")
        
        # Check if sentiment columns exist
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'company_scores_current' AND column_name = 'sentiment_analysis'
        """)
        
        if cursor.fetchone():
            print("Sentiment columns already exist in company_scores_current")
        else:
            print("Adding sentiment columns to company_scores_current...")
            cursor.execute("""
                ALTER TABLE company_scores_current 
                ADD COLUMN sentiment_analysis JSONB,
                ADD COLUMN sentiment_score DECIMAL(5,2),
                ADD COLUMN sentiment_grade VARCHAR(20),
                ADD COLUMN sentiment_source VARCHAR(50)
            """)
            print("Sentiment columns added to company_scores_current")
        
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'company_scores_historical' AND column_name = 'sentiment_analysis'
        """)
        
        if cursor.fetchone():
            print("Sentiment columns already exist in company_scores_historical")
        else:
            print("Adding sentiment columns to company_scores_historical...")
            cursor.execute("""
                ALTER TABLE company_scores_historical 
                ADD COLUMN sentiment_analysis JSONB,
                ADD COLUMN sentiment_score DECIMAL(5,2),
                ADD COLUMN sentiment_grade VARCHAR(20),
                ADD COLUMN sentiment_source VARCHAR(50)
            """)
            print("Sentiment columns added to company_scores_historical")
        
        # Create indexes for sentiment columns
        print("Creating sentiment indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_company_scores_sentiment_score ON company_scores_current(sentiment_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_company_scores_sentiment_grade ON company_scores_current(sentiment_grade)",
            "CREATE INDEX IF NOT EXISTS idx_company_scores_sentiment_source ON company_scores_current(sentiment_source)",
            "CREATE INDEX IF NOT EXISTS idx_company_scores_historical_sentiment_score ON company_scores_historical(sentiment_score DESC, date_calculated)",
            "CREATE INDEX IF NOT EXISTS idx_company_scores_historical_sentiment_grade ON company_scores_historical(sentiment_grade, date_calculated)",
            "CREATE INDEX IF NOT EXISTS idx_company_scores_historical_sentiment_source ON company_scores_historical(sentiment_source, date_calculated)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            print(f"Index created: {index_sql.split()[-1]}")
        
        print("Database schema update completed successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    success = update_database_schema()
    sys.exit(0 if success else 1)

