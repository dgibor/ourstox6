#!/usr/bin/env python3
"""
Script to update existing values in company_scores_current table to match new scoring system
"""

from database import DatabaseManager

def update_current_table_values():
    """Update existing values in company_scores_current table to match new scoring system"""
    try:
        db = DatabaseManager()
        print("Database connection successful")
        
        # Update the existing values to match the new scoring system
        # Map old values to new values:
        # "Very High" -> "Strong Sell"
        # "High" -> "Sell" 
        # "Medium" -> "Neutral"
        # "Low" -> "Buy"
        # "Very Low" -> "Strong Buy"
        # "None" -> "Neutral"
        
        update_queries = [
            # Update fundamental_risk_level
            "UPDATE company_scores_current SET fundamental_risk_level = 'Strong Sell' WHERE fundamental_risk_level = 'Very High';",
            "UPDATE company_scores_current SET fundamental_risk_level = 'Sell' WHERE fundamental_risk_level = 'High';",
            "UPDATE company_scores_current SET fundamental_risk_level = 'Neutral' WHERE fundamental_risk_level = 'Medium';",
            "UPDATE company_scores_current SET fundamental_risk_level = 'Buy' WHERE fundamental_risk_level = 'Low';",
            "UPDATE company_scores_current SET fundamental_risk_level = 'Strong Buy' WHERE fundamental_risk_level = 'Very Low';",
            "UPDATE company_scores_current SET fundamental_risk_level = 'Neutral' WHERE fundamental_risk_level = 'None';",
            
            # Update technical_risk_level
            "UPDATE company_scores_current SET technical_risk_level = 'Strong Sell' WHERE technical_risk_level = 'Very High';",
            "UPDATE company_scores_current SET technical_risk_level = 'Sell' WHERE technical_risk_level = 'High';",
            "UPDATE company_scores_current SET technical_risk_level = 'Neutral' WHERE technical_risk_level = 'Medium';",
            "UPDATE company_scores_current SET technical_risk_level = 'Buy' WHERE technical_risk_level = 'Low';",
            "UPDATE company_scores_current SET technical_risk_level = 'Strong Buy' WHERE technical_risk_level = 'Very Low';",
            "UPDATE company_scores_current SET technical_risk_level = 'Neutral' WHERE technical_risk_level = 'None';",
            
            # Set NULL values to 'Neutral'
            "UPDATE company_scores_current SET fundamental_risk_level = 'Neutral' WHERE fundamental_risk_level IS NULL;",
            "UPDATE company_scores_current SET technical_risk_level = 'Neutral' WHERE technical_risk_level IS NULL;"
        ]
        
        print("Updating existing values in company_scores_current table...")
        for i, query in enumerate(update_queries, 1):
            print(f"Executing query {i}/{len(update_queries)}: {query[:50]}...")
            db.execute_update(query)
        
        print("Values updated successfully!")
        
        # Verify the changes
        print("\nVerifying updated values...")
        result = db.execute_query("""
            SELECT DISTINCT fundamental_risk_level, technical_risk_level, COUNT(*) as count
            FROM company_scores_current 
            GROUP BY fundamental_risk_level, technical_risk_level
            ORDER BY fundamental_risk_level, technical_risk_level
        """)
        
        print("\nUpdated values in company_scores_current table:")
        for row in result:
            print(f"  fundamental_risk_level: '{row[0]}', technical_risk_level: '{row[1]}', count: {row[2]}")
        
        return True
        
    except Exception as e:
        print(f"Error updating current table values: {e}")
        return False

if __name__ == "__main__":
    success = update_current_table_values()
    if success:
        print("\n✅ Values updated successfully!")
    else:
        print("\n❌ Failed to update values!")

