#!/usr/bin/env python3
"""
Debug CRM enterprise value issue
"""

import sys
import os
import requests

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def debug_crm_enterprise_value():
    """Debug why enterprise_value is not set for CRM"""
    config = Config()
    api_key = config.get_api_key('fmp')
    
    ticker = "CRM"
    
    print(f"🔍 Debugging enterprise value for {ticker}")
    print("=" * 50)
    
    # 1. Check profile data
    print("1️⃣ Checking FMP Profile Data:")
    print("-" * 30)
    
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
    params = {'apikey': api_key}
    
    response = requests.get(profile_url, params=params, timeout=30)
    if response.status_code == 200:
        profile_data = response.json()
        
        # Handle case where profile_data is a list
        if isinstance(profile_data, list) and len(profile_data) > 0:
            profile_data = profile_data[0]
        
        if profile_data and isinstance(profile_data, dict):
            print(f"Market Cap: ${profile_data.get('mktCap', 0):,.0f}")
            print(f"Enterprise Value: ${profile_data.get('enterpriseValue', 0):,.0f}")
            print(f"Shares Outstanding: {profile_data.get('sharesOutstanding', 0):,.0f}")
            print(f"Current Price: ${profile_data.get('price', 0):.2f}")
            
            # Check if enterpriseValue is missing or 0
            enterprise_value = profile_data.get('enterpriseValue', 0)
            if enterprise_value == 0 or enterprise_value is None:
                print("⚠️  Enterprise Value is 0 or missing from FMP API")
                
                # Calculate it manually
                market_cap = profile_data.get('mktCap', 0)
                print(f"📊 Manual calculation:")
                print(f"  Market Cap: ${market_cap:,.0f}")
                
                # Get total debt from balance sheet
                balance_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}"
                balance_response = requests.get(balance_url, params={'apikey': api_key, 'limit': 1}, timeout=30)
                
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    if balance_data and len(balance_data) > 0:
                        latest_balance = balance_data[0]
                        total_debt = latest_balance.get('totalDebt', 0)
                        print(f"  Total Debt: ${total_debt:,.0f}")
                        
                        # Calculate enterprise value
                        calculated_ev = market_cap + total_debt
                        print(f"  Calculated EV: ${calculated_ev:,.0f}")
                        print(f"  Formula: Market Cap + Total Debt")
        else:
            print("❌ No profile data found")
    else:
        print(f"❌ Failed to fetch profile data: {response.status_code}")
    
    # 2. Check current database values
    print(f"\n2️⃣ Current Database Values:")
    print("-" * 30)
    
    from database import DatabaseManager
    db = DatabaseManager()
    
    query = """
    SELECT market_cap, enterprise_value, total_debt, shares_outstanding
    FROM stocks WHERE ticker = %s
    """
    
    result = db.fetch_one(query, (ticker,))
    if result:
        market_cap, enterprise_value, total_debt, shares_outstanding = result
        print(f"Market Cap: ${market_cap:,.0f}" if market_cap else "Market Cap: NULL")
        print(f"Enterprise Value: ${enterprise_value:,.0f}" if enterprise_value else "Enterprise Value: NULL")
        print(f"Total Debt: ${total_debt:,.0f}" if total_debt else "Total Debt: NULL")
        print(f"Shares Outstanding: {shares_outstanding:,.0f}" if shares_outstanding else "Shares Outstanding: NULL")
        
        # Calculate what EV should be
        if market_cap and total_debt:
            calculated_ev = market_cap + total_debt
            print(f"\n📊 Enterprise Value should be: ${calculated_ev:,.0f}")
            print(f"Formula: Market Cap + Total Debt")
            
            if enterprise_value == 0 or enterprise_value is None:
                print("❌ Enterprise Value is not set correctly in database")
            else:
                print("✅ Enterprise Value is set correctly")
    else:
        print("❌ No data found in database")

if __name__ == "__main__":
    debug_crm_enterprise_value() 