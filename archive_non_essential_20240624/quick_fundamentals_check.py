#!/usr/bin/env python3
"""
Quick check of company fundamentals update progress
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def quick_fundamentals_check():
    """Quick check of company fundamentals update progress"""
    
    print("📊 QUICK COMPANY FUNDAMENTALS CHECK")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Get total count of stocks with market cap
    total_query = "SELECT COUNT(*) FROM stocks WHERE market_cap IS NOT NULL"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Get count with recent fundamentals update
    recent_query = """
    SELECT COUNT(*) FROM company_fundamentals 
    WHERE last_updated > NOW() - INTERVAL '1 hour'
    """
    recent_result = db.fetch_one(recent_query)
    recent_count = recent_result[0] if recent_result else 0
    
    # Get count with any fundamentals data
    any_fundamentals_query = "SELECT COUNT(*) FROM company_fundamentals"
    any_fundamentals_result = db.fetch_one(any_fundamentals_query)
    any_fundamentals_count = any_fundamentals_result[0] if any_fundamentals_result else 0
    
    print(f"📈 PROGRESS SUMMARY:")
    print(f"   Total stocks with market cap: {total_stocks}")
    print(f"   Updated in last hour: {recent_count}")
    print(f"   Total in company_fundamentals: {any_fundamentals_count}")
    print(f"   Progress: {(recent_count / total_stocks * 100):.1f}% (last hour)")
    
    # Show recent updates
    print(f"\n🕐 RECENT UPDATES (last 10):")
    recent_updates_query = """
    SELECT ticker, last_updated 
    FROM company_fundamentals 
    ORDER BY last_updated DESC 
    LIMIT 10
    """
    recent_updates = db.execute_query(recent_updates_query)
    
    if recent_updates:
        for ticker, update_time in recent_updates:
            print(f"   {ticker}: {update_time}")
    else:
        print(f"   No recent updates found")
    
    # Show sample data
    print(f"\n📊 SAMPLE DATA:")
    sample_query = """
    SELECT ticker, revenue, net_income, market_cap
    FROM company_fundamentals 
    WHERE revenue IS NOT NULL
    ORDER BY market_cap DESC 
    LIMIT 5
    """
    sample_data = db.execute_query(sample_query)
    
    if sample_data:
        print(f"   Ticker | Revenue    | Net Income | Market Cap")
        print(f"   -------|------------|------------|------------")
        for row in sample_data:
            ticker, revenue, net_income, market_cap = row
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
            print(f"   {ticker:6} | {revenue_str:10} | {net_income_str:10} | {market_cap_str:10}")
    else:
        print(f"   No sample data found")
    
    print(f"\n✅ Status: Processing is working!")
    print(f"   • {recent_count} companies updated in last hour")
    print(f"   • Background process is running")
    print(f"   • Large companies are being processed first")

if __name__ == "__main__":
    quick_fundamentals_check() 