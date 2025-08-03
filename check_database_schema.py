"""
Check the actual database schema to understand the correct column names
"""

import logging
import sys
import os
import psycopg2.extras

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_schema():
    """Check the database schema"""
    
    try:
        # Import with fallback
        try:
            from daily_run.database import DatabaseManager
        except ImportError:
            # Add daily_run to path and try again
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))
            from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Check stocks table schema
        logger.info("--- Checking stocks table schema ---")
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'stocks'
                ORDER BY ordinal_position
            """)
            stocks_columns = cursor.fetchall()
            
            logger.info("Stocks table columns:")
            for col in stocks_columns:
                logger.info(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Check company_fundamentals table schema
        logger.info("\n--- Checking company_fundamentals table schema ---")
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'company_fundamentals'
                ORDER BY ordinal_position
            """)
            fundamentals_columns = cursor.fetchall()
            
            logger.info("Company fundamentals table columns:")
            for col in fundamentals_columns:
                logger.info(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Check sample data
        logger.info("\n--- Checking sample data ---")
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM stocks LIMIT 1")
            sample_stock = cursor.fetchone()
            if sample_stock:
                logger.info("Sample stock data:")
                for key, value in sample_stock.items():
                    logger.info(f"  {key}: {value}")
            
            cursor.execute("SELECT * FROM company_fundamentals LIMIT 1")
            sample_fundamental = cursor.fetchone()
            if sample_fundamental:
                logger.info("Sample fundamental data:")
                for key, value in sample_fundamental.items():
                    logger.info(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema check failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking database schema...")
    success = check_schema()
    
    if success:
        logger.info("✅ Schema check completed!")
    else:
        logger.error("❌ Schema check failed!")
        sys.exit(1) 