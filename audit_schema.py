#!/usr/bin/env python3
"""
Database Schema Audit Script
"""

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def audit_database_schema():
    """Audit the database schema to identify issues"""
    
    # Database configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 DATABASE SCHEMA AUDIT")
        print("=" * 50)
        
        # Check stocks table schema
        print("\n📊 STOCKS TABLE SCHEMA:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            ORDER BY ordinal_position
        """)
        
        stocks_columns = cur.fetchall()
        for col in stocks_columns:
            print(f"  {col[0]}: {col[1]} ({col[2]})")
        
        # Check daily_charts table schema
        print("\n📈 DAILY_CHARTS TABLE SCHEMA:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'daily_charts' 
            ORDER BY ordinal_position
        """)
        
        daily_charts_columns = cur.fetchall()
        for col in daily_charts_columns:
            print(f"  {col[0]}: {col[1]} ({col[2]})")
        
        # Check company_fundamentals table schema
        print("\n💰 COMPANY_FUNDAMENTALS TABLE SCHEMA:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'company_fundamentals' 
            ORDER BY ordinal_position
        """)
        
        fundamentals_columns = cur.fetchall()
        for col in fundamentals_columns:
            print(f"  {col[0]}: {col[1]} ({col[2]})")
        
        # Check financial_ratios table schema
        print("\n📊 FINANCIAL_RATIOS TABLE SCHEMA:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'financial_ratios' 
            ORDER BY ordinal_position
        """)
        
        ratios_columns = cur.fetchall()
        for col in ratios_columns:
            print(f"  {col[0]}: {col[1]} ({col[2]})")
        
        # Check for table existence
        print("\n🔍 TABLE EXISTENCE CHECK:")
        tables_to_check = ['stocks', 'daily_charts', 'company_fundamentals', 'financial_ratios', 'fundamentals']
        
        for table in tables_to_check:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            
            exists = cur.fetchone()[0]
            status = "✅ EXISTS" if exists else "❌ MISSING"
            print(f"  {table}: {status}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Schema audit completed successfully!")
        
    except Exception as e:
        print(f"❌ Schema audit failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    audit_database_schema() 