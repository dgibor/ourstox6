#!/usr/bin/env python3
"""
Manually fix MSFT and BAC data with correct revenue and net income values
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def fix_ticker_data(ticker, correct_revenue, correct_net_income, correct_ebitda):
    """Fix data for a specific ticker"""
    db = DatabaseManager()
    
    print(f"🔧 Fixing {ticker} data...")
    
    # Update with correct values
    update_query = """
    UPDATE stocks SET
        revenue_ttm = %s,
        net_income_ttm = %s,
        ebitda_ttm = %s,
        fundamentals_last_update = %s
    WHERE ticker = %s
    """
    
    db.execute_update(update_query, (
        correct_revenue,
        correct_net_income,
        correct_ebitda,
        datetime.now(),
        ticker
    ))
    
    print(f"✅ Updated {ticker} with:")
    print(f"  Revenue: ${correct_revenue:,.0f}")
    print(f"  Net Income: ${correct_net_income:,.0f}")
    print(f"  EBITDA: ${correct_ebitda:,.0f}")
    
    # Verify the update
    verify_query = """
    SELECT revenue_ttm, net_income_ttm, ebitda_ttm
    FROM stocks WHERE ticker = %s
    """
    
    result = db.fetch_one(verify_query, (ticker,))
    if result:
        revenue, net_income, ebitda = result
        print(f"✅ Verification for {ticker}:")
        print(f"  Revenue: ${revenue:,.0f}" if revenue else "  Revenue: NULL")
        print(f"  Net Income: ${net_income:,.0f}" if net_income else "  Net Income: NULL")
        print(f"  EBITDA: ${ebitda:,.0f}" if ebitda else "  EBITDA: NULL")

def main():
    """Fix MSFT and BAC data"""
    
    # Correct values from FMP API (2024 annual data)
    msft_data = {
        'revenue': 245122000000,  # $245.1B
        'net_income': 88136000000,  # $88.1B
        'ebitda': 133009000000  # $133.0B
    }
    
    bac_data = {
        'revenue': 192434000000,  # $192.4B
        'net_income': 27132000000,  # $27.1B
        'ebitda': 31443000000  # $31.4B
    }
    
    print("🔧 Fixing MSFT and BAC data with correct values")
    print("=" * 60)
    
    # Fix MSFT
    fix_ticker_data('MSFT', msft_data['revenue'], msft_data['net_income'], msft_data['ebitda'])
    
    print("\n" + "-" * 60 + "\n")
    
    # Fix BAC
    fix_ticker_data('BAC', bac_data['revenue'], bac_data['net_income'], bac_data['ebitda'])
    
    print("\n🎉 Data fixing completed!")

if __name__ == "__main__":
    main() 