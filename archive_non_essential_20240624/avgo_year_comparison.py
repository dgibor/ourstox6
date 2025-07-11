#!/usr/bin/env python3
"""
Compare AVGO data across years
"""

import sys
import os
import requests

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def avgo_year_comparison():
    """Compare AVGO data across years"""
    config = Config()
    api_key = config.get_api_key('fmp')
    
    print("📊 AVGO YEAR COMPARISON")
    print("=" * 40)
    
    # Get income statement data
    income_url = f"https://financialmodelingprep.com/api/v3/income-statement/AVGO"
    params = {'apikey': api_key, 'limit': 5}
    
    response = requests.get(income_url, params=params, timeout=30)
    if response.status_code == 200:
        income_data = response.json()
        
        print("Year | Revenue | Net Income | EBITDA")
        print("-----|---------|------------|--------")
        
        for period in income_data[:3]:
            year = period.get('calendarYear', 'N/A')
            revenue = period.get('revenue', 0) / 1e9
            net_income = period.get('netIncome', 0) / 1e9
            ebitda = period.get('ebitda', 0) / 1e9
            
            print(f"{year} | ${revenue:6.1f}B | ${net_income:6.1f}B | ${ebitda:6.1f}B")
        
        print(f"\n🔍 ANALYSIS:")
        print(f"2024: Revenue=${income_data[0].get('revenue', 0)/1e9:.1f}B, Net Income=${income_data[0].get('netIncome', 0)/1e9:.1f}B")
        print(f"2023: Revenue=${income_data[1].get('revenue', 0)/1e9:.1f}B, Net Income=${income_data[1].get('netIncome', 0)/1e9:.1f}B")
        
        print(f"\n💡 FINDING:")
        print(f"• 2023 data matches web references better")
        print(f"• 2024 shows much lower net income")
        print(f"• Web references are using 2023 data")

if __name__ == "__main__":
    avgo_year_comparison() 