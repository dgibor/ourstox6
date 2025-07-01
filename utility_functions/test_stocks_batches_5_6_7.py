import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def test_stocks_batches_5_6_7():
    """Test the stocks table update results for batches 5, 6, and 7"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print("🔍 Testing Stocks Table Update Results for Batches 5, 6, and 7")
        print("=" * 70)
        
        # Check total count
        cur.execute("SELECT COUNT(*) FROM stocks")
        total_count = cur.fetchone()[0]
        print(f"📊 Total stocks in database: {total_count}")
        
        # Check for new columns
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            AND column_name IN ('market_cap_b', 'description', 'business_model', 'moat_1', 'moat_2', 'moat_3', 'moat_4')
            ORDER BY column_name
        """)
        new_columns = cur.fetchall()
        print(f"\n📋 New columns added: {len(new_columns)}")
        for col_name, col_type in new_columns:
            print(f"   - {col_name}: {col_type}")
        
        # Check data completeness
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(description) as with_description,
                COUNT(business_model) as with_business_model,
                COUNT(market_cap_b) as with_market_cap,
                COUNT(moat_1) as with_moat_1,
                COUNT(peer_a) as with_peer_a
            FROM stocks
        """)
        completeness = cur.fetchone()
        print(f"\n📈 Data Completeness:")
        print(f"   - Total records: {completeness[0]}")
        print(f"   - With description: {completeness[1]} ({completeness[1]/completeness[0]*100:.1f}%)")
        print(f"   - With business model: {completeness[2]} ({completeness[2]/completeness[0]*100:.1f}%)")
        print(f"   - With market cap: {completeness[3]} ({completeness[3]/completeness[0]*100:.1f}%)")
        print(f"   - With moat 1: {completeness[4]} ({completeness[4]/completeness[0]*100:.1f}%)")
        print(f"   - With peer A: {completeness[5]} ({completeness[5]/completeness[0]*100:.1f}%)")
        
        # Check for duplicates
        cur.execute("""
            SELECT ticker, COUNT(*) as count
            FROM stocks 
            GROUP BY ticker 
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        if duplicates:
            print(f"\n⚠️  Found {len(duplicates)} duplicate tickers:")
            for ticker, count in duplicates:
                print(f"   - {ticker}: {count} records")
        else:
            print(f"\n✅ No duplicate tickers found")
        
        # Sample records from batches 5, 6, 7
        print(f"\n📋 Sample Records from Batches 5, 6, 7:")
        
        # Get some sample tickers from the new batches
        sample_tickers = ['CS', 'CSX', 'CTLT', 'CTSH', 'CTVA', 'CVS', 'CVX', 'CWK', 'CWT', 'CZR']
        
        for ticker in sample_tickers:
            cur.execute("""
                SELECT ticker, company_name, sector, industry, market_cap_b, 
                       description, business_model, moat_1, peer_a
                FROM stocks WHERE ticker = %s
            """, (ticker,))
            result = cur.fetchone()
            if result:
                ticker, company_name, sector, industry, market_cap_b, description, business_model, moat_1, peer_a = result
                print(f"\n   {ticker} - {company_name}")
                print(f"      Sector: {sector}")
                print(f"      Industry: {industry}")
                print(f"      Market Cap: {market_cap_b}B")
                print(f"      Business Model: {business_model}")
                print(f"      Moat 1: {moat_1}")
                print(f"      Peer A: {peer_a}")
                print(f"      Description: {description[:100]}..." if description else "      Description: None")
        
        # Check logo count
        cur.execute("SELECT COUNT(*) FROM stocks WHERE logo_url IS NOT NULL AND logo_url != ''")
        logo_count = cur.fetchone()[0]
        print(f"\n🖼️  Logos available: {logo_count} ({logo_count/total_count*100:.1f}%)")
        
        # Check recent updates
        cur.execute("""
            SELECT COUNT(*) FROM stocks 
            WHERE last_updated >= CURRENT_DATE - INTERVAL '1 day'
        """)
        recent_updates = cur.fetchone()[0]
        print(f"🔄 Recent updates (last 24h): {recent_updates}")
        
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_stocks_batches_5_6_7() 