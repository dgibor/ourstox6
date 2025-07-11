#!/usr/bin/env python3
"""
Clean company_fundamentals table to include only stocks from the stocks table
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_company_fundamentals():
    """Clean company_fundamentals table to include only stocks from stocks table"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        logger.info("🔍 Starting company_fundamentals table cleanup...")
        
        # Get initial counts
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stocks_count = cursor.fetchone()[0]
        logger.info(f"📊 Stocks table count: {stocks_count}")
        
        cursor.execute("SELECT COUNT(*) FROM company_fundamentals")
        fundamentals_count_before = cursor.fetchone()[0]
        logger.info(f"📊 Company fundamentals count before cleanup: {fundamentals_count_before}")
        
        # Find records in company_fundamentals that don't exist in stocks table
        cursor.execute("""
            SELECT cf.ticker, COUNT(*) as record_count
            FROM company_fundamentals cf
            LEFT JOIN stocks s ON cf.ticker = s.ticker
            WHERE s.ticker IS NULL
            GROUP BY cf.ticker
            ORDER BY record_count DESC
        """)
        
        orphaned_records = cursor.fetchall()
        
        if orphaned_records:
            logger.info(f"🗑️  Found {len(orphaned_records)} tickers with orphaned records:")
            for ticker, count in orphaned_records[:10]:  # Show first 10
                logger.info(f"   {ticker}: {count} records")
            
            if len(orphaned_records) > 10:
                logger.info(f"   ... and {len(orphaned_records) - 10} more tickers")
            
            # Delete orphaned records
            cursor.execute("""
                DELETE FROM company_fundamentals 
                WHERE ticker NOT IN (SELECT ticker FROM stocks)
            """)
            
            deleted_count = cursor.rowcount
            logger.info(f"🗑️  Deleted {deleted_count} orphaned records")
        else:
            logger.info("✅ No orphaned records found")
        
        # Check for duplicate records per ticker
        cursor.execute("""
            SELECT ticker, COUNT(*) as record_count
            FROM company_fundamentals
            GROUP BY ticker
            HAVING COUNT(*) > 1
            ORDER BY record_count DESC
        """)
        
        duplicate_records = cursor.fetchall()
        
        if duplicate_records:
            logger.info(f"🔄 Found {len(duplicate_records)} tickers with duplicate records:")
            for ticker, count in duplicate_records[:10]:  # Show first 10
                logger.info(f"   {ticker}: {count} records")
            
            if len(duplicate_records) > 10:
                logger.info(f"   ... and {len(duplicate_records) - 10} more tickers")
            
            # Keep only the most recent record for each ticker
            cursor.execute("""
                DELETE FROM company_fundamentals 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM company_fundamentals 
                    GROUP BY ticker
                )
            """)
            
            duplicate_deleted_count = cursor.rowcount
            logger.info(f"🔄 Deleted {duplicate_deleted_count} duplicate records")
        else:
            logger.info("✅ No duplicate records found")
        
        # Get final counts
        cursor.execute("SELECT COUNT(*) FROM company_fundamentals")
        fundamentals_count_after = cursor.fetchone()[0]
        logger.info(f"📊 Company fundamentals count after cleanup: {fundamentals_count_after}")
        
        # Verify all records are for stocks in the stocks table
        cursor.execute("""
            SELECT COUNT(*) 
            FROM company_fundamentals cf
            LEFT JOIN stocks s ON cf.ticker = s.ticker
            WHERE s.ticker IS NULL
        """)
        
        remaining_orphaned = cursor.fetchone()[0]
        if remaining_orphaned == 0:
            logger.info("✅ All company_fundamentals records now correspond to stocks in stocks table")
        else:
            logger.warning(f"⚠️  Still found {remaining_orphaned} orphaned records")
        
        # Check how many stocks have fundamentals
        cursor.execute("""
            SELECT COUNT(DISTINCT s.ticker) 
            FROM stocks s 
            INNER JOIN company_fundamentals cf ON s.ticker = cf.ticker
        """)
        stocks_with_fundamentals = cursor.fetchone()[0]
        logger.info(f"📊 Stocks with fundamentals after cleanup: {stocks_with_fundamentals}")
        
        # Check how many stocks are missing fundamentals
        cursor.execute("""
            SELECT COUNT(*) 
            FROM stocks s 
            LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.ticker IS NULL
        """)
        stocks_missing_fundamentals = cursor.fetchone()[0]
        logger.info(f"📊 Stocks missing fundamentals after cleanup: {stocks_missing_fundamentals}")
        
        # Commit changes
        conn.commit()
        logger.info("✅ Database changes committed successfully")
        
        # Summary
        total_deleted = fundamentals_count_before - fundamentals_count_after
        logger.info(f"📋 Cleanup Summary:")
        logger.info(f"   - Records before: {fundamentals_count_before}")
        logger.info(f"   - Records after: {fundamentals_count_after}")
        logger.info(f"   - Total deleted: {total_deleted}")
        logger.info(f"   - Stocks with fundamentals: {stocks_with_fundamentals}/{stocks_count}")
        logger.info(f"   - Stocks missing fundamentals: {stocks_missing_fundamentals}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    clean_company_fundamentals() 