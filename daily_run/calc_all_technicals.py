import os
import psycopg2
import subprocess
from dotenv import load_dotenv
import requests
import traceback

PING_URL = "https://hc-ping.com/9a33c6a4-9478-4b2f-90e9-65f05bfd6d7f"

def send_healthcheck_report(success, summary):
    if success:
        requests.post(PING_URL, data=summary.encode("utf-8"))
    else:
        requests.post(PING_URL + "/fail", data=summary.encode("utf-8"))

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

tables = [
    {'table': 'market_data', 'ticker_col': 'ticker'},
    {'table': 'daily_charts', 'ticker_col': 'ticker'},
    {'table': 'sectors', 'ticker_col': 'ticker'}
]

def get_all_tickers(table, ticker_col):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT {ticker_col} FROM {table}")
    tickers = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return tickers

def main():
    summary_lines = []
    try:
        for entry in tables:
            table = entry['table']
            ticker_col = entry['ticker_col']
            tickers = get_all_tickers(table, ticker_col)  # Process all tickers
            updated = 0
            skipped = 0
            
            print(f"Processing {len(tickers)} tickers in {table}")
            
            for i, ticker in enumerate(tickers, 1):
                if i % 50 == 0:  # Progress update every 50 tickers
                    print(f"Progress: {i}/{len(tickers)} tickers processed")
                
                result = subprocess.run([
                    "python", "daily_run/calc_technicals.py",
                    "--table", table,
                    "--ticker_col", ticker_col,
                    "--ticker", str(ticker)
                ], capture_output=True, text=True)
                
                if "Not enough data" in result.stdout or "No price data found" in result.stdout:
                    skipped += 1
                elif result.returncode == 0:
                    updated += 1
                else:
                    print(f"Error processing {ticker}: {result.stderr}")
                    skipped += 1
            
            summary_lines.append(f"{table}: {updated} updated, {skipped} skipped (total: {len(tickers)})")
            print(f"Completed {table}: {updated} updated, {skipped} skipped")
        
        summary = "✅ Daily run complete:\n" + "\n".join(summary_lines)
        print(summary)
        send_healthcheck_report(True, summary)
    except Exception as e:
        tb = traceback.format_exc()
        summary = f"❌ Daily run failed: {e}\n\nTraceback:\n{tb}"
        print(summary)
        send_healthcheck_report(False, summary)
        raise

if __name__ == "__main__":
    main() 