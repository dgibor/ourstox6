import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

cur = conn.cursor()
cur.execute("""
    SELECT ticker, diluted_eps_ttm, book_value_per_share, revenue_ttm, 
           ebitda_ttm, shareholders_equity, market_cap
    FROM stocks 
    WHERE ticker = 'AAPL'
""")

row = cur.fetchone()
if row:
    print("AAPL fundamental data:")
    print(f"  Ticker: {row[0]}")
    print(f"  Diluted EPS TTM: {row[1]}")
    print(f"  Book Value per Share: {row[2]}")
    print(f"  Revenue TTM: {row[3]}")
    print(f"  EBITDA TTM: {row[4]}")
    print(f"  Shareholders Equity: {row[5]}")
    print(f"  Market Cap: {row[6]}")
else:
    print("No data found for AAPL")

conn.close() 