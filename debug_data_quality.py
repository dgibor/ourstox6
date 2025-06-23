import os
import psycopg2
from dotenv import load_dotenv
import sys

# Add the daily_run directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def test_fixed_calculator():
    """Test the fixed financial ratios calculator"""
    print("🧮 Testing fixed financial ratios calculator...")
    
    from daily_run.financial_ratios_calculator import FinancialRatiosCalculator
    calculator = FinancialRatiosCalculator()
    
    # Test AAPL specifically
    print("\n📊 Testing AAPL ratios with fixed calculator:")
    stock_data = calculator.get_stock_data('AAPL')
    if stock_data:
        print(f"  Current Price: ${stock_data['current_price']:.2f}")
        print(f"  Diluted EPS TTM: {stock_data['diluted_eps_ttm']}")
        print(f"  Book Value per Share: {stock_data['book_value_per_share']}")
        print(f"  Market Cap: ${stock_data['market_cap']:,.0f}")
        print(f"  Revenue TTM: ${stock_data['revenue_ttm']:,.0f}")
        
        # Calculate P/E manually to verify
        if stock_data['current_price'] and stock_data['diluted_eps_ttm']:
            manual_pe = stock_data['current_price'] / float(stock_data['diluted_eps_ttm'])
            print(f"  Manual P/E calculation: {manual_pe:.2f}")
        
        # Test the calculator
        ratios = calculator.calculate_all_ratios('AAPL')
        if ratios:
            print(f"\n  Calculated ratios:")
            for ratio_name, ratio_data in ratios.items():
                value = ratio_data.get('value')
                flag = ratio_data.get('quality_flag')
                if value is not None:
                    print(f"    {ratio_name}: {value:.2f} ({flag})")
                else:
                    print(f"    {ratio_name}: {flag}")
    
    calculator.close()

def check_data_sources():
    """Check what data sources are providing what data"""
    print("\n🔍 Checking data sources for AAPL...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Check company_fundamentals table for AAPL
    cur.execute("""
        SELECT data_source, report_date, revenue, net_income, ebitda, eps_diluted, book_value_per_share
        FROM company_fundamentals 
        WHERE ticker = 'AAPL' 
        ORDER BY report_date DESC, last_updated DESC
        LIMIT 5
    """)
    
    fundamental_records = cur.fetchall()
    if fundamental_records:
        print("📋 Company fundamentals records:")
        for i, record in enumerate(fundamental_records, 1):
            print(f"  Record {i}:")
            print(f"    Data Source: {record[0]}")
            print(f"    Report Date: {record[1]}")
            print(f"    Revenue: ${record[2]:,.0f}" if record[2] else "    Revenue: None")
            print(f"    Net Income: ${record[3]:,.0f}" if record[3] else "    Net Income: None")
            print(f"    EBITDA: ${record[4]:,.0f}" if record[4] else "    EBITDA: None")
            print(f"    EPS Diluted: {record[5]}" if record[5] else "    EPS Diluted: None")
            print(f"    Book Value per Share: {record[6]}" if record[6] else "    Book Value per Share: None")
    else:
        print("❌ No company fundamentals records found")
    
    # Check stocks table for AAPL
    cur.execute("""
        SELECT revenue_ttm, net_income_ttm, ebitda_ttm, diluted_eps_ttm, book_value_per_share, fundamentals_last_update
        FROM stocks 
        WHERE ticker = 'AAPL'
    """)
    
    stock_record = cur.fetchone()
    if stock_record:
        print(f"\n📊 Stocks table data:")
        print(f"  Revenue TTM: ${stock_record[0]:,.0f}" if stock_record[0] else "  Revenue TTM: None")
        print(f"  Net Income TTM: ${stock_record[1]:,.0f}" if stock_record[1] else "  Net Income TTM: None")
        print(f"  EBITDA TTM: ${stock_record[2]:,.0f}" if stock_record[2] else "  EBITDA TTM: None")
        print(f"  Diluted EPS TTM: {stock_record[3]}" if stock_record[3] else "  Diluted EPS TTM: None")
        print(f"  Book Value per Share: {stock_record[4]}" if stock_record[4] else "  Book Value per Share: None")
        print(f"  Last Updated: {stock_record[5]}")
    
    cur.close()
    conn.close()

def main():
    print("🔧 Debugging data quality issues...")
    
    # Test the fixed calculator
    test_fixed_calculator()
    
    # Check data sources
    check_data_sources()

if __name__ == "__main__":
    main()
