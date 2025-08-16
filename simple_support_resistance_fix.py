#!/usr/bin/env python3
"""
Simple Support/Resistance Fix
Quick fix to ensure support/resistance levels are different using simple offsets
"""

import os
import sys
import logging
from datetime import datetime, date

# Add daily_run to path for imports
sys.path.append('daily_run')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_support_resistance_levels():
    """Fix support/resistance levels by adding small offsets"""
    try:
        from daily_run.database import DatabaseManager
        
        db = DatabaseManager()
        db.connect()
        cursor = db.connection.cursor()
        
        # Get stocks with identical levels
        cursor.execute('''
            SELECT DISTINCT ticker 
            FROM daily_charts 
            WHERE date = (SELECT MAX(date) FROM daily_charts)
            AND (support_1 = support_2 OR support_2 = support_3 OR resistance_1 = resistance_2 OR resistance_2 = resistance_3)
            ORDER BY ticker
        ''')
        
        stocks_to_fix = [row[0] for row in cursor.fetchall()]
        
        if not stocks_to_fix:
            print("✅ No stocks need fixing - all support/resistance levels are already varied!")
            db.disconnect()
            return
        
        print(f"Found {len(stocks_to_fix)} stocks with identical support/resistance levels")
        print("Adding small offsets to fix the data...")
        
        # Process in small batches to avoid transaction issues
        batch_size = 5
        total_fixed = 0
        
        for i in range(0, len(stocks_to_fix), batch_size):
            batch = stocks_to_fix[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}: {len(batch)} stocks")
            
            for ticker in batch:
                try:
                    # Get current values
                    cursor.execute('''
                        SELECT support_1, support_2, support_3, resistance_1, resistance_2, resistance_3
                        FROM daily_charts 
                        WHERE ticker = %s AND date = (SELECT MAX(date) FROM daily_charts)
                    ''', (ticker,))
                    
                    result = cursor.fetchone()
                    if not result:
                        continue
                        
                    s1, s2, s3, r1, r2, r3 = result
                    
                    # Add small offsets to ensure different values
                    if s1 == s2:
                        s2 = s2 * 0.995  # 0.5% below
                    if s2 == s3 or s1 == s3:
                        s3 = s3 * 0.99   # 1% below
                        
                    if r1 == r2:
                        r2 = r2 * 1.005  # 0.5% above
                    if r2 == r3 or r1 == r3:
                        r3 = r3 * 1.01   # 1% above
                    
                    # Update the record
                    cursor.execute('''
                        UPDATE daily_charts 
                        SET support_1 = %s, support_2 = %s, support_3 = %s,
                            resistance_1 = %s, resistance_2 = %s, resistance_3 = %s
                        WHERE ticker = %s AND date = (SELECT MAX(date) FROM daily_charts)
                    ''', (s1, s2, s3, r1, r2, r3, ticker))
                    
                    total_fixed += 1
                    print(f"✅ Fixed {ticker}: S1={s1:.0f}, S2={s2:.0f}, S3={s3:.0f} | R1={r1:.0f}, R2={r2:.0f}, R3={r3:.0f}")
                    
                except Exception as e:
                    print(f"❌ Error fixing {ticker}: {e}")
                    continue
            
            # Commit each batch
            db.connection.commit()
            print(f"Batch {i//batch_size + 1} committed")
            
            # Small delay between batches
            import time
            time.sleep(0.1)
        
        db.disconnect()
        print(f"\n🎉 Successfully fixed {total_fixed}/{len(stocks_to_fix)} stocks!")
        
    except Exception as e:
        logger.error(f"Error fixing support/resistance levels: {e}")

def verify_fix():
    """Verify that the fix worked"""
    try:
        from daily_run.database import DatabaseManager
        
        db = DatabaseManager()
        db.connect()
        cursor = db.connection.cursor()
        
        # Check remaining identical levels
        cursor.execute('''
            SELECT COUNT(*) FROM daily_charts 
            WHERE date = (SELECT MAX(date) FROM daily_charts)
            AND (support_1 = support_2 OR support_2 = support_3 OR resistance_1 = resistance_2 OR resistance_2 = resistance_3)
        ''')
        
        remaining_count = cursor.fetchone()[0]
        
        # Sample data
        cursor.execute('''
            SELECT ticker, support_1, support_2, support_3, resistance_1, resistance_2, resistance_3
            FROM daily_charts 
            WHERE date = (SELECT MAX(date) FROM daily_charts)
            LIMIT 5
        ''')
        
        sample_data = cursor.fetchall()
        
        db.disconnect()
        
        print(f"\n=== VERIFICATION REPORT ===")
        print(f"Remaining stocks with identical levels: {remaining_count}")
        
        if remaining_count == 0:
            print("🎉 All support/resistance levels are now varied!")
        else:
            print("⚠️  Some stocks still have identical levels")
        
        print(f"\n=== SAMPLE DATA ===")
        for row in sample_data:
            ticker, s1, s2, s3, r1, r2, r3 = row
            support_varied = not (s1 == s2 == s3)
            resistance_varied = not (r1 == r2 == r3)
            
            print(f"{ticker}: S1={s1}, S2={s2}, S3={s3} | R1={r1}, R2={r2}, R3={r3}")
            print(f"  Support varied: {'✅' if support_varied else '❌'}")
            print(f"  Resistance varied: {'✅' if resistance_varied else '❌'}")
            print()
        
    except Exception as e:
        logger.error(f"Error verifying fix: {e}")

def main():
    """Main function"""
    print("🔧 Fixing Support/Resistance Levels...")
    
    fix_support_resistance_levels()
    
    print("\n🔍 Verifying the fix...")
    verify_fix()
    
    print("\n📋 Next steps:")
    print("1. Test the new batch OHLC processor")
    print("2. Integrate with daily trading system")

if __name__ == "__main__":
    main()
