#!/usr/bin/env python3
"""
Debug the revenue issue to understand why we're getting $391B instead of correct TTM
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def debug_revenue_issue():
    """Debug the revenue issue"""
    print("🔍 Debugging AAPL revenue issue...")
    
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Check all company_fundamentals records for AAPL
        print("\n📋 All company_fundamentals records for AAPL:")
        cur.execute("""
            SELECT ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                   revenue, net_income, ebitda, data_source, last_updated
            FROM company_fundamentals 
            WHERE ticker = 'AAPL'
            ORDER BY last_updated DESC
        """)
        
        records = cur.fetchall()
        for i, record in enumerate(records, 1):
            ticker, report_date, period_type, fiscal_year, fiscal_quarter, revenue, net_income, ebitda, source, updated = record
            print(f"  Record {i}:")
            print(f"    Period: {period_type} {fiscal_year} Q{fiscal_quarter}")
            print(f"    Revenue: ${revenue:,.0f}")
            print(f"    Net Income: ${net_income:,.0f}")
            print(f"    EBITDA: ${ebitda:,.0f}")
            print(f"    Source: {source}")
            print(f"    Date: {updated}")
            print()
        
        # Check if we have quarterly data
        print("\n📊 Checking for quarterly data:")
        cur.execute("""
            SELECT DISTINCT period_type, fiscal_year, fiscal_quarter
            FROM company_fundamentals 
            WHERE ticker = 'AAPL'
            ORDER BY fiscal_year DESC, fiscal_quarter DESC
        """)
        
        periods = cur.fetchall()
        for period in periods:
            period_type, fiscal_year, fiscal_quarter = period
            print(f"  {period_type} {fiscal_year} Q{fiscal_quarter}")
        
        # Calculate what TTM should be from quarterly data
        print("\n🧮 Calculating TTM from quarterly data:")
        cur.execute("""
            SELECT fiscal_year, fiscal_quarter, revenue
            FROM company_fundamentals 
            WHERE ticker = 'AAPL' AND period_type = 'quarterly'
            ORDER BY fiscal_year DESC, fiscal_quarter DESC
            LIMIT 4
        """)
        
        quarters = cur.fetchall()
        if quarters:
            ttm_revenue = sum(q[2] for q in quarters if q[2])
            print(f"  Last 4 quarters revenue sum: ${ttm_revenue:,.0f}")
            print("  Quarters used:")
            for year, quarter, revenue in quarters:
                print(f"    {year} Q{quarter}: ${revenue:,.0f}")
        else:
            print("  No quarterly data found")
        
        # Check what's in stocks table
        print("\n📊 Stocks table current values:")
        cur.execute("""
            SELECT revenue_ttm, net_income_ttm, ebitda_ttm, fundamentals_last_update
            FROM stocks 
            WHERE ticker = 'AAPL'
        """)
        
        stock_data = cur.fetchone()
        if stock_data:
            revenue_ttm, net_income_ttm, ebitda_ttm, last_update = stock_data
            print(f"  Revenue TTM: ${revenue_ttm:,.0f}")
            print(f"  Net Income TTM: ${net_income_ttm:,.0f}")
            print(f"  EBITDA TTM: ${ebitda_ttm:,.0f}")
            print(f"  Last Updated: {last_update}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_revenue_issue() 