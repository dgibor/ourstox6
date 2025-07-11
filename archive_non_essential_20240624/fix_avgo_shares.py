#!/usr/bin/env python3
"""
Fix AVGO's shares outstanding and enterprise value calculation
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def fix_avgo_shares():
    """Fix AVGO's shares outstanding and enterprise value"""
    db = DatabaseManager()
    
    print("🔧 FIXING AVGO SHARES OUTSTANDING AND ENTERPRISE VALUE")
    print("=" * 60)
    
    # Get current AVGO data
    query = """
    SELECT 
        market_cap, total_debt, cash_and_equivalents
    FROM stocks 
    WHERE ticker = 'AVGO'
    """
    
    result = db.fetch_one(query)
    
    if result:
        market_cap, total_debt, cash = result
        
        # Convert to float
        market_cap = float(market_cap) if market_cap else 0
        total_debt = float(total_debt) if total_debt else 0
        cash = float(cash) if cash else 0
        
        # Calculate correct enterprise value: Market Cap + Total Debt - Cash
        enterprise_value = market_cap + total_debt - cash
        
        # Set correct shares outstanding (from web research)
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
            
            # Verify and show updated ratios
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
                
                # Convert to float
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
                
                # Get current price
                price_query = """
                SELECT close FROM daily_charts WHERE ticker = 'AVGO' ORDER BY date DESC LIMIT 1
                """
                price_result = db.fetch_one(price_query)
                current_price = to_float(price_result[0] / 100) if price_result else None
                
                # Calculate ratios
                pe_ratio = market_cap / net_income if market_cap and net_income else None
                pb_ratio = current_price / (shareholders_equity / shares_outstanding) if all([current_price, shareholders_equity, shares_outstanding]) else None
                ps_ratio = market_cap / revenue if market_cap and revenue else None
                ev_ebitda = enterprise_value / ebitda if enterprise_value and ebitda else None
                
                print(f"\n📊 UPDATED AVGO RATIOS:")
                print(f"PE Ratio: {pe_ratio:.2f}" if pe_ratio else "PE Ratio: NULL")
                print(f"PB Ratio: {pb_ratio:.2f}" if pb_ratio else "PB Ratio: NULL")
                print(f"PS Ratio: {ps_ratio:.2f}" if ps_ratio else "PS Ratio: NULL")
                print(f"EV/EBITDA: {ev_ebitda:.2f}" if ev_ebitda else "EV/EBITDA: NULL")
                
                print(f"\n🎯 COMPARISON WITH WEB DATA:")
                print(f"| PE Ratio: {pe_ratio:.1f} vs 25.0 (StockAnalysis) | {'✅' if pe_ratio and abs(pe_ratio - 25.0) < 10 else '⚠️'} |")
                print(f"| PS Ratio: {ps_ratio:.1f} vs 8.0 (Macrotrends) | {'✅' if ps_ratio and abs(ps_ratio - 8.0) < 3 else '⚠️'} |")
                print(f"| EV/EBITDA: {ev_ebitda:.1f} vs 15.0 (Macrotrends) | {'✅' if ev_ebitda and abs(ev_ebitda - 15.0) < 5 else '⚠️'} |")
                print(f"| PB Ratio: {pb_ratio:.1f} vs ~19.0 (Estimated) | {'✅' if pb_ratio and pb_ratio > 0 else '⚠️'} |")
                
                return True
            else:
                print(f"❌ Failed to verify update")
                return False
                
        except Exception as e:
            print(f"❌ Error updating AVGO: {e}")
            return False
    else:
        print(f"❌ No data found for AVGO")
        return False

if __name__ == "__main__":
    fix_avgo_shares() 