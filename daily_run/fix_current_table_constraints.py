#!/usr/bin/env python3
"""
Script to fix database constraints on company_scores_current table to match the scoring system output
"""

from database import DatabaseManager

def fix_current_table_constraints():
    """Fix database constraints on company_scores_current table to match scoring system output"""
    try:
        db = DatabaseManager()
        print("Database connection successful")
        
        # Fix the risk level constraints on company_scores_current table
        # The scoring system uses "Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell" for all ratings
        # But the database expects risk levels to use "Very Low", "Low", "Medium", "High", "Very High"
        
        # We need to update the risk level constraints to accept the scoring system values
        fix_queries = [
            # Drop the existing constraints
            "ALTER TABLE company_scores_current DROP CONSTRAINT IF EXISTS company_scores_current_fundamental_risk_level_check;",
            "ALTER TABLE company_scores_current DROP CONSTRAINT IF EXISTS company_scores_current_technical_risk_level_check;",
            
            # Add new constraints that accept the scoring system values
            "ALTER TABLE company_scores_current ADD CONSTRAINT company_scores_current_fundamental_risk_level_check CHECK (fundamental_risk_level IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy'));",
            "ALTER TABLE company_scores_current ADD CONSTRAINT company_scores_current_technical_risk_level_check CHECK (technical_risk_level IN ('Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy'));"
        ]
        
        print("Fixing company_scores_current table constraints...")
        for i, query in enumerate(fix_queries, 1):
            print(f"Executing query {i}/{len(fix_queries)}: {query[:50]}...")
            db.execute_update(query)
        
        print("Company_scores_current table constraints fixed successfully!")
        
        # Verify the changes
        print("\nVerifying constraints...")
        result = db.execute_query("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = (SELECT oid FROM pg_class WHERE relname = 'company_scores_current') 
            AND conname LIKE '%risk_level%'
        """)
        
        for row in result:
            print(f"{row[0]}: {row[1]}")
        
        return True
        
    except Exception as e:
        print(f"Error fixing company_scores_current table constraints: {e}")
        return False

if __name__ == "__main__":
    success = fix_current_table_constraints()
    if success:
        print("\n✅ Company_scores_current table constraints fixed successfully!")
    else:
        print("\n❌ Company_scores_current table constraints fix failed!")

