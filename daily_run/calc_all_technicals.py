import os
import psycopg2
import subprocess
from dotenv import load_dotenv

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

def run_calc_technicals(table, ticker_col, ticker):
    cmd = [
        'python', '-m', 'daily_run.calc_technicals',
        '--table', table,
        '--ticker_col', ticker_col,
        '--ticker', ticker
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip() + '\n' + result.stderr.strip()
    updated = False
    skipped = False
    if 'Successfully calculated and validated indicators' in output:
        updated = True
    elif 'Not enough data' in output:
        skipped = True
    print(f"{table} | {ticker}: {output}")
    return updated, skipped

if __name__ == "__main__":
    for entry in tables:
        table = entry['table']
        ticker_col = entry['ticker_col']
        print(f"Processing table: {table}")
        tickers = get_all_tickers(table, ticker_col)
        updated_count = 0
        skipped_count = 0
        for ticker in tickers:
            updated, skipped = run_calc_technicals(table, ticker_col, ticker)
            if updated:
                updated_count += 1
            elif skipped:
                skipped_count += 1
        print(f"SUMMARY for {table}: Updated: {updated_count}, Skipped (not enough data): {skipped_count}, Total: {len(tickers)}\n") 