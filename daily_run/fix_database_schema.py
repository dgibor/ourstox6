#!/usr/bin/env python3
"""
Fix Database Schema for Analyst Scoring

Adds missing columns needed for analyst scoring to work properly.
"""

import psycopg2
import os
from dotenv import load_dotenv

def fix_database_schema():
    """Fix the database schema for analyst scoring"""
    print("🔧 Fixing database schema for analyst scoring...")
    
    # Load environment variables
    load_dotenv()
    
    # Get database connection details
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'ourstox6')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        cursor = conn.cursor()
        
        # Check if active column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' AND column_name = 'active'
        """)
        
        if not cursor.fetchone():
            print("  ➕ Adding 'active' column to stocks table...")
            cursor.execute("ALTER TABLE stocks ADD COLUMN active BOOLEAN DEFAULT true")
            
            # Update existing records to be active
            cursor.execute("UPDATE stocks SET active = true WHERE active IS NULL")
            print("  ✅ Added 'active' column and set all existing stocks to active")
        else:
            print("  ✅ 'active' column already exists in stocks table")
        
        # Check if enhanced_scores table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'enhanced_scores'
        """)
        
        if not cursor.fetchone():
            print("  ➕ Creating enhanced_scores table...")
            cursor.execute("""
                CREATE TABLE enhanced_scores (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(10) NOT NULL,
                    sector VARCHAR(50),
                    fundamental_health DECIMAL(5,2),
                    technical_health DECIMAL(5,2),
                    vwap_sr_score DECIMAL(5,2),
                    composite_score DECIMAL(5,2),
                    rating VARCHAR(20),
                    current_price DECIMAL(10,2),
                    vwap DECIMAL(10,2),
                    analyst_score DECIMAL(5,2),
                    analyst_components JSONB,
                    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  ✅ Created enhanced_scores table")
        else:
            print("  ✅ enhanced_scores table already exists")
            
            # Check if analyst_score column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'enhanced_scores' AND column_name = 'analyst_score'
            """)
            
            if not cursor.fetchone():
                print("  ➕ Adding analyst_score columns to enhanced_scores table...")
                cursor.execute("""
                    ALTER TABLE enhanced_scores 
                    ADD COLUMN analyst_score DECIMAL(5,2),
                    ADD COLUMN analyst_components JSONB
                """)
                print("  ✅ Added analyst_score columns")
            else:
                print("  ✅ analyst_score columns already exist")
        
        # Commit changes
        conn.commit()
        print("  ✅ Database schema updated successfully")
        
        # Show final table structure
        print("\n📊 Final stocks table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            ORDER BY ordinal_position
        """)
        
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database schema fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    fix_database_schema()
