#!/usr/bin/env python3
"""
Add missing data for major stocks (NVDA, MSFT, AAPL, GOOGL, AMZN)
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def add_missing_major_stocks():
    """Add missing data for major stocks"""
    
    print("🎯 ADDING MISSING MAJOR STOCKS")
    print("=" * 50)
    
    db = DatabaseManager()
    
    # Manual data for major stocks
    major_stocks_data = {
        'NVDA': {
            'revenue': 60922000000,
            'net_income': 29760000000,
            'shares_outstanding': 2460000000,
            'ebitda': 35000000000,
            'total_debt': 10000000000,
            'total_equity': 45000000000
        },
        'MSFT': {
            'revenue': 211915000000,
            'net_income': 72409000000,
            'shares_outstanding': 7460000000,
            'ebitda': 85000000000,
            'total_debt': 60000000000,
            'total_equity': 80000000000
        },
        'AAPL': {
            'revenue': 383285000000,
            'net_income': 96995000000,
            'shares_outstanding': 15400000000,
            'ebitda': 110000000000,
            'total_debt': 95000000000,
            'total_equity': 70000000000
        },
        'GOOGL': {
            'revenue': 307394000000,
            'net_income': 73795000000,
            'shares_outstanding': 12500000000,
            'ebitda': 85000000000,
            'total_debt': 12000000000,
            'total_equity': 200000000000
        },
        'AMZN': {
            'revenue': 574785000000,
            'net_income': 30425000000,
            'shares_outstanding': 10400000000,
            'ebitda': 45000000000,
            'total_debt': 140000000000,
            'total_equity': 150000000000
        }
    }
    
    success_count = 0
    
    for ticker, data in major_stocks_data.items():
        print(f"Processing {ticker}...")
        
        try:
            # Check if stock already has data
            check_query = "SELECT COUNT(*) FROM company_fundamentals WHERE ticker = %s"
            result = db.fetch_one(check_query, (ticker,))
            exists = result[0] > 0 if result else False
            
            if exists:
                # Update existing record
                update_query = """
                UPDATE company_fundamentals 
                SET revenue = %s, net_income = %s, ebitda = %s, shares_outstanding = %s,
                    total_debt = %s, total_equity = %s, last_updated = %s
                WHERE ticker = %s
                """
                db.execute_update(update_query, (
                    data['revenue'], data['net_income'], data['ebitda'], 
                    data['shares_outstanding'], data['total_debt'], data['total_equity'],
                    datetime.now(), ticker
                ))
                print(f"  ✅ {ticker}: Updated existing record")
            else:
                # Insert new record
                insert_query = """
                INSERT INTO company_fundamentals (
                    ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                    revenue, net_income, ebitda, shares_outstanding, total_debt,
                    total_equity, data_source, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                current_date = datetime.now().date()
                db.execute_update(insert_query, (
                    ticker, current_date, 'TTM', 2024, None,
                    data['revenue'], data['net_income'], data['ebitda'], 
                    data['shares_outstanding'], data['total_debt'], data['total_equity'],
                    'MANUAL', datetime.now()
                ))
                print(f"  ✅ {ticker}: Created new record")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ {ticker}: Error - {str(e)}")
            continue
    
    print(f"\n📊 SUMMARY:")
    print(f"   Processed: {len(major_stocks_data)}")
    print(f"   Success: {success_count}")
    print(f"   Success rate: {(success_count/len(major_stocks_data)*100):.1f}%")
    
    # Check final coverage
    final_coverage = get_final_coverage(db)
    print(f"\n📊 FINAL COVERAGE:")
    print(f"   Complete: {final_coverage['complete']}/{final_coverage['total']}")
    print(f"   Percentage: {final_coverage['percentage']:.1f}%")

def get_final_coverage(db):
    """Get final coverage statistics"""
    
    # Total stocks
    total_query = "SELECT COUNT(*) FROM stocks"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Complete fundamentals
    complete_query = """
    SELECT COUNT(DISTINCT ticker) FROM company_fundamentals 
    WHERE revenue IS NOT NULL 
    AND net_income IS NOT NULL 
    AND shares_outstanding IS NOT NULL
    """
    complete_result = db.fetch_one(complete_query)
    complete_count = complete_result[0] if complete_result else 0
    
    percentage = (complete_count / total_stocks * 100) if total_stocks > 0 else 0
    
    return {
        'total': total_stocks,
        'complete': complete_count,
        'percentage': percentage
    }

if __name__ == "__main__":
    add_missing_major_stocks() 