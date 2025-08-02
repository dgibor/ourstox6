#!/usr/bin/env python3
"""
Debug Fundamental Data Query Issues
"""

import sys
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager

def debug_fundamental_data():
    """Debug why fundamental data isn't being found"""
    print("🔍 DEBUGGING FUNDAMENTAL DATA QUERIES")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # 1. Check if fundamental data exists
        print("\n📊 1. CHECKING FUNDAMENTAL DATA EXISTS")
        print("-" * 40)
        
        count_query = "SELECT COUNT(*) FROM company_fundamentals"
        count = db.fetch_one(count_query)
        print(f"Total fundamental records: {count[0]}")
        
        # 2. Check the query that's failing
        print("\n📊 2. TESTING THE FAILING QUERY")
        print("-" * 40)
        
        # This is the query from calculate_fundamental_ratios.py
        test_query = """
        SELECT 
            cf.*,
            s.shares_outstanding,
            (SELECT close FROM daily_charts WHERE ticker = cf.ticker ORDER BY date DESC LIMIT 1) as current_price
        FROM company_fundamentals cf
        JOIN stocks s ON cf.ticker = s.ticker
        WHERE cf.ticker = 'AAPL'
        AND cf.period_type = 'annual'
        ORDER BY cf.report_date DESC
        LIMIT 1
        """
        
        print("Testing query for AAPL:")
        print(test_query)
        
        try:
            result = db.fetch_all_dict(test_query)
            print(f"Query result: {len(result)} rows")
            if result:
                print(f"Found data for AAPL: {result[0]}")
            else:
                print("No data found for AAPL")
        except Exception as e:
            print(f"Query failed: {e}")
        
        # 3. Check what period_type values exist
        print("\n📊 3. CHECKING PERIOD_TYPE VALUES")
        print("-" * 40)
        
        period_query = """
        SELECT period_type, COUNT(*) as count
        FROM company_fundamentals
        GROUP BY period_type
        ORDER BY count DESC
        """
        
        periods = db.execute_query(period_query)
        print("Period types in database:")
        for period_type, count in periods:
            print(f"  {period_type}: {count} records")
        
        # 4. Check AAPL specifically
        print("\n📊 4. CHECKING AAPL DATA")
        print("-" * 40)
        
        aapl_query = """
        SELECT ticker, period_type, report_date, revenue, net_income
        FROM company_fundamentals
        WHERE ticker = 'AAPL'
        ORDER BY report_date DESC
        LIMIT 5
        """
        
        aapl_data = db.execute_query(aapl_query)
        print("AAPL fundamental data:")
        for row in aapl_data:
            ticker, period_type, report_date, revenue, net_income = row
            print(f"  {ticker} | {period_type} | {report_date} | Revenue: {revenue} | Net Income: {net_income}")
        
        # 5. Check if AAPL exists in stocks table
        print("\n📊 5. CHECKING AAPL IN STOCKS TABLE")
        print("-" * 40)
        
        stocks_query = """
        SELECT ticker, company_name, shares_outstanding
        FROM stocks
        WHERE ticker = 'AAPL'
        """
        
        stocks_data = db.fetch_one(stocks_query)
        if stocks_data:
            ticker, company_name, shares_outstanding = stocks_data
            print(f"AAPL in stocks: {ticker} | {company_name} | Shares: {shares_outstanding}")
        else:
            print("AAPL not found in stocks table")
        
        # 6. Check if AAPL has price data
        print("\n📊 6. CHECKING AAPL PRICE DATA")
        print("-" * 40)
        
        price_query = """
        SELECT ticker, date, close
        FROM daily_charts
        WHERE ticker = 'AAPL'
        ORDER BY date DESC
        LIMIT 3
        """
        
        price_data = db.execute_query(price_query)
        print("AAPL recent price data:")
        for row in price_data:
            ticker, date, close = row
            print(f"  {ticker} | {date} | Close: {close}")
        
        # 7. Test the corrected query
        print("\n📊 7. TESTING CORRECTED QUERY")
        print("-" * 40)
        
        # Try with 'ttm' instead of 'annual'
        corrected_query = """
        SELECT 
            cf.*,
            s.shares_outstanding,
            (SELECT close FROM daily_charts WHERE ticker = cf.ticker ORDER BY date DESC LIMIT 1) as current_price
        FROM company_fundamentals cf
        JOIN stocks s ON cf.ticker = s.ticker
        WHERE cf.ticker = 'AAPL'
        AND cf.period_type = 'ttm'
        ORDER BY cf.report_date DESC
        LIMIT 1
        """
        
        try:
            result = db.fetch_all_dict(corrected_query)
            print(f"Corrected query result: {len(result)} rows")
            if result:
                print(f"Found data for AAPL with 'ttm': {result[0]}")
            else:
                print("No data found for AAPL with 'ttm'")
        except Exception as e:
            print(f"Corrected query failed: {e}")
        
    except Exception as e:
        print(f"❌ Error debugging: {e}")

if __name__ == "__main__":
    debug_fundamental_data() 