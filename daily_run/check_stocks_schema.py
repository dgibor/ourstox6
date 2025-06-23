#!/usr/bin/env python3
"""
Check all columns in the stocks table
"""

from database import DatabaseManager

def check_stocks_schema():
    print("Checking stocks table schema")
    print("=" * 50)
    
    db = DatabaseManager()
    db.connect()
    
    # Get all columns in stocks table
    query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'stocks'
    ORDER BY ordinal_position
    """
    
    try:
        results = db.execute_query(query)
        if results:
            print("All columns in stocks table:")
            print("-" * 50)
            fundamental_columns = []
            for row in results:
                column_name, data_type, is_nullable = row
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"  {column_name}: {data_type} ({nullable})")
                
                # Identify fundamental columns
                if any(keyword in column_name.lower() for keyword in [
                    'revenue', 'income', 'debt', 'equity', 'market', 'shares', 
                    'eps', 'book', 'cash', 'assets', 'liabilities', 'operating',
                    'gross', 'ebitda', 'fundamental'
                ]):
                    fundamental_columns.append(column_name)
            
            print(f"\nFundamental columns found: {len(fundamental_columns)}")
            print("-" * 30)
            for col in fundamental_columns:
                print(f"  {col}")
        else:
            print("No columns found in stocks table")
    except Exception as e:
        print(f"Error checking schema: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    check_stocks_schema() 