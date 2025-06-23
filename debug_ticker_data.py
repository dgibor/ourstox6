import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def debug_ticker_data(ticker):
    """Debug fundamental data for a specific ticker"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print(f"\n🔍 Debugging {ticker} fundamental data:")
    print("=" * 50)
    
    # Check stocks table
    cur.execute("""
        SELECT ticker, company_name, market_cap, shares_outstanding, 
               diluted_eps_ttm, book_value_per_share, revenue_ttm, 
               net_income_ttm, total_assets, total_debt, shareholders_equity,
               current_assets, current_liabilities, cash_and_equivalents,
               operating_income, ebitda_ttm, fundamentals_last_update
        FROM stocks 
        WHERE ticker = %s
    """, (ticker,))
    
    stock_data = cur.fetchone()
    if stock_data:
        print("📊 Stocks table data:")
        print(f"  Ticker: {stock_data[0]}")
        print(f"  Company: {stock_data[1]}")
        print(f"  Market Cap: {stock_data[2]}")
        print(f"  Shares Outstanding: {stock_data[3]}")
        print(f"  Diluted EPS TTM: {stock_data[4]}")
        print(f"  Book Value per Share: {stock_data[5]}")
        print(f"  Revenue TTM: {stock_data[6]}")
        print(f"  Net Income TTM: {stock_data[7]}")
        print(f"  Total Assets: {stock_data[8]}")
        print(f"  Total Debt: {stock_data[9]}")
        print(f"  Shareholders Equity: {stock_data[10]}")
        print(f"  Current Assets: {stock_data[11]}")
        print(f"  Current Liabilities: {stock_data[12]}")
        print(f"  Cash & Equivalents: {stock_data[13]}")
        print(f"  Operating Income: {stock_data[14]}")
        print(f"  EBITDA TTM: {stock_data[15]}")
        print(f"  Last Updated: {stock_data[16]}")
    else:
        print("❌ No data found in stocks table")
    
    # Check latest price
    cur.execute("""
        SELECT close, date FROM daily_charts 
        WHERE ticker = %s 
        ORDER BY date DESC 
        LIMIT 1
    """, (ticker,))
    
    price_data = cur.fetchone()
    if price_data:
        print(f"\n💰 Latest price data:")
        print(f"  Close: ${price_data[0]/100:.2f} (stored as {price_data[0]} cents)")
        print(f"  Date: {price_data[1]}")
    else:
        print("❌ No price data found")
    
    # Check financial ratios
    cur.execute("""
        SELECT calculation_date, pe_ratio, pb_ratio, ps_ratio, ev_ebitda, graham_number
        FROM financial_ratios 
        WHERE ticker = %s 
        ORDER BY calculation_date DESC 
        LIMIT 1
    """, (ticker,))
    
    ratio_data = cur.fetchone()
    if ratio_data:
        print(f"\n📈 Latest calculated ratios:")
        print(f"  Calculation Date: {ratio_data[0]}")
        print(f"  P/E Ratio: {ratio_data[1]}")
        print(f"  P/B Ratio: {ratio_data[2]}")
        print(f"  P/S Ratio: {ratio_data[3]}")
        print(f"  EV/EBITDA: {ratio_data[4]}")
        print(f"  Graham Number: {ratio_data[5]}")
    else:
        print("❌ No ratio data found")
    
    # Check company_fundamentals table
    cur.execute("""
        SELECT report_date, period_type, revenue, net_income, ebitda, eps_diluted, book_value_per_share
        FROM company_fundamentals 
        WHERE ticker = %s 
        ORDER BY report_date DESC 
        LIMIT 3
    """, (ticker,))
    
    fundamental_data = cur.fetchall()
    if fundamental_data:
        print(f"\n📋 Company fundamentals table (last 3 records):")
        for i, row in enumerate(fundamental_data, 1):
            print(f"  Record {i}:")
            print(f"    Report Date: {row[0]}")
            print(f"    Period Type: {row[1]}")
            print(f"    Revenue: {row[2]}")
            print(f"    Net Income: {row[3]}")
            print(f"    EBITDA: {row[4]}")
            print(f"    EPS Diluted: {row[5]}")
            print(f"    Book Value per Share: {row[6]}")
    else:
        print("❌ No company fundamentals data found")
    
    cur.close()
    conn.close()

def main():
    tickers = ['AMZN', 'AVGO', 'NVDA', 'AAPL', 'XOM']
    
    for ticker in tickers:
        debug_ticker_data(ticker)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main() 