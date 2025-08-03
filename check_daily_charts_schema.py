"""
Check if there's a daily_charts table that contains current prices
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

def check_daily_charts():
    """Check the daily_charts table schema"""
    
    try:
        # Import with fallback
        try:
            from daily_run.database import DatabaseManager
        except ImportError:
            # Add daily_run to path and try again
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))
            from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Check if daily_charts table exists
        logger.info("--- Checking if daily_charts table exists ---")
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'daily_charts'
            """)
            table_exists = cursor.fetchone()
            
            if table_exists:
                logger.info("✅ daily_charts table exists")
                
                # Check daily_charts table schema
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'daily_charts'
                    ORDER BY ordinal_position
                """)
                daily_charts_columns = cursor.fetchall()
                
                logger.info("Daily charts table columns:")
                for col in daily_charts_columns:
                    logger.info(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
                
                # Check sample data
                cursor.execute("SELECT * FROM daily_charts LIMIT 1")
                sample_daily = cursor.fetchone()
                if sample_daily:
                    logger.info("Sample daily chart data:")
                    for key, value in sample_daily.items():
                        logger.info(f"  {key}: {value}")
                
                # Check latest prices for some tickers
                test_tickers = ['AAPL', 'MSFT', 'GOOGL']
                for ticker in test_tickers:
                    cursor.execute("""
                        SELECT ticker, close, date 
                        FROM daily_charts 
                        WHERE ticker = %s 
                        ORDER BY date DESC 
                        LIMIT 1
                    """, (ticker,))
                    latest_price = cursor.fetchone()
                    if latest_price:
                        logger.info(f"Latest price for {ticker}: ${latest_price['close']} on {latest_price['date']}")
                    else:
                        logger.info(f"No price data found for {ticker}")
                        
            else:
                logger.warning("❌ daily_charts table does not exist")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Daily charts check failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking daily_charts table...")
    success = check_daily_charts()
    
    if success:
        logger.info("✅ Daily charts check completed!")
    else:
        logger.error("❌ Daily charts check failed!")
        sys.exit(1) 