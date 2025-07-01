import os
import psycopg2
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/download_logos.log'),
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
LOGOS_DIR = 'pre_filled_stocks/logos'
os.makedirs(LOGOS_DIR, exist_ok=True)

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(**DB_CONFIG)

def get_clearbit_logo_url(ticker):
    """Get Clearbit logo URL for a ticker"""
    return f'https://logo.clearbit.com/{ticker}.com'

def get_yahoo_logo_url(ticker):
    """Get Yahoo Finance logo URL for a ticker"""
    return f'https://logo.clearbit.com/{ticker}.com'

def download_logo(ticker, logo_url=None):
    """Download logo for a ticker"""
    filename = f"{ticker}.png"
    filepath = os.path.join(LOGOS_DIR, filename)
    
    # Skip if logo already exists
    if os.path.exists(filepath):
        return True, "Already exists"
    
    # Try different logo sources
    logo_sources = []
    
    if logo_url and logo_url.strip() and logo_url.lower() != 'nan':
        logo_sources.append(logo_url)
    
    # Add fallback sources
    logo_sources.extend([
        get_clearbit_logo_url(ticker),
        get_yahoo_logo_url(ticker)
    ])
    
    for url in logo_sources:
        try:
            logging.info(f"Trying to download logo for {ticker} from {url}")
            resp = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if resp.status_code == 200 and resp.headers.get('Content-Type', '').startswith('image'):
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                logging.info(f"Successfully downloaded logo for {ticker}")
                return True, "Downloaded"
            else:
                logging.warning(f"Failed to download logo for {ticker}: HTTP {resp.status_code}")
                
        except Exception as e:
            logging.warning(f"Error downloading logo for {ticker} from {url}: {e}")
            continue
    
    return False, "Failed all sources"

def main():
    """Main execution function"""
    logging.info("Starting logo download for all stocks...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get all tickers from stocks table
        cur.execute("SELECT ticker, company_name, logo_url FROM stocks ORDER BY ticker")
        stocks = cur.fetchall()
        
        logging.info(f"Found {len(stocks)} companies in database")
        
        # Get existing logos
        existing_logos = set()
        for fname in os.listdir(LOGOS_DIR):
            if fname.endswith('.png') or fname.endswith('.jpg'):
                existing_logos.add(os.path.splitext(fname)[0].upper())
        
        logging.info(f"Found {len(existing_logos)} existing logos")
        
        # Download logos
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for ticker, company_name, logo_url in stocks:
            if not ticker or ticker.strip() == '':
                continue
                
            ticker = ticker.strip().upper()
            
            # Skip if logo already exists
            if ticker in existing_logos:
                skip_count += 1
                continue
            
            logging.info(f"Processing {ticker}: {company_name}")
            
            success, message = download_logo(ticker, logo_url)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # Add small delay to be respectful to servers
            time.sleep(0.5)
        
        # Summary
        logging.info("Logo download completed!")
        logging.info(f"Summary:")
        logging.info(f"  - Total companies: {len(stocks)}")
        logging.info(f"  - Already existed: {skip_count}")
        logging.info(f"  - Successfully downloaded: {success_count}")
        logging.info(f"  - Failed: {fail_count}")
        logging.info(f"  - Total logos now: {len(existing_logos) + success_count}")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 