import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def print_industries_etfs():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT etf_ticker, sector, industry, etf_name
        FROM industries
        ORDER BY etf_ticker;
    """)
    rows = cur.fetchall()
    print(f"{'etf_ticker':<10} | {'sector':<25} | {'industry':<30} | {'etf_name'}")
    print('-'*90)
    for row in rows:
        print(f"{row[0]:<10} | {row[1]:<25} | {row[2]:<30} | {row[3]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    print_industries_etfs() 