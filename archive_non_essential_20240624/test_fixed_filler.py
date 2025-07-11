#!/usr/bin/env python3
"""
Test Fixed Large Cap Fundamentals Filler
Test with just 3 tickers to verify it works
"""

import os
import sys
from fixed_large_cap_filler import FixedLargeCapFundamentalsFiller

def test_fixed_filler():
    """Test the fixed filler with 3 tickers"""
    print("🧪 Testing Fixed Large Cap Fundamentals Filler")
    print("=" * 50)
    print("Testing with first 3 large cap tickers")
    print()
    
    try:
        filler = FixedLargeCapFundamentalsFiller()
        
        # Get all missing tickers
        all_missing = filler.get_large_cap_missing_tickers()
        
        if not all_missing:
            print("✅ No large cap tickers missing fundamental data!")
            return
        
        # Take first 3 for testing
        test_tickers = all_missing[:3]
        
        print(f"🧪 Testing with {len(test_tickers)} tickers:")
        for i, ticker_info in enumerate(test_tickers):
            market_cap_b = ticker_info['market_cap'] / 1_000_000_000
            print(f"  {i+1}. {ticker_info['ticker']}: ${market_cap_b:.1f}B - {ticker_info['company_name']}")
        
        print()
        print("Starting test...")
        print()
        
        # Process just these 3 tickers
        successful = 0
        failed = 0
        
        for i, ticker_info in enumerate(test_tickers):
            ticker = ticker_info['ticker']
            market_cap = ticker_info['market_cap']
            
            print(f"Processing {i+1}/3: {ticker}")
            
            try:
                # Fetch financial data for this ticker
                financial_data = filler.fetch_single_ticker_financials(ticker)
                
                if financial_data:
                    # Update database
                    if filler.update_fundamental_record(ticker, financial_data):
                        successful += 1
                        print(f"✅ Successfully updated {ticker}")
                    else:
                        failed += 1
                        print(f"❌ Failed to update database for {ticker}")
                else:
                    failed += 1
                    print(f"❌ No financial data available for {ticker}")
                
            except Exception as e:
                failed += 1
                print(f"❌ Error processing {ticker}: {e}")
        
        # Summary
        print()
        print("🧪 Test Results:")
        print(f"  - Successful: {successful}")
        print(f"  - Failed: {failed}")
        print(f"  - API calls used: {filler.api_calls_made}")
        
        if successful > 0:
            print("✅ Test successful! The fixed filler is working.")
            print("You can now run the full process.")
        else:
            print("❌ Test failed. All tickers failed to update.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_filler() 