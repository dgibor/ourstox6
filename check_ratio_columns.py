#!/usr/bin/env python3
"""
Check ratio columns in database
"""

import sys
sys.path.insert(0, 'daily_run')

from database import DatabaseManager

def check_ratio_columns():
    """Check what ratio columns exist in the database"""
    db = DatabaseManager()
    
    try:
        # Get all ratio columns
        result = db.fetch_all_dict(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name LIKE %s ORDER BY column_name",
            ('company_fundamentals', '%ratio%')
        )
        
        print("Ratio columns in database:")
        for row in result:
            print(f"  - {row['column_name']}")
            
        # Get all columns for reference
        all_columns = db.fetch_all_dict(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY column_name",
            ('company_fundamentals',)
        )
        
        print(f"\nTotal columns in company_fundamentals: {len(all_columns)}")
        print("All columns:")
        for row in all_columns:
            print(f"  - {row['column_name']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ratio_columns() 