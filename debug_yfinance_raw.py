#!/usr/bin/env python3
"""
Debug script to test raw yfinance data fetching
"""

import yfinance as yf
import pandas as pd

def test_raw_yfinance():
    """Test raw yfinance data fetching"""
    print("🔍 Testing raw yfinance data...")
    
    try:
        # Test with AAPL
        print("📊 Fetching AAPL data with yfinance...")
        stock = yf.Ticker('AAPL')
        
        # Get financial statements
        print("\n📋 Income Statement:")
        income_stmt = stock.financials
        print(f"Shape: {income_stmt.shape}")
        print(f"Columns: {list(income_stmt.columns)}")
        print(f"Index: {list(income_stmt.index)}")
        
        if not income_stmt.empty:
            print("\n📊 Income Statement Data:")
            print(income_stmt.head())
            
            # Check for Total Revenue
            if 'Total Revenue' in income_stmt.index:
                revenue_data = income_stmt.loc['Total Revenue']
                print(f"\n💰 Total Revenue data:")
                print(revenue_data)
                print(f"Sum of last 4 quarters: {revenue_data.head(4).sum():,.0f}")
            else:
                print("❌ 'Total Revenue' not found in income statement")
        else:
            print("❌ Income statement is empty")
        
        # Get balance sheet
        print("\n📋 Balance Sheet:")
        balance_sheet = stock.balance_sheet
        print(f"Shape: {balance_sheet.shape}")
        if not balance_sheet.empty:
            print("Columns:", list(balance_sheet.columns))
            print("Index:", list(balance_sheet.index))
        
        # Get cash flow
        print("\n📋 Cash Flow:")
        cash_flow = stock.cashflow
        print(f"Shape: {cash_flow.shape}")
        if not cash_flow.empty:
            print("Columns:", list(cash_flow.columns))
            print("Index:", list(cash_flow.index))
        
        # Get info
        print("\n📋 Key Statistics:")
        info = stock.info
        print(f"Keys available: {list(info.keys())}")
        
        # Check specific TTM metrics
        ttm_metrics = {
            'trailingEps': info.get('trailingEps'),
            'priceToSalesTrailing12Months': info.get('priceToSalesTrailing12Months'),
            'enterpriseToEbitda': info.get('enterpriseToEbitda'),
            'marketCap': info.get('marketCap'),
            'revenuePerShare': info.get('revenuePerShare'),
            'totalRevenue': info.get('totalRevenue')
        }
        
        print(f"\n💰 TTM Metrics:")
        for key, value in ttm_metrics.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_yfinance() 