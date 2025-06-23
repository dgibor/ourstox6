#!/usr/bin/env python3
"""
Debug fundamental data storage with detailed logging
"""

from service_factory import ServiceFactory
from database import DatabaseManager
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_fundamental_storage(ticker='AAPL'):
    print(f"Debugging fundamental storage for {ticker}")
    print("=" * 50)
    
    # Test 1: Check current database state
    print("\n1. Current database state:")
    print("-" * 30)
    
    db = DatabaseManager()
    db.connect()
    
    # Check stocks table
    stocks_query = "SELECT ticker, market_cap, revenue_ttm, net_income_ttm FROM stocks WHERE ticker = %s"
    stocks_result = db.execute_query(stocks_query, (ticker,))
    if stocks_result:
        print(f"Stocks table - {ticker}: {stocks_result[0]}")
    else:
        print(f"Stocks table - {ticker}: No record found")
    
    # Check company_fundamentals table
    cf_query = "SELECT ticker, revenue, net_income FROM company_fundamentals WHERE ticker = %s"
    cf_result = db.execute_query(cf_query, (ticker,))
    if cf_result:
        print(f"Company_fundamentals table - {ticker}: {cf_result[0]}")
    else:
        print(f"Company_fundamentals table - {ticker}: No record found")
    
    db.disconnect()
    
    # Test 2: Try to fetch and store fundamental data
    print(f"\n2. Fetching and storing fundamental data for {ticker}:")
    print("-" * 30)
    
    factory = ServiceFactory()
    fundamental_service = factory.get_fundamental_service()
    
    try:
        # Get data without storing first
        print("Fetching data...")
        data = fundamental_service.get_fundamental_data(ticker)
        
        if data:
            print(f"Data fetched successfully from {data['provider']}")
            print(f"Data keys: {list(data['data'].keys())}")
            
            # Try to store manually
            print("Attempting to store data...")
            success = fundamental_service.store_fundamental_data(ticker, data['data'])
            print(f"Storage result: {success}")
        else:
            print("No data fetched")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check database state after storage
    print(f"\n3. Database state after storage:")
    print("-" * 30)
    
    db = DatabaseManager()
    db.connect()
    
    # Check stocks table again
    stocks_result = db.execute_query(stocks_query, (ticker,))
    if stocks_result:
        print(f"Stocks table - {ticker}: {stocks_result[0]}")
    else:
        print(f"Stocks table - {ticker}: No record found")
    
    # Check company_fundamentals table again
    cf_result = db.execute_query(cf_query, (ticker,))
    if cf_result:
        print(f"Company_fundamentals table - {ticker}: {cf_result[0]}")
    else:
        print(f"Company_fundamentals table - {ticker}: No record found")
    
    db.disconnect()

if __name__ == "__main__":
    debug_fundamental_storage('AAPL') 