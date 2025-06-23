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

def format_number(value):
    if value is None:
        return "NULL"
    return f"{value:,.0f}"

def check_aapl_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get stock data
    cur.execute("""
        SELECT ticker, market_cap, shares_outstanding, diluted_eps_ttm, 
               book_value_per_share, revenue_ttm, net_income_ttm, 
               total_assets, total_debt, shareholders_equity, 
               current_assets, current_liabilities, cash_and_equivalents,
               operating_income, ebitda_ttm
        FROM stocks 
        WHERE ticker = 'AAPL'
    """)
    
    stock_data = cur.fetchone()
    if stock_data:
        print("AAPL Stock Data:")
        print(f"Ticker: {stock_data[0]}")
        print(f"Market Cap: {format_number(stock_data[1])}")
        print(f"Shares Outstanding: {format_number(stock_data[2])}")
        print(f"Diluted EPS TTM: {stock_data[3]}")
        print(f"Book Value Per Share: {stock_data[4]}")
        print(f"Revenue TTM: {format_number(stock_data[5])}")
        print(f"Net Income TTM: {format_number(stock_data[6])}")
        print(f"Total Assets: {format_number(stock_data[7])}")
        print(f"Total Debt: {format_number(stock_data[8])}")
        print(f"Shareholders Equity: {format_number(stock_data[9])}")
        print(f"Current Assets: {format_number(stock_data[10])}")
        print(f"Current Liabilities: {format_number(stock_data[11])}")
        print(f"Cash and Equivalents: {format_number(stock_data[12])}")
        print(f"Operating Income: {format_number(stock_data[13])}")
        print(f"EBITDA TTM: {format_number(stock_data[14])}")
        
        # Get latest price
        cur.execute("""
            SELECT close FROM daily_charts 
            WHERE ticker = 'AAPL' 
            ORDER BY date DESC 
            LIMIT 1
        """)
        
        price_data = cur.fetchone()
        if price_data:
            current_price = price_data[0] / 100.0  # Convert from integer format
            print(f"Current Price: ${current_price:.2f}")
            
            # Calculate ratios manually
            print("\nManual Calculations:")
            
            # P/E Ratio
            if stock_data[3] and stock_data[3] > 0:
                pe_ratio = current_price / stock_data[3]
                print(f"P/E Ratio: {pe_ratio:.2f}")
                print(f"P/E Ratio (capped): {min(pe_ratio, 999):.2f}")
            else:
                print("P/E Ratio: N/A - No EPS data")
            
            # P/B Ratio
            if stock_data[9] and stock_data[9] > 0:
                pb_ratio = stock_data[1] / stock_data[9]
                print(f"P/B Ratio: {pb_ratio:.2f}")
            else:
                print("P/B Ratio: N/A - No book value data")
            
            # P/S Ratio
            if stock_data[5] and stock_data[5] > 0:
                ps_ratio = stock_data[1] / stock_data[5]
                print(f"P/S Ratio: {ps_ratio:.2f}")
                print(f"P/S Ratio (capped): {min(ps_ratio, 50):.2f}")
            else:
                print("P/S Ratio: N/A - No revenue data")
            
            # EV/EBITDA
            if stock_data[14] and stock_data[14] > 0:
                total_debt = stock_data[8] or 0
                cash = stock_data[12] or 0
                enterprise_value = stock_data[1] + total_debt - cash
                ev_ebitda = enterprise_value / stock_data[14]
                print(f"Enterprise Value: {enterprise_value:,.0f}")
                print(f"EV/EBITDA: {ev_ebitda:.2f}")
            else:
                print("EV/EBITDA: N/A - No EBITDA data")
            
            # Graham Number
            if stock_data[3] and stock_data[3] > 0 and stock_data[4] and stock_data[4] > 0:
                import math
                graham_number = math.sqrt(15 * stock_data[3] * stock_data[4])
                print(f"Graham Number: {graham_number:.2f}")
            else:
                print("Graham Number: N/A - Requires positive EPS and book value")
    
    conn.close()

if __name__ == "__main__":
    check_aapl_data() 