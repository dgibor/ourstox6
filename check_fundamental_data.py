#!/usr/bin/env python3
import sys
sys.path.insert(0, 'daily_run')

from database import DatabaseManager

def check_fundamental_data():
    """Check what fundamental data is actually stored"""
    db = DatabaseManager()
    
    ticker = 'IBM'
    
    print(f"🔍 CHECKING FUNDAMENTAL DATA FOR {ticker}")
    print("=" * 60)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                ticker, last_updated, period_type,
                revenue, gross_profit, operating_income, net_income, ebitda,
                eps_diluted, book_value_per_share, total_assets, total_debt, total_equity,
                cash_and_equivalents, operating_cash_flow, free_cash_flow, capex,
                shares_outstanding, shares_float, data_source,
                cost_of_goods_sold, current_assets, current_liabilities
            FROM company_fundamentals 
            WHERE ticker = %s AND period_type = 'ttm' 
            ORDER BY last_updated DESC 
            LIMIT 1
        """, (ticker,))
        
        result = cursor.fetchone()
        
        if result:
            print(f"Ticker: {result[0]}")
            print(f"Last Updated: {result[1]}")
            print(f"Period Type: {result[2]}")
            print(f"Data Source: {result[19]}")
            print()
            
            # Core financial metrics
            print("💰 CORE FINANCIAL METRICS:")
            print(f"  • Revenue: ${result[3]:,.0f}" if result[3] else "  • Revenue: None")
            print(f"  • Gross Profit: ${result[4]:,.0f}" if result[4] else "  • Gross Profit: None")
            print(f"  • Operating Income: ${result[5]:,.0f}" if result[5] else "  • Operating Income: None")
            print(f"  • Net Income: ${result[6]:,.0f}" if result[6] else "  • Net Income: None")
            print(f"  • EBITDA: ${result[7]:,.0f}" if result[7] else "  • EBITDA: None")
            print()
            
            # Valuation metrics
            print("📊 VALUATION METRICS:")
            print(f"  • EPS Diluted: ${result[8]:.2f}" if result[8] else "  • EPS Diluted: None")
            print(f"  • Book Value Per Share: ${result[9]:.2f}" if result[9] else "  • Book Value Per Share: None")
            print()
            
            # Balance sheet
            print("🏦 BALANCE SHEET:")
            print(f"  • Total Assets: ${result[10]:,.0f}" if result[10] else "  • Total Assets: None")
            print(f"  • Total Debt: ${result[11]:,.0f}" if result[11] else "  • Total Debt: None")
            print(f"  • Total Equity: ${result[12]:,.0f}" if result[12] else "  • Total Equity: None")
            print(f"  • Cash & Equivalents: ${result[13]:,.0f}" if result[13] else "  • Cash & Equivalents: None")
            print()
            
            # Cash flow
            print("💸 CASH FLOW:")
            print(f"  • Operating Cash Flow: ${result[14]:,.0f}" if result[14] else "  • Operating Cash Flow: None")
            print(f"  • Free Cash Flow: ${result[15]:,.0f}" if result[15] else "  • Free Cash Flow: None")
            print(f"  • CapEx: ${result[16]:,.0f}" if result[16] else "  • CapEx: None")
            print()
            
            # Shares
            print("📈 SHARES:")
            print(f"  • Shares Outstanding: {result[17]:,}" if result[17] else "  • Shares Outstanding: None")
            print(f"  • Shares Float: {result[18]:,}" if result[18] else "  • Shares Float: None")
            print()
            
            # Additional fields
            print("📋 ADDITIONAL FIELDS:")
            print(f"  • Cost of Goods Sold: ${result[20]:,.0f}" if result[20] else "  • Cost of Goods Sold: None")
            print(f"  • Current Assets: ${result[21]:,}" if result[21] else "  • Current Assets: None")
            print(f"  • Current Liabilities: ${result[22]:,}" if result[22] else "  • Current Liabilities: None")
            print()
            
            # Missing critical fields analysis
            print("❌ MISSING CRITICAL FIELDS FOR RATIO CALCULATIONS:")
            missing_fields = []
            
            if not result[8]:  # eps_diluted
                missing_fields.append("eps_diluted (P/E, PEG ratios)")
            if not result[9]:  # book_value_per_share
                missing_fields.append("book_value_per_share (P/B ratio)")
            if not result[13]:  # cash_and_equivalents
                missing_fields.append("cash_and_equivalents (Quick ratio)")
            if not result[14]:  # operating_cash_flow
                missing_fields.append("operating_cash_flow (Interest coverage)")
            
            # Check if we have inventory, accounts_receivable, accounts_payable
            # These might be in a different table or not collected
            missing_fields.extend([
                "inventory (Inventory turnover, Current ratio)",
                "accounts_receivable (Receivables turnover)",
                "accounts_payable (Cash conversion cycle)"
            ])
            
            for field in missing_fields:
                print(f"  • {field}")
            
            print(f"\n📊 SUMMARY:")
            print(f"  • Fields with data: {sum(1 for r in result[3:] if r is not None)}/20")
            print(f"  • Missing critical fields: {len(missing_fields)}")
            print(f"  • This explains why only 7/27 ratios could be calculated")
            
        else:
            print(f"❌ No fundamental data found for {ticker}")

if __name__ == "__main__":
    check_fundamental_data() 