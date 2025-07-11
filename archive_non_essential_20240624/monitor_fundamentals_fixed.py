#!/usr/bin/env python3
"""
Monitor the progress of fixed company fundamentals update
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def monitor_fundamentals_fixed():
    """Monitor the progress of fixed company fundamentals update"""
    
    print("📊 MONITORING FIXED COMPANY FUNDAMENTALS UPDATE")
    print("=" * 60)
    
    db = DatabaseManager()
    
    # Get total count of stocks with market cap
    total_query = "SELECT COUNT(*) FROM stocks WHERE market_cap IS NOT NULL"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Get count with recent fundamentals update
    recent_query = """
    SELECT COUNT(*) FROM company_fundamentals 
    WHERE last_updated > NOW() - INTERVAL '30 minutes'
    """
    recent_result = db.fetch_one(recent_query)
    recent_count = recent_result[0] if recent_result else 0
    
    # Get count with any fundamentals data
    any_fundamentals_query = "SELECT COUNT(*) FROM company_fundamentals"
    any_fundamentals_result = db.fetch_one(any_fundamentals_query)
    any_fundamentals_count = any_fundamentals_result[0] if any_fundamentals_result else 0
    
    print(f"📈 PROGRESS SUMMARY:")
    print(f"   Total stocks with market cap: {total_stocks}")
    print(f"   Updated in last 30 minutes: {recent_count}")
    print(f"   Total in company_fundamentals: {any_fundamentals_count}")
    print(f"   Progress: {(recent_count / total_stocks * 100):.1f}% (last 30 min)")
    print(f"   Overall coverage: {(any_fundamentals_count / total_stocks * 100):.1f}%")
    
    # Show recent updates
    print(f"\n🕐 RECENT UPDATES (last 15):")
    recent_updates_query = """
    SELECT ticker, last_updated 
    FROM company_fundamentals 
    ORDER BY last_updated DESC 
    LIMIT 15
    """
    recent_updates = db.execute_query(recent_updates_query)
    
    if recent_updates:
        for ticker, update_time in recent_updates:
            print(f"   {ticker}: {update_time}")
    else:
        print(f"   No recent updates found")
    
    # Show largest companies processed
    print(f"\n🏆 LARGEST COMPANIES PROCESSED:")
    largest_query = """
    SELECT cf.ticker, cf.market_cap, cf.last_updated
    FROM company_fundamentals cf
    WHERE cf.market_cap IS NOT NULL
    ORDER BY cf.market_cap DESC
    LIMIT 10
    """
    largest_data = db.execute_query(largest_query)
    
    if largest_data:
        print(f"   Ticker | Market Cap | Last Update")
        print(f"   -------|------------|-------------")
        for ticker, market_cap, last_update in largest_data:
            # Convert decimal to float
            def to_float(val):
                try:
                    return float(val) if val is not None else None
                except Exception:
                    return None
            
            market_cap_float = to_float(market_cap)
            market_cap_b = market_cap_float / 1e9 if market_cap_float else 0
            update_str = last_update.strftime('%H:%M:%S') if last_update else "NULL"
            print(f"   {ticker:6} | ${market_cap_b:8.1f}B | {update_str}")
    else:
        print(f"   No data found")
    
    # Show sample data quality
    print(f"\n📊 SAMPLE DATA QUALITY:")
    sample_query = """
    SELECT ticker, revenue, net_income, ebitda, market_cap, enterprise_value
    FROM company_fundamentals 
    WHERE revenue IS NOT NULL
    ORDER BY market_cap DESC 
    LIMIT 5
    """
    sample_data = db.execute_query(sample_query)
    
    if sample_data:
        print(f"   Ticker | Revenue    | Net Income | EBITDA     | Market Cap")
        print(f"   -------|------------|------------|------------|------------")
        for row in sample_data:
            ticker, revenue, net_income, ebitda, market_cap = row[:5]
            # Convert decimal to float
            def to_float(val):
                try:
                    return float(val) if val is not None else None
                except Exception:
                    return None
            
            revenue_float = to_float(revenue)
            net_income_float = to_float(net_income)
            ebitda_float = to_float(ebitda)
            market_cap_float = to_float(market_cap)
            
            revenue_str = f"${revenue_float/1e9:.1f}B" if revenue_float else "NULL"
            net_income_str = f"${net_income_float/1e9:.1f}B" if net_income_float else "NULL"
            ebitda_str = f"${ebitda_float/1e9:.1f}B" if ebitda_float else "NULL"
            market_cap_str = f"${market_cap_float/1e9:.1f}B" if market_cap_float else "NULL"
            print(f"   {ticker:6} | {revenue_str:10} | {net_income_str:10} | {ebitda_str:10} | {market_cap_str:10}")
    else:
        print(f"   No sample data found")
    
    print(f"\n💡 STATUS:")
    if recent_count > 0:
        print(f"   ✅ Processing is active!")
        print(f"   • {recent_count} companies updated in last 30 minutes")
        print(f"   • Background process is running")
        print(f"   • Large companies are being processed first")
    else:
        print(f"   ⚠️  No recent updates detected")
        print(f"   • Check if background process is still running")
        print(f"   • May need to restart the process")
    
    print(f"\n📄 Next check: Run this script again in a few minutes")

if __name__ == "__main__":
    monitor_fundamentals_fixed() 