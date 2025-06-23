#!/usr/bin/env python3
"""
Check AAPL's actual revenue from multiple sources
"""

import yfinance as yf
import requests
import json

def check_aapl_revenue():
    """Check AAPL's actual revenue from multiple sources"""
    print("🔍 Checking AAPL's actual revenue...")
    
    try:
        # Method 1: yfinance
        print("\n📊 Method 1: yfinance")
        stock = yf.Ticker('AAPL')
        info = stock.info
        
        print(f"Total Revenue: ${info.get('totalRevenue', 0):,.0f}")
        print(f"Revenue Per Share: ${info.get('revenuePerShare', 0):,.2f}")
        print(f"Market Cap: ${info.get('marketCap', 0):,.0f}")
        print(f"P/S Ratio: {info.get('priceToSalesTrailing12Months', 0)}")
        
        # Calculate revenue from P/S ratio and market cap
        if info.get('priceToSalesTrailing12Months') and info.get('marketCap'):
            ps_ratio = info.get('priceToSalesTrailing12Months')
            market_cap = info.get('marketCap')
            calculated_revenue = market_cap / ps_ratio
            print(f"Calculated Revenue (Market Cap / P/S): ${calculated_revenue:,.0f}")
        
    except Exception as e:
        print(f"❌ yfinance error: {e}")
    
    try:
        # Method 2: Alpha Vantage (if API key available)
        print("\n📊 Method 2: Alpha Vantage")
        api_key = "demo"  # Use demo key for testing
        
        url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=AAPL&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if 'annualReports' in data and data['annualReports']:
            latest = data['annualReports'][0]
            print(f"Total Revenue: ${float(latest.get('totalRevenue', 0)):,.0f}")
            print(f"Net Income: ${float(latest.get('netIncome', 0)):,.0f}")
        else:
            print("No data available from Alpha Vantage")
            
    except Exception as e:
        print(f"❌ Alpha Vantage error: {e}")
    
    # Method 3: Manual calculation from known values
    print("\n📊 Method 3: Manual calculation")
    print("AAPL's actual TTM revenue should be around $400-450B")
    print("The $391B value seems too low for AAPL's current revenue")
    
    # Check what we have in our database
    print("\n📊 Method 4: Our database values")
    import os
    import psycopg2
    from dotenv import load_dotenv
    
    load_dotenv()
    
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
        
        # Check company_fundamentals
        cur.execute("""
            SELECT revenue, data_source, last_updated
            FROM company_fundamentals 
            WHERE ticker = 'AAPL'
            ORDER BY last_updated DESC
        """)
        
        records = cur.fetchall()
        print("Company fundamentals records:")
        for record in records:
            revenue, source, updated = record
            print(f"  {source}: ${revenue:,.0f} ({updated})")
        
        # Check stocks table
        cur.execute("""
            SELECT revenue_ttm, market_cap, fundamentals_last_update
            FROM stocks 
            WHERE ticker = 'AAPL'
        """)
        
        stock_data = cur.fetchone()
        if stock_data:
            revenue_ttm, market_cap, last_update = stock_data
            print(f"\nStocks table:")
            print(f"  Revenue TTM: ${revenue_ttm:,.0f}")
            print(f"  Market Cap: ${market_cap:,.0f}")
            print(f"  Last Updated: {last_update}")
            
            if revenue_ttm and market_cap:
                ps_ratio = market_cap / revenue_ttm
                print(f"  Calculated P/S Ratio: {ps_ratio:.2f}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_aapl_revenue() 