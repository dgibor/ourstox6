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

def test_stocks_batches_8_9():
    """Test the stocks table update results for batches 8 and 9"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print("🔍 Testing Stocks Table Update Results for Batches 8 and 9")
        print("=" * 70)
        
        # Check total count
        cur.execute("SELECT COUNT(*) FROM stocks")
        total_count = cur.fetchone()[0]
        print(f"📊 Total stocks in database: {total_count}")
        
        # Check for new columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'stocks'")
        columns = [row[0] for row in cur.fetchall()]
        expected_columns = [
            'description', 'business_model', 'products_services', 'main_customers', 'markets',
            'moat_1', 'moat_2', 'moat_3', 'moat_4', 'peer_a', 'peer_b', 'peer_c',
            'exchange', 'country', 'logo_path'
        ]
        missing_columns = [col for col in expected_columns if col not in columns]
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
        else:
            print("✅ All expected columns present.")
        
        # Check for duplicates
        cur.execute("SELECT ticker, COUNT(*) FROM stocks GROUP BY ticker HAVING COUNT(*) > 1")
        duplicates = cur.fetchall()
        if duplicates:
            print(f"❌ Duplicate tickers found: {duplicates}")
        else:
            print("✅ No duplicate tickers found.")
        
        # Check data completeness for key fields
        print("\n📋 Data Completeness Check:")
        fields_to_check = [
            'company_name', 'industry', 'sector', 'market_cap_b', 
            'description', 'business_model', 'products_services',
            'main_customers', 'markets', 'moat_1', 'moat_2', 'moat_3', 'moat_4',
            'peer_a', 'peer_b', 'peer_c', 'exchange', 'country', 'logo_path'
        ]
        
        for field in fields_to_check:
            if field == 'market_cap_b':
                # For numeric fields, only check for NULL
                cur.execute(f"SELECT COUNT(*) FROM stocks WHERE {field} IS NULL")
            else:
                # For text fields, check for NULL or empty string
                cur.execute(f"SELECT COUNT(*) FROM stocks WHERE {field} IS NULL OR {field} = ''")
            
            missing_count = cur.fetchone()[0]
            total_with_data = total_count - missing_count
            completeness = (total_with_data / total_count) * 100 if total_count > 0 else 0
            print(f"{field}: {missing_count} missing values ({completeness:.1f}% complete)")
        
        # Show a few sample records
        print("\nSample records:")
        cur.execute("SELECT ticker, company_name, industry, sector, market_cap_b, logo_path FROM stocks ORDER BY RANDOM() LIMIT 5")
        for row in cur.fetchall():
            print(row)
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_stocks_batches_8_9() 