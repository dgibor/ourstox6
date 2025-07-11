#!/usr/bin/env python3
"""
Fix stocks missing shares outstanding data
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService

def fix_missing_shares_outstanding():
    """Fix stocks missing shares outstanding data"""
    
    print("🔧 FIXING MISSING SHARES OUTSTANDING")
    print("=" * 50)
    
    db = DatabaseManager()
    fmp = FMPService()
    
    # Get stocks missing shares outstanding
    missing_query = """
    SELECT DISTINCT cf.ticker 
    FROM company_fundamentals cf
    WHERE cf.shares_outstanding IS NULL
    ORDER BY cf.revenue DESC NULLS LAST
    """
    
    missing_stocks = db.execute_query(missing_query)
    tickers = [row[0] for row in missing_stocks] if missing_stocks else []
    
    print(f"📋 Found {len(tickers)} stocks missing shares outstanding")
    
    if not tickers:
        print("✅ All stocks have shares outstanding data!")
        return
    
    # Process each ticker
    success_count = 0
    for i, ticker in enumerate(tickers):
        print(f"  [{i+1}/{len(tickers)}] {ticker}...", end=" ")
        
        try:
            # Fetch key statistics specifically for shares outstanding
            key_stats = fmp.fetch_key_statistics(ticker)
            
            if key_stats and key_stats.get('market_data', {}).get('shares_outstanding'):
                shares_outstanding = key_stats['market_data']['shares_outstanding']
                
                # Update the database
                update_query = """
                UPDATE company_fundamentals 
                SET shares_outstanding = %s, last_updated = %s
                WHERE ticker = %s
                """
                
                db.execute_update(update_query, (shares_outstanding, datetime.now(), ticker))
                print(f"✅ Updated: {shares_outstanding:,}")
                success_count += 1
            else:
                print(f"❌ No shares data found")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"💥 Error: {str(e)}")
            continue
    
    print(f"\n📊 SUMMARY:")
    print(f"   Processed: {len(tickers)}")
    print(f"   Success: {success_count}")
    print(f"   Success rate: {(success_count/len(tickers)*100):.1f}%")
    
    fmp.close()

if __name__ == "__main__":
    fix_missing_shares_outstanding() 