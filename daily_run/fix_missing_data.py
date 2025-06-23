#!/usr/bin/env python3
"""
Fix missing data: shares_outstanding and next_earnings_date
"""

from database import DatabaseManager
from fmp_service import FMPService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_missing_data(tickers):
    print(f"Fixing missing data for: {tickers}")
    print("=" * 60)
    
    fmp_service = FMPService()
    db = DatabaseManager()
    db.connect()
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # Get current data from FMP
            print("  Fetching current data from FMP...")
            
            # Get profile data for shares outstanding
            profile_data = fmp_service.fetch_company_profile(ticker)
            
            if profile_data:
                shares_outstanding = profile_data.get('sharesOutstanding')
                if shares_outstanding and shares_outstanding > 0:
                    print(f"  Shares Outstanding: {shares_outstanding:,.0f}")
                    
                    # Update shares_outstanding in database
                    update_query = "UPDATE stocks SET shares_outstanding = %s WHERE ticker = %s"
                    db.execute_update(update_query, (int(shares_outstanding), ticker))
                    print(f"  ✅ Updated shares_outstanding for {ticker}")
                else:
                    print(f"  ⚠️  No valid shares_outstanding data for {ticker}")
            
            # Get earnings calendar data
            print("  Fetching earnings calendar data...")
            earnings_data = fmp_service.fetch_earnings_calendar(ticker)
            
            if earnings_data and len(earnings_data) > 0:
                next_earnings = earnings_data[0]
                earnings_date = next_earnings.get('date')
                if earnings_date:
                    print(f"  Next Earnings Date: {earnings_date}")
                    
                    # Update next_earnings_date in database
                    update_query = "UPDATE stocks SET next_earnings_date = %s WHERE ticker = %s"
                    db.execute_update(update_query, (earnings_date, ticker))
                    print(f"  ✅ Updated next_earnings_date for {ticker}")
                else:
                    print(f"  ⚠️  No valid earnings date for {ticker}")
            else:
                print(f"  ⚠️  No earnings calendar data for {ticker}")
                
        except Exception as e:
            print(f"  ❌ Error processing {ticker}: {e}")
        
        # Rate limiting
        if i < len(tickers):
            import time
            time.sleep(1)
    
    # Commit all changes
    db.commit()
    db.disconnect()
    fmp_service.close()
    
    print(f"\n{'='*60}")
    print("Fix completed!")

def check_fixed_data(tickers):
    print(f"\nChecking fixed data for: {tickers}")
    print("=" * 60)
    
    db = DatabaseManager()
    db.connect()
    
    query = """
    SELECT ticker, shares_outstanding, next_earnings_date, market_cap
    FROM stocks 
    WHERE ticker = ANY(%s)
    ORDER BY ticker
    """
    
    try:
        results = db.execute_query(query, (tickers,))
        if results:
            print("Updated data:")
            print("-" * 60)
            for row in results:
                ticker, shares_outstanding, next_earnings_date, market_cap = row
                print(f"\n{ticker}:")
                print(f"  Shares Outstanding: {shares_outstanding:,.0f}" if shares_outstanding else "  Shares Outstanding: NULL")
                print(f"  Next Earnings Date: {next_earnings_date}")
                print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: NULL")
        else:
            print("No records found")
    except Exception as e:
        print(f"Error querying data: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    fix_missing_data(tickers)
    check_fixed_data(tickers) 