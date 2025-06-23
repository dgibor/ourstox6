#!/usr/bin/env python3
"""
Fix revenue_ttm issue by updating stocks table with correct TTM data from company_fundamentals
"""

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_revenue_ttm():
    """Fix revenue_ttm by updating stocks table with correct TTM data"""
    print("🔧 Fixing revenue_ttm issue...")
    
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
        
        # Get the latest fundamental data for each ticker
        cur.execute("""
            SELECT DISTINCT ON (ticker) 
                ticker, revenue, net_income, ebitda, data_source, last_updated
            FROM company_fundamentals 
            WHERE revenue IS NOT NULL 
            ORDER BY ticker, last_updated DESC
        """)
        
        fundamentals = cur.fetchall()
        print(f"📋 Found {len(fundamentals)} tickers with fundamental data")
        
        updated_count = 0
        for record in fundamentals:
            ticker, revenue, net_income, ebitda, data_source, last_updated = record
            
            print(f"\n📊 Processing {ticker}:")
            print(f"  Revenue: ${revenue:,.0f}")
            print(f"  Net Income: ${net_income:,.0f}")
            print(f"  EBITDA: ${ebitda:,.0f}")
            print(f"  Source: {data_source}")
            print(f"  Date: {last_updated}")
            
            # Update stocks table with TTM data
            cur.execute("""
                UPDATE stocks 
                SET revenue_ttm = %s,
                    net_income_ttm = %s,
                    ebitda_ttm = %s,
                    fundamentals_last_update = CURRENT_TIMESTAMP
                WHERE ticker = %s
            """, (revenue, net_income, ebitda, ticker))
            
            if cur.rowcount > 0:
                updated_count += 1
                print(f"  ✅ Updated stocks table")
            else:
                print(f"  ⚠️  No matching record in stocks table")
        
        conn.commit()
        print(f"\n✅ Successfully updated {updated_count} tickers")
        
        # Verify the fix for our test tickers
        test_tickers = ['AAPL', 'AMZN', 'AVGO', 'NVDA', 'XOM']
        print(f"\n🔍 Verifying fix for test tickers...")
        
        for ticker in test_tickers:
            cur.execute("""
                SELECT ticker, revenue_ttm, net_income_ttm, ebitda_ttm, 
                       fundamentals_last_update
                FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            
            stock_data = cur.fetchone()
            if stock_data:
                print(f"📊 {ticker}:")
                print(f"  Revenue TTM: ${stock_data[1]:,.0f}" if stock_data[1] else "  Revenue TTM: None")
                print(f"  Net Income TTM: ${stock_data[2]:,.0f}" if stock_data[2] else "  Net Income TTM: None")
                print(f"  EBITDA TTM: ${stock_data[3]:,.0f}" if stock_data[3] else "  EBITDA TTM: None")
                print(f"  Last Updated: {stock_data[4]}")
            else:
                print(f"❌ {ticker}: Not found in stocks table")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_revenue_ttm() 