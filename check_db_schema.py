#!/usr/bin/env python3
"""
Check database schema for scoring tables
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_schema():
    """Check the current schema of scoring tables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # Check company_scores_current table
        print("=== COMPANY_SCORES_CURRENT TABLE ===")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'company_scores_current'
            ORDER BY ordinal_position
        """)
        
        current_columns = cursor.fetchall()
        for col in current_columns:
            print(f"{col[0]}: {col[1]}{'(' + str(col[2]) + ')' if col[2] else ''}")
        
        print("\n=== COMPANY_SCORES_HISTORICAL TABLE ===")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'company_scores_historical'
            ORDER BY ordinal_position
        """)
        
        historical_columns = cursor.fetchall()
        for col in historical_columns:
            print(f"{col[0]}: {col[1]}{'(' + str(col[2]) + ')' if col[2] else ''}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_schema() 