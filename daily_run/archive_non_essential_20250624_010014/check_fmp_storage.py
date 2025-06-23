#!/usr/bin/env python3
"""
Test FMP storage directly and check database
"""

from fmp_service import FMPService
from database import DatabaseManager
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_fmp_storage(ticker='AMC'):
    print(f"Testing FMP storage for {ticker}")
    print("=" * 50)
    
    # Check initial state
    db = DatabaseManager()
    db.connect()
    
    print(f"\n1. Initial database state:")
    print("-" * 30)
    
    stocks_query = "SELECT ticker, market_cap, revenue_ttm, net_income_ttm FROM stocks WHERE ticker = %s"
    stocks_result = db.execute_query(stocks_query, (ticker,))
    if stocks_result:
        print(f"Stocks table: {stocks_result[0]}")
    else:
        print(f"Ticker {ticker} not found in stocks table")
    
    cf_query = "SELECT ticker, revenue, net_income FROM company_fundamentals WHERE ticker = %s"
    cf_result = db.execute_query(cf_query, (ticker,))
    if cf_result:
        print(f"Company_fundamentals table: {cf_result}")
    else:
        print(f"No records in company_fundamentals for {ticker}")
    
    db.disconnect()
    
    # Test FMP service directly
    print(f"\n2. Testing FMP service:")
    print("-" * 30)
    
    fmp_service = FMPService()
    
    try:
        # Get and store data
        print("Fetching and storing FMP data...")
        result = fmp_service.get_fundamental_data(ticker)
        
        if result:
            print(f"✅ FMP data fetched successfully")
            print(f"Financial data keys: {list(result.get('financial_data', {}).keys())}")
            print(f"Key stats keys: {list(result.get('key_stats', {}).keys())}")
        else:
            print("❌ No FMP data fetched")
            
    except Exception as e:
        print(f"❌ FMP error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fmp_service.close()
    
    # Check final state
    print(f"\n3. Final database state:")
    print("-" * 30)
    
    db = DatabaseManager()
    db.connect()
    
    stocks_result = db.execute_query(stocks_query, (ticker,))
    if stocks_result:
        print(f"Stocks table: {stocks_result[0]}")
    else:
        print(f"Ticker {ticker} not found in stocks table")
    
    cf_result = db.execute_query(cf_query, (ticker,))
    if cf_result:
        print(f"Company_fundamentals table: {cf_result}")
    else:
        print(f"No records in company_fundamentals for {ticker}")
    
    db.disconnect()

if __name__ == "__main__":
    test_fmp_storage('AMC') 