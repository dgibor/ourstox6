#!/usr/bin/env python3
"""
Fill all companies with complete data in company_fundamentals table
Repeat until all stocks have full data
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
        logging.FileHandler(f'fill_all_fundamentals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

def fill_all_company_fundamentals():
    """Fill all companies with complete data in company_fundamentals table"""
    
    print("🚀 FILLING ALL COMPANY FUNDAMENTALS")
    print("=" * 60)
    print("✅ Processing all stocks in stocks table")
    print("✅ Filling company_fundamentals table")
    print("✅ Repeating until all stocks have full data")
    print("=" * 60)
    
    # Initialize services
    db = DatabaseManager()
    fmp = FMPService()
    
    iteration = 1
    total_processed = 0
    total_success = 0
    
    while True:
        print(f"\n🔄 ITERATION {iteration}")
        print("=" * 40)
        
        # Get stocks that need processing
        stocks_to_process = get_stocks_needing_processing(db)
        
        if not stocks_to_process:
            print("✅ All stocks have complete data!")
            break
        
        print(f"📋 Found {len(stocks_to_process)} stocks needing processing")
        
        # Process this batch
        batch_stats = process_stocks_batch(fmp, db, stocks_to_process, iteration)
        
        total_processed += batch_stats['processed']
        total_success += batch_stats['success']
        
        print(f"\n📊 ITERATION {iteration} SUMMARY:")
        print(f"   Processed: {batch_stats['processed']}")
        print(f"   Success: {batch_stats['success']}")
        print(f"   Failed: {batch_stats['failed']}")
        print(f"   Success rate: {(batch_stats['success'] / batch_stats['processed'] * 100):.1f}%")
        
        # Check if we should continue
        if batch_stats['success'] == 0:
            print("⚠️  No successful updates in this iteration. Stopping.")
            break
        
        # Wait before next iteration
        print(f"\n⏳ Waiting 30 seconds before next iteration...")
        time.sleep(30)
        
        iteration += 1
        
        # Safety check - don't run forever
        if iteration > 10:
            print("⚠️  Reached maximum iterations (10). Stopping.")
            break
    
    # Final summary
    print(f"\n🎉 FINAL SUMMARY")
    print("=" * 60)
    print(f"Total iterations: {iteration - 1}")
    print(f"Total processed: {total_processed}")
    print(f"Total success: {total_success}")
    print(f"Overall success rate: {(total_success / total_processed * 100):.1f}%" if total_processed > 0 else "N/A")
    
    # Show final coverage
    final_coverage = get_final_coverage(db)
    print(f"\n📊 FINAL COVERAGE:")
    print(f"   Total stocks: {final_coverage['total']}")
    print(f"   With fundamentals: {final_coverage['with_fundamentals']}")
    print(f"   Coverage: {(final_coverage['with_fundamentals'] / final_coverage['total'] * 100):.1f}%")
    
    fmp.close()
    return total_success > 0

def get_stocks_needing_processing(db):
    """Get stocks that need processing (missing fundamentals or incomplete data)"""
    
    # Get stocks that don't have complete fundamentals data
    query = """
    SELECT s.ticker 
    FROM stocks s
    LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
    WHERE cf.ticker IS NULL 
       OR cf.revenue IS NULL 
       OR cf.net_income IS NULL 
       OR cf.market_cap IS NULL
       OR cf.last_updated IS NULL
       OR cf.last_updated < NOW() - INTERVAL '24 hours'
    ORDER BY s.market_cap DESC NULLS LAST, s.ticker
    """
    
    result = db.execute_query(query)
    return [row[0] for row in result] if result else []

def process_stocks_batch(fmp, db, tickers, iteration):
    """Process a batch of stocks"""
    
    stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    # Configuration
    BATCH_SIZE = 20
    DELAY_BETWEEN_BATCHES = 3
    DELAY_BETWEEN_REQUESTS = 1
    
    print(f"⚙️  Processing {len(tickers)} stocks in batches of {BATCH_SIZE}")
    
    # Process in batches
    for batch_start in range(0, len(tickers), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(tickers))
        batch_tickers = tickers[batch_start:batch_end]
        
        print(f"\n🔄 Batch {batch_start//BATCH_SIZE + 1}/{(len(tickers) + BATCH_SIZE - 1)//BATCH_SIZE}")
        print(f"   Processing: {batch_start + 1}-{batch_end} of {len(tickers)}")
        
        # Process each ticker in the batch
        for i, ticker in enumerate(batch_tickers):
            ticker_num = batch_start + i + 1
            
            print(f"  [{ticker_num}/{len(tickers)}] {ticker}...", end=" ")
            
            try:
                success = process_single_stock(fmp, db, ticker)
                
                if success:
                    print(f"✅ Success")
                    stats['success'] += 1
                else:
                    print(f"❌ Failed")
                    stats['failed'] += 1
                    stats['errors'].append(f"{ticker}: Processing failed")
                
                stats['processed'] += 1
                
                # Rate limiting between requests
                if i < len(batch_tickers) - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                error_msg = f"{ticker}: {str(e)}"
                print(f"💥 Error")
                stats['failed'] += 1
                stats['processed'] += 1
                stats['errors'].append(error_msg)
                logging.error(f"Error processing {ticker}: {e}")
                continue
        
        # Rate limiting between batches
        if batch_end < len(tickers):
            print(f"\n⏳ Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    return stats

def process_single_stock(fmp, db, ticker):
    """Process a single stock and update company_fundamentals"""
    try:
        # Fetch financial statements
        financial_data = fmp.fetch_financial_statements(ticker)
        if not financial_data:
            return False
        
        # Fetch key statistics
        key_stats = fmp.fetch_key_statistics(ticker)
        if not key_stats:
            return False
        
        # Store the data in stocks table
        success = fmp.store_fundamental_data(ticker, financial_data, key_stats)
        
        if success:
            # Update company_fundamentals table
            update_fundamentals_query = """
            INSERT INTO company_fundamentals (
                ticker, revenue, net_income, ebitda, market_cap, 
                enterprise_value, shares_outstanding, total_debt, 
                shareholders_equity, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker) DO UPDATE SET
                revenue = EXCLUDED.revenue,
                net_income = EXCLUDED.net_income,
                ebitda = EXCLUDED.ebitda,
                market_cap = EXCLUDED.market_cap,
                enterprise_value = EXCLUDED.enterprise_value,
                shares_outstanding = EXCLUDED.shares_outstanding,
                total_debt = EXCLUDED.total_debt,
                shareholders_equity = EXCLUDED.shareholders_equity,
                last_updated = EXCLUDED.last_updated
            """
            
            # Extract data
            income = financial_data.get('income_statement', {})
            balance = financial_data.get('balance_sheet', {})
            market_data = key_stats.get('market_data', {})
            
            params = (
                ticker,
                income.get('revenue'),
                income.get('net_income'),
                income.get('ebitda'),
                market_data.get('market_cap'),
                market_data.get('enterprise_value'),
                market_data.get('shares_outstanding'),
                balance.get('total_debt'),
                balance.get('total_equity'),
                datetime.now()
            )
            
            db.execute_update(update_fundamentals_query, params)
        
        return success
        
    except Exception as e:
        logging.error(f"Error processing {ticker}: {e}")
        return False

def get_final_coverage(db):
    """Get final coverage statistics"""
    
    # Get total stocks
    total_query = "SELECT COUNT(*) FROM stocks"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Get stocks with complete fundamentals
    fundamentals_query = """
    SELECT COUNT(*) FROM company_fundamentals 
    WHERE revenue IS NOT NULL 
    AND net_income IS NOT NULL 
    AND market_cap IS NOT NULL
    """
    fundamentals_result = db.fetch_one(fundamentals_query)
    with_fundamentals = fundamentals_result[0] if fundamentals_result else 0
    
    return {
        'total': total_stocks,
        'with_fundamentals': with_fundamentals
    }

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"🕐 Started at: {start_time}")
    
    success = fill_all_company_fundamentals()
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n🕐 Completed at: {end_time}")
    print(f"⏱️  Total duration: {duration}")
    
    if success:
        print(f"\n🎉 All company fundamentals filling completed successfully!")
    else:
        print(f"\n⚠️  Company fundamentals filling completed with some issues") 