#!/usr/bin/env python3
"""
Debug FMP API Calls for Fundamental Data
Test individual API endpoints to see what data is returned
"""

import os
import requests
import json
from typing import Dict, List, Any

# FMP API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

def test_fmp_api():
    """Test FMP API endpoints"""
    if not FMP_API_KEY:
        print("❌ FMP_API_KEY environment variable is required")
        return
    
    print("🔍 Testing FMP API endpoints")
    print("=" * 50)
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}:")
        
        # Test profile
        print(f"  - Profile:")
        profile_url = f"{FMP_BASE_URL}/profile/{ticker}"
        params = {'apikey': FMP_API_KEY}
        
        try:
            response = requests.get(profile_url, params=params, timeout=10)
            if response.status_code == 200:
                profile_data = response.json()
                print(f"    ✅ Success - {len(profile_data)} records")
                if isinstance(profile_data, list) and len(profile_data) > 0:
                    print(f"    📋 Keys: {list(profile_data[0].keys())}")
            else:
                print(f"    ❌ Failed - {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Test income statement
        print(f"  - Income Statement:")
        income_url = f"{FMP_BASE_URL}/income-statement/{ticker}"
        params = {'apikey': FMP_API_KEY, 'limit': 4}
        
        try:
            response = requests.get(income_url, params=params, timeout=10)
            if response.status_code == 200:
                income_data = response.json()
                print(f"    ✅ Success - {len(income_data)} records")
                if isinstance(income_data, list) and len(income_data) > 0:
                    print(f"    📋 Keys: {list(income_data[0].keys())}")
                    print(f"    💰 Revenue: {income_data[0].get('revenue', 'N/A')}")
                    print(f"    💵 Net Income: {income_data[0].get('netIncome', 'N/A')}")
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
                if isinstance(balance_data, list) and len(balance_data) > 0:
                    print(f"    📋 Keys: {list(balance_data[0].keys())}")
                    print(f"    🏢 Total Assets: {balance_data[0].get('totalAssets', 'N/A')}")
                    print(f"    💳 Total Equity: {balance_data[0].get('totalStockholdersEquity', 'N/A')}")
                    print(f"    📈 Shares Outstanding: {balance_data[0].get('totalSharesOutstanding', 'N/A')}")
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
                if isinstance(cash_data, list) and len(cash_data) > 0:
                    print(f"    📋 Keys: {list(cash_data[0].keys())}")
                    print(f"    💰 Free Cash Flow: {cash_data[0].get('freeCashFlow', 'N/A')}")
            else:
                print(f"    ❌ Failed - {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        print()

def test_batch_api():
    """Test batch API endpoints"""
    print("\n🔍 Testing FMP Batch API endpoints")
    print("=" * 50)
    
    # Test batch profile
    print("📊 Testing Batch Profile:")
    symbols = "AAPL,MSFT,GOOGL"
    batch_profile_url = f"{FMP_BASE_URL}/profile/{symbols}"
    params = {'apikey': FMP_API_KEY}
    
    try:
        response = requests.get(batch_profile_url, params=params, timeout=10)
        if response.status_code == 200:
            profile_data = response.json()
            print(f"  ✅ Success - {len(profile_data)} records")
            if isinstance(profile_data, list) and len(profile_data) > 0:
                print(f"  📋 Keys: {list(profile_data[0].keys())}")
                for item in profile_data:
                    print(f"    - {item.get('symbol', 'N/A')}: {item.get('companyName', 'N/A')}")
        else:
            print(f"  ❌ Failed - {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test batch income statement
    print("\n📊 Testing Batch Income Statement:")
    batch_income_url = f"{FMP_BASE_URL}/income-statement/{symbols}"
    params = {'apikey': FMP_API_KEY, 'limit': 4}
    
    try:
        response = requests.get(batch_income_url, params=params, timeout=10)
        if response.status_code == 200:
            income_data = response.json()
            print(f"  ✅ Success - {len(income_data)} records")
            if isinstance(income_data, list) and len(income_data) > 0:
                print(f"  📋 Keys: {list(income_data[0].keys())}")
                # Group by symbol
                symbols_data = {}
                for item in income_data:
                    symbol = item.get('symbol', 'N/A')
                    if symbol not in symbols_data:
                        symbols_data[symbol] = []
                    symbols_data[symbol].append(item)
                
                for symbol, data in symbols_data.items():
                    print(f"    - {symbol}: {len(data)} quarters")
                    if data:
                        print(f"      Latest revenue: {data[0].get('revenue', 'N/A')}")
        else:
            print(f"  ❌ Failed - {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    """Main function"""
    print("🚀 FMP API Debug Test")
    print("=" * 60)
    
    test_fmp_api()
    test_batch_api()
    
    print("\n✅ Debug test completed")

if __name__ == "__main__":
    main() 