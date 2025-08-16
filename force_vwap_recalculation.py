#!/usr/bin/env python3
"""
Force VWAP Recalculation
Forces recalculation of VWAP for all stocks to fix corrupted data
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

class ForceVWAPRecalculator:
    """Forces VWAP recalculation for all stocks"""
    
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
    
    def get_all_stocks(self) -> List[str]:
        """Get all stocks that have recent data"""
        try:
            cursor = self.db.connection.cursor()
            
            cursor.execute("""
                SELECT DISTINCT ticker 
                FROM daily_charts 
                WHERE date = (SELECT MAX(date) FROM daily_charts)
                ORDER BY ticker
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting all stocks: {e}")
            return []
    
    def recalculate_vwap_for_stock(self, ticker: str) -> Tuple[bool, float]:
        """Recalculate VWAP for a specific stock"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get last 100 days of price/volume data
            cursor.execute("""
                SELECT date, open, high, low, close, volume 
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 100
            """, (ticker,))
            
            price_data = cursor.fetchall()
            
            if not price_data:
                logger.warning(f"No price data found for {ticker}")
                return False, 0.0
            
            # Convert to DataFrame
            df = pd.DataFrame(price_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate VWAP: (Price × Volume) / Volume
            # Note: Database prices are already stored as 100x (bigint format)
            # So we don't need to multiply by 100 again
            if 'volume' in df.columns and not df['volume'].isna().all() and df['volume'].sum() > 0:
                # Use volume-weighted average
                vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
            else:
                # Fallback to simple average if no volume data
                vwap = df['close'].mean()
            
            # Database already stores prices as 100x, so VWAP should be stored as-is
            vwap_db = int(vwap)
            
            # Update the database
            cursor.execute("""
                UPDATE daily_charts 
                SET vwap = %s 
                WHERE ticker = %s AND date = (SELECT MAX(date) FROM daily_charts WHERE ticker = %s)
            """, (vwap_db, ticker, ticker))
            
            self.db.connection.commit()
            cursor.close()
            
            logger.info(f"Updated VWAP for {ticker}: {vwap:.2f} (DB: {vwap_db})")
            return True, vwap
            
        except Exception as e:
            logger.error(f"Error recalculating VWAP for {ticker}: {e}")
            return False, 0.0
    
    def recalculate_all_vwap(self) -> Dict[str, bool]:
        """Recalculate VWAP for all stocks"""
        try:
            # Get all stocks
            all_stocks = self.get_all_stocks()
            logger.info(f"Found {len(all_stocks)} stocks to process")
            
            if not all_stocks:
                logger.info("No stocks found")
                return {}
            
            results = {}
            
            for i, ticker in enumerate(all_stocks, 1):
                logger.info(f"Processing {ticker} ({i}/{len(all_stocks)})...")
                success, vwap = self.recalculate_vwap_for_stock(ticker)
                results[ticker] = success
                
                if success:
                    logger.info(f"✅ Successfully recalculated VWAP for {ticker}: ${vwap:.2f}")
                else:
                    logger.error(f"❌ Failed to recalculate VWAP for {ticker}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in recalculate_all_vwap: {e}")
            return {}
    
    def validate_vwap_calculation(self) -> Dict[str, Dict]:
        """Validate that VWAP recalculation worked correctly"""
        try:
            cursor = self.db.connection.cursor()
            
            # Test tickers
            test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
            
            validation_results = {}
            
            for ticker in test_tickers:
                cursor.execute("""
                    SELECT close, vwap, date 
                    FROM daily_charts 
                    WHERE ticker = %s 
                    ORDER BY date DESC 
                    LIMIT 1
                """, (ticker,))
                
                result = cursor.fetchone()
                if result:
                    close_price, vwap, date = result
                    
                    # Convert to actual prices
                    actual_close = close_price / 100.0
                    actual_vwap = vwap / 100.0 if vwap else 0.0
                    
                    # Calculate price vs VWAP relationship
                    if actual_vwap > 0:
                        price_vs_vwap = actual_close / actual_vwap
                        vwap_ratio = f"{price_vs_vwap:.2f}x"
                        
                        # Check if VWAP is realistic (within 0.1x to 10x of current price)
                        is_realistic = 0.1 <= price_vs_vwap <= 10.0
                        
                        validation_results[ticker] = {
                            'close': actual_close,
                            'vwap': actual_vwap,
                            'price_vs_vwap': price_vs_vwap,
                            'vwap_ratio': vwap_ratio,
                            'is_realistic': is_realistic,
                            'date': date
                        }
                    else:
                        validation_results[ticker] = {
                            'close': actual_close,
                            'vwap': 0.0,
                            'price_vs_vwap': 0.0,
                            'vwap_ratio': 'N/A',
                            'is_realistic': False,
                            'date': date
                        }
            
            cursor.close()
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating VWAP calculation: {e}")
            return {}

def main():
    """Main function to force VWAP recalculation"""
    calculator = ForceVWAPRecalculator()
    
    if not calculator.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting forced VWAP recalculation...")
        
        # Recalculate all VWAP
        recalc_results = calculator.recalculate_all_vwap()
        
        # Show results
        successful_recalcs = sum(1 for success in recalc_results.values() if success)
        total_attempts = len(recalc_results)
        
        print(f"\n{'='*60}")
        print("VWAP RECALCULATION RESULTS")
        print(f"{'='*60}")
        print(f"Total stocks processed: {total_attempts}")
        print(f"Successful recalculations: {successful_recalcs}")
        print(f"Failed recalculations: {total_attempts - successful_recalcs}")
        print(f"Success rate: {successful_recalcs/total_attempts*100:.1f}%")
        
        # Validate recalculation
        logger.info("Validating VWAP recalculation...")
        validation_results = calculator.validate_vwap_calculation()
        
        if validation_results:
            print(f"\n{'='*60}")
            print("VWAP VALIDATION RESULTS")
            print(f"{'='*60}")
            
            realistic_count = 0
            total_count = len(validation_results)
            
            for ticker, data in validation_results.items():
                status = "✅ REALISTIC" if data['is_realistic'] else "❌ UNREALISTIC"
                if data['is_realistic']:
                    realistic_count += 1
                    
                print(f"\n{ticker}:")
                print(f"  Close: ${data['close']:.2f}")
                print(f"  VWAP: ${data['vwap']:.2f}")
                print(f"  Price vs VWAP: {data['vwap_ratio']}")
                print(f"  Status: {status}")
            
            print(f"\n{'='*40}")
            print(f"VALIDATION SUMMARY:")
            print(f"  Realistic VWAP: {realistic_count}/{total_count}")
            print(f"  Unrealistic VWAP: {total_count - realistic_count}/{total_count}")
            print(f"  Realistic Rate: {realistic_count/total_count*100:.1f}%")
            print(f"{'='*40}")
        
        print(f"\n{'='*60}")
        print("VWAP RECALCULATION COMPLETED")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        calculator.disconnect_db()

if __name__ == "__main__":
    main()
