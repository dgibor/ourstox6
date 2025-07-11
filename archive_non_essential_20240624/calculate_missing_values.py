#!/usr/bin/env python3
"""
Calculate missing shares_outstanding and eps_diluted for AAPL
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def calculate_missing_values():
    """Calculate missing values for AAPL"""
    db = DatabaseManager()
    
    ticker = "AAPL"
    
    print(f"🧮 Calculating missing values for {ticker}")
    print("=" * 50)
    
    # Get current AAPL data
    query = """
    SELECT 
        revenue, net_income, total_equity, book_value_per_share
    FROM company_fundamentals 
    WHERE ticker = 'AAPL'
    ORDER BY last_updated DESC
    LIMIT 1
    """
    
    result = db.fetch_one(query)
    
    if not result:
        print(f"❌ No data found for {ticker}")
        return
    
    revenue, net_income, total_equity, book_value_per_share = result
    
    # Convert to float for calculations
    total_equity = float(total_equity) if total_equity is not None else None
    book_value_per_share = float(book_value_per_share) if book_value_per_share is not None else None
    revenue = float(revenue) if revenue is not None else None
    net_income = float(net_income) if net_income is not None else None
    
    print(f"📊 Current data:")
    print(f"  Revenue: ${revenue:,.0f}")
    print(f"  Net Income: ${net_income:,.0f}")
    print(f"  Total Equity: ${total_equity:,.0f}")
    print(f"  Book Value Per Share: ${book_value_per_share:.2f}")
    
    # Get current price from daily_charts
    price_query = "SELECT close FROM daily_charts WHERE ticker = 'AAPL' ORDER BY date DESC LIMIT 1"
    price_result = db.fetch_one(price_query)
    if price_result:
        current_price = price_result[0] / 100.0  # Convert from cents
        print(f"  Current Price (from daily_charts): ${current_price:.2f}")
    else:
        print(f"❌ No current price found")
        return
    
    # Calculate market cap from current price and shares
    # We'll estimate shares from total equity and book value per share
    if total_equity and book_value_per_share:
        estimated_shares = total_equity / book_value_per_share
        estimated_market_cap = current_price * estimated_shares
        print(f"  Estimated Market Cap: ${estimated_market_cap:,.0f}")
    else:
        print(f"❌ Cannot estimate market cap - missing required data")
        return
    
    # Calculate shares outstanding
    if estimated_market_cap and current_price:
        calculated_shares = estimated_market_cap / current_price
        print(f"\n📈 Calculated Shares Outstanding: {calculated_shares:,.0f}")
    else:
        print(f"\n❌ Cannot calculate shares outstanding - missing required data")
        return
    
    # Calculate EPS
    if net_income and calculated_shares:
        calculated_eps = net_income / calculated_shares
        print(f"📈 Calculated EPS: ${calculated_eps:.2f}")
    else:
        print(f"❌ Cannot calculate EPS - missing required data")
        return
    
    # Calculate PE ratio
    if current_price and calculated_eps:
        calculated_pe = current_price / calculated_eps
        print(f"📈 Calculated PE Ratio: {calculated_pe:.2f}")
    else:
        print(f"❌ Cannot calculate PE ratio - missing required data")
        return
    
    # Update the database with calculated values
    print(f"\n💾 Updating database with calculated values...")
    try:
        update_query = """
        UPDATE company_fundamentals 
        SET shares_outstanding = %s, eps_diluted = %s, price_to_earnings = %s
        WHERE ticker = 'AAPL' AND report_date = (
            SELECT report_date FROM company_fundamentals 
            WHERE ticker = 'AAPL' 
            ORDER BY last_updated DESC 
            LIMIT 1
        )
        """
        
        affected_rows = db.execute_update(update_query, (calculated_shares, calculated_eps, calculated_pe))
        print(f"✅ Updated {affected_rows} record(s)")
        
        # Verify the update
        verify_query = """
        SELECT shares_outstanding, eps_diluted, price_to_earnings
        FROM company_fundamentals 
        WHERE ticker = 'AAPL'
        ORDER BY last_updated DESC
        LIMIT 1
        """
        
        verify_result = db.fetch_one(verify_query)
        if verify_result:
            shares, eps, pe = verify_result
            print(f"\n✅ Verification:")
            print(f"  Shares Outstanding: {shares:,.0f}")
            print(f"  EPS: ${eps:.2f}")
            print(f"  PE Ratio: {pe:.2f}")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")

if __name__ == "__main__":
    calculate_missing_values() 