import os
import time
import logging
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
from typing import List, Dict, Tuple
import concurrent.futures
from ratelimit import limits, sleep_and_retry

# Load environment variables
load_dotenv()

# Ensure logs directory exists
os.makedirs('daily_run/logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/get_sector_prices.log'),
        logging.StreamHandler()
    ]
)

# Configure delisted sectors logging (though rare for ETFs)
delisted_logger = logging.getLogger('delisted_sectors')
delisted_logger.setLevel(logging.INFO)
delisted_handler = logging.FileHandler('daily_run/logs/delisted.log')
delisted_handler.setFormatter(logging.Formatter('%(asctime)s - SECTOR - %(message)s'))
delisted_logger.addHandler(delisted_handler)
delisted_logger.propagate = False

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# API configurations
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Constants
BATCH_SIZE = 500
MAX_RETRIES = 2
FINNHUB_CALLS_PER_MIN = 60
ALPHA_VANTAGE_CALLS_PER_MIN = 5

class SectorPriceCollector:
    def __init__(self, test_mode=False):
        self.successful_tickers = []
        self.failed_tickers = []
        self.delisted_tickers = []
        self.retry_attempt = 0
        self.conn = None
        self.cur = None
        self.test_mode = test_mode
        self.setup_database()

    def setup_database(self):
        """Initialize database connection"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor()
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise

    def get_all_tickers(self):
        if self.test_mode:
            # Use a fixed list of tickers for testing
            return ['XLK', 'XLF', 'XLV', 'XLI', 'XLY']
        else:
            self.cur.execute("SELECT etf_ticker FROM industries WHERE industry = 'Sector ETF'")
            return [row[0] for row in self.cur.fetchall()]

    def is_delisted_error(self, error_msg: str) -> bool:
        """Check if error message indicates delisted stock"""
        delisted_indicators = [
            'delisted',
            'No data found, symbol may be delisted',
            'possibly delisted'
        ]
        return any(indicator.lower() in str(error_msg).lower() for indicator in delisted_indicators)

    def is_rate_limit_error(self, error_msg: str) -> bool:
        """Check if error message indicates rate limiting"""
        rate_limit_indicators = [
            'rate limit',
            'too many requests',
            '429',
            'YFRateLimitError'
        ]
        return any(indicator.lower() in str(error_msg).lower() for indicator in rate_limit_indicators)

    def log_delisted_sector(self, ticker: str, error_msg: str):
        """Log delisted sector ETF to separate log file"""
        delisted_logger.info(f"DELISTED: {ticker} - {error_msg}")
        self.delisted_tickers.append(ticker)

    def collect_yahoo_prices(self, tickers: List[str]) -> Tuple[Dict[str, dict], List[str]]:
        """Collect prices using Yahoo Finance API and return price data"""
        prices_data = {}
        failed = []
        for i in range(0, len(tickers), BATCH_SIZE):
            batch = tickers[i:i + BATCH_SIZE]
            try:
                data = yf.download(batch, period="1d", threads=True)
                # If only one ticker, data is a DataFrame, else MultiIndex
                if isinstance(data.columns, pd.MultiIndex):
                    for ticker in batch:
                        try:
                            tdata = data.xs(ticker, axis=1, level=1, drop_level=False)
                            if tdata.empty:
                                logging.error(f"Skipping {ticker}: Empty data returned")
                                failed.append(ticker)
                                continue
                            row = tdata.iloc[-1]
                            # Skip if any price is NaN
                            if any(pd.isna(row[field].item()) for field in ['Open', 'High', 'Low', 'Close']):
                                logging.error(f"Skipping {ticker}: NaN price data")
                                failed.append(ticker)
                                continue
                            prices_data[ticker] = {
                                'open': int(round(row['Open'].item() * 100)),
                                'high': int(round(row['High'].item() * 100)),
                                'low': int(round(row['Low'].item() * 100)),
                                'close': int(round(row['Close'].item() * 100)),
                                'volume': int(row['Volume'].item()) if not pd.isna(row['Volume'].item()) else None
                            }
                        except Exception as e:
                            logging.error(f"Error processing {ticker}: {e}")
                            failed.append(ticker)
                else:
                    # Single ticker
                    try:
                        if data.empty:
                            logging.error(f"Skipping {batch[0]}: Empty data returned")
                            failed.append(batch[0])
                            continue
                        row = data.iloc[-1]
                        ticker = batch[0]
                        if any(pd.isna(row[field].item()) for field in ['Open', 'High', 'Low', 'Close']):
                            logging.error(f"Skipping {ticker}: NaN price data")
                            failed.append(ticker)
                            continue
                        prices_data[ticker] = {
                            'open': int(round(row['Open'].item() * 100)),
                            'high': int(round(row['High'].item() * 100)),
                            'low': int(round(row['Low'].item() * 100)),
                            'close': int(round(row['Close'].item() * 100)),
                            'volume': int(row['Volume'].item()) if not pd.isna(row['Volume'].item()) else None
                        }
                    except Exception as e:
                        logging.error(f"Error processing {batch[0]}: {e}")
                        failed.append(batch[0])
                time.sleep(2)
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Error downloading batch: {e}")
                
                # Check for rate limiting or delisted errors
                for ticker in batch:
                    if self.is_rate_limit_error(error_msg):
                        logging.warning(f"Rate limit detected for {ticker}: {error_msg}")
                    elif self.is_delisted_error(error_msg):
                        self.log_delisted_sector(ticker, error_msg)
                    
                failed.extend(batch)
        return prices_data, failed

    @sleep_and_retry
    @limits(calls=FINNHUB_CALLS_PER_MIN, period=60)
    def get_finnhub_price(self, ticker: str) -> Dict:
        """Get price from Finnhub API with rate limiting"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Finnhub API error for {ticker}: {e}")
            return None

    def collect_finnhub_prices(self, tickers: List[str]) -> Tuple[Dict[str, dict], List[str]]:
        """Collect prices using Finnhub API and return price data"""
        prices_data = {}
        failed = []
        
        for ticker in tickers[:300]:  # Limit to 300 calls to preserve quota
            try:
                data = self.get_finnhub_price(ticker)
                if data and 'c' in data and data['c'] is not None:
                    # Convert Finnhub data to our format
                    prices_data[ticker] = {
                        'open': int(round(data['o'] * 100)) if data.get('o') else None,
                        'high': int(round(data['h'] * 100)) if data.get('h') else None,
                        'low': int(round(data['l'] * 100)) if data.get('l') else None,
                        'close': int(round(data['c'] * 100)) if data.get('c') else None,
                        'volume': int(data.get('v', 0)) if data.get('v') else None
                    }
                    logging.info(f"Successfully got Finnhub price for sector {ticker}")
                else:
                    failed.append(ticker)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logging.error(f"Error processing {ticker} with Finnhub: {e}")
                failed.append(ticker)
        
        return prices_data, failed

    def get_alpha_vantage_price(self, ticker: str) -> Dict:
        """Get price from Alpha Vantage API"""
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Alpha Vantage API error for {ticker}: {e}")
            return None

    def collect_alpha_vantage_prices(self, tickers: List[str]) -> Tuple[Dict[str, dict], List[str]]:
        """Collect prices using Alpha Vantage API and return price data"""
        prices_data = {}
        failed = []
        
        for ticker in tickers[:100]:  # Limit to 100 calls to preserve quota
            try:
                data = self.get_alpha_vantage_price(ticker)
                if data and 'Global Quote' in data:
                    quote = data['Global Quote']
                    if quote.get('05. price'):
                        # Convert Alpha Vantage data to our format
                        prices_data[ticker] = {
                            'open': int(round(float(quote['02. open']) * 100)) if quote.get('02. open') else None,
                            'high': int(round(float(quote['03. high']) * 100)) if quote.get('03. high') else None,
                            'low': int(round(float(quote['04. low']) * 100)) if quote.get('04. low') else None,
                            'close': int(round(float(quote['05. price']) * 100)) if quote.get('05. price') else None,
                            'volume': int(quote['06. volume']) if quote.get('06. volume') else None
                        }
                        logging.info(f"Successfully got Alpha Vantage price for sector {ticker}")
                    else:
                        failed.append(ticker)
                else:
                    failed.append(ticker)
                time.sleep(15)  # Rate limiting for Alpha Vantage
            except Exception as e:
                logging.error(f"Error processing {ticker} with Alpha Vantage: {e}")
                failed.append(ticker)
        
        return prices_data, failed

    def get_previous_close(self, tickers: List[str]) -> Dict[str, float]:
        """Get previous close prices from database"""
        previous_closes = {}
        try:
            for ticker in tickers:
                self.cur.execute("""
                    SELECT close 
                    FROM sectors 
                    WHERE ticker = %s 
                    AND date = (
                        SELECT MAX(date) 
                        FROM sectors 
                        WHERE ticker = %s
                    )
                """, (ticker, ticker))
                result = self.cur.fetchone()
                if result:
                    previous_closes[ticker] = result[0]
        except Exception as e:
            logging.error(f"Error getting previous closes: {e}")
        return previous_closes

    def get_sector_info(self, ticker: str) -> Dict:
        """Get sector information from industries table"""
        try:
            self.cur.execute("""
                SELECT sector, industry, etf_name
                FROM industries
                WHERE etf_ticker = %s
            """, (ticker,))
            result = self.cur.fetchone()
            if result:
                return {
                    'sector_name': result[0],
                    'sector_category': result[1],
                    'etf_name': result[2]
                }
            return None
        except Exception as e:
            logging.error(f"Error getting sector info for {ticker}: {e}")
            return None

    def update_database(self, prices_data: Dict):
        """Update database with collected prices"""
        try:
            self.cur.execute("BEGIN")
            
            for ticker, data in prices_data.items():
                # Get sector information
                sector_info = self.get_sector_info(ticker)
                if not sector_info:
                    logging.error(f"No sector info found for {ticker}, skipping...")
                    continue

                self.cur.execute("""
                    INSERT INTO sectors (
                        ticker, date, open, high, low, close, volume,
                        sector_name, sector_category, etf_name,
                        created_at, updated_at
                    )
                    VALUES (
                        %s, CURRENT_DATE, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    ticker,
                    data.get('open'),
                    data.get('high'),
                    data.get('low'),
                    data.get('close'),
                    data.get('volume'),
                    sector_info['sector_name'],
                    sector_info['sector_category'],
                    sector_info['etf_name']
                ))
            
            self.conn.commit()
            logging.info(f"Successfully updated {len(prices_data)} records in database")
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Database update error: {e}")
            raise

    def run(self):
        """Main execution function with improved fallback sequence"""
        try:
            # Get all tickers
            all_tickers = self.get_all_tickers()
            logging.info(f"Processing {len(all_tickers)} sector tickers")

            # Phase 1: Yahoo Finance (primary)
            logging.info("Phase 1: Yahoo Finance for sectors")
            prices_data, failed = self.collect_yahoo_prices(all_tickers)
            self.successful_tickers = list(prices_data.keys())
            self.failed_tickers = failed
            if prices_data:
                self.update_database(prices_data)

            # Phase 2: Finnhub (first fallback)
            if self.failed_tickers:
                logging.info(f"Phase 2: Finnhub for {len(self.failed_tickers)} failed sector tickers")
                finnhub_prices, failed = self.collect_finnhub_prices(self.failed_tickers)
                if finnhub_prices:
                    self.update_database(finnhub_prices)
                    self.successful_tickers.extend(list(finnhub_prices.keys()))
                self.failed_tickers = failed

            # Phase 3: Yahoo Finance retry (after 1 hour wait)
            if self.failed_tickers and self.retry_attempt < MAX_RETRIES:
                self.retry_attempt += 1
                logging.info(f"Phase 3: Yahoo Finance retry {self.retry_attempt} for sectors (waiting 1 hour)")
                time.sleep(3600)  # Wait 1 hour
                yahoo_retry_prices, failed = self.collect_yahoo_prices(self.failed_tickers)
                if yahoo_retry_prices:
                    self.update_database(yahoo_retry_prices)
                    self.successful_tickers.extend(list(yahoo_retry_prices.keys()))
                self.failed_tickers = failed

            # Phase 4: Finnhub retry (second fallback)
            if self.failed_tickers:
                logging.info(f"Phase 4: Finnhub retry for {len(self.failed_tickers)} failed sector tickers")
                finnhub_retry_prices, failed = self.collect_finnhub_prices(self.failed_tickers)
                if finnhub_retry_prices:
                    self.update_database(finnhub_retry_prices)
                    self.successful_tickers.extend(list(finnhub_retry_prices.keys()))
                self.failed_tickers = failed

            # Phase 5: Alpha Vantage (third fallback)
            if self.failed_tickers:
                logging.info(f"Phase 5: Alpha Vantage for {len(self.failed_tickers)} failed sector tickers")
                alpha_prices, failed = self.collect_alpha_vantage_prices(self.failed_tickers)
                if alpha_prices:
                    self.update_database(alpha_prices)
                    self.successful_tickers.extend(list(alpha_prices.keys()))
                self.failed_tickers = failed

            # Phase 6: Previous Close Fallback (final fallback)
            if self.failed_tickers:
                logging.info(f"Phase 6: Previous close fallback for {len(self.failed_tickers)} failed sector tickers")
                previous_closes = self.get_previous_close(self.failed_tickers)
                if previous_closes:
                    # Convert previous closes to price data format and update database
                    previous_prices = {}
                    for ticker, close_price in previous_closes.items():
                        previous_prices[ticker] = {
                            'open': close_price,
                            'high': close_price,
                            'low': close_price,
                            'close': close_price,
                            'volume': None
                        }
                    self.update_database(previous_prices)
                    self.successful_tickers.extend(list(previous_prices.keys()))
                    # Remove successfully processed tickers from failed list
                    self.failed_tickers = [t for t in self.failed_tickers if t not in previous_closes]

            # Log summary
            logging.info(f"Successfully processed: {len(self.successful_tickers)} sectors")
            logging.info(f"Failed to process: {len(self.failed_tickers)} sectors")
            logging.info(f"Delisted sectors found: {len(self.delisted_tickers)}")
            
            if self.failed_tickers:
                logging.warning(f"Failed sector tickers: {self.failed_tickers}")
            if self.delisted_tickers:
                logging.info(f"Delisted sector tickers logged: {self.delisted_tickers}")

        except Exception as e:
            logging.error(f"Error in main execution: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    import sys
    test_mode = "--test" in sys.argv
    collector = SectorPriceCollector(test_mode=test_mode)
    collector.run() 