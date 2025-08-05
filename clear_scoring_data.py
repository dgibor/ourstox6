#!/usr/bin/env python3
"""
Clear existing scoring data to test with fresh data
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clear_scoring_data():
    """Clear existing scoring data"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # Clear existing data
        print("Clearing existing scoring data...")
        clear_queries = [
            "DELETE FROM company_scores_historical;",
            "DELETE FROM company_scores_current;",
            "DELETE FROM score_calculation_logs;"
        ]
        
        for query in clear_queries:
            try:
                cursor.execute(query)
                print(f"✅ Executed: {query}")
            except Exception as e:
                print(f"⚠️  Warning for {query}: {e}")
        
        conn.commit()
        print("\n✅ Scoring data cleared successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")

if __name__ == "__main__":
    clear_scoring_data() 