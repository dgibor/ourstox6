#!/usr/bin/env python3
"""
Check stocks table schema
"""

import sys
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager

def check_stocks_schema():
    """Check what columns exist in the stocks table"""
    try:
        db = DatabaseManager()
        
        # Get column information
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'stocks'
        ORDER BY ordinal_position
        """
        
        columns = db.execute_query(query)
        
        print("📋 STOCKS TABLE SCHEMA:")
        print("=" * 50)
        for col in columns:
            column_name, data_type, is_nullable = col
            print(f"📊 {column_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        
        # Check if there's a price-related column
        price_columns = [col[0] for col in columns if 'price' in col[0].lower()]
        print(f"\n💰 Price-related columns: {price_columns}")
        
        # Check if there's a market cap column
        market_cap_columns = [col[0] for col in columns if 'market' in col[0].lower() or 'cap' in col[0].lower()]
        print(f"📈 Market cap related columns: {market_cap_columns}")
        
        return columns
        
    except Exception as e:
        print(f"❌ Error checking stocks schema: {e}")
        return None

if __name__ == "__main__":
    check_stocks_schema() 