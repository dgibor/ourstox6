#!/usr/bin/env python3
import sys
sys.path.insert(0, 'daily_run')

from database import DatabaseManager

def check_missing_columns():
    """Check which columns are missing from the database"""
    db = DatabaseManager()
    
    # Columns that the enhanced FMP service wants to insert
    desired_columns = [
        'inventory', 'accounts_receivable', 'accounts_payable', 
        'retained_earnings', 'capex', 'shares_float'
    ]
    
    print("🔍 CHECKING MISSING DATABASE COLUMNS")
    print("=" * 50)
    
    with db.get_cursor() as cursor:
        # Check which columns exist
        existing_columns = []
        missing_columns = []
        
        for column in desired_columns:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'company_fundamentals' 
                AND column_name = %s
            """, (column,))
            
            result = cursor.fetchone()
            if result:
                existing_columns.append(column)
            else:
                missing_columns.append(column)
        
        print("✅ Existing columns:")
        for col in existing_columns:
            print(f"  • {col}")
        
        print("\n❌ Missing columns:")
        for col in missing_columns:
            print(f"  • {col}")
        
        if missing_columns:
            print(f"\n📋 SQL to add missing columns:")
            print("-" * 30)
            for col in missing_columns:
                print(f"ALTER TABLE company_fundamentals ADD COLUMN {col} bigint;")
        else:
            print("\n✅ All desired columns exist!")

if __name__ == "__main__":
    check_missing_columns() 