#!/usr/bin/env python3
"""
Fix Database Schema - Simple Version
Uses same connection method as working scoring files
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def fix_database_schema():
    """Fix the database schema by increasing string length for grade/rating columns"""
    
    # Use same database config as working files
    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print(f"🔧 Connecting to database: {db_config['host']}:{db_config['port']}")
    
    # SQL commands to fix schema
    fix_commands = [
        # Fix company_scores_current table
        """
        ALTER TABLE company_scores_current 
        ALTER COLUMN fundamental_health_grade TYPE character varying(20),
        ALTER COLUMN value_rating TYPE character varying(20),
        ALTER COLUMN fundamental_risk_level TYPE character varying(20),
        ALTER COLUMN technical_health_grade TYPE character varying(20),
        ALTER COLUMN trading_signal_rating TYPE character varying(20),
        ALTER COLUMN technical_risk_level TYPE character varying(20),
        ALTER COLUMN overall_grade TYPE character varying(20);
        """,
        
        # Fix company_scores_historical table
        """
        ALTER TABLE company_scores_historical 
        ALTER COLUMN fundamental_health_grade TYPE character varying(20),
        ALTER COLUMN value_rating TYPE character varying(20),
        ALTER COLUMN fundamental_risk_level TYPE character varying(20),
        ALTER COLUMN technical_health_grade TYPE character varying(20),
        ALTER COLUMN trading_signal_rating TYPE character varying(20),
        ALTER COLUMN technical_risk_level TYPE character varying(20),
        ALTER COLUMN overall_grade TYPE character varying(20);
        """
    ]
    
    conn = None
    try:
        # Connect to database using same method as working files
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("🔧 Fixing database schema...")
        
        # Execute fix commands
        for i, command in enumerate(fix_commands, 1):
            print(f"Executing fix command {i}...")
            cursor.execute(command)
            conn.commit()
            print(f"✅ Fix command {i} completed")
        
        # Verify the changes
        print("\n🔍 Verifying schema changes...")
        verify_query = """
        SELECT 
            table_name,
            column_name,
            data_type,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_name IN ('company_scores_current', 'company_scores_historical')
        AND (column_name LIKE '%grade%' OR column_name LIKE '%rating%' OR column_name LIKE '%level%')
        ORDER BY table_name, column_name;
        """
        
        cursor.execute(verify_query)
        results = cursor.fetchall()
        
        print("\n📋 Schema verification results:")
        for result in results:
            table_name, column_name, data_type, max_length = result
            print(f"  {table_name}.{column_name}: {data_type}({max_length})")
        
        print("\n✅ Database schema fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        if conn:
            conn.rollback()
        return False
    
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    fix_database_schema() 