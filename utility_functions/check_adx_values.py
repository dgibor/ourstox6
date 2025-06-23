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

def check_adx_values():
    tickers = ['NVDA', 'MSFT', 'XOM', 'AAPL', 'SOFI', 'AAL']
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        for ticker in tickers:
            print(f"\n--- {ticker} ---")
            cur.execute("""
                SELECT date, adx_14, close 
                FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 3
            """, (ticker,))
            
            rows = cur.fetchall()
            if rows:
                for row in rows:
                    date, adx, close = row
                    close_price = close / 100.0 if close else None
                    adx_value = adx / 100.0 if adx else None
                    close_str = f"${close_price:.2f}" if close_price else "None"
                    adx_str = f"{adx_value:.2f}" if adx_value else "None"
                    print(f"Date: {date}, Close: {close_str}, ADX: {adx_str}")
            else:
                print(f"No data found for {ticker}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_adx_values() 