#!/usr/bin/env python3
"""
Check company_fundamentals table structure
"""

from database import DatabaseManager

def check_table_structure():
    """Check the structure of company_fundamentals table"""
    db = DatabaseManager()
    
    try:
        # Get column names
        result = db.execute_query("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_fundamentals' 
            ORDER BY ordinal_position
        """)
        
        print("Company_fundamentals table columns:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        # Check constraints
        print("\nChecking constraints...")
        constraint_result = db.execute_query("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'company_fundamentals'
        """)
        
        print("Constraints:")
        for row in constraint_result:
            print(f"  {row[0]}: {row[1]}")
        
        # Check unique constraints specifically
        print("\nChecking unique constraints...")
        unique_result = db.execute_query("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'company_fundamentals' 
                AND tc.constraint_type = 'UNIQUE'
        """)
        
        print("Unique constraint columns:")
        for row in unique_result:
            print(f"  {row[0]}")
        
    except Exception as e:
        print(f"Error checking table structure: {e}")

if __name__ == "__main__":
    check_table_structure() 