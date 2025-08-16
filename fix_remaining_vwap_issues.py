#!/usr/bin/env python3
"""
Fix Remaining VWAP Issues
Targets specific stocks with corrupted VWAP data and fixes them
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

class RemainingVWAPFixer:
    """Fixes remaining corrupted VWAP data for specific stocks"""
    
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
    
    def get_problematic_stocks(self) -> List[str]:
        """Get stocks with unrealistic VWAP values"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get stocks where VWAP is more than 5x current price or less than 0.2x current price
            cursor.execute("""
                SELECT DISTINCT dc.ticker 
                FROM daily_charts dc
                WHERE dc.vwap IS NOT NULL 
                AND dc.date = (SELECT MAX(date) FROM daily_charts WHERE ticker = dc.ticker)
                AND (
                    dc.vwap > dc.close * 5 OR 
                    dc.vwap < dc.close * 0.2
                )
                ORDER BY dc.ticker
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting problematic stocks: {e}")
            return []
    
    def fix_stock_vwap(self, ticker: str) -> Tuple[bool, float]:
        """Fix VWAP for a specific stock"""
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
            # Database prices are already stored as 100x (bigint format)
            if 'volume' in df.columns and not df['volume'].isna().all() and df['volume'].sum() > 0:
                # Use volume-weighted average
                vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
            else:
                # Fallback to simple average if no volume data
                vwap = df['close'].mean()
            
            # Store VWAP as-is (already in 100x format)
            vwap_db = int(vwap)
            
            # Update the database
            cursor.execute("""
                UPDATE daily_charts 
                SET vwap = %s 
                WHERE ticker = %s AND date = (SELECT MAX(date) FROM daily_charts WHERE ticker = %s)
            """, (vwap_db, ticker, ticker))
            
            self.db.connection.commit()
            cursor.close()
            
            # Convert to actual price for logging
            actual_vwap = vwap / 100.0
            logger.info(f"Updated VWAP for {ticker}: ${actual_vwap:.2f} (DB: {vwap_db})")
            return True, actual_vwap
            
        except Exception as e:
            logger.error(f"Error fixing VWAP for {ticker}: {e}")
            return False, 0.0
    
    def fix_all_problematic_stocks(self) -> Dict[str, bool]:
        """Fix VWAP for all problematic stocks"""
        try:
            problematic_stocks = self.get_problematic_stocks()
            logger.info(f"Found {len(problematic_stocks)} stocks with VWAP issues")
            
            if not problematic_stocks:
                logger.info("No VWAP issues found")
                return {}
            
            results = {}
            
            for ticker in problematic_stocks:
                logger.info(f"Fixing VWAP for {ticker}...")
                success, vwap = self.fix_stock_vwap(ticker)
                results[ticker] = success
                
                if success:
                    logger.info(f"✅ Successfully fixed VWAP for {ticker}: ${vwap:.2f}")
                else:
                    logger.error(f"❌ Failed to fix VWAP for {ticker}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fix_all_problematic_stocks: {e}")
            return {}
    
    def validate_fixes(self) -> Dict[str, Dict]:
        """Validate that VWAP fixes are working correctly"""
        try:
            cursor = self.db.connection.cursor()
            
            # Test tickers that were problematic
            test_tickers = ['NVDA', 'META', 'NFLX', 'AMD', 'INTC']
            
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
                        
                        # Check if VWAP is realistic (within 0.2x to 5x of current price)
                        is_realistic = 0.2 <= price_vs_vwap <= 5.0
                        
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
            logger.error(f"Error validating fixes: {e}")
            return {}

def main():
    """Main function to fix remaining VWAP issues"""
    fixer = RemainingVWAPFixer()
    
    if not fixer.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting remaining VWAP fixes...")
        
        # Fix all problematic stocks
        fix_results = fixer.fix_all_problematic_stocks()
        
        # Show results
        successful_fixes = sum(1 for success in fix_results.values() if success)
        total_attempts = len(fix_results)
        
        print(f"\n{'='*60}")
        print("REMAINING VWAP FIX RESULTS")
        print(f"{'='*60}")
        print(f"Total stocks processed: {total_attempts}")
        print(f"Successful fixes: {successful_fixes}")
        print(f"Failed fixes: {total_attempts - successful_fixes}")
        print(f"Success rate: {successful_fixes/total_attempts*100:.1f}%")
        
        if fix_results:
            print(f"\nDetailed Results:")
            for ticker, success in fix_results.items():
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"  {ticker}: {status}")
        
        # Validate fixes
        logger.info("Validating VWAP fixes...")
        validation_results = fixer.validate_fixes()
        
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
        print("REMAINING VWAP FIXES COMPLETED")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        fixer.disconnect_db()

if __name__ == "__main__":
    main()
