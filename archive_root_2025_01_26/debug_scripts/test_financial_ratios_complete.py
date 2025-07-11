import os
import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv
import time

print("[DEBUG] Script started.")

# Add the daily_run directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def test_database_connection():
    print("[DEBUG] Testing database connection...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Database connected successfully: {version[0]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def ensure_stocks_exist(tickers):
    print("[DEBUG] Ensuring all tickers exist in stocks table...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for ticker in tickers:
            cur.execute("SELECT ticker FROM stocks WHERE ticker = %s", (ticker,))
            if not cur.fetchone():
                print(f"⚠️  Ticker {ticker} not found in stocks table. Adding it...")
                cur.execute("""
                    INSERT INTO stocks (ticker, company_name, sector, industry) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (ticker) DO NOTHING
                """, (ticker, f"{ticker} Corp", "Technology", "Technology"))
        conn.commit()
        cur.close()
        conn.close()
        print("✅ All tickers ensured to exist in stocks table")
        return True
    except Exception as e:
        print(f"❌ Error ensuring tickers exist: {e}")
        return False

def retrieve_fundamental_data_with_fallback(ticker):
    print(f"[DEBUG] Starting fundamental data retrieval for {ticker}...")
    # Phase 1: Yahoo Finance (primary)
    yahoo_success = False
    try:
        from daily_run.yahoo_finance_service import YahooFinanceService
        print(f"[DEBUG] Instantiating YahooFinanceService for {ticker}...")
        yahoo_service = YahooFinanceService()
        print(f"[DEBUG] Calling get_fundamental_data for {ticker}...")
        data = yahoo_service.get_fundamental_data(ticker)
        yahoo_service.close()
        print(f"[DEBUG] YahooFinanceService closed for {ticker}.")
        if data and (data.get('financial_data') or data.get('key_stats')):
            print(f"    ✅ Yahoo Finance data retrieved for {ticker}")
            yahoo_success = True
        else:
            print(f"    ⚠️  Yahoo Finance returned no data for {ticker}")
    except Exception as e:
        print(f"    ❌ Yahoo Finance error for {ticker}: {e}")
    # Check if we have complete data from Yahoo (including key metrics)
    if yahoo_success:
        try:
            print(f"[DEBUG] Checking Yahoo data completeness for {ticker}...")
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT diluted_eps_ttm, book_value_per_share, market_cap, revenue_ttm
                FROM stocks WHERE ticker = %s
            """, (ticker,))
            yahoo_data = cur.fetchone()
            cur.close()
            conn.close()
            if yahoo_data and all(yahoo_data):
                print(f"    ✅ Yahoo Finance provided complete data for {ticker}")
                return True
            else:
                print(f"    ⚠️  Yahoo Finance missing key metrics for {ticker}, trying other services...")
        except Exception as e:
            print(f"    ❌ Error checking Yahoo data completeness for {ticker}: {e}")
    # Phase 2: Finnhub (first fallback)
    try:
        print(f"[DEBUG] Instantiating FinnhubService for {ticker}...")
        from daily_run.finnhub_service import FinnhubService
        finnhub_service = FinnhubService()
        print(f"[DEBUG] Calling get_fundamental_data for {ticker} (Finnhub)...")
        data = finnhub_service.get_fundamental_data(ticker)
        finnhub_service.close()
        print(f"[DEBUG] FinnhubService closed for {ticker}.")
        if data and (data.get('financial_data') or data.get('profile_data')):
            print(f"    ✅ Finnhub data retrieved for {ticker}")
            try:
                print(f"[DEBUG] Checking Finnhub data completeness for {ticker}...")
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()
                cur.execute("""
                    SELECT diluted_eps_ttm, book_value_per_share, market_cap, revenue_ttm
                    FROM stocks WHERE ticker = %s
                """, (ticker,))
                finnhub_data = cur.fetchone()
                cur.close()
                conn.close()
                if finnhub_data and all(finnhub_data):
                    print(f"    ✅ Finnhub provided complete data for {ticker}")
                    return True
                else:
                    print(f"    ⚠️  Finnhub missing key metrics for {ticker}, trying Alpha Vantage...")
            except Exception as e:
                print(f"    ❌ Error checking Finnhub data completeness for {ticker}: {e}")
        else:
            print(f"    ⚠️  Finnhub returned no data for {ticker}")
    except Exception as e:
        print(f"    ❌ Finnhub error for {ticker}: {e}")
    # Phase 3: Alpha Vantage (second fallback)
    try:
        print(f"[DEBUG] Instantiating AlphaVantageService for {ticker}...")
        from daily_run.alpha_vantage_service import AlphaVantageService
        alpha_service = AlphaVantageService()
        print(f"[DEBUG] Calling get_fundamental_data for {ticker} (Alpha Vantage)...")
        data = alpha_service.get_fundamental_data(ticker)
        alpha_service.close()
        print(f"[DEBUG] AlphaVantageService closed for {ticker}.")
        if data and (data.get('income_statement') or data.get('balance_sheet') or data.get('cash_flow')):
            print(f"    ✅ Alpha Vantage data retrieved for {ticker}")
            try:
                print(f"[DEBUG] Checking Alpha Vantage data completeness for {ticker}...")
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()
                cur.execute("""
                    SELECT diluted_eps_ttm, book_value_per_share, market_cap, revenue_ttm
                    FROM stocks WHERE ticker = %s
                """, (ticker,))
                alpha_data = cur.fetchone()
                cur.close()
                conn.close()
                if alpha_data and all(alpha_data):
                    print(f"    ✅ Alpha Vantage provided complete data for {ticker}")
                    return True
                else:
                    print(f"    ⚠️  Alpha Vantage missing key metrics for {ticker}, trying FMP...")
            except Exception as e:
                print(f"    ❌ Error checking Alpha Vantage data completeness for {ticker}: {e}")
        else:
            print(f"    ⚠️  Alpha Vantage returned no data for {ticker}")
    except Exception as e:
        print(f"    ❌ Alpha Vantage error for {ticker}: {e}")
    # Phase 4: FMP (third fallback)
    try:
        print(f"[DEBUG] Instantiating FMPService for {ticker}...")
        from daily_run.fmp_service import FMPService
        fmp_service = FMPService()
        print(f"[DEBUG] Calling get_fundamental_data for {ticker} (FMP)...")
        data = fmp_service.get_fundamental_data(ticker)
        fmp_service.close()
        print(f"[DEBUG] FMPService closed for {ticker}.")
        if data and (data.get('income_statement') or data.get('balance_sheet') or data.get('cash_flow')):
            print(f"    ✅ FMP data retrieved for {ticker}")
            try:
                print(f"[DEBUG] Checking FMP data completeness for {ticker}...")
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()
                cur.execute("""
                    SELECT diluted_eps_ttm, book_value_per_share, market_cap, revenue_ttm
                    FROM stocks WHERE ticker = %s
                """, (ticker,))
                fmp_data = cur.fetchone()
                cur.close()
                conn.close()
                if fmp_data and all(fmp_data):
                    print(f"    ✅ FMP provided complete data for {ticker}")
                    return True
                else:
                    print(f"    ⚠️  FMP missing key metrics for {ticker}, trying previous DB data...")
            except Exception as e:
                print(f"    ❌ Error checking FMP data completeness for {ticker}: {e}")
        else:
            print(f"    ⚠️  FMP returned no data for {ticker}")
    except Exception as e:
        print(f"    ❌ FMP error for {ticker}: {e}")
    print(f"[DEBUG] Fallbacks exhausted for {ticker}.")
    return False

def retrieve_fundamental_data(tickers):
    print("[DEBUG] Starting fundamental data retrieval for all tickers...")
    results = []
    for ticker in tickers:
        print(f"[DEBUG] Processing {ticker}...")
        result = retrieve_fundamental_data_with_fallback(ticker)
        results.append(result)
    print("[DEBUG] Fundamental data retrieval complete for all tickers.")
    return results

def calculate_financial_ratios(tickers):
    print("[DEBUG] Starting financial ratios calculation...")
    try:
        from daily_run.ratios_calculator import RatiosCalculator
        calculator = RatiosCalculator()
        successful_calculations = 0
        failed_calculations = 0
        for ticker in tickers:
            print(f"[DEBUG] Calculating ratios for {ticker}...")
            try:
                result = calculator.calculate_all_ratios(ticker)
                if result and 'error' not in result:
                    ratios = result.get('ratios', {})
                    data_quality = result.get('data_quality_score', 0)
                    if store_ratios_in_database(calculator.db.connection, ticker, ratios):
                        successful_calculations += 1
                        print(f"    ✅ Calculated and stored ratios for {ticker} (Quality: {data_quality}%)")
                        for ratio_name, ratio_value in ratios.items():
                            if ratio_value is not None:
                                print(f"      {ratio_name}: {ratio_value:.2f}")
                            else:
                                print(f"      {ratio_name}: N/A")
                    else:
                        failed_calculations += 1
                        print(f"    ❌ Failed to store ratios for {ticker}")
                else:
                    failed_calculations += 1
                    error_msg = result.get('error', 'Unknown error') if result else 'No result'
                    print(f"    ❌ No ratios calculated for {ticker}: {error_msg}")
            except Exception as e:
                failed_calculations += 1
                print(f"    ❌ Error calculating ratios for {ticker}: {e}")
        calculator.close()
        print(f"[DEBUG] Financial ratio calculation complete: {successful_calculations}/{len(tickers)} successful")
        return successful_calculations > 0
    except Exception as e:
        print(f"❌ Error in financial ratio calculation: {e}")
        return False

def store_ratios_in_database(conn, ticker: str, ratios: dict):
    print(f"[DEBUG] Storing ratios in database for {ticker}...")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT market_cap, total_debt, cash_and_equivalents 
            FROM stocks WHERE ticker = %s
        """, (ticker,))
        stock_data = cur.fetchone()
        market_cap = stock_data[0] if stock_data else None
        total_debt = stock_data[1] or 0 if stock_data else 0
        cash = stock_data[2] or 0 if stock_data else 0
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
            ratios.get('pe_ratio'),
            ratios.get('pb_ratio'),
            ratios.get('ps_ratio'),
            ratios.get('ev_ebitda'),
            ratios.get('graham_number'),
            market_cap,
            enterprise_value
        ))
        conn.commit()
        cur.close()
        print(f"[DEBUG] Ratios stored for {ticker}.")
        return True
    except Exception as e:
        print(f"[DEBUG] Error storing ratios for {ticker}: {e}")
        logging.error(f"Error storing ratios for {ticker}: {e}")
        return False

def create_comprehensive_csv(tickers):
    print("[DEBUG] Creating comprehensive CSV...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("[DEBUG] Database connection for CSV established.")
        query = """
        SELECT DISTINCT ON (s.ticker)
            s.ticker,
            s.company_name,
            s.sector,
            s.industry,
            s.market_cap,
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
            s.fundamentals_last_update,
            fr.calculation_date,
            fr.pe_ratio,
            fr.pb_ratio,
            fr.ps_ratio,
            fr.ev_ebitda,
            fr.graham_number,
            fr.enterprise_value,
            dc.close as latest_close,
            dc.date as latest_price_date
        FROM stocks s
        LEFT JOIN financial_ratios fr ON s.ticker = fr.ticker 
            AND fr.calculation_date = (
                SELECT MAX(calculation_date) 
                FROM financial_ratios fr2 
                WHERE fr2.ticker = s.ticker
            )
        LEFT JOIN LATERAL (
            SELECT close, date 
            FROM daily_charts dc 
            WHERE dc.ticker = s.ticker 
            ORDER BY date DESC 
            LIMIT 1
        ) dc ON true
        WHERE s.ticker = ANY(%s)
        ORDER BY s.ticker
        """
        df = pd.read_sql_query(query, conn, params=(tickers,))
        print("[DEBUG] Data fetched for CSV.")
        conn.close()
        print("[DEBUG] Database connection for CSV closed.")
        if df.empty:
            print("❌ No data found for any tickers")
            return None
        if 'latest_close' in df.columns:
            df['latest_close'] = df['latest_close'].apply(lambda x: x / 100.0 if pd.notnull(x) else x)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_financial_data_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Comprehensive CSV created: {filename}")
        print(f"[DEBUG] CSV saved as {filename}.")
        print(f"\n📊 CSV Summary:")
        print(f"  Total rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        print(f"\n📋 Data Completeness Check:")
        fundamental_columns = ['market_cap', 'diluted_eps_ttm', 'book_value_per_share', 'revenue_ttm', 'ebitda_ttm']
        ratio_columns = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'graham_number']
        print("  Fundamental Data:")
        for col in fundamental_columns:
            if col in df.columns:
                non_null_count = df[col].notna().sum()
                print(f"    {col}: {non_null_count}/{len(df)} ({non_null_count/len(df)*100:.1f}%)")
        print("  Calculated Ratios:")
        for col in ratio_columns:
            if col in df.columns:
                non_null_count = df[col].notna().sum()
                print(f"    {col}: {non_null_count}/{len(df)} ({non_null_count/len(df)*100:.1f}%)")
        return filename
    except Exception as e:
        print(f"❌ Error creating CSV: {e}")
        return None

def validate_csv_data(filename):
    print(f"[DEBUG] Validating CSV data in {filename}...")
    try:
        df = pd.read_csv(filename)
        print(f"[DEBUG] CSV loaded: {filename}, {len(df)} rows, {len(df.columns)} columns.")
        print(f"\n📊 CSV Validation Results:")
        print(f"  File: {filename}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        for idx, row in df.iterrows():
            print(f"\n  📈 {row['ticker']} Data Validation:")
            print(f"    Market Cap: ${row['market_cap']:,.0f}")
            print(f"    P/E Ratio: {row['pe_ratio']}")
            print(f"    P/B Ratio: {row['pb_ratio']}")
            print(f"    P/S Ratio: {row['ps_ratio']}")
            print(f"    Graham Number: ${row['graham_number']}")
            print(f"    Latest Close: ${row['latest_close']}")
            if row['pb_ratio'] and row['pb_ratio'] > 20:
                print(f"      ⚠️  P/B ratio seems unusual: {row['pb_ratio']}")
        print("[DEBUG] CSV validation complete.")
        data_completeness = (df[['market_cap', 'diluted_eps_ttm', 'book_value_per_share', 'revenue_ttm', 'ebitda_ttm', 'pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'graham_number']].notna().sum().sum()) / (len(df) * 10) * 100
        print(f"\n📋 Overall Data Quality:\n  Data Completeness: {data_completeness:.1f}%")
        if data_completeness >= 80:
            print("  ✅ Data quality is good (≥80% complete)")
        else:
            print("  ⚠️  Data quality is below 80%!")
        print("[DEBUG] CSV data validation finished.")
        return True
    except Exception as e:
        print(f"❌ Error validating CSV: {e}")
        return False

def main():
    print("[DEBUG] Main function started.")
    tickers = ['AMZN', 'AVGO', 'NVDA', 'AAPL', 'XOM']
    print(f"[DEBUG] Tickers: {tickers}")
    print("[DEBUG] Step 1: Test database connection...")
    if not test_database_connection():
        print("❌ Exiting: Database connection failed.")
        return
    print("[DEBUG] Step 2: Ensure stocks exist...")
    ensure_stocks_exist(tickers)
    print("[DEBUG] Step 3: Retrieve fundamental data...")
    retrieve_fundamental_data(tickers)
    print("[DEBUG] Step 4: Calculate financial ratios...")
    calculate_financial_ratios(tickers)
    print("[DEBUG] Step 5: Create comprehensive CSV...")
    filename = create_comprehensive_csv(tickers)
    if filename:
        print("[DEBUG] Step 6: Validate CSV data...")
        validate_csv_data(filename)
    print("[DEBUG] Script complete.")

if __name__ == "__main__":
    main() 