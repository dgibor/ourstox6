#!/usr/bin/env python3
"""
Fix Corrupted VWAP Data
Recalculates VWAP from price/volume data to fix corrupted database values
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

class VWAPFixer:
    """Fixes corrupted VWAP data in the database"""
    
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
    
    def get_stocks_with_vwap_issues(self) -> List[str]:
        """Get stocks that have unrealistic VWAP values"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get stocks where VWAP is more than 10x current price or less than 0.1x current price
            cursor.execute("""
                SELECT DISTINCT dc.ticker 
                FROM daily_charts dc
                WHERE dc.vwap IS NOT NULL 
                AND dc.date = (SELECT MAX(date) FROM daily_charts WHERE ticker = dc.ticker)
                AND (
                    dc.vwap > dc.close * 10 OR 
                    dc.vwap < dc.close * 0.1 OR
                    dc.vwap > 1000000 OR
                    dc.vwap < 100
                )
                ORDER BY dc.ticker
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting stocks with VWAP issues: {e}")
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
            if 'volume' in df.columns and not df['volume'].isna().all() and df['volume'].sum() > 0:
                # Use volume-weighted average
                vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
            else:
                # Fallback to simple average if no volume data
                vwap = df['close'].mean()
            
            # Convert to database format (multiply by 100 for bigint storage)
            vwap_db = int(vwap * 100)
            
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
    
    def fix_all_vwap_issues(self) -> Dict[str, bool]:
        """Fix VWAP for all stocks with issues"""
        try:
            # Get stocks with VWAP issues
            problematic_stocks = self.get_stocks_with_vwap_issues()
            logger.info(f"Found {len(problematic_stocks)} stocks with VWAP issues")
            
            if not problematic_stocks:
                logger.info("No VWAP issues found")
                return {}
            
            results = {}
            
            for ticker in problematic_stocks:
                logger.info(f"Fixing VWAP for {ticker}...")
                success, vwap = self.recalculate_vwap_for_stock(ticker)
                results[ticker] = success
                
                if success:
                    logger.info(f"✅ Successfully fixed VWAP for {ticker}: ${vwap:.2f}")
                else:
                    logger.error(f"❌ Failed to fix VWAP for {ticker}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fix_all_vwap_issues: {e}")
            return {}
    
    def validate_vwap_fixes(self) -> Dict[str, Dict]:
        """Validate that VWAP fixes are working correctly"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get sample of stocks to validate
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
                        
                        # Check if VWAP is realistic
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
            logger.error(f"Error validating VWAP fixes: {e}")
            return {}

def main():
    """Main function to fix VWAP issues"""
    fixer = VWAPFixer()
    
    if not fixer.connect_db():
        logger.error("Failed to connect to database")
        return
    
    try:
        logger.info("Starting VWAP data fix...")
        
        # Fix all VWAP issues
        fix_results = fixer.fix_all_vwap_issues()
        
        # Show results
        successful_fixes = sum(1 for success in fix_results.values() if success)
        total_attempts = len(fix_results)
        
        print(f"\n{'='*60}")
        print("VWAP FIX RESULTS")
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
        validation_results = fixer.validate_vwap_fixes()
        
        if validation_results:
            print(f"\n{'='*60}")
            print("VWAP VALIDATION RESULTS")
            print(f"{'='*60}")
            
            for ticker, data in validation_results.items():
                status = "✅ REALISTIC" if data['is_realistic'] else "❌ UNREALISTIC"
                print(f"\n{ticker}:")
                print(f"  Close: ${data['close']:.2f}")
                print(f"  VWAP: ${data['vwap']:.2f}")
                print(f"  Price vs VWAP: {data['vwap_ratio']}")
                print(f"  Status: {status}")
        
        print(f"\n{'='*60}")
        print("VWAP FIX COMPLETED")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    
    finally:
        fixer.disconnect_db()

if __name__ == "__main__":
    main()
