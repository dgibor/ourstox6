#!/usr/bin/env python3
"""
Script to check current values in company_scores_current table
"""

from database import DatabaseManager

def check_current_table_values():
    """Check current values in company_scores_current table"""
    try:
        db = DatabaseManager()
        print("Database connection successful")
        
        # Check what values are currently in the risk level fields
        print("\nChecking current values in company_scores_current table...")
        
        result = db.execute_query("""
            SELECT DISTINCT fundamental_risk_level, technical_risk_level, COUNT(*) as count
            FROM company_scores_current 
            GROUP BY fundamental_risk_level, technical_risk_level
            ORDER BY fundamental_risk_level, technical_risk_level
        """)
        
        print("\nCurrent values in company_scores_current table:")
        for row in result:
            print(f"  fundamental_risk_level: '{row[0]}', technical_risk_level: '{row[1]}', count: {row[2]}")
        
        # Also check for any NULL values
        result = db.execute_query("""
            SELECT COUNT(*) as null_count
            FROM company_scores_current 
            WHERE fundamental_risk_level IS NULL OR technical_risk_level IS NULL
        """)
        
        null_count = result[0][0] if result else 0
        print(f"\nNULL values count: {null_count}")
        
        return True
        
    except Exception as e:
        print(f"Error checking current table values: {e}")
        return False

if __name__ == "__main__":
    success = check_current_table_values()
    if not success:
        print("\n❌ Failed to check current table values!")

