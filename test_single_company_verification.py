#!/usr/bin/env python3
"""
Quick test to verify the complete system works for one company
"""

import sys
sys.path.insert(0, 'daily_run')

from enhanced_multi_service_fundamental_manager import EnhancedMultiServiceFundamentalManager
from calculate_fundamental_ratios import DailyFundamentalRatioCalculator
from database import DatabaseManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_company():
    """Test the complete system for one company"""
    print("🧪 TESTING COMPLETE SYSTEM FOR ONE COMPANY")
    print("=" * 60)
    
    manager = EnhancedMultiServiceFundamentalManager()
    db = DatabaseManager()
    ratio_calculator = DailyFundamentalRatioCalculator(db)
    
    ticker = "MSFT"
    
    try:
        # Step 1: Get fundamental data
        print(f"\n📊 Getting fundamental data for {ticker}...")
        result = manager.get_fundamental_data_with_fallback(ticker)
        
        if result and result.data:
            print(f"✅ Fundamental data: {len(result.data)}/16 fields collected")
            print(f"   Success rate: {result.success_rate:.1%}")
            print(f"   Primary source: {result.primary_source}")
            print(f"   Fallback sources: {result.fallback_sources_used}")
            
            # Step 2: Store data
            print(f"\n💾 Storing fundamental data...")
            storage_success = manager.store_fundamental_data(result)
            print(f"✅ Storage: {'Success' if storage_success else 'Failed'}")
            
            # Step 3: Calculate ratios
            print(f"\n🧮 Calculating ratios...")
            companies = ratio_calculator.get_companies_needing_ratio_updates()
            target_company = next((c for c in companies if c['ticker'] == ticker), None)
            
            if target_company:
                ratio_success = ratio_calculator.calculate_ratios_for_company(target_company)
                print(f"✅ Ratio calculation: {'Success' if ratio_success else 'Failed'}")
                
                # Step 4: Verify ratios
                print(f"\n🔍 Verifying ratios...")
                ratio_data = get_ratio_data(ticker, db)
                if ratio_data:
                    print(f"✅ Ratio verification: {len(ratio_data)} ratios found")
                    print("Sample ratios:")
                    for i, (ratio_name, value) in enumerate(ratio_data.items()):
                        if i >= 5:  # Show first 5 ratios
                            break
                        print(f"   • {ratio_name}: {value}")
                else:
                    print("⚠️ No ratios found")
            else:
                print("⚠️ Company not found in ratio update list")
        else:
            print("❌ Failed to get fundamental data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.close()

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

if __name__ == "__main__":
    test_single_company() 