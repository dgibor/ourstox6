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
        logging.FileHandler('logs/find_missing_logos.log'),
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

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(**DB_CONFIG)

def get_yahoo_logo_url(ticker):
    """Get Yahoo Finance logo URL for a ticker"""
    return f'https://logo.clearbit.com/{ticker}.com'

def get_company_website_logo(ticker, company_name):
    """Try to get logo from company website"""
    # Common company website patterns
    patterns = [
        f'https://logo.clearbit.com/{ticker}.com',
        f'https://logo.clearbit.com/{ticker.lower()}.com',
        f'https://logo.clearbit.com/{company_name.lower().replace(" ", "").replace(".", "").replace(",", "")}.com',
        f'https://logo.clearbit.com/{company_name.lower().replace(" ", "-").replace(".", "").replace(",", "")}.com',
        f'https://logo.clearbit.com/{company_name.lower().replace(" ", "").replace(".", "").replace(",", "").replace("&", "and")}.com',
    ]
    return patterns

def download_logo(ticker, company_name):
    """Download logo for a ticker using multiple sources"""
    filename = f"{ticker}.png"
    filepath = os.path.join(LOGOS_DIR, filename)
    
    # Skip if logo already exists
    if os.path.exists(filepath):
        return True, "Already exists"
    
    # Try different logo sources
    logo_sources = get_company_website_logo(ticker, company_name)
    
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
    logging.info("Starting to find missing logos...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get all tickers from stocks table
        cur.execute("SELECT ticker, company_name FROM stocks ORDER BY ticker")
        stocks = cur.fetchall()
        
        logging.info(f"Found {len(stocks)} companies in database")
        
        # Get existing logos
        existing_logos = set()
        for fname in os.listdir(LOGOS_DIR):
            if fname.endswith('.png') or fname.endswith('.jpg'):
                existing_logos.add(os.path.splitext(fname)[0].upper())
        
        logging.info(f"Found {len(existing_logos)} existing logos")
        
        # Find missing logos
        missing_tickers = []
        for ticker, company_name in stocks:
            if not ticker or ticker.strip() == '':
                continue
                
            ticker = ticker.strip().upper()
            
            # Skip if logo already exists
            if ticker in existing_logos:
                continue
            
            missing_tickers.append((ticker, company_name))
        
        logging.info(f"Found {len(missing_tickers)} companies missing logos")
        
        # Try to download missing logos
        success_count = 0
        fail_count = 0
        
        for ticker, company_name in missing_tickers:
            logging.info(f"Processing {ticker}: {company_name}")
            
            success, message = download_logo(ticker, company_name)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # Add small delay to be respectful to servers
            time.sleep(0.5)
        
        # Summary
        remaining_logos = len([f for f in os.listdir(LOGOS_DIR) if f.endswith(('.png', '.jpg'))])
        
        logging.info("Missing logo search completed!")
        logging.info(f"Summary:")
        logging.info(f"  - Companies missing logos: {len(missing_tickers)}")
        logging.info(f"  - Successfully downloaded: {success_count}")
        logging.info(f"  - Failed: {fail_count}")
        logging.info(f"  - Total logos now: {remaining_logos}")
        logging.info(f"  - Logo coverage: {(remaining_logos/len(stocks))*100:.1f}%")
        
        # List remaining missing logos
        if fail_count > 0:
            logging.info("Remaining missing logos:")
            for ticker, company_name in missing_tickers:
                if not os.path.exists(os.path.join(LOGOS_DIR, f"{ticker}.png")):
                    logging.info(f"  - {ticker}: {company_name}")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 