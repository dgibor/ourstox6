#!/usr/bin/env python3
"""
Batch fix scaling issues for stocks with progress tracking and error handling
"""

import sys
import os
from datetime import datetime
import time
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService

def get_tickers_batch(limit=None, offset=0):
    """Get a batch of tickers from the stocks table"""
    db = DatabaseManager()
    
    query = """
    SELECT ticker FROM stocks 
    WHERE ticker IS NOT NULL AND ticker != ''
    ORDER BY ticker
    """
    
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    
    results = db.execute_query(query)
    return [row[0] for row in results] if results else []

def batch_fix_stocks(batch_size=50, max_tickers=None):
    """Process stocks in batches with progress tracking"""
    print("🚀 BATCH FIX STOCKS - SCALING ISSUE RESOLUTION")
    print("=" * 70)
    
    # Initialize services
    db = DatabaseManager()
    fmp = FMPService()
    
    # Get total count
    total_query = "SELECT COUNT(*) FROM stocks WHERE ticker IS NOT NULL AND ticker != ''"
    total_count = db.fetch_one(total_query)[0]
    
    if max_tickers:
        total_count = min(total_count, max_tickers)
    
    print(f"📊 Total tickers to process: {total_count}")
    print(f"📦 Batch size: {batch_size}")
    
    # Process in batches
    successful = 0
    failed = 0
    processed = 0
    errors = []
    
    offset = 0
    
    while processed < total_count:
        # Get batch of tickers
        current_batch_size = min(batch_size, total_count - processed)
        tickers = get_tickers_batch(current_batch_size, offset)
        
        if not tickers:
            break
        
        print(f"\n📦 Processing batch {offset//batch_size + 1} ({len(tickers)} tickers)...")
        
        for i, ticker in enumerate(tickers, 1):
            current_progress = processed + i
            print(f"[{current_progress}/{total_count}] Processing {ticker}...")
            
            try:
                # Fetch financial statements
                financial_data = fmp.fetch_financial_statements(ticker)
                if not financial_data:
                    print(f"  ❌ No financial data for {ticker}")
                    failed += 1
                    errors.append(f"{ticker}: No financial data")
                    continue
                
                # Fetch key statistics
                key_stats = fmp.fetch_key_statistics(ticker)
                if not key_stats:
                    print(f"  ❌ No key stats for {ticker}")
                    failed += 1
                    errors.append(f"{ticker}: No key stats")
                    continue
                
                # Store the data
                success = fmp.store_fundamental_data(ticker, financial_data, key_stats)
                if success:
                    print(f"  ✅ Updated {ticker}")
                    successful += 1
                    
                    # Log the corrected values
                    income = financial_data.get('income_statement', {})
                    if income.get('revenue'):
                        print(f"    Revenue: ${income.get('revenue'):,.0f}")
                    if income.get('net_income'):
                        print(f"    Net Income: ${income.get('net_income'):,.0f}")
                else:
                    print(f"  ❌ Failed to store data for {ticker}")
                    failed += 1
                    errors.append(f"{ticker}: Failed to store data")
                    
            except Exception as e:
                print(f"  ❌ Error processing {ticker}: {e}")
                failed += 1
                errors.append(f"{ticker}: {str(e)}")
            
            # Rate limiting
            time.sleep(0.3)  # 300ms pause between requests
        
        processed += len(tickers)
        offset += batch_size
        
        # Progress update
        progress_pct = (processed / total_count) * 100
        print(f"\n📈 Progress: {processed}/{total_count} ({progress_pct:.1f}%)")
        print(f"✅ Successful: {successful}, ❌ Failed: {failed}")
        
        # Save progress to file
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'processed': processed,
            'total': total_count,
            'successful': successful,
            'failed': failed,
            'progress_pct': progress_pct,
            'errors': errors[-10:]  # Keep last 10 errors
        }
        
        with open('batch_progress.json', 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    # Final summary
    print(f"\n{'='*70}")
    print("📊 FINAL SUMMARY:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful/(successful+failed)*100):.1f}%")
    print(f"🎉 Batch processing completed!")
    
    if errors:
        print(f"\n❌ Last 10 errors:")
        for error in errors[-10:]:
            print(f"  {error}")
    
    # Close connections
    fmp.close()

def main():
    """Main function with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch fix scaling issues for stocks")
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size (default: 50)')
    parser.add_argument('--max-tickers', type=int, help='Maximum number of tickers to process')
    parser.add_argument('--test', action='store_true', help='Test mode - process only first 5 tickers')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 TEST MODE - Processing only first 5 tickers")
        batch_fix_stocks(batch_size=5, max_tickers=5)
    else:
        batch_fix_stocks(batch_size=args.batch_size, max_tickers=args.max_tickers)

if __name__ == "__main__":
    main() 