import os
import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv
import time

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
    """Test database connection"""
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
    """Ensure all tickers exist in the stocks table"""
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
    """
    Retrieve fundamental data using multi-service fallback system:
    Yahoo → Finnhub → Alpha Vantage → FMP → Previous DB data
    """
    print(f"  Processing {ticker} with multi-service fallback...")
    
    # Phase 1: Yahoo Finance (primary)
    yahoo_success = False
    try:
        from daily_run.yahoo_finance_service import YahooFinanceService
        yahoo_service = YahooFinanceService()
        data = yahoo_service.get_fundamental_data(ticker)
        yahoo_service.close()
        
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
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT diluted_eps_ttm, book_value_per_share, market_cap, revenue_ttm
                FROM stocks WHERE ticker = %s
            """, (ticker,))
            yahoo_data = cur.fetchone()
            cur.close()
            conn.close()
            
            # If we have all key metrics, we're done
            if yahoo_data and all(yahoo_data):
                print(f"    ✅ Yahoo Finance provided complete data for {ticker}")
                return True
            else:
                print(f"    ⚠️  Yahoo Finance missing key metrics for {ticker}, trying other services...")
        except Exception as e:
            print(f"    ❌ Error checking Yahoo data completeness for {ticker}: {e}")
    
    # Phase 2: Finnhub (first fallback)
    try:
        from daily_run.finnhub_service import FinnhubService
        finnhub_service = FinnhubService()
        data = finnhub_service.get_fundamental_data(ticker)
        finnhub_service.close()
        
        if data and (data.get('financial_data') or data.get('profile_data')):
            print(f"    ✅ Finnhub data retrieved for {ticker}")
            
            # Check if Finnhub provided complete data
            try:
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
        from daily_run.alpha_vantage_service import AlphaVantageService
        alpha_service = AlphaVantageService()
        data = alpha_service.get_fundamental_data(ticker)
        alpha_service.close()
        
        if data and (data.get('income_statement') or data.get('balance_sheet') or data.get('cash_flow')):
            print(f"    ✅ Alpha Vantage data retrieved for {ticker}")
            
            # Check if Alpha Vantage provided complete data
            try:
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
        from daily_run.fmp_service import FMPService
        fmp_service = FMPService()
        data = fmp_service.get_fundamental_data(ticker)
        fmp_service.close()
        
        if data and (data.get('income_statement') or data.get('balance_sheet') or data.get('cash_flow')):
            print(f"    ✅ FMP data retrieved for {ticker}")
            
            # Check if FMP provided complete data
            try:
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
                    print(f"    ⚠️  FMP missing key metrics for {ticker}")
            except Exception as e:
                print(f"    ❌ Error checking FMP data completeness for {ticker}: {e}")
        else:
            print(f"    ⚠️  FMP returned no data for {ticker}")
    except Exception as e:
        print(f"    ❌ FMP error for {ticker}: {e}")
    
    # Phase 5: Check if we have any existing data in database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT market_cap, diluted_eps_ttm, book_value_per_share, revenue_ttm, ebitda_ttm
            FROM stocks WHERE ticker = %s
        """, (ticker,))
        existing_data = cur.fetchone()
        cur.close()
        conn.close()
        
        if existing_data and any(existing_data):
            print(f"    ⚠️  Using existing database data for {ticker}")
            return True
        else:
            print(f"    ❌ No data available from any source for {ticker}")
            return False
    except Exception as e:
        print(f"    ❌ Database check error for {ticker}: {e}")
        return False

def retrieve_fundamental_data(tickers):
    """Step 1: Retrieve fundamental data for the tickers using multi-service fallback"""
    print("\n📊 Step 1: Retrieving fundamental data with multi-service fallback...")
    
    successful_retrievals = 0
    failed_retrievals = 0
    
    for ticker in tickers:
        try:
            if retrieve_fundamental_data_with_fallback(ticker):
                successful_retrievals += 1
            else:
                failed_retrievals += 1
            
            # Add delay between tickers to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            failed_retrievals += 1
            print(f"    ❌ Unexpected error for {ticker}: {e}")
    
    print(f"✅ Fundamental data retrieval complete: {successful_retrievals}/{len(tickers)} successful")
    return successful_retrievals > 0

def calculate_financial_ratios(tickers):
    """Step 2: Calculate financial ratios for the tickers"""
    print("\n🧮 Step 2: Calculating financial ratios...")
    
    try:
        from daily_run.financial_ratios_calculator import FinancialRatiosCalculator
        calculator = FinancialRatiosCalculator()
        
        successful_calculations = 0
        failed_calculations = 0
        
        for ticker in tickers:
            print(f"  Calculating ratios for {ticker}...")
            try:
                ratios = calculator.calculate_all_ratios(ticker)
                if ratios:
                    # Store ratios in database
                    if store_ratios_in_database(calculator.conn, ticker, ratios):
                        successful_calculations += 1
                        print(f"    ✅ Calculated and stored ratios for {ticker}")
                        
                        # Print summary of calculated ratios
                        for ratio_name, ratio_data in ratios.items():
                            value = ratio_data.get('value')
                            flag = ratio_data.get('quality_flag')
                            if value is not None:
                                print(f"      {ratio_name}: {value:.2f} ({flag})")
                            else:
                                print(f"      {ratio_name}: {flag}")
                    else:
                        failed_calculations += 1
                        print(f"    ❌ Failed to store ratios for {ticker}")
                else:
                    failed_calculations += 1
                    print(f"    ❌ No ratios calculated for {ticker}")
            except Exception as e:
                failed_calculations += 1
                print(f"    ❌ Error calculating ratios for {ticker}: {e}")
        
        calculator.close()
        print(f"✅ Financial ratio calculation complete: {successful_calculations}/{len(tickers)} successful")
        return successful_calculations > 0
        
    except Exception as e:
        print(f"❌ Error in financial ratio calculation: {e}")
        return False

def store_ratios_in_database(conn, ticker: str, ratios: dict):
    """Store calculated ratios in the financial_ratios table"""
    try:
        cur = conn.cursor()
        
        # Get stock data for enterprise value calculation
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

def create_comprehensive_csv(tickers):
    """Step 3: Create comprehensive CSV with all data"""
    print("\n📈 Step 3: Creating comprehensive CSV...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Query to get all fundamental data and calculated ratios
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
        conn.close()
        
        if df.empty:
            print("❌ No data found for any tickers")
            return None
        
        # Convert latest_close from cents to dollars
        if 'latest_close' in df.columns:
            df['latest_close'] = df['latest_close'].apply(lambda x: x / 100.0 if pd.notnull(x) else x)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_financial_data_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"✅ Comprehensive CSV created: {filename}")
        
        # Print summary
        print(f"\n📊 CSV Summary:")
        print(f"  Total rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        
        # Check data completeness
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
    """Step 4: Validate the CSV data for reasonableness"""
    print(f"\n🔍 Step 4: Validating CSV data in {filename}...")
    
    try:
        df = pd.read_csv(filename)
        
        print(f"📊 CSV Validation Results:")
        print(f"  File: {filename}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        
        # Check for each ticker
        for ticker in ['AMZN', 'AVGO', 'NVDA', 'AAPL', 'XOM']:
            ticker_data = df[df['ticker'] == ticker]
            if not ticker_data.empty:
                print(f"\n  📈 {ticker} Data Validation:")
                
                # Check fundamental data
                market_cap = ticker_data['market_cap'].iloc[0]
                if pd.notnull(market_cap):
                    print(f"    Market Cap: ${market_cap:,.0f}")
                
                pe_ratio = ticker_data['pe_ratio'].iloc[0]
                if pd.notnull(pe_ratio):
                    print(f"    P/E Ratio: {pe_ratio:.2f}")
                    if pe_ratio < 0 or pe_ratio > 1000:
                        print(f"      ⚠️  P/E ratio seems unusual: {pe_ratio}")
                
                pb_ratio = ticker_data['pb_ratio'].iloc[0]
                if pd.notnull(pb_ratio):
                    print(f"    P/B Ratio: {pb_ratio:.2f}")
                    if pb_ratio < 0 or pb_ratio > 50:
                        print(f"      ⚠️  P/B ratio seems unusual: {pb_ratio}")
                
                ps_ratio = ticker_data['ps_ratio'].iloc[0]
                if pd.notnull(ps_ratio):
                    print(f"    P/S Ratio: {ps_ratio:.2f}")
                    if ps_ratio < 0 or ps_ratio > 100:
                        print(f"      ⚠️  P/S ratio seems unusual: {ps_ratio}")
                
                graham_number = ticker_data['graham_number'].iloc[0]
                if pd.notnull(graham_number):
                    print(f"    Graham Number: ${graham_number:.2f}")
                
                latest_close = ticker_data['latest_close'].iloc[0]
                if pd.notnull(latest_close):
                    print(f"    Latest Close: ${latest_close:.2f}")
            else:
                print(f"    ❌ No data found for {ticker}")
        
        # Overall data quality assessment
        print(f"\n📋 Overall Data Quality:")
        total_cells = len(df) * len(df.columns)
        non_null_cells = df.notna().sum().sum()
        completeness = (non_null_cells / total_cells) * 100
        print(f"  Data Completeness: {completeness:.1f}%")
        
        if completeness >= 80:
            print("  ✅ Data quality is good (≥80% complete)")
        elif completeness >= 60:
            print("  ⚠️  Data quality is moderate (60-80% complete)")
        else:
            print("  ❌ Data quality is poor (<60% complete)")
        
        return completeness >= 60
        
    except Exception as e:
        print(f"❌ Error validating CSV: {e}")
        return False

def main():
    """Main execution function"""
    print("🚀 Starting comprehensive financial ratios test with multi-service fallback...")
    print("=" * 80)
    
    # Define test tickers
    tickers = ['AMZN', 'AVGO', 'NVDA', 'AAPL', 'XOM']
    print(f"📊 Testing with tickers: {', '.join(tickers)}")
    
    # Step 0: Test database connection
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        return
    
    # Step 0.5: Ensure tickers exist in database
    if not ensure_stocks_exist(tickers):
        print("❌ Cannot proceed without ensuring tickers exist")
        return
    
    # Step 1: Retrieve fundamental data with multi-service fallback
    if not retrieve_fundamental_data(tickers):
        print("⚠️  Fundamental data retrieval had issues, but continuing...")
    
    # Step 2: Calculate financial ratios
    if not calculate_financial_ratios(tickers):
        print("⚠️  Financial ratio calculation had issues, but continuing...")
    
    # Step 3: Create comprehensive CSV
    csv_filename = create_comprehensive_csv(tickers)
    if not csv_filename:
        print("❌ Failed to create CSV file")
        return
    
    # Step 4: Validate CSV data
    if validate_csv_data(csv_filename):
        print(f"\n✅ Test completed successfully!")
        print(f"📁 CSV file location: {os.path.abspath(csv_filename)}")
        print(f"📊 You can now review the comprehensive financial data in the CSV file.")
    else:
        print(f"\n⚠️  Test completed with data quality issues.")
        print(f"📁 CSV file location: {os.path.abspath(csv_filename)}")
        print(f"📊 Please review the CSV file and check for data quality issues.")

if __name__ == "__main__":
    main() 