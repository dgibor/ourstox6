#!/usr/bin/env python3
"""
Check FMP API raw data for AVGO
"""

import sys
import os
import requests

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def check_avgo_fmp_raw():
    """Check FMP API raw data for AVGO"""
    config = Config()
    api_key = config.get_api_key('fmp')
    
    ticker = "AVGO"
    
    print(f"🔍 CHECKING FMP RAW DATA FOR {ticker}")
    print("=" * 50)
    
    # Check income statement
    print("1️⃣ Income Statement Data:")
    print("-" * 30)
    
    income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}"
    params = {'apikey': api_key, 'limit': 10}
    
    response = requests.get(income_url, params=params, timeout=30)
    if response.status_code == 200:
        income_data = response.json()
        if income_data and len(income_data) > 0:
            print(f"Found {len(income_data)} periods")
            
            for i, period in enumerate(income_data[:5]):  # Show first 5 periods
                print(f"\nPeriod {i+1}:")
                print(f"  Period: {period.get('period')}")
                print(f"  Calendar Year: {period.get('calendarYear')}")
                print(f"  Revenue: ${period.get('revenue', 0):,.0f}")
                print(f"  Net Income: ${period.get('netIncome', 0):,.0f}")
                print(f"  EBITDA: ${period.get('ebitda', 0):,.0f}")
                
                # Check if this is quarterly or annual
                period_str = str(period.get('period', ''))
                if 'Q' in period_str:
                    print(f"  ⚠️  QUARTERLY DATA")
                else:
                    print(f"  ✅ ANNUAL DATA")
        else:
            print("❌ No income statement data found")
    else:
        print(f"❌ Failed to fetch income statement: {response.status_code}")
    
    # Check profile data
    print(f"\n2️⃣ Profile Data:")
    print("-" * 30)
    
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
    params = {'apikey': api_key}
    
    response = requests.get(profile_url, params=params, timeout=30)
    if response.status_code == 200:
        profile_data = response.json()
        
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
    
    # Check key metrics
    print(f"\n3️⃣ Key Metrics:")
    print("-" * 30)
    
    metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}"
    params = {'apikey': api_key, 'limit': 5}
    
    response = requests.get(metrics_url, params=params, timeout=30)
    if response.status_code == 200:
        metrics_data = response.json()
        if metrics_data and len(metrics_data) > 0:
            latest = metrics_data[0]
            print(f"PE Ratio: {latest.get('peRatio', 'N/A')}")
            print(f"PS Ratio: {latest.get('priceToSalesRatio', 'N/A')}")
            print(f"EV/EBITDA: {latest.get('enterpriseValueOverEBITDA', 'N/A')}")
            print(f"PB Ratio: {latest.get('pbRatio', 'N/A')}")
        else:
            print("❌ No metrics data found")
    else:
        print(f"❌ Failed to fetch metrics: {response.status_code}")

if __name__ == "__main__":
    check_avgo_fmp_raw() 