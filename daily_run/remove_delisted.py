#!/usr/bin/env python3
"""
Script to remove delisted stocks from the database.
Reads from delisted.log and removes tickers from relevant database tables.
"""

import os
import logging
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Ensure logs directory exists
os.makedirs('daily_run/logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/remove_delisted.log'),
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

class DelistedStockRemover:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.setup_database()
        
    def setup_database(self):
        """Initialize database connection"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor()
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise
    
    def read_delisted_stocks(self, log_file_path='daily_run/logs/delisted.log'):
        """Read delisted stocks from log file"""
        delisted_tickers = set()
        
        if not os.path.exists(log_file_path):
            logging.info(f"No delisted log file found at {log_file_path}")
            return delisted_tickers
        
        try:
            with open(log_file_path, 'r') as file:
                for line in file:
                    # Parse log line format: "YYYY-MM-DD HH:MM:SS,mmm - DELISTED: TICKER - error message"
                    match = re.search(r'DELISTED:\s+([A-Za-z0-9.-]+)\s+-', line)
                    if match:
                        ticker = match.group(1).strip()
                        delisted_tickers.add(ticker)
                        
            logging.info(f"Found {len(delisted_tickers)} delisted stocks in log file")
            return delisted_tickers
            
        except Exception as e:
            logging.error(f"Error reading delisted log file: {e}")
            return delisted_tickers
    
    def check_ticker_exists(self, ticker, table_name):
        """Check if ticker exists in specified table"""
        try:
            self.cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE ticker = %s", (ticker,))
            count = self.cur.fetchone()[0]
            return count > 0
        except Exception as e:
            logging.error(f"Error checking ticker {ticker} in {table_name}: {e}")
            return False
    
    def remove_from_table(self, ticker, table_name):
        """Remove ticker from specified table"""
        try:
            self.cur.execute(f"DELETE FROM {table_name} WHERE ticker = %s", (ticker,))
            deleted_count = self.cur.rowcount
            if deleted_count > 0:
                logging.info(f"Removed {deleted_count} records for {ticker} from {table_name}")
                return deleted_count
            else:
                logging.info(f"No records found for {ticker} in {table_name}")
                return 0
        except Exception as e:
            logging.error(f"Error removing {ticker} from {table_name}: {e}")
            return 0
    
    def remove_delisted_stocks(self, delisted_tickers):
        """Remove delisted stocks from all relevant tables"""
        if not delisted_tickers:
            logging.info("No delisted stocks to remove")
            return
        
        # Tables to clean up (in order of dependencies)
        tables_to_clean = [
            'daily_charts',      # Main price data
            'technical_indicators', # Technical indicators (if exists)
            'stocks'             # Main stocks table (remove last due to foreign key constraints)
        ]
        
        total_removed = 0
        
        try:
            self.cur.execute("BEGIN")
            
            for ticker in delisted_tickers:
                logging.info(f"Processing delisted stock: {ticker}")
                ticker_removed = 0
                
                for table in tables_to_clean:
                    # Check if table exists first
                    self.cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table,))
                    
                    table_exists = self.cur.fetchone()[0]
                    
                    if table_exists:
                        if self.check_ticker_exists(ticker, table):
                            removed = self.remove_from_table(ticker, table)
                            ticker_removed += removed
                    else:
                        logging.info(f"Table {table} does not exist, skipping")
                
                if ticker_removed > 0:
                    total_removed += 1
                    logging.info(f"Successfully removed {ticker} from database ({ticker_removed} total records)")
                else:
                    logging.info(f"Ticker {ticker} was not found in any tables")
            
            self.conn.commit()
            logging.info(f"Successfully removed {total_removed} delisted stocks from database")
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error removing delisted stocks: {e}")
            raise
    
    def backup_delisted_log(self):
        """Backup and clear the delisted log file after processing"""
        delisted_log_path = 'daily_run/logs/delisted.log'
        
        if not os.path.exists(delisted_log_path):
            return
        
        try:
            # Create backup with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'daily_run/logs/delisted_backup_{timestamp}.log'
            
            # Copy content to backup
            with open(delisted_log_path, 'r') as original:
                with open(backup_path, 'w') as backup:
                    backup.write(original.read())
            
            # Clear original file
            with open(delisted_log_path, 'w') as original:
                original.write('')
            
            logging.info(f"Delisted log backed up to {backup_path} and cleared")
            
        except Exception as e:
            logging.error(f"Error backing up delisted log: {e}")
    
    def run(self):
        """Main execution function"""
        try:
            logging.info("Starting delisted stock removal process")
            
            # Read delisted stocks from log file
            delisted_tickers = self.read_delisted_stocks()
            
            if delisted_tickers:
                logging.info(f"Processing {len(delisted_tickers)} delisted stocks: {list(delisted_tickers)}")
                
                # Remove delisted stocks from database
                self.remove_delisted_stocks(delisted_tickers)
                
                # Backup and clear the delisted log file
                self.backup_delisted_log()
                
                logging.info("Delisted stock removal process completed successfully")
            else:
                logging.info("No delisted stocks found to process")
                
        except Exception as e:
            logging.error(f"Error in delisted stock removal process: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    remover = DelistedStockRemover()
    remover.run() 