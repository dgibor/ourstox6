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

def test_stocks_update():
    """Test the stocks table update results"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print("🔍 Testing Stocks Table Update Results")
        print("=" * 50)
        
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
        
        # Sample some updated records
        print(f"\n📝 Sample Updated Records:")
        cur.execute("""
            SELECT ticker, company_name, sector, industry, market_cap_b, 
                   LEFT(description, 100) as desc_preview
            FROM stocks 
            WHERE description IS NOT NULL AND description != ''
            ORDER BY market_cap_b DESC NULLS LAST
            LIMIT 5
        """)
        samples = cur.fetchall()
        for ticker, company, sector, industry, market_cap, desc in samples:
            print(f"   - {ticker}: {company}")
            print(f"     Sector: {sector}, Industry: {industry}")
            print(f"     Market Cap: {market_cap}B" if market_cap else "     Market Cap: N/A")
            print(f"     Description: {desc}...")
            print()
        
        # Check logo downloads
        logo_dir = '../pre_filled_stocks/logos'
        if os.path.exists(logo_dir):
            logo_files = [f for f in os.listdir(logo_dir) if f.endswith('.png')]
            print(f"🖼️  Logo files downloaded: {len(logo_files)}")
            print(f"   - Logo directory: {logo_dir}")
        else:
            print(f"⚠️  Logo directory not found: {logo_dir}")
        
        print("\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_stocks_update() 