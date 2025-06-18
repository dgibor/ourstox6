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
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.cci import calculate_cci
from indicators.bollinger_bands import calculate_bollinger_bands
from indicators.macd import calculate_macd
from indicators.atr import calculate_atr
from indicators.vwap import calculate_vwap

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

# Configure logging - determine correct log path based on execution context
log_dir = 'daily_run/logs' if os.path.exists('daily_run/logs') else 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/calc_technicals.log'),
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
    """Calculate all technical indicators, skipping those without sufficient data"""
    indicators = {}
    data_length = len(df)
    
    # RSI (needs 14+ days)
    if data_length >= 14:
        try:
            indicators['rsi_14'] = calculate_rsi(df['close'])
        except Exception as e:
            logging.warning(f"Failed to calculate RSI: {e}")
    
    # CCI (needs 20+ days)
    if data_length >= 20:
        try:
            indicators['cci_20'] = calculate_cci(df['high'], df['low'], df['close'])
        except Exception as e:
            logging.warning(f"Failed to calculate CCI: {e}")
    
    # EMAs (need respective periods)
    if data_length >= 20:
        try:
            indicators['ema_20'] = calculate_ema(df['close'], 20)
        except Exception as e:
            logging.warning(f"Failed to calculate EMA_20: {e}")
    
    if data_length >= 50:
        try:
            indicators['ema_50'] = calculate_ema(df['close'], 50)
        except Exception as e:
            logging.warning(f"Failed to calculate EMA_50: {e}")
    
    if data_length >= 100:
        try:
            indicators['ema_100'] = calculate_ema(df['close'], 100)
        except Exception as e:
            logging.warning(f"Failed to calculate EMA_100: {e}")
    
    if data_length >= 200:
        try:
            indicators['ema_200'] = calculate_ema(df['close'], 200)
        except Exception as e:
            logging.warning(f"Failed to calculate EMA_200: {e}")
    
    # Bollinger Bands (needs 20+ days)
    if data_length >= 20:
        try:
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df['close'])
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
        except Exception as e:
            logging.warning(f"Failed to calculate Bollinger Bands: {e}")
    
    # MACD (needs 26+ days for calculation)
    if data_length >= 26:
        try:
            macd_line, signal_line, histogram = calculate_macd(df['close'])
            indicators['macd_line'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = histogram
        except Exception as e:
            logging.warning(f"Failed to calculate MACD: {e}")
    
    # ATR (needs 14+ days)
    if data_length >= 14:
        try:
            indicators['atr_14'] = calculate_atr(df['high'], df['low'], df['close'])
        except Exception as e:
            logging.warning(f"Failed to calculate ATR: {e}")
    
    # VWAP (needs 1+ days)
    if data_length >= 1:
        try:
            indicators['vwap'] = calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
        except Exception as e:
            logging.warning(f"Failed to calculate VWAP: {e}")
    
    return indicators

def update_database(cur, ticker: str, indicators: dict, table: str, ticker_col: str):
    """Update the database with calculated indicators"""
    if not indicators:
        logging.warning(f"No indicators calculated for {ticker}")
        return
    
    # Get the latest date from any available indicator
    available_indicators = [ind for ind in indicators.values() if ind is not None]
    if not available_indicators:
        logging.warning(f"No valid indicators for {ticker}")
        return
        
    latest_date = max(available_indicators[0].index)
    
    # Build dynamic update query based on available indicators
    update_fields = []
    values = []
    
    indicator_mappings = {
        'rsi_14': 'rsi_14',
        'cci_20': 'cci_20', 
        'ema_20': 'ema_20',
        'ema_50': 'ema_50',
        'ema_100': 'ema_100',
        'ema_200': 'ema_200',
        'bb_upper': 'bb_upper',
        'bb_middle': 'bb_middle',
        'bb_lower': 'bb_lower',
        'macd_line': 'macd_line',
        'macd_signal': 'macd_signal',
        'macd_histogram': 'macd_histogram',
        'atr_14': 'atr_14',
        'vwap': 'vwap'
    }
    
    for indicator_key, db_column in indicator_mappings.items():
        if indicator_key in indicators and indicators[indicator_key] is not None:
            update_fields.append(f"{db_column} = %s")
            values.append(int(round(indicators[indicator_key].iloc[-1] * 100)))
    
    if not update_fields:
        logging.warning(f"No valid indicator values to update for {ticker}")
        return
    
    # Add ticker and date to values
    values.extend([ticker, latest_date.strftime('%Y-%m-%d')])
    
    # Prepare the update query
    update_query = f"""
        UPDATE {table}
        SET {', '.join(update_fields)}
        WHERE {ticker_col} = %s AND date = %s
    """
    
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
    MIN_ROWS = 1  # Minimum 1 row to calculate at least VWAP
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
        
        logging.info(f"Processing {test_ticker} with {len(df)} rows of data")
        indicators = calculate_indicators(df)
        
        if indicators:
            update_database(cur, test_ticker, indicators, table, ticker_col)
            conn.commit()
            logging.info(f"Successfully calculated indicators for {test_ticker} in {table}: {list(indicators.keys())}")
        else:
            logging.warning(f"No indicators could be calculated for {test_ticker} in {table}")
            
    except Exception as e:
        logging.error(f"Error: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main() 