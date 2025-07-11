#!/usr/bin/env python3
"""
Automatically fix scaling issues for all stocks in the database
"""

import sys
import os
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService

def get_all_tickers():
    """Get all tickers from the stocks table"""
    db = DatabaseManager()
    
    query = """
    SELECT ticker FROM stocks 
    WHERE ticker IS NOT NULL AND ticker != ''
    ORDER BY ticker
    """
    
    results = db.fetch_all(query)
    return [row[0] for row in results] if results else []

def auto_fix_stock(ticker, fmp_service, db):
    """Automatically fix scaling for a single stock"""
    print(f"🔧 Processing {ticker}...")
    
    try:
        # Fetch financial statements
        financial_data = fmp_service.fetch_financial_statements(ticker)
        if not financial_data:
            print(f"❌ No financial data for {ticker}")
            return False
        
        # Fetch key statistics
        key_stats = fmp_service.fetch_key_statistics(ticker)
        if not key_stats:
            print(f"❌ No key stats for {ticker}")
            return False
        
        # Store the data (this will automatically use the corrected TTM logic)
        success = fmp_service.store_fundamental_data(ticker, financial_data, key_stats)
        if success:
            print(f"✅ Successfully updated {ticker}")
            
            # Log the corrected values
            income = financial_data.get('income_statement', {})
            if income.get('revenue'):
                print(f"  Revenue: ${income.get('revenue'):,.0f}")
            if income.get('net_income'):
                print(f"  Net Income: ${income.get('net_income'):,.0f}")
            
            return True
        else:
            print(f"❌ Failed to store data for {ticker}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        return False

def main():
    """Automatically fix all stocks"""
    print("🚀 AUTO-FIX ALL STOCKS - SCALING ISSUE RESOLUTION")
    print("=" * 70)
    
    # Initialize services
    db = DatabaseManager()
    fmp = FMPService()
    
    # Get all tickers
    print("📋 Getting all tickers from database...")
    tickers = get_all_tickers()
    print(f"Found {len(tickers)} tickers to process")
    
    if not tickers:
        print("❌ No tickers found in database")
        return
    
    # Process each ticker
    successful = 0
    failed = 0
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
        
        success = auto_fix_stock(ticker, fmp, db)
        if success:
            successful += 1
        else:
            failed += 1
        
        # Rate limiting - pause between requests
        if i < len(tickers):  # Don't pause after the last one
            time.sleep(0.5)  # 500ms pause between requests
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 PROCESSING SUMMARY:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful/(successful+failed)*100):.1f}%")
    print(f"🎉 All stocks processed with corrected scaling logic!")
    
    # Close connections
    fmp.close()

if __name__ == "__main__":
    main() 