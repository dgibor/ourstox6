#!/usr/bin/env python3
"""
Check Fundamental Data Completion
Counts tickers with all required fundamental data and those still missing, with a breakdown by market cap.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def check_fundamental_completion():
    db = DatabaseManager()
    
    # Define required fields
    required_fields = [
        'revenue', 'gross_profit', 'operating_income', 'net_income', 'ebitda',
        'eps_diluted', 'book_value_per_share',
        'total_assets', 'total_debt', 'total_equity', 'cash_and_equivalents',
        'operating_cash_flow', 'free_cash_flow', 'capex',
        'shares_outstanding', 'shares_float',
        'price_to_earnings', 'price_to_book', 'price_to_sales', 'ev_to_ebitda',
        'return_on_equity', 'return_on_assets', 'debt_to_equity_ratio', 'current_ratio',
        'gross_margin', 'operating_margin', 'net_margin', 'peg_ratio',
        'return_on_invested_capital', 'quick_ratio', 'interest_coverage', 'altman_z_score',
        'asset_turnover', 'inventory_turnover', 'receivables_turnover',
        'revenue_growth_yoy', 'earnings_growth_yoy', 'fcf_growth_yoy', 'fcf_to_net_income',
        'cash_conversion_cycle', 'market_cap', 'enterprise_value', 'graham_number'
    ]
    
    # Count tickers with all required fields present (not null)
    all_fields = ' AND '.join([f"cf.{field} IS NOT NULL" for field in required_fields])
    complete_query = f"""
        SELECT COUNT(DISTINCT cf.ticker) as complete_count
        FROM company_fundamentals cf
        WHERE {all_fields}
    """
    complete_count = db.fetch_one(complete_query)[0]
    
    # Count tickers missing any required field
    any_missing = ' OR '.join([f"cf.{field} IS NULL" for field in required_fields])
    missing_query = f"""
        SELECT COUNT(DISTINCT s.ticker) as missing_count
        FROM stocks s
        LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
        WHERE {any_missing}
    """
    missing_count = db.fetch_one(missing_query)[0]
    
    # Get total tickers
    total_query = "SELECT COUNT(DISTINCT ticker) FROM stocks"
    total_count = db.fetch_one(total_query)[0]
    
    print(f"Total tickers: {total_count}")
    print(f"Tickers with all required data: {complete_count}")
    print(f"Tickers missing data: {missing_count}")
    print(f"Completion rate: {complete_count / total_count * 100:.1f}%")
    
    # Breakdown by market cap for missing
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
            WHERE {any_missing}
        ) sub
        GROUP BY market_cap_category
        ORDER BY count DESC
    """
    breakdown = db.execute_query(breakdown_query)
    print("\nBreakdown of tickers missing data by market cap:")
    for row in breakdown:
        print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    check_fundamental_completion() 