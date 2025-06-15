import os
import sys
import logging
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse

# Add the indicators directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'indicators'))

# Import indicator calculation modules
from daily_run.indicators.ema import calculate_ema
from daily_run.indicators.rsi import calculate_rsi
from daily_run.indicators.cci import calculate_cci
from daily_run.indicators.bollinger_bands import calculate_bollinger_bands
from daily_run.indicators.macd import calculate_macd
from daily_run.indicators.atr import calculate_atr
from daily_run.indicators.vwap import calculate_vwap

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}
print("DB_CONFIG:", DB_CONFIG)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/calc_technicals.log'),
        logging.StreamHandler()
    ]
)

def get_price_data(cur, ticker: str, table: str, ticker_col: str, days: int = 100) -> pd.DataFrame:
    """Fetch price data for a ticker"""
    cur.execute(f"""
        SELECT date, open, high, low, close, volume
        FROM {table}
        WHERE {ticker_col} = %s
        ORDER BY date DESC
        LIMIT %s
    """, (ticker, days))
    
    data = cur.fetchall()
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df.sort_index()

def calculate_indicators(df: pd.DataFrame) -> dict:
    """Calculate all technical indicators"""
    indicators = {}
    
    # RSI
    indicators['rsi_14'] = calculate_rsi(df['close'])
    
    # CCI
    indicators['cci_20'] = calculate_cci(df['high'], df['low'], df['close'])
    
    # EMAs
    indicators['ema_20'] = calculate_ema(df['close'], 20)
    indicators['ema_50'] = calculate_ema(df['close'], 50)
    indicators['ema_100'] = calculate_ema(df['close'], 100)
    indicators['ema_200'] = calculate_ema(df['close'], 200)
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df['close'])
    indicators['bb_upper'] = bb_upper
    indicators['bb_middle'] = bb_middle
    indicators['bb_lower'] = bb_lower
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(df['close'])
    indicators['macd_line'] = macd_line
    indicators['macd_signal'] = signal_line
    indicators['macd_histogram'] = histogram
    
    # ATR
    indicators['atr_14'] = calculate_atr(df['high'], df['low'], df['close'])
    
    # VWAP
    indicators['vwap'] = calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
    
    return indicators

def update_database(cur, ticker: str, indicators: dict, table: str, ticker_col: str):
    """Update the database with calculated indicators"""
    # Get the latest date
    latest_date = max(indicators['rsi_14'].index)
    
    # Prepare the update query
    update_query = f"""
        UPDATE {table}
        SET 
            rsi_14 = %s,
            cci_20 = %s,
            ema_20 = %s,
            ema_50 = %s,
            ema_100 = %s,
            ema_200 = %s,
            bb_upper = %s,
            bb_middle = %s,
            bb_lower = %s,
            macd_line = %s,
            macd_signal = %s,
            macd_histogram = %s,
            atr_14 = %s,
            vwap = %s
        WHERE {ticker_col} = %s AND date = %s
    """
    
    # Get the latest values for each indicator
    values = [
        int(round(indicators['rsi_14'].iloc[-1] * 100)),
        int(round(indicators['cci_20'].iloc[-1] * 100)),
        int(round(indicators['ema_20'].iloc[-1] * 100)),
        int(round(indicators['ema_50'].iloc[-1] * 100)),
        int(round(indicators['ema_100'].iloc[-1] * 100)),
        int(round(indicators['ema_200'].iloc[-1] * 100)),
        int(round(indicators['bb_upper'].iloc[-1] * 100)),
        int(round(indicators['bb_middle'].iloc[-1] * 100)),
        int(round(indicators['bb_lower'].iloc[-1] * 100)),
        int(round(indicators['macd_line'].iloc[-1] * 100)),
        int(round(indicators['macd_signal'].iloc[-1] * 100)),
        int(round(indicators['macd_histogram'].iloc[-1] * 100)),
        int(round(indicators['atr_14'].iloc[-1] * 100)),
        int(round(indicators['vwap'].iloc[-1] * 100)),
        ticker,
        latest_date.strftime('%Y-%m-%d')
    ]
    
    cur.execute(update_query, values)

def validate_calculations(cur, ticker: str, table: str, ticker_col: str) -> bool:
    """Validate that the calculations were inserted correctly"""
    cur.execute(f"""
        SELECT 
            rsi_14, cci_20, ema_20, ema_50, ema_100, ema_200,
            bb_upper, bb_middle, bb_lower,
            macd_line, macd_signal, macd_histogram,
            atr_14, vwap
        FROM {table}
        WHERE {ticker_col} = %s
        ORDER BY date DESC
        LIMIT 1
    """, (ticker,))
    
    result = cur.fetchone()
    if not result:
        return False
    
    # Check if any values are NULL
    return all(x is not None for x in result)

def print_latest_indicators():
    import psycopg2
    from dotenv import load_dotenv
    import os
    load_dotenv()
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('''SELECT date, rsi_14, cci_20, ema_20, ema_50, ema_100, ema_200, bb_upper, bb_middle, bb_lower, macd_line, macd_signal, macd_histogram, atr_14, vwap FROM market_data WHERE ticker = %s ORDER BY date DESC LIMIT 1''', ('SPY',))
        row = cur.fetchone()
        if row:
            print("Latest technical indicators for SPY:")
            print("date, rsi_14, cci_20, ema_20, ema_50, ema_100, ema_200, bb_upper, bb_middle, bb_lower, macd_line, macd_signal, macd_histogram, atr_14, vwap")
            print(row)
        else:
            print("No row found for SPY.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching indicators: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--table', type=str, default='market_data', help='Table name to update')
    parser.add_argument('--ticker_col', type=str, default='ticker', help='Ticker column name')
    parser.add_argument('--ticker', type=str, default='SPY', help='Ticker to process')
    args = parser.parse_args()
    table = args.table
    ticker_col = args.ticker_col
    test_ticker = args.ticker
    MIN_ROWS = 100
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        df = get_price_data(cur, test_ticker, table, ticker_col)
        if df.empty:
            logging.error(f"No price data found for {test_ticker} in {table}")
            return
        if len(df) < MIN_ROWS:
            logging.warning(f"Not enough data for {test_ticker} in {table}: only {len(df)} rows, need at least {MIN_ROWS}. Skipping.")
            return
        indicators = calculate_indicators(df)
        update_database(cur, test_ticker, indicators, table, ticker_col)
        conn.commit()
        if validate_calculations(cur, test_ticker, table, ticker_col):
            logging.info(f"Successfully calculated and validated indicators for {test_ticker} in {table}")
        else:
            logging.error(f"Validation failed for {test_ticker} in {table}")
    except Exception as e:
        logging.error(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()
    print_latest_indicators()

if __name__ == "__main__":
    main() 