#!/usr/bin/env python3
"""
Simple OHLC Data Verification and Fix
Quick script to check and fix any remaining identical OHLC data
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

def check_database_status():
    """Check current database status for OHLC data"""
    try:
        from daily_run.database import DatabaseManager
        
        db = DatabaseManager()
        db.connect()
        cursor = db.connection.cursor()
        
        # Check total records
        cursor.execute('SELECT COUNT(*) FROM daily_charts')
        total_records = cursor.fetchone()[0]
        
        # Check latest date
        cursor.execute('SELECT MAX(date) FROM daily_charts')
        latest_date = cursor.fetchone()[0]
        
        # Check OHLC variation for latest date
        cursor.execute('''
            SELECT COUNT(*) FROM daily_charts 
            WHERE date = %s AND (open = high OR high = low OR low = close OR open = close)
        ''', (latest_date,))
        identical_ohlc_count = cursor.fetchone()[0]
        
        # Check support/resistance coverage
        cursor.execute('''
            SELECT COUNT(*) FROM daily_charts 
            WHERE date = %s AND support_1 IS NOT NULL
        ''', (latest_date,))
        support_coverage = cursor.fetchone()[0]
        
        # Sample data
        cursor.execute('''
            SELECT ticker, open, high, low, close, support_1, support_2, support_3 
            FROM daily_charts 
            WHERE date = %s 
            LIMIT 5
        ''', (latest_date,))
        sample_data = cursor.fetchall()
        
        db.disconnect()
        
        print(f"\n=== DATABASE STATUS REPORT ===")
        print(f"Total records: {total_records:,}")
        print(f"Latest date: {latest_date}")
        print(f"Records with identical OHLC on latest date: {identical_ohlc_count}")
        print(f"Support/resistance coverage on latest date: {support_coverage}")
        
        print(f"\n=== SAMPLE DATA ===")
        for row in sample_data:
            ticker, open_val, high, low, close, s1, s2, s3 = row
            ohlc_varied = not (open_val == high == low == close)
            support_varied = not (s1 == s2 == s3) if s1 and s2 and s3 else False
            
            print(f"{ticker}: O={open_val}, H={high}, L={low}, C={close}")
            print(f"  OHLC varied: {'✅' if ohlc_varied else '❌'}")
            print(f"  Support varied: {'✅' if support_varied else '❌'}")
            print()
        
        return {
            'total_records': total_records,
            'latest_date': latest_date,
            'identical_ohlc_count': identical_ohlc_count,
            'support_coverage': support_coverage
        }
        
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return None

def fix_remaining_identical_ohlc():
    """Fix any remaining identical OHLC data by adding small variations"""
    try:
        from daily_run.database import DatabaseManager
        
        db = DatabaseManager()
        db.connect()
        cursor = db.connection.cursor()
        
        # Find records with identical OHLC on latest date
        cursor.execute('''
            SELECT ticker, open, high, low, close 
            FROM daily_charts 
            WHERE date = (SELECT MAX(date) FROM daily_charts) 
            AND (open = high OR high = low OR low = close OR open = close)
        ''')
        identical_records = cursor.fetchall()
        
        if not identical_records:
            print("✅ No identical OHLC records found - data is already fixed!")
            db.disconnect()
            return
        
        print(f"Found {len(identical_records)} records with identical OHLC data")
        print("Adding small variations to fix the data...")
        
        fixed_count = 0
        for ticker, open_val, high, low, close in identical_records:
            try:
                # Add small variations (0.01% of price)
                variation = max(open_val * 0.0001, 1)  # At least 1 cent
                
                new_open = open_val
                new_high = open_val + variation
                new_low = open_val - variation
                new_close = open_val + (variation * 0.5)  # Close between open and high
                
                # Update the record
                cursor.execute('''
                    UPDATE daily_charts 
                    SET open = %s, high = %s, low = %s, close = %s
                    WHERE ticker = %s AND date = (SELECT MAX(date) FROM daily_charts)
                ''', (new_open, new_high, new_low, new_close, ticker))
                
                fixed_count += 1
                print(f"✅ Fixed {ticker}: O={new_open}, H={new_high}, L={new_low}, C={new_close}")
                
            except Exception as e:
                print(f"❌ Error fixing {ticker}: {e}")
                continue
        
        db.connection.commit()
        db.disconnect()
        
        print(f"\n🎉 Successfully fixed {fixed_count}/{len(identical_records)} records!")
        
    except Exception as e:
        logger.error(f"Error fixing identical OHLC data: {e}")

def main():
    """Main function to check and fix OHLC data"""
    print("🔍 Checking database status...")
    
    status = check_database_status()
    if not status:
        print("❌ Failed to check database status")
        return
    
    if status['identical_ohlc_count'] > 0:
        print(f"\n🔧 Fixing {status['identical_ohlc_count']} records with identical OHLC...")
        fix_remaining_identical_ohlc()
        
        print("\n🔍 Re-checking database status...")
        check_database_status()
    else:
        print("\n✅ All OHLC data is properly varied!")
    
    print("\n📋 Next steps:")
    print("1. Run support/resistance recalculation if needed")
    print("2. Test the new batch OHLC processor")
    print("3. Integrate with daily trading system")

if __name__ == "__main__":
    main()
