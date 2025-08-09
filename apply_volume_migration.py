#!/usr/bin/env python3
"""
Apply database migration for volume-based technical indicators
Increases column precision for OBV, VPT and related volume indicators
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the daily_run module to the path
sys.path.append('daily_run')

def apply_migration():
    """Apply the volume column precision migration"""
    load_dotenv()
    
    # Use the same database configuration as the existing system
    try:
        from daily_run.config import Config
        connection_params = Config.get_db_config()
    except ImportError:
        # Fallback to environment variables
        connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'dbname': os.getenv('DB_NAME', 'ourstox'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    try:
        print("🔧 Connecting to database...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        print("📊 Checking current column types...")
        cursor.execute("""
            SELECT column_name, data_type, numeric_precision, numeric_scale 
            FROM information_schema.columns 
            WHERE table_name = 'daily_charts' 
            AND column_name IN ('obv', 'vpt', 'volume_confirmation', 'volume_weighted_high', 'volume_weighted_low')
            ORDER BY column_name;
        """)
        
        current_columns = cursor.fetchall()
        print("Current column specifications:")
        for col in current_columns:
            print(f"  {col[0]}: {col[1]}({col[2]},{col[3]})")
        
        print("\n🚀 Applying migration...")
        
        # Read and execute migration SQL
        with open('database_migration_volume_columns.sql', 'r') as f:
            migration_sql = f.read()
        
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration applied successfully!")
        
        print("\n📋 Verifying new column types...")
        cursor.execute("""
            SELECT column_name, data_type, numeric_precision, numeric_scale 
            FROM information_schema.columns 
            WHERE table_name = 'daily_charts' 
            AND column_name IN ('obv', 'vpt', 'volume_confirmation', 'volume_weighted_high', 'volume_weighted_low')
            ORDER BY column_name;
        """)
        
        new_columns = cursor.fetchall()
        print("New column specifications:")
        for col in new_columns:
            print(f"  {col[0]}: {col[1]}({col[2]},{col[3]})")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print("   - Volume indicators can now store values up to 10 billion")
        print("   - OBV and VPT will no longer be artificially capped at 10 million")
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    apply_migration()
