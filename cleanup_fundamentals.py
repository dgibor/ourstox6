import os
import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
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

def cleanup_duplicate_fundamentals():
    """Clean up duplicate fundamental records"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🧹 Cleaning up duplicate fundamental records...")
        
        # Find tickers with multiple records for the same period
        cur.execute("""
            SELECT ticker, fiscal_year, fiscal_quarter, period_type, COUNT(*) as count
            FROM company_fundamentals
            GROUP BY ticker, fiscal_year, fiscal_quarter, period_type
            HAVING COUNT(*) > 1
            ORDER BY ticker, fiscal_year DESC, fiscal_quarter DESC
        """)
        
        duplicates = cur.fetchall()
        
        if not duplicates:
            print("✅ No duplicate fundamental records found!")
            return
        
        print(f"📊 Found {len(duplicates)} duplicate groups:")
        
        for ticker, fiscal_year, fiscal_quarter, period_type, count in duplicates:
            print(f"  {ticker} {period_type} {fiscal_year} Q{fiscal_quarter}: {count} records")
            
            # Keep the most recent record for each duplicate group
            cur.execute("""
                DELETE FROM company_fundamentals 
                WHERE ticker = %s 
                AND fiscal_year = %s 
                AND fiscal_quarter = %s 
                AND period_type = %s
                AND id NOT IN (
                    SELECT MAX(id) 
                    FROM company_fundamentals 
                    WHERE ticker = %s 
                    AND fiscal_year = %s 
                    AND fiscal_quarter = %s 
                    AND period_type = %s
                )
            """, (ticker, fiscal_year, fiscal_quarter, period_type, 
                  ticker, fiscal_year, fiscal_quarter, period_type))
            
            deleted_count = cur.rowcount
            print(f"    Deleted {deleted_count} duplicate records")
        
        conn.commit()
        print(f"\n✅ Cleanup complete")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error cleaning up duplicates: {e}")
        import traceback
        traceback.print_exc()

def verify_data_consistency():
    """Verify data consistency between tables"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n🔍 Verifying data consistency...")
        
        # Check for tickers with revenue discrepancies
        cur.execute("""
            SELECT s.ticker, s.revenue_ttm, cf.revenue as fundamental_revenue,
                   cf.data_source, cf.fiscal_year
            FROM stocks s
            JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.revenue IS NOT NULL 
            AND s.revenue_ttm IS NOT NULL
            AND s.revenue_ttm != cf.revenue
            AND cf.fiscal_year = (
                SELECT MAX(fiscal_year) 
                FROM company_fundamentals cf2 
                WHERE cf2.ticker = s.ticker
            )
            ORDER BY s.ticker
        """)
        
        discrepancies = cur.fetchall()
        
        if not discrepancies:
            print("✅ No revenue discrepancies found!")
        else:
            print(f"⚠️  Found {len(discrepancies)} revenue discrepancies:")
            for ticker, stocks_revenue, fundamental_revenue, data_source, fiscal_year in discrepancies:
                diff = abs(stocks_revenue - fundamental_revenue)
                diff_pct = (diff / fundamental_revenue) * 100
                print(f"  {ticker}: Stocks=${stocks_revenue:,.0f}, Fundamentals=${fundamental_revenue:,.0f} ({diff_pct:.1f}% diff)")
        
        # Check for missing fundamental data
        cur.execute("""
            SELECT s.ticker, s.revenue_ttm, s.net_income_ttm
            FROM stocks s
            WHERE s.revenue_ttm IS NULL OR s.net_income_ttm IS NULL
            ORDER BY s.ticker
        """)
        
        missing_data = cur.fetchall()
        
        if not missing_data:
            print("✅ All stocks have fundamental data!")
        else:
            print(f"⚠️  Found {len(missing_data)} stocks with missing fundamental data:")
            for ticker, revenue, net_income in missing_data:
                missing = []
                if revenue is None:
                    missing.append("revenue")
                if net_income is None:
                    missing.append("net_income")
                print(f"  {ticker}: Missing {', '.join(missing)}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying consistency: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to clean up and verify data"""
    print("🧹 Data Cleanup and Verification Script")
    print("=" * 50)
    
    # Clean up duplicates
    cleanup_duplicate_fundamentals()
    
    # Verify consistency
    verify_data_consistency()
    
    print("\n" + "=" * 50)
    print("Cleanup and verification complete!")

if __name__ == "__main__":
    main() 