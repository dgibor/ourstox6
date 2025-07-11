#!/usr/bin/env python3
"""
Debug why AVGO calculations are different from web references
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def debug_avgo_calculations():
    """Debug AVGO calculation differences"""
    db = DatabaseManager()
    
    print("🔍 DEBUGGING AVGO CALCULATION DIFFERENCES")
    print("=" * 60)
    
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
        
        print(f"📊 CURRENT DATA:")
        print(f"Revenue: ${revenue:,.0f}")
        print(f"Net Income: ${net_income:,.0f}")
        print(f"EBITDA: ${ebitda:,.0f}")
        print(f"Market Cap: ${market_cap:,.0f}")
        print(f"Enterprise Value: ${enterprise_value:,.0f}")
        print(f"Current Price: ${current_price:.2f}")
        print(f"Shares Outstanding: {shares_outstanding:,.0f}")
        print()
        
        # Calculate ratios step by step
        print(f"🔢 CALCULATION BREAKDOWN:")
        
        # PE Ratio
        if market_cap and net_income:
            pe_ratio = market_cap / net_income
            print(f"PE Ratio = Market Cap / Net Income")
            print(f"PE Ratio = ${market_cap:,.0f} / ${net_income:,.0f}")
            print(f"PE Ratio = {pe_ratio:.2f}")
        else:
            pe_ratio = None
            print(f"PE Ratio = NULL (missing data)")
        
        print()
        
        # PS Ratio
        if market_cap and revenue:
            ps_ratio = market_cap / revenue
            print(f"PS Ratio = Market Cap / Revenue")
            print(f"PS Ratio = ${market_cap:,.0f} / ${revenue:,.0f}")
            print(f"PS Ratio = {ps_ratio:.2f}")
        else:
            ps_ratio = None
            print(f"PS Ratio = NULL (missing data)")
        
        print()
        
        # EV/EBITDA
        if enterprise_value and ebitda:
            ev_ebitda = enterprise_value / ebitda
            print(f"EV/EBITDA = Enterprise Value / EBITDA")
            print(f"EV/EBITDA = ${enterprise_value:,.0f} / ${ebitda:,.0f}")
            print(f"EV/EBITDA = {ev_ebitda:.2f}")
        else:
            ev_ebitda = None
            print(f"EV/EBITDA = NULL (missing data)")
        
        print()
        
        # PB Ratio
        if current_price and shareholders_equity and shares_outstanding:
            book_value_per_share = shareholders_equity / shares_outstanding
            pb_ratio = current_price / book_value_per_share
            print(f"Book Value Per Share = Shareholders Equity / Shares Outstanding")
            print(f"Book Value Per Share = ${shareholders_equity:,.0f} / {shares_outstanding:,.0f}")
            print(f"Book Value Per Share = ${book_value_per_share:.2f}")
            print(f"PB Ratio = Current Price / Book Value Per Share")
            print(f"PB Ratio = ${current_price:.2f} / ${book_value_per_share:.2f}")
            print(f"PB Ratio = {pb_ratio:.2f}")
        else:
            pb_ratio = None
            print(f"PB Ratio = NULL (missing data)")
        
        print(f"\n{'='*60}")
        print("🎯 WEB REFERENCE COMPARISON:")
        print("=" * 60)
        
        print(f"\n📊 Expected Values (from web research):")
        print(f"Revenue: ~$35.8B (FMP reference)")
        print(f"Net Income: ~$14.0B (FMP reference)")
        print(f"PE Ratio: ~25.0 (StockAnalysis)")
        print(f"PS Ratio: ~8.0 (Macrotrends)")
        print(f"EV/EBITDA: ~15.0 (Macrotrends)")
        print(f"PB Ratio: ~19.0 (Estimated)")
        
        print(f"\n🔍 ANALYSIS:")
        
        # Check if revenue is inflated
        if revenue and revenue > 40e9:  # If revenue > $40B
            print(f"⚠️  Revenue appears inflated: ${revenue/1e9:.1f}B vs expected ~$35.8B")
            print(f"   This could be due to TTM calculation summing quarterly data")
        
        # Check if net income is too low
        if net_income and net_income < 10e9:  # If net income < $10B
            print(f"⚠️  Net income appears too low: ${net_income/1e9:.1f}B vs expected ~$14.0B")
            print(f"   This could be due to TTM calculation issues")
        
        # Check PE ratio
        if pe_ratio and pe_ratio > 100:
            print(f"⚠️  PE ratio is very high: {pe_ratio:.1f} vs expected ~25.0")
            print(f"   This suggests net income is too low or market cap is too high")
        
        # Check PS ratio
        if ps_ratio and ps_ratio > 20:
            print(f"⚠️  PS ratio is very high: {ps_ratio:.1f} vs expected ~8.0")
            print(f"   This suggests revenue is too low or market cap is too high")
        
        # Check EV/EBITDA
        if ev_ebitda and ev_ebitda > 30:
            print(f"⚠️  EV/EBITDA is very high: {ev_ebitda:.1f} vs expected ~15.0")
            print(f"   This suggests EBITDA is too low or enterprise value is too high")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"1. Check if TTM calculation is summing quarterly data instead of using annual")
        print(f"2. Verify that FMP API is returning correct annual data")
        print(f"3. Consider using different data source for comparison")
        print(f"4. Check if there are any data scaling issues")

if __name__ == "__main__":
    debug_avgo_calculations() 