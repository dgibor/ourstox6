#!/usr/bin/env python3
"""
Debug FMP key statistics extraction for AAPL
"""

import sys
import os
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def debug_key_stats():
    """Debug key statistics extraction for AAPL"""
    config = Config()
    api_key = config.get_api_key('fmp')
    
    ticker = "AAPL"
    
    print(f"🔍 Debugging key statistics for {ticker}")
    print("=" * 50)
    
    # Fetch profile data
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
    print(f"📡 Fetching profile data...")
    
    try:
        profile_response = requests.get(profile_url, timeout=10)
        profile_data = profile_response.json()
        
        if profile_data and len(profile_data) > 0:
            profile = profile_data[0]
            print(f"✅ Profile data received:")
            print(f"  Market Cap: ${profile.get('mktCap', 0):,.0f}")
            print(f"  Enterprise Value: ${profile.get('enterpriseValue', 0):,.0f}")
            print(f"  Shares Outstanding: {profile.get('sharesOutstanding', 0):,.0f}")
            print(f"  Current Price: ${profile.get('price', 0):.2f}")
        else:
            print(f"❌ No profile data received")
            return
    except Exception as e:
        print(f"❌ Error fetching profile data: {e}")
        return
    
    # Fetch key metrics
    metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={api_key}"
    print(f"\n📡 Fetching key metrics...")
    
    try:
        metrics_response = requests.get(metrics_url, timeout=10)
        metrics_data = metrics_response.json()
        
        if metrics_data and len(metrics_data) > 0:
            metrics = metrics_data[0]
            print(f"✅ Key metrics received:")
            print(f"  PE Ratio: {metrics.get('peRatio', 0)}")
            print(f"  PB Ratio: {metrics.get('pbRatio', 0)}")
            print(f"  PS Ratio: {metrics.get('priceToSalesRatio', 0)}")
            print(f"  EV/EBITDA: {metrics.get('enterpriseValueOverEBITDA', 0)}")
            print(f"  ROE: {metrics.get('roe', 0)}")
            print(f"  ROA: {metrics.get('roa', 0)}")
            print(f"  Debt/Equity: {metrics.get('debtToEquityRatio', 0)}")
            print(f"  Current Ratio: {metrics.get('currentRatio', 0)}")
            print(f"  Gross Margin: {metrics.get('grossProfitMargin', 0)}")
            print(f"  Operating Margin: {metrics.get('operatingProfitMargin', 0)}")
            print(f"  Net Margin: {metrics.get('netProfitMargin', 0)}")
            print(f"  EPS: {metrics.get('eps', 0)}")
            print(f"  Book Value Per Share: {metrics.get('bookValuePerShare', 0)}")
            print(f"  Cash Per Share: {metrics.get('cashPerShare', 0)}")
            print(f"  Revenue Per Share: {metrics.get('revenuePerShare', 0)}")
        else:
            print(f"❌ No key metrics received")
            return
    except Exception as e:
        print(f"❌ Error fetching key metrics: {e}")
        return

if __name__ == "__main__":
    debug_key_stats() 