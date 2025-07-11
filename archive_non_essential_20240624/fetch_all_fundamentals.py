#!/usr/bin/env python3
"""
Fetch fundamental data for all target tickers
"""

import sys
sys.path.append('..')

from fmp_service import FMPService

def fetch_all_fundamentals():
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    service = FMPService()
    
    print("Fetching fundamental data for target tickers...")
    
    for ticker in tickers:
        try:
            print(f"\n📊 Fetching data for {ticker}...")
            result = service.get_fundamental_data(ticker)
            
            if result:
                print(f"✅ Successfully fetched data for {ticker}")
                if result.get('key_stats') and result['key_stats'].get('ratios'):
                    ratios = result['key_stats']['ratios']
                    print(f"   PE: {ratios.get('pe_ratio', 'N/A')}")
                    print(f"   PB: {ratios.get('pb_ratio', 'N/A')}")
                    print(f"   ROE: {ratios.get('roe', 'N/A')}")
                    print(f"   D/E: {ratios.get('debt_to_equity', 'N/A')}")
                    print(f"   CR: {ratios.get('current_ratio', 'N/A')}")
            else:
                print(f"❌ Failed to fetch data for {ticker}")
                
        except Exception as e:
            print(f"❌ Error fetching data for {ticker}: {e}")
    
    service.close()
    print("\n✅ Finished fetching fundamental data for all tickers")

if __name__ == "__main__":
    fetch_all_fundamentals() 