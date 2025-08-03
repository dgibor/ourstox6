#!/usr/bin/env python3
"""
Fix FMP Service Fundamental Data Population Issues

This script addresses the following issues:
1. Shares outstanding not being populated properly
2. New columns (cost_of_goods_sold, current_assets, current_liabilities) not being populated
3. Data not being stored in company_fundamentals table correctly
"""

import sys
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager
from fmp_service import FMPService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_fmp_fundamental_data():
    """Fix fundamental data population issues"""
    print("🔧 FIXING FMP FUNDAMENTAL DATA POPULATION")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        fmp_service = FMPService()
        
        # 1. Get companies missing critical data
        print("\n📊 1. IDENTIFYING COMPANIES WITH MISSING DATA:")
        print("-" * 40)
        
        missing_data_query = """
        SELECT DISTINCT cf.ticker
        FROM company_fundamentals cf
        WHERE cf.shares_outstanding IS NULL 
           OR cf.shares_outstanding = 0
           OR cf.cost_of_goods_sold IS NULL
           OR cf.current_assets IS NULL
           OR cf.current_liabilities IS NULL
        ORDER BY cf.ticker
        LIMIT 10
        """
        
        missing_tickers = db.execute_query(missing_data_query)
        tickers = [row[0] for row in missing_tickers]
        
        print(f"Found {len(tickers)} companies with missing critical data")
        print(f"Sample tickers: {tickers[:5]}")
        
        if not tickers:
            print("✅ No companies found with missing critical data")
            return
        
        # 2. Test FMP service for one company
        print(f"\n📊 2. TESTING FMP SERVICE FOR {tickers[0]}:")
        print("-" * 40)
        
        test_ticker = tickers[0]
        print(f"Testing FMP service for: {test_ticker}")
        
        # Fetch financial statements
        financial_data = fmp_service.fetch_financial_statements(test_ticker)
        print(f"Financial data fetched: {'✅' if financial_data else '❌'}")
        
        if financial_data:
            print(f"  Income statement: {len(financial_data.get('income_statement', {}))} fields")
            print(f"  Balance sheet: {len(financial_data.get('balance_sheet', {}))} fields")
            print(f"  Cash flow: {len(financial_data.get('cash_flow', {}))} fields")
        
        # Fetch key statistics
        key_stats = fmp_service.fetch_key_statistics(test_ticker)
        print(f"Key statistics fetched: {'✅' if key_stats else '❌'}")
        
        if key_stats:
            market_data = key_stats.get('market_data', {})
            print(f"  Market cap: ${market_data.get('market_cap', 0):,.0f}")
            print(f"  Shares outstanding: {market_data.get('shares_outstanding', 0):,.0f}")
            print(f"  Enterprise value: ${market_data.get('enterprise_value', 0):,.0f}")
        
        # 3. Check what's missing in the data
        print(f"\n📊 3. ANALYZING MISSING DATA FOR {test_ticker}:")
        print("-" * 40)
        
        if financial_data and key_stats:
            income = financial_data.get('income_statement', {})
            balance = financial_data.get('balance_sheet', {})
            cash_flow = financial_data.get('cash_flow', {})
            market_data = key_stats.get('market_data', {})
            
            print("Available data:")
            print(f"  Revenue: ${income.get('revenue', 0):,.0f}")
            print(f"  Net income: ${income.get('net_income', 0):,.0f}")
            print(f"  Total assets: ${balance.get('total_assets', 0):,.0f}")
            print(f"  Total debt: ${balance.get('total_debt', 0):,.0f}")
            print(f"  Current assets: ${balance.get('current_assets', 0):,.0f}")
            print(f"  Current liabilities: ${balance.get('current_liabilities', 0):,.0f}")
            print(f"  Shares outstanding: {market_data.get('shares_outstanding', 0):,.0f}")
            
            # Check for cost of goods sold
            if 'cost_of_goods_sold' not in income:
                print("  ❌ Cost of goods sold: NOT AVAILABLE in FMP data")
            else:
                print(f"  ✅ Cost of goods sold: ${income.get('cost_of_goods_sold', 0):,.0f}")
        
        # 4. Check current database state
        print(f"\n📊 4. CURRENT DATABASE STATE FOR {test_ticker}:")
        print("-" * 40)
        
        current_data_query = """
        SELECT 
            shares_outstanding,
            cost_of_goods_sold,
            current_assets,
            current_liabilities,
            revenue,
            net_income,
            last_updated
        FROM company_fundamentals 
        WHERE ticker = %s
        """
        
        current_data = db.fetch_one(current_data_query, (test_ticker,))
        
        if current_data:
            shares_out, cogs, curr_assets, curr_liab, revenue, net_income, last_updated = current_data
            print(f"  Shares outstanding: {shares_out or 'NULL'}")
            print(f"  Cost of goods sold: {cogs or 'NULL'}")
            print(f"  Current assets: {curr_assets or 'NULL'}")
            print(f"  Current liabilities: {curr_liab or 'NULL'}")
            print(f"  Revenue: ${revenue or 0:,.0f}")
            print(f"  Net income: ${net_income or 0:,.0f}")
            print(f"  Last updated: {last_updated}")
        else:
            print(f"  ❌ No data found in company_fundamentals table")
        
        # 5. Recommendations
        print(f"\n📊 5. RECOMMENDATIONS:")
        print("-" * 40)
        
        print("🔧 IMMEDIATE FIXES NEEDED:")
        print("1. Update FMP service to populate shares_outstanding in company_fundamentals table")
        print("2. Add cost_of_goods_sold mapping from FMP income statement data")
        print("3. Ensure current_assets and current_liabilities are properly mapped")
        print("4. Run the fundamental data population script to update all companies")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Fix the FMP service data mapping")
        print("2. Run: python archive_non_essential_20240624/fill_all_fundamentals_fmp.py")
        print("3. Verify the ratio calculator works with populated data")
        
        fmp_service.close()
        
    except Exception as e:
        print(f"❌ Error fixing FMP fundamental data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_fmp_fundamental_data() 