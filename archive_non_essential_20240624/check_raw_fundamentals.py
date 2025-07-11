#!/usr/bin/env python3
"""
Check Raw Fundamental Data Completion
Counts tickers with raw fundamental data (not calculated ratios) that should be fetched from APIs.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def check_raw_fundamentals():
    db = DatabaseManager()
    
    # Define raw fundamental fields that should be fetched from APIs
    raw_fields = [
        'revenue', 'gross_profit', 'operating_income', 'net_income', 'ebitda',
        'eps_diluted', 'book_value_per_share',
        'total_assets', 'total_debt', 'total_equity', 'cash_and_equivalents',
        'operating_cash_flow', 'free_cash_flow', 'capex',
        'shares_outstanding', 'shares_float'
    ]
    
    # Count tickers with all raw fields present (not null)
    all_raw_fields = ' AND '.join([f"cf.{field} IS NOT NULL" for field in raw_fields])
    complete_query = f"""
        SELECT COUNT(DISTINCT cf.ticker) as complete_count
        FROM company_fundamentals cf
        WHERE {all_raw_fields}
    """
    complete_count = db.fetch_one(complete_query)[0]
    
    # Count tickers missing any raw field
    any_missing_raw = ' OR '.join([f"cf.{field} IS NULL" for field in raw_fields])
    missing_query = f"""
        SELECT COUNT(DISTINCT s.ticker) as missing_count
        FROM stocks s
        LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
        WHERE cf.ticker IS NULL OR {any_missing_raw}
    """
    missing_count = db.fetch_one(missing_query)[0]
    
    # Get total tickers
    total_query = "SELECT COUNT(DISTINCT ticker) FROM stocks"
    total_count = db.fetch_one(total_query)[0]
    
    print(f"Total tickers: {total_count}")
    print(f"Tickers with all raw fundamental data: {complete_count}")
    print(f"Tickers missing raw fundamental data: {missing_count}")
    print(f"Raw data completion rate: {complete_count / total_count * 100:.1f}%")
    
    # Check which specific fields are most commonly missing
    print(f"\nMissing field analysis:")
    print("-" * 40)
    for field in raw_fields:
        missing_field_query = f"""
            SELECT COUNT(DISTINCT s.ticker) as missing_count
            FROM stocks s
            LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.ticker IS NULL OR cf.{field} IS NULL
        """
        missing_field_count = db.fetch_one(missing_field_query)[0]
        percentage = (missing_field_count / total_count) * 100
        print(f"  {field}: {missing_field_count} missing ({percentage:.1f}%)")
    
    # Breakdown by market cap for missing raw data
    breakdown_query = f"""
        SELECT market_cap_category, COUNT(*) as count FROM (
            SELECT 
                s.ticker,
                CASE 
                    WHEN s.market_cap >= 10000000000 THEN 'Large Cap ($10B+)' 
                    WHEN s.market_cap >= 2000000000 THEN 'Mid Cap ($2B-$10B)'
                    WHEN s.market_cap >= 300000000 THEN 'Small Cap ($300M-$2B)'
                    WHEN s.market_cap > 0 THEN 'Micro Cap ($0-$300M)'
                    ELSE 'Unknown/No Market Cap'
                END as market_cap_category
            FROM stocks s
            LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.ticker IS NULL OR {any_missing_raw}
        ) sub
        GROUP BY market_cap_category
        ORDER BY count DESC
    """
    breakdown = db.execute_query(breakdown_query)
    print(f"\nBreakdown of tickers missing raw data by market cap:")
    for row in breakdown:
        print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    check_raw_fundamentals() 