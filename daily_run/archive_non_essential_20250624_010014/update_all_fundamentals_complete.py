#!/usr/bin/env python3
"""
Update all fundamental data for the 10 tickers with complete column coverage
"""

from fmp_service import FMPService
from database import DatabaseManager
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_all_fundamentals_complete(tickers):
    print(f"Updating all fundamental data for: {tickers}")
    print("=" * 80)
    
    fmp_service = FMPService()
    updated = []
    failed = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # Check current state
            db = DatabaseManager()
            db.connect()
            
            # Check how many fundamental columns are filled
            fundamental_columns = [
                'market_cap', 'revenue_ttm', 'net_income_ttm', 'total_assets', 'total_debt',
                'shareholders_equity', 'current_assets', 'current_liabilities', 'operating_income',
                'cash_and_equivalents', 'free_cash_flow', 'shares_outstanding', 'diluted_eps_ttm',
                'book_value_per_share', 'ebitda_ttm', 'enterprise_value'
            ]
            
            columns_str = ', '.join(fundamental_columns)
            before_query = f"SELECT {columns_str} FROM stocks WHERE ticker = %s"
            before_result = db.execute_query(before_query, (ticker,))
            db.disconnect()
            
            if before_result:
                before_data = before_result[0]
                filled_before = sum(1 for val in before_data if val is not None)
                print(f"  Before: {filled_before}/{len(fundamental_columns)} columns filled")
            
            # Update with FMP service
            result = fmp_service.get_fundamental_data(ticker)
            
            if result:
                # Check final state
                db = DatabaseManager()
                db.connect()
                after_result = db.execute_query(before_query, (ticker,))
                db.disconnect()
                
                if after_result:
                    after_data = after_result[0]
                    filled_after = sum(1 for val in after_data if val is not None)
                    print(f"  After:  {filled_after}/{len(fundamental_columns)} columns filled")
                    
                    if filled_after > filled_before:
                        updated.append(ticker)
                        print(f"  ✅ {ticker} updated successfully (+{filled_after - filled_before} columns)")
                    else:
                        failed.append(ticker)
                        print(f"  ⚠️  {ticker} no improvement")
                else:
                    failed.append(ticker)
                    print(f"  ❌ {ticker} not found in database after update")
            else:
                failed.append(ticker)
                print(f"  ❌ {ticker} no data fetched")
                
        except Exception as e:
            failed.append(ticker)
            print(f"  ❌ {ticker} error: {e}")
        
        # Rate limiting between requests
        if i < len(tickers):
            time.sleep(1)
    
    fmp_service.close()
    
    print(f"\n{'='*80}")
    print("FINAL SUMMARY:")
    print(f"✅ Updated: {len(updated)} tickers")
    print(f"❌ Failed: {len(failed)} tickers")
    
    if updated:
        print(f"✅ Successfully updated: {updated}")
    if failed:
        print(f"❌ Failed tickers: {failed}")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    update_all_fundamentals_complete(tickers) 