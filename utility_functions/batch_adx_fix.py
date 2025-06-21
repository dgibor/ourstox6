import os
import psycopg2
import subprocess
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

def get_tickers_to_fix(limit=100):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute('''
        SELECT ticker FROM daily_charts dc1
        WHERE date = (
            SELECT MAX(date) FROM daily_charts dc2 WHERE dc2.ticker = dc1.ticker
        ) AND adx_14 IS NULL
    ''')
    missed = [row[0] for row in cur.fetchall()]
    tickers = []
    for ticker in missed:
        cur.execute('SELECT COUNT(*) FROM daily_charts WHERE ticker = %s', (ticker,))
        count = cur.fetchone()[0]
        if count >= 28:
            tickers.append(ticker)
        if len(tickers) >= limit:
            break
    cur.close()
    conn.close()
    return tickers

def main():
    tickers = get_tickers_to_fix(100)
    print(f"Running ADX calculation for {len(tickers)} tickers...")
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}] {ticker}")
        result = subprocess.run([
            "python", "daily_run/calc_technicals.py",
            "--table", "daily_charts",
            "--ticker", ticker
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error for {ticker}: {result.stderr}")
        elif "Not enough data" in result.stdout or "No price data found" in result.stdout:
            print(f"Skipped {ticker} (not enough data)")
        else:
            print(f"Calculated for {ticker}")

if __name__ == "__main__":
    main() 