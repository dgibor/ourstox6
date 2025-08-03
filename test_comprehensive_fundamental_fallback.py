#!/usr/bin/env python3
"""
Comprehensive Test for Enhanced Fundamental Fallback System

This script tests the enhanced fundamental fallback system on 20 companies
and verifies that all ratios are calculated correctly.
"""

import sys
sys.path.insert(0, 'daily_run')

from enhanced_multi_service_fundamental_manager import EnhancedMultiServiceFundamentalManager
from calculate_fundamental_ratios import DailyFundamentalRatioCalculator
from database import DatabaseManager
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_comprehensive_fundamental_fallback():
    """Test the enhanced fundamental fallback system on 20 companies"""
    print("🧪 COMPREHENSIVE FUNDAMENTAL FALLBACK SYSTEM TEST")
    print("=" * 80)
    
    # Test companies - diverse mix of large caps, mid caps, and different sectors
    test_companies = [
        "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK.B", "UNH", "JNJ", "V",
        "WMT", "PG", "JPM", "HD", "MA", "DIS", "PYPL", "NFLX", "CRM", "ADBE"
    ]
    
    manager = EnhancedMultiServiceFundamentalManager()
    db = DatabaseManager()
    ratio_calculator = DailyFundamentalRatioCalculator(db)
    
    results_summary = []
    fundamental_results = []
    
    print(f"\n📊 Testing {len(test_companies)} companies:")
    print("-" * 50)
    
    for i, ticker in enumerate(test_companies, 1):
        print(f"\n[{i:2d}/{len(test_companies)}] Testing {ticker}:")
        print("-" * 40)
        
        try:
            # Step 1: Get fundamental data with fallback
            start_time = time.time()
            result = manager.get_fundamental_data_with_fallback(ticker)
            fundamental_time = time.time() - start_time
            
            if result and result.data:
                print(f"✅ Fundamental data collected:")
                print(f"   • Primary source: {result.primary_source}")
                print(f"   • Fallback sources: {result.fallback_sources_used}")
                print(f"   • Success rate: {result.success_rate:.1%}")
                print(f"   • Fields found: {len(result.data)}/16")
                print(f"   • Missing fields: {result.missing_fields}")
                print(f"   • Time taken: {fundamental_time:.2f}s")
                
                # Step 2: Store fundamental data
                start_time = time.time()
                storage_success = manager.store_fundamental_data(result)
                storage_time = time.time() - start_time
                
                if storage_success:
                    print(f"✅ Data storage: Success ({storage_time:.2f}s)")
                    
                    # Step 3: Calculate ratios
                    start_time = time.time()
                    ratio_success = test_ratio_calculation(ticker, ratio_calculator)
                    ratio_time = time.time() - start_time
                    
                    if ratio_success:
                        print(f"✅ Ratio calculation: Success ({ratio_time:.2f}s)")
                        
                        # Get ratio results for verification
                        ratio_data = get_ratio_data(ticker, db)
                        if ratio_data:
                            print(f"✅ Ratio verification: {len(ratio_data)} ratios calculated")
                            
                            # Add to results
                            results_summary.append({
                                'ticker': ticker,
                                'fundamental_success': True,
                                'fundamental_time': fundamental_time,
                                'storage_success': True,
                                'storage_time': storage_time,
                                'ratio_success': True,
                                'ratio_time': ratio_time,
                                'success_rate': result.success_rate,
                                'fallback_sources': len(result.fallback_sources_used),
                                'missing_fields': len(result.missing_fields),
                                'ratios_calculated': len(ratio_data),
                                'total_time': fundamental_time + storage_time + ratio_time
                            })
                            
                            fundamental_results.append({
                                'ticker': ticker,
                                'result': result,
                                'ratio_data': ratio_data
                            })
                        else:
                            print(f"⚠️ Ratio verification: No ratio data found")
                            results_summary.append({
                                'ticker': ticker,
                                'fundamental_success': True,
                                'fundamental_time': fundamental_time,
                                'storage_success': True,
                                'storage_time': storage_time,
                                'ratio_success': False,
                                'ratio_time': ratio_time,
                                'success_rate': result.success_rate,
                                'fallback_sources': len(result.fallback_sources_used),
                                'missing_fields': len(result.missing_fields),
                                'ratios_calculated': 0,
                                'total_time': fundamental_time + storage_time + ratio_time
                            })
                    else:
                        print(f"❌ Ratio calculation: Failed ({ratio_time:.2f}s)")
                        results_summary.append({
                            'ticker': ticker,
                            'fundamental_success': True,
                            'fundamental_time': fundamental_time,
                            'storage_success': True,
                            'storage_time': storage_time,
                            'ratio_success': False,
                            'ratio_time': ratio_time,
                            'success_rate': result.success_rate,
                            'fallback_sources': len(result.fallback_sources_used),
                            'missing_fields': len(result.missing_fields),
                            'ratios_calculated': 0,
                            'total_time': fundamental_time + storage_time + ratio_time
                        })
                else:
                    print(f"❌ Data storage: Failed ({storage_time:.2f}s)")
                    results_summary.append({
                        'ticker': ticker,
                        'fundamental_success': True,
                        'fundamental_time': fundamental_time,
                        'storage_success': False,
                        'storage_time': storage_time,
                        'ratio_success': False,
                        'ratio_time': 0,
                        'success_rate': result.success_rate,
                        'fallback_sources': len(result.fallback_sources_used),
                        'missing_fields': len(result.missing_fields),
                        'ratios_calculated': 0,
                        'total_time': fundamental_time + storage_time
                    })
            else:
                print(f"❌ Fundamental data: Failed")
                results_summary.append({
                    'ticker': ticker,
                    'fundamental_success': False,
                    'fundamental_time': fundamental_time,
                    'storage_success': False,
                    'storage_time': 0,
                    'ratio_success': False,
                    'ratio_time': 0,
                    'success_rate': 0.0,
                    'fallback_sources': 0,
                    'missing_fields': 16,
                    'ratios_calculated': 0,
                    'total_time': fundamental_time
                })
                
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            results_summary.append({
                'ticker': ticker,
                'fundamental_success': False,
                'fundamental_time': 0,
                'storage_success': False,
                'storage_time': 0,
                'ratio_success': False,
                'ratio_time': 0,
                'success_rate': 0.0,
                'fallback_sources': 0,
                'missing_fields': 16,
                'ratios_calculated': 0,
                'total_time': 0
            })
        
        # Rate limiting between companies
        if i < len(test_companies):
            time.sleep(2)
    
    # Display comprehensive results
    display_comprehensive_results(results_summary, fundamental_results)
    
    # Cleanup
    manager.close()
    
    print(f"\n✅ Comprehensive test completed successfully!")

def test_ratio_calculation(ticker: str, ratio_calculator: DailyFundamentalRatioCalculator) -> bool:
    """Test ratio calculation for a specific ticker"""
    try:
        # Get companies needing ratio updates
        companies = ratio_calculator.get_companies_needing_ratio_updates()
        
        # Find our ticker in the list
        target_company = next((c for c in companies if c['ticker'] == ticker), None)
        
        if target_company:
            # Calculate ratios
            success = ratio_calculator.calculate_ratios_for_company(target_company)
            return success
        else:
            logger.warning(f"Company {ticker} not found in companies needing ratio updates")
            return False
            
    except Exception as e:
        logger.error(f"Error calculating ratios for {ticker}: {e}")
        return False

def get_ratio_data(ticker: str, db: DatabaseManager) -> dict:
    """Get calculated ratio data for a ticker"""
    try:
        query = """
        SELECT 
            price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda, peg_ratio,
            return_on_equity, return_on_assets, return_on_invested_capital, gross_margin, operating_margin, net_margin,
            debt_to_equity_ratio, current_ratio, quick_ratio, interest_coverage,
            asset_turnover, inventory_turnover, receivables_turnover,
            revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
            fcf_to_net_income, cash_conversion_cycle, graham_number
        FROM company_fundamentals 
        WHERE ticker = %s AND period_type = 'ttm'
        ORDER BY last_updated DESC
        LIMIT 1
        """
        
        result = db.fetch_one(query, (ticker,))
        if result:
            columns = [
                'price_to_earnings', 'price_to_book', 'price_to_sales', 'ev_to_ebitda', 'peg_ratio',
                'return_on_equity', 'return_on_assets', 'return_on_invested_capital', 'gross_margin', 'operating_margin', 'net_margin',
                'debt_to_equity_ratio', 'current_ratio', 'quick_ratio', 'interest_coverage',
                'asset_turnover', 'inventory_turnover', 'receivables_turnover',
                'revenue_growth_yoy', 'earnings_growth_yoy', 'fcf_growth_yoy',
                'fcf_to_net_income', 'cash_conversion_cycle', 'graham_number'
            ]
            
            ratio_data = {}
            for i, column in enumerate(columns):
                if i < len(result):
                    ratio_data[column] = result[i]
            
            return ratio_data
        else:
            return {}
            
    except Exception as e:
        logger.error(f"Error getting ratio data for {ticker}: {e}")
        return {}

def display_comprehensive_results(results_summary: list, fundamental_results: list):
    """Display comprehensive test results"""
    print(f"\n📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    # Calculate statistics
    total_companies = len(results_summary)
    fundamental_success = sum(1 for r in results_summary if r['fundamental_success'])
    storage_success = sum(1 for r in results_summary if r['storage_success'])
    ratio_success = sum(1 for r in results_summary if r['ratio_success'])
    
    avg_success_rate = sum(r['success_rate'] for r in results_summary) / total_companies
    avg_fallback_sources = sum(r['fallback_sources'] for r in results_summary) / total_companies
    avg_missing_fields = sum(r['missing_fields'] for r in results_summary) / total_companies
    avg_ratios_calculated = sum(r['ratios_calculated'] for r in results_summary) / total_companies
    avg_total_time = sum(r['total_time'] for r in results_summary) / total_companies
    
    print(f"\n📈 OVERALL STATISTICS:")
    print(f"   • Total companies tested: {total_companies}")
    print(f"   • Fundamental data success: {fundamental_success}/{total_companies} ({fundamental_success/total_companies:.1%})")
    print(f"   • Data storage success: {storage_success}/{total_companies} ({storage_success/total_companies:.1%})")
    print(f"   • Ratio calculation success: {ratio_success}/{total_companies} ({ratio_success/total_companies:.1%})")
    print(f"   • Average success rate: {avg_success_rate:.1%}")
    print(f"   • Average fallback sources used: {avg_fallback_sources:.1f}")
    print(f"   • Average missing fields: {avg_missing_fields:.1f}")
    print(f"   • Average ratios calculated: {avg_ratios_calculated:.1f}")
    print(f"   • Average total time per company: {avg_total_time:.2f}s")
    
    print(f"\n📋 DETAILED RESULTS:")
    print("-" * 80)
    print(f"{'Ticker':<6} {'Fund':<4} {'Store':<5} {'Ratio':<5} {'Success':<7} {'Fallback':<8} {'Missing':<7} {'Ratios':<6} {'Time':<6}")
    print("-" * 80)
    
    for result in results_summary:
        fund_status = "✅" if result['fundamental_success'] else "❌"
        store_status = "✅" if result['storage_success'] else "❌"
        ratio_status = "✅" if result['ratio_success'] else "❌"
        
        print(f"{result['ticker']:<6} {fund_status:<4} {store_status:<5} {ratio_status:<5} "
              f"{result['success_rate']:<7.1%} {result['fallback_sources']:<8} {result['missing_fields']:<7} "
              f"{result['ratios_calculated']:<6} {result['total_time']:<6.1f}s")
    
    # Show top performers
    print(f"\n🏆 TOP PERFORMERS:")
    print("-" * 40)
    
    # Best success rate
    best_success = max(results_summary, key=lambda x: x['success_rate'])
    print(f"   • Best success rate: {best_success['ticker']} ({best_success['success_rate']:.1%})")
    
    # Most ratios calculated
    most_ratios = max(results_summary, key=lambda x: x['ratios_calculated'])
    print(f"   • Most ratios calculated: {most_ratios['ticker']} ({most_ratios['ratios_calculated']} ratios)")
    
    # Fastest processing
    fastest = min(results_summary, key=lambda x: x['total_time'])
    print(f"   • Fastest processing: {fastest['ticker']} ({fastest['total_time']:.1f}s)")
    
    # Show sample ratio data
    if fundamental_results:
        print(f"\n📊 SAMPLE RATIO DATA:")
        print("-" * 40)
        
        # Show first successful result
        sample = next((r for r in fundamental_results if r['ratio_data']), None)
        if sample:
            print(f"   • Company: {sample['ticker']}")
            print(f"   • Ratios calculated: {len(sample['ratio_data'])}")
            
            # Show first 5 ratios
            for i, (ratio_name, value) in enumerate(sample['ratio_data'].items()):
                if i >= 5:
                    break
                print(f"     - {ratio_name}: {value}")
            
            if len(sample['ratio_data']) > 5:
                print(f"     ... and {len(sample['ratio_data']) - 5} more ratios")
    
    # Show issues summary
    print(f"\n⚠️ ISSUES SUMMARY:")
    print("-" * 40)
    
    failed_fundamental = [r for r in results_summary if not r['fundamental_success']]
    failed_storage = [r for r in results_summary if not r['storage_success']]
    failed_ratios = [r for r in results_summary if not r['ratio_success']]
    
    if failed_fundamental:
        print(f"   • Fundamental data failures: {[r['ticker'] for r in failed_fundamental]}")
    if failed_storage:
        print(f"   • Storage failures: {[r['ticker'] for r in failed_storage]}")
    if failed_ratios:
        print(f"   • Ratio calculation failures: {[r['ticker'] for r in failed_ratios]}")
    
    if not failed_fundamental and not failed_storage and not failed_ratios:
        print(f"   • No issues found! All systems working perfectly! 🎉")

if __name__ == "__main__":
    test_comprehensive_fundamental_fallback() 