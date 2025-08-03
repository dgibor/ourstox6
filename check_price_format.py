"""
Check the actual format of price data in daily_charts table
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

def check_price_format():
    """Check the actual format of price data"""
    
    try:
        # Import with fallback
        try:
            from daily_run.database import DatabaseManager
        except ImportError:
            # Add daily_run to path and try again
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))
            from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Check price data for major stocks
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
        
        logger.info("--- Checking price data format ---")
        
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            for ticker in test_tickers:
                cursor.execute("""
                    SELECT ticker, close, date, open, high, low
                    FROM daily_charts 
                    WHERE ticker = %s 
                    ORDER BY date DESC 
                    LIMIT 3
                """, (ticker,))
                
                results = cursor.fetchall()
                if results:
                    logger.info(f"\n{ticker} - Latest 3 days:")
                    for i, row in enumerate(results):
                        logger.info(f"  {row['date']}: Close=${row['close']}, Open=${row['open']}, High=${row['high']}, Low=${row['low']}")
                        
                        # Check if it looks like cents or dollars
                        if row['close'] and row['close'] > 0:
                            if row['close'] < 1000:
                                logger.info(f"    → Looks like CENTS (${row['close']/100:.2f})")
                            else:
                                logger.info(f"    → Looks like DOLLARS (${row['close']:.2f})")
                else:
                    logger.warning(f"No data found for {ticker}")
        
        # Check data type and range
        logger.info("\n--- Checking data type and range ---")
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    MIN(close) as min_close,
                    MAX(close) as max_close,
                    AVG(close) as avg_close,
                    COUNT(*) as total_records
                FROM daily_charts 
                WHERE close IS NOT NULL AND close > 0
            """)
            
            stats = cursor.fetchone()
            if stats:
                logger.info(f"Price Statistics:")
                logger.info(f"  Min: {stats['min_close']}")
                logger.info(f"  Max: {stats['max_close']}")
                logger.info(f"  Avg: {stats['avg_close']:.2f}")
                logger.info(f"  Total Records: {stats['total_records']}")
                
                # Analyze the range
                if stats['max_close'] < 10000:
                    logger.info("  → Data appears to be in CENTS (need to divide by 100)")
                else:
                    logger.info("  → Data appears to be in DOLLARS (no conversion needed)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Price format check failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking price data format...")
    success = check_price_format()
    
    if success:
        logger.info("✅ Price format check completed!")
    else:
        logger.error("❌ Price format check failed!")
        sys.exit(1) 