import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def check_stocks_table():
    """Verify stocks table has all information from batch files and provide data quality report"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print("🔍 Analyzing stocks table data quality...")
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cur.fetchone()[0]
        print(f"\n📊 Total stocks in database: {total_stocks}")
        
        # Check for duplicates
        cur.execute("""
            SELECT ticker, COUNT(*) as count
            FROM stocks 
            GROUP BY ticker 
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} tickers with duplicates:")
            for ticker, count in duplicates:
                print(f"   - {ticker}: {count} records")
        else:
            print("✅ No duplicate tickers found")
        
        # Data completeness analysis
        print(f"\n📋 Data Completeness Analysis:")
        
        completeness_checks = [
            ('company_name', 'Company Name'),
            ('industry', 'Industry'),
            ('sector', 'Sector'),
            ('market_cap_b', 'Market Cap'),
            ('description', 'Description'),
            ('business_model', 'Business Model'),
            ('products_services', 'Products/Services'),
            ('main_customers', 'Main Customers'),
            ('markets', 'Markets'),
            ('moat', 'Moat'),
            ('peer_a', 'Peer A'),
            ('peer_b', 'Peer B'),
            ('peer_c', 'Peer C')
        ]
        
        for column, display_name in completeness_checks:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({column}) as filled,
                    ROUND(COUNT({column}) * 100.0 / COUNT(*), 1) as percentage
                FROM stocks
            """)
            result = cur.fetchone()
            print(f"   - {display_name}: {result[1]}/{result[0]} ({result[2]}%)")
        
        # Sector distribution
        print(f"\n🏭 Sector Distribution:")
        cur.execute("""
            SELECT sector, COUNT(*) as count
            FROM stocks 
            WHERE sector IS NOT NULL AND sector != ''
            GROUP BY sector 
            ORDER BY count DESC
            LIMIT 10
        """)
        sectors = cur.fetchall()
        for sector, count in sectors:
            print(f"   - {sector}: {count} stocks")
        
        # Industry distribution
        print(f"\n🏢 Industry Distribution (Top 10):")
        cur.execute("""
            SELECT industry, COUNT(*) as count
            FROM stocks 
            WHERE industry IS NOT NULL AND industry != ''
            GROUP BY industry 
            ORDER BY count DESC
            LIMIT 10
        """)
        industries = cur.fetchall()
        for industry, count in industries:
            print(f"   - {industry}: {count} stocks")
        
        # Market cap distribution
        print(f"\n💰 Market Cap Distribution:")
        cur.execute("""
            SELECT cap_category, COUNT(*) as count FROM (
                SELECT 
                    CASE 
                        WHEN market_cap_b >= 100 THEN 'Large Cap (100B+)'
                        WHEN market_cap_b >= 10 THEN 'Mid Cap (10-100B)'
                        WHEN market_cap_b >= 1 THEN 'Small Cap (1-10B)'
                        WHEN market_cap_b > 0 THEN 'Micro Cap (<1B)'
                        ELSE 'Unknown'
                    END as cap_category
                FROM stocks
            ) sub
            GROUP BY cap_category
            ORDER BY 
                CASE cap_category
                    WHEN 'Large Cap (100B+)' THEN 1
                    WHEN 'Mid Cap (10-100B)' THEN 2
                    WHEN 'Small Cap (1-10B)' THEN 3
                    WHEN 'Micro Cap (<1B)' THEN 4
                    ELSE 5
                END
        """)
        market_caps = cur.fetchall()
        for category, count in market_caps:
            print(f"   - {category}: {count} stocks")
        
        # Sample records
        print(f"\n📝 Sample Records:")
        cur.execute("""
            SELECT ticker, company_name, sector, industry, market_cap_b
            FROM stocks 
            WHERE description IS NOT NULL AND description != ''
            ORDER BY market_cap_b DESC NULLS LAST
            LIMIT 5
        """)
        samples = cur.fetchall()
        for ticker, company, sector, industry, market_cap in samples:
            print(f"   - {ticker}: {company} ({sector}) - ${market_cap}B")
        
        # Check for records with all batch data fields
        print(f"\n✅ Records with Complete Batch Data:")
        cur.execute("""
            SELECT COUNT(*) as complete_records
            FROM stocks 
            WHERE description IS NOT NULL AND description != ''
                AND business_model IS NOT NULL AND business_model != ''
                AND products_services IS NOT NULL AND products_services != ''
                AND main_customers IS NOT NULL AND main_customers != ''
                AND markets IS NOT NULL AND markets != ''
                AND moat IS NOT NULL AND moat != ''
        """)
        complete_records = cur.fetchone()[0]
        print(f"   - {complete_records} stocks have all batch data fields filled")
        
        # Check for records missing batch data
        print(f"\n⚠️  Records Missing Batch Data:")
        cur.execute("""
            SELECT COUNT(*) as missing_records
            FROM stocks 
            WHERE description IS NULL OR description = ''
                OR business_model IS NULL OR business_model = ''
                OR products_services IS NULL OR products_services = ''
                OR main_customers IS NULL OR main_customers = ''
                OR markets IS NULL OR markets = ''
                OR moat IS NULL OR moat = ''
        """)
        missing_records = cur.fetchone()[0]
        print(f"   - {missing_records} stocks are missing some batch data fields")
        
        # Summary
        print(f"\n🎯 Summary:")
        print(f"   - Total stocks: {total_stocks}")
        print(f"   - Complete records: {complete_records}")
        print(f"   - Incomplete records: {missing_records}")
        print(f"   - Duplicate tickers: {len(duplicates)}")
        
        if complete_records > 0 and missing_records == 0:
            print("✅ All stocks have complete batch data!")
        elif complete_records > 0:
            print("⚠️  Some stocks are missing batch data fields")
        else:
            print("❌ No stocks have complete batch data")
        
    except Exception as e:
        print(f"❌ Error checking stocks table: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_stocks_table() 