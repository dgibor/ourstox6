#!/usr/bin/env python3
"""
Quick test batch processing for a small number of stocks
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService

def quick_test_batch():
    """Quick test with a small batch of stocks"""
    
    print("🧪 QUICK TEST BATCH PROCESSING")
    print("=" * 50)
    
    # Initialize services
    db = DatabaseManager()
    fmp = FMPService()
    
    # Test with a small batch of well-known stocks
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print(f"📋 Testing with {len(test_tickers)} tickers: {', '.join(test_tickers)}")
    print()
    
    stats = {'success': 0, 'failed': 0, 'errors': []}
    
    for i, ticker in enumerate(test_tickers):
        print(f"[{i+1}/{len(test_tickers)}] Processing {ticker}...")
        
        try:
            # Fetch financial statements
            print(f"  📊 Fetching financial data...")
            financial_data = fmp.fetch_financial_statements(ticker)
            if not financial_data:
                print(f"    ❌ No financial data")
                stats['failed'] += 1
                continue
            
            # Fetch key statistics
            print(f"  📈 Fetching key statistics...")
            key_stats = fmp.fetch_key_statistics(ticker)
            if not key_stats:
                print(f"    ❌ No key statistics")
                stats['failed'] += 1
                continue
            
            # Store the data
            print(f"  💾 Storing data...")
            success = fmp.store_fundamental_data(ticker, financial_data, key_stats)
            
            if success:
                print(f"    ✅ Success")
                stats['success'] += 1
                
                # Show some key data
                income = financial_data.get('income_statement', {})
                market_data = key_stats.get('market_data', {})
                
                if income.get('revenue'):
                    print(f"      Revenue: ${income.get('revenue'):,.0f}")
                if income.get('net_income'):
                    print(f"      Net Income: ${income.get('net_income'):,.0f}")
                if market_data.get('market_cap'):
                    print(f"      Market Cap: ${market_data.get('market_cap'):,.0f}")
                
            else:
                print(f"    ❌ Failed to store")
                stats['failed'] += 1
            
        except Exception as e:
            error_msg = f"{ticker}: {str(e)}"
            print(f"    💥 Error: {error_msg}")
            stats['failed'] += 1
            stats['errors'].append(error_msg)
            continue
        
        # Small delay between requests
        if i < len(test_tickers) - 1:
            time.sleep(1)
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Successful: {stats['success']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"Success rate: {(stats['success'] / len(test_tickers) * 100):.1f}%")
    
    if stats['errors']:
        print(f"\n❌ Errors:")
        for error in stats['errors']:
            print(f"  • {error}")
    
    fmp.close()
    
    if stats['success'] >= 3:  # At least 3 out of 5 successful
        print(f"\n🎉 Quick test PASSED! Ready for full batch processing.")
        return True
    else:
        print(f"\n⚠️  Quick test FAILED! Check issues before full processing.")
        return False

if __name__ == "__main__":
    quick_test_batch() 