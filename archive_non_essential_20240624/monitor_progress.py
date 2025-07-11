#!/usr/bin/env python3
"""
Monitor the progress of batch processing
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def monitor_progress():
    """Monitor the progress of batch processing"""
    
    print("📊 MONITORING BATCH PROCESSING PROGRESS")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Get total count
    total_query = "SELECT COUNT(*) FROM stocks"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Get count with recent fundamentals
    recent_query = """
    SELECT COUNT(*) FROM stocks 
    WHERE fundamentals_last_update > NOW() - INTERVAL '1 hour'
    """
    recent_result = db.fetch_one(recent_query)
    recent_count = recent_result[0] if recent_result else 0
    
    # Get count with any fundamentals
    any_fundamentals_query = """
    SELECT COUNT(*) FROM stocks 
    WHERE revenue_ttm IS NOT NULL OR net_income_ttm IS NOT NULL
    """
    any_fundamentals_result = db.fetch_one(any_fundamentals_query)
    any_fundamentals_count = any_fundamentals_result[0] if any_fundamentals_result else 0
    
    print(f"📈 PROGRESS SUMMARY:")
    print(f"   Total stocks in database: {total_stocks}")
    print(f"   Updated in last hour: {recent_count}")
    print(f"   With fundamentals data: {any_fundamentals_count}")
    print(f"   Progress: {(recent_count / total_stocks * 100):.1f}% (last hour)")
    print(f"   Overall coverage: {(any_fundamentals_count / total_stocks * 100):.1f}%")
    
    # Show recent updates
    print(f"\n🕐 RECENT UPDATES (last 10):")
    recent_updates_query = """
    SELECT ticker, fundamentals_last_update 
    FROM stocks 
    WHERE fundamentals_last_update IS NOT NULL
    ORDER BY fundamentals_last_update DESC 
    LIMIT 10
    """
    recent_updates = db.execute_query(recent_updates_query)
    
    if recent_updates:
        for ticker, update_time in recent_updates:
            print(f"   {ticker}: {update_time}")
    else:
        print(f"   No recent updates found")
    
    # Show some sample data
    print(f"\n📊 SAMPLE DATA (5 stocks):")
    sample_query = """
    SELECT ticker, revenue_ttm, net_income_ttm, market_cap, fundamentals_last_update
    FROM stocks 
    WHERE revenue_ttm IS NOT NULL
    ORDER BY fundamentals_last_update DESC 
    LIMIT 5
    """
    sample_data = db.execute_query(sample_query)
    
    if sample_data:
        print(f"   Ticker | Revenue    | Net Income | Market Cap | Last Update")
        print(f"   -------|------------|------------|------------|-------------")
        for ticker, revenue, net_income, market_cap, last_update in sample_data:
            # Convert decimal to float
            def to_float(val):
                try:
                    return float(val) if val is not None else None
                except Exception:
                    return None
            
            revenue_float = to_float(revenue)
            net_income_float = to_float(net_income)
            market_cap_float = to_float(market_cap)
            
            revenue_str = f"${revenue_float/1e9:.1f}B" if revenue_float else "NULL"
            net_income_str = f"${net_income_float/1e9:.1f}B" if net_income_float else "NULL"
            market_cap_str = f"${market_cap_float/1e9:.1f}B" if market_cap_float else "NULL"
            update_str = last_update.strftime('%H:%M:%S') if last_update else "NULL"
            print(f"   {ticker:6} | {revenue_str:10} | {net_income_str:10} | {market_cap_str:10} | {update_str}")
    else:
        print(f"   No sample data found")
    
    print(f"\n💡 TIPS:")
    print(f"   • Check the log file for detailed progress")
    print(f"   • The process runs in batches of 20 stocks")
    print(f"   • Each stock takes ~2-3 seconds to process")
    print(f"   • Estimated completion: {total_stocks * 2 / 60:.1f} minutes total")

if __name__ == "__main__":
    monitor_progress() 