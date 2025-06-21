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
from indicators.stochastic import calculate_stochastic
from indicators.support_resistance import calculate_support_resistance
from indicators.adx import calculate_adx

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
    
    # Convert price data back to normal scale (divide by 100) for calculations
    # Price data is stored as integers (multiplied by 100) in the database
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if col in df.columns:
            df[col] = df[col] / 100.0
    
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
    
    # ADX (needs 28+ days for meaningful results - 14 for TR/DM + 14 for smoothing)
    if data_length >= 28:
        try:
            indicators['adx_14'] = calculate_adx(df['high'], df['low'], df['close'])
        except Exception as e:
            logging.warning(f"Failed to calculate ADX: {e}")
    
    # VWAP (needs 1+ days)
    if data_length >= 1:
        try:
            indicators['vwap'] = calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
        except Exception as e:
            logging.warning(f"Failed to calculate VWAP: {e}")
    
    # Stochastic Oscillator (needs 14+ days)
    if data_length >= 14:
        try:
            stoch_k, stoch_d = calculate_stochastic(df['high'], df['low'], df['close'])
            indicators['stoch_k'] = stoch_k
            indicators['stoch_d'] = stoch_d
        except Exception as e:
            logging.warning(f"Failed to calculate Stochastic: {e}")
    
    # Support and Resistance (needs 20+ days for meaningful results)
    if data_length >= 20:
        try:
            sr_indicators = calculate_support_resistance(df['high'], df['low'], df['close'])
            indicators.update(sr_indicators)
        except Exception as e:
            logging.warning(f"Failed to calculate Support/Resistance: {e}")
    
    return indicators

def update_database(cur, ticker: str, indicators: dict, table: str, ticker_col: str):
    """Update the database with calculated indicators for ALL records"""
    if not indicators:
        logging.warning(f"No indicators calculated for {ticker}")
        return
    
    # Get all available indicators that are not None
    available_indicators = [ind for ind in indicators.values() if ind is not None]
    if not available_indicators:
        logging.warning(f"No valid indicators for {ticker}")
        return
    
    # Get all dates from the first available indicator (they should all have the same index)
    all_dates = available_indicators[0].index
    
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
        'adx_14': 'adx_14',
        'vwap': 'vwap',
        'stoch_k': 'stoch_k',
        'stoch_d': 'stoch_d',
        'resistance_1': 'resistance_1',
        'resistance_2': 'resistance_2',
        'resistance_3': 'resistance_3',
        'support_1': 'support_1',
        'support_2': 'support_2',
        'support_3': 'support_3',
        'swing_high_5d': 'swing_high_5d',
        'swing_low_5d': 'swing_low_5d',
        'swing_high_10d': 'swing_high_10d',
        'swing_low_10d': 'swing_low_10d',
        'swing_high_20d': 'swing_high_20d',
        'swing_low_20d': 'swing_low_20d',
        'week_high': 'week_high',
        'week_low': 'week_low',
        'month_high': 'month_high',
        'month_low': 'month_low',
        'nearest_support': 'nearest_support',
        'nearest_resistance': 'nearest_resistance',
        'support_strength': 'support_strength',
        'resistance_strength': 'resistance_strength',
        'pivot_point': 'pivot_point'
    }
    
    updated_count = 0
    
    # Update ALL records, not just the latest
    for date_idx in all_dates:
        date_str = date_idx.strftime('%Y-%m-%d')
        
        # Build update values for this specific date
        update_fields = []
        values = []
        
        for indicator_key, db_column in indicator_mappings.items():
            if indicator_key in indicators and indicators[indicator_key] is not None:
                indicator_series = indicators[indicator_key]
                if date_idx in indicator_series.index:
                    value = indicator_series.loc[date_idx]
                    if pd.notna(value):
                        update_fields.append(f"{db_column} = %s")
                        # Convert to integer (multiply by 100 to maintain precision)
                        values.append(int(round(value * 100)))
        
        if update_fields:
            values.extend([ticker, date_str])
            update_query = f"""
                UPDATE {table}
                SET {', '.join(update_fields)}
                WHERE {ticker_col} = %s AND date = %s
            """
            cur.execute(update_query, values)
            updated_count += 1
    
    logging.info(f"Updated {updated_count} records for {ticker}")

def validate_calculations(cur, ticker: str, table: str, ticker_col: str) -> bool:
    """Validate that the calculations were inserted correctly"""
    cur.execute(f"""
        SELECT 
            rsi_14, cci_20, ema_20, ema_50, ema_100, ema_200,
            bb_upper, bb_middle, bb_lower,
            macd_line, macd_signal, macd_histogram,
            atr_14, adx_14, vwap, stoch_k, stoch_d,
            resistance_1, resistance_2, resistance_3,
            support_1, support_2, support_3,
            swing_high_5d, swing_low_5d, swing_high_10d, swing_low_10d,
            swing_high_20d, swing_low_20d, week_high, week_low,
            month_high, month_low, nearest_support, nearest_resistance,
            support_strength, resistance_strength, pivot_point
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
        cur.execute('''SELECT date, rsi_14, cci_20, ema_20, ema_50, ema_100, ema_200, bb_upper, bb_middle, bb_lower, macd_line, macd_signal, macd_histogram, atr_14, adx_14, vwap, stoch_k, stoch_d, resistance_1, resistance_2, resistance_3, support_1, support_2, support_3, swing_high_5d, swing_low_5d, pivot_point FROM market_data WHERE ticker = %s ORDER BY date DESC LIMIT 1''', ('SPY',))
        row = cur.fetchone()
        if row:
            print("Latest technical indicators for SPY:")
            print("date, rsi_14, cci_20, ema_20, ema_50, ema_100, ema_200, bb_upper, bb_middle, bb_lower, macd_line, macd_signal, macd_histogram, atr_14, adx_14, vwap, stoch_k, stoch_d, resistance_1, resistance_2, resistance_3, support_1, support_2, support_3, swing_high_5d, swing_low_5d, pivot_point")
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