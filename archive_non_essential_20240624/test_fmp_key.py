#!/usr/bin/env python3
"""
Test FMP API Key
Simple test to verify if the new FMP API key is working
"""

import sys
import os
import requests

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def test_fmp_key():
    """Test if the FMP API key is working"""
    config = Config()
    api_key = config.get_api_key('fmp')
    
    if not api_key:
        print("❌ No FMP API key found in environment")
        return False
    
    print(f"🔑 Testing FMP API key: {api_key[:10]}...")
    
    # Test with a simple API call
    url = f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print("✅ API key is working!")
                print(f"📊 Sample data: {data[0]}")
                return True
            else:
                print("⚠️  API returned empty data")
                return False
        elif response.status_code == 429:
            print("❌ Rate limit exceeded (429)")
            return False
        elif response.status_code == 403:
            print("❌ API key invalid or quota exceeded (403)")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    test_fmp_key() 