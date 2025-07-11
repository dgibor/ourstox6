#!/usr/bin/env python3
"""
Check company_fundamentals table structure and data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def check_fundamentals_structure():
    """Check company_fundamentals table structure and data"""
    
    print("🔍 CHECKING COMPANY_FUNDAMENTALS TABLE")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Check table structure
    print("📋 TABLE STRUCTURE:")
    structure_query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'company_fundamentals'
    ORDER BY ordinal_position
    """
    structure_result = db.execute_query(structure_query)
    
    if structure_result:
        print("   Column | Type | Nullable")
        print("   -------|------|---------")
        for column, data_type, nullable in structure_result:
            print(f"   {column:7} | {data_type:15} | {nullable}")
    else:
        print("   No structure found")
    
    # Check sample data
    print(f"\n📊 SAMPLE DATA:")
    sample_query = """
    SELECT ticker, revenue, net_income, ebitda, market_cap, enterprise_value, last_updated
    FROM company_fundamentals 
    ORDER BY last_updated DESC 
    LIMIT 5
    """
    sample_data = db.execute_query(sample_query)
    
    if sample_data:
        print("   Ticker | Revenue | Net Income | EBITDA | Market Cap | Enterprise Value | Last Updated")
        print("   -------|---------|------------|--------|------------|------------------|-------------")
        for row in sample_data:
            ticker, revenue, net_income, ebitda, market_cap, enterprise_value, last_updated = row
            print(f"   {ticker:6} | {revenue:7} | {net_income:10} | {ebitda:6} | {market_cap:10} | {enterprise_value:16} | {last_updated}")
    else:
        print("   No data found")
    
    # Check data counts
    print(f"\n📈 DATA COUNTS:")
    count_query = "SELECT COUNT(*) FROM company_fundamentals"
    count_result = db.fetch_one(count_query)
    total_count = count_result[0] if count_result else 0
    
    revenue_count_query = "SELECT COUNT(*) FROM company_fundamentals WHERE revenue IS NOT NULL"
    revenue_count_result = db.fetch_one(revenue_count_query)
    revenue_count = revenue_count_result[0] if revenue_count_result else 0
    
    market_cap_count_query = "SELECT COUNT(*) FROM company_fundamentals WHERE market_cap IS NOT NULL"
    market_cap_count_result = db.fetch_one(market_cap_count_query)
    market_cap_count = market_cap_count_result[0] if market_cap_count_result else 0
    
    print(f"   Total records: {total_count}")
    print(f"   With revenue: {revenue_count}")
    print(f"   With market cap: {market_cap_count}")
    
    # Check for duplicates
    print(f"\n🔍 DUPLICATE CHECK:")
    duplicate_query = """
    SELECT ticker, COUNT(*) as count
    FROM company_fundamentals
    GROUP BY ticker
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 5
    """
    duplicate_result = db.execute_query(duplicate_query)
    
    if duplicate_result:
        print("   Ticker | Count")
        print("   -------|------")
        for ticker, count in duplicate_result:
            print(f"   {ticker:6} | {count:5}")
    else:
        print("   No duplicates found")

if __name__ == "__main__":
    check_fundamentals_structure() 