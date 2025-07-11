#!/usr/bin/env python3
"""
Check fundamental data for test tickers
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_fundamentals():
    """Check fundamental data for test tickers"""
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
        
        test_tickers = ['AAPL', 'AMZN', 'AVGO', 'NVDA', 'XOM']
        
        for ticker in test_tickers:
            print(f"\n📊 {ticker}:")
            
            # Check company_fundamentals
            cur.execute("""
                SELECT revenue, net_income, ebitda, data_source, last_updated
                FROM company_fundamentals 
                WHERE ticker = %s
                ORDER BY last_updated DESC
                LIMIT 3
            """, (ticker,))
            
            fundamentals = cur.fetchall()
            if fundamentals:
                print("  📋 Company fundamentals:")
                for i, record in enumerate(fundamentals, 1):
                    revenue, net_income, ebitda, source, updated = record
                    print(f"    Record {i}: ${revenue:,.0f} revenue, {source}, {updated}")
            else:
                print("  ❌ No fundamental data")
            
            # Check stocks table
            cur.execute("""
                SELECT revenue_ttm, net_income_ttm, ebitda_ttm, fundamentals_last_update
                FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            
            stock_data = cur.fetchone()
            if stock_data:
                revenue_ttm, net_income_ttm, ebitda_ttm, last_update = stock_data
                print("  📊 Stocks table:")
                print(f"    Revenue TTM: ${revenue_ttm:,.0f}" if revenue_ttm else "    Revenue TTM: None")
                print(f"    Net Income TTM: ${net_income_ttm:,.0f}" if net_income_ttm else "    Net Income TTM: None")
                print(f"    EBITDA TTM: ${ebitda_ttm:,.0f}" if ebitda_ttm else "    EBITDA TTM: None")
                print(f"    Last Updated: {last_update}")
            else:
                print("  ❌ Not in stocks table")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_fundamentals() 