#!/usr/bin/env python3
"""
Monitor the progress of filling all company fundamentals (Fixed)
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def monitor_fill_progress():
    """Monitor the progress of filling all company fundamentals"""
    
    print("📊 MONITORING FILL ALL COMPANY FUNDAMENTALS PROGRESS (FIXED)")
    print("=" * 70)
    
    db = DatabaseManager()
    
    # Get total stocks
    total_query = "SELECT COUNT(*) FROM stocks"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Get stocks with complete fundamentals
    complete_query = """
    SELECT COUNT(DISTINCT ticker) FROM company_fundamentals 
    WHERE revenue IS NOT NULL 
    AND net_income IS NOT NULL 
    AND shares_outstanding IS NOT NULL
    """
    complete_result = db.fetch_one(complete_query)
    complete_fundamentals = complete_result[0] if complete_result else 0
    
    # Get stocks with any fundamentals
    any_query = "SELECT COUNT(DISTINCT ticker) FROM company_fundamentals"
    any_result = db.fetch_one(any_query)
    any_fundamentals = any_result[0] if any_result else 0
    
    # Get recently updated (last hour)
    recent_query = """
    SELECT COUNT(DISTINCT ticker) FROM company_fundamentals 
    WHERE last_updated > NOW() - INTERVAL '1 hour'
    """
    recent_result = db.fetch_one(recent_query)
    recent_updates = recent_result[0] if recent_result else 0
    
    print(f"📈 PROGRESS SUMMARY:")
    print(f"   Total stocks: {total_stocks}")
    print(f"   With complete fundamentals: {complete_fundamentals} ({(complete_fundamentals/total_stocks*100):.1f}%)")
    print(f"   With any fundamentals: {any_fundamentals} ({(any_fundamentals/total_stocks*100):.1f}%)")
    print(f"   Updated in last hour: {recent_updates}")
    print(f"   Remaining: {total_stocks - complete_fundamentals}")
    
    # Show recent updates
    print(f"\n🕐 RECENT UPDATES (last 20):")
    recent_updates_query = """
    SELECT ticker, last_updated 
    FROM company_fundamentals 
    ORDER BY last_updated DESC 
    LIMIT 20
    """
    recent_updates_list = db.execute_query(recent_updates_query)
    
    if recent_updates_list:
        for ticker, update_time in recent_updates_list:
            print(f"   {ticker}: {update_time}")
    else:
        print(f"   No recent updates found")
    
    # Show sample complete data
    print(f"\n📊 SAMPLE COMPLETE DATA:")
    sample_query = """
    SELECT ticker, revenue, net_income, shares_outstanding, last_updated
    FROM company_fundamentals 
    WHERE revenue IS NOT NULL 
    AND net_income IS NOT NULL 
    AND shares_outstanding IS NOT NULL
    ORDER BY revenue DESC 
    LIMIT 10
    """
    sample_data = db.execute_query(sample_query)
    
    if sample_data:
        print(f"   Ticker | Revenue    | Net Income | Shares Out | Last Update")
        print(f"   -------|------------|------------|------------|-------------")
        for row in sample_data:
            ticker, revenue, net_income, shares_outstanding, last_update = row
            # Convert decimal to float
            def to_float(val):
                try:
                    return float(val) if val is not None else None
                except Exception:
                    return None
            
            revenue_float = to_float(revenue)
            net_income_float = to_float(net_income)
            shares_float = to_float(shares_outstanding)
            
            revenue_str = f"${revenue_float/1e9:.1f}B" if revenue_float else "NULL"
            net_income_str = f"${net_income_float/1e9:.1f}B" if net_income_float else "NULL"
            shares_str = f"{shares_float/1e6:.1f}M" if shares_float else "NULL"
            update_str = last_update.strftime('%H:%M:%S') if last_update else "NULL"
            print(f"   {ticker:6} | {revenue_str:10} | {net_income_str:10} | {shares_str:10} | {update_str}")
    else:
        print(f"   No complete data found")
    
    # Show stocks still needing processing
    print(f"\n⚠️  STOCKS STILL NEEDING PROCESSING:")
    missing_query = """
    SELECT s.ticker 
    FROM stocks s
    LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
    WHERE cf.ticker IS NULL 
       OR cf.revenue IS NULL 
       OR cf.net_income IS NULL 
       OR cf.shares_outstanding IS NULL
    ORDER BY s.market_cap DESC NULLS LAST
    LIMIT 10
    """
    missing_data = db.execute_query(missing_query)
    
    if missing_data:
        missing_tickers = [row[0] for row in missing_data]
        print(f"   {', '.join(missing_tickers)}")
        if len(missing_data) == 10:
            print(f"   ... and more (showing first 10)")
    else:
        print(f"   All stocks have complete data! 🎉")
    
    # Show data quality stats
    print(f"\n📊 DATA QUALITY STATS:")
    quality_query = """
    SELECT 
        COUNT(DISTINCT ticker) as total_tickers,
        COUNT(DISTINCT CASE WHEN revenue IS NOT NULL THEN ticker END) as with_revenue,
        COUNT(DISTINCT CASE WHEN net_income IS NOT NULL THEN ticker END) as with_net_income,
        COUNT(DISTINCT CASE WHEN ebitda IS NOT NULL THEN ticker END) as with_ebitda,
        COUNT(DISTINCT CASE WHEN shares_outstanding IS NOT NULL THEN ticker END) as with_shares,
        COUNT(DISTINCT CASE WHEN total_debt IS NOT NULL THEN ticker END) as with_debt
    FROM company_fundamentals
    """
    quality_result = db.fetch_one(quality_query)
    
    if quality_result:
        total_tickers, with_revenue, with_net_income, with_ebitda, with_shares, with_debt = quality_result
        print(f"   Total tickers in fundamentals: {total_tickers}")
        print(f"   With revenue: {with_revenue} ({(with_revenue/total_tickers*100):.1f}%)" if total_tickers > 0 else "   With revenue: 0")
        print(f"   With net income: {with_net_income} ({(with_net_income/total_tickers*100):.1f}%)" if total_tickers > 0 else "   With net income: 0")
        print(f"   With EBITDA: {with_ebitda} ({(with_ebitda/total_tickers*100):.1f}%)" if total_tickers > 0 else "   With EBITDA: 0")
        print(f"   With shares outstanding: {with_shares} ({(with_shares/total_tickers*100):.1f}%)" if total_tickers > 0 else "   With shares outstanding: 0")
        print(f"   With total debt: {with_debt} ({(with_debt/total_tickers*100):.1f}%)" if total_tickers > 0 else "   With total debt: 0")
    
    print(f"\n💡 STATUS:")
    coverage_rate = complete_fundamentals / total_stocks * 100
    if coverage_rate >= 95:
        print(f"   🎉 EXCELLENT! {coverage_rate:.1f}% coverage achieved")
        print(f"   ✅ Almost all stocks have complete data")
    elif coverage_rate >= 80:
        print(f"   ✅ GOOD! {coverage_rate:.1f}% coverage achieved")
        print(f"   ⚠️  Some stocks still need processing")
    elif coverage_rate >= 50:
        print(f"   ⚠️  MODERATE! {coverage_rate:.1f}% coverage achieved")
        print(f"   🔧 Many stocks still need processing")
    else:
        print(f"   🔧 NEEDS WORK! Only {coverage_rate:.1f}% coverage")
        print(f"   📈 Background process is running")
    
    if recent_updates > 0:
        print(f"   ✅ Background process is active ({recent_updates} updates in last hour)")
    else:
        print(f"   ⚠️  No recent updates - check if process is running")
    
    print(f"\n📄 Next check: Run this script again in a few minutes")

if __name__ == "__main__":
    monitor_fill_progress() 