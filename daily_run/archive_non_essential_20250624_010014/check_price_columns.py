#!/usr/bin/env python3
"""
Check price-related columns in stocks table
"""

from database import DatabaseManager

def check_price_columns():
    print("Checking price-related columns in stocks table")
    print("=" * 50)
    
    db = DatabaseManager()
    db.connect()
    
    # Get all columns that might contain price data
    query = """
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_name = 'stocks' 
    AND (column_name LIKE '%price%' OR column_name LIKE '%close%' OR column_name LIKE '%open%' OR column_name LIKE '%high%' OR column_name LIKE '%low%')
    ORDER BY column_name
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print("Price-related columns:")
            for row in results:
                column_name, data_type = row
                print(f"  {column_name}: {data_type}")
        else:
            print("No price-related columns found")
    except Exception as e:
        print(f"Error: {e}")
    
    # Also check for any numeric columns that might be price
    query2 = """
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_name = 'stocks' 
    AND data_type IN ('numeric', 'bigint', 'integer')
    ORDER BY column_name
    """
    
    try:
        results = db.execute_query(query2)
        if results:
            print(f"\nAll numeric columns:")
            for row in results:
                column_name, data_type = row
                print(f"  {column_name}: {data_type}")
    except Exception as e:
        print(f"Error: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    check_price_columns() 