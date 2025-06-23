#!/usr/bin/env python3
"""
Fix revenue_ttm issue by updating stocks table with correct TTM data from company_fundamentals
"""

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

def fix_revenue_ttm():
    """Fix revenue TTM in stocks table using correct data from company_fundamentals"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔧 Fixing Revenue TTM in stocks table...")
        
        # Get all tickers with incorrect revenue data
        cur.execute("""
            SELECT s.ticker, s.revenue_ttm, cf.revenue as correct_revenue,
                   cf.data_source, cf.last_updated
            FROM stocks s
            JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.revenue IS NOT NULL 
            AND (s.revenue_ttm IS NULL OR s.revenue_ttm != cf.revenue)
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
            return
        
        print(f"📊 Found {len(discrepancies)} tickers with revenue discrepancies:")
        
        fixed_count = 0
        for ticker, current_revenue, correct_revenue, data_source, last_updated in discrepancies:
            if current_revenue:
                discrepancy = abs(current_revenue - correct_revenue)
                discrepancy_pct = (discrepancy / correct_revenue) * 100
                print(f"\n  {ticker}:")
                print(f"    Current: ${current_revenue:,.0f}")
                print(f"    Correct: ${correct_revenue:,.0f}")
                print(f"    Difference: ${discrepancy:,.0f} ({discrepancy_pct:.1f}%)")
                print(f"    Source: {data_source}")
            else:
                print(f"\n  {ticker}:")
                print(f"    Current: NULL")
                print(f"    Correct: ${correct_revenue:,.0f}")
                print(f"    Source: {data_source}")
            
            # Update the stocks table with correct revenue
            cur.execute("""
                UPDATE stocks 
                SET revenue_ttm = %s, fundamentals_last_update = CURRENT_TIMESTAMP
                WHERE ticker = %s
            """, (correct_revenue, ticker))
            
            fixed_count += 1
        
        conn.commit()
        print(f"\n✅ Fixed revenue TTM for {fixed_count} tickers")
        
        # Verify the fix
        print("\n🔍 Verifying the fix...")
        cur.execute("""
            SELECT s.ticker, s.revenue_ttm, cf.revenue as fundamental_revenue
            FROM stocks s
            JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.revenue IS NOT NULL 
            AND cf.fiscal_year = (
                SELECT MAX(fiscal_year) 
                FROM company_fundamentals cf2 
                WHERE cf2.ticker = s.ticker
            )
            ORDER BY s.ticker
            LIMIT 10
        """)
        
        verification = cur.fetchall()
        print(f"\n📊 Verification (first 10 tickers):")
        for ticker, stocks_revenue, fundamental_revenue in verification:
            if stocks_revenue == fundamental_revenue:
                print(f"  ✅ {ticker}: ${stocks_revenue:,.0f}")
            else:
                print(f"  ❌ {ticker}: Stocks=${stocks_revenue:,.0f}, Fundamentals=${fundamental_revenue:,.0f}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing revenue TTM: {e}")
        import traceback
        traceback.print_exc()

def calculate_ttm_from_quarterly():
    """Calculate TTM revenue from quarterly data for tickers that need it"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n🧮 Calculating TTM from quarterly data...")
        
        # Find tickers with quarterly data but no TTM
        cur.execute("""
            SELECT DISTINCT cf.ticker
            FROM company_fundamentals cf
            WHERE cf.period_type = 'quarterly'
            AND cf.revenue IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM stocks s 
                WHERE s.ticker = cf.ticker 
                AND s.revenue_ttm IS NOT NULL
            )
        """)
        
        tickers_needing_ttm = [row[0] for row in cur.fetchall()]
        
        if not tickers_needing_ttm:
            print("✅ No tickers need TTM calculation from quarterly data")
            return
        
        print(f"📊 Found {len(tickers_needing_ttm)} tickers needing TTM calculation")
        
        for ticker in tickers_needing_ttm:
            # Get last 4 quarters of revenue
            cur.execute("""
                SELECT revenue, fiscal_year, fiscal_quarter
                FROM company_fundamentals
                WHERE ticker = %s 
                AND period_type = 'quarterly'
                AND revenue IS NOT NULL
                ORDER BY fiscal_year DESC, fiscal_quarter DESC
                LIMIT 4
            """, (ticker,))
            
            quarters = cur.fetchall()
            
            if len(quarters) >= 4:
                ttm_revenue = sum(q[0] for q in quarters)
                print(f"\n  {ticker} TTM Revenue: ${ttm_revenue:,.0f}")
                print(f"    Quarters used:")
                for revenue, year, quarter in quarters:
                    print(f"      {year} Q{quarter}: ${revenue:,.0f}")
                
                # Update stocks table
                cur.execute("""
                    UPDATE stocks 
                    SET revenue_ttm = %s, fundamentals_last_update = CURRENT_TIMESTAMP
                    WHERE ticker = %s
                """, (ttm_revenue, ticker))
            else:
                print(f"\n  ⚠️  {ticker}: Only {len(quarters)} quarters available, need 4 for TTM")
        
        conn.commit()
        print(f"\n✅ TTM calculation complete")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error calculating TTM from quarterly data: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to fix revenue TTM issues"""
    print("🔧 Revenue TTM Fix Script")
    print("=" * 50)
    
    # Fix revenue discrepancies
    fix_revenue_ttm()
    
    # Calculate TTM from quarterly data where needed
    calculate_ttm_from_quarterly()
    
    print("\n" + "=" * 50)
    print("Revenue TTM fix complete!")

if __name__ == "__main__":
    main() 