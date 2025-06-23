#!/usr/bin/env python3
"""
Test Alpha Vantage with proper rate limiting
"""

import time
import requests
from config import Config

def test_alpha_vantage_with_delay():
    """Test Alpha Vantage API with proper delays"""
    print("Testing Alpha Vantage API with Rate Limiting")
    print("=" * 60)
    
    api_key = Config.get_api_key('alpha_vantage')
    print(f"API Key: {api_key[:8]}..." if api_key else "Not set")
    
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for i, ticker in enumerate(test_tickers):
        print(f"\n--- Test {i+1}: {ticker} ---")
        
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Information' in data:
                    info = data['Information']
                    print(f"Info: {info}")
                    if 'rate limit' in info.lower():
                        print("Rate limit hit - this is expected for free tier")
                    elif 'demo' in info.lower():
                        print("Demo key detected")
                    else:
                        print("Other information message")
                
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    price = quote.get('05. price', 'N/A')
                    volume = quote.get('06. volume', 'N/A')
                    print(f"SUCCESS: Price=${price}, Volume={volume}")
                else:
                    print("No Global Quote data")
                    print(f"Available keys: {list(data.keys())}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")
        
        # Wait 12 seconds between calls (5 calls per minute = 12 seconds)
        if i < len(test_tickers) - 1:
            print("Waiting 12 seconds for rate limit...")
            time.sleep(12)

if __name__ == "__main__":
    test_alpha_vantage_with_delay() 