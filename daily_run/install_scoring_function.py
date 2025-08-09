#!/usr/bin/env python3
"""
Script to install the missing upsert_company_scores database function
"""

from database import DatabaseManager
import os

def install_scoring_function():
    """Install the missing upsert_company_scores function"""
    try:
        db = DatabaseManager()
        print("Database connection successful")
        
        # Read the SQL function definition from the schema file
        schema_file_path = os.path.join(os.path.dirname(__file__), '..', 'create_scoring_tables.sql')
        
        with open(schema_file_path, 'r') as f:
            sql_content = f.read()
        
        # Extract the upsert_company_scores function definition
        # Find the function definition in the SQL file
        function_start = sql_content.find('CREATE OR REPLACE FUNCTION upsert_company_scores(')
        if function_start == -1:
            print("ERROR: Could not find upsert_company_scores function in schema file")
            return False
        
        # Find the end of the function (look for the $$ LANGUAGE plpgsql; part)
        function_end = sql_content.find('$$ LANGUAGE plpgsql;', function_start)
        if function_end == -1:
            print("ERROR: Could not find end of upsert_company_scores function")
            return False
        
        # Extract the complete function definition
        function_sql = sql_content[function_start:function_end + 20]  # Include the LANGUAGE part
        
        print("Installing upsert_company_scores function...")
        print("Function SQL preview (first 200 chars):")
        print(function_sql[:200] + "...")
        
        # Execute the function creation
        db.execute_update(function_sql)
        
        print("Function installed successfully!")
        
        # Verify the function was installed
        function_exists = db.fetch_one("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_name = 'upsert_company_scores'
        """)
        
        if function_exists:
            print("✅ Function verification successful: upsert_company_scores is now available")
            return True
        else:
            print("❌ Function verification failed: upsert_company_scores not found")
            return False
            
    except Exception as e:
        print(f"Error installing function: {e}")
        return False

if __name__ == "__main__":
    success = install_scoring_function()
    if success:
        print("\n🎉 Database function installation completed successfully!")
    else:
        print("\n❌ Database function installation failed!")

