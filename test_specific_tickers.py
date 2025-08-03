#!/usr/bin/env python3
"""
Test fundamental ratio calculations for specific tickers
"""
import sys
import time
sys.path.insert(0, 'daily_run')

from enhanced_multi_service_fundamental_manager import EnhancedMultiServiceFundamentalManager
from database import DatabaseManager
from calculate_fundamental_ratios import DailyFundamentalRatioCalculator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_specific_tickers():
    """Test fundamental ratio calculations for specific tickers"""
    tickers = ['PG', 'AZN', 'COST', 'XOM', 'ORCL', 'LLY', 'TSM', 'AVGO', 'WFC', 'AMD', 'CVX', 'IBM', 'CSCO']
    
    print("🧪 TESTING FUNDAMENTAL RATIO CALCULATIONS")
    print("=" * 60)
    print(f"Target tickers: {', '.join(tickers)}")
    print("=" * 60)
    
    manager = EnhancedMultiServiceFundamentalManager()
    db = DatabaseManager()
    ratio_calculator = DailyFundamentalRatioCalculator(db)
    
    results = {
        'total': len(tickers),
        'fundamental_success': 0,
        'storage_success': 0,
        'ratio_success': 0,
        'details': []
    }
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Testing {ticker}:")
        print("-" * 40)
        
        start_time = time.time()
        ticker_result = {
            'ticker': ticker,
            'fundamental_success': False,
            'storage_success': False,
            'ratio_success': False,
            'success_rate': 0.0,
            'time_taken': 0.0,
            'error': None
        }
        
        try:
            # Step 1: Get fundamental data
            print(f"📊 Getting fundamental data for {ticker}...")
            result = manager.get_fundamental_data_with_fallback(ticker)
            
            if result and result.data:
                ticker_result['fundamental_success'] = True
                ticker_result['success_rate'] = result.success_rate
                results['fundamental_success'] += 1
                
                print(f"✅ Fundamental data: {len(result.data)}/16 fields collected")
                print(f"   Success rate: {result.success_rate:.1%}")
                print(f"   Primary source: {result.primary_source}")
                print(f"   Fallback sources: {result.fallback_sources_used}")
                
                # Step 2: Store data
                print(f"💾 Storing fundamental data...")
                storage_success = manager.store_fundamental_data(result)
                if storage_success:
                    ticker_result['storage_success'] = True
                    results['storage_success'] += 1
                    print(f"✅ Storage: Success")
                else:
                    print(f"❌ Storage: Failed")
                
                # Step 3: Calculate ratios
                print(f"🧮 Calculating ratios...")
                companies = ratio_calculator.get_companies_needing_ratio_updates()
                target_company = next((c for c in companies if c['ticker'] == ticker), None)
                
                if target_company:
                    ratio_success = ratio_calculator.calculate_ratios_for_company(target_company)
                    if ratio_success:
                        ticker_result['ratio_success'] = True
                        results['ratio_success'] += 1
                        print(f"✅ Ratio calculation: Success")
                    else:
                        print(f"❌ Ratio calculation: Failed")
                else:
                    print(f"⚠️ Company not found in ratio update list")
            else:
                print(f"❌ Failed to get fundamental data")
                
        except Exception as e:
            ticker_result['error'] = str(e)
            print(f"❌ Error: {e}")
        
        ticker_result['time_taken'] = time.time() - start_time
        results['details'].append(ticker_result)
        
        print(f"⏱️ Time taken: {ticker_result['time_taken']:.1f}s")
    
    # Print summary
    print(f"\n📊 FINAL RESULTS")
    print("=" * 60)
    print(f"Total tickers processed: {results['total']}")
    print(f"Fundamental data success: {results['fundamental_success']}/{results['total']} ({results['fundamental_success']/results['total']*100:.1f}%)")
    print(f"Data storage success: {results['storage_success']}/{results['total']} ({results['storage_success']/results['total']*100:.1f}%)")
    print(f"Ratio calculation success: {results['ratio_success']}/{results['total']} ({results['ratio_success']/results['total']*100:.1f}%)")
    
    print(f"\n📋 DETAILED RESULTS:")
    print("-" * 60)
    print(f"{'Ticker':<6} {'Fund':<5} {'Store':<5} {'Ratio':<5} {'Success':<8} {'Time':<6}")
    print("-" * 60)
    
    for detail in results['details']:
        fund_status = "✅" if detail['fundamental_success'] else "❌"
        store_status = "✅" if detail['storage_success'] else "❌"
        ratio_status = "✅" if detail['ratio_success'] else "❌"
        success_rate = f"{detail['success_rate']:.1%}" if detail['fundamental_success'] else "N/A"
        time_taken = f"{detail['time_taken']:.1f}s"
        
        print(f"{detail['ticker']:<6} {fund_status:<5} {store_status:<5} {ratio_status:<5} {success_rate:<8} {time_taken:<6}")
    
    print(f"\n✅ Test completed successfully!")
    
    # Close connections
    try:
        manager.close()
        db.close()
    except:
        pass

if __name__ == "__main__":
    test_specific_tickers() 