import os
import psycopg2
from dotenv import load_dotenv
from datetime import date

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

tickers = ['AAPL', 'MSFT', 'AMZN', 'TSLA', 'NVDA']
today = date.today().isoformat()

def check_prices():
    try:
        print("\nDatabase connection info:")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Port: {DB_CONFIG['port']}")
        print(f"Database: {DB_CONFIG['dbname']}")
        print(f"User: {DB_CONFIG['user']}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print(f"Checking daily_charts for {tickers} on {today}...")
        for ticker in tickers:
            cur.execute("""
                SELECT ticker, date, open, high, low, close, volume
                FROM daily_charts
                WHERE ticker = %s AND date = %s
            """, (ticker, today))
            row = cur.fetchone()
            if row:
                print(f"Found: {row}")
            else:
                print(f"Not found: {ticker}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_prices() 