#!/usr/bin/env python3
"""
Debug ratios retrieval from database
"""

import sys
sys.path.append('..')

from database import DatabaseManager

def debug_ratios():
    db = DatabaseManager()
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    
    print("=== DEBUGGING RATIOS RETRIEVAL ===")
    print("=" * 60)
    
    for ticker in tickers:
        try:
            print(f"\n📊 Debugging {ticker}...")
            
            # Check company_fundamentals table
            result = db.execute_query("""
                SELECT last_updated, price_to_earnings, price_to_book, return_on_equity, 
                       debt_to_equity_ratio, current_ratio, ev_to_ebitda, price_to_sales,
                       return_on_assets, gross_margin, operating_margin, net_margin,
                       revenue_growth_yoy, earnings_growth_yoy
                FROM company_fundamentals 
                WHERE ticker = %s
                ORDER BY last_updated DESC
                LIMIT 1
            """, (ticker,))
            
            if result:
                row = result[0]
                print(f"✅ Latest data from company_fundamentals:")
                print(f"   Last Updated: {row[0]}")
                print(f"   PE: {row[1]}")
                print(f"   PB: {row[2]}")
                print(f"   ROE: {row[3]}")
                print(f"   D/E: {row[4]}")
                print(f"   CR: {row[5]}")
                print(f"   EV/EBITDA: {row[6]}")
                print(f"   P/S: {row[7]}")
                print(f"   ROA: {row[8]}")
                print(f"   Gross Margin: {row[9]}")
                print(f"   Operating Margin: {row[10]}")
                print(f"   Net Margin: {row[11]}")
                print(f"   Revenue Growth: {row[12]}")
                print(f"   Earnings Growth: {row[13]}")
            else:
                print(f"❌ No data found in company_fundamentals for {ticker}")
                
        except Exception as e:
            print(f"❌ Error debugging {ticker}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Finished debugging ratios")

if __name__ == "__main__":
    debug_ratios() 