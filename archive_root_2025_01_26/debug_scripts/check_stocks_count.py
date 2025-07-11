#!/usr/bin/env python3
"""
Quick script to check stocks table count
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_stocks():
    """Check stocks table count and show sample tickers"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM stocks")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total stocks in stocks table: {total_count}")
        
        # Get sample tickers
        cursor.execute("SELECT ticker FROM stocks LIMIT 10")
        sample_tickers = [row[0] for row in cursor.fetchall()]
        print(f"📋 Sample tickers: {sample_tickers}")
        
        # Check for duplicates
        cursor.execute("SELECT ticker, COUNT(*) FROM stocks GROUP BY ticker HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} duplicate tickers:")
            for ticker, count in duplicates[:5]:  # Show first 5
                print(f"   {ticker}: {count} times")
        else:
            print("✅ No duplicate tickers found")
        
        # Check company_fundamentals table
        cursor.execute("SELECT COUNT(*) FROM company_fundamentals")
        fundamentals_count = cursor.fetchone()[0]
        print(f"📊 Total records in company_fundamentals: {fundamentals_count}")
        
        # Check how many stocks have fundamentals
        cursor.execute("""
            SELECT COUNT(DISTINCT s.ticker) 
            FROM stocks s 
            INNER JOIN company_fundamentals cf ON s.ticker = cf.ticker
        """)
        stocks_with_fundamentals = cursor.fetchone()[0]
        print(f"📊 Stocks with fundamentals: {stocks_with_fundamentals}")
        
        # Check how many stocks are missing fundamentals
        cursor.execute("""
            SELECT COUNT(*) 
            FROM stocks s 
            LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
            WHERE cf.ticker IS NULL
        """)
        stocks_missing_fundamentals = cursor.fetchone()[0]
        print(f"📊 Stocks missing fundamentals: {stocks_missing_fundamentals}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_stocks() 