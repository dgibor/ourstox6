#!/usr/bin/env python3
"""
Debug script to test Yahoo Finance revenue data fetching
"""

import os
import sys
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Load environment variables
load_dotenv()

def test_yahoo_revenue():
    """Test Yahoo Finance revenue fetching"""
    print("🔍 Testing Yahoo Finance revenue data...")
    
    # Import after path setup
    from daily_run.yahoo_finance_service import YahooFinanceService
    
    service = YahooFinanceService()
    
    try:
        # Test with AAPL
        print("📊 Fetching AAPL data...")
        result = service.get_fundamental_data('AAPL')
        
        if result:
            print("✅ Successfully fetched data")
            if result.get('financial_data'):
                income = result['financial_data'].get('income_statement', {})
                print(f"📋 Income Statement Data:")
                print(f"  Revenue: ${income.get('revenue', 0):,.0f}")
                print(f"  Revenue Annual: ${income.get('revenue_annual', 0):,.0f}")
                print(f"  TTM Periods: {income.get('ttm_periods', 0)}")
                print(f"  Net Income: ${income.get('net_income', 0):,.0f}")
                print(f"  EBITDA: ${income.get('ebitda', 0):,.0f}")
        else:
            print("❌ Failed to fetch data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        service.close()
    
    # Check what's in the database
    print("\n🔍 Checking database contents...")
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
        
        # Check stocks table
        cur.execute("""
            SELECT ticker, revenue_ttm, net_income_ttm, ebitda_ttm, 
                   fundamentals_last_update
            FROM stocks 
            WHERE ticker = 'AAPL'
        """)
        
        stock_data = cur.fetchone()
        if stock_data:
            print(f"📊 Stocks table for AAPL:")
            print(f"  Revenue TTM: ${stock_data[1]:,.0f}" if stock_data[1] else "  Revenue TTM: None")
            print(f"  Net Income TTM: ${stock_data[2]:,.0f}" if stock_data[2] else "  Net Income TTM: None")
            print(f"  EBITDA TTM: ${stock_data[3]:,.0f}" if stock_data[3] else "  EBITDA TTM: None")
            print(f"  Last Updated: {stock_data[4]}")
        
        # Check company_fundamentals table
        cur.execute("""
            SELECT ticker, data_source, revenue, net_income, ebitda, last_updated
            FROM company_fundamentals 
            WHERE ticker = 'AAPL'
            ORDER BY last_updated DESC
            LIMIT 3
        """)
        
        fundamentals = cur.fetchall()
        print(f"\n📋 Company fundamentals for AAPL:")
        for i, record in enumerate(fundamentals, 1):
            print(f"  Record {i}:")
            print(f"    Data Source: {record[1]}")
            print(f"    Revenue: ${record[2]:,.0f}" if record[2] else "    Revenue: None")
            print(f"    Net Income: ${record[3]:,.0f}" if record[3] else "    Net Income: None")
            print(f"    EBITDA: ${record[4]:,.0f}" if record[4] else "    EBITDA: None")
            print(f"    Last Updated: {record[5]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_yahoo_revenue() 