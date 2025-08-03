#!/usr/bin/env python3
"""
Script to add missing columns to company_fundamentals table
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_missing_columns():
    """Add missing columns to company_fundamentals table"""
    
    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', 5432)
    }
    
    # SQL commands to add missing columns
    sql_commands = [
        "ALTER TABLE company_fundamentals ADD COLUMN inventory bigint;",
        "ALTER TABLE company_fundamentals ADD COLUMN accounts_receivable bigint;",
        "ALTER TABLE company_fundamentals ADD COLUMN accounts_payable bigint;",
        "ALTER TABLE company_fundamentals ADD COLUMN retained_earnings bigint;"
    ]
    
    print("🔧 ADDING MISSING DATABASE COLUMNS")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"Executing command {i}/4: {sql}")
                cursor.execute(sql)
                conn.commit()
                print(f"✅ Successfully executed: {sql}")
            except Exception as e:
                print(f"❌ Error executing {sql}: {e}")
                conn.rollback()
        
        cursor.close()
        conn.close()
        print("\n🎉 Database schema update completed!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    add_missing_columns() 