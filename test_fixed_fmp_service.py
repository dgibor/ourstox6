#!/usr/bin/env python3
"""
Test the fixed FMP service with a single company
"""

import sys
sys.path.insert(0, 'daily_run')

from config import Config
from database import DatabaseManager
from fmp_service import FMPService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_fmp_service():
    """Test the fixed FMP service"""
    print("🧪 TESTING FIXED FMP SERVICE")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        fmp_service = FMPService()
        
        # Test with a company that had missing data
        test_ticker = "AAON"
        
        print(f"\n📊 Testing with: {test_ticker}")
        print("-" * 40)
        
        # 1. Check before state
        print("1. BEFORE STATE:")
        before_query = """
        SELECT 
            shares_outstanding,
            cost_of_goods_sold,
            current_assets,
            current_liabilities,
            revenue,
            net_income,
            last_updated
        FROM company_fundamentals 
        WHERE ticker = %s
        """
        
        before_data = db.fetch_one(before_query, (test_ticker,))
        
        if before_data:
            shares_out, cogs, curr_assets, curr_liab, revenue, net_income, last_updated = before_data
            print(f"  Shares outstanding: {shares_out or 'NULL'}")
            print(f"  Cost of goods sold: {cogs or 'NULL'}")
            print(f"  Current assets: {curr_assets or 'NULL'}")
            print(f"  Current liabilities: {curr_liab or 'NULL'}")
            print(f"  Revenue: ${revenue or 0:,.0f}")
            print(f"  Net income: ${net_income or 0:,.0f}")
            print(f"  Last updated: {last_updated}")
        
        # 2. Run FMP service
        print(f"\n2. RUNNING FMP SERVICE:")
        print("-" * 40)
        
        result = fmp_service.get_fundamental_data(test_ticker)
        
        if result:
            print("✅ FMP service completed successfully")
            
            financial_data = result.get('financial_data', {})
            key_stats = result.get('key_stats', {})
            
            if financial_data:
                income = financial_data.get('income_statement', {})
                balance = financial_data.get('balance_sheet', {})
                cash_flow = financial_data.get('cash_flow', {})
                
                print(f"  Revenue: ${income.get('revenue', 0):,.0f}")
                print(f"  Cost of goods sold: ${income.get('cost_of_goods_sold', 0):,.0f}")
                print(f"  Current assets: ${balance.get('current_assets', 0):,.0f}")
                print(f"  Current liabilities: ${balance.get('current_liabilities', 0):,.0f}")
            
            if key_stats:
                market_data = key_stats.get('market_data', {})
                print(f"  Shares outstanding: {market_data.get('shares_outstanding', 0):,.0f}")
        else:
            print("❌ FMP service failed")
            return
        
        # 3. Check after state
        print(f"\n3. AFTER STATE:")
        print("-" * 40)
        
        after_data = db.fetch_one(before_query, (test_ticker,))
        
        if after_data:
            shares_out, cogs, curr_assets, curr_liab, revenue, net_income, last_updated = after_data
            print(f"  Shares outstanding: {shares_out or 'NULL'}")
            print(f"  Cost of goods sold: {cogs or 'NULL'}")
            print(f"  Current assets: {curr_assets or 'NULL'}")
            print(f"  Current liabilities: {curr_liab or 'NULL'}")
            print(f"  Revenue: ${revenue or 0:,.0f}")
            print(f"  Net income: ${net_income or 0:,.0f}")
            print(f"  Last updated: {last_updated}")
        
        # 4. Test ratio calculation
        print(f"\n4. TESTING RATIO CALCULATION:")
        print("-" * 40)
        
        try:
            from daily_run.calculate_fundamental_ratios import DailyFundamentalRatioCalculator
            calculator = DailyFundamentalRatioCalculator(db)
            
            # Get companies needing updates
            companies = calculator.get_companies_needing_ratio_updates()
            
            if companies:
                test_company = next((c for c in companies if c['ticker'] == test_ticker), None)
                if test_company:
                    print(f"✅ {test_ticker} found in companies needing ratio updates")
                    print(f"  Current price: ${test_company.get('current_price', 0):.2f}")
                    print(f"  Last ratio calculation: {test_company.get('last_ratio_calculation')}")
                else:
                    print(f"⚠️ {test_ticker} not found in companies needing ratio updates")
            else:
                print("⚠️ No companies found needing ratio updates")
                
        except Exception as e:
            print(f"❌ Error testing ratio calculation: {e}")
        
        fmp_service.close()
        
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing fixed FMP service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_fmp_service() 