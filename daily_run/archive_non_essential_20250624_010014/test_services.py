#!/usr/bin/env python3
"""
Test script to check each service individually
"""

import sys
import os
from price_service import YahooPriceService, AlphaVantagePriceService, FinnhubPriceService, FMPPriceService
from config import Config

def test_service(service_name: str, service_class, test_ticker: str = 'AAPL'):
    """Test a single service"""
    print(f"\n{'='*50}")
    print(f"Testing {service_name} Service")
    print(f"{'='*50}")
    
    try:
        # Check if API key is available
        api_key = Config.get_api_key(service_name.lower().replace('price', '').replace('service', ''))
        if api_key:
            print(f"✅ API Key: Available")
        else:
            print(f"⚠️  API Key: Not set")
        
        # Create service instance
        service = service_class()
        
        # Test the service
        print(f"Testing with ticker: {test_ticker}")
        data = service.get_data(test_ticker)
        
        if data:
            print(f"✅ SUCCESS: Got data for {test_ticker}")
            print(f"   Close price: ${data['close']/100:.2f}")
            print(f"   Volume: {data['volume']:,}" if data['volume'] else "   Volume: N/A")
        else:
            print(f"❌ FAILED: No data returned for {test_ticker}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print(f"{'='*50}")

def main():
    """Test all services"""
    print("🧪 Testing All Price Services")
    print("=" * 60)
    
    # Test each service
    test_service("Yahoo", YahooPriceService, "AAPL")
    test_service("Alpha Vantage", AlphaVantagePriceService, "AAPL")
    test_service("Finnhub", FinnhubPriceService, "AAPL")
    test_service("FMP", FMPPriceService, "AAPL")
    
    print(f"\n{'='*60}")
    print("Service Testing Complete")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 