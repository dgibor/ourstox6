#!/usr/bin/env python3
"""
Check how many tickers are still missing fundamental data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def check_missing_tickers():
    """Check how many tickers are missing fundamental data"""
    db = DatabaseManager()
    
    # Query to get missing tickers
    query = """
    SELECT COUNT(DISTINCT s.ticker) as missing_count
    FROM stocks s
    LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
    WHERE cf.ticker IS NULL 
       OR cf.total_assets IS NULL 
       OR cf.total_equity IS NULL
       OR cf.total_debt IS NULL
       OR cf.free_cash_flow IS NULL
       OR cf.shares_outstanding IS NULL
       OR cf.total_assets = 0
       OR cf.total_equity = 0
       OR cf.shares_outstanding = 0
    """
    
    try:
        result = db.execute_query(query)
        missing_count = result[0][0] if result else 0
        
        print(f"Total tickers missing fundamental data: {missing_count}")
        
        # Get breakdown by market cap
        breakdown_query = """
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
            WHERE cf.ticker IS NULL 
               OR cf.total_assets IS NULL 
               OR cf.total_equity IS NULL
               OR cf.total_debt IS NULL
               OR cf.free_cash_flow IS NULL
               OR cf.shares_outstanding IS NULL
               OR cf.total_assets = 0
               OR cf.total_equity = 0
               OR cf.shares_outstanding = 0
        ) sub
        GROUP BY market_cap_category
        """
        
        breakdown_result = db.execute_query(breakdown_query)
        
        print("\nBreakdown by market cap:")
        print("-" * 40)
        # Order categories for display
        order = [
            'Large Cap ($10B+)',
            'Mid Cap ($2B-$10B)',
            'Small Cap ($300M-$2B)',
            'Micro Cap ($0-$300M)',
            'Unknown/No Market Cap'
        ]
        breakdown_dict = {cat: 0 for cat in order}
        for category, count in breakdown_result:
            breakdown_dict[category] = count
        for category in order:
            print(f"{category}: {breakdown_dict[category]} tickers")
        
        # Get total tickers count for comparison
        total_query = "SELECT COUNT(*) FROM stocks"
        total_result = db.execute_query(total_query)
        total_tickers = total_result[0][0] if total_result else 0
        
        print(f"\nTotal tickers in database: {total_tickers}")
        print(f"Tickers with complete data: {total_tickers - missing_count}")
        print(f"Completion rate: {((total_tickers - missing_count) / total_tickers * 100):.1f}%")
        
    except Exception as e:
        print(f"Error checking missing tickers: {e}")

if __name__ == "__main__":
    check_missing_tickers() 