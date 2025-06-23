import os
import psycopg2
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

def create_fundamental_schema():
    """Create fundamental value investing schema extensions"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Creating fundamental value investing schema...")
        
        # 1. Add fundamental columns to stocks table
        print("Adding fundamental columns to stocks table...")
        cur.execute("""
            ALTER TABLE stocks 
            ADD COLUMN IF NOT EXISTS market_cap numeric,
            ADD COLUMN IF NOT EXISTS revenue_ttm numeric,
            ADD COLUMN IF NOT EXISTS net_income_ttm numeric,
            ADD COLUMN IF NOT EXISTS total_assets numeric,
            ADD COLUMN IF NOT EXISTS total_debt numeric,
            ADD COLUMN IF NOT EXISTS shareholders_equity numeric,
            ADD COLUMN IF NOT EXISTS current_assets numeric,
            ADD COLUMN IF NOT EXISTS current_liabilities numeric,
            ADD COLUMN IF NOT EXISTS operating_income numeric,
            ADD COLUMN IF NOT EXISTS cash_and_equivalents numeric,
            ADD COLUMN IF NOT EXISTS free_cash_flow numeric,
            ADD COLUMN IF NOT EXISTS shares_outstanding bigint,
            ADD COLUMN IF NOT EXISTS diluted_eps_ttm numeric,
            ADD COLUMN IF NOT EXISTS book_value_per_share numeric,
            ADD COLUMN IF NOT EXISTS ebitda_ttm numeric,
            ADD COLUMN IF NOT EXISTS enterprise_value numeric,
            ADD COLUMN IF NOT EXISTS peer_1_ticker VARCHAR(10),
            ADD COLUMN IF NOT EXISTS peer_2_ticker VARCHAR(10), 
            ADD COLUMN IF NOT EXISTS peer_3_ticker VARCHAR(10),
            ADD COLUMN IF NOT EXISTS sector_etf_ticker VARCHAR(10),
            ADD COLUMN IF NOT EXISTS peers_last_updated TIMESTAMP,
            ADD COLUMN IF NOT EXISTS industry_classification VARCHAR(100),
            ADD COLUMN IF NOT EXISTS gics_sector VARCHAR(50),
            ADD COLUMN IF NOT EXISTS gics_industry VARCHAR(100),
            ADD COLUMN IF NOT EXISTS market_cap_category VARCHAR(20),
            ADD COLUMN IF NOT EXISTS fundamentals_last_update TIMESTAMP,
            ADD COLUMN IF NOT EXISTS next_earnings_date DATE,
            ADD COLUMN IF NOT EXISTS data_priority INTEGER DEFAULT 1;
        """)
        
        # 2. Create company_fundamentals table
        print("Creating company_fundamentals table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS company_fundamentals (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                report_date DATE NOT NULL,
                period_type VARCHAR(10) NOT NULL,
                fiscal_year INTEGER,
                fiscal_quarter INTEGER,
                revenue NUMERIC(15,2),
                gross_profit NUMERIC(15,2),
                operating_income NUMERIC(15,2),
                net_income NUMERIC(15,2),
                ebitda NUMERIC(15,2),
                eps_diluted NUMERIC(8,4),
                book_value_per_share NUMERIC(8,4),
                total_assets NUMERIC(15,2),
                total_debt NUMERIC(15,2),
                total_equity NUMERIC(15,2),
                cash_and_equivalents NUMERIC(15,2),
                operating_cash_flow NUMERIC(15,2),
                free_cash_flow NUMERIC(15,2),
                capex NUMERIC(15,2),
                shares_outstanding BIGINT,
                shares_float BIGINT,
                data_source VARCHAR(20) NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, report_date, period_type),
                FOREIGN KEY (ticker) REFERENCES stocks(ticker)
            );
        """)
        
        # 3. Create financial_ratios table
        print("Creating financial_ratios table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS financial_ratios (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                calculation_date DATE NOT NULL,
                pe_ratio NUMERIC(8,4),
                pb_ratio NUMERIC(8,4),
                ps_ratio NUMERIC(8,4),
                ev_ebitda NUMERIC(8,4),
                peg_ratio NUMERIC(8,4),
                roe NUMERIC(8,4),
                roa NUMERIC(8,4),
                roic NUMERIC(8,4),
                gross_margin NUMERIC(8,4),
                operating_margin NUMERIC(8,4),
                net_margin NUMERIC(8,4),
                debt_to_equity NUMERIC(8,4),
                current_ratio NUMERIC(8,4),
                quick_ratio NUMERIC(8,4),
                interest_coverage NUMERIC(8,4),
                altman_z_score NUMERIC(8,4),
                asset_turnover NUMERIC(8,4),
                inventory_turnover NUMERIC(8,4),
                receivables_turnover NUMERIC(8,4),
                revenue_growth_yoy NUMERIC(8,4),
                earnings_growth_yoy NUMERIC(8,4),
                fcf_growth_yoy NUMERIC(8,4),
                fcf_to_net_income NUMERIC(8,4),
                cash_conversion_cycle INTEGER,
                market_cap NUMERIC(15,2),
                enterprise_value NUMERIC(15,2),
                graham_number NUMERIC(8,4),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, calculation_date),
                FOREIGN KEY (ticker) REFERENCES stocks(ticker)
            );
        """)
        
        # 4. Create industry_benchmarks table
        print("Creating industry_benchmarks table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS industry_benchmarks (
                id SERIAL PRIMARY KEY,
                industry_code VARCHAR(50) NOT NULL,
                sector_code VARCHAR(50) NOT NULL,
                calculation_date DATE NOT NULL,
                company_count INTEGER NOT NULL,
                avg_pe_ratio NUMERIC(8,4),
                median_pe_ratio NUMERIC(8,4),
                avg_pb_ratio NUMERIC(8,4),
                avg_roe NUMERIC(8,4),
                avg_debt_to_equity NUMERIC(8,4),
                avg_gross_margin NUMERIC(8,4),
                avg_operating_margin NUMERIC(8,4),
                pe_ratio_25p NUMERIC(8,4),
                pe_ratio_75p NUMERIC(8,4),
                pe_ratio_90p NUMERIC(8,4),
                roe_25p NUMERIC(8,4),
                roe_75p NUMERIC(8,4),
                roe_90p NUMERIC(8,4),
                debt_eq_25p NUMERIC(8,4),
                debt_eq_75p NUMERIC(8,4),
                debt_eq_90p NUMERIC(8,4),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(industry_code, calculation_date)
            );
        """)
        
        # 5. Create peer_companies table
        print("Creating peer_companies table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS peer_companies (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                peer_ticker VARCHAR(10) NOT NULL,
                similarity_score NUMERIC(4,3),
                criteria_matched TEXT[],
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker) REFERENCES stocks(ticker),
                FOREIGN KEY (peer_ticker) REFERENCES stocks(ticker)
            );
        """)
        
        # 6. Create earnings_calendar table
        print("Creating earnings_calendar table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS earnings_calendar (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                earnings_date DATE NOT NULL,
                confirmed BOOLEAN DEFAULT FALSE,
                time_of_day VARCHAR(10),
                eps_estimate NUMERIC(8,4),
                revenue_estimate NUMERIC(15,2),
                priority_level INTEGER DEFAULT 1,
                data_updated BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker) REFERENCES stocks(ticker)
            );
        """)
        
        # 7. Create api_usage_tracking table
        print("Creating api_usage_tracking table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_usage_tracking (
                id SERIAL PRIMARY KEY,
                api_provider VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                endpoint VARCHAR(100) NOT NULL,
                calls_made INTEGER DEFAULT 0,
                calls_limit INTEGER NOT NULL,
                reset_time TIMESTAMP,
                UNIQUE(api_provider, date, endpoint)
            );
        """)
        
        # 8. Create investor_scores table
        print("Creating investor_scores table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS investor_scores (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                calculation_date DATE NOT NULL,
                conservative_score INTEGER,
                garp_score INTEGER,
                deep_value_score INTEGER,
                valuation_score INTEGER,
                quality_score INTEGER,
                financial_health_score INTEGER,
                profitability_score INTEGER,
                growth_score INTEGER,
                management_score INTEGER,
                risk_level VARCHAR(20),
                risk_factors TEXT[],
                score_explanation JSONB,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, calculation_date),
                FOREIGN KEY (ticker) REFERENCES stocks(ticker)
            );
        """)
        
        # 9. Create csv_configurations table
        print("Creating csv_configurations table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS csv_configurations (
                id SERIAL PRIMARY KEY,
                file_name VARCHAR(100) NOT NULL,
                version INTEGER NOT NULL,
                content JSONB NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(file_name, version)
            );
        """)
        
        # 10. Create data_update_log table
        print("Creating data_update_log table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data_update_log (
                id SERIAL PRIMARY KEY,
                update_type VARCHAR(50) NOT NULL,
                ticker VARCHAR(10),
                status VARCHAR(20) NOT NULL,
                error_message TEXT,
                records_processed INTEGER,
                execution_time_ms INTEGER,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP
            );
        """)
        
        # 11. Create market_context table
        print("Creating market_context table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS market_context (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL UNIQUE,
                vix_level NUMERIC(6,2),
                spy_trend VARCHAR(20),
                interest_rate_10y NUMERIC(6,4),
                yield_curve_spread NUMERIC(6,4),
                bull_market_modifier NUMERIC(4,3) DEFAULT 1.0,
                bear_market_modifier NUMERIC(4,3) DEFAULT 1.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for performance
        print("Creating indexes...")
        
        # Indexes for company_fundamentals
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker_date ON company_fundamentals(ticker, report_date DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_period ON company_fundamentals(period_type, fiscal_year, fiscal_quarter);")
        
        # Indexes for financial_ratios
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ratios_ticker_date ON financial_ratios(ticker, calculation_date DESC);")
        
        # Indexes for industry_benchmarks
        cur.execute("CREATE INDEX IF NOT EXISTS idx_benchmarks_industry_date ON industry_benchmarks(industry_code, calculation_date DESC);")
        
        # Indexes for peer_companies
        cur.execute("CREATE INDEX IF NOT EXISTS idx_peer_ticker ON peer_companies(ticker);")
        
        # Indexes for earnings_calendar
        cur.execute("CREATE INDEX IF NOT EXISTS idx_earnings_date ON earnings_calendar(earnings_date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_earnings_priority ON earnings_calendar(priority_level DESC, earnings_date);")
        
        # Indexes for investor_scores
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scores_ticker_date ON investor_scores(ticker, calculation_date DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scores_latest ON investor_scores(ticker, calculation_date DESC);")
        
        # Indexes for stocks table
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stocks_priority ON stocks(data_priority DESC, fundamentals_last_update ASC NULLS FIRST);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stocks_earnings ON stocks(next_earnings_date) WHERE next_earnings_date IS NOT NULL;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stocks_peer_lookup ON stocks(industry, market_cap DESC) WHERE market_cap > 100000000;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stocks_priority_selection ON stocks(data_priority DESC, fundamentals_last_update ASC NULLS FIRST, market_cap DESC) WHERE market_cap > 100000000;")
        
        # Create helper views
        print("Creating helper views...")
        
        # Latest ratios per company
        cur.execute("""
            CREATE OR REPLACE VIEW latest_financial_ratios AS
            SELECT DISTINCT ON (ticker) 
                ticker, calculation_date, pe_ratio, pb_ratio, roe, debt_to_equity,
                gross_margin, operating_margin, net_margin, altman_z_score,
                revenue_growth_yoy, earnings_growth_yoy, market_cap
            FROM financial_ratios
            ORDER BY ticker, calculation_date DESC;
        """)
        
        # Companies needing fundamental updates
        cur.execute("""
            CREATE OR REPLACE VIEW companies_needing_updates AS
            SELECT 
                s.ticker, 
                s.company_name,
                s.data_priority,
                s.fundamentals_last_update,
                s.next_earnings_date,
                CASE 
                    WHEN s.next_earnings_date <= CURRENT_DATE + INTERVAL '7 days' THEN 5
                    WHEN s.fundamentals_last_update IS NULL THEN 4
                    WHEN s.fundamentals_last_update < CURRENT_DATE - INTERVAL '30 days' THEN 3
                    WHEN s.fundamentals_last_update < CURRENT_DATE - INTERVAL '90 days' THEN 2
                    ELSE 1
                END as calculated_priority
            FROM stocks s
            ORDER BY calculated_priority DESC, s.data_priority DESC, s.fundamentals_last_update ASC NULLS FIRST;
        """)
        
        # Industry summary for benchmarking
        cur.execute("""
            CREATE OR REPLACE VIEW industry_summary AS
            SELECT 
                s.industry,
                COUNT(*) as company_count,
                AVG(fr.pe_ratio) as avg_pe,
                AVG(fr.roe) as avg_roe,
                AVG(fr.debt_to_equity) as avg_debt_eq,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fr.pe_ratio) as median_pe,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fr.roe) as median_roe
            FROM stocks s
            JOIN latest_financial_ratios fr ON s.ticker = fr.ticker
            WHERE s.industry IS NOT NULL
            GROUP BY s.industry
            HAVING COUNT(*) >= 3;
        """)
        
        # Create materialized view for latest company metrics
        cur.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_latest_company_metrics AS
            SELECT DISTINCT ON (fr.ticker)
                fr.ticker,
                fr.calculation_date,
                fr.pe_ratio,
                fr.pb_ratio,
                fr.roe,
                fr.debt_to_equity,
                fr.altman_z_score,
                s.company_name,
                s.sector,
                s.industry,
                s.market_cap,
                s.peer_1_ticker,
                s.peer_2_ticker,
                s.peer_3_ticker
            FROM financial_ratios fr
            JOIN stocks s ON fr.ticker = s.ticker
            ORDER BY fr.ticker, fr.calculation_date DESC;
        """)
        
        # Create indexes on materialized view
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mv_latest_company_metrics_ticker ON mv_latest_company_metrics(ticker);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mv_latest_company_metrics_sector ON mv_latest_company_metrics(sector, industry);")
        
        conn.commit()
        print("Fundamental schema created successfully!")
        
        # Test the schema
        print("Testing schema...")
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%fundamental%' OR table_name LIKE '%ratio%' OR table_name LIKE '%benchmark%' OR table_name LIKE '%peer%' OR table_name LIKE '%earnings%' OR table_name LIKE '%api%' OR table_name LIKE '%investor%' OR table_name LIKE '%csv%' OR table_name LIKE '%data_update%' OR table_name LIKE '%market_context%';")
        table_count = cur.fetchone()[0]
        print(f"Created {table_count} fundamental analysis tables")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating fundamental schema: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    create_fundamental_schema() 