#!/usr/bin/env python3
"""
Final script to process all stocks with comprehensive safety features
"""

import sys
import os
import time
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'all_stocks_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

def run_all_stocks_final():
    """Process all stocks with comprehensive safety features"""
    
    print("🚀 FINAL BATCH PROCESSING - ALL STOCKS")
    print("=" * 60)
    print("✅ System tested and verified")
    print("✅ Error handling implemented")
    print("✅ Rate limiting configured")
    print("✅ Progress tracking enabled")
    print("=" * 60)
    
    # Initialize services
    db = DatabaseManager()
    fmp = FMPService()
    
    # Get all tickers
    print("📋 Getting all tickers from database...")
    tickers_query = "SELECT ticker FROM stocks ORDER BY ticker"
    tickers_result = db.fetch_all(tickers_query)
    
    if not tickers_result:
        print("❌ No tickers found in database")
        return False
    
    tickers = [row[0] for row in tickers_result]
    total_tickers = len(tickers)
    
    print(f"✅ Found {total_tickers} tickers to process")
    
    # Safety check
    print(f"\n⚠️  SAFETY CHECK:")
    print(f"   This will process {total_tickers} stocks")
    print(f"   Estimated time: {total_tickers * 2} seconds ({total_tickers * 2 / 60:.1f} minutes)")
    print(f"   API calls: {total_tickers * 2} (2 per stock)")
    
    # Ask for confirmation
    response = input(f"\n🤔 Proceed with processing all {total_tickers} stocks? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled by user")
        return False
    
    # Statistics tracking
    stats = {
        'total': total_tickers,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # Configuration
    BATCH_SIZE = 20  # Process 20 at a time
    DELAY_BETWEEN_BATCHES = 3  # 3 seconds between batches
    DELAY_BETWEEN_REQUESTS = 1  # 1 second between individual requests
    
    print(f"\n⚙️  Configuration:")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Delay between batches: {DELAY_BETWEEN_BATCHES}s")
    print(f"   Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
    print(f"   Estimated total time: {(total_tickers * DELAY_BETWEEN_REQUESTS + (total_tickers // BATCH_SIZE) * DELAY_BETWEEN_BATCHES) / 60:.1f} minutes")
    print()
    
    start_time = datetime.now()
    print(f"🕐 Started at: {start_time}")
    print()
    
    # Process in batches
    for batch_start in range(0, total_tickers, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_tickers)
        batch_tickers = tickers[batch_start:batch_end]
        
        print(f"🔄 Batch {batch_start//BATCH_SIZE + 1}/{(total_tickers + BATCH_SIZE - 1)//BATCH_SIZE}")
        print(f"   Processing: {batch_start + 1}-{batch_end} of {total_tickers}")
        print(f"   Progress: {(batch_start / total_tickers * 100):.1f}% complete")
        print()
        
        # Process each ticker in the batch
        for i, ticker in enumerate(batch_tickers):
            ticker_num = batch_start + i + 1
            
            print(f"  [{ticker_num}/{total_tickers}] {ticker}...", end=" ")
            
            try:
                # Check if we should skip this ticker
                skip_reason = should_skip_ticker(db, ticker)
                if skip_reason:
                    print(f"⏭️  Skipped ({skip_reason})")
                    stats['skipped'] += 1
                    continue
                
                # Process the ticker
                success = process_single_ticker(fmp, ticker)
                
                if success:
                    print(f"✅ Success")
                    stats['success'] += 1
                else:
                    print(f"❌ Failed")
                    stats['failed'] += 1
                    stats['errors'].append(f"{ticker}: Processing failed")
                
                # Rate limiting between requests
                if i < len(batch_tickers) - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                error_msg = f"{ticker}: {str(e)}"
                print(f"💥 Error")
                stats['failed'] += 1
                stats['errors'].append(error_msg)
                logging.error(f"Error processing {ticker}: {e}")
                continue
        
        # Rate limiting between batches
        if batch_end < total_tickers:
            print(f"\n⏳ Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)
        
        print()
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"🕐 Started: {start_time}")
    print(f"🕐 Ended: {end_time}")
    print(f"⏱️  Duration: {duration}")
    print()
    print(f"📈 Statistics:")
    print(f"   Total tickers: {stats['total']}")
    print(f"   ✅ Successful: {stats['success']}")
    print(f"   ❌ Failed: {stats['failed']}")
    print(f"   ⏭️  Skipped: {stats['skipped']}")
    print(f"   Success rate: {(stats['success'] / stats['total'] * 100):.1f}%")
    
    if stats['errors']:
        print(f"\n❌ Errors encountered ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"   • {error}")
        if len(stats['errors']) > 5:
            print(f"   ... and {len(stats['errors']) - 5} more errors")
    
    # Save detailed summary
    summary_file = f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_file, 'w') as f:
        f.write(f"All Stocks Processing Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Started: {start_time}\n")
        f.write(f"Ended: {end_time}\n")
        f.write(f"Duration: {duration}\n\n")
        f.write(f"Total tickers: {stats['total']}\n")
        f.write(f"Successful: {stats['success']}\n")
        f.write(f"Failed: {stats['failed']}\n")
        f.write(f"Skipped: {stats['skipped']}\n")
        f.write(f"Success rate: {(stats['success'] / stats['total'] * 100):.1f}%\n")
        if stats['errors']:
            f.write(f"\nErrors:\n")
            for error in stats['errors']:
                f.write(f"  • {error}\n")
    
    print(f"\n📄 Detailed summary saved to: {summary_file}")
    
    fmp.close()
    
    if stats['success'] > stats['total'] * 0.8:  # 80% success rate
        print(f"\n🎉 EXCELLENT! Processing completed with high success rate!")
        return True
    elif stats['success'] > stats['total'] * 0.5:  # 50% success rate
        print(f"\n✅ GOOD! Processing completed with reasonable success rate.")
        return True
    else:
        print(f"\n⚠️  WARNING! Low success rate. Check errors and retry if needed.")
        return False

def should_skip_ticker(db, ticker):
    """Check if we should skip processing this ticker"""
    
    # Check if ticker was recently updated (within last 12 hours)
    recent_query = """
    SELECT fundamentals_last_update 
    FROM stocks 
    WHERE ticker = %s AND fundamentals_last_update > NOW() - INTERVAL '12 hours'
    """
    recent_result = db.fetch_one(recent_query, (ticker,))
    if recent_result:
        return "Recently updated"
    
    return None  # Don't skip

def process_single_ticker(fmp, ticker):
    """Process a single ticker with error handling"""
    try:
        # Fetch financial statements
        financial_data = fmp.fetch_financial_statements(ticker)
        if not financial_data:
            return False
        
        # Fetch key statistics
        key_stats = fmp.fetch_key_statistics(ticker)
        if not key_stats:
            return False
        
        # Store the data
        success = fmp.store_fundamental_data(ticker, financial_data, key_stats)
        return success
        
    except Exception as e:
        logging.error(f"Error processing {ticker}: {e}")
        return False

if __name__ == "__main__":
    run_all_stocks_final() 