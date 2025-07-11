#!/usr/bin/env python3
"""
Check company_fundamentals table schema
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_schema():
    """Check the company_fundamentals table schema"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("🔍 Checking company_fundamentals table schema...")
        print()
        
        # Get table columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'company_fundamentals' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("📋 Company fundamentals table columns:")
        print("-" * 50)
        for col_name, data_type, is_nullable in columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"  {col_name:<25} {data_type:<15} {nullable}")
        
        print()
        print(f"📊 Total columns: {len(columns)}")
        
        # Check if shareholders_equity column exists
        column_names = [col[0] for col in columns]
        if 'shareholders_equity' in column_names:
            print("✅ shareholders_equity column exists")
        else:
            print("❌ shareholders_equity column does NOT exist")
            print("   This is causing the error in the script!")
        
        # Check for similar columns
        equity_columns = [col for col in column_names if 'equity' in col.lower()]
        if equity_columns:
            print(f"📋 Found equity-related columns: {equity_columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_schema() 