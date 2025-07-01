import os
import psycopg2
import pandas as pd
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

OUTPUT_CSV = '../pre_filled_stocks/all_db_tickers.csv'

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute('SELECT ticker FROM stocks ORDER BY ticker')
    tickers = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    df = pd.DataFrame({'ticker': tickers, 'logo_url': [''] * len(tickers)})
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Exported {len(tickers)} tickers to {OUTPUT_CSV}")

if __name__ == '__main__':
    main() 