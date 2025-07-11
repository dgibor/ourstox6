import os
import sys
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def debug_yahoo_raw_data(ticker='AAPL'):
    """Debug raw Yahoo Finance data"""
    try:
        print(f"\n=== Raw Yahoo Finance Debug for {ticker} ===")
        
        # Get the stock object
        stock = yf.Ticker(ticker)
        
        # Get financial statements
        print("\n📊 Fetching financial statements...")
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        print(f"\n📈 Income Statement Shape: {income_stmt.shape}")
        print(f"📈 Income Statement Columns: {list(income_stmt.columns)}")
        print(f"📈 Income Statement Index: {list(income_stmt.index)}")
        
        if not income_stmt.empty:
            print(f"\n📊 Income Statement Data:")
            print(income_stmt.head(10))
            
            # Check for Total Revenue
            if 'Total Revenue' in income_stmt.index:
                revenue_row = income_stmt.loc['Total Revenue']
                print(f"\n💰 Total Revenue Row:")
                print(revenue_row)
                
                # Calculate TTM from last 4 quarters
                if len(revenue_row) >= 4:
                    ttm_revenue = revenue_row.head(4).sum()
                    print(f"\n🧮 TTM Revenue (last 4 quarters): ${ttm_revenue:,.0f}")
                    print(f"  Quarters used: {list(revenue_row.head(4).index)}")
                    print(f"  Values: {list(revenue_row.head(4).values)}")
                else:
                    print(f"\n⚠️  Not enough quarters for TTM calculation")
                    print(f"  Available quarters: {len(revenue_row)}")
            else:
                print(f"\n❌ 'Total Revenue' not found in income statement")
                print(f"  Available rows: {list(income_stmt.index)}")
        else:
            print(f"\n❌ Income statement is empty")
        
        # Check balance sheet
        print(f"\n📊 Balance Sheet Shape: {balance_sheet.shape}")
        if not balance_sheet.empty:
            print(f"📊 Balance Sheet Columns: {list(balance_sheet.columns)}")
            print(f"📊 Balance Sheet Index: {list(balance_sheet.index)}")
        
        # Check cash flow
        print(f"\n📊 Cash Flow Shape: {cash_flow.shape}")
        if not cash_flow.empty:
            print(f"📊 Cash Flow Columns: {list(cash_flow.columns)}")
            print(f"📊 Cash Flow Index: {list(cash_flow.index)}")
        
        # Get info
        print(f"\n📊 Fetching stock info...")
        info = stock.info
        
        print(f"\n📊 Key Info Fields:")
        key_fields = ['marketCap', 'enterpriseValue', 'sharesOutstanding', 'currentPrice', 
                     'trailingPE', 'priceToBook', 'priceToSalesTrailing12Months']
        for field in key_fields:
            value = info.get(field, 'N/A')
            print(f"  {field}: {value}")
        
    except Exception as e:
        print(f"❌ Error debugging Yahoo Finance raw data: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main debug function"""
    ticker = 'AAPL'
    
    print("🔍 Raw Yahoo Finance Data Debug Script")
    print("=" * 50)
    
    debug_yahoo_raw_data(ticker)
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    main() 