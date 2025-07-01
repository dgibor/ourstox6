import os
import psycopg2
import requests
import time
import logging
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/yahoo_finance_logos.log'),
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

def get_yahoo_finance_logo_url(ticker):
    """Get Yahoo Finance logo URL for a ticker"""
    return f'https://finance.yahoo.com/quote/{ticker}'

def extract_logo_from_yahoo_page(ticker):
    """Try to extract logo URL from Yahoo Finance page"""
    url = get_yahoo_finance_logo_url(ticker)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Look for logo patterns in the HTML
            content = response.text
            
            # Try different logo patterns
            logo_patterns = [
                r'https://logo\.clearbit\.com/[^"\']+',
                r'https://[^"\']*logo[^"\']*\.(?:png|jpg|jpeg|svg)',
                r'https://[^"\']*\.yahoo\.com[^"\']*logo[^"\']*\.(?:png|jpg|jpeg|svg)',
            ]
            
            for pattern in logo_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    return matches[0]
        
        return None
        
    except Exception as e:
        logging.warning(f"Error fetching Yahoo Finance page for {ticker}: {e}")
        return None

def try_yahoo_finance_logo(ticker):
    """Try to get logo from Yahoo Finance"""
    # Try direct Yahoo Finance logo URL
    yahoo_logo_url = f'https://logo.clearbit.com/{ticker}.com'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(yahoo_logo_url, headers=headers, timeout=10)
        
        if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image'):
            return yahoo_logo_url
        
        return None
        
    except Exception as e:
        logging.warning(f"Error trying Yahoo Finance logo for {ticker}: {e}")
        return None

def download_logo(ticker, company_name):
    """Download logo for a ticker using Yahoo Finance"""
    filename = f"{ticker}.png"
    filepath = os.path.join(LOGOS_DIR, filename)
    
    # Skip if logo already exists
    if os.path.exists(filepath):
        return True, "Already exists"
    
    # Try Yahoo Finance approach
    logo_url = try_yahoo_finance_logo(ticker)
    
    if logo_url:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(logo_url, headers=headers, timeout=10)
            
            if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image'):
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logging.info(f"Successfully downloaded logo for {ticker} from Yahoo Finance")
                return True, "Downloaded from Yahoo Finance"
            else:
                logging.warning(f"Failed to download logo for {ticker}: HTTP {response.status_code}")
                
        except Exception as e:
            logging.warning(f"Error downloading logo for {ticker} from Yahoo Finance: {e}")
    
    return False, "Failed Yahoo Finance"

def main():
    """Main execution function"""
    logging.info("Starting Yahoo Finance logo search...")
    
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
        
        # Try to download missing logos using Yahoo Finance
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
            time.sleep(1)
        
        # Summary
        remaining_logos = len([f for f in os.listdir(LOGOS_DIR) if f.endswith(('.png', '.jpg'))])
        
        logging.info("Yahoo Finance logo search completed!")
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