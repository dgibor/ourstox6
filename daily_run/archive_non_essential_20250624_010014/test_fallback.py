#!/usr/bin/env python3
"""
Test fallback logic in price collector
"""

from price_service import PriceCollector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_fallback():
    """Test the fallback logic"""
    print("Testing Price Collector Fallback Logic")
    print("=" * 60)
    
    collector = PriceCollector('stocks')
    
    # Test with a few tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print(f"Testing with tickers: {test_tickers}")
    print("\nTesting individual service fallback...")
    
    for ticker in test_tickers:
        print(f"\n--- Testing {ticker} ---")
        ticker_data = None
        
        # Try each service in order
        for service_name in collector.service_order:
            try:
                print(f"  Trying {service_name}...")
                service = collector.services[service_name]
                ticker_data = service.get_data(ticker)
                if ticker_data:
                    print(f"  SUCCESS {service_name}: ${ticker_data['close']/100:.2f}")
                    break
                else:
                    print(f"  FAILED {service_name}: No data")
            except Exception as e:
                print(f"  ERROR {service_name}: {str(e)[:50]}...")
                continue
        
        if ticker_data:
            print(f"  FINAL RESULT: Got data for {ticker}")
        else:
            print(f"  FINAL RESULT: All services failed for {ticker}")
    
    print(f"\n{'='*60}")
    print("Fallback Test Complete")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_fallback() 