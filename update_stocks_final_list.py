import os
import psycopg2
import pandas as pd
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/update_stocks_final_list.log'),
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

# CSV file path
CSV_FILE = 'pre_filled_stocks/updated_stock_list_300625_v10.csv'

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(**DB_CONFIG)

def update_stocks_schema():
    """Update stocks table schema to accommodate all CSV columns"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        logging.info("🔄 Updating stocks table schema...")
        
        # Add new columns for CSV data
        new_columns = [
            ('market_cap_b', 'numeric(10,2)'),
            ('description', 'text'),
            ('business_model', 'text'),
            ('products_services', 'text'),
            ('main_customers', 'text'),
            ('markets', 'text'),
            ('moat_1', 'text'),
            ('moat_2', 'text'),
            ('moat_3', 'text'),
            ('moat_4', 'text'),
            ('peer_a', 'text'),
            ('peer_b', 'text'),
            ('peer_c', 'text')
        ]
        
        for col_name, col_type in new_columns:
            cur.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='stocks' AND column_name='{col_name}'
                    ) THEN
                        ALTER TABLE stocks ADD COLUMN {col_name} {col_type};
                        RAISE NOTICE 'Added column % to stocks table', '{col_name}';
                    ELSE
                        RAISE NOTICE 'Column % already exists in stocks table', '{col_name}';
                    END IF;
                END$$;
            """)
        
        # Ensure unique constraint on ticker
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                    WHERE tc.table_name = 'stocks' AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'ticker'
                ) THEN
                    ALTER TABLE stocks ADD CONSTRAINT unique_ticker UNIQUE (ticker);
                    RAISE NOTICE 'Added unique constraint on ticker column';
                ELSE
                    RAISE NOTICE 'Unique constraint on ticker already exists';
                END IF;
            END$$;
        """)
        
        conn.commit()
        logging.info("✅ Stocks table schema updated successfully!")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"❌ Error updating schema: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def remove_foreign_key_references(tickers_to_delete):
    """Remove foreign key references to tickers that will be deleted"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        logging.info(f"Removing foreign key references for {len(tickers_to_delete)} tickers...")
        
        # List of tables that reference stocks.ticker
        dependent_tables = [
            'financial_ratios',
            'company_fundamentals', 
            'peer_companies',
            'earnings_calendar',
            'investor_scores',
            'daily_charts',
            'sectors',
            'portfolio',
            'top_stocks'
        ]
        
        for table in dependent_tables:
            try:
                # Check if table exists
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if table_exists:
                    # Check if table has ticker column
                    cur.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = '{table}' AND column_name = 'ticker'
                        );
                    """)
                    has_ticker = cur.fetchone()[0]
                    
                    if has_ticker:
                        placeholders = ','.join(['%s'] * len(tickers_to_delete))
                        cur.execute(f"DELETE FROM {table} WHERE ticker IN ({placeholders})", list(tickers_to_delete))
                        deleted_count = cur.rowcount
                        if deleted_count > 0:
                            logging.info(f"Deleted {deleted_count} records from {table}")
                        
            except Exception as e:
                logging.warning(f"Could not clean table {table}: {e}")
                continue
        
        conn.commit()
        logging.info("Foreign key references removed successfully!")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error removing foreign key references: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def sync_stocks_with_csv():
    """Sync stocks table with the final CSV file"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        logging.info("🔄 Reading CSV file...")
        df = pd.read_csv(CSV_FILE)
        logging.info(f"📊 Loaded {len(df)} records from CSV")
        
        # Get current tickers in database
        cur.execute("SELECT ticker FROM stocks")
        current_tickers = {row[0] for row in cur.fetchall()}
        logging.info(f"📊 Found {len(current_tickers)} current tickers in database")
        
        # Get tickers from CSV
        csv_tickers = set(df['Ticker'].str.strip().str.upper())
        logging.info(f"📊 Found {len(csv_tickers)} tickers in CSV")
        
        # Find tickers to delete (in DB but not in CSV)
        tickers_to_delete = current_tickers - csv_tickers
        if tickers_to_delete:
            logging.info(f"🗑️ Deleting {len(tickers_to_delete)} tickers not in CSV: {sorted(tickers_to_delete)}")
            
            # First remove foreign key references
            remove_foreign_key_references(tickers_to_delete)
            
            # Now delete from stocks table
            placeholders = ','.join(['%s'] * len(tickers_to_delete))
            cur.execute(f"DELETE FROM stocks WHERE ticker IN ({placeholders})", list(tickers_to_delete))
            logging.info(f"✅ Deleted {len(tickers_to_delete)} tickers")
        
        # Process each row in CSV
        inserted_count = 0
        updated_count = 0
        
        for _, row in df.iterrows():
            # Skip rows with missing or invalid tickers
            if pd.isna(row['Ticker']) or not isinstance(row['Ticker'], str):
                continue
            ticker = row['Ticker'].strip().upper()
            if not ticker:  # Skip empty tickers
                continue
            
            # Prepare data
            data = {
                'ticker': ticker,
                'company_name': row['Company Name'].strip() if pd.notna(row['Company Name']) else None,
                'industry': row['Industry'].strip() if pd.notna(row['Industry']) else None,
                'sector': row['Sector'].strip() if pd.notna(row['Sector']) else None,
                'market_cap_b': float(row['Market Cap (B)']) if pd.notna(row['Market Cap (B)']) else None,
                'exchange': row['Exchange'].strip() if pd.notna(row['Exchange']) else None,
                'country': row['Country'].strip() if pd.notna(row['Country']) else None,
                'description': row['Description'].strip() if pd.notna(row['Description']) else None,
                'business_model': row['Business_Model'].strip() if pd.notna(row['Business_Model']) else None,
                'products_services': row['Products_Services'].strip() if pd.notna(row['Products_Services']) else None,
                'main_customers': row['Main_Customers'].strip() if pd.notna(row['Main_Customers']) else None,
                'markets': row['Markets'].strip() if pd.notna(row['Markets']) else None,
                'moat_1': row['Moat 1'].strip() if pd.notna(row['Moat 1']) else None,
                'moat_2': row['Moat 2'].strip() if pd.notna(row['Moat 2']) else None,
                'moat_3': row['Moat 3'].strip() if pd.notna(row['Moat 3']) else None,
                'moat_4': row['Moat 4'].strip() if pd.notna(row['Moat 4']) else None,
                'peer_a': row['Peer A'].strip() if pd.notna(row['Peer A']) else None,
                'peer_b': row['Peer B'].strip() if pd.notna(row['Peer B']) else None,
                'peer_c': row['Peer C'].strip() if pd.notna(row['Peer C']) else None,
                'last_updated': datetime.now()
            }
            
            # Check if ticker exists
            cur.execute("SELECT COUNT(*) FROM stocks WHERE ticker = %s", (ticker,))
            exists = cur.fetchone()[0] > 0
            
            if exists:
                # Update existing record
                cur.execute("""
                    UPDATE stocks SET
                        company_name = %(company_name)s,
                        industry = %(industry)s,
                        sector = %(sector)s,
                        market_cap_b = %(market_cap_b)s,
                        exchange = %(exchange)s,
                        country = %(country)s,
                        description = %(description)s,
                        business_model = %(business_model)s,
                        products_services = %(products_services)s,
                        main_customers = %(main_customers)s,
                        markets = %(markets)s,
                        moat_1 = %(moat_1)s,
                        moat_2 = %(moat_2)s,
                        moat_3 = %(moat_3)s,
                        moat_4 = %(moat_4)s,
                        peer_a = %(peer_a)s,
                        peer_b = %(peer_b)s,
                        peer_c = %(peer_c)s,
                        last_updated = %(last_updated)s
                    WHERE ticker = %(ticker)s
                """, data)
                updated_count += 1
            else:
                # Insert new record
                cur.execute("""
                    INSERT INTO stocks (
                        ticker, company_name, industry, sector, market_cap_b,
                        exchange, country, description, business_model,
                        products_services, main_customers, markets,
                        moat_1, moat_2, moat_3, moat_4,
                        peer_a, peer_b, peer_c, last_updated
                    ) VALUES (
                        %(ticker)s, %(company_name)s, %(industry)s, %(sector)s, %(market_cap_b)s,
                        %(exchange)s, %(country)s, %(description)s, %(business_model)s,
                        %(products_services)s, %(main_customers)s, %(markets)s,
                        %(moat_1)s, %(moat_2)s, %(moat_3)s, %(moat_4)s,
                        %(peer_a)s, %(peer_b)s, %(peer_c)s, %(last_updated)s
                    )
                """, data)
                inserted_count += 1
        
        conn.commit()
        logging.info(f"✅ Sync completed: {inserted_count} inserted, {updated_count} updated")
        
        return inserted_count, updated_count, len(tickers_to_delete)
        
    except Exception as e:
        conn.rollback()
        logging.error(f"❌ Error syncing stocks: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def run_qa_verification():
    """Run QA verification to ensure stocks table matches CSV"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        logging.info("🔍 Running QA verification...")
        
        # Read CSV again for comparison
        df = pd.read_csv(CSV_FILE)
        csv_tickers = set(df['Ticker'].str.strip().str.upper())
        
        # Get database tickers
        cur.execute("SELECT ticker FROM stocks")
        db_tickers = {row[0] for row in cur.fetchall()}
        
        # Check counts
        csv_count = len(csv_tickers)
        db_count = len(db_tickers)
        
        logging.info(f"📊 CSV ticker count: {csv_count}")
        logging.info(f"📊 Database ticker count: {db_count}")
        
        if csv_count == db_count:
            logging.info("✅ Ticker counts match!")
        else:
            logging.warning(f"⚠️ Ticker counts don't match! Difference: {abs(csv_count - db_count)}")
        
        # Check for missing tickers
        missing_in_db = csv_tickers - db_tickers
        extra_in_db = db_tickers - csv_tickers
        
        if missing_in_db:
            logging.error(f"❌ Missing in database: {sorted(missing_in_db)}")
        else:
            logging.info("✅ All CSV tickers present in database")
            
        if extra_in_db:
            logging.error(f"❌ Extra in database: {sorted(extra_in_db)}")
        else:
            logging.info("✅ No extra tickers in database")
        
        # Check data completeness
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN company_name IS NOT NULL THEN 1 END) as with_name,
                COUNT(CASE WHEN sector IS NOT NULL THEN 1 END) as with_sector,
                COUNT(CASE WHEN industry IS NOT NULL THEN 1 END) as with_industry,
                COUNT(CASE WHEN market_cap_b IS NOT NULL THEN 1 END) as with_market_cap,
                COUNT(CASE WHEN description IS NOT NULL THEN 1 END) as with_description
            FROM stocks
        """)
        
        stats = cur.fetchone()
        total, with_name, with_sector, with_industry, with_market_cap, with_description = stats
        
        logging.info(f"📊 Data completeness:")
        logging.info(f"  - Total records: {total}")
        logging.info(f"  - With company name: {with_name} ({with_name/total*100:.1f}%)")
        logging.info(f"  - With sector: {with_sector} ({with_sector/total*100:.1f}%)")
        logging.info(f"  - With industry: {with_industry} ({with_industry/total*100:.1f}%)")
        logging.info(f"  - With market cap: {with_market_cap} ({with_market_cap/total*100:.1f}%)")
        logging.info(f"  - With description: {with_description} ({with_description/total*100:.1f}%)")
        
        # Check sector distribution
        cur.execute("""
            SELECT sector, COUNT(*) as count
            FROM stocks
            WHERE sector IS NOT NULL
            GROUP BY sector
            ORDER BY count DESC
            LIMIT 10
        """)
        
        sectors = cur.fetchall()
        logging.info(f"📊 Top sectors:")
        for sector, count in sectors:
            logging.info(f"  - {sector}: {count}")
        
        # Sample verification
        cur.execute("""
            SELECT ticker, company_name, sector, industry, market_cap_b
            FROM stocks
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        samples = cur.fetchall()
        logging.info(f"📊 Sample records:")
        for ticker, name, sector, industry, market_cap in samples:
            logging.info(f"  - {ticker}: {name} ({sector}, {industry}, ${market_cap}B)")
        
        # Overall status
        if not missing_in_db and not extra_in_db and csv_count == db_count:
            logging.info("🎉 QA verification PASSED - stocks table perfectly matches CSV!")
            return True
        else:
            logging.error("❌ QA verification FAILED - discrepancies found!")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error in QA verification: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def main():
    """Main execution function"""
    logging.info("🚀 Starting stocks table update with final CSV list...")
    
    try:
        # Step 1: Update schema
        update_stocks_schema()
        
        # Step 2: Sync data
        inserted, updated, deleted = sync_stocks_with_csv()
        
        # Step 3: Run QA
        qa_passed = run_qa_verification()
        
        # Summary
        logging.info("📋 SUMMARY:")
        logging.info(f"  - Records inserted: {inserted}")
        logging.info(f"  - Records updated: {updated}")
        logging.info(f"  - Records deleted: {deleted}")
        logging.info(f"  - QA verification: {'PASSED' if qa_passed else 'FAILED'}")
        
        if qa_passed:
            logging.info("🎉 Stocks table successfully updated and verified!")
        else:
            logging.error("❌ Stocks table update completed but QA failed!")
            
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 