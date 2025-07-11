#!/usr/bin/env python3
"""
Test FMP Financial Data Fetching for Top 25 Companies
Debug the financial data fetching process
"""

import os
import requests
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FMP API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

def test_fmp_api_key():
    """Test FMP API key"""
    if not FMP_API_KEY:
        print("❌ FMP_API_KEY not set")
        return False
    
    # Test with a simple API call
    url = f"{FMP_BASE_URL}/profile/AAPL"
    params = {'apikey': FMP_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            print("✅ FMP API key is valid")
            return True
        else:
            print(f"❌ FMP API key test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

def test_financial_data_fetching():
    """Test financial data fetching for top companies"""
    if not test_fmp_api_key():
        return
    
    # Top 5 companies by market cap
    test_tickers = ['NVDA', 'MSFT', 'AAPL', 'AMZN', 'GOOGL']
    
    print(f"\n🔍 Testing Financial Data Fetching for Top 5 Companies")
    print("=" * 60)
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}:")
        
        # Test income statement
        print(f"  - Income Statement:")
        income_url = f"{FMP_BASE_URL}/income-statement/{ticker}"
        params = {'apikey': FMP_API_KEY, 'limit': 4}
        
        try:
            response = requests.get(income_url, params=params, timeout=10)
            if response.status_code == 200:
                income_data = response.json()
                print(f"    ✅ Success - {len(income_data)} records")
                if income_data and len(income_data) > 0:
                    latest = income_data[0]
                    print(f"    📋 Revenue: {latest.get('revenue', 'N/A')}")
                    print(f"    📋 Net Income: {latest.get('netIncome', 'N/A')}")
                    print(f"    📋 Date: {latest.get('date', 'N/A')}")
            else:
                print(f"    ❌ Failed - {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Test balance sheet
        print(f"  - Balance Sheet:")
        balance_url = f"{FMP_BASE_URL}/balance-sheet-statement/{ticker}"
        params = {'apikey': FMP_API_KEY, 'limit': 4}
        
        try:
            response = requests.get(balance_url, params=params, timeout=10)
            if response.status_code == 200:
                balance_data = response.json()
                print(f"    ✅ Success - {len(balance_data)} records")
                if balance_data and len(balance_data) > 0:
                    latest = balance_data[0]
                    print(f"    📋 Total Assets: {latest.get('totalAssets', 'N/A')}")
                    print(f"    📋 Total Equity: {latest.get('totalStockholdersEquity', 'N/A')}")
                    print(f"    📋 Shares Outstanding: {latest.get('totalSharesOutstanding', 'N/A')}")
            else:
                print(f"    ❌ Failed - {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Test cash flow
        print(f"  - Cash Flow:")
        cash_url = f"{FMP_BASE_URL}/cash-flow-statement/{ticker}"
        params = {'apikey': FMP_API_KEY, 'limit': 4}
        
        try:
            response = requests.get(cash_url, params=params, timeout=10)
            if response.status_code == 200:
                cash_data = response.json()
                print(f"    ✅ Success - {len(cash_data)} records")
                if cash_data and len(cash_data) > 0:
                    latest = cash_data[0]
                    print(f"    📋 Free Cash Flow: {latest.get('freeCashFlow', 'N/A')}")
                    print(f"    📋 Operating Cash Flow: {latest.get('operatingCashFlow', 'N/A')}")
            else:
                print(f"    ❌ Failed - {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_batch_financials():
    """Test batch financial data fetching"""
    if not test_fmp_api_key():
        return
    
    print(f"\n🔍 Testing Batch Financial Data Fetching")
    print("=" * 60)
    
    # Test batch income statement
    symbols = "NVDA,MSFT,AAPL,AMZN,GOOGL"
    batch_income_url = f"{FMP_BASE_URL}/income-statement/{symbols}"
    params = {'apikey': FMP_API_KEY, 'limit': 4}
    
    print(f"Testing batch income statement for: {symbols}")
    
    try:
        response = requests.get(batch_income_url, params=params, timeout=30)
        if response.status_code == 200:
            income_data = response.json()
            print(f"✅ Success - {len(income_data)} records")
            
            # Group by symbol
            symbols_data = {}
            for item in income_data:
                symbol = item.get('symbol', 'N/A')
                if symbol not in symbols_data:
                    symbols_data[symbol] = []
                symbols_data[symbol].append(item)
            
            for symbol, data in symbols_data.items():
                print(f"  - {symbol}: {len(data)} quarters")
                if data:
                    latest = data[0]
                    print(f"    Revenue: {latest.get('revenue', 'N/A')}")
                    print(f"    Net Income: {latest.get('netIncome', 'N/A')}")
        else:
            print(f"❌ Failed - {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🚀 FMP Financial Data Testing")
    print("=" * 60)
    
    # Test individual financial data fetching
    test_financial_data_fetching()
    
    # Test batch financial data fetching
    test_batch_financials()
    
    print("\n✅ Testing completed")

if __name__ == "__main__":
    main() 