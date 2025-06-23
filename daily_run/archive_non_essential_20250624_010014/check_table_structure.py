#!/usr/bin/env python3
"""
Check table structure
"""

import psycopg2
from common_imports import DB_CONFIG

def check_stocks_table():
    """Check the structure of the stocks table"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get column names
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        
        print("Stocks table columns:")
        for col_name, data_type in columns:
            print(f"  {col_name} ({data_type})")
        
        cur.close()
        conn.close()
        
        return [col[0] for col in columns]
        
    except Exception as e:
        print(f"Error checking table structure: {e}")
        return []

if __name__ == "__main__":
    check_stocks_table() 