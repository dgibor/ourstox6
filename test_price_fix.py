#!/usr/bin/env python3
"""
Test script to verify price service database fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

from price_service import PriceCollector
from database import DatabaseManager

def test_price_service_fix():
    """Test the fixed price service"""
    print("🧪 Testing Price Service Database Fix")
    print("=" * 50)
    
    try:
        # Test database connection first
        db = DatabaseManager()
        if not db.test_connection():
            print("❌ Database connection failed")
            return
        print("✅ Database connection successful")
        
        # Test price collector with small batch
        collector = PriceCollector('stocks')
        test_tickers = ['AAPL', 'MSFT']  # Small test batch
        
        print(f"\n📊 Testing price collection for {test_tickers}")
        
        # Test price collection
        prices_data, failed_tickers = collector.collect_prices_batch(test_tickers)
        
        print(f"✅ Collected prices for {len(prices_data)} tickers")
        print(f"❌ Failed to collect prices for {len(failed_tickers)} tickers")
        
        if prices_data:
            print("\n📈 Sample price data:")
            for ticker, data in prices_data.items():
                print(f"  {ticker}: ${data.get('close', 0)/100:.2f}")
        
        # Test database update
        if prices_data:
            print(f"\n💾 Testing database update...")
            updated_count = collector.update_database(prices_data)
            print(f"✅ Updated {updated_count} tickers in database")
            
            # Verify data was stored
            print(f"\n🔍 Verifying stored data...")
            for ticker in prices_data.keys():
                latest_price = db.get_latest_price(ticker)
                if latest_price:
                    print(f"  ✅ {ticker}: ${latest_price:.2f} (stored)")
                else:
                    print(f"  ❌ {ticker}: No price data found")
        
        collector.close()
        db.disconnect()
        
        print("\n✅ Price service database fix test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_price_service_fix() 