import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def check_adx_coverage():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get all tickers
        cur.execute("SELECT DISTINCT ticker FROM daily_charts")
        all_tickers = [row[0] for row in cur.fetchall()]
        
        # Get tickers with ADX calculated (not null for the latest date)
        cur.execute("""
            SELECT ticker FROM daily_charts dc1
            WHERE date = (
                SELECT MAX(date) FROM daily_charts dc2 WHERE dc2.ticker = dc1.ticker
            ) AND adx_14 IS NOT NULL
        """)
        adx_tickers = set(row[0] for row in cur.fetchall())
        
        calculated = list(adx_tickers)
        missed = [t for t in all_tickers if t not in adx_tickers]
        
        print(f"Total tickers: {len(all_tickers)}")
        print(f"Tickers with ADX: {len(calculated)}")
        print(f"Tickers missing ADX: {len(missed)}")
        
        # For each missed ticker, check if there is sufficient data
        missed_with_data = []
        missed_without_data = []
        for ticker in missed:
            cur.execute("SELECT COUNT(*) FROM daily_charts WHERE ticker = %s", (ticker,))
            count = cur.fetchone()[0]
            if count >= 28:
                missed_with_data.append((ticker, count))
            else:
                missed_without_data.append((ticker, count))
        
        print(f"\nMissed with sufficient data (>=28 rows): {len(missed_with_data)}")
        for t, c in missed_with_data[:20]:
            print(f"{t}: {c} rows")
        if len(missed_with_data) > 20:
            print(f"...and {len(missed_with_data)-20} more")
        
        print(f"\nMissed with insufficient data (<28 rows): {len(missed_without_data)}")
        for t, c in missed_without_data[:20]:
            print(f"{t}: {c} rows")
        if len(missed_without_data) > 20:
            print(f"...and {len(missed_without_data)-20} more")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_adx_coverage() 