import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

BATCH_FILES = [
    '../pre_filled_stocks/batch1.csv',
    '../pre_filled_stocks/batch2.csv',
    '../pre_filled_stocks/batch3.csv',
    '../pre_filled_stocks/batch4.csv'
]

TICKER_MAXLEN = 20  # DB schema limit

def clean_ticker(ticker):
    if not isinstance(ticker, str):
        ticker = str(ticker)
    ticker = ticker.strip().upper()
    if not ticker or ticker == 'TICKER':
        return None, 'empty or header'
    if len(ticker) > TICKER_MAXLEN:
        return ticker[:TICKER_MAXLEN], 'truncated'
    return ticker, None

def safe_str(val):
    if pd.isna(val):
        return ''
    return str(val).strip()

def safe_float(val):
    try:
        return float(val)
    except Exception:
        return None

def upload_batch_csvs_max_insert():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    total_inserted = 0
    total_updated = 0
    total_skipped = 0
    try:
        for batch_file in BATCH_FILES:
            print(f"\n📁 Processing {batch_file}...")
            if not os.path.exists(batch_file):
                print(f"⚠️  File not found: {batch_file}")
                continue
            try:
                df = pd.read_csv(batch_file, on_bad_lines='skip')
                print(f"   Found {len(df)} records (problematic lines skipped)")
            except Exception as e:
                print(f"   ❌ Error reading {batch_file}: {e}")
                continue
            df = df.fillna('')
            for idx, row in df.iterrows():
                ticker, ticker_warn = clean_ticker(row.get('Ticker', ''))
                if not ticker:
                    total_skipped += 1
                    continue
                company_name = safe_str(row.get('Company Name', ''))
                industry = safe_str(row.get('Industry', ''))
                sector = safe_str(row.get('Sector', ''))
                market_cap_b = safe_float(row.get('Market Cap (B)', None))
                description = safe_str(row.get('Description', ''))
                business_model = safe_str(row.get('Business_Model', ''))
                products_services = safe_str(row.get('Products_Services', ''))
                main_customers = safe_str(row.get('Main_Customers', ''))
                markets = safe_str(row.get('Markets', ''))
                moat = safe_str(row.get('Moat', ''))
                peer_a = safe_str(row.get('Peer A', ''))
                peer_b = safe_str(row.get('Peer B', ''))
                peer_c = safe_str(row.get('Peer C', ''))
                if ticker_warn:
                    print(f"   ⚠️  Ticker '{row.get('Ticker', '')}' {ticker_warn} (using '{ticker}')")
                try:
                    cur.execute("SELECT id FROM stocks WHERE ticker = %s", (ticker,))
                    existing = cur.fetchone()
                    if existing:
                        cur.execute("""
                            UPDATE stocks SET 
                                company_name = %s,
                                industry = %s,
                                sector = %s,
                                market_cap_b = %s,
                                description = %s,
                                business_model = %s,
                                products_services = %s,
                                main_customers = %s,
                                markets = %s,
                                moat = %s,
                                peer_a = %s,
                                peer_b = %s,
                                peer_c = %s,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE ticker = %s
                        """, (
                            company_name, industry, sector, market_cap_b, description,
                            business_model, products_services, main_customers, markets,
                            moat, peer_a, peer_b, peer_c, ticker
                        ))
                        total_updated += 1
                    else:
                        cur.execute("""
                            INSERT INTO stocks (
                                ticker, company_name, industry, sector, market_cap_b,
                                description, business_model, products_services, main_customers,
                                markets, moat, peer_a, peer_b, peer_c, last_updated
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (
                            ticker, company_name, industry, sector, market_cap_b,
                            description, business_model, products_services, main_customers,
                            markets, moat, peer_a, peer_b, peer_c
                        ))
                        total_inserted += 1
                except Exception as row_e:
                    print(f"   ⚠️  Skipping ticker {ticker} at row {idx+1} due to error: {row_e}")
                    conn.rollback()
                    total_skipped += 1
                    continue
            print(f"   ✅ Completed {batch_file}")
        conn.commit()
        print(f"\n🎉 Upload completed successfully!")
        print(f"   📊 Total records inserted: {total_inserted}")
        print(f"   📊 Total records updated: {total_updated}")
        print(f"   📊 Total records skipped: {total_skipped}")
        print(f"   📊 Total stocks in database: {get_total_stocks(cur)}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error uploading batch files: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def get_total_stocks(cur):
    cur.execute("SELECT COUNT(*) FROM stocks")
    return cur.fetchone()[0]

if __name__ == "__main__":
    upload_batch_csvs_max_insert() 