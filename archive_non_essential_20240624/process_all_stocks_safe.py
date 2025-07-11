#!/usr/bin/env python3
"""
Safe batch processing for all stocks with comprehensive error handling
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
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('all_stocks_processing.log'),
        logging.StreamHandler()
    ]
)

def process_all_stocks_safe():
    """Process all stocks safely with comprehensive error handling"""
    
    print("🚀 STARTING SAFE BATCH PROCESSING FOR ALL STOCKS")
    print("=" * 60)
    
    # Initialize services
    db = DatabaseManager()
    fmp = FMPService()
    config = Config()
    
    # Get all tickers from database
    print("📋 Getting all tickers from database...")
    tickers_query = "SELECT ticker FROM stocks ORDER BY ticker"
    tickers_result = db.fetch_all(tickers_query)
    
    if not tickers_result:
        print("❌ No tickers found in database")
        return False
    
    tickers = [row[0] for row in tickers_result]
    total_tickers = len(tickers)
    
    print(f"✅ Found {total_tickers} tickers to process")
    
    # Statistics tracking
    stats = {
        'total': total_tickers,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # Rate limiting
    BATCH_SIZE = 10  # Process 10 at a time
    DELAY_BETWEEN_BATCHES = 2  # 2 seconds between batches
    DELAY_BETWEEN_REQUESTS = 0.5  # 0.5 seconds between individual requests
    
    print(f"⚙️  Configuration:")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Delay between batches: {DELAY_BETWEEN_BATCHES}s")
    print(f"   Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
    print()
    
    # Process in batches
    for batch_start in range(0, total_tickers, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_tickers)
        batch_tickers = tickers[batch_start:batch_end]
        
        print(f"🔄 Processing batch {batch_start//BATCH_SIZE + 1}/{(total_tickers + BATCH_SIZE - 1)//BATCH_SIZE}")
        print(f"   Tickers: {batch_start + 1}-{batch_end} of {total_tickers}")
        print(f"   Batch: {', '.join(batch_tickers)}")
        print()
        
        # Process each ticker in the batch
        for i, ticker in enumerate(batch_tickers):
            ticker_num = batch_start + i + 1
            
            print(f"  [{ticker_num}/{total_tickers}] Processing {ticker}...")
            
            try:
                # Check if we should skip this ticker
                skip_reason = should_skip_ticker(db, ticker)
                if skip_reason:
                    print(f"    ⏭️  Skipped: {skip_reason}")
                    stats['skipped'] += 1
                    continue
                
                # Process the ticker
                success = process_single_ticker(fmp, ticker)
                
                if success:
                    print(f"    ✅ Success")
                    stats['success'] += 1
                else:
                    print(f"    ❌ Failed")
                    stats['failed'] += 1
                    stats['errors'].append(f"{ticker}: Processing failed")
                
                # Rate limiting between requests
                if i < len(batch_tickers) - 1:  # Don't delay after last ticker in batch
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                error_msg = f"{ticker}: {str(e)}"
                print(f"    💥 Error: {error_msg}")
                stats['failed'] += 1
                stats['errors'].append(error_msg)
                logging.error(f"Error processing {ticker}: {e}")
                continue
        
        # Rate limiting between batches
        if batch_end < total_tickers:  # Don't delay after last batch
            print(f"⏳ Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)
        
        print()
    
    # Final summary
    print("=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"Total tickers: {stats['total']}")
    print(f"✅ Successful: {stats['success']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"⏭️  Skipped: {stats['skipped']}")
    print(f"Success rate: {(stats['success'] / stats['total'] * 100):.1f}%")
    
    if stats['errors']:
        print(f"\n❌ Errors encountered:")
        for error in stats['errors'][:10]:  # Show first 10 errors
            print(f"   • {error}")
        if len(stats['errors']) > 10:
            print(f"   ... and {len(stats['errors']) - 10} more errors")
    
    # Save summary to file
    summary_file = f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Processing Summary - {datetime.now()}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total tickers: {stats['total']}\n")
        f.write(f"Successful: {stats['success']}\n")
        f.write(f"Failed: {stats['failed']}\n")
        f.write(f"Skipped: {stats['skipped']}\n")
        f.write(f"Success rate: {(stats['success'] / stats['total'] * 100):.1f}%\n")
        if stats['errors']:
            f.write(f"\nErrors:\n")
            for error in stats['errors']:
                f.write(f"  • {error}\n")
    
    print(f"\n📄 Summary saved to: {summary_file}")
    print(f"📋 Full log saved to: all_stocks_processing.log")
    
    fmp.close()
    return stats['success'] > 0

def should_skip_ticker(db, ticker):
    """Check if we should skip processing this ticker"""
    
    # Check if ticker was recently updated (within last 24 hours)
    recent_query = """
    SELECT fundamentals_last_update 
    FROM stocks 
    WHERE ticker = %s AND fundamentals_last_update > NOW() - INTERVAL '24 hours'
    """
    recent_result = db.fetch_one(recent_query, (ticker,))
    if recent_result:
        return "Recently updated (within 24 hours)"
    
    # Check if ticker has basic data already
    basic_query = """
    SELECT revenue_ttm, net_income_ttm, market_cap 
    FROM stocks 
    WHERE ticker = %s
    """
    basic_result = db.fetch_one(basic_query, (ticker,))
    if basic_result and all(basic_result):
        return "Already has complete data"
    
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
    start_time = datetime.now()
    print(f"🕐 Started at: {start_time}")
    
    success = process_all_stocks_safe()
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n🕐 Completed at: {end_time}")
    print(f"⏱️  Total duration: {duration}")
    
    if success:
        print(f"\n🎉 Batch processing completed successfully!")
    else:
        print(f"\n⚠️  Batch processing completed with some issues") 