#!/usr/bin/env python3
"""
FIX CORRUPTED DATA
This script identifies and fixes corrupted price data in the database.
"""

import psycopg2
import pandas as pd
import logging
from daily_run.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCorruptionFixer:
    def __init__(self):
        self.db = None
        
    def connect_db(self):
        """Connect to database"""
        try:
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
            
    def identify_corrupted_data(self):
        """Identify stocks with corrupted price data"""
        try:
            cursor = self.db.connection.cursor()
            
            # Find stocks with unrealistic prices
            cursor.execute("""
                SELECT 
                    ticker,
                    close,
                    vwap,
                    support_1,
                    resistance_1
                FROM daily_charts 
                WHERE close < 100 OR close > 10000000
                   OR vwap < 100 OR vwap > 10000000
                   OR support_1 < 100 OR support_1 > 10000000
                   OR resistance_1 < 100 OR resistance_1 > 10000000
                ORDER BY ticker
            """)
            
            corrupted_stocks = cursor.fetchall()
            cursor.close()
            
            logger.info(f"Found {len(corrupted_stocks)} stocks with corrupted data")
            return corrupted_stocks
            
        except Exception as e:
            logger.error(f"Error identifying corrupted data: {e}")
            return []
            
    def fix_corrupted_data(self):
        """Fix corrupted price data by multiplying by 100 if values are too low"""
        try:
            cursor = self.db.connection.cursor()
            
            # Fix close prices
            cursor.execute("""
                UPDATE daily_charts 
                SET close = close * 100
                WHERE close < 100 AND close > 0
            """)
            close_fixed = cursor.rowcount
            
            # Fix VWAP
            cursor.execute("""
                UPDATE daily_charts 
                SET vwap = vwap * 100
                WHERE vwap < 100 AND vwap > 0
            """)
            vwap_fixed = cursor.rowcount
            
            # Fix support levels
            cursor.execute("""
                UPDATE daily_charts 
                SET support_1 = support_1 * 100
                WHERE support_1 < 100 AND support_1 > 0
            """)
            support_fixed = cursor.rowcount
            
            cursor.execute("""
                UPDATE daily_charts 
                SET support_2 = support_2 * 100
                WHERE support_2 < 100 AND support_2 > 0
            """)
            support2_fixed = cursor.rowcount
            
            cursor.execute("""
                UPDATE daily_charts 
                SET support_3 = support_3 * 100
                WHERE support_3 < 100 AND support_3 > 0
            """)
            support3_fixed = cursor.rowcount
            
            # Fix resistance levels
            cursor.execute("""
                UPDATE daily_charts 
                SET resistance_1 = resistance_1 * 100
                WHERE resistance_1 < 100 AND resistance_1 > 0
            """)
            resistance_fixed = cursor.rowcount
            
            cursor.execute("""
                UPDATE daily_charts 
                SET resistance_2 = resistance_2 * 100
                WHERE resistance_2 < 100 AND resistance_2 > 0
            """)
            resistance2_fixed = cursor.rowcount
            
            cursor.execute("""
                UPDATE daily_charts 
                SET resistance_3 = resistance_3 * 100
                WHERE resistance_3 < 100 AND resistance_3 > 0
            """)
            resistance3_fixed = cursor.rowcount
            
            # Fix moving averages
            cursor.execute("""
                UPDATE daily_charts 
                SET ema_20 = ema_20 * 100
                WHERE ema_20 < 100 AND ema_20 > 0
            """)
            ema20_fixed = cursor.rowcount
            
            cursor.execute("""
                UPDATE daily_charts 
                SET ema_50 = ema_50 * 100
                WHERE ema_50 < 100 AND ema_50 > 0
            """)
            ema50_fixed = cursor.rowcount
            
            cursor.execute("""
                UPDATE daily_charts 
                SET ema_200 = ema_200 * 100
                WHERE ema_200 < 100 AND ema_200 > 0
            """)
            ema200_fixed = cursor.rowcount
            
            # Commit changes
            self.db.connection.commit()
            cursor.close()
            
            logger.info(f"Fixed corrupted data:")
            logger.info(f"  Close prices: {close_fixed}")
            logger.info(f"  VWAP: {vwap_fixed}")
            logger.info(f"  Support levels: {support_fixed + support2_fixed + support3_fixed}")
            logger.info(f"  Resistance levels: {resistance_fixed + resistance2_fixed + resistance3_fixed}")
            logger.info(f"  Moving averages: {ema20_fixed + ema50_fixed + ema200_fixed}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fixing corrupted data: {e}")
            self.db.connection.rollback()
            return False
            
    def verify_fixes(self):
        """Verify that corrupted data has been fixed"""
        try:
            cursor = self.db.connection.cursor()
            
            # Check for remaining corrupted data
            cursor.execute("""
                SELECT COUNT(*) 
                FROM daily_charts 
                WHERE close < 100 OR close > 10000000
                   OR vwap < 100 OR vwap > 10000000
            """)
            
            remaining_corrupted = cursor.fetchone()[0]
            cursor.close()
            
            if remaining_corrupted == 0:
                logger.info("✅ All corrupted data has been fixed!")
                return True
            else:
                logger.warning(f"⚠️  {remaining_corrupted} records still have corrupted data")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying fixes: {e}")
            return False

def main():
    """Main execution function"""
    try:
        # Initialize fixer
        fixer = DataCorruptionFixer()
        
        # Connect to database
        if not fixer.connect_db():
            logger.error("Failed to connect to database")
            return
            
        # Identify corrupted data
        corrupted_stocks = fixer.identify_corrupted_data()
        
        if corrupted_stocks:
            logger.info("Corrupted stocks found:")
            for stock in corrupted_stocks:
                logger.info(f"  {stock[0]}: Close=${stock[1]}, VWAP=${stock[2]}")
            
            # Fix corrupted data
            if fixer.fix_corrupted_data():
                # Verify fixes
                fixer.verify_fixes()
            else:
                logger.error("Failed to fix corrupted data")
        else:
            logger.info("No corrupted data found")
            
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        
    finally:
        # Cleanup
        if 'fixer' in locals():
            fixer.disconnect_db()

if __name__ == "__main__":
    main()
