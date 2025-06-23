#!/usr/bin/env python3
"""
Migration script to create new financial database schema
"""

import os
import psycopg2
import logging
from datetime import datetime
from dotenv import load_dotenv

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

def create_new_schema():
    """Create the new financial schema tables"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        logging.info("Creating new financial schema...")
        
        # 1. Create financials table
        logging.info("Creating financials table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS financials (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL UNIQUE,
                
                -- Market Data
                market_cap NUMERIC(15,2),
                shares_outstanding BIGINT,
                current_price NUMERIC(8,2),
                
                -- Income Statement (TTM)
                revenue_ttm NUMERIC(15,2),
                gross_profit_ttm NUMERIC(15,2),
                operating_income_ttm NUMERIC(15,2),
                net_income_ttm NUMERIC(15,2),
                ebitda_ttm NUMERIC(15,2),
                
                -- Per Share Metrics
                diluted_eps_ttm NUMERIC(8,4),
                book_value_per_share NUMERIC(8,4),
                
                -- Balance Sheet
                total_assets NUMERIC(15,2),
                total_debt NUMERIC(15,2),
                shareholders_equity NUMERIC(15,2),
                cash_and_equivalents NUMERIC(15,2),
                current_assets NUMERIC(15,2),
                current_liabilities NUMERIC(15,2),
                
                -- Cash Flow
                operating_cash_flow_ttm NUMERIC(15,2),
                free_cash_flow_ttm NUMERIC(15,2),
                capex_ttm NUMERIC(15,2),
                
                -- Earnings Calendar
                next_earnings_date DATE,
                earnings_time VARCHAR(10),
                eps_estimate NUMERIC(8,4),
                revenue_estimate NUMERIC(15,2),
                
                -- Data Source & Timestamps
                data_source VARCHAR(20),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_update_priority INTEGER DEFAULT 1,
                
                FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
            );
        """)
        
        # 2. Create current_ratios table
        logging.info("Creating current_ratios table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS current_ratios (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL UNIQUE,
                
                -- Valuation Ratios
                pe_ratio NUMERIC(8,4),
                pb_ratio NUMERIC(8,4),
                ps_ratio NUMERIC(8,4),
                ev_ebitda NUMERIC(8,4),
                
                -- Profitability Ratios
                roe NUMERIC(8,4),
                roa NUMERIC(8,4),
                roic NUMERIC(8,4),
                gross_margin NUMERIC(8,4),
                operating_margin NUMERIC(8,4),
                net_margin NUMERIC(8,4),
                
                -- Financial Health
                debt_to_equity NUMERIC(8,4),
                current_ratio NUMERIC(8,4),
                quick_ratio NUMERIC(8,4),
                interest_coverage NUMERIC(8,4),
                
                -- Efficiency Ratios
                asset_turnover NUMERIC(8,4),
                inventory_turnover NUMERIC(8,4),
                receivables_turnover NUMERIC(8,4),
                
                -- Growth Metrics (YoY)
                revenue_growth_yoy NUMERIC(8,4),
                earnings_growth_yoy NUMERIC(8,4),
                fcf_growth_yoy NUMERIC(8,4),
                
                -- Quality Metrics
                fcf_to_net_income NUMERIC(8,4),
                
                -- Market Data
                enterprise_value NUMERIC(15,2),
                
                -- Value Investing Metrics
                graham_number NUMERIC(8,4),
                altman_z_score NUMERIC(8,4),
                
                -- Calculation Metadata
                calculation_date DATE NOT NULL,
                price_used NUMERIC(8,2),
                data_quality_score INTEGER,
                calculation_notes TEXT[],
                
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
            );
        """)
        
        # 3. Create update_log table
        logging.info("Creating update_log table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS update_log (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10),
                update_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                records_updated INTEGER DEFAULT 0,
                execution_time_ms INTEGER,
                error_message TEXT,
                data_source VARCHAR(20),
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                
                FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
            );
        """)
        
        # 4. Create indexes for performance
        logging.info("Creating indexes...")
        
        # Indexes for financials
        cur.execute("CREATE INDEX IF NOT EXISTS idx_financials_ticker ON financials(ticker);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_financials_next_earnings ON financials(next_earnings_date) WHERE next_earnings_date IS NOT NULL;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_financials_update_priority ON financials(next_update_priority DESC, last_updated ASC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_financials_market_cap ON financials(market_cap DESC) WHERE market_cap IS NOT NULL;")
        
        # Indexes for current_ratios
        cur.execute("CREATE INDEX IF NOT EXISTS idx_current_ratios_ticker ON current_ratios(ticker);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_current_ratios_calculation_date ON current_ratios(calculation_date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_current_ratios_pe ON current_ratios(pe_ratio) WHERE pe_ratio IS NOT NULL;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_current_ratios_pb ON current_ratios(pb_ratio) WHERE pb_ratio IS NOT NULL;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_current_ratios_ps ON current_ratios(ps_ratio) WHERE ps_ratio IS NOT NULL;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_current_ratios_roe ON current_ratios(roe) WHERE roe IS NOT NULL;")
        
        # Indexes for update_log
        cur.execute("CREATE INDEX IF NOT EXISTS idx_update_log_ticker_date ON update_log(ticker, started_at DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_update_log_type_date ON update_log(update_type, started_at DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_update_log_status ON update_log(status, started_at DESC);")
        
        conn.commit()
        logging.info("✅ New schema created successfully!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error creating schema: {e}")
        return False

def migrate_existing_data():
    """Migrate existing data from old tables to new schema"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        logging.info("Migrating existing data...")
        
        # 1. Migrate fundamental data from stocks table to financials
        logging.info("Migrating fundamental data from stocks table...")
        cur.execute("""
            INSERT INTO financials (
                ticker, market_cap, shares_outstanding, revenue_ttm, net_income_ttm, 
                ebitda_ttm, total_debt, shareholders_equity, cash_and_equivalents,
                diluted_eps_ttm, book_value_per_share, total_assets, current_assets,
                current_liabilities, operating_income_ttm, data_source, last_updated
            )
            SELECT 
                ticker, market_cap, shares_outstanding, revenue_ttm, net_income_ttm,
                ebitda_ttm, total_debt, shareholders_equity, cash_and_equivalents,
                diluted_eps_ttm, book_value_per_share, total_assets, current_assets,
                current_liabilities, operating_income, 'migration', fundamentals_last_update
            FROM stocks 
            WHERE market_cap IS NOT NULL OR revenue_ttm IS NOT NULL
            ON CONFLICT (ticker) DO UPDATE SET
                market_cap = EXCLUDED.market_cap,
                shares_outstanding = EXCLUDED.shares_outstanding,
                revenue_ttm = EXCLUDED.revenue_ttm,
                net_income_ttm = EXCLUDED.net_income_ttm,
                ebitda_ttm = EXCLUDED.ebitda_ttm,
                total_debt = EXCLUDED.total_debt,
                shareholders_equity = EXCLUDED.shareholders_equity,
                cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                diluted_eps_ttm = EXCLUDED.diluted_eps_ttm,
                book_value_per_share = EXCLUDED.book_value_per_share,
                total_assets = EXCLUDED.total_assets,
                current_assets = EXCLUDED.current_assets,
                current_liabilities = EXCLUDED.current_liabilities,
                operating_income_ttm = EXCLUDED.operating_income_ttm,
                last_updated = EXCLUDED.last_updated;
        """)
        
        # 2. Migrate latest ratios from financial_ratios table
        logging.info("Migrating latest ratios from financial_ratios table...")
        cur.execute("""
            INSERT INTO current_ratios (
                ticker, pe_ratio, pb_ratio, ps_ratio, ev_ebitda, graham_number,
                enterprise_value, calculation_date, price_used, data_quality_score
            )
            SELECT DISTINCT ON (fr.ticker)
                fr.ticker, fr.pe_ratio, fr.pb_ratio, fr.ps_ratio, fr.ev_ebitda, 
                fr.graham_number, fr.enterprise_value, fr.calculation_date,
                NULL as price_used, 80 as data_quality_score
            FROM financial_ratios fr
            ORDER BY fr.ticker, fr.calculation_date DESC
            ON CONFLICT (ticker) DO UPDATE SET
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                ps_ratio = EXCLUDED.ps_ratio,
                ev_ebitda = EXCLUDED.ev_ebitda,
                graham_number = EXCLUDED.graham_number,
                enterprise_value = EXCLUDED.enterprise_value,
                calculation_date = EXCLUDED.calculation_date,
                last_updated = CURRENT_TIMESTAMP;
        """)
        
        # 3. Get migration statistics
        cur.execute("SELECT COUNT(*) FROM financials;")
        financials_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM current_ratios;")
        ratios_count = cur.fetchone()[0]
        
        conn.commit()
        logging.info(f"✅ Migration completed!")
        logging.info(f"   Financials migrated: {financials_count}")
        logging.info(f"   Ratios migrated: {ratios_count}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error migrating data: {e}")
        return False

def main():
    """Main migration function"""
    logging.info("🚀 Starting database migration to new financial schema...")
    
    # Step 1: Create new schema
    if not create_new_schema():
        logging.error("Failed to create new schema. Exiting.")
        return
    
    # Step 2: Migrate existing data
    if not migrate_existing_data():
        logging.error("Failed to migrate existing data. Exiting.")
        return
    
    logging.info("🎉 Migration completed successfully!")
    logging.info("📝 Next steps:")
    logging.info("   1. Update application code to use new tables")
    logging.info("   2. Test the new schema thoroughly")
    logging.info("   3. Drop old tables after validation")

if __name__ == "__main__":
    main() 