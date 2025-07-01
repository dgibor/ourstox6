import psycopg2
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

def remove_duplicates():
    """Remove duplicate records from the stocks table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        print("🔍 Checking for duplicate tickers...")
        
        # Find duplicate tickers
        cur.execute("""
            SELECT ticker, COUNT(*) as count
            FROM stocks 
            GROUP BY ticker 
            HAVING COUNT(*) > 1
            ORDER BY count DESC, ticker
        """)
        
        duplicates = cur.fetchall()
        
        if not duplicates:
            print("✅ No duplicate tickers found!")
            return
        
        print(f"⚠️  Found {len(duplicates)} tickers with duplicates:")
        for ticker, count in duplicates:
            print(f"   - {ticker}: {count} records")
        
        total_removed = 0
        
        for ticker, count in duplicates:
            print(f"\n🔄 Processing duplicates for {ticker}...")
            
            # Get all records for this ticker
            cur.execute("""
                SELECT id, company_name, industry, sector, market_cap_b, 
                       description, business_model, products_services, 
                       main_customers, markets, moat, peer_a, peer_b, peer_c,
                       last_updated,
                       CASE 
                           WHEN description IS NOT NULL AND description != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN business_model IS NOT NULL AND business_model != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN products_services IS NOT NULL AND products_services != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN main_customers IS NOT NULL AND main_customers != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN markets IS NOT NULL AND markets != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN moat IS NOT NULL AND moat != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN peer_a IS NOT NULL AND peer_a != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN peer_b IS NOT NULL AND peer_b != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN peer_c IS NOT NULL AND peer_c != '' THEN 1 ELSE 0 END +
                       CASE 
                           WHEN market_cap_b IS NOT NULL THEN 1 ELSE 0 END
                       as completeness_score
                FROM stocks 
                WHERE ticker = %s
                ORDER BY completeness_score DESC, last_updated DESC NULLS LAST, id ASC
            """, (ticker,))
            
            records = cur.fetchall()
            
            # Keep the first record (most complete and recent)
            keep_id = records[0][0]
            keep_completeness = records[0][-1]
            
            print(f"   Keeping record ID {keep_id} (completeness score: {keep_completeness})")
            
            # Delete other records
            for record in records[1:]:
                delete_id = record[0]
                delete_completeness = record[-1]
                print(f"   Deleting record ID {delete_id} (completeness score: {delete_completeness})")
                
                cur.execute("DELETE FROM stocks WHERE id = %s", (delete_id,))
                total_removed += 1
        
        conn.commit()
        print(f"\n🎉 Duplicate removal completed!")
        print(f"   📊 Total duplicate records removed: {total_removed}")
        
        # Verify no duplicates remain
        cur.execute("""
            SELECT ticker, COUNT(*) as count
            FROM stocks 
            GROUP BY ticker 
            HAVING COUNT(*) > 1
        """)
        
        remaining_duplicates = cur.fetchall()
        if not remaining_duplicates:
            print("✅ Verification: No duplicate tickers remain!")
        else:
            print(f"⚠️  Warning: {len(remaining_duplicates)} tickers still have duplicates")
            for ticker, count in remaining_duplicates:
                print(f"   - {ticker}: {count} records")
        
        # Show final count
        cur.execute("SELECT COUNT(*) FROM stocks")
        final_count = cur.fetchone()[0]
        print(f"   📊 Final stocks count: {final_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error removing duplicates: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    remove_duplicates() 