#!/usr/bin/env python3
import sys
sys.path.insert(0, 'daily_run')

from database import DatabaseManager

def check_database():
    db = DatabaseManager()
    
    # Check table structure
    print("🔍 CHECKING DATABASE STRUCTURE")
    print("=" * 50)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_fundamentals' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print("Company Fundamentals Table Columns:")
        for col_name, data_type in columns:
            print(f"  • {col_name} ({data_type})")
    
    print("\n" + "=" * 50)
    print("🔍 CHECKING IBM DATA")
    print("=" * 50)
    
    # Check IBM data
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT ticker, last_updated, 
                   price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda, peg_ratio,
                   return_on_equity, return_on_assets, return_on_invested_capital,
                   gross_margin, operating_margin, net_margin,
                   debt_to_equity_ratio, current_ratio, quick_ratio,
                   interest_coverage, altman_z_score,
                   asset_turnover, inventory_turnover, receivables_turnover,
                   revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
                   fcf_to_net_income, cash_conversion_cycle,
                   market_cap, enterprise_value, graham_number
            FROM company_fundamentals 
            WHERE ticker = 'IBM' AND period_type = 'ttm' 
            ORDER BY last_updated DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if result:
            print("IBM Database Results:")
            print(f"Ticker: {result[0]}")
            print(f"Last Updated: {result[1]}")
            print("\nValuation Ratios:")
            print(f"  • P/E Ratio: {result[2]}")
            print(f"  • P/B Ratio: {result[3]}")
            print(f"  • P/S Ratio: {result[4]}")
            print(f"  • EV/EBITDA: {result[5]}")
            print(f"  • PEG Ratio: {result[6]}")
            print("\nProfitability Ratios:")
            print(f"  • ROE: {result[7]}")
            print(f"  • ROA: {result[8]}")
            print(f"  • ROIC: {result[9]}")
            print(f"  • Gross Margin: {result[10]}")
            print(f"  • Operating Margin: {result[11]}")
            print(f"  • Net Margin: {result[12]}")
            print("\nFinancial Health:")
            print(f"  • Debt/Equity: {result[13]}")
            print(f"  • Current Ratio: {result[14]}")
            print(f"  • Quick Ratio: {result[15]}")
            print(f"  • Interest Coverage: {result[16]}")
            print(f"  • Altman Z-Score: {result[17]}")
            print("\nEfficiency Ratios:")
            print(f"  • Asset Turnover: {result[18]}")
            print(f"  • Inventory Turnover: {result[19]}")
            print(f"  • Receivables Turnover: {result[20]}")
            print("\nGrowth Ratios:")
            print(f"  • Revenue Growth YoY: {result[21]}")
            print(f"  • Earnings Growth YoY: {result[22]}")
            print(f"  • FCF Growth YoY: {result[23]}")
            print("\nCash Flow:")
            print(f"  • FCF to Net Income: {result[24]}")
            print(f"  • Cash Conversion Cycle: {result[25]}")
            print("\nValuation Metrics:")
            print(f"  • Market Cap: {result[26]}")
            print(f"  • Enterprise Value: {result[27]}")
            print(f"  • Graham Number: {result[28]}")
        else:
            print("No IBM data found in company_fundamentals table")

if __name__ == "__main__":
    check_database() 