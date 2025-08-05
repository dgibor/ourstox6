import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def check_fundamental_data():
    """Check what fundamental data is available in the database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'PG', 'PFE', 'CSCO']
        
        print("Checking fundamental data availability...")
        print("=" * 60)
        
        for ticker in test_tickers:
            print(f"\n📊 {ticker}:")
            
            # Check company_fundamentals
            cursor.execute("""
                SELECT COUNT(*) as count FROM company_fundamentals WHERE ticker = %s
            """, (ticker,))
            result = cursor.fetchone()
            fundamental_count = result['count']
            
            # Check financial_ratios
            cursor.execute("""
                SELECT COUNT(*) as count FROM financial_ratios WHERE ticker = %s
            """, (ticker,))
            result = cursor.fetchone()
            ratios_count = result['count']
            
            # Check stocks table
            cursor.execute("""
                SELECT sector, market_cap_b FROM stocks WHERE ticker = %s
            """, (ticker,))
            result = cursor.fetchone()
            
            print(f"  Company Fundamentals: {fundamental_count} records")
            print(f"  Financial Ratios: {ratios_count} records")
            
            if result:
                print(f"  Sector: {result['sector']}")
                print(f"  Market Cap: {result['market_cap_b']}B")
            else:
                print(f"  Sector: Not found in stocks table")
                print(f"  Market Cap: Not found")
            
            # Get sample data if available
            if fundamental_count > 0:
                cursor.execute("""
                    SELECT 
                        price_to_earnings, price_to_book, return_on_equity, 
                        return_on_assets, debt_to_equity_ratio, current_ratio,
                        ev_to_ebitda, gross_margin, operating_margin, net_margin,
                        revenue_growth_yoy, earnings_growth_yoy
                    FROM company_fundamentals 
                    WHERE ticker = %s 
                    ORDER BY report_date DESC 
                    LIMIT 1
                """, (ticker,))
                
                data = cursor.fetchone()
                if data:
                    print(f"  Sample Data:")
                    for key, value in data.items():
                        if value is not None:
                            print(f"    {key}: {value}")
                        else:
                            print(f"    {key}: NULL")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_fundamental_data() 