#!/usr/bin/env python3
"""
Fix missing data using calculations and alternative sources
"""

from database import DatabaseManager
import requests
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_current_price_from_daily_charts(ticker):
    """Get current price from daily_charts table"""
    db = DatabaseManager()
    db.connect()
    
    try:
        query = """
        SELECT close FROM daily_charts 
        WHERE ticker = %s 
        ORDER BY date DESC 
        LIMIT 1
        """
        result = db.execute_query(query, (ticker,))
        if result:
            return result[0][0] / 100  # Convert from cents to dollars
        return None
    except Exception as e:
        print(f"Error getting price for {ticker}: {e}")
        return None
    finally:
        db.disconnect()

def calculate_shares_outstanding(market_cap, current_price):
    """Calculate shares outstanding from market cap and current price"""
    if market_cap and current_price and current_price > 0:
        return int(market_cap / current_price)
    return None

def fix_with_calculations(tickers):
    print(f"Fixing data with calculations for: {tickers}")
    print("=" * 60)
    
    db = DatabaseManager()
    db.connect()
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # Get current data from database
            query = "SELECT market_cap FROM stocks WHERE ticker = %s"
            result = db.execute_query(query, (ticker,))
            
            if result and result[0][0]:
                market_cap = result[0][0]
                print(f"  Market Cap: ${market_cap:,.0f}")
                
                # Get current price
                current_price = get_current_price_from_daily_charts(ticker)
                if current_price:
                    print(f"  Current Price: ${current_price:.2f}")
                    
                    # Calculate shares outstanding
                    shares_outstanding = calculate_shares_outstanding(market_cap, current_price)
                    if shares_outstanding:
                        print(f"  Calculated Shares Outstanding: {shares_outstanding:,.0f}")
                        
                        # Update shares_outstanding in database
                        update_query = "UPDATE stocks SET shares_outstanding = %s WHERE ticker = %s"
                        db.execute_update(update_query, (shares_outstanding, ticker))
                        print(f"  ✅ Updated shares_outstanding for {ticker}")
                    else:
                        print(f"  ⚠️  Could not calculate shares_outstanding for {ticker}")
                else:
                    print(f"  ⚠️  No current price available for {ticker}")
            else:
                print(f"  ⚠️  No market cap data for {ticker}")
            
            # Try to get earnings date from Yahoo Finance API
            print("  Fetching earnings date...")
            try:
                # Use a simple approach - try to get from Yahoo Finance
                yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
                params = {
                    'interval': '1d',
                    'range': '1d'
                }
                
                response = requests.get(yahoo_url, params=params, timeout=10)
                if response.status_code == 200:
                    # For now, let's set a placeholder date since earnings dates are complex
                    # In a real implementation, you'd parse the earnings calendar
                    print(f"  ⚠️  Earnings date lookup not implemented yet for {ticker}")
                else:
                    print(f"  ⚠️  Could not fetch data for {ticker}")
                    
            except Exception as e:
                print(f"  ⚠️  Error fetching earnings data for {ticker}: {e}")
                
        except Exception as e:
            print(f"  ❌ Error processing {ticker}: {e}")
        
        # Rate limiting
        if i < len(tickers):
            time.sleep(0.5)
    
    # Close connection
    db.disconnect()
    
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
    fix_with_calculations(tickers)
    check_fixed_data(tickers) 