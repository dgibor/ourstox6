#!/usr/bin/env python3
"""
Check daily_scores table for updated fundamental scores
"""

import sys
sys.path.append('..')

from database import DatabaseManager

def check_scores():
    db = DatabaseManager()
    
    print("=== DAILY_SCORES TABLE - FUNDAMENTAL SCORES ===")
    
    try:
        result = db.execute_query("""
            SELECT ticker, calculation_date, 
                   valuation_score, quality_score, growth_score, financial_health_score, management_score,
                   conservative_investor_score, garp_investor_score, deep_value_investor_score,
                   fundamental_data_quality_score, fundamental_calculation_status, fundamental_error_message
            FROM daily_scores 
            WHERE ticker IN ('NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM')
            ORDER BY ticker, calculation_date DESC
        """)
        
        if result:
            for row in result:
                print(f"{row[0]}: {row[1]}")
                print(f"   Valuation: {row[2]}, Quality: {row[3]}, Growth: {row[4]}, Health: {row[5]}, Management: {row[6]}")
                print(f"   Conservative: {row[7]}, GARP: {row[8]}, Deep Value: {row[9]}")
                print(f"   Data Quality: {row[10]}%, Status: {row[11]}")
                if row[12]:  # error message
                    print(f"   Error: {row[12]}")
                print()
        else:
            print("No scores found for target tickers")
            
    except Exception as e:
        print(f"Error querying daily_scores: {e}")

if __name__ == "__main__":
    check_scores() 