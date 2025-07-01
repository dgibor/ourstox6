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

# Batch CSV file paths
BATCH_FILES = [
    '../pre_filled_stocks/batch1.csv',
    '../pre_filled_stocks/batch2.csv',
    '../pre_filled_stocks/batch3.csv',
    '../pre_filled_stocks/batch4.csv'
]

def upload_batch_csvs():
    """Upload all four batch CSV files to the stocks table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    total_inserted = 0
    total_updated = 0
    
    try:
        for batch_file in BATCH_FILES:
            print(f"\n📁 Processing {batch_file}...")
            
            if not os.path.exists(batch_file):
                print(f"⚠️  File not found: {batch_file}")
                continue
            
            # Read CSV file with error handling for bad lines
            try:
                df = pd.read_csv(batch_file, on_bad_lines='skip')
                print(f"   Found {len(df)} records (problematic lines skipped)")
            except Exception as e:
                print(f"   ❌ Error reading {batch_file}: {e}")
                continue
            
            # Clean and prepare data
            df = df.fillna('')
            
            # Process each record
            for _, row in df.iterrows():
                ticker = str(row['Ticker']).strip()
                company_name = str(row['Company Name']).strip()
                industry = str(row['Industry']).strip()
                sector = str(row['Sector']).strip()
                # Ensure market_cap_b is a float or None
                try:
                    market_cap_b = float(row['Market Cap (B)']) if str(row['Market Cap (B)']).strip() not in ('', 'nan', 'None') else None
                except Exception:
                    market_cap_b = None
                description = str(row['Description']).strip()
                business_model = str(row['Business_Model']).strip()
                products_services = str(row['Products_Services']).strip()
                main_customers = str(row['Main_Customers']).strip()
                markets = str(row['Markets']).strip()
                moat = str(row['Moat']).strip()
                peer_a = str(row['Peer A']).strip()
                peer_b = str(row['Peer B']).strip()
                peer_c = str(row['Peer C']).strip()
                
                try:
                    # Check if ticker already exists
                    cur.execute("SELECT id FROM stocks WHERE ticker = %s", (ticker,))
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing record
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
                        # Insert new record
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
                    print(f"   ⚠️  Skipping ticker {ticker} due to error: {row_e}")
                    conn.rollback()
                    continue
            
            print(f"   ✅ Completed {batch_file}")
        
        conn.commit()
        print(f"\n🎉 Upload completed successfully!")
        print(f"   📊 Total records inserted: {total_inserted}")
        print(f"   📊 Total records updated: {total_updated}")
        print(f"   📊 Total records processed: {total_inserted + total_updated}")
        
        # Verify final count
        cur.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cur.fetchone()[0]
        print(f"   📊 Total stocks in database: {total_stocks}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error uploading batch files: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    upload_batch_csvs() 