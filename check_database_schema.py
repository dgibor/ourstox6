#!/usr/bin/env python3
"""
Check Database Schema
Check what columns actually exist in the database tables
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

# Add daily_run to path for imports
sys.path.append('daily_run')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaChecker:
    """Check database schema"""
    
    def __init__(self):
        self.db = None
        
    def connect_db(self):
        """Connect to database"""
        try:
            from daily_run.database import DatabaseManager
            self.db = DatabaseManager()
            self.db.connect()
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect_db(self):
        """Disconnect from database"""
        if self.db:
            self.db.disconnect()
            logger.info("Database disconnected")
    
    def check_stocks_table_schema(self):
        """Check stocks table schema"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'stocks'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            cursor.close()
            
            print("STOCKS TABLE SCHEMA:")
            print("=" * 50)
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            return columns
            
        except Exception as e:
            logger.error(f"Error checking stocks table schema: {e}")
            return []
    
    def check_daily_charts_table_schema(self):
        """Check daily_charts table schema"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'daily_charts'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            cursor.close()
            
            print("\nDAILY_CHARTS TABLE SCHEMA:")
            print("=" * 50)
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            return columns
            
        except Exception as e:
            logger.error(f"Error checking daily_charts table schema: {e}")
            return []
    
    def check_sample_data(self, table_name: str, limit: int = 5):
        """Check sample data from a table"""
        try:
            cursor = self.db.connection.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()
            
            if rows:
                print(f"\nSAMPLE DATA FROM {table_name.upper()} TABLE:")
                print("=" * 50)
                for i, row in enumerate(rows):
                    print(f"  Row {i+1}: {row}")
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error checking sample data from {table_name}: {e}")

def main():
    """Main function to check database schema"""
    checker = SchemaChecker()
    
    if not checker.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting database schema check...")
        
        # Check stocks table schema
        stocks_columns = checker.check_stocks_table_schema()
        
        # Check daily_charts table schema
        daily_charts_columns = checker.check_daily_charts_table_schema()
        
        # Check sample data
        checker.check_sample_data('stocks', 3)
        checker.check_sample_data('daily_charts', 3)
        
        print("\n" + "=" * 80)
        print("SCHEMA CHECK COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        checker.disconnect_db()

if __name__ == "__main__":
    main()
