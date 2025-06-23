#!/usr/bin/env python3
"""
Update fundamental data for a list of tickers with better error handling
"""

from service_factory import ServiceFactory
from database import DatabaseManager
import sys
import time

def update_fundamentals_for_tickers(tickers):
    print(f"Updating fundamentals for: {tickers}")
    print("=" * 60)
    
    factory = ServiceFactory()
    fundamental_service = factory.get_fundamental_service()
    updated = []
    failed = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # Check current state
            db = DatabaseManager()
            db.connect()
            stocks_query = "SELECT market_cap, revenue_ttm, net_income_ttm FROM stocks WHERE ticker = %s"
            before_result = db.execute_query(stocks_query, (ticker,))
            db.disconnect()
            
            if before_result:
                before_market_cap, before_revenue, before_income = before_result[0]
                print(f"  Before: MC=${before_market_cap}, Rev=${before_revenue}, NI=${before_income}")
            
            # Fetch and store data
            data = fundamental_service.get_fundamental_data_with_storage(ticker)
            
            if data:
                # Check state after storage
                db = DatabaseManager()
                db.connect()
                after_result = db.execute_query(stocks_query, (ticker,))
                db.disconnect()
                
                if after_result:
                    after_market_cap, after_revenue, after_income = after_result[0]
                    print(f"  After:  MC=${after_market_cap}, Rev=${after_revenue}, NI=${after_income}")
                    
                    # Check if data actually changed
                    if (before_market_cap != after_market_cap or 
                        before_revenue != after_revenue or 
                        before_income != after_income):
                        updated.append(ticker)
                        print(f"  ✅ {ticker} updated successfully")
                    else:
                        failed.append(ticker)
                        print(f"  ⚠️  {ticker} no change in data")
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
            time.sleep(2)
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"✅ Updated: {len(updated)} tickers")
    print(f"❌ Failed: {len(failed)} tickers")
    
    if updated:
        print(f"✅ Successfully updated: {updated}")
    if failed:
        print(f"❌ Failed tickers: {failed}")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    # Accept tickers as command line args or use a default list
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    update_fundamentals_for_tickers(tickers) 