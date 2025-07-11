#!/usr/bin/env python3
"""
Check existing fundamental data for AAPL
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def check_aapl_existing():
    db = DatabaseManager()
    
    # Check existing records for AAPL
    query = """
    SELECT ticker, report_date, period_type, fiscal_year, fiscal_quarter,
           revenue, gross_profit, operating_income, net_income, ebitda,
           eps_diluted, book_value_per_share,
           total_assets, total_debt, total_equity, cash_and_equivalents,
           operating_cash_flow, free_cash_flow, capex,
           shares_outstanding, shares_float,
           price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda,
           return_on_equity, return_on_assets, debt_to_equity_ratio, current_ratio,
           gross_margin, operating_margin, net_margin,
           data_source, last_updated
    FROM company_fundamentals 
    WHERE ticker = 'AAPL'
    ORDER BY report_date DESC, last_updated DESC
    """
    
    try:
        result = db.execute_query(query)
        print(f"Found {len(result)} existing records for AAPL:")
        print("-" * 80)
        
        for i, row in enumerate(result):
            print(f"Record {i+1}:")
            print(f"  Date: {row[1]}, Period: {row[2]}, Fiscal Year: {row[3]}, Quarter: {row[4]}")
            print(f"  Revenue: ${row[5]:,.0f}" if row[5] else "  Revenue: NULL")
            print(f"  Net Income: ${row[9]:,.0f}" if row[9] else "  Net Income: NULL")
            print(f"  Total Assets: ${row[13]:,.0f}" if row[13] else "  Total Assets: NULL")
            print(f"  Shares Outstanding: {row[19]:,.0f}" if row[19] else "  Shares Outstanding: NULL")
            print(f"  EPS: {row[11]}" if row[11] else "  EPS: NULL")
            print(f"  Book Value Per Share: {row[12]}" if row[12] else "  Book Value Per Share: NULL")
            print(f"  Data Source: {row[31]}")
            print(f"  Last Updated: {row[32]}")
            print()
            
    except Exception as e:
        print(f"Error checking AAPL data: {e}")

if __name__ == "__main__":
    check_aapl_existing() 