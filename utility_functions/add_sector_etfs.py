import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SECTOR_ETFS = [
    {"etf_ticker": "XLC", "sector": "Communication Services", "industry": "Sector ETF", "etf_name": "Communication Services Select Sector SPDR Fund"},
    {"etf_ticker": "XLY", "sector": "Consumer Discretionary", "industry": "Sector ETF", "etf_name": "Consumer Discretionary Select Sector SPDR Fund"},
    {"etf_ticker": "XLP", "sector": "Consumer Staples", "industry": "Sector ETF", "etf_name": "Consumer Staples Select Sector SPDR Fund"},
    {"etf_ticker": "XLE", "sector": "Energy", "industry": "Sector ETF", "etf_name": "Energy Select Sector SPDR Fund"},
    {"etf_ticker": "XLF", "sector": "Financials", "industry": "Sector ETF", "etf_name": "Financial Select Sector SPDR Fund"},
    {"etf_ticker": "XLV", "sector": "Health Care", "industry": "Sector ETF", "etf_name": "Health Care Select Sector SPDR Fund"},
    {"etf_ticker": "XLI", "sector": "Industrials", "industry": "Sector ETF", "etf_name": "Industrial Select Sector SPDR Fund"},
    {"etf_ticker": "XLB", "sector": "Materials", "industry": "Sector ETF", "etf_name": "Materials Select Sector SPDR Fund"},
    {"etf_ticker": "XLRE", "sector": "Real Estate", "industry": "Sector ETF", "etf_name": "Real Estate Select Sector SPDR Fund"},
    {"etf_ticker": "XLK", "sector": "Information Technology", "industry": "Sector ETF", "etf_name": "Technology Select Sector SPDR Fund"},
    {"etf_ticker": "XLU", "sector": "Utilities", "industry": "Sector ETF", "etf_name": "Utilities Select Sector SPDR Fund"},
]

def add_sector_etfs():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    for etf in SECTOR_ETFS:
        cur.execute("""
            SELECT 1 FROM industries WHERE etf_ticker = %s AND sector = %s AND industry = %s
        """, (etf['etf_ticker'], etf['sector'], etf['industry']))
        if cur.fetchone():
            print(f"{etf['etf_ticker']} already exists, skipping.")
            continue
        cur.execute("""
            INSERT INTO industries (sector, industry, etf_name, etf_ticker)
            VALUES (%s, %s, %s, %s)
        """, (etf['sector'], etf['industry'], etf['etf_name'], etf['etf_ticker']))
        print(f"Added {etf['etf_ticker']} - {etf['etf_name']}")
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    add_sector_etfs() 