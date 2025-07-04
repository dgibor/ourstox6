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
from ratelimit import limits, sleep_and_retry

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/get_market_prices.log'),
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

# API configurations
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Constants
BATCH_SIZE = 500
MAX_RETRIES = 2
FINNHUB_CALLS_PER_MIN = 60
ALPHA_VANTAGE_CALLS_PER_MIN = 5

class MarketPriceCollector:
    def __init__(self, test_mode=False):
        self.successful_tickers = []
        self.failed_tickers = []
        self.retry_attempt = 0
        self.conn = None
        self.cur = None
        self.test_mode = test_mode
        self.setup_database()

    def setup_database(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor()
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise

    def get_all_tickers(self):
        if self.test_mode:
            # Use a fixed list of tickers for testing
            return ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']
        else:
            self.cur.execute("SELECT etf_ticker FROM market_etf")
            return [row[0] for row in self.cur.fetchall()]

    def get_market_info(self, ticker: str) -> Dict:
        try:
            self.cur.execute("""
                SELECT category, indicator, etf_name
                FROM market_etf
                WHERE etf_ticker = %s
            """, (ticker,))
            result = self.cur.fetchone()
            if result:
                return {
                    'category': result[0],
                    'indicator': result[1],
                    'etf_name': result[2]
                }
            return None
        except Exception as e:
            logging.error(f"Error getting market info for {ticker}: {e}")
            return None

    def collect_yahoo_prices(self, tickers: List[str]) -> Tuple[Dict[str, dict], List[str]]:
        prices_data = {}
        failed = []
        for i in range(0, len(tickers), BATCH_SIZE):
            batch = tickers[i:i + BATCH_SIZE]
            try:
                data = yf.download(batch, period="1d", threads=True)
                if isinstance(data.columns, pd.MultiIndex):
                    for ticker in batch:
                        try:
                            tdata = data.xs(ticker, axis=1, level=1, drop_level=False)
                            if tdata.empty:
                                logging.error(f"Skipping {ticker}: Empty data returned")
                                failed.append(ticker)
                                continue
                            row = tdata.iloc[-1]
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
                logging.error(f"Error downloading batch: {e}")
                failed.extend(batch)
        return prices_data, failed

    @sleep_and_retry
    @limits(calls=FINNHUB_CALLS_PER_MIN, period=60)
    def get_finnhub_price(self, ticker: str) -> Dict:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Finnhub API error for {ticker}: {e}")
            return None

    def collect_finnhub_prices(self, tickers: List[str]) -> Tuple[List[str], List[str]]:
        successful = []
        failed = []
        for ticker in tickers[:300]:
            try:
                data = self.get_finnhub_price(ticker)
                if data and 'c' in data:
                    successful.append(ticker)
                else:
                    failed.append(ticker)
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error processing {ticker} with Finnhub: {e}")
                failed.append(ticker)
        return successful, failed

    def get_alpha_vantage_price(self, ticker: str) -> Dict:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Alpha Vantage API error for {ticker}: {e}")
            return None

    def collect_alpha_vantage_prices(self, tickers: List[str]) -> Tuple[List[str], List[str]]:
        successful = []
        failed = []
        for ticker in tickers[:100]:
            try:
                data = self.get_alpha_vantage_price(ticker)
                if data and 'Global Quote' in data:
                    successful.append(ticker)
                else:
                    failed.append(ticker)
                time.sleep(15)
            except Exception as e:
                logging.error(f"Error processing {ticker} with Alpha Vantage: {e}")
                failed.append(ticker)
        return successful, failed

    def get_previous_close(self, tickers: List[str]) -> Dict[str, float]:
        previous_closes = {}
        try:
            for ticker in tickers:
                self.cur.execute("""
                    SELECT close 
                    FROM market_data 
                    WHERE ticker = %s 
                    AND date = (
                        SELECT MAX(date) 
                        FROM market_data 
                        WHERE ticker = %s
                    )
                """, (ticker, ticker))
                result = self.cur.fetchone()
                if result:
                    previous_closes[ticker] = result[0]
        except Exception as e:
            logging.error(f"Error getting previous closes: {e}")
        return previous_closes

    def update_database(self, prices_data: Dict):
        try:
            self.cur.execute("BEGIN")
            for ticker, data in prices_data.items():
                market_info = self.get_market_info(ticker)
                if not market_info:
                    logging.error(f"No market info found for {ticker}, skipping...")
                    continue
                self.cur.execute("""
                    INSERT INTO market_data (
                        ticker, date, open, high, low, close, volume,
                        category, indicator, etf_name,
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
                    market_info['category'],
                    market_info['indicator'],
                    market_info['etf_name']
                ))
            self.conn.commit()
            logging.info(f"Successfully updated {len(prices_data)} records in database")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Database update error: {e}")
            raise

    def run(self):
        try:
            all_tickers = self.get_all_tickers()
            logging.info(f"Processing {len(all_tickers)} tickers")
            prices_data, failed = self.collect_yahoo_prices(all_tickers)
            self.successful_tickers = list(prices_data.keys())
            self.failed_tickers = failed
            if prices_data:
                self.update_database(prices_data)
            if self.failed_tickers:
                successful, failed = self.collect_finnhub_prices(self.failed_tickers)
                self.successful_tickers.extend(successful)
                self.failed_tickers = failed
            while self.failed_tickers and self.retry_attempt < MAX_RETRIES:
                self.retry_attempt += 1
                logging.info(f"Retry attempt {self.retry_attempt}")
                time.sleep(3600)
                successful, failed = self.collect_yahoo_prices(self.failed_tickers)
                self.successful_tickers.extend(successful)
                self.failed_tickers = failed
            if self.failed_tickers:
                successful, failed = self.collect_alpha_vantage_prices(self.failed_tickers)
                self.successful_tickers.extend(successful)
                self.failed_tickers = failed
            if self.failed_tickers:
                previous_closes = self.get_previous_close(self.failed_tickers)
                for ticker, close in previous_closes.items():
                    self.successful_tickers.append(ticker)
            logging.info(f"Successfully processed: {len(self.successful_tickers)}")
            logging.info(f"Failed to process: {len(self.failed_tickers)}")
        except Exception as e:
            logging.error(f"Error in main execution: {e}")
        finally:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()
    collector = MarketPriceCollector(test_mode=args.test)
    collector.run() 