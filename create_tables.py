#!/usr/bin/env python3
"""
Script to create scoring database tables
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_connection():
    """Get database connection"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'ourstox6'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            cursor_factory=RealDictCursor
        )
        return connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

def execute_sql_file(file_path):
    """Execute SQL file"""
    try:
        with open(file_path, 'r') as file:
            sql_content = file.read()
        
        with get_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_content)
                conn.commit()
                print("✅ Database tables created successfully!")
                
    except Exception as e:
        print(f"❌ Error executing SQL file: {e}")
        raise

if __name__ == "__main__":
    sql_file = "create_scoring_tables.sql"
    if os.path.exists(sql_file):
        print(f"Creating database tables from {sql_file}...")
        execute_sql_file(sql_file)
    else:
        print(f"❌ SQL file {sql_file} not found!")
        sys.exit(1) 