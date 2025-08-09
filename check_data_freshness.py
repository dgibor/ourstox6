#!/usr/bin/env python3
"""
Check the freshness of our price data vs chart dates
"""

import sys
sys.path.append('daily_run')

from daily_run.database import DatabaseManager
from datetime import datetime, timedelta

def check_data_freshness():
    """Check how fresh our price data is"""
    
    db = DatabaseManager()
    db.connect()
    
    tickers = ['AAPL', 'NVDA', 'SPY']
    
    print("🔍 DATA FRESHNESS CHECK")
    print("=" * 50)
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
    print()
    
    for ticker in tickers:
        print(f"📊 {ticker}:")
        
        # Get latest price data
        query = """
        SELECT date, close, volume
        FROM daily_charts 
        WHERE ticker = %s 
        ORDER BY date DESC 
        LIMIT 5
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(query, (ticker,))
            results = cursor.fetchall()
        
        if results:
            print(f"  Latest data dates:")
            for i, row in enumerate(results):
                date_str = str(row[0])
                close_price = row[1]
                volume = row[2] if row[2] else 0
                days_ago = (datetime.now().date() - row[0]).days if hasattr(row[0], 'day') else 'Unknown'
                print(f"    {i+1}. {date_str} (${close_price:.2f}, vol={volume:,}) - {days_ago} days ago")
        else:
            print(f"  ❌ No data found for {ticker}")
        
        print()
    
    # Check for recent vs old data pattern
    print("🔍 ANALYSIS:")
    print("- Chart images show today's live values")
    print("- Our database might have stale data")
    print("- Price scaling jumps suggest data inconsistencies")
    print("- Need to verify data update frequency")
    
    db.disconnect()

if __name__ == "__main__":
    check_data_freshness()
