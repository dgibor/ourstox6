#!/usr/bin/env python3
"""Check stocks table structure"""

from daily_run.database import DatabaseManager

def check_stocks_table():
    db = DatabaseManager()
    try:
        db.connect()
        
        # Get column names
        result = db.execute_query("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            ORDER BY ordinal_position
        """)
        
        print("Stocks table columns:")
        for row in result:
            print(f"  {row[0]} ({row[1]})")
            
        # Check if table has any data
        count_result = db.execute_query("SELECT COUNT(*) FROM stocks")
        print(f"\nTotal records: {count_result[0][0]}")
        
        # Show sample data
        sample_result = db.execute_query("SELECT ticker, company_name FROM stocks LIMIT 3")
        if sample_result:
            print("\nSample records:")
            for row in sample_result:
                print(f"  {row[0]}: {row[1]}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_stocks_table() 