#!/usr/bin/env python3
"""
Targeted Support/Resistance Calculator
Fills in missing support/resistance data for stocks without running the full daily system
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add daily_run to path for imports
sys.path.append('daily_run')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupportResistanceFiller:
    """Targeted support/resistance calculator and database updater"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.db_connection = None
        
    def get_db_connection(self):
        """Get database connection"""
        if not self.db_connection or self.db_connection.closed:
            try:
                self.db_connection = psycopg2.connect(**self.db_config)
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self.db_connection
    
    def get_stocks_needing_support_resistance(self) -> List[str]:
        """Get list of stocks that need support/resistance data"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Find stocks with recent data but missing support/resistance
            query = """
            SELECT DISTINCT ticker 
            FROM daily_charts 
            WHERE date = (SELECT MAX(date) FROM daily_charts)
            AND (support_1 IS NULL OR resistance_1 IS NULL OR pivot_point IS NULL)
            ORDER BY ticker
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            tickers = [row[0] for row in results]
            
            logger.info(f"Found {len(tickers)} stocks needing support/resistance data")
            return tickers
            
        except Exception as e:
            logger.error(f"Error getting stocks needing support/resistance: {e}")
            return []
    
    def get_price_data(self, ticker: str, days: int = 60) -> Optional[pd.DataFrame]:
        """Get price data for a ticker"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
            SELECT date, open, high, low, close, volume
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT %s
            """
            
            cursor.execute(query, (ticker, days))
            results = cursor.fetchall()
            
            if not results:
                logger.warning(f"No data found for {ticker}")
                return None
            
            df = pd.DataFrame(results, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Convert to numeric
            price_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in price_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting data for {ticker}: {e}")
            return None
    
    def calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        try:
            if len(df) < 20:
                logger.warning(f"Insufficient data for {len(df)} days, need at least 20")
                return {}
            
            # Basic support and resistance levels
            high = df['high']
            low = df['low']
            close = df['close']
            
            # Support levels (rolling minimums)
            support_1 = low.rolling(window=20).min().iloc[-1]
            support_2 = low.rolling(window=40).min().iloc[-1]
            support_3 = low.rolling(window=60).min().iloc[-1]
            
            # Resistance levels (rolling maximums)
            resistance_1 = high.rolling(window=20).max().iloc[-1]
            resistance_2 = high.rolling(window=40).max().iloc[-1]
            resistance_3 = high.rolling(window=60).max().iloc[-1]
            
            # Pivot point
            latest_high = high.iloc[-1]
            latest_low = low.iloc[-1]
            latest_close = close.iloc[-1]
            pivot_point = (latest_high + latest_low + latest_close) / 3
            
            # Swing levels
            swing_high_5d = high.rolling(window=5).max().iloc[-1]
            swing_low_5d = low.rolling(window=5).min().iloc[-1]
            swing_high_10d = high.rolling(window=10).max().iloc[-1]
            swing_low_10d = low.rolling(window=10).min().iloc[-1]
            swing_high_20d = high.rolling(window=20).max().iloc[-1]
            swing_low_20d = low.rolling(window=20).min().iloc[-1]
            
            # Weekly and monthly levels
            week_high = high.rolling(window=7).max().iloc[-1]
            week_low = low.rolling(window=7).min().iloc[-1]
            month_high = high.rolling(window=21).max().iloc[-1]
            month_low = low.rolling(window=21).min().iloc[-1]
            
            # Nearest levels
            current_price = close.iloc[-1]
            nearest_support = support_1 if support_1 < current_price else support_2
            nearest_resistance = resistance_1 if resistance_1 > current_price else resistance_2
            
            # Strength indicators (simple implementation)
            support_strength = 5  # Default medium strength
            resistance_strength = 5  # Default medium strength
            
            return {
                'support_1': support_1,
                'support_2': support_2,
                'support_3': support_3,
                'resistance_1': resistance_1,
                'resistance_2': resistance_2,
                'resistance_3': resistance_3,
                'pivot_point': pivot_point,
                'swing_high_5d': swing_high_5d,
                'swing_low_5d': swing_low_5d,
                'swing_high_10d': swing_high_10d,
                'swing_low_10d': swing_low_10d,
                'swing_high_20d': swing_high_20d,
                'swing_low_20d': swing_low_20d,
                'week_high': week_high,
                'week_low': week_low,
                'month_high': month_high,
                'month_low': month_low,
                'nearest_support': nearest_support,
                'nearest_resistance': nearest_resistance,
                'support_strength': support_strength,
                'resistance_strength': resistance_strength
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {}
    
    def update_database(self, ticker: str, indicators: Dict[str, float], target_date: str = None):
        """Update database with support/resistance indicators"""
        if not target_date:
            target_date = date.today().strftime('%Y-%m-%d')
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Build update query
            update_fields = []
            values = []
            
            for indicator, value in indicators.items():
                if value is not None and not pd.isna(value):
                    # Convert float to integer for database storage (multiply by 100 for precision)
                    if isinstance(value, float):
                        value = int(value * 100)
                    
                    update_fields.append(f"{indicator} = %s")
                    values.append(value)
            
            if update_fields:
                values.extend([ticker, target_date])
                
                query = f"""
                UPDATE daily_charts 
                SET {', '.join(update_fields)}
                WHERE ticker = %s AND date = %s
                """
                
                cursor.execute(query, tuple(values))
                conn.commit()
                
                logger.info(f"Updated {len(update_fields)} indicators for {ticker}")
                return len(update_fields)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error updating database for {ticker}: {e}")
            if conn:
                conn.rollback()
            return 0
    
    def process_all_stocks(self):
        """Process all stocks needing support/resistance data"""
        logger.info("Starting support/resistance calculation for all stocks...")
        
        # Get stocks that need data
        tickers = self.get_stocks_needing_support_resistance()
        
        if not tickers:
            logger.info("No stocks need support/resistance data")
            return
        
        successful = 0
        failed = 0
        
        for i, ticker in enumerate(tickers, 1):
            try:
                logger.info(f"Processing {i}/{len(tickers)}: {ticker}")
                
                # Get price data
                price_data = self.get_price_data(ticker, days=60)
                if price_data is None or len(price_data) < 20:
                    logger.warning(f"Insufficient data for {ticker}")
                    failed += 1
                    continue
                
                # Calculate support/resistance
                indicators = self.calculate_support_resistance(price_data)
                if not indicators:
                    logger.warning(f"Failed to calculate indicators for {ticker}")
                    failed += 1
                    continue
                
                # Update database
                updated_count = self.update_database(ticker, indicators)
                if updated_count > 0:
                    successful += 1
                    logger.info(f"✅ {ticker}: Updated {updated_count} indicators")
                else:
                    failed += 1
                    logger.warning(f"❌ {ticker}: Failed to update database")
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                failed += 1
        
        logger.info(f"Support/Resistance calculation completed: {successful} successful, {failed} failed")
        
        # Check final coverage
        self.check_coverage()
    
    def check_coverage(self):
        """Check the final coverage of support/resistance data"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM daily_charts")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM daily_charts WHERE support_1 IS NOT NULL")
            support_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM daily_charts WHERE resistance_1 IS NOT NULL")
            resistance_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM daily_charts WHERE pivot_point IS NOT NULL")
            pivot_count = cursor.fetchone()[0]
            
            logger.info("=== FINAL COVERAGE REPORT ===")
            logger.info(f"Total records: {total}")
            logger.info(f"Support 1 coverage: {support_count}/{total} ({support_count/total*100:.1f}%)")
            logger.info(f"Resistance 1 coverage: {resistance_count}/{total} ({resistance_count/total*100:.1f}%)")
            logger.info(f"Pivot point coverage: {pivot_count}/{total} ({pivot_count/total*100:.1f}%)")
            
        except Exception as e:
            logger.error(f"Error checking coverage: {e}")

def main():
    """Main execution function"""
    try:
        filler = SupportResistanceFiller()
        filler.process_all_stocks()
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
    finally:
        if hasattr(filler, 'db_connection') and filler.db_connection:
            filler.db_connection.close()

if __name__ == "__main__":
    main()
