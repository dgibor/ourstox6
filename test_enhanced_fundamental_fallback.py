#!/usr/bin/env python3
"""
Test Enhanced Fundamental Fallback System

This script demonstrates how the multi-service fallback system works
to maximize fundamental data coverage.
"""

import sys
sys.path.insert(0, 'daily_run')

from enhanced_multi_service_fundamental_manager import EnhancedMultiServiceFundamentalManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fundamental_fallback_system():
    """Test the enhanced fundamental fallback system"""
    print("🧪 TESTING ENHANCED FUNDAMENTAL FALLBACK SYSTEM")
    print("=" * 70)
    
    manager = EnhancedMultiServiceFundamentalManager()
    
    # Test with companies that might have missing data
    test_tickers = ["AAPL", "AAON", "TSLA", "NVDA"]
    
    results_summary = []
    
    for ticker in test_tickers:
        print(f"\n📊 TESTING {ticker}:")
        print("-" * 50)
        
        try:
            # Get data with fallback
            result = manager.get_fundamental_data_with_fallback(ticker)
            
            # Display results
            print(f"✅ Primary source: {result.primary_source}")
            print(f"🔄 Fallback sources used: {result.fallback_sources_used}")
            print(f"📈 Success rate: {result.success_rate:.1%}")
            print(f"❌ Missing fields: {result.missing_fields}")
            
            print(f"\n📋 Data collected:")
            for field, item in result.data.items():
                print(f"  • {field}: {item.value} (from {item.source}, confidence: {item.confidence:.2f})")
            
            # Store the data
            if result.data:
                success = manager.store_fundamental_data(result)
                print(f"\n💾 Storage: {'✅ Success' if success else '❌ Failed'}")
            
            # Add to summary
            results_summary.append({
                'ticker': ticker,
                'success_rate': result.success_rate,
                'primary_source': result.primary_source,
                'fallback_sources': len(result.fallback_sources_used),
                'missing_fields': len(result.missing_fields)
            })
            
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            results_summary.append({
                'ticker': ticker,
                'success_rate': 0.0,
                'primary_source': 'error',
                'fallback_sources': 0,
                'missing_fields': 16  # All fields missing
            })
    
    # Display summary
    print(f"\n📊 SUMMARY RESULTS:")
    print("=" * 70)
    
    total_success_rate = sum(r['success_rate'] for r in results_summary)
    avg_success_rate = total_success_rate / len(results_summary) if results_summary else 0
    
    print(f"Average success rate: {avg_success_rate:.1%}")
    print(f"Total fallback sources used: {sum(r['fallback_sources'] for r in results_summary)}")
    print(f"Total missing fields: {sum(r['missing_fields'] for r in results_summary)}")
    
    print(f"\n📋 Detailed Results:")
    for result in results_summary:
        print(f"  {result['ticker']}: {result['success_rate']:.1%} success, "
              f"{result['fallback_sources']} fallbacks, {result['missing_fields']} missing")
    
    manager.close()
    
    print(f"\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_fundamental_fallback_system() 