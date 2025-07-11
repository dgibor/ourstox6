#!/usr/bin/env python3
"""
Calculate missing ratios for AAPL
"""

import sys
import os
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def calculate_missing_ratios(ticker=None):
    """Calculate missing ratios for a ticker"""
    db = DatabaseManager()
    if not ticker:
        ticker = "AAPL"
    
    print(f"🧮 Calculating missing ratios for {ticker}")
    print("=" * 50)
    
    # Get current price from daily_charts
    price_query = """
    SELECT close FROM daily_charts WHERE ticker = %s ORDER BY date DESC LIMIT 1
    """
    price_result = db.fetch_one(price_query, (ticker,))
    current_price = price_result[0] / 100 if price_result and price_result[0] else None
    
    # Get other data from stocks table
    query = """
    SELECT 
        market_cap, enterprise_value, shares_outstanding,
        revenue_ttm, net_income_ttm, ebitda_ttm, book_value_per_share,
        total_debt, shareholders_equity, total_assets
    FROM stocks 
    WHERE ticker = %s
    """
    
    result = db.fetch_one(query, (ticker,))
    if not result:
        print(f"❌ No data found for {ticker}")
        return
    
    (market_cap, enterprise_value, shares_outstanding,
     revenue_ttm, net_income_ttm, ebitda_ttm, book_value_per_share,
     total_debt, shareholders_equity, total_assets) = result
    
    # Convert all Decimal values to float for calculations
    def to_float(val):
        try:
            return float(val) if val is not None else None
        except Exception:
            return None
    
    market_cap = to_float(market_cap)
    enterprise_value = to_float(enterprise_value)
    shares_outstanding = to_float(shares_outstanding)
    revenue_ttm = to_float(revenue_ttm)
    net_income_ttm = to_float(net_income_ttm)
    ebitda_ttm = to_float(ebitda_ttm)
    book_value_per_share = to_float(book_value_per_share)
    total_debt = to_float(total_debt)
    shareholders_equity = to_float(shareholders_equity)
    total_assets = to_float(total_assets)
    current_price = to_float(current_price)
    
    print(f"📊 Current data:")
    print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: NULL")
    print(f"  Enterprise Value: ${enterprise_value:,.0f}" if enterprise_value else "  Enterprise Value: NULL")
    print(f"  Current Price: ${current_price:.2f}" if current_price else "  Current Price: NULL")
    print(f"  Book Value Per Share: ${book_value_per_share:.2f}" if book_value_per_share else "  Book Value Per Share: NULL")
    print(f"  Revenue TTM: ${revenue_ttm:,.0f}" if revenue_ttm else "  Revenue TTM: NULL")
    print(f"  EBITDA TTM: ${ebitda_ttm:,.0f}" if ebitda_ttm else "  EBITDA TTM: NULL")
    
    # Calculate missing ratios
    ratios = {}
    
    # PB Ratio = Price / Book Value Per Share
    if current_price and book_value_per_share and book_value_per_share > 0:
        ratios['pb_ratio'] = current_price / book_value_per_share
        print(f"📈 Calculated PB Ratio: {ratios['pb_ratio']:.2f}")
    else:
        print("❌ Cannot calculate PB Ratio - missing price or book value")
    
    # PS Ratio = Market Cap / Revenue
    if market_cap and revenue_ttm and revenue_ttm > 0:
        ratios['ps_ratio'] = market_cap / revenue_ttm
        print(f"📈 Calculated PS Ratio: {ratios['ps_ratio']:.2f}")
    else:
        print("❌ Cannot calculate PS Ratio - missing market cap or revenue")
    
    # EV/EBITDA = Enterprise Value / EBITDA
    if enterprise_value and ebitda_ttm and ebitda_ttm > 0:
        ratios['ev_ebitda'] = enterprise_value / ebitda_ttm
        print(f"📈 Calculated EV/EBITDA: {ratios['ev_ebitda']:.2f}")
    else:
        print("❌ Cannot calculate EV/EBITDA - missing enterprise value or EBITDA")
    
    # Update database with calculated ratios
    if ratios:
        print(f"\n💾 Updating database with calculated ratios...")
        
        # Insert or update in financial_ratios table
        insert_query = """
        INSERT INTO financial_ratios (
            ticker, calculation_date, pb_ratio, ps_ratio, ev_ebitda, 
            market_cap, enterprise_value, last_updated
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker, calculation_date) DO UPDATE SET
            pb_ratio = EXCLUDED.pb_ratio,
            ps_ratio = EXCLUDED.ps_ratio,
            ev_ebitda = EXCLUDED.ev_ebitda,
            market_cap = EXCLUDED.market_cap,
            enterprise_value = EXCLUDED.enterprise_value,
            last_updated = EXCLUDED.last_updated
        """
        
        db.execute_update(insert_query, (
            ticker,
            datetime.now().date(),
            ratios.get('pb_ratio'),
            ratios.get('ps_ratio'),
            ratios.get('ev_ebitda'),
            market_cap,
            enterprise_value,
            datetime.now()
        ))
        
        print(f"✅ Updated {len(ratios)} ratios in financial_ratios table")
        
        # Verify the update
        verify_query = """
        SELECT pb_ratio, ps_ratio, ev_ebitda, calculation_date
        FROM financial_ratios WHERE ticker = %s ORDER BY calculation_date DESC LIMIT 1
        """
        verify_result = db.fetch_one(verify_query, (ticker,))
        if verify_result:
            pb, ps, ev_ebitda, calc_date = verify_result
            print(f"\n✅ Verification:")
            print(f"  PB Ratio: {pb:.2f}" if pb else "  PB Ratio: NULL")
            print(f"  PS Ratio: {ps:.2f}" if ps else "  PS Ratio: NULL")
            print(f"  EV/EBITDA: {ev_ebitda:.2f}" if ev_ebitda else "  EV/EBITDA: NULL")
            print(f"  Calculation Date: {calc_date}")
    else:
        print("❌ No ratios calculated - missing required data")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate missing ratios for a ticker.")
    parser.add_argument('--ticker', type=str, default='AAPL', help='Ticker symbol (default: AAPL)')
    args = parser.parse_args()
    calculate_missing_ratios(args.ticker) 