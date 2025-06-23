#!/usr/bin/env python3
"""
Test Daily Fundamentals Updater
"""

from daily_fundamentals_updater import DailyFundamentalsUpdater
from database import DatabaseManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_fundamentals_updater():
    print("Testing Daily Fundamentals Updater")
    print("=" * 50)
    
    updater = DailyFundamentalsUpdater()
    
    try:
        # Test 1: Get tickers needing updates
        print("\n1. Testing ticker identification...")
        tickers_needing_updates = updater.get_tickers_needing_updates()
        
        print(f"Found {len(tickers_needing_updates)} tickers needing updates:")
        for ticker_info in tickers_needing_updates[:5]:  # Show first 5
            print(f"  {ticker_info['ticker']}: {', '.join(ticker_info['reasons'])}")
        
        if len(tickers_needing_updates) > 5:
            print(f"  ... and {len(tickers_needing_updates) - 5} more")
        
        # Test 2: Run a small update (limit to 3 tickers)
        if tickers_needing_updates:
            print(f"\n2. Testing update for first 3 tickers...")
            test_tickers = tickers_needing_updates[:3]
            
            for ticker_info in test_tickers:
                ticker = ticker_info['ticker']
                reasons = ticker_info['reasons']
                
                print(f"\nUpdating {ticker}...")
                success = updater.update_ticker_fundamentals(ticker, reasons)
                print(f"Result: {'✅ Success' if success else '❌ Failed'}")
        
        # Test 3: Check database state after updates
        print(f"\n3. Checking database state...")
        check_database_state()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        updater.close()

def check_database_state():
    """Check the current state of fundamental data in database"""
    db = DatabaseManager()
    db.connect()
    
    try:
        # Get sample of tickers with their fundamental data
        query = """
        SELECT 
            ticker,
            shares_outstanding,
            next_earnings_date,
            market_cap,
            revenue_ttm,
            net_income_ttm,
            total_assets,
            total_debt
        FROM stocks 
        ORDER BY ticker 
        LIMIT 5
        """
        
        results = db.execute_query(query)
        
        print("Sample fundamental data:")
        print("-" * 40)
        for row in results:
            ticker, shares_out, earnings_date, market_cap, revenue, net_income, total_assets, total_debt = row
            
            print(f"\n{ticker}:")
            print(f"  Shares Outstanding: {shares_out:,.0f}" if shares_out else "  Shares Outstanding: NULL")
            print(f"  Next Earnings: {earnings_date}")
            print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: NULL")
            print(f"  Revenue TTM: ${revenue:,.0f}" if revenue else "  Revenue TTM: NULL")
            print(f"  Net Income TTM: ${net_income:,.0f}" if net_income else "  Net Income TTM: NULL")
            print(f"  Total Assets: ${total_assets:,.0f}" if total_assets else "  Total Assets: NULL")
            print(f"  Total Debt: ${total_debt:,.0f}" if total_debt else "  Total Debt: NULL")
            
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    test_fundamentals_updater() 