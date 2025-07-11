#!/usr/bin/env python3
"""
Fix scaling issues for XOM, META, and fetch data for PLTR
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService

def fix_ticker_scaling(ticker):
    """Fix scaling issues for a ticker by re-fetching data"""
    db = DatabaseManager()
    fmp = FMPService()
    
    print(f"🔧 Fixing scaling for {ticker}")
    print("=" * 50)
    
    # 1. Reset fundamental data
    print(f"1️⃣ Resetting {ticker} data...")
    reset_query = """
    UPDATE stocks SET
        revenue_ttm = NULL,
        net_income_ttm = NULL,
        ebitda_ttm = NULL,
        total_assets = NULL,
        total_debt = NULL,
        shareholders_equity = NULL,
        cash_and_equivalents = NULL,
        current_assets = NULL,
        current_liabilities = NULL,
        operating_income = NULL,
        free_cash_flow = NULL,
        market_cap = NULL,
        enterprise_value = NULL,
        shares_outstanding = NULL,
        diluted_eps_ttm = NULL,
        book_value_per_share = NULL,
        fundamentals_last_update = NULL
    WHERE ticker = %s
    """
    
    db.execute_update(reset_query, (ticker,))
    print(f"✅ Reset fundamental data for {ticker}")
    
    # 2. Re-fetch fundamental data
    print(f"2️⃣ Re-fetching fundamental data for {ticker}...")
    
    try:
        # Fetch financial statements
        financial_data = fmp.fetch_financial_statements(ticker)
        if not financial_data:
            print(f"❌ Failed to fetch financial statements for {ticker}")
            return False
        
        # Fetch key statistics
        key_stats = fmp.fetch_key_statistics(ticker)
        if not key_stats:
            print(f"❌ Failed to fetch key statistics for {ticker}")
            return False
        
        # Store the data
        success = fmp.store_fundamental_data(ticker, financial_data, key_stats)
        if success:
            print(f"✅ Successfully stored fundamental data for {ticker}")
        else:
            print(f"❌ Failed to store fundamental data for {ticker}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        return False
    
    # 3. Verify the data
    print(f"3️⃣ Verifying {ticker} data...")
    
    verify_query = """
    SELECT 
        revenue_ttm, net_income_ttm, ebitda_ttm, total_assets, shareholders_equity,
        market_cap, shares_outstanding, diluted_eps_ttm
    FROM stocks WHERE ticker = %s
    """
    
    result = db.fetch_one(verify_query, (ticker,))
    if result:
        revenue, net_income, ebitda, assets, equity, market_cap, shares, eps = result
        print(f"✅ Verification for {ticker}:")
        print(f"  Revenue: ${revenue:,.0f}" if revenue else "  Revenue: NULL")
        print(f"  Net Income: ${net_income:,.0f}" if net_income else "  Net Income: NULL")
        print(f"  EBITDA: ${ebitda:,.0f}" if ebitda else "  EBITDA: NULL")
        print(f"  Total Assets: ${assets:,.0f}" if assets else "  Total Assets: NULL")
        print(f"  Shareholders Equity: ${equity:,.0f}" if equity else "  Shareholders Equity: NULL")
        print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: NULL")
        print(f"  Shares Outstanding: {shares:,.0f}" if shares else "  Shares Outstanding: NULL")
        print(f"  EPS: ${eps:.2f}" if eps else "  EPS: NULL")
    else:
        print(f"❌ No data found for {ticker}")
        return False
    
    return True

def main():
    """Fix scaling for XOM, META, and fetch PLTR"""
    tickers = ["XOM", "META", "PLTR"]
    
    for ticker in tickers:
        print(f"\n{'='*60}")
        success = fix_ticker_scaling(ticker)
        if success:
            print(f"✅ {ticker} processing completed successfully")
        else:
            print(f"❌ {ticker} processing failed")
        print(f"{'='*60}\n")
    
    print("🎉 All processing completed!")

if __name__ == "__main__":
    main() 