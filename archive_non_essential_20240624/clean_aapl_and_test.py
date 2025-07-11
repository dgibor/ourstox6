#!/usr/bin/env python3
"""
Clean AAPL data and test fundamental pipeline
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService
from config import Config

def clean_aapl_and_test():
    """Clean existing AAPL data and test the pipeline"""
    print("🧹 Cleaning AAPL data and testing pipeline")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Clean existing AAPL data
    print("1️⃣ Cleaning existing AAPL data...")
    try:
        delete_query = "DELETE FROM company_fundamentals WHERE ticker = 'AAPL'"
        affected_rows = db.execute_update(delete_query)
        print(f"✅ Deleted {affected_rows} existing AAPL records")
    except Exception as e:
        print(f"❌ Error cleaning AAPL data: {e}")
        return False
    
    # Test the pipeline
    print("\n2️⃣ Testing fundamental data pipeline...")
    config = Config()
    fmp = FMPService()
    
    ticker = "AAPL"
    
    try:
        print(f"📊 Processing {ticker}...")
        
        # Fetch fundamental data
        print(f"\n3️⃣ Fetching fundamental data for {ticker}...")
        fundamental_data = fmp.get_fundamental_data(ticker)
        
        if not fundamental_data:
            print(f"❌ No fundamental data found for {ticker}")
            return False
        
        print(f"✅ Fundamental data fetched: {len(fundamental_data)} records")
        
        # Fetch key statistics
        print(f"\n4️⃣ Fetching key statistics for {ticker}...")
        key_stats = fmp.fetch_key_statistics(ticker)
        
        if not key_stats:
            print(f"❌ No key statistics found for {ticker}")
            return False
        
        print(f"✅ Key statistics fetched: {len(key_stats)} records")
        
        # Store data
        print(f"\n5️⃣ Storing data for {ticker}...")
        success = fmp.store_fundamental_data(ticker, fundamental_data, key_stats)
        
        if not success:
            print(f"❌ Failed to store data for {ticker}")
            return False
        
        print(f"✅ Data stored successfully")
        
        # Verify data
        print(f"\n6️⃣ Verifying stored data...")
        verify_query = """
        SELECT 
            revenue, gross_profit, operating_income, net_income, ebitda,
            eps_diluted, book_value_per_share,
            total_assets, total_debt, total_equity, cash_and_equivalents,
            operating_cash_flow, free_cash_flow, capex,
            shares_outstanding, shares_float,
            price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda,
            return_on_equity, return_on_assets, debt_to_equity_ratio, current_ratio,
            gross_margin, operating_margin, net_margin,
            data_source, last_updated
        FROM company_fundamentals 
        WHERE ticker = 'AAPL'
        ORDER BY last_updated DESC
        LIMIT 1
        """
        
        result = db.fetch_one(verify_query)
        
        if not result:
            print(f"❌ No data found after storage")
            return False
        
        print(f"✅ Data verification - Found record with:")
        print(f"  Revenue: ${result[0]:,.0f}" if result[0] else "  Revenue: NULL")
        print(f"  Net Income: ${result[3]:,.0f}" if result[3] else "  Net Income: NULL")
        print(f"  Total Assets: ${result[7]:,.0f}" if result[7] else "  Total Assets: NULL")
        print(f"  Total Debt: ${result[8]:,.0f}" if result[8] else "  Total Debt: NULL")
        print(f"  Total Equity: ${result[9]:,.0f}" if result[9] else "  Total Equity: NULL")
        print(f"  Shares Outstanding: {result[14]:,.0f}" if result[14] else "  Shares Outstanding: NULL")
        print(f"  EPS: {result[5]}" if result[5] else "  EPS: NULL")
        print(f"  Book Value Per Share: {result[6]}" if result[6] else "  Book Value Per Share: NULL")
        print(f"  PE Ratio: {result[15]}" if result[15] else "  PE Ratio: NULL")
        print(f"  ROE: {result[20]}" if result[20] else "  ROE: NULL")
        print(f"  Data Source: {result[26]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        return False

if __name__ == "__main__":
    success = clean_aapl_and_test()
    if success:
        print(f"\n🎉 AAPL fundamental data pipeline test completed successfully!")
    else:
        print(f"\n❌ AAPL fundamental data pipeline test failed!") 