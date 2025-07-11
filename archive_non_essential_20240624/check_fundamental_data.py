#!/usr/bin/env python3
"""
Check fundamental data availability
"""

import sys
sys.path.append('..')

from database import DatabaseManager

def check_fundamental_data():
    db = DatabaseManager()
    
    # Check financial_ratios table
    print("=== FINANCIAL_RATIOS TABLE ===")
    result = db.execute_query("""
        SELECT ticker, calculation_date, pe_ratio, pb_ratio, roe, debt_to_equity, current_ratio 
        FROM financial_ratios 
        WHERE ticker IN ('NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM')
        ORDER BY ticker
    """)
    
    for row in result:
        print(f"{row[0]}: {row[1]} - PE:{row[2]}, PB:{row[3]}, ROE:{row[4]}, D/E:{row[5]}, CR:{row[6]}")
    
    # Check company_fundamentals table schema
    print("\n=== COMPANY_FUNDAMENTALS TABLE SCHEMA ===")
    try:
        result = db.execute_query("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_fundamentals' 
            ORDER BY ordinal_position
        """)
        
        print("Available columns:")
        for row in result:
            print(f"  {row[0]} ({row[1]})")
    except Exception as e:
        print(f"Error querying schema: {e}")
    
    # Now check company_fundamentals with ratio data
    print("\n=== COMPANY_FUNDAMENTALS TABLE DATA (with ratios) ===")
    try:
        result = db.execute_query("""
            SELECT ticker, last_updated, price_to_earnings, price_to_book, return_on_equity, 
                   debt_to_equity_ratio, current_ratio, gross_margin, operating_margin, net_margin
            FROM company_fundamentals 
            WHERE ticker IN ('NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM')
            ORDER BY ticker, last_updated DESC
        """)
        
        for row in result:
            print(f"{row[0]}: {row[1]} - PE:{row[2]}, PB:{row[3]}, ROE:{row[4]}, D/E:{row[5]}, CR:{row[6]}, GM:{row[7]}, OM:{row[8]}, NM:{row[9]}")
    except Exception as e:
        print(f"Error querying company_fundamentals: {e}")

if __name__ == "__main__":
    check_fundamental_data() 