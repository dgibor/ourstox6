import os
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cleanup_logos.log'),
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

def cleanup_extra_logos():
    """Remove logo files that don't correspond to companies in the database"""
    logging.info("Starting logo cleanup process...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get all tickers from stocks table
        cur.execute("SELECT ticker FROM stocks")
        db_tickers = {row[0].upper() for row in cur.fetchall()}
        
        logging.info(f"Found {len(db_tickers)} companies in database")
        
        # Get all logo files
        logo_files = [f for f in os.listdir(LOGOS_DIR) if f.endswith(('.png', '.jpg'))]
        logo_tickers = {f.replace('.png', '').replace('.jpg', '').upper() for f in logo_files}
        
        logging.info(f"Found {len(logo_tickers)} logo files")
        
        # Find extra logos (logos for companies not in database)
        extra_tickers = logo_tickers - db_tickers
        
        logging.info(f"Found {len(extra_tickers)} extra logos to remove")
        
        # Remove extra logo files
        removed_count = 0
        for ticker in extra_tickers:
            # Try both .png and .jpg extensions
            for ext in ['.png', '.jpg']:
                filepath = os.path.join(LOGOS_DIR, f"{ticker}{ext}")
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        logging.info(f"Removed extra logo: {ticker}{ext}")
                        removed_count += 1
                        break  # Only remove one file per ticker
                    except Exception as e:
                        logging.error(f"Error removing {filepath}: {e}")
        
        # Summary
        remaining_logos = len([f for f in os.listdir(LOGOS_DIR) if f.endswith(('.png', '.jpg'))])
        
        logging.info("Logo cleanup completed!")
        logging.info(f"Summary:")
        logging.info(f"  - Extra logos removed: {removed_count}")
        logging.info(f"  - Logos remaining: {remaining_logos}")
        logging.info(f"  - Companies in database: {len(db_tickers)}")
        logging.info(f"  - Logo coverage: {(remaining_logos/len(db_tickers))*100:.1f}%")
        
    except Exception as e:
        logging.error(f"Error in cleanup process: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    cleanup_extra_logos() 