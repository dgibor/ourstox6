#!/usr/bin/env python3
"""
Debug shares_outstanding issue
"""

from fmp_service import FMPService
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_shares_outstanding(ticker='GME'):
    print(f"Debugging shares_outstanding for {ticker}")
    print("=" * 50)
    
    fmp_service = FMPService()
    
    try:
        # Get key statistics
        print("Fetching key statistics...")
        key_stats = fmp_service.fetch_key_statistics(ticker)
        
        if key_stats:
            print(f"Key stats structure: {list(key_stats.keys())}")
            
            if 'market_data' in key_stats:
                market_data = key_stats['market_data']
                print(f"Market data: {market_data}")
                
                shares_outstanding = market_data.get('shares_outstanding')
                print(f"Shares outstanding: {shares_outstanding}")
                
                # Check if it's 0 or None
                if shares_outstanding == 0:
                    print("⚠️  Shares outstanding is 0 - this might be a data issue")
                elif shares_outstanding is None:
                    print("⚠️  Shares outstanding is None")
                else:
                    print(f"✅ Shares outstanding: {shares_outstanding:,.0f}")
            else:
                print("❌ No market_data in key_stats")
        else:
            print("❌ No key_stats returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fmp_service.close()

if __name__ == "__main__":
    debug_shares_outstanding('GME') 