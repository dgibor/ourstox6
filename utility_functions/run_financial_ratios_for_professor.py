import os
import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

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

def safe_float(value):
    """Converts a value to a float, returning None if conversion fails or value is None."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def get_all_data_as_floats(conn, ticker: str):
    """
    Fetches all necessary data for a ticker and converts all numeric fields to floats.
    This is the definitive, type-safe way to get data for calculations.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get all fundamental and price data in one go
        cur.execute("""
            SELECT 
                s.ticker, s.market_cap, s.shares_outstanding, s.diluted_eps_ttm, 
                s.book_value_per_share, s.revenue_ttm, s.net_income_ttm, 
                s.total_assets, s.total_debt, s.shareholders_equity, 
                s.current_assets, s.current_liabilities, s.cash_and_equivalents,
                s.ebitda_ttm,
                (SELECT dc.close FROM daily_charts dc WHERE dc.ticker = s.ticker ORDER BY dc.date DESC LIMIT 1) as latest_close
            FROM stocks s
            WHERE s.ticker = %s;
        """, (ticker,))
        data = cur.fetchone()

        if not data:
            logging.warning(f"No stock data found for {ticker}")
            return None

        # Convert all numeric values to floats for safe calculations
        float_data = {key: safe_float(value) for key, value in data.items()}

        # Handle specific conversions
        if float_data.get('latest_close'):
            float_data['latest_close'] /= 100.0  # Convert cents to dollars

        return float_data

def store_ratios_in_database(conn, ticker: str, ratios: dict, stock_data: dict):
    """Store calculated ratios in the financial_ratios table, handling None values"""
    try:
        cur = conn.cursor()
        # Safely compute enterprise value
        market_cap = stock_data.get('market_cap')
        total_debt = stock_data.get('total_debt') or 0
        cash = stock_data.get('cash_and_equivalents') or 0
        enterprise_value = market_cap + total_debt - cash if market_cap is not None else None
        cur.execute("""
            INSERT INTO financial_ratios 
            (ticker, calculation_date, pe_ratio, pb_ratio, ps_ratio, ev_ebitda, graham_number, market_cap, enterprise_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, calculation_date)
            DO UPDATE SET
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                ps_ratio = EXCLUDED.ps_ratio,
                ev_ebitda = EXCLUDED.ev_ebitda,
                graham_number = EXCLUDED.graham_number,
                market_cap = EXCLUDED.market_cap,
                enterprise_value = EXCLUDED.enterprise_value,
                last_updated = CURRENT_TIMESTAMP
        """, (
            ticker,
            datetime.now().date(),
            ratios.get('pe_ratio', {}).get('value'),
            ratios.get('pb_ratio', {}).get('value'),
            ratios.get('ps_ratio', {}).get('value'),
            ratios.get('ev_ebitda', {}).get('value'),
            ratios.get('graham_number', {}).get('value'),
            market_cap,
            enterprise_value
        ))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        logging.error(f"Error storing ratios for {ticker}: {e}")
        return False

def get_stock_data_for_calculation(conn, ticker: str):
    """DEPRECATED - Replaced by get_all_data_as_floats"""
    pass

def calculate_pe_ratio(current_price: float, diluted_eps_ttm: float):
    """Calculate P/E ratio"""
    if diluted_eps_ttm is None or diluted_eps_ttm <= 0:
        return None, "N/A - Negative Earnings"
    
    if current_price is None or current_price <= 0:
        return None, "N/A - Invalid Price"
    
    pe_ratio = current_price / diluted_eps_ttm
    capped_ratio = min(pe_ratio, 999)
    
    quality_flag = "Normal"
    if pe_ratio > 999:
        quality_flag = "Capped - Extreme Value"
    
    return capped_ratio, quality_flag

def calculate_pb_ratio(market_cap: float, shareholders_equity: float):
    """Calculate P/B ratio"""
    if shareholders_equity is None or shareholders_equity <= 0:
        return None, "N/A - Negative Book Value"
    
    if market_cap is None or market_cap <= 0:
        return None, "N/A - Invalid Market Cap"
    
    pb_ratio = market_cap / shareholders_equity
    return pb_ratio, "Normal"

def calculate_ev_ebitda(market_cap: float, total_debt: float, cash: float, ebitda_ttm: float):
    """Calculate EV/EBITDA ratio"""
    if ebitda_ttm is None or ebitda_ttm <= 0:
        return None, "N/A - Negative EBITDA"
    
    if market_cap is None or market_cap <= 0:
        return None, "N/A - Invalid Market Cap"
    
    total_debt = total_debt or 0
    cash = cash or 0
    
    enterprise_value = market_cap + total_debt - cash
    ev_ebitda_ratio = enterprise_value / ebitda_ttm
    
    return ev_ebitda_ratio, "Normal"

def calculate_ps_ratio(market_cap: float, revenue_ttm: float):
    """Calculate P/S ratio"""
    if revenue_ttm is None or revenue_ttm <= 0:
        return None, "N/A - No Revenue"
    
    if market_cap is None or market_cap <= 0:
        return None, "N/A - Invalid Market Cap"
    
    ps_ratio = market_cap / revenue_ttm
    capped_ratio = min(ps_ratio, 50)
    
    quality_flag = "Normal"
    if ps_ratio > 50:
        quality_flag = "Capped - High P/S Ratio"
    
    return capped_ratio, quality_flag

def calculate_graham_number(diluted_eps_ttm: float, book_value_per_share: float):
    """Calculate Graham Number"""
    import math
    
    if diluted_eps_ttm is None or diluted_eps_ttm <= 0 or book_value_per_share is None or book_value_per_share <= 0:
        return None, "N/A - Requires Positive Earnings & Book Value"
    
    graham_number = math.sqrt(15 * diluted_eps_ttm * book_value_per_share)
    return graham_number, "Normal"

def calculate_all_ratios_for_ticker(conn, ticker: str):
    """
    Calculates all financial ratios for a ticker using clean, float-only data.
    """
    stock_data = get_all_data_as_floats(conn, ticker)
    if not stock_data:
        logging.warning(f"No data available for {ticker} after processing.")
        return None, None

    ratios = {}
    
    # All data is now guaranteed to be float or None, so we can calculate safely.
    latest_close = stock_data.get('latest_close')
    diluted_eps = stock_data.get('diluted_eps_ttm')
    market_cap = stock_data.get('market_cap')
    equity = stock_data.get('shareholders_equity')
    ebitda = stock_data.get('ebitda_ttm')
    debt = stock_data.get('total_debt')
    cash = stock_data.get('cash_and_equivalents')
    revenue = stock_data.get('revenue_ttm')
    bvps = stock_data.get('book_value_per_share')

    pe_ratio, pe_flag = calculate_pe_ratio(latest_close, diluted_eps)
    ratios['pe_ratio'] = {'value': pe_ratio, 'quality_flag': pe_flag}

    pb_ratio, pb_flag = calculate_pb_ratio(market_cap, equity)
    ratios['pb_ratio'] = {'value': pb_ratio, 'quality_flag': pb_flag}

    ev_ebitda, ev_flag = calculate_ev_ebitda(market_cap, debt, cash, ebitda)
    ratios['ev_ebitda'] = {'value': ev_ebitda, 'quality_flag': ev_flag}

    ps_ratio, ps_flag = calculate_ps_ratio(market_cap, revenue)
    ratios['ps_ratio'] = {'value': ps_ratio, 'quality_flag': ps_flag}

    graham_number, gn_flag = calculate_graham_number(diluted_eps, bvps)
    ratios['graham_number'] = {'value': graham_number, 'quality_flag': gn_flag}

    return ratios, stock_data

def get_latest_ratios_from_database(tickers: list):
    """Get the latest calculated ratios and all input data from the database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        query = """
        SELECT DISTINCT ON (fr.ticker)
            fr.ticker,
            fr.calculation_date,
            fr.pe_ratio,
            fr.pb_ratio,
            fr.ps_ratio,
            fr.ev_ebitda,
            fr.graham_number,
            fr.market_cap,
            fr.enterprise_value,
            s.company_name,
            s.sector,
            s.industry,
            -- Add all input fields used for calculations
            s.shares_outstanding,
            s.diluted_eps_ttm,
            s.book_value_per_share,
            s.revenue_ttm,
            s.net_income_ttm,
            s.total_assets,
            s.total_debt,
            s.shareholders_equity,
            s.current_assets,
            s.current_liabilities,
            s.cash_and_equivalents,
            s.operating_income,
            s.ebitda_ttm,
            dc.close as latest_close
        FROM financial_ratios fr
        JOIN stocks s ON fr.ticker = s.ticker
        LEFT JOIN LATERAL (
            SELECT close FROM daily_charts dc WHERE dc.ticker = fr.ticker ORDER BY date DESC LIMIT 1
        ) dc ON true
        WHERE fr.ticker = ANY(%s)
        ORDER BY fr.ticker, fr.calculation_date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(tickers,))
        conn.close()
        
        # Convert latest_close from int to float price if present
        if 'latest_close' in df.columns:
            df['latest_close'] = df['latest_close'].apply(lambda x: x / 100.0 if pd.notnull(x) else x)
        
        return df
        
    except Exception as e:
        logging.error(f"Error fetching ratios from database: {e}")
        return pd.DataFrame()

def main():
    # List of tickers to process
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 'UNH', 'V']
    
    print(f"🚀 Starting financial ratio calculations for {len(tickers)} tickers...")
    print(f"Tickers: {', '.join(tickers)}")
    print()
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    # Step 1: Calculate and store ratios for each ticker
    successful_calculations = 0
    failed_calculations = 0
    
    for ticker in tickers:
        print(f"📊 Processing {ticker}...")
        
        # Use the new, robust calculation function
        ratios, stock_data = calculate_all_ratios_for_ticker(conn, ticker)
        
        if ratios and stock_data:
            # Store in database
            if store_ratios_in_database(conn, ticker, ratios, stock_data):
                successful_calculations += 1
                print(f"  ✅ Calculated and stored ratios for {ticker}")
                
                # Print summary of calculated ratios
                for ratio_name, ratio_data in ratios.items():
                    value = ratio_data.get('value')
                    flag = ratio_data.get('quality_flag')
                    if value is not None:
                        print(f"    {ratio_name}: {value:.2f} ({flag})")
                    else:
                        print(f"    {ratio_name}: {flag}")
            else:
                failed_calculations += 1
                print(f"  ❌ Failed to store ratios for {ticker}")
        else:
            failed_calculations += 1
            print(f"  ❌ No data available for {ticker}")
        
        print()
    
    print(f"✅ Completed calculations: {successful_calculations}/{len(tickers)} tickers successful")
    print()
    
    # Step 2: Get the latest ratios from database and create CSV
    print("📈 Fetching latest ratios from database...")
    ratios_df = get_latest_ratios_from_database(tickers)
    
    if ratios_df.empty:
        print("❌ No ratios found in database. Exiting.")
        return
    
    # Step 3: Create CSV files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Main ratios CSV
    ratios_filename = f"financial_ratios_{timestamp}.csv"
    ratios_df.to_csv(ratios_filename, index=False)
    print(f"💾 Saved financial ratios to: {ratios_filename}")
    
    # Step 4: Print summary
    print()
    print("📊 SUMMARY:")
    print(f"Total tickers processed: {len(tickers)}")
    print(f"Successful calculations: {successful_calculations}")
    print(f"Failed calculations: {failed_calculations}")
    print(f"Tickers with ratios in CSV: {len(ratios_df)}")
    print()
    
    print("📋 RATIOS CALCULATED:")
    ratio_columns = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'graham_number']
    for col in ratio_columns:
        if col in ratios_df.columns:
            non_null_count = ratios_df[col].notna().sum()
            print(f"  {col}: {non_null_count}/{len(ratios_df)} tickers")
    
    print()
    print("📁 FILES CREATED:")
    print(f"  {ratios_filename} - Financial ratios for all tickers")
    print()
    print("🎯 Ready for professor validation!")
    
    # Close database connection
    conn.close()

if __name__ == "__main__":
    main() 