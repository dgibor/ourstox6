#!/usr/bin/env python3
"""
Check unique constraints on company_fundamentals table
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def check_constraints():
    db = DatabaseManager()
    
    # Check unique constraints
    query = """
    SELECT conname, pg_get_constraintdef(oid) 
    FROM pg_constraint 
    WHERE conrelid = 'company_fundamentals'::regclass AND contype = 'u';
    """
    
    try:
        result = db.execute_query(query)
        print("Unique constraints on company_fundamentals:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")
    except Exception as e:
        print(f"Error checking constraints: {e}")

if __name__ == "__main__":
    check_constraints() 