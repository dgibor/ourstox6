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

def check_data_count():
    tickers = ['AAPL', 'MSFT', 'SOFI', 'XOM', 'AAL']
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        for ticker in tickers:
            print(f"\n--- {ticker} ---")
            cur.execute("""
                SELECT COUNT(*) as count, MIN(date), MAX(date)
                FROM daily_charts 
                WHERE ticker = %s
            """, (ticker,))
            
            row = cur.fetchone()
            if row:
                count, min_date, max_date = row
                print(f"Total rows: {count}")
                print(f"Date range: {min_date} to {max_date}")
                print(f"Days of data: {count}")
            else:
                print(f"No data found for {ticker}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data_count() 