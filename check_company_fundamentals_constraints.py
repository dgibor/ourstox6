#!/usr/bin/env python3
"""
Check constraints on company_fundamentals table
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_constraints():
    """Check constraints on company_fundamentals table"""
    
    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', 5432)
    }
    
    print("🔍 CHECKING COMPANY_FUNDAMENTALS CONSTRAINTS")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check primary key
        cursor.execute("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'company_fundamentals' 
            AND constraint_type = 'PRIMARY KEY'
        """)
        primary_keys = cursor.fetchall()
        
        print("🔑 Primary Keys:")
        for pk in primary_keys:
            print(f"  • {pk[0]}: {pk[1]}")
        
        # Check unique constraints
        cursor.execute("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'company_fundamentals' 
            AND constraint_type = 'UNIQUE'
        """)
        unique_constraints = cursor.fetchall()
        
        print("\n🔒 Unique Constraints:")
        for uc in unique_constraints:
            print(f"  • {uc[0]}: {uc[1]}")
        
        # Check columns in primary key
        if primary_keys:
            pk_name = primary_keys[0][0]
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.key_column_usage 
                WHERE constraint_name = %s
                ORDER BY ordinal_position
            """, (pk_name,))
            pk_columns = cursor.fetchall()
            print(f"\n📋 Primary Key Columns ({pk_name}):")
            for col in pk_columns:
                print(f"  • {col[0]}")
        
        # Check unique constraint columns
        if unique_constraints:
            for uc in unique_constraints:
                uc_name = uc[0]
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.key_column_usage 
                    WHERE constraint_name = %s
                    ORDER BY ordinal_position
                """, (uc_name,))
                uc_columns = cursor.fetchall()
                print(f"\n📋 Unique Constraint Columns ({uc_name}):")
                for col in uc_columns:
                    print(f"  • {col[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_constraints() 