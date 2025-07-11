#!/usr/bin/env python3
"""
Simple AVGO calculation debug
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def simple_avgo_debug():
    """Simple debug of AVGO calculations"""
    db = DatabaseManager()
    
    print("🔍 SIMPLE AVGO DEBUG")
    print("=" * 40)
    
    # Get AVGO data
    query = """
    SELECT 
        revenue_ttm, net_income_ttm, ebitda_ttm,
        market_cap, enterprise_value, shares_outstanding
    FROM stocks 
    WHERE ticker = 'AVGO'
    """
    
    result = db.fetch_one(query)
    
    if result:
        revenue, net_income, ebitda, market_cap, enterprise_value, shares_outstanding = result
        
        print(f"Revenue: ${revenue:,.0f}")
        print(f"Net Income: ${net_income:,.0f}")
        print(f"EBITDA: ${ebitda:,.0f}")
        print(f"Market Cap: ${market_cap:,.0f}")
        print(f"Enterprise Value: ${enterprise_value:,.0f}")
        print(f"Shares Outstanding: {shares_outstanding:,.0f}")
        
        # Calculate ratios
        pe_ratio = market_cap / net_income if market_cap and net_income else None
        ps_ratio = market_cap / revenue if market_cap and revenue else None
        ev_ebitda = enterprise_value / ebitda if enterprise_value and ebitda else None
        
        print(f"\nCalculated Ratios:")
        print(f"PE Ratio: {pe_ratio:.2f}" if pe_ratio else "NULL")
        print(f"PS Ratio: {ps_ratio:.2f}" if ps_ratio else "NULL")
        print(f"EV/EBITDA: {ev_ebitda:.2f}" if ev_ebitda else "NULL")
        
        print(f"\nExpected (Web):")
        print(f"PE Ratio: ~25.0")
        print(f"PS Ratio: ~8.0")
        print(f"EV/EBITDA: ~15.0")
        
        print(f"\nIssues:")
        if pe_ratio and pe_ratio > 100:
            print(f"❌ PE Ratio too high - Net income may be too low")
        if ps_ratio and ps_ratio > 20:
            print(f"❌ PS Ratio too high - Revenue may be too low")
        if ev_ebitda and ev_ebitda > 30:
            print(f"❌ EV/EBITDA too high - EBITDA may be too low")

if __name__ == "__main__":
    simple_avgo_debug() 