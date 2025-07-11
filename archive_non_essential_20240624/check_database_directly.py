#!/usr/bin/env python3
"""
Check database directly for MSFT and BAC data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def check_database_directly():
    """Check database directly for ticker data"""
    db = DatabaseManager()
    
    tickers = ["MSFT", "BAC"]
    
    for ticker in tickers:
        print(f"📊 Database check for {ticker}")
        print("=" * 40)
        
        query = """
        SELECT 
            ticker, revenue_ttm, net_income_ttm, ebitda_ttm,
            market_cap, enterprise_value, shares_outstanding,
            total_assets, total_debt, shareholders_equity,
            fundamentals_last_update
        FROM stocks 
        WHERE ticker = %s
        """
        
        result = db.fetch_one(query, (ticker,))
        if result:
            (ticker, revenue, net_income, ebitda, market_cap, enterprise_value, 
             shares_outstanding, total_assets, total_debt, shareholders_equity, 
             last_update) = result
            
            print(f"  Revenue TTM: ${revenue:,.0f}" if revenue else "  Revenue TTM: NULL")
            print(f"  Net Income TTM: ${net_income:,.0f}" if net_income else "  Net Income TTM: NULL")
            print(f"  EBITDA TTM: ${ebitda:,.0f}" if ebitda else "  EBITDA TTM: NULL")
            print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: NULL")
            print(f"  Enterprise Value: ${enterprise_value:,.0f}" if enterprise_value else "  Enterprise Value: NULL")
            print(f"  Shares Outstanding: {shares_outstanding:,.0f}" if shares_outstanding else "  Shares Outstanding: NULL")
            print(f"  Total Assets: ${total_assets:,.0f}" if total_assets else "  Total Assets: NULL")
            print(f"  Total Debt: ${total_debt:,.0f}" if total_debt else "  Total Debt: NULL")
            print(f"  Shareholders Equity: ${shareholders_equity:,.0f}" if shareholders_equity else "  Shareholders Equity: NULL")
            print(f"  Last Update: {last_update}")
        else:
            print(f"  No data found for {ticker}")
        
        print()

if __name__ == "__main__":
    check_database_directly() 