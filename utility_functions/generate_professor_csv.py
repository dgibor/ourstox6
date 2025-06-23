import os
import sys
import logging
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import subprocess

# Add the daily_run directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'daily_run'))

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_calculations_for_ticker(ticker: str) -> bool:
    """Run technical calculations for a specific ticker"""
    try:
        result = subprocess.run([
            "python", "daily_run/calc_technicals.py",
            "--table", "daily_charts",
            "--ticker_col", "ticker",
            "--ticker", ticker
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info(f"✅ Successfully calculated indicators for {ticker}")
            return True
        else:
            logging.error(f"❌ Failed to calculate indicators for {ticker}: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"❌ Error running calculations for {ticker}: {e}")
        return False

def get_latest_indicators_data(tickers: list) -> pd.DataFrame:
    """Get the latest technical indicators data for the specified tickers"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Get the most recent data for each ticker
        query = """
        SELECT DISTINCT ON (ticker)
            ticker,
            date,
            open,
            high,
            low,
            close,
            volume,
            rsi_14,
            cci_20,
            atr_14,
            ema_20,
            ema_50,
            ema_100,
            ema_200,
            macd_line,
            macd_signal,
            macd_histogram,
            bb_upper,
            bb_middle,
            bb_lower,
            vwap,
            stoch_k,
            stoch_d,
            pivot_point,
            resistance_1,
            resistance_2,
            resistance_3,
            support_1,
            support_2,
            support_3,
            swing_high_5d,
            swing_low_5d,
            swing_high_10d,
            swing_low_10d,
            swing_high_20d,
            swing_low_20d,
            week_high,
            week_low,
            month_high,
            month_low,
            nearest_support,
            nearest_resistance,
            support_strength,
            resistance_strength
        FROM daily_charts
        WHERE ticker = ANY(%s)
        ORDER BY ticker, date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(tickers,))
        conn.close()
        
        # Convert price data from integer format (divide by 100)
        price_columns = ['open', 'high', 'low', 'close', 'ema_20', 'ema_50', 'ema_100', 'ema_200',
                        'bb_upper', 'bb_middle', 'bb_lower', 'vwap', 'pivot_point',
                        'resistance_1', 'resistance_2', 'resistance_3', 'support_1', 'support_2', 'support_3',
                        'swing_high_5d', 'swing_low_5d', 'swing_high_10d', 'swing_low_10d',
                        'swing_high_20d', 'swing_low_20d', 'week_high', 'week_low', 'month_high', 'month_low',
                        'nearest_support', 'nearest_resistance']
        
        for col in price_columns:
            if col in df.columns:
                df[col] = df[col] / 100.0
        
        # Convert indicator values from integer format (divide by 100)
        indicator_columns = ['rsi_14', 'cci_20', 'stoch_k', 'stoch_d', 'support_strength', 'resistance_strength']
        for col in indicator_columns:
            if col in df.columns:
                df[col] = df[col] / 100.0
        
        return df
        
    except Exception as e:
        logging.error(f"❌ Error fetching data from database: {e}")
        return pd.DataFrame()

def get_data_availability_summary(tickers: list) -> pd.DataFrame:
    """Get a summary of data availability for each ticker"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        query = """
        SELECT 
            ticker,
            COUNT(*) as total_records,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as rsi_records,
            COUNT(CASE WHEN cci_20 IS NOT NULL THEN 1 END) as cci_records,
            COUNT(CASE WHEN ema_20 IS NOT NULL THEN 1 END) as ema_20_records,
            COUNT(CASE WHEN ema_50 IS NOT NULL THEN 1 END) as ema_50_records,
            COUNT(CASE WHEN ema_100 IS NOT NULL THEN 1 END) as ema_100_records,
            COUNT(CASE WHEN ema_200 IS NOT NULL THEN 1 END) as ema_200_records,
            COUNT(CASE WHEN macd_line IS NOT NULL THEN 1 END) as macd_records,
            COUNT(CASE WHEN bb_upper IS NOT NULL THEN 1 END) as bb_records,
            COUNT(CASE WHEN atr_14 IS NOT NULL THEN 1 END) as atr_records,
            COUNT(CASE WHEN vwap IS NOT NULL THEN 1 END) as vwap_records,
            COUNT(CASE WHEN stoch_k IS NOT NULL THEN 1 END) as stoch_records
        FROM daily_charts
        WHERE ticker = ANY(%s)
        GROUP BY ticker
        ORDER BY ticker
        """
        
        df = pd.read_sql_query(query, conn, params=(tickers,))
        conn.close()
        
        return df
        
    except Exception as e:
        logging.error(f"❌ Error fetching data availability summary: {e}")
        return pd.DataFrame()

def main():
    # List of tickers to process
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 'UNH', 'V']
    
    print(f"🚀 Starting technical indicator calculations for {len(tickers)} tickers...")
    print(f"Tickers: {', '.join(tickers)}")
    print()
    
    # Step 1: Run calculations for each ticker
    successful_calculations = 0
    for ticker in tickers:
        print(f"📊 Processing {ticker}...")
        if run_calculations_for_ticker(ticker):
            successful_calculations += 1
        print()
    
    print(f"✅ Completed calculations: {successful_calculations}/{len(tickers)} tickers successful")
    print()
    
    # Step 2: Get the latest indicators data
    print("📈 Fetching latest technical indicators data...")
    indicators_df = get_latest_indicators_data(tickers)
    
    if indicators_df.empty:
        print("❌ No data retrieved. Exiting.")
        return
    
    # Step 3: Get data availability summary
    print("📋 Generating data availability summary...")
    availability_df = get_data_availability_summary(tickers)
    
    # Step 4: Create CSV files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Main indicators CSV
    indicators_filename = f"technical_indicators_{timestamp}.csv"
    indicators_df.to_csv(indicators_filename, index=False)
    print(f"💾 Saved main indicators data to: {indicators_filename}")
    
    # Data availability summary CSV
    availability_filename = f"data_availability_summary_{timestamp}.csv"
    availability_df.to_csv(availability_filename, index=False)
    print(f"💾 Saved data availability summary to: {availability_filename}")
    
    # Step 5: Print summary
    print()
    print("📊 SUMMARY:")
    print(f"Total tickers processed: {len(tickers)}")
    print(f"Successful calculations: {successful_calculations}")
    print(f"Tickers with data: {len(indicators_df)}")
    print()
    
    print("📋 INDICATORS CALCULATED:")
    indicator_columns = ['rsi_14', 'cci_20', 'atr_14', 'ema_20', 'ema_50', 'ema_100', 'ema_200',
                        'macd_line', 'macd_signal', 'macd_histogram', 'bb_upper', 'bb_middle', 'bb_lower',
                        'vwap', 'stoch_k', 'stoch_d', 'pivot_point']
    
    for col in indicator_columns:
        if col in indicators_df.columns:
            non_null_count = indicators_df[col].notna().sum()
            print(f"  {col}: {non_null_count}/{len(indicators_df)} tickers")
    
    print()
    print("📁 FILES CREATED:")
    print(f"  {indicators_filename} - Latest technical indicators for all tickers")
    print(f"  {availability_filename} - Data availability summary")
    print()
    print("🎯 Ready for professor validation!")

if __name__ == "__main__":
    main() 