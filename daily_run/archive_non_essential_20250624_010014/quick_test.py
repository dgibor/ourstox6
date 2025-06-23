#!/usr/bin/env python3
"""
Quick test to check system status
"""

from price_service import PriceCollector
from database import DatabaseManager
import time

def quick_test():
    """Quick test with first 10 tickers"""
    print("Quick System Status Test")
    print("=" * 50)
    
    # Get first 10 tickers
    db = DatabaseManager()
    db.connect()
    tickers = db.get_tickers('stocks')[:10]
    db.disconnect()
    
    print(f"Testing with tickers: {tickers}")
    print(f"Total tickers to test: {len(tickers)}")
    
    # Test price collection
    print("\n1. Testing Price Collection...")
    collector = PriceCollector('stocks')
    
    start_time = time.time()
    prices, failed = collector.collect_prices_batch(tickers)
    end_time = time.time()
    
    print(f"Price collection completed in {end_time - start_time:.1f} seconds")
    print(f"   Successful: {len(prices)}")
    print(f"   Failed: {len(failed)}")
    
    if prices:
        print(f"   Sample prices:")
        for ticker, data in list(prices.items())[:3]:
            print(f"     {ticker}: ${data['close']/100:.2f}")
    
    if failed:
        print(f"   Failed tickers: {failed}")
    
    # Test database update
    print("\n2. Testing Database Update...")
    if prices:
        updated_count = collector.update_database(prices)
        print(f"Database updated: {updated_count} tickers")
    else:
        print("No prices to update")
    
    collector.close()
    
    print(f"\n{'='*50}")
    print("Quick Test Summary:")
    print(f"Price Collection: {len(prices)}/{len(tickers)} successful")
    print(f"Database Update: {'Working' if prices else 'No data'}")
    print(f"System Status: {'OPERATIONAL' if len(prices) > 0 else 'ISSUES DETECTED'}")
    print(f"{'='*50}")

if __name__ == "__main__":
    quick_test() 