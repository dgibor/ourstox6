#!/usr/bin/env python3
"""
Check Company Fundamentals Schema
"""

import sys
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager

def check_schema():
    """Check what columns exist in company_fundamentals table"""
    print("🔍 CHECKING COMPANY_FUNDAMENTALS SCHEMA")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Get column information
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'company_fundamentals'
        ORDER BY ordinal_position
        """
        
        columns = db.execute_query(query)
        
        print("📊 COMPANY_FUNDAMENTALS TABLE COLUMNS:")
        print("-" * 40)
        for column_name, data_type, is_nullable in columns:
            print(f"  {column_name}: {data_type} (nullable: {is_nullable})")
        
        # Check if specific columns exist
        print("\n🔍 CHECKING SPECIFIC COLUMNS:")
        print("-" * 40)
        
        critical_columns = [
            'inventory', 'accounts_receivable', 'accounts_payable', 
            'cost_of_goods_sold', 'retained_earnings', 'current_assets',
            'current_liabilities', 'eps_diluted', 'book_value_per_share'
        ]
        
        for column in critical_columns:
            exists = any(col[0] == column for col in columns)
            print(f"  {column}: {'✅ EXISTS' if exists else '❌ MISSING'}")
        
        # Check sample data for AAPL
        print("\n📊 SAMPLE AAPL DATA:")
        print("-" * 40)
        
        sample_query = """
        SELECT *
        FROM company_fundamentals
        WHERE ticker = 'AAPL'
        ORDER BY report_date DESC
        LIMIT 1
        """
        
        sample_data = db.fetch_one(sample_query)
        if sample_data:
            print("AAPL fundamental data found:")
            for i, value in enumerate(sample_data):
                print(f"  Column {i}: {value}")
        else:
            print("No AAPL data found")
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_schema() 