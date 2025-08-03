#!/usr/bin/env python3
"""
Test enhanced fundamental data collection for specified tickers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daily_run.enhanced_multi_service_fundamental_manager import EnhancedMultiServiceFundamentalManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fundamental_collection():
    """Test fundamental data collection for specified tickers"""
    
    # Test tickers
    tickers = ['PG', 'AZN', 'COST', 'XOM', 'ORCL', 'LLY', 'TSM', 'AVGO', 'WFC', 'AMD', 'CVX', 'IBM', 'CSCO']
    
    print("🧪 TESTING ENHANCED FUNDAMENTAL DATA COLLECTION")
    print("=" * 60)
    
    manager = EnhancedMultiServiceFundamentalManager()
    results = {}
    
    try:
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Testing {ticker}...")
            
            try:
                # Get fundamental data
                result = manager.get_fundamental_data_with_fallback(ticker)
                
                # Store the data
                storage_success = manager.store_fundamental_data(result)
                
                # Record results
                results[ticker] = {
                    'success': True,
                    'data_count': len(result.data),
                    'success_rate': result.success_rate,
                    'primary_source': result.primary_source,
                    'fallback_sources': result.fallback_sources_used,
                    'missing_fields': result.missing_fields,
                    'storage_success': storage_success
                }
                
                print(f"✅ {ticker}: {len(result.data)} fields collected ({result.success_rate:.1%} success rate)")
                print(f"   Primary: {result.primary_source}, Fallbacks: {result.fallback_sources_used}")
                print(f"   Storage: {'Success' if storage_success else 'Failed'}")
                
            except Exception as e:
                print(f"❌ {ticker}: Error - {e}")
                results[ticker] = {
                    'success': False,
                    'error': str(e)
                }
    
    finally:
        manager.close()
    
    # Summary
    print(f"\n📊 SUMMARY RESULTS")
    print("=" * 60)
    
    successful = [t for t, r in results.items() if r.get('success', False)]
    failed = [t for t, r in results.items() if not r.get('success', False)]
    
    print(f"✅ Successful: {len(successful)}/{len(tickers)} ({len(successful)/len(tickers):.1%})")
    print(f"❌ Failed: {len(failed)}/{len(tickers)} ({len(failed)/len(tickers):.1%})")
    
    if successful:
        avg_success_rate = sum(r['success_rate'] for r in results.values() if r.get('success')) / len(successful)
        avg_data_count = sum(r['data_count'] for r in results.values() if r.get('success')) / len(successful)
        print(f"📈 Average success rate: {avg_success_rate:.1%}")
        print(f"📊 Average data fields: {avg_data_count:.1f}")
    
    print(f"\n✅ Successful tickers: {', '.join(successful)}")
    if failed:
        print(f"❌ Failed tickers: {', '.join(failed)}")
    
    return results

if __name__ == "__main__":
    test_fundamental_collection() 