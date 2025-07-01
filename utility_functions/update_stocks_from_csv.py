import os
import psycopg2
import pandas as pd
import yfinance as yf
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/update_stocks.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Paths
LOGOS_DIR = '../pre_filled_stocks/logos'
os.makedirs(LOGOS_DIR, exist_ok=True)

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(**DB_CONFIG)

def update_stocks_schema():
    """Add new columns to stocks table if they don't exist"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Add new columns for CSV data
        new_columns = [
            ('market_cap_b', 'numeric(10,2)'),
            ('description', 'text'),
            ('business_model', 'text'),
            ('products_services', 'text'),
            ('main_customers', 'text'),
            ('markets', 'text'),
            ('moat_1', 'text'),
            ('moat_2', 'text'),
            ('moat_3', 'text'),
            ('moat_4', 'text'),
            ('peer_a', 'text'),
            ('peer_b', 'text'),
            ('peer_c', 'text')
        ]
        
        for col_name, col_type in new_columns:
            cur.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='stocks' AND column_name='{col_name}'
                    ) THEN
                        ALTER TABLE stocks ADD COLUMN {col_name} {col_type};
                        RAISE NOTICE 'Added column % to stocks table', '{col_name}';
                    ELSE
                        RAISE NOTICE 'Column % already exists in stocks table', '{col_name}';
                    END IF;
                END$$;
            """)
        
        # Ensure unique constraint on ticker
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                    WHERE tc.table_name = 'stocks' AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'ticker'
                ) THEN
                    ALTER TABLE stocks ADD CONSTRAINT unique_ticker UNIQUE (ticker);
                    RAISE NOTICE 'Added unique constraint on ticker column';
                ELSE
                    RAISE NOTICE 'Unique constraint on ticker already exists';
                END IF;
            END$$;
        """)
        
        conn.commit()
        logging.info("✅ Stocks table schema updated successfully!")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"❌ Error updating schema: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def download_logo(ticker, logo_url=None):
    """Download company logo and save as PNG"""
    try:
        # Check if logo already exists
        logo_path = os.path.join(LOGOS_DIR, f"{ticker}.png")
        if os.path.exists(logo_path):
            logging.info(f"Logo already exists for {ticker}")
            return logo_path
        
        # If no logo URL provided, try to get from yfinance
        if not logo_url:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                logo_url = info.get('logo_url')
                if not logo_url:
                    # Try alternative method
                    logo_url = f"https://logo.clearbit.com/{ticker.lower()}.com"
            except Exception as e:
                logging.warning(f"Could not get logo URL for {ticker}: {e}")
                logo_url = f"https://logo.clearbit.com/{ticker.lower()}.com"
        
        # Download the logo
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(logo_url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(logo_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"✅ Downloaded logo for {ticker}")
            return logo_path
        else:
            logging.warning(f"Failed to download logo for {ticker}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"Error downloading logo for {ticker}: {e}")
        return None

def get_company_info_from_web(ticker):
    """Get additional company information from web sources"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract relevant information
        company_info = {
            'exchange': info.get('exchange', ''),
            'country': info.get('country', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'market_cap': info.get('marketCap', 0),
            'description': info.get('longBusinessSummary', ''),
            'logo_url': info.get('logo_url', '')
        }
        
        # Convert market cap to billions
        if company_info['market_cap']:
            company_info['market_cap_b'] = company_info['market_cap'] / 1_000_000_000
        else:
            company_info['market_cap_b'] = None
        
        return company_info
        
    except Exception as e:
        logging.warning(f"Could not get web info for {ticker}: {e}")
        return {}

def clean_market_cap(market_cap_str):
    """Convert market cap string to numeric value in billions"""
    if pd.isna(market_cap_str) or market_cap_str == '':
        return None
    
    try:
        # Remove any non-numeric characters except decimal points
        clean_str = str(market_cap_str).strip()
        
        # Handle different formats (e.g., "3605", "3.6B", "3,605")
        if 'B' in clean_str.upper():
            # Already in billions
            return float(clean_str.upper().replace('B', '').replace(',', ''))
        elif 'M' in clean_str.upper():
            # Convert millions to billions
            return float(clean_str.upper().replace('M', '').replace(',', '')) / 1000
        elif 'K' in clean_str.upper():
            # Convert thousands to billions
            return float(clean_str.upper().replace('K', '').replace(',', '')) / 1_000_000
        else:
            # Assume it's already in billions or a raw number
            return float(clean_str.replace(',', ''))
            
    except (ValueError, TypeError):
        logging.warning(f"Could not parse market cap: {market_cap_str}")
        return None

def update_stocks_from_csv(csv_file_path):
    """Main function to update stocks table from CSV file"""
    logging.info(f"🚀 Starting stocks table update from {csv_file_path}")
    
    # Update schema first
    update_stocks_schema()
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file_path)
        logging.info(f"📊 Loaded {len(df)} records from CSV")
    except Exception as e:
        logging.error(f"❌ Error reading CSV file: {e}")
        return
    
    # Clean and prepare data
    df = df.fillna('')
    
    # Connect to database
    conn = get_db_connection()
    cur = conn.cursor()
    
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    try:
        for idx, row in df.iterrows():
            ticker = str(row['Ticker']).strip().upper()
            
            if not ticker or ticker == 'TICKER':
                continue
            
            logging.info(f"Processing {ticker} ({idx + 1}/{len(df)})")
            
            try:
                # Get additional info from web
                web_info = get_company_info_from_web(ticker)
                
                # Prepare data for database
                company_name = str(row['Company Name']).strip()
                industry = str(row['Industry']).strip() or web_info.get('industry', '')
                sector = str(row['Sector']).strip() or web_info.get('sector', '')
                market_cap_b = clean_market_cap(row['Market Cap (B)']) or web_info.get('market_cap_b')
                description = str(row['Description']).strip() or web_info.get('description', '')
                business_model = str(row['Business_Model']).strip()
                products_services = str(row['Products_Services']).strip()
                main_customers = str(row['Main_Customers']).strip()
                markets = str(row['Markets']).strip()
                moat_1 = str(row['Moat 1']).strip()
                moat_2 = str(row['Moat 2']).strip()
                moat_3 = str(row['Moat 3']).strip()
                moat_4 = str(row['Moat 4']).strip()
                peer_a = str(row['Peer A']).strip()
                peer_b = str(row['Peer B']).strip()
                peer_c = str(row['Peer C']).strip()
                exchange = web_info.get('exchange', '')
                country = web_info.get('country', '')
                
                # Download logo
                logo_path = download_logo(ticker, web_info.get('logo_url'))
                logo_url = logo_path if logo_path else ''
                
                # Check if ticker already exists
                cur.execute("SELECT id FROM stocks WHERE ticker = %s", (ticker,))
                existing = cur.fetchone()
                
                if existing:
                    # Update existing record
                    cur.execute("""
                        UPDATE stocks SET 
                            company_name = %s,
                            exchange = %s,
                            sector = %s,
                            industry = %s,
                            country = %s,
                            logo_url = %s,
                            market_cap_b = %s,
                            description = %s,
                            business_model = %s,
                            products_services = %s,
                            main_customers = %s,
                            markets = %s,
                            moat_1 = %s,
                            moat_2 = %s,
                            moat_3 = %s,
                            moat_4 = %s,
                            peer_a = %s,
                            peer_b = %s,
                            peer_c = %s,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE ticker = %s
                    """, (
                        company_name, exchange, sector, industry, country, logo_url,
                        market_cap_b, description, business_model, products_services,
                        main_customers, markets, moat_1, moat_2, moat_3, moat_4,
                        peer_a, peer_b, peer_c, ticker
                    ))
                    updated_count += 1
                    logging.info(f"✅ Updated {ticker}")
                else:
                    # Insert new record
                    cur.execute("""
                        INSERT INTO stocks (
                            ticker, company_name, exchange, sector, industry, country,
                            logo_url, market_cap_b, description, business_model,
                            products_services, main_customers, markets,
                            moat_1, moat_2, moat_3, moat_4,
                            peer_a, peer_b, peer_c, last_updated
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                        )
                    """, (
                        ticker, company_name, exchange, sector, industry, country,
                        logo_url, market_cap_b, description, business_model,
                        products_services, main_customers, markets,
                        moat_1, moat_2, moat_3, moat_4,
                        peer_a, peer_b, peer_c
                    ))
                    inserted_count += 1
                    logging.info(f"✅ Inserted {ticker}")
                
                # Commit every 10 records to avoid long transactions
                if (idx + 1) % 10 == 0:
                    conn.commit()
                    logging.info(f"💾 Committed batch {idx + 1}")
                
                # Rate limiting to avoid overwhelming APIs
                time.sleep(0.1)
                
            except Exception as e:
                error_count += 1
                logging.error(f"❌ Error processing {ticker}: {e}")
                continue
        
        # Final commit
        conn.commit()
        
        # Summary
        logging.info(f"\n🎯 Update Summary:")
        logging.info(f"   - Total records processed: {len(df)}")
        logging.info(f"   - New records inserted: {inserted_count}")
        logging.info(f"   - Existing records updated: {updated_count}")
        logging.info(f"   - Errors encountered: {error_count}")
        
        # Verify results
        cur.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cur.fetchone()[0]
        logging.info(f"   - Total stocks in database: {total_stocks}")
        
        # Check for duplicates
        cur.execute("""
            SELECT ticker, COUNT(*) as count
            FROM stocks 
            GROUP BY ticker 
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        if duplicates:
            logging.warning(f"⚠️  Found {len(duplicates)} duplicate tickers:")
            for ticker, count in duplicates:
                logging.warning(f"   - {ticker}: {count} records")
        else:
            logging.info("✅ No duplicate tickers found")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"❌ Database error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def main():
    """Main execution function"""
    csv_files = [
        '../pre_filled_stocks/batch1_fixed.csv',
        '../pre_filled_stocks/batch2_corrected.csv',
        '../pre_filled_stocks/batch3_corrected.csv',
        '../pre_filled_stocks/batch4_fixed.csv'
    ]
    
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            logging.error(f"❌ CSV file not found: {csv_file}")
            continue
        
        logging.info(f"🚀 Processing CSV file: {csv_file}")
        try:
            update_stocks_from_csv(csv_file)
            logging.info(f"✅ Completed processing: {csv_file}")
        except Exception as e:
            logging.error(f"❌ Failed to process {csv_file}: {e}")
            continue
    
    logging.info("🎉 All CSV files processing completed!")

if __name__ == "__main__":
    main() 