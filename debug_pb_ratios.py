import os
import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def debug_pb_ratios():
    """Debug P/B ratios for tickers with unusually high values"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 Debugging P/B Ratios")
        print("=" * 50)
        
        # Check tickers with high P/B ratios
        tickers_to_check = ['AAPL', 'NVDA']
        
        for ticker in tickers_to_check:
            print(f"\n📊 Analyzing {ticker}:")
            
            # Get current stock data
            cur.execute("""
                SELECT market_cap, shareholders_equity, book_value_per_share, 
                       shares_outstanding
                FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            
            stock_data = cur.fetchone()
            if stock_data:
                market_cap, shareholders_equity, book_value_per_share, shares_outstanding = stock_data
                
                print(f"  Market Cap: ${market_cap:,.0f}" if market_cap else "  Market Cap: NULL")
                print(f"  Shareholders Equity: ${shareholders_equity:,.0f}" if shareholders_equity else "  Shareholders Equity: NULL")
                print(f"  Book Value per Share: ${book_value_per_share:.2f}" if book_value_per_share else "  Book Value per Share: NULL")
                print(f"  Shares Outstanding: {shares_outstanding:,.0f}" if shares_outstanding else "  Shares Outstanding: NULL")
                
                # Calculate P/B ratio manually
                if market_cap and shareholders_equity and shareholders_equity > 0:
                    pb_ratio = market_cap / shareholders_equity
                    print(f"  Calculated P/B Ratio: {pb_ratio:.2f}")
                    
                    # Check if book value per share calculation makes sense
                    if book_value_per_share and shares_outstanding and shares_outstanding > 0:
                        calculated_bvps = shareholders_equity / shares_outstanding
                        print(f"  Calculated BVPS: ${calculated_bvps:.2f}")
                        print(f"  Stored BVPS: ${book_value_per_share:.2f}")
                        
                        if abs(calculated_bvps - book_value_per_share) > 0.01:
                            print(f"  ⚠️  BVPS mismatch! Calculated: ${calculated_bvps:.2f}, Stored: ${book_value_per_share:.2f}")
                
                # Check financial ratios table
                cur.execute("""
                    SELECT pb_ratio, calculation_date
                    FROM financial_ratios 
                    WHERE ticker = %s
                    ORDER BY calculation_date DESC
                    LIMIT 1
                """, (ticker,))
                
                ratio_data = cur.fetchone()
                if ratio_data:
                    stored_pb, calc_date = ratio_data
                    print(f"  Stored P/B Ratio: {stored_pb:.2f} (calculated on {calc_date})")
                
                # Check if shareholders equity seems reasonable
                if shareholders_equity:
                    market_cap_float = float(market_cap) if market_cap else 0
                    equity_float = float(shareholders_equity) if shareholders_equity else 0
                    
                    if equity_float < 1000000000:  # Less than $1B
                        print(f"  ⚠️  Shareholders equity seems low: ${equity_float:,.0f}")
                    elif equity_float > market_cap_float * 0.5:  # More than 50% of market cap
                        print(f"  ✅ Shareholders equity seems reasonable")
                    else:
                        print(f"  ℹ️  Shareholders equity: ${equity_float:,.0f} ({equity_float/market_cap_float*100:.1f}% of market cap)")
            else:
                print(f"  ❌ No stock data found for {ticker}")
        
        # Check for any data quality issues
        print(f"\n🔍 Data Quality Check:")
        cur.execute("""
            SELECT ticker, market_cap, shareholders_equity, 
                   CASE 
                       WHEN shareholders_equity > 0 THEN market_cap / shareholders_equity 
                       ELSE NULL 
                   END as pb_ratio
            FROM stocks 
            WHERE shareholders_equity IS NOT NULL 
            AND shareholders_equity > 0
            ORDER BY pb_ratio DESC
            LIMIT 10
        """)
        
        high_pb_tickers = cur.fetchall()
        print(f"  Top 10 highest P/B ratios:")
        for ticker, market_cap, equity, pb_ratio in high_pb_tickers:
            print(f"    {ticker}: {pb_ratio:.2f} (Market Cap: ${market_cap:,.0f}, Equity: ${equity:,.0f})")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error debugging P/B ratios: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main debug function"""
    print("🔍 P/B Ratio Debug Script")
    print("=" * 50)
    
    debug_pb_ratios()
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    main() 