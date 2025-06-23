#!/usr/bin/env python3
"""
Debug why fundamental data storage is failing
"""

from service_factory import ServiceFactory
from database import DatabaseManager
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_storage_issue(ticker='GME'):
    print(f"Debugging storage issue for {ticker}")
    print("=" * 50)
    
    # Check current state
    db = DatabaseManager()
    db.connect()
    
    print(f"\n1. Current state for {ticker}:")
    print("-" * 30)
    
    # Check stocks table
    stocks_query = "SELECT ticker, market_cap, revenue_ttm, net_income_ttm FROM stocks WHERE ticker = %s"
    stocks_result = db.execute_query(stocks_query, (ticker,))
    if stocks_result:
        print(f"Stocks table: {stocks_result[0]}")
    else:
        print(f"Ticker {ticker} not found in stocks table")
    
    # Check company_fundamentals table
    cf_query = "SELECT ticker, report_date, period_type FROM company_fundamentals WHERE ticker = %s"
    cf_result = db.execute_query(cf_query, (ticker,))
    if cf_result:
        print(f"Company_fundamentals table: {cf_result}")
    else:
        print(f"No records in company_fundamentals for {ticker}")
    
    db.disconnect()
    
    # Try to fetch and store data
    print(f"\n2. Fetching and storing data for {ticker}:")
    print("-" * 30)
    
    factory = ServiceFactory()
    fundamental_service = factory.get_fundamental_service()
    
    try:
        # Get data
        print("Fetching fundamental data...")
        data = fundamental_service.get_fundamental_data(ticker)
        
        if data:
            print(f"✅ Data fetched from {data['provider']}")
            print(f"Data structure: {list(data['data'].keys())}")
            
            # Try to store
            print("Attempting to store data...")
            success = fundamental_service.store_fundamental_data(ticker, data['data'])
            print(f"Storage result: {success}")
            
            if success:
                print("✅ Data stored successfully")
            else:
                print("❌ Data storage failed")
        else:
            print("❌ No data fetched")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check state after storage attempt
    print(f"\n3. State after storage attempt:")
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
    debug_storage_issue('GME') 