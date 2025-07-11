#!/usr/bin/env python3
"""
Debug FMP API responses to see what data is actually available
"""

import sys
sys.path.append('..')

import requests
import json
from config import FMP_API_KEY

def debug_fmp_api():
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    
    print("=== DEBUGGING FMP API RESPONSES ===")
    print("=" * 60)
    
    for ticker in tickers:
        try:
            print(f"\n📊 Debugging {ticker} FMP API...")
            
            # Fetch key statistics directly
            url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={FMP_API_KEY}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    metrics = data[0]
                    print(f"✅ FMP API Response for {ticker}:")
                    print(f"   PE Ratio: {metrics.get('peRatio')}")
                    print(f"   PB Ratio: {metrics.get('pbRatio')}")
                    print(f"   P/S Ratio: {metrics.get('priceToSalesRatio')}")
                    print(f"   EV/EBITDA: {metrics.get('enterpriseValueOverEBITDA')}")
                    print(f"   ROE: {metrics.get('roe')}")
                    print(f"   ROA: {metrics.get('roa')}")
                    print(f"   Debt/Equity: {metrics.get('debtToEquityRatio')}")
                    print(f"   Current Ratio: {metrics.get('currentRatio')}")
                    print(f"   Gross Margin: {metrics.get('grossProfitMargin')}")
                    print(f"   Operating Margin: {metrics.get('operatingProfitMargin')}")
                    print(f"   Net Margin: {metrics.get('netProfitMargin')}")
                else:
                    print(f"❌ No metrics data returned for {ticker}")
            else:
                print(f"❌ API request failed for {ticker}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error debugging {ticker}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Finished debugging FMP API")

if __name__ == "__main__":
    debug_fmp_api() 