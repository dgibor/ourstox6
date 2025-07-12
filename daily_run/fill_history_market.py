import os
import time
import logging
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta, date
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
        logging.FileHandler('daily_run/logs/fill_history_market.log'),
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
MIN_HISTORY_DAYS = 100

class MarketHistoryFiller:
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

def get_market_etf_gaps(cur):
    cur.execute('''
        SELECT ticker, COUNT(*) as days_available, MIN(date), MAX(date)
        FROM market_data
        WHERE date::date >= (CURRENT_DATE - INTERVAL '120 days')
        GROUP BY ticker
    ''')
    ticker_info = cur.fetchall()
    cur.execute('SELECT etf_ticker FROM market_etf')
    all_tickers = set(row[0] for row in cur.fetchall())
    ticker_gaps = {}
    for ticker, days_available, min_date, max_date in ticker_info:
        if days_available < MIN_HISTORY_DAYS:
            ticker_gaps[ticker] = {'days_available': days_available, 'min_date': min_date, 'max_date': max_date}
    # Add tickers with no data at all
    for ticker in all_tickers:
        if ticker not in ticker_gaps and not any(ticker == row[0] for row in ticker_info):
            ticker_gaps[ticker] = {'days_available': 0, 'min_date': None, 'max_date': None}
    return ticker_gaps

def is_rate_limit_error(error_msg):
    """Check if error is due to rate limiting."""
    rate_limit_indicators = [
        "too many requests",
        "rate limit",
        "429",
        "try again later",
        "exceeded",
        "quota",
        "throttle"
    ]
    error_lower = str(error_msg).lower()
    return any(indicator in error_lower for indicator in rate_limit_indicators)

def is_delisted_error(error_msg):
    """Check if error indicates stock is delisted."""
    # More specific delisted indicators - avoid false positives
    delisted_indicators = [
        "symbol may be delisted",
        "no data found, symbol may be delisted",
        "possibly delisted",
        "delisted",
        "invalid symbol",
        "ticker not found",
        "404 not found"
    ]
    error_lower = str(error_msg).lower()
    
    # Check for specific delisted patterns
    if any(indicator in error_lower for indicator in delisted_indicators):
        return True
    
    # Additional check: if it's a YFRateLimitError, it's NOT delisted
    if "rate limit" in error_lower or "too many requests" in error_lower:
        return False
    
    # Additional check: if it's a timeout or connection error, it's NOT delisted
    if "timeout" in error_lower or "connection" in error_lower:
        return False
    
    return False

def log_delisted_stock(symbol):
    """Log delisted stock to separate file."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'delisted.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - DELISTED: {symbol}\n")
    
    # Use debug level instead of warning to reduce log noise
    logging.debug(f"Stock {symbol} appears to be delisted - logged to delisted.log")

def fetch_yahoo_history_single(ticker, start_date, end_date):
    """Fetch historical data for a single ticker using Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        
        if data.empty:
            logging.warning(f"Yahoo Finance returned empty data for {ticker}")
            return None, "empty_data"
        
        logging.info(f"Yahoo: Fetched {len(data)} days of data for {ticker}")
        return data, "success"
        
    except Exception as e:
        error_msg = str(e)
        if is_rate_limit_error(error_msg):
            logging.warning(f"Yahoo rate limit for {ticker}: {error_msg}")
            return None, "rate_limit"
        elif is_delisted_error(error_msg):
            return None, "delisted"
        else:
            logging.error(f"Yahoo error for {ticker}: {error_msg}")
            return None, "error"

def fetch_yahoo_history(tickers, start_date, end_date):
    """Try to fetch batch data, fall back to individual if rate limited."""
    try:
        data = yf.download(tickers, start=start_date, end=end_date, threads=True, group_by='ticker', auto_adjust=False)
        if data is None or data.empty:
            return None, "empty_data"
        return data, "success"
    except Exception as e:
        error_msg = str(e)
        if is_rate_limit_error(error_msg):
            logging.warning(f"Yahoo batch rate limited: {error_msg}")
            return None, "rate_limit"
        else:
            logging.error(f"Yahoo batch download error: {e}")
            return None, "error"

@sleep_and_retry
@limits(calls=FINNHUB_CALLS_PER_MIN, period=60)
def fetch_finnhub_history(ticker, start_date, end_date):
    """Fetch historical data using Finnhub API."""
    try:
        # Ensure datetime objects for timestamp conversion
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.min.time())
        
        url = f"https://finnhub.io/api/v1/stock/candle"
        params = {
            'symbol': ticker,
            'resolution': 'D',
            'from': int(start_date.timestamp()),
            'to': int(end_date.timestamp()),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if response.status_code == 429:
            return None, "rate_limit"
        elif data.get('s') == 'no_data':
            return None, "delisted"
        elif data.get('s') != 'ok':
            return None, "error"
        
        df = pd.DataFrame({
            'date': pd.to_datetime(data['t'], unit='s'),
            'Open': data['o'],
            'High': data['h'],
            'Low': data['l'],
            'Close': data['c'],
            'Volume': data['v']
        })
        df.set_index('date', inplace=True)
        
        logging.info(f"Finnhub: Fetched {len(df)} days of data for {ticker}")
        return df, "success"
        
    except Exception as e:
        error_msg = str(e)
        if is_rate_limit_error(error_msg):
            return None, "rate_limit"
        else:
            logging.error(f"Finnhub error for {ticker}: {error_msg}")
            return None, "error"

@sleep_and_retry
@limits(calls=ALPHA_VANTAGE_CALLS_PER_MIN, period=60)
def fetch_alpha_vantage_history(ticker, years=5):
    """Fetch historical data using Alpha Vantage API."""
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'apikey': ALPHA_VANTAGE_API_KEY,
            'outputsize': 'compact'  # Changed to compact to get ~100 days
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'Error Message' in data:
            return None, "delisted"
        elif 'Note' in data and 'API call frequency' in data['Note']:
            return None, "rate_limit"
        elif 'Time Series (Daily)' not in data:
            return None, "error"
        
        ts = data['Time Series (Daily)']
        df = pd.DataFrame.from_dict(ts, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. volume': 'Volume'
        })
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        df = df.sort_index()
        
        # Filter to requested time range (last ~120 days to match other scripts)
        cutoff_date = date.today() - timedelta(days=years*365 if years*365 < 120 else 120)
        df = df[df.index.date >= cutoff_date]
        
        logging.info(f"Alpha Vantage: Fetched {len(df)} days of data for {ticker}")
        return df, "success"
        
    except Exception as e:
        error_msg = str(e)
        if is_rate_limit_error(error_msg):
            return None, "rate_limit"
        else:
            logging.error(f"Alpha Vantage error for {ticker}: {error_msg}")
            return None, "error"

def fetch_stock_history_with_fallback(ticker, start_date, end_date):
    """
    Fetch historical data with API fallback system:
    Yahoo → Finnhub → Yahoo (1hr later) → Finnhub → Alpha Vantage → DB previous close
    """
    # Calculate years from date range for Alpha Vantage
    days_requested = (end_date - start_date).days
    years_requested = max(1, days_requested // 365)
    
    phases = [
        ("Yahoo (Phase 1)", lambda: fetch_yahoo_history_single(ticker, start_date, end_date)),
        ("Finnhub (Phase 2)", lambda: fetch_finnhub_history(ticker, start_date, end_date)),
        ("Yahoo (Phase 3)", lambda: fetch_yahoo_history_single(ticker, start_date, end_date)),  # 1hr retry
        ("Finnhub (Phase 4)", lambda: fetch_finnhub_history(ticker, start_date, end_date)),
        ("Alpha Vantage (Phase 5)", lambda: fetch_alpha_vantage_history(ticker, years_requested))
    ]
    
    for phase_name, fetch_func in phases:
        try:
            data, status = fetch_func()
            
            if status == "success" and data is not None and not data.empty:
                return data
            elif status == "delisted":
                log_delisted_stock(ticker)
                return None
            elif status == "rate_limit":
                logging.warning(f"{phase_name} rate limited for {ticker}, trying next API")
                continue
            else:
                logging.warning(f"{phase_name} failed for {ticker}, trying next API")
                continue
                
        except Exception as e:
            logging.error(f"{phase_name} exception for {ticker}: {e}")
            continue
    
    # Phase 6: No data available from any API
    logging.warning(f"All APIs failed for {ticker}, no historical data available")
    return None

def get_market_info(cur, ticker):
    cur.execute("""
        SELECT category, indicator, etf_name FROM market_etf WHERE etf_ticker = %s
    """, (ticker,))
    result = cur.fetchone()
    if result:
        return {
            'category': result[0],
            'indicator': result[1],
            'etf_name': result[2]
        }
    return None

def insert_market_history(conn, cur, ticker, hist_df):
    market_info = get_market_info(cur, ticker)
    if not market_info:
        logging.error(f"No market info found for {ticker}, skipping insert.")
        return
    for idx, row in hist_df.iterrows():
        try:
            cur.execute('''
                INSERT INTO market_data (
                    ticker, date, open, high, low, close, volume,
                    category, indicator, etf_name,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (ticker, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                ticker,
                idx.strftime('%Y-%m-%d'),
                int(round(row['Open'] * 100)) if not pd.isna(row['Open']) else None,
                int(round(row['High'] * 100)) if not pd.isna(row['High']) else None,
                int(round(row['Low'] * 100)) if not pd.isna(row['Low']) else None,
                int(round(row['Close'] * 100)) if not pd.isna(row['Close']) else None,
                int(row['Volume']) if not pd.isna(row['Volume']) else None,
                market_info['category'],
                market_info['indicator'],
                market_info['etf_name']
            ))
        except Exception as e:
            logging.error(f"Insert error for {ticker} on {idx}: {e}")
    conn.commit()

def fill_history_market(test_mode=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    if test_mode:
        tickers = ['SPY']
    else:
        ticker_gaps = get_market_etf_gaps(cur)
        logging.info(f"Market ETFs needing history fill: {len(ticker_gaps)}")
        tickers = list(ticker_gaps.keys())
    today = date.today()
    start_date = today - timedelta(days=120)
    
    # First try batch processing with Yahoo
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i+BATCH_SIZE]
        logging.info(f"Processing batch {i//BATCH_SIZE+1}: {batch}")
        
        data, status = fetch_yahoo_history(batch, start_date, today)
        failed_tickers = []
        
        if status == "success" and data is not None:
            for ticker in batch:
                try:
                    # Handle multi-level columns from yfinance batch download
                    if isinstance(data, pd.DataFrame) and hasattr(data.columns, 'levels'):
                        if ticker in data.columns.get_level_values(0):
                            tdf = data[ticker].dropna(subset=['Open', 'High', 'Low', 'Close'])
                        else:
                            failed_tickers.append(ticker)
                            continue
                    elif isinstance(data, pd.DataFrame) and set(['Open', 'High', 'Low', 'Close']).issubset(data.columns):
                        tdf = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
                    else:
                        failed_tickers.append(ticker)
                        continue
                    
                    if tdf.empty:
                        failed_tickers.append(ticker)
                        continue
                        
                    logging.info(f"Inserting {len(tdf)} rows for {ticker}")
                    if test_mode:
                        print(f"DataFrame for {ticker}:")
                        print(tdf.head(10))
                    insert_market_history(conn, cur, ticker, tdf)
                    logging.info(f"Batch processing successful for {ticker}")
                except Exception as e:
                    logging.error(f"Error processing {ticker} from batch: {e}")
                    failed_tickers.append(ticker)
        else:
            # Entire batch failed
            logging.warning(f"Yahoo batch failed with status: {status}")
            failed_tickers = batch
        
        # Process failed tickers individually with full fallback system
        for ticker in failed_tickers:
            logging.info(f"Processing {ticker} individually with fallback system")
            tdf = fetch_stock_history_with_fallback(ticker, start_date, today)
            if tdf is not None and not tdf.empty:
                logging.info(f"Inserting {len(tdf)} rows for {ticker} (fallback)")
                insert_market_history(conn, cur, ticker, tdf)
                logging.info(f"Successfully retrieved data for {ticker} via fallback")
            else:
                logging.warning(f"Failed to retrieve any data for {ticker}")
        
        # Rate limiting pause between batches
        if i + BATCH_SIZE < len(tickers):
            logging.info("Pausing between batches...")
            time.sleep(10)
    
    cur.close()
    conn.close()
    logging.info("Market ETF history fill complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()
    fill_history_market(test_mode=args.test) 