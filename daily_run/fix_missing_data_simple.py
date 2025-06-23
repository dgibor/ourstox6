#!/usr/bin/env python3
"""
Fix missing data: shares_outstanding and next_earnings_date (simplified)
"""

from database import DatabaseManager
from fmp_service import FMPService
import requests
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_missing_data_simple(tickers):
    print(f"Fixing missing data for: {tickers}")
    print("=" * 60)
    
    fmp_service = FMPService()
    db = DatabaseManager()
    db.connect()
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # Get key statistics which includes profile data
            print("  Fetching key statistics from FMP...")
            key_stats = fmp_service.fetch_key_statistics(ticker)
            
            if key_stats and 'market_data' in key_stats:
                market_data = key_stats['market_data']
                shares_outstanding = market_data.get('shares_outstanding')
                
                if shares_outstanding and shares_outstanding > 0:
                    print(f"  Shares Outstanding: {shares_outstanding:,.0f}")
                    
                    # Update shares_outstanding in database
                    update_query = "UPDATE stocks SET shares_outstanding = %s WHERE ticker = %s"
                    db.execute_update(update_query, (int(shares_outstanding), ticker))
                    print(f"  ✅ Updated shares_outstanding for {ticker}")
                else:
                    print(f"  ⚠️  No valid shares_outstanding data for {ticker}")
            
            # Get earnings calendar data using direct API call
            print("  Fetching earnings calendar data...")
            try:
                earnings_url = f"https://financialmodelingprep.com/api/v3/earning_calendar"
                params = {
                    'apikey': 'G8MrHbCaKkOG7BKncIAmdQOhoMFR0QFL',
                    'from': '2025-01-01',
                    'to': '2025-12-31'
                }
                
                response = requests.get(earnings_url, params=params, timeout=30)
                if response.status_code == 200:
                    earnings_data = response.json()
                    
                    # Find earnings for this ticker
                    ticker_earnings = [e for e in earnings_data if e.get('symbol') == ticker]
                    
                    if ticker_earnings:
                        next_earnings = ticker_earnings[0]
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
                else:
                    print(f"  ⚠️  Failed to fetch earnings calendar for {ticker}")
                    
            except Exception as e:
                print(f"  ⚠️  Error fetching earnings calendar for {ticker}: {e}")
                
        except Exception as e:
            print(f"  ❌ Error processing {ticker}: {e}")
        
        # Rate limiting
        if i < len(tickers):
            time.sleep(1)
    
    # Close connections
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
    fix_missing_data_simple(tickers)
    check_fixed_data(tickers) 