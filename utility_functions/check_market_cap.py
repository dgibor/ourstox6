import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def check_market_cap_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Check AAPL specifically
    cur.execute("SELECT ticker, market_cap, shares_outstanding, fundamentals_last_update FROM stocks WHERE ticker = 'AAPL'")
    aapl_data = cur.fetchone()
    print(f"AAPL data: {aapl_data}")
    
    # Check all stocks with market cap
    cur.execute("SELECT ticker, market_cap FROM stocks WHERE market_cap IS NOT NULL")
    stocks_with_market_cap = cur.fetchall()
    print(f"Stocks with market cap: {len(stocks_with_market_cap)}")
    for stock in stocks_with_market_cap:
        print(f"  {stock[0]}: {stock[1]}")
    
    # Check stocks with market cap > 1M
    cur.execute("SELECT ticker, market_cap FROM stocks WHERE market_cap > 1000000")
    stocks_above_1m = cur.fetchall()
    print(f"Stocks with market cap > 1M: {len(stocks_above_1m)}")
    for stock in stocks_above_1m:
        print(f"  {stock[0]}: {stock[1]}")
    
    # Check stocks with no fundamentals_last_update
    cur.execute("SELECT COUNT(*) FROM stocks WHERE fundamentals_last_update IS NULL")
    no_fundamentals = cur.fetchone()[0]
    print(f"Stocks with no fundamentals_last_update: {no_fundamentals}")
    
    # Check the scheduler query
    cur.execute("""
        SELECT ticker, company_name, market_cap, next_earnings_date, fundamentals_last_update
        FROM stocks 
        WHERE fundamentals_last_update IS NULL
        AND market_cap > 100000
        ORDER BY market_cap DESC
        LIMIT 10
    """)
    scheduler_results = cur.fetchall()
    print(f"Scheduler query results: {len(scheduler_results)}")
    for result in scheduler_results:
        print(f"  {result}")
    
    # Check stocks with market cap > 100K
    cur.execute("SELECT COUNT(*) FROM stocks WHERE market_cap > 100000")
    stocks_above_100k = cur.fetchone()[0]
    print(f"Stocks with market cap > 100K: {stocks_above_100k}")
    
    # Check stocks with market cap > 100K and no fundamentals
    cur.execute("SELECT COUNT(*) FROM stocks WHERE market_cap > 100000 AND fundamentals_last_update IS NULL")
    stocks_above_100k_no_fundamentals = cur.fetchone()[0]
    print(f"Stocks with market cap > 100K and no fundamentals: {stocks_above_100k_no_fundamentals}")
    
    # Show a few stocks with no fundamentals
    cur.execute("SELECT ticker, market_cap, fundamentals_last_update FROM stocks WHERE fundamentals_last_update IS NULL LIMIT 5")
    no_fundamentals_stocks = cur.fetchall()
    print("Sample stocks with no fundamentals:")
    for stock in no_fundamentals_stocks:
        print(f"  {stock[0]}: market_cap={stock[1]}, fundamentals_last_update={stock[2]}")
    
    # Check shares_outstanding and market_cap for key tickers
    cur.execute("SELECT ticker, shares_outstanding, market_cap FROM stocks WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA')")
    key_tickers = cur.fetchall()
    print('Key tickers shares_outstanding and market_cap:')
    for row in key_tickers:
        print(f"  {row[0]}: shares_outstanding={row[1]}, market_cap={row[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_market_cap_data() 