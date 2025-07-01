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
        logging.FileHandler('logs/update_stocks_batches_8_9.log'),
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

def ensure_logos_directory():
    """Ensure logos directory exists"""
    os.makedirs(LOGOS_DIR, exist_ok=True)

def update_stocks_schema(conn):
    """Update stocks table schema to include new columns if they don't exist"""
    cur = conn.cursor()
    
    # Columns to add if they don't exist
    columns_to_add = [
        ('description', 'TEXT'),
        ('business_model', 'VARCHAR(50)'),
        ('products_services', 'TEXT'),
        ('main_customers', 'TEXT'),
        ('markets', 'TEXT'),
        ('moat_1', 'VARCHAR(100)'),
        ('moat_2', 'VARCHAR(100)'),
        ('moat_3', 'VARCHAR(100)'),
        ('moat_4', 'VARCHAR(100)'),
        ('peer_a', 'VARCHAR(10)'),
        ('peer_b', 'VARCHAR(10)'),
        ('peer_c', 'VARCHAR(10)'),
        ('exchange', 'VARCHAR(10)'),
        ('country', 'VARCHAR(50)'),
        ('logo_path', 'VARCHAR(255)')
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE stocks ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
            logging.info(f"Added column {column_name} to stocks table")
        except Exception as e:
            logging.warning(f"Column {column_name} might already exist: {e}")
    
    conn.commit()
    cur.close()

def clean_market_cap(market_cap_str):
    """Convert market cap string to numeric value in billions"""
    if pd.isna(market_cap_str) or market_cap_str == '':
        return None
    
    try:
        # Remove any non-numeric characters except decimal points
        cleaned = re.sub(r'[^\d.]', '', str(market_cap_str))
        if cleaned:
            return float(cleaned)
        return None
    except:
        return None

def download_logo(ticker, company_name):
    """Download company logo from Yahoo Finance"""
    try:
        # Try to get logo from Yahoo Finance
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if 'logo_url' in info and info['logo_url']:
            logo_url = info['logo_url']
            response = requests.get(logo_url, timeout=10)
            
            if response.status_code == 200:
                # Save logo
                logo_filename = f"{ticker.lower()}.png"
                logo_path = os.path.join(LOGOS_DIR, logo_filename)
                
                with open(logo_path, 'wb') as f:
                    f.write(response.content)
                
                logging.info(f"Downloaded logo for {ticker}")
                return logo_path
        
        logging.warning(f"No logo found for {ticker}")
        return None
        
    except Exception as e:
        logging.error(f"Error downloading logo for {ticker}: {e}")
        return None

def get_company_info(ticker):
    """Get additional company information from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'exchange': info.get('exchange', 'NYSE'),
            'country': info.get('country', 'US'),
            'description': info.get('longBusinessSummary', ''),
            'market_cap': info.get('marketCap', 0) / 1e9 if info.get('marketCap') else None
        }
    except Exception as e:
        logging.error(f"Error getting info for {ticker}: {e}")
        return {
            'exchange': 'NYSE',
            'country': 'US',
            'description': '',
            'market_cap': None
        }

def process_csv_file(csv_file, conn):
    """Process a single CSV file and update the database"""
    logging.info(f"Processing {csv_file}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file)
        logging.info(f"Loaded {len(df)} records from {csv_file}")
        
        cur = conn.cursor()
        stats = {'processed': 0, 'inserted': 0, 'updated': 0, 'errors': 0}
        
        for index, row in df.iterrows():
            ticker = row['Ticker'].strip()
            company_name = row['Company Name'].strip()
            
            logging.info(f"Processing {ticker} ({index + 1}/{len(df)})")
            
            try:
                # Get additional info from Yahoo Finance
                yf_info = get_company_info(ticker)
                
                # Clean and prepare data
                market_cap = clean_market_cap(row['Market Cap (B)'])
                if market_cap is None and yf_info['market_cap']:
                    market_cap = yf_info['market_cap']
                
                # Download logo if not exists
                logo_path = None
                logo_filename = f"{ticker.lower()}.png"
                existing_logo_path = os.path.join(LOGOS_DIR, logo_filename)
                
                if os.path.exists(existing_logo_path):
                    logo_path = existing_logo_path
                    logging.info(f"Logo already exists for {ticker}")
                else:
                    logo_path = download_logo(ticker, company_name)
                
                # Check if ticker already exists
                cur.execute("SELECT ticker FROM stocks WHERE ticker = %s", (ticker,))
                exists = cur.fetchone()
                
                if exists:
                    # Update existing record
                    update_query = """
                    UPDATE stocks SET 
                        company_name = %s, industry = %s, sector = %s, market_cap_b = %s,
                        description = %s, business_model = %s, products_services = %s,
                        main_customers = %s, markets = %s, moat_1 = %s, moat_2 = %s,
                        moat_3 = %s, moat_4 = %s, peer_a = %s, peer_b = %s, peer_c = %s,
                        exchange = %s, country = %s, logo_path = %s
                    WHERE ticker = %s
                    """
                    
                    cur.execute(update_query, (
                        company_name, row['Industry'], row['Sector'], market_cap,
                        row['Description'], row['Business_Model'], row['Products_Services'],
                        row['Main_Customers'], row['Markets'], row['Moat 1'], row['Moat 2'],
                        row['Moat 3'], row['Moat 4'], row['Peer A'], row['Peer B'], row['Peer C'],
                        yf_info['exchange'], yf_info['country'], logo_path, ticker
                    ))
                    
                    stats['updated'] += 1
                    logging.info(f"Updated {ticker}")
                    
                else:
                    # Insert new record
                    insert_query = """
                    INSERT INTO stocks (
                        ticker, company_name, industry, sector, market_cap_b,
                        description, business_model, products_services, main_customers,
                        markets, moat_1, moat_2, moat_3, moat_4, peer_a, peer_b, peer_c,
                        exchange, country, logo_path
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """
                    
                    cur.execute(insert_query, (
                        ticker, company_name, row['Industry'], row['Sector'], market_cap,
                        row['Description'], row['Business_Model'], row['Products_Services'],
                        row['Main_Customers'], row['Markets'], row['Moat 1'], row['Moat 2'],
                        row['Moat 3'], row['Moat 4'], row['Peer A'], row['Peer B'], row['Peer C'],
                        yf_info['exchange'], yf_info['country'], logo_path
                    ))
                    
                    stats['inserted'] += 1
                    logging.info(f"Inserted {ticker}")
                
                stats['processed'] += 1
                
                # Commit every 10 records
                if stats['processed'] % 10 == 0:
                    conn.commit()
                    logging.info(f"Committed batch at {ticker}")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                stats['errors'] += 1
                logging.error(f"Error processing {ticker}: {e}")
                # Rollback transaction on error
                conn.rollback()
                continue
        
        # Final commit
        conn.commit()
        cur.close()
        
        logging.info(f"Completed {csv_file}: {stats}")
        return stats
        
    except Exception as e:
        logging.error(f"Error processing {csv_file}: {e}")
        return {'processed': 0, 'inserted': 0, 'updated': 0, 'errors': 1}

def main():
    """Main execution function"""
    csv_files = [
        '../pre_filled_stocks/batch8.csv',
        '../pre_filled_stocks/batch9.csv'
    ]
    
    total_stats = {
        'processed': 0,
        'inserted': 0,
        'updated': 0,
        'errors': 0
    }
    
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            logging.error(f"CSV file not found: {csv_file}")
            continue
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            
            # Update schema if needed
            update_stocks_schema(conn)
            
            # Process the file
            stats = process_csv_file(csv_file, conn)
            
            # Update total stats
            for key in total_stats:
                total_stats[key] += stats[key]
            
            conn.close()
            
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            continue
    
    logging.info(f"Final Summary: {total_stats}")

if __name__ == "__main__":
    ensure_logos_directory()
    main() 