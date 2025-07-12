import os
import psycopg2
import pandas as pd
import yfinance as yf
import requests
import time
import logging
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

BATCH_SIZE = 500
MIN_HISTORY_DAYS = 100
FINNHUB_CALLS_PER_MIN = 60
ALPHA_VANTAGE_CALLS_PER_MIN = 5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/fill_history_sector.log'),
        logging.StreamHandler()
    ]
)

def get_sector_etf_gaps(cur):
    cur.execute('''
        SELECT ticker, COUNT(*) as days_available, MIN(date), MAX(date)
        FROM sectors
        WHERE date::date >= (CURRENT_DATE - INTERVAL '120 days')
        GROUP BY ticker
    ''')
    ticker_info = cur.fetchall()
    cur.execute("SELECT etf_ticker FROM industries WHERE industry = 'Sector ETF'")
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
    delisted_indicators = [
        "delisted",
        "no data found",
        "not found",
        "invalid symbol",
        "no price data",
        "ticker not found",
        "404"
    ]
    error_lower = str(error_msg).lower()
    return any(indicator in error_lower for indicator in delisted_indicators)

def log_delisted_stock(symbol):
    """Log delisted stock to separate file."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'delisted.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - DELISTED: {symbol}\n")
    
    logging.warning(f"Stock {symbol} appears to be delisted - logged to delisted.log")

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

def get_sector_info(cur, ticker):
    cur.execute("""
        SELECT sector, industry, etf_name FROM industries WHERE etf_ticker = %s
    """, (ticker,))
    result = cur.fetchone()
    if result:
        return {
            'sector_name': result[0],
            'sector_category': result[1],
            'etf_name': result[2]
        }
    return None

def insert_sector_history(conn, cur, ticker, hist_df):
    sector_info = get_sector_info(cur, ticker)
    if not sector_info:
        logging.error(f"No sector info found for {ticker}, skipping insert.")
        return
    for idx, row in hist_df.iterrows():
        try:
            cur.execute('''
                INSERT INTO sectors (
                    ticker, date, open, high, low, close, volume,
                    sector_name, sector_category, etf_name,
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
                sector_info['sector_name'],
                sector_info['sector_category'],
                sector_info['etf_name']
            ))
        except Exception as e:
            logging.error(f"Insert error for {ticker} on {idx}: {e}")
    conn.commit()

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

def fetch_fmp_history(ticker, start_date, end_date):
    """Fetch historical data using FMP API."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apikey': os.getenv('FMP_API_KEY')
        }
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        if 'historical' not in data or not data['historical']:
            return None, "empty_data"
        df = pd.DataFrame(data['historical'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        df = df.sort_index()
        logging.info(f"FMP: Fetched {len(df)} days of data for {ticker}")
        return df, "success"
    except Exception as e:
        logging.error(f"FMP error for {ticker}: {e}")
        return None, "error"

def fill_history_sector():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ticker_gaps = get_sector_etf_gaps(cur)
    logging.info(f"Sector ETFs needing history fill: {len(ticker_gaps)}")
    tickers = list(ticker_gaps.keys())
    today = date.today()
    start_date = today - timedelta(days=120)
    for ticker in tickers:
        logging.info(f"Processing {ticker} for sector historical fill...")
        # Try FMP first
        tdf, status = fetch_fmp_history(ticker, start_date, today)
        if status == "success" and tdf is not None and not tdf.empty:
            insert_sector_history(conn, cur, ticker, tdf)
            logging.info(f"FMP fill successful for {ticker}")
            continue
        # If FMP fails, try Alpha Vantage
        tdf, status = fetch_alpha_vantage_history(ticker, years=1)
        if status == "success" and tdf is not None and not tdf.empty:
            insert_sector_history(conn, cur, ticker, tdf)
            logging.info(f"Alpha Vantage fill successful for {ticker}")
            continue
        logging.warning(f"Both FMP and Alpha Vantage failed for {ticker}")
    cur.close()
    conn.close()
    logging.info("Sector ETF history fill complete.")

if __name__ == "__main__":
    fill_history_sector()
