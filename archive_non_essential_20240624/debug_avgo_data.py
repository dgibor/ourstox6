#!/usr/bin/env python3
"""
Debug AVGO data to check FMP API responses
"""

import sys
import os
import requests

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def debug_avgo_data():
    """Debug AVGO data from FMP API"""
    config = Config()
    api_key = config.get_api_key('fmp')
    
    ticker = "AVGO"
    
    print(f"🔍 Debugging AVGO data from FMP API")
    print("=" * 50)
    
    # 1. Check income statement data
    print("1️⃣ Checking Income Statement Data:")
    print("-" * 40)
    
    income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}"
    params = {'apikey': api_key, 'limit': 5}
    
    response = requests.get(income_url, params=params, timeout=30)
    if response.status_code == 200:
        income_data = response.json()
        if income_data and len(income_data) > 0:
            latest = income_data[0]
            print(f"Latest Period: {latest.get('period')}")
            print(f"Calendar Year: {latest.get('calendarYear')}")
            print(f"Revenue: ${latest.get('revenue', 0):,.0f}")
            print(f"Net Income: ${latest.get('netIncome', 0):,.0f}")
            print(f"EBITDA: ${latest.get('ebitda', 0):,.0f}")
            print(f"Gross Profit: ${latest.get('grossProfit', 0):,.0f}")
            print(f"Operating Income: ${latest.get('operatingIncome', 0):,.0f}")
            
            # Check if this is quarterly or annual data
            period = latest.get('period', '')
            if 'Q' in str(period):
                print("⚠️  This appears to be QUARTERLY data, not annual!")
            else:
                print("✅ This appears to be ANNUAL data")
        else:
            print("❌ No income statement data found")
    else:
        print(f"❌ Failed to fetch income statement: {response.status_code}")
    
    # 2. Check balance sheet data
    print(f"\n2️⃣ Checking Balance Sheet Data:")
    print("-" * 40)
    
    balance_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}"
    params = {'apikey': api_key, 'limit': 5}
    
    response = requests.get(balance_url, params=params, timeout=30)
    if response.status_code == 200:
        balance_data = response.json()
        if balance_data and len(balance_data) > 0:
            latest = balance_data[0]
            print(f"Latest Period: {latest.get('period')}")
            print(f"Calendar Year: {latest.get('calendarYear')}")
            print(f"Total Assets: ${latest.get('totalAssets', 0):,.0f}")
            print(f"Total Debt: ${latest.get('totalDebt', 0):,.0f}")
            print(f"Total Equity: ${latest.get('totalStockholdersEquity', 0):,.0f}")
            print(f"Cash: ${latest.get('cashAndCashEquivalents', 0):,.0f}")
            
            # Check if this is quarterly or annual data
            period = latest.get('period', '')
            if 'Q' in str(period):
                print("⚠️  This appears to be QUARTERLY data, not annual!")
            else:
                print("✅ This appears to be ANNUAL data")
        else:
            print("❌ No balance sheet data found")
    else:
        print(f"❌ Failed to fetch balance sheet: {response.status_code}")
    
    # 3. Check profile data
    print(f"\n3️⃣ Checking Profile Data:")
    print("-" * 40)
    
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
    params = {'apikey': api_key}
    
    response = requests.get(profile_url, params=params, timeout=30)
    if response.status_code == 200:
        profile_data = response.json()
        
        # Handle case where profile_data is a list
        if isinstance(profile_data, list) and len(profile_data) > 0:
            profile_data = profile_data[0]
        
        if profile_data and isinstance(profile_data, dict):
            print(f"Market Cap: ${profile_data.get('mktCap', 0):,.0f}")
            print(f"Enterprise Value: ${profile_data.get('enterpriseValue', 0):,.0f}")
            print(f"Shares Outstanding: {profile_data.get('sharesOutstanding', 0):,.0f}")
            print(f"Current Price: ${profile_data.get('price', 0):.2f}")
        else:
            print("❌ No profile data found")
    else:
        print(f"❌ Failed to fetch profile: {response.status_code}")

if __name__ == "__main__":
    debug_avgo_data() 