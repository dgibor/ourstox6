#!/usr/bin/env python3
"""
Test FMP service
"""

from price_service import FMPPriceService
from config import Config

def test_fmp_service():
    """Test FMP service"""
    print("Testing FMP Service")
    print("=" * 50)
    
    api_key = Config.get_api_key('fmp')
    print(f"API Key available: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key length: {len(api_key)} characters")
    
    service = FMPPriceService()
    print(f"Service API key: {'Set' if service.api_key else 'Not set'}")
    
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for ticker in test_tickers:
        try:
            print(f"\nTesting {ticker}...")
            data = service.get_data(ticker)
            if data:
                print(f"  SUCCESS: ${data['close']/100:.2f}")
                print(f"  Volume: {data['volume']:,}" if data['volume'] else "  Volume: N/A")
            else:
                print(f"  FAILED: No data")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    test_fmp_service() 