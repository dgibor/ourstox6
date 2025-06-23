#!/usr/bin/env python3
"""
Check missing data: shares_outstanding and next_earnings_date
"""

from database import DatabaseManager

def check_missing_data(tickers):
    print(f"Checking missing data for: {tickers}")
    print("=" * 60)
    
    db = DatabaseManager()
    db.connect()
    
    # Check shares_outstanding and next_earnings_date
    query = """
    SELECT ticker, shares_outstanding, next_earnings_date, market_cap, current_price
    FROM stocks 
    WHERE ticker = ANY(%s)
    ORDER BY ticker
    """
    
    try:
        results = db.execute_query(query, (tickers,))
        if results:
            print("Current state:")
            print("-" * 60)
            for row in results:
                ticker, shares_outstanding, next_earnings_date, market_cap, current_price = row
                print(f"\n{ticker}:")
                print(f"  Shares Outstanding: {shares_outstanding}")
                print(f"  Next Earnings Date: {next_earnings_date}")
                print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: NULL")
                print(f"  Current Price: ${current_price/100:.2f}" if current_price else "  Current Price: NULL")
                
                # Calculate what shares_outstanding should be
                if market_cap and current_price and current_price > 0:
                    calculated_shares = market_cap / (current_price / 100)
                    print(f"  Calculated Shares: {calculated_shares:,.0f}")
        else:
            print("No records found")
    except Exception as e:
        print(f"Error querying data: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    check_missing_data(tickers) 