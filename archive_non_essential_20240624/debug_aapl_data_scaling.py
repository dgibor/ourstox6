#!/usr/bin/env python3
"""
Debug AAPL data scaling issue by checking raw FMP API responses
"""

import sys
import os
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def debug_aapl_data_scaling():
    """Debug the data scaling issue for AAPL"""
    config = Config()
    api_key = config.get_api_key('fmp')
    
    ticker = "AAPL"
    
    print(f"🔍 Debugging data scaling for {ticker}")
    print("=" * 60)
    
    # 1. Check income statement data
    print("1️⃣ Checking Income Statement Data:")
    print("-" * 40)
    
    income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=4&apikey={api_key}"
    
    try:
        income_response = requests.get(income_url, timeout=10)
        income_data = income_response.json()
        
        if income_data and len(income_data) > 0:
            print(f"✅ Found {len(income_data)} income statement periods:")
            
            for i, period in enumerate(income_data[:4]):
                print(f"\n  Period {i+1}:")
                print(f"    Date: {period.get('date', 'N/A')}")
                print(f"    Revenue: ${period.get('revenue', 0):,.0f}")
                print(f"    Net Income: ${period.get('netIncome', 0):,.0f}")
                print(f"    Gross Profit: ${period.get('grossProfit', 0):,.0f}")
                print(f"    Operating Income: ${period.get('operatingIncome', 0):,.0f}")
                print(f"    EBITDA: ${period.get('ebitda', 0):,.0f}")
        else:
            print(f"❌ No income statement data received")
            return
    except Exception as e:
        print(f"❌ Error fetching income statement: {e}")
        return
    
    # 2. Check balance sheet data
    print(f"\n2️⃣ Checking Balance Sheet Data:")
    print("-" * 40)
    
    balance_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?limit=1&apikey={api_key}"
    
    try:
        balance_response = requests.get(balance_url, timeout=10)
        balance_data = balance_response.json()
        
        if balance_data and len(balance_data) > 0:
            balance = balance_data[0]
            print(f"✅ Balance sheet data:")
            print(f"    Date: {balance.get('date', 'N/A')}")
            print(f"    Total Assets: ${balance.get('totalAssets', 0):,.0f}")
            print(f"    Total Debt: ${balance.get('totalDebt', 0):,.0f}")
            print(f"    Total Equity: ${balance.get('totalStockholdersEquity', 0):,.0f}")
            print(f"    Cash & Equivalents: ${balance.get('cashAndCashEquivalents', 0):,.0f}")
        else:
            print(f"❌ No balance sheet data received")
    except Exception as e:
        print(f"❌ Error fetching balance sheet: {e}")
    
    # 3. Check key metrics
    print(f"\n3️⃣ Checking Key Metrics:")
    print("-" * 40)
    
    metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={api_key}"
    
    try:
        metrics_response = requests.get(metrics_url, timeout=10)
        metrics_data = metrics_response.json()
        
        if metrics_data and len(metrics_data) > 0:
            metrics = metrics_data[0]
            print(f"✅ Key metrics data:")
            print(f"    Date: {metrics.get('date', 'N/A')}")
            print(f"    PE Ratio: {metrics.get('peRatio', 0)}")
            print(f"    PB Ratio: {metrics.get('pbRatio', 0)}")
            print(f"    PS Ratio: {metrics.get('priceToSalesRatio', 0)}")
            print(f"    ROE: {metrics.get('roe', 0)}")
            print(f"    ROA: {metrics.get('roa', 0)}")
            print(f"    Debt/Equity: {metrics.get('debtToEquityRatio', 0)}")
            print(f"    Current Ratio: {metrics.get('currentRatio', 0)}")
            print(f"    Gross Margin: {metrics.get('grossProfitMargin', 0)}")
            print(f"    Operating Margin: {metrics.get('operatingProfitMargin', 0)}")
            print(f"    Net Margin: {metrics.get('netProfitMargin', 0)}")
            print(f"    EPS: {metrics.get('eps', 0)}")
            print(f"    Book Value Per Share: {metrics.get('bookValuePerShare', 0)}")
        else:
            print(f"❌ No key metrics data received")
    except Exception as e:
        print(f"❌ Error fetching key metrics: {e}")
    
    # 4. Check profile data
    print(f"\n4️⃣ Checking Profile Data:")
    print("-" * 40)
    
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
    
    try:
        profile_response = requests.get(profile_url, timeout=10)
        profile_data = profile_response.json()
        
        if profile_data and len(profile_data) > 0:
            profile = profile_data[0]
            print(f"✅ Profile data:")
            print(f"    Market Cap: ${profile.get('mktCap', 0):,.0f}")
            print(f"    Enterprise Value: ${profile.get('enterpriseValue', 0):,.0f}")
            print(f"    Shares Outstanding: {profile.get('sharesOutstanding', 0):,.0f}")
            print(f"    Current Price: ${profile.get('price', 0):.2f}")
        else:
            print(f"❌ No profile data received")
    except Exception as e:
        print(f"❌ Error fetching profile data: {e}")

if __name__ == "__main__":
    debug_aapl_data_scaling() 