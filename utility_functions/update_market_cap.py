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

def update_market_cap():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    # Get all tickers and shares_outstanding
    cur.execute("SELECT ticker, shares_outstanding FROM stocks")
    stocks = cur.fetchall()
    updated = 0
    for ticker, shares in stocks:
        if not shares or shares == 0:
            continue
        # Get latest close price
        cur.execute("""
            SELECT close FROM daily_charts
            WHERE ticker = %s
            ORDER BY date DESC LIMIT 1
        """, (ticker,))
        row = cur.fetchone()
        if not row or row[0] is None:
            continue
        price = row[0]
        market_cap = price * shares
        cur.execute("UPDATE stocks SET market_cap = %s WHERE ticker = %s", (market_cap, ticker))
        updated += 1
    conn.commit()
    print(f"Updated market cap for {updated} stocks.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    update_market_cap() 