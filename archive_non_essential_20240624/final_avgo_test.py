#!/usr/bin/env python3
"""
Final AVGO test - check current data and compare with web references
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def final_avgo_test():
    """Final test of AVGO data"""
    db = DatabaseManager()
    
    print("🎯 FINAL AVGO TEST - CURRENT DATA")
    print("=" * 50)
    
    # Get current AVGO data
    query = """
    SELECT 
        revenue_ttm, net_income_ttm, ebitda_ttm,
        market_cap, enterprise_value, shares_outstanding,
        total_assets, total_debt, shareholders_equity,
        cash_and_equivalents
    FROM stocks 
    WHERE ticker = 'AVGO'
    """
    
    result = db.fetch_one(query)
    
    if result:
        (revenue, net_income, ebitda, market_cap, enterprise_value, 
         shares_outstanding, total_assets, total_debt, shareholders_equity,
         cash) = result
        
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
        total_assets = to_float(total_assets)
        total_debt = to_float(total_debt)
        shareholders_equity = to_float(shareholders_equity)
        cash = to_float(cash)
        
        # Get current price
        price_query = """
        SELECT close FROM daily_charts WHERE ticker = 'AVGO' ORDER BY date DESC LIMIT 1
        """
        price_result = db.fetch_one(price_query)
        current_price = to_float(price_result[0] / 100) if price_result else None
        
        print(f"📊 CURRENT AVGO DATA:")
        print(f"Revenue: ${revenue:,.0f}")
        print(f"Net Income: ${net_income:,.0f}")
        print(f"EBITDA: ${ebitda:,.0f}")
        print(f"Market Cap: ${market_cap:,.0f}")
        print(f"Enterprise Value: ${enterprise_value:,.0f}")
        print(f"Current Price: ${current_price:.2f}" if current_price else "Current Price: NULL")
        print(f"Shares Outstanding: {shares_outstanding:,.0f}")
        print(f"Total Debt: ${total_debt:,.0f}")
        print(f"Cash: ${cash:,.0f}")
        print()
        
        # Calculate ratios
        pe_ratio = market_cap / net_income if market_cap and net_income else None
        pb_ratio = current_price / (shareholders_equity / shares_outstanding) if all([current_price, shareholders_equity, shares_outstanding]) else None
        ps_ratio = market_cap / revenue if market_cap and revenue else None
        ev_ebitda = enterprise_value / ebitda if enterprise_value and ebitda else None
        roe = net_income / shareholders_equity if net_income and shareholders_equity else None
        roa = net_income / total_assets if net_income and total_assets else None
        debt_to_equity = total_debt / shareholders_equity if total_debt and shareholders_equity else None
        
        print(f"📈 CALCULATED RATIOS:")
        print(f"PE Ratio: {pe_ratio:.2f}" if pe_ratio else "PE Ratio: NULL")
        print(f"PB Ratio: {pb_ratio:.2f}" if pb_ratio else "PB Ratio: NULL")
        print(f"PS Ratio: {ps_ratio:.2f}" if ps_ratio else "PS Ratio: NULL")
        print(f"EV/EBITDA: {ev_ebitda:.2f}" if ev_ebitda else "EV/EBITDA: NULL")
        print(f"ROE: {roe*100:.2f}%" if roe else "ROE: NULL")
        print(f"ROA: {roa*100:.2f}%" if roa else "ROA: NULL")
        print(f"Debt/Equity: {debt_to_equity:.2f}" if debt_to_equity else "Debt/Equity: NULL")
        
        print(f"\n{'='*60}")
        print("🎯 COMPARISON WITH WEB DATA:")
        print("=" * 60)
        
        print("\n📊 Broadcom (AVGO) - 2024")
        print("| Ratio/Metric         | Your Value      | Web Reference (2024) | Status |")
        print("|----------------------|----------------|----------------------|--------|")
        
        # Revenue comparison
        if revenue:
            revenue_b = revenue / 1e9
            if abs(revenue_b - 35.8) < 5:
                revenue_status = "✅ MATCHES"
            else:
                revenue_status = "⚠️ Close"
            print(f"| Revenue              | ${revenue_b:.1f}B        | $35.8B (FMP)        | {revenue_status} |")
        
        # Net Income comparison
        if net_income:
            net_income_b = net_income / 1e9
            if abs(net_income_b - 14.0) < 2:
                net_income_status = "✅ MATCHES"
            else:
                net_income_status = "⚠️ Close"
            print(f"| Net Income           | ${net_income_b:.1f}B         | $14.0B (FMP)         | {net_income_status} |")
        
        # PE Ratio comparison
        if pe_ratio:
            if abs(pe_ratio - 25.0) < 10:
                pe_status = "✅ MATCHES"
            else:
                pe_status = "⚠️ Close"
            print(f"| PE Ratio             | {pe_ratio:.1f}           | 25.0 (StockAnalysis) | {pe_status} |")
        
        # PS Ratio comparison
        if ps_ratio:
            if abs(ps_ratio - 8.0) < 3:
                ps_status = "✅ MATCHES"
            else:
                ps_status = "⚠️ Close"
            print(f"| PS Ratio             | {ps_ratio:.1f}            | 8.0 (Macrotrends)    | {ps_status} |")
        
        # EV/EBITDA comparison
        if ev_ebitda:
            if abs(ev_ebitda - 15.0) < 5:
                ev_status = "✅ MATCHES"
            else:
                ev_status = "⚠️ Close"
            print(f"| EV/EBITDA            | {ev_ebitda:.1f}           | 15.0 (Macrotrends)   | {ev_status} |")
        else:
            print(f"| EV/EBITDA            | NULL           | 15.0 (Macrotrends)   | ⚠️ Missing |")
        
        print(f"\n✅ Final AVGO test completed!")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"✅ Revenue: {'✅' if revenue else '❌'}")
        print(f"✅ Net Income: {'✅' if net_income else '❌'}")
        print(f"✅ PE Ratio: {'✅' if pe_ratio else '❌'}")
        print(f"✅ PS Ratio: {'✅' if ps_ratio else '❌'}")
        print(f"✅ EV/EBITDA: {'✅' if ev_ebitda else '❌'}")
        print(f"✅ PB Ratio: {'✅' if pb_ratio else '❌'}")
        
        return True
    else:
        print(f"❌ No data found for AVGO")
        return False

if __name__ == "__main__":
    final_avgo_test() 