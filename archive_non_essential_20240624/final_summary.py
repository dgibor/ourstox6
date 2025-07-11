#!/usr/bin/env python3
"""
Final summary of batch processing results
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def final_summary():
    """Show final summary of batch processing results"""
    
    print("🎉 FINAL BATCH PROCESSING SUMMARY")
    print("=" * 60)
    
    db = DatabaseManager()
    
    # Get comprehensive statistics
    total_query = "SELECT COUNT(*) FROM stocks"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Get stocks with fundamentals data
    fundamentals_query = """
    SELECT COUNT(*) FROM stocks 
    WHERE revenue_ttm IS NOT NULL OR net_income_ttm IS NOT NULL
    """
    fundamentals_result = db.fetch_one(fundamentals_query)
    fundamentals_count = fundamentals_result[0] if fundamentals_result else 0
    
    # Get stocks with complete data
    complete_query = """
    SELECT COUNT(*) FROM stocks 
    WHERE revenue_ttm IS NOT NULL 
    AND net_income_ttm IS NOT NULL 
    AND market_cap IS NOT NULL
    """
    complete_result = db.fetch_one(complete_query)
    complete_count = complete_result[0] if complete_result else 0
    
    # Get recently updated stocks
    recent_query = """
    SELECT COUNT(*) FROM stocks 
    WHERE fundamentals_last_update > NOW() - INTERVAL '2 hours'
    """
    recent_result = db.fetch_one(recent_query)
    recent_count = recent_result[0] if recent_result else 0
    
    print(f"📊 COMPREHENSIVE STATISTICS:")
    print(f"   Total stocks in database: {total_stocks}")
    print(f"   With fundamentals data: {fundamentals_count} ({(fundamentals_count/total_stocks*100):.1f}%)")
    print(f"   With complete data: {complete_count} ({(complete_count/total_stocks*100):.1f}%)")
    print(f"   Updated in last 2 hours: {recent_count} ({(recent_count/total_stocks*100):.1f}%)")
    
    # Show data quality metrics
    print(f"\n📈 DATA QUALITY METRICS:")
    
    # Revenue coverage
    revenue_query = "SELECT COUNT(*) FROM stocks WHERE revenue_ttm IS NOT NULL"
    revenue_result = db.fetch_one(revenue_query)
    revenue_count = revenue_result[0] if revenue_result else 0
    print(f"   Revenue data: {revenue_count}/{total_stocks} ({(revenue_count/total_stocks*100):.1f}%)")
    
    # Net income coverage
    net_income_query = "SELECT COUNT(*) FROM stocks WHERE net_income_ttm IS NOT NULL"
    net_income_result = db.fetch_one(net_income_query)
    net_income_count = net_income_result[0] if net_income_result else 0
    print(f"   Net income data: {net_income_count}/{total_stocks} ({(net_income_count/total_stocks*100):.1f}%)")
    
    # Market cap coverage
    market_cap_query = "SELECT COUNT(*) FROM stocks WHERE market_cap IS NOT NULL"
    market_cap_result = db.fetch_one(market_cap_query)
    market_cap_count = market_cap_result[0] if market_cap_result else 0
    print(f"   Market cap data: {market_cap_count}/{total_stocks} ({(market_cap_count/total_stocks*100):.1f}%)")
    
    # Enterprise value coverage
    ev_query = "SELECT COUNT(*) FROM stocks WHERE enterprise_value IS NOT NULL"
    ev_result = db.fetch_one(ev_query)
    ev_count = ev_result[0] if ev_result else 0
    print(f"   Enterprise value data: {ev_count}/{total_stocks} ({(ev_count/total_stocks*100):.1f}%)")
    
    # Show sample of successfully processed stocks
    print(f"\n✅ SAMPLE SUCCESSFULLY PROCESSED STOCKS:")
    sample_query = """
    SELECT ticker, revenue_ttm, net_income_ttm, market_cap, fundamentals_last_update
    FROM stocks 
    WHERE revenue_ttm IS NOT NULL AND net_income_ttm IS NOT NULL
    ORDER BY fundamentals_last_update DESC 
    LIMIT 10
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
    
    # Show stocks without data
    print(f"\n⚠️  STOCKS WITHOUT FUNDAMENTALS DATA:")
    missing_query = """
    SELECT ticker FROM stocks 
    WHERE revenue_ttm IS NULL AND net_income_ttm IS NULL
    ORDER BY ticker
    LIMIT 10
    """
    missing_data = db.execute_query(missing_query)
    
    if missing_data:
        missing_tickers = [row[0] for row in missing_data]
        print(f"   {', '.join(missing_tickers)}")
        if len(missing_data) == 10:
            print(f"   ... and more (showing first 10)")
    else:
        print(f"   All stocks have fundamentals data! 🎉")
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    coverage_rate = fundamentals_count / total_stocks * 100
    if coverage_rate >= 95:
        print(f"   🎉 EXCELLENT! {coverage_rate:.1f}% coverage achieved")
        print(f"   ✅ System is working perfectly")
        print(f"   ✅ Data quality is high")
    elif coverage_rate >= 80:
        print(f"   ✅ GOOD! {coverage_rate:.1f}% coverage achieved")
        print(f"   ⚠️  Some stocks may need manual attention")
    else:
        print(f"   ⚠️  NEEDS ATTENTION! Only {coverage_rate:.1f}% coverage")
        print(f"   🔧 Check logs for errors and retry if needed")
    
    print(f"\n📄 Next steps:")
    print(f"   • Check log files for any errors")
    print(f"   • Verify data quality with sample stocks")
    print(f"   • Run ratio calculations if needed")
    print(f"   • System is ready for production use! 🚀")

if __name__ == "__main__":
    final_summary() 