#!/usr/bin/env python3
"""
Check the current status of fundamental data in the database
"""

import sys
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager

def check_fundamental_data_status():
    """Check the current status of fundamental data"""
    print("🔍 CHECKING FUNDAMENTAL DATA STATUS")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # 1. Check company_fundamentals table
        print("\n📊 1. COMPANY_FUNDAMENTALS TABLE STATUS:")
        print("-" * 40)
        
        # Count total records
        count_query = "SELECT COUNT(*) FROM company_fundamentals"
        total_count = db.fetch_one(count_query)
        print(f"Total records: {total_count[0]}")
        
        # Check recent updates
        recent_query = """
        SELECT COUNT(*) 
        FROM company_fundamentals 
        WHERE last_updated >= CURRENT_DATE - INTERVAL '7 days'
        """
        recent_count = db.fetch_one(recent_query)
        print(f"Updated in last 7 days: {recent_count[0]}")
        
        # Check data quality for a few sample companies
        sample_query = """
        SELECT ticker, revenue, net_income, total_assets, total_debt, shares_outstanding, last_updated
        FROM company_fundamentals 
        ORDER BY last_updated DESC 
        LIMIT 5
        """
        sample_data = db.execute_query(sample_query)
        
        print(f"\n📋 Sample data (last 5 updated):")
        for row in sample_data:
            ticker, revenue, net_income, total_assets, total_debt, shares_outstanding, last_updated = row
            filled_fields = sum(1 for val in [revenue, net_income, total_assets, total_debt, shares_outstanding] if val is not None)
            print(f"  {ticker}: {filled_fields}/5 fields filled, last updated: {last_updated}")
        
        # 2. Check stocks table fundamental columns
        print("\n📊 2. STOCKS TABLE FUNDAMENTAL COLUMNS:")
        print("-" * 40)
        
        stocks_query = """
        SELECT 
            COUNT(*) as total_stocks,
            COUNT(CASE WHEN market_cap IS NOT NULL THEN 1 END) as market_cap_filled,
            COUNT(CASE WHEN shares_outstanding IS NOT NULL AND shares_outstanding > 0 THEN 1 END) as shares_filled,
            COUNT(CASE WHEN revenue_ttm IS NOT NULL THEN 1 END) as revenue_filled,
            COUNT(CASE WHEN net_income_ttm IS NOT NULL THEN 1 END) as net_income_filled,
            COUNT(CASE WHEN fundamentals_last_update IS NOT NULL THEN 1 END) as fundamentals_updated
        FROM stocks
        """
        stocks_data = db.fetch_one(stocks_query)
        
        total_stocks, market_cap_filled, shares_filled, revenue_filled, net_income_filled, fundamentals_updated = stocks_data
        
        print(f"Total stocks: {total_stocks}")
        print(f"Market cap filled: {market_cap_filled} ({market_cap_filled/total_stocks*100:.1f}%)")
        print(f"Shares outstanding filled: {shares_filled} ({shares_filled/total_stocks*100:.1f}%)")
        print(f"Revenue TTM filled: {revenue_filled} ({revenue_filled/total_stocks*100:.1f}%)")
        print(f"Net income TTM filled: {net_income_filled} ({net_income_filled/total_stocks*100:.1f}%)")
        print(f"Fundamentals updated: {fundamentals_updated} ({fundamentals_updated/total_stocks*100:.1f}%)")
        
        # 3. Check for the new columns we added
        print("\n📊 3. NEW COLUMNS STATUS:")
        print("-" * 40)
        
        new_columns_query = """
        SELECT 
            COUNT(CASE WHEN cost_of_goods_sold IS NOT NULL THEN 1 END) as cogs_filled,
            COUNT(CASE WHEN current_assets IS NOT NULL THEN 1 END) as current_assets_filled,
            COUNT(CASE WHEN current_liabilities IS NOT NULL THEN 1 END) as current_liabilities_filled
        FROM company_fundamentals
        """
        new_columns_data = db.fetch_one(new_columns_query)
        
        cogs_filled, current_assets_filled, current_liabilities_filled = new_columns_data
        
        print(f"Cost of goods sold filled: {cogs_filled} ({cogs_filled/total_count[0]*100:.1f}%)")
        print(f"Current assets filled: {current_assets_filled} ({current_assets_filled/total_count[0]*100:.1f}%)")
        print(f"Current liabilities filled: {current_liabilities_filled} ({current_liabilities_filled/total_count[0]*100:.1f}%)")
        
        # 4. Check when fundamentals were last updated
        print("\n📊 4. LAST UPDATE TIMES:")
        print("-" * 40)
        
        last_update_query = """
        SELECT 
            MIN(last_updated) as earliest_update,
            MAX(last_updated) as latest_update,
            COUNT(CASE WHEN last_updated >= CURRENT_DATE - INTERVAL '1 day' THEN 1 END) as updated_today,
            COUNT(CASE WHEN last_updated >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as updated_this_week
        FROM company_fundamentals
        WHERE last_updated IS NOT NULL
        """
        last_update_data = db.fetch_one(last_update_query)
        
        earliest, latest, updated_today, updated_this_week = last_update_data
        
        print(f"Earliest update: {earliest}")
        print(f"Latest update: {latest}")
        print(f"Updated today: {updated_today}")
        print(f"Updated this week: {updated_this_week}")
        
        # 5. Recommendations
        print("\n📊 5. RECOMMENDATIONS:")
        print("-" * 40)
        
        if total_count[0] == 0:
            print("❌ CRITICAL: No fundamental data found in company_fundamentals table")
            print("   → Run the FMP fundamental data population script")
        elif recent_count[0] == 0:
            print("⚠️  WARNING: No fundamental data updated in the last 7 days")
            print("   → Consider running the FMP fundamental data population script")
        else:
            print("✅ Fundamental data appears to be up to date")
        
        if shares_filled == 0:
            print("❌ CRITICAL: No shares outstanding data found")
            print("   → This will prevent market cap and ratio calculations")
        
        if cogs_filled == 0:
            print("⚠️  WARNING: No cost of goods sold data found")
            print("   → This will prevent gross margin calculations")
        
        if current_assets_filled == 0:
            print("⚠️  WARNING: No current assets data found")
            print("   → This will prevent current ratio calculations")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error checking fundamental data status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_fundamental_data_status() 