#!/usr/bin/env python3
"""
Check the schema of the company_fundamentals table
"""

from database import DatabaseManager

def check_fundamentals_schema():
    print("Checking company_fundamentals table schema")
    print("=" * 50)
    
    db = DatabaseManager()
    db.connect()
    
    # Get table columns
    query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'company_fundamentals'
    ORDER BY ordinal_position
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print("Columns in company_fundamentals table:")
            print("-" * 40)
            for row in results:
                column_name, data_type, is_nullable = row
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"  {column_name}: {data_type} ({nullable})")
        else:
            print("No columns found in company_fundamentals table")
    except Exception as e:
        print(f"Error checking schema: {e}")
    
    # Check if table exists and has data
    try:
        count_query = "SELECT COUNT(*) FROM company_fundamentals"
        result = db.execute_query(count_query)
        total_count = result[0][0] if result else 0
        print(f"\nTotal records in company_fundamentals: {total_count}")
        
        if total_count > 0:
            # Show sample data
            sample_query = "SELECT * FROM company_fundamentals LIMIT 3"
            sample_results = db.execute_query(sample_query)
            if sample_results:
                print("\nSample data:")
                print("-" * 40)
                for row in sample_results:
                    print(f"  {row}")
    except Exception as e:
        print(f"Error checking data: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    check_fundamentals_schema() 