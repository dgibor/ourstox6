#!/usr/bin/env python3
"""
Check the actual fundamental data values in the database for specific tickers
"""

from database import DatabaseManager

def check_actual_fundamental_data(tickers):
    print(f"Checking actual fundamental data for: {tickers}")
    print("=" * 60)
    
    db = DatabaseManager()
    db.connect()
    
    # Check stocks table fundamental columns
    print("1. Stocks table fundamental data:")
    print("-" * 40)
    
    stocks_query = """
    SELECT ticker, market_cap, revenue_ttm, net_income_ttm, total_debt, 
           shareholders_equity, shares_outstanding, diluted_eps_ttm, book_value_per_share
    FROM stocks 
    WHERE ticker = ANY(%s)
    ORDER BY ticker
    """
    
    try:
        results = db.execute_query(stocks_query, (tickers,))
        if results:
            print("Ticker | Market Cap | Revenue TTM | Net Income TTM | Total Debt | Equity | Shares | EPS | Book Value")
            print("-" * 100)
            for row in results:
                ticker, market_cap, revenue_ttm, net_income_ttm, total_debt, equity, shares, eps, book_value = row
                print(f"{ticker:6} | {market_cap:>11} | {revenue_ttm:>12} | {net_income_ttm:>14} | {total_debt:>10} | {equity:>7} | {shares:>6} | {eps:>3} | {book_value:>10}")
        else:
            print("No records found in stocks table.")
    except Exception as e:
        print(f"Error querying stocks table: {e}")
    
    # Check company_fundamentals table
    print(f"\n2. Company_fundamentals table data:")
    print("-" * 40)
    
    cf_query = """
    SELECT ticker, report_date, period_type, revenue, net_income, ebitda, eps_diluted, data_source
    FROM company_fundamentals 
    WHERE ticker = ANY(%s)
    ORDER BY ticker, report_date DESC
    """
    
    try:
        results = db.execute_query(cf_query, (tickers,))
        if results:
            print("Ticker | Report Date | Period | Revenue | Net Income | EBITDA | EPS | Source")
            print("-" * 80)
            for row in results:
                ticker, report_date, period_type, revenue, net_income, ebitda, eps_diluted, data_source = row
                print(f"{ticker:6} | {report_date} | {period_type:6} | {revenue:>8} | {net_income:>11} | {ebitda:>6} | {eps_diluted:>3} | {data_source}")
        else:
            print("No records found in company_fundamentals table.")
    except Exception as e:
        print(f"Error querying company_fundamentals table: {e}")
    
    # Check if tickers exist in stocks table at all
    print(f"\n3. Checking if tickers exist in stocks table:")
    print("-" * 40)
    
    existence_query = """
    SELECT ticker, close, volume, date
    FROM stocks 
    WHERE ticker = ANY(%s)
    ORDER BY ticker
    """
    
    try:
        results = db.execute_query(existence_query, (tickers,))
        if results:
            print("Ticker | Close | Volume | Date")
            print("-" * 30)
            for row in results:
                ticker, close, volume, date = row
                print(f"{ticker:6} | {close:>5} | {volume:>6} | {date}")
        else:
            print("No records found in stocks table.")
    except Exception as e:
        print(f"Error querying stocks table: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    tickers = ['GME', 'AMC', 'BB', 'NOK', 'HOOD', 'DJT', 'AMD', 'INTC', 'QCOM', 'MU']
    check_actual_fundamental_data(tickers) 