#!/usr/bin/env python3
"""
Detailed test for Alpha Vantage service
"""

import requests
from config import Config

def test_alpha_vantage_direct():
    """Test Alpha Vantage API directly"""
    print("Testing Alpha Vantage API Directly")
    print("=" * 50)
    
    api_key = Config.get_api_key('alpha_vantage')
    print(f"API Key available: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key length: {len(api_key)} characters")
    
    ticker = 'AAPL'
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
    
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {data}")
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                print(f"Global Quote found: {quote}")
                
                if quote:
                    print(f"Price: {quote.get('05. price', 'N/A')}")
                    print(f"Open: {quote.get('02. open', 'N/A')}")
                    print(f"High: {quote.get('03. high', 'N/A')}")
                    print(f"Low: {quote.get('04. low', 'N/A')}")
                    print(f"Volume: {quote.get('06. volume', 'N/A')}")
                else:
                    print("Global Quote is empty")
            else:
                print("Global Quote not found in response")
                print(f"Available keys: {list(data.keys())}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_alpha_vantage_service():
    """Test Alpha Vantage service class"""
    print("\nTesting Alpha Vantage Service Class")
    print("=" * 50)
    
    from price_service import AlphaVantagePriceService
    
    service = AlphaVantagePriceService()
    print(f"Service API key: {'Set' if service.api_key else 'Not set'}")
    
    try:
        data = service.get_data('AAPL')
        if data:
            print(f"SUCCESS: Got data for AAPL")
            print(f"Close: ${data['close']/100:.2f}")
            print(f"Volume: {data['volume']:,}" if data['volume'] else "Volume: N/A")
        else:
            print("FAILED: No data returned")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_alpha_vantage_direct()
    test_alpha_vantage_service() 