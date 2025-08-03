"""
Check for older price data that might be stored in dollars
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

def check_older_price_data():
    """Check for older price data that might be in dollars"""
    
    try:
        # Import with fallback
        try:
            from daily_run.database import DatabaseManager
        except ImportError:
            # Add daily_run to path and try again
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))
            from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Check price data for major stocks - look for data in dollars
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
        
        logger.info("--- Checking for price data in dollars ---")
        
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            for ticker in test_tickers:
                # Look for data that's clearly in dollars (over 1000)
                cursor.execute("""
                    SELECT ticker, close, date, open, high, low
                    FROM daily_charts 
                    WHERE ticker = %s AND close > 1000
                    ORDER BY date DESC 
                    LIMIT 5
                """, (ticker,))
                
                results = cursor.fetchall()
                if results:
                    logger.info(f"\n{ticker} - Recent data in DOLLARS:")
                    for i, row in enumerate(results):
                        logger.info(f"  {row['date']}: Close=${row['close']:.2f}, Open=${row['open']:.2f}, High=${row['high']:.2f}, Low=${row['low']:.2f}")
                else:
                    logger.warning(f"No dollar-format data found for {ticker}")
                
                # Also check the most recent data regardless of format
                cursor.execute("""
                    SELECT ticker, close, date
                    FROM daily_charts 
                    WHERE ticker = %s 
                    ORDER BY date DESC 
                    LIMIT 1
                """, (ticker,))
                
                latest = cursor.fetchone()
                if latest:
                    logger.info(f"  Latest data for {ticker}: {latest['date']} - ${latest['close']}")
        
        # Check if there are any recent dates with dollar-format data
        logger.info("\n--- Checking for recent dollar-format data ---")
        with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT DISTINCT date
                FROM daily_charts 
                WHERE close > 1000
                ORDER BY date DESC 
                LIMIT 10
            """)
            
            dollar_dates = cursor.fetchall()
            if dollar_dates:
                logger.info("Recent dates with dollar-format data:")
                for row in dollar_dates:
                    logger.info(f"  {row['date']}")
            else:
                logger.warning("No recent dollar-format data found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Price data check failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking for older price data in dollars...")
    success = check_older_price_data()
    
    if success:
        logger.info("✅ Price data check completed!")
    else:
        logger.error("❌ Price data check failed!")
        sys.exit(1) 