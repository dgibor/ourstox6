import os
import psycopg2
import pandas as pd
import yfinance as yf
import requests
import time
import logging
from datetime import date, timedelta, datetime
from dotenv import load_dotenv

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

BATCH_SIZE = 20
MIN_HISTORY_DAYS = 100

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

def fetch_yahoo_history(tickers, start_date, end_date):
    try:
        data = yf.download(tickers, start=start_date, end=end_date, threads=True, group_by='ticker', auto_adjust=False)
        return data
    except Exception as e:
        logging.error(f"Yahoo download error: {e}")
        return None

def fetch_finnhub_history(ticker, start_date, end_date):
    url = f"https://finnhub.io/api/v1/stock/candle"
    params = {
        'symbol': ticker,
        'resolution': 'D',
        'from': int(start_date.strftime('%s')),
        'to': int(end_date.strftime('%s')),
        'token': FINNHUB_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('s') == 'ok':
                df = pd.DataFrame({
                    'date': pd.to_datetime(data['t'], unit='s'),
                    'Open': data['o'],
                    'High': data['h'],
                    'Low': data['l'],
                    'Close': data['c'],
                    'Volume': data['v']
                })
                df.set_index('date', inplace=True)
                return df
        return None
    except Exception as e:
        logging.error(f"Finnhub error for {ticker}: {e}")
        return None

def fetch_alpha_vantage_history(ticker):
    url = f"https://www.alphavantage.co/query"
    params = {
        'function': 'TIME_SERIES_DAILY_ADJUSTED',
        'symbol': ticker,
        'apikey': ALPHA_VANTAGE_API_KEY,
        'outputsize': 'compact'
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            ts = data.get('Time Series (Daily)', {})
            if ts:
                df = pd.DataFrame.from_dict(ts, orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.rename(columns={
                    '1. open': 'Open',
                    '2. high': 'High',
                    '3. low': 'Low',
                    '4. close': 'Close',
                    '6. volume': 'Volume'
                })
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
                return df
        return None
    except Exception as e:
        logging.error(f"Alpha Vantage error for {ticker}: {e}")
        return None

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

def fill_history_sector():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    ticker_gaps = get_sector_etf_gaps(cur)
    logging.info(f"Sector ETFs needing history fill: {len(ticker_gaps)}")
    tickers = list(ticker_gaps.keys())
    today = date.today()
    start_date = today - timedelta(days=120)
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i+BATCH_SIZE]
        logging.info(f"Processing batch {i//BATCH_SIZE+1}: {batch}")
        data = fetch_yahoo_history(batch, start_date, today)
        failed_tickers = []
        if data is None:
            logging.error(f"Yahoo batch failed: {batch}")
            failed_tickers = batch
        else:
            for ticker in batch:
                try:
                    if isinstance(data, pd.DataFrame) and ticker in data.columns.get_level_values(0):
                        tdf = data[ticker].dropna(subset=['Open', 'High', 'Low', 'Close'])
                    elif isinstance(data, pd.DataFrame) and set(['Open', 'High', 'Low', 'Close']).issubset(data.columns):
                        tdf = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
                    else:
                        logging.error(f"No data for {ticker} in batch")
                        failed_tickers.append(ticker)
                        continue
                    if tdf.empty:
                        failed_tickers.append(ticker)
                        continue
                    insert_sector_history(conn, cur, ticker, tdf)
                except Exception as e:
                    logging.error(f"Error processing {ticker}: {e}")
                    failed_tickers.append(ticker)
        # Finnhub fallback for failed tickers
        for ticker in failed_tickers:
            time.sleep(1.2)  # Finnhub rate limit
            tdf = fetch_finnhub_history(ticker, start_date, today)
            if tdf is not None and not tdf.empty:
                insert_sector_history(conn, cur, ticker, tdf)
                continue
            # Alpha Vantage fallback (very limited quota)
            tdf = fetch_alpha_vantage_history(ticker)
            if tdf is not None and not tdf.empty:
                # Only keep last 100 days
                tdf = tdf.sort_index().iloc[-100:]
                insert_sector_history(conn, cur, ticker, tdf)
        time.sleep(10)  # Conservative delay
    cur.close()
    conn.close()
    logging.info("Sector ETF history fill complete.")

if __name__ == "__main__":
    fill_history_sector() 