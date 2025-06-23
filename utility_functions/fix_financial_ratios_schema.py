import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def fix_schema():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        print("Dropping views industry_summary and latest_financial_ratios (CASCADE)...")
        cur.execute("DROP VIEW IF EXISTS industry_summary CASCADE;")
        cur.execute("DROP VIEW IF EXISTS latest_financial_ratios CASCADE;")
        print("Altering market_cap and enterprise_value columns in financial_ratios table...")
        cur.execute("ALTER TABLE financial_ratios ALTER COLUMN market_cap TYPE NUMERIC(20,2);")
        cur.execute("ALTER TABLE financial_ratios ALTER COLUMN enterprise_value TYPE NUMERIC(20,2);")
        print("Recreating view latest_financial_ratios...")
        cur.execute("""
            CREATE OR REPLACE VIEW latest_financial_ratios AS
            SELECT DISTINCT ON (ticker) 
                ticker, calculation_date, pe_ratio, pb_ratio, roe, debt_to_equity,
                gross_margin, operating_margin, net_margin, altman_z_score,
                revenue_growth_yoy, earnings_growth_yoy, market_cap
            FROM financial_ratios
            ORDER BY ticker, calculation_date DESC;
        """)
        print("Recreating view industry_summary...")
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
        conn.commit()
        print("✅ Schema updated successfully!")
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_schema() 