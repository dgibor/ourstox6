#!/usr/bin/env python3
"""
Debug the revenue issue to understand why we're getting $391B instead of correct TTM
"""

import os
import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

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

def debug_revenue_data(ticker='AAPL'):
    """Debug revenue data in both tables"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"\n=== Revenue Debug for {ticker} ===")
        
        # Check stocks table
        cur.execute("""
            SELECT ticker, revenue_ttm, net_income_ttm, market_cap, 
                   fundamentals_last_update
            FROM stocks 
            WHERE ticker = %s
        """, (ticker,))
        stocks_data = cur.fetchone()
        
        if stocks_data:
            print(f"\n📊 Stocks Table Data:")
            print(f"  Revenue TTM: ${stocks_data[1]:,.0f}" if stocks_data[1] else "  Revenue TTM: NULL")
            print(f"  Net Income TTM: ${stocks_data[2]:,.0f}" if stocks_data[2] else "  Net Income TTM: NULL")
            print(f"  Market Cap: ${stocks_data[3]:,.0f}" if stocks_data[3] else "  Market Cap: NULL")
            print(f"  Last Update: {stocks_data[4]}")
        else:
            print(f"❌ No data found in stocks table for {ticker}")
        
        # Check company_fundamentals table
        cur.execute("""
            SELECT ticker, revenue, net_income, fiscal_year, fiscal_quarter, 
                   period_type, data_source, last_updated
            FROM company_fundamentals 
            WHERE ticker = %s
            ORDER BY fiscal_year DESC, fiscal_quarter DESC
            LIMIT 5
        """, (ticker,))
        fundamentals_data = cur.fetchall()
        
        if fundamentals_data:
            print(f"\n📈 Company Fundamentals Table Data:")
            for row in fundamentals_data:
                print(f"  Revenue: ${row[1]:,.0f}" if row[1] else "  Revenue: NULL")
                print(f"  Net Income: ${row[2]:,.0f}" if row[2] else "  Net Income: NULL")
                print(f"  Fiscal Year: {row[3]}, Quarter: {row[4]}, Period: {row[5]}")
                print(f"  Data Source: {row[6]}, Last Updated: {row[7]}")
                print()
        else:
            print(f"❌ No data found in company_fundamentals table for {ticker}")
        
        # Check if there's a discrepancy
        if stocks_data and fundamentals_data:
            stocks_revenue = stocks_data[1]
            latest_fundamental_revenue = fundamentals_data[0][1]
            
            if stocks_revenue and latest_fundamental_revenue:
                discrepancy = abs(stocks_revenue - latest_fundamental_revenue)
                discrepancy_pct = (discrepancy / latest_fundamental_revenue) * 100
                print(f"\n🔍 Revenue Discrepancy Analysis:")
                print(f"  Stocks Table Revenue: ${stocks_revenue:,.0f}")
                print(f"  Latest Fundamental Revenue: ${latest_fundamental_revenue:,.0f}")
                print(f"  Absolute Difference: ${discrepancy:,.0f}")
                print(f"  Percentage Difference: {discrepancy_pct:.2f}%")
                
                if discrepancy_pct > 1:  # More than 1% difference
                    print(f"  ⚠️  Significant discrepancy detected!")
                else:
                    print(f"  ✅ Revenue data is consistent")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error debugging revenue data: {e}")

def test_yahoo_revenue_fetch(ticker='AAPL'):
    """Test Yahoo Finance revenue fetching specifically"""
    try:
        print(f"\n=== Testing Yahoo Finance Revenue Fetch for {ticker} ===")
        
        from daily_run.yahoo_finance_service import YahooFinanceService
        yahoo_service = YahooFinanceService()
        
        # Test the financial statements fetch
        financial_data = yahoo_service.fetch_financial_statements(ticker)
        
        if financial_data and financial_data.get('income_statement'):
            income = financial_data['income_statement']
            print(f"\n📊 Yahoo Finance Income Statement Data:")
            print(f"  Revenue: ${income.get('revenue', 0):,.0f}")
            print(f"  Revenue Annual: ${income.get('revenue_annual', 0):,.0f}")
            print(f"  Net Income: ${income.get('net_income', 0):,.0f}")
            print(f"  TTM Periods: {income.get('ttm_periods', 0)}")
            print(f"  Fiscal Year: {income.get('fiscal_year', 'N/A')}")
        else:
            print(f"❌ No income statement data returned from Yahoo Finance")
        
        yahoo_service.close()
        
    except Exception as e:
        print(f"❌ Error testing Yahoo Finance: {e}")

def main():
    """Main debug function"""
    ticker = 'AAPL'
    
    print("🔍 Revenue Data Debug Script")
    print("=" * 50)
    
    # Debug current database state
    debug_revenue_data(ticker)
    
    # Test Yahoo Finance fetching
    test_yahoo_revenue_fetch(ticker)
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    main() 