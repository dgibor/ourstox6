#!/usr/bin/env python3
"""
Manually fix AVGO's enterprise value and shares outstanding
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def fix_avgo_manual():
    """Manually fix AVGO's missing data"""
    db = DatabaseManager()
    
    print("🔧 MANUALLY FIXING AVGO DATA")
    print("=" * 40)
    
    # Based on web research for AVGO (Broadcom):
    # - Market Cap: ~$1.29T (from FMP)
    # - Enterprise Value: ~$1.35T (Market Cap + Total Debt - Cash)
    # - Shares Outstanding: ~4.7B shares
    # - Total Debt: $67.6B (from FMP)
    # - Cash: $9.3B (from FMP)
    
    # Calculate correct enterprise value
    market_cap = 1294300874600  # From FMP
    total_debt = 67566000000    # From FMP
    cash = 9348000000           # From FMP
    enterprise_value = market_cap + total_debt - cash
    
    # Shares outstanding (from web research)
    shares_outstanding = 4700000000  # 4.7B shares
    
    print(f"Market Cap: ${market_cap:,.0f}")
    print(f"Total Debt: ${total_debt:,.0f}")
    print(f"Cash: ${cash:,.0f}")
    print(f"Calculated Enterprise Value: ${enterprise_value:,.0f}")
    print(f"Shares Outstanding: {shares_outstanding:,.0f}")
    
    # Update the database
    update_query = """
    UPDATE stocks 
    SET 
        enterprise_value = %s,
        shares_outstanding = %s
    WHERE ticker = 'AVGO'
    """
    
    try:
        db.execute_update(update_query, (enterprise_value, shares_outstanding))
        print(f"✅ Successfully updated AVGO data")
        
        # Verify the update
        verify_query = """
        SELECT 
            revenue_ttm, net_income_ttm, ebitda_ttm,
            market_cap, enterprise_value, shares_outstanding,
            total_assets, total_debt, shareholders_equity
        FROM stocks 
        WHERE ticker = 'AVGO'
        """
        
        result = db.fetch_one(verify_query)
        if result:
            (revenue, net_income, ebitda, market_cap, enterprise_value, 
             shares_outstanding, total_assets, total_debt, shareholders_equity) = result
            
            # Convert to float to avoid decimal issues
            def to_float(val):
                try:
                    return float(val) if val is not None else None
                except Exception:
                    return None
            
            revenue = to_float(revenue)
            net_income = to_float(net_income)
            ebitda = to_float(ebitda)
            market_cap = to_float(market_cap)
            enterprise_value = to_float(enterprise_value)
            shares_outstanding = to_float(shares_outstanding)
            shareholders_equity = to_float(shareholders_equity)
            
            # Calculate ratios
            current_price = 275.65  # From our data
            pe_ratio = market_cap / net_income if market_cap and net_income else None
            pb_ratio = current_price / (shareholders_equity / shares_outstanding) if all([current_price, shareholders_equity, shares_outstanding]) else None
            ps_ratio = market_cap / revenue if market_cap and revenue else None
            ev_ebitda = enterprise_value / ebitda if enterprise_value and ebitda else None
            
            print(f"\n📊 UPDATED AVGO RATIOS:")
            print(f"PE Ratio: {pe_ratio:.2f}" if pe_ratio else "PE Ratio: NULL")
            print(f"PB Ratio: {pb_ratio:.2f}" if pb_ratio else "PB Ratio: NULL")
            print(f"PS Ratio: {ps_ratio:.2f}" if ps_ratio else "PS Ratio: NULL")
            print(f"EV/EBITDA: {ev_ebitda:.2f}" if ev_ebitda else "EV/EBITDA: NULL")
            
            return True
        else:
            print(f"❌ Failed to verify update")
            return False
            
    except Exception as e:
        print(f"❌ Error updating AVGO: {e}")
        return False

if __name__ == "__main__":
    fix_avgo_manual() 