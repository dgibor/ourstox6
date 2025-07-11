#!/usr/bin/env python3
"""
Fill all fundamentals for all stocks in the database using FMP Premium.
- Batch processing with rate limit handling
- Robust error handling and logging
- Can resume if interrupted (skips already-filled tickers)
- Updates stocks table with missing company information
- Railway deployment ready
"""

from common_imports import os, time, logging, DB_CONFIG, setup_logging, datetime
import psycopg2
from fmp_service import FMPService

# Setup logging
setup_logging('fill_all_fundamentals_fmp', log_file='daily_run/logs/fill_all_fundamentals_fmp.log')

BATCH_SIZE = 10  # Number of tickers per batch
SLEEP_BETWEEN_BATCHES = 10  # seconds
MAX_RETRIES = 3


def get_all_tickers():
    """Fetch all tickers from the stocks table."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('SELECT ticker FROM stocks ORDER BY ticker')
        tickers = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        logging.info(f"Found {len(tickers)} tickers in database")
        return tickers
    except Exception as e:
        logging.error(f"Error fetching tickers: {e}")
        return []


def already_filled(service, ticker):
    """Check if fundamentals are already filled for this ticker (recently updated)."""
    try:
        service.cur.execute("SELECT fundamentals_last_update FROM stocks WHERE ticker = %s", (ticker,))
        row = service.cur.fetchone()
        if row and row[0]:
            # If updated in the last 90 days, skip
            last_update = row[0]
            if (datetime.now() - last_update).days < 90:
                return True
        return False
    except Exception as e:
        logging.warning(f"Error checking last update for {ticker}: {e}")
        return False


def update_stocks_table_info(service, ticker, key_stats):
    """Update stocks table with missing company information from FMP."""
    try:
        if not key_stats:
            return False
            
        market_data = key_stats.get('market_data', {})
        profile_data = key_stats.get('profile_data', {})
        
        # Prepare update data
        update_fields = {}
        
        # Market data
        if market_data.get('market_cap'):
            update_fields['market_cap'] = market_data['market_cap']
        if market_data.get('shares_outstanding'):
            update_fields['shares_outstanding'] = market_data['shares_outstanding']
        if market_data.get('enterprise_value'):
            update_fields['enterprise_value'] = market_data['enterprise_value']
            
        # Company profile data
        if profile_data.get('companyName') and not profile_data.get('companyName').strip() == '':
            update_fields['company_name'] = profile_data['companyName']
        if profile_data.get('sector') and not profile_data.get('sector').strip() == '':
            update_fields['sector'] = profile_data['sector']
        if profile_data.get('industry') and not profile_data.get('industry').strip() == '':
            update_fields['industry'] = profile_data['industry']
        if profile_data.get('website') and not profile_data.get('website').strip() == '':
            update_fields['website'] = profile_data['website']
        if profile_data.get('description') and not profile_data.get('description').strip() == '':
            update_fields['description'] = profile_data['description']
            
        if not update_fields:
            return False
            
        # Build dynamic UPDATE query
        set_clause = ", ".join([f"{key} = %s" for key in update_fields.keys()])
        values = list(update_fields.values()) + [ticker]
        
        service.cur.execute(f"""
            UPDATE stocks 
            SET {set_clause}
            WHERE ticker = %s
        """, tuple(values))
        
        service.conn.commit()
        logging.info(f"Updated stocks table for {ticker} with {len(update_fields)} fields")
        return True
        
    except Exception as e:
        logging.error(f"Error updating stocks table for {ticker}: {e}")
        service.conn.rollback()
        return False


def process_ticker(service, ticker, current_count, total_count):
    """Process a single ticker with comprehensive error handling and progress tracking."""
    print(f"[{current_count}/{total_count}] Processing {ticker}...")
    
    # Check if already filled
    if already_filled(service, ticker):
        print(f"  [SKIP] {ticker}: Already filled recently")
        logging.info(f"  [SKIP] {ticker}: Already filled recently, skipping")
        return "skipped"
    
    # Process with retries
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  [ATTEMPT {attempt}] Fetching data for {ticker}...")
            
            # Fetch fundamental data
            result = service.get_fundamental_data(ticker)
            
            if result:
                # Update stocks table with company info
                key_stats = result.get('key_stats', {})
                if key_stats:
                    update_stocks_table_info(service, ticker, key_stats)
                
                print(f"  [SUCCESS] {ticker}: Success (attempt {attempt})")
                logging.info(f"  [SUCCESS] {ticker}: Success (attempt {attempt})")
                return "success"
            else:
                raise Exception("No data returned from FMP")
                
        except Exception as e:
            error_msg = str(e)
            print(f"  [WARNING] {ticker}: Attempt {attempt} failed: {error_msg}")
            logging.warning(f"  [WARNING] {ticker}: Attempt {attempt} failed: {error_msg}")
            
            # Handle specific errors
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                wait_time = 30 * attempt  # Longer wait for rate limits
                print(f"  [RATE LIMIT] Waiting {wait_time}s...")
                time.sleep(wait_time)
            elif "not found" in error_msg.lower() or "404" in error_msg:
                print(f"  [NOT FOUND] {ticker}: Ticker not found in FMP")
                return "not_found"
            elif attempt == MAX_RETRIES:
                print(f"  [FAILED] {ticker}: Failed after {MAX_RETRIES} attempts")
                logging.error(f"  [FAILED] {ticker}: Failed after {MAX_RETRIES} attempts")
                return "failed"
            else:
                wait_time = 5 * attempt
                print(f"  [WAITING] {wait_time}s before retry...")
                time.sleep(wait_time)
    
    return "failed"


def fill_fundamentals_for_all():
    """Main function to fill fundamentals for all tickers."""
    print("=" * 80)
    print("FMP PREMIUM FUNDAMENTALS FILL - STARTING")
    print("=" * 80)
    
    logging.info("Starting FMP Premium Fundamentals Fill")
    logging.info("=" * 60)
    
    tickers = get_all_tickers()
    if not tickers:
        logging.error("No tickers found in database")
        print("ERROR: No tickers found in database")
        return
    
    service = FMPService()
    total = len(tickers)
    success, failed, skipped, not_found = 0, 0, 0, 0
    failed_tickers = []
    not_found_tickers = []

    print(f"Processing {total} tickers in batches of {BATCH_SIZE}")
    print(f"Sleep between batches: {SLEEP_BETWEEN_BATCHES}s")
    print(f"Max retries per ticker: {MAX_RETRIES}")
    print("=" * 80)
    
    logging.info(f"Processing {total} tickers in batches of {BATCH_SIZE}")
    logging.info(f"Sleep between batches: {SLEEP_BETWEEN_BATCHES}s")
    logging.info(f"Max retries per ticker: {MAX_RETRIES}")
    logging.info("=" * 60)

    for i in range(0, total, BATCH_SIZE):
        batch = tickers[i:i+BATCH_SIZE]
        batch_num = i//BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n{'='*60}")
        print(f"BATCH {batch_num}/{total_batches}: {batch}")
        print(f"{'='*60}")
        logging.info(f"Batch {batch_num}/{total_batches}: {batch}")
        
        batch_success, batch_failed, batch_skipped, batch_not_found = 0, 0, 0, 0
        
        for j, ticker in enumerate(batch):
            current_count = i + j + 1
            
            result = process_ticker(service, ticker, current_count, total)
            
            if result == "success":
                batch_success += 1
                success += 1
            elif result == "skipped":
                batch_skipped += 1
                skipped += 1
            elif result == "not_found":
                batch_not_found += 1
                not_found += 1
                not_found_tickers.append(ticker)
            else:  # failed
                batch_failed += 1
                failed += 1
                failed_tickers.append(ticker)
        
        # Batch summary
        print(f"\n[BATCH {batch_num} SUMMARY]")
        print(f"  Success: {batch_success}, Skipped: {batch_skipped}, Failed: {batch_failed}, Not Found: {batch_not_found}")
        
        # Overall progress
        processed = success + failed + skipped + not_found
        progress_pct = (processed / total) * 100
        print(f"[OVERALL PROGRESS] {processed}/{total} ({progress_pct:.1f}%)")
        print(f"  Total Success: {success}, Total Failed: {failed}, Total Skipped: {skipped}, Total Not Found: {not_found}")
        
        if i + BATCH_SIZE < total:  # Don't sleep after the last batch
            print(f"\n[SLEEPING] {SLEEP_BETWEEN_BATCHES}s between batches...")
            logging.info(f"[SLEEPING] {SLEEP_BETWEEN_BATCHES}s between batches...")
            time.sleep(SLEEP_BETWEEN_BATCHES)

    # Final summary
    print("\n" + "=" * 80)
    print("FMP PREMIUM FUNDAMENTALS FILL - COMPLETE!")
    print("=" * 80)
    print(f"FINAL SUMMARY:")
    print(f"  [SUCCESS] Successful: {success}")
    print(f"  [SKIP] Skipped (already filled): {skipped}")
    print(f"  [NOT FOUND] Not found in FMP: {not_found}")
    print(f"  [FAILED] Failed: {failed}")
    
    if (success + failed) > 0:
        success_rate = success/(success+failed)*100
        print(f"  [RATE] Success Rate: {success_rate:.1f}%")
    else:
        print(f"  [RATE] Success Rate: N/A")
    
    if failed_tickers:
        print(f"\n[FAILED TICKERS] {failed_tickers}")
    
    if not_found_tickers:
        print(f"\n[NOT FOUND TICKERS] {not_found_tickers}")
    
    logging.info("=" * 60)
    logging.info("FMP Premium Fundamentals Fill Complete!")
    logging.info(f"FINAL SUMMARY:")
    logging.info(f"  [SUCCESS] Successful: {success}")
    logging.info(f"  [SKIP] Skipped (already filled): {skipped}")
    logging.info(f"  [NOT FOUND] Not found in FMP: {not_found}")
    logging.info(f"  [FAILED] Failed: {failed}")
    if (success + failed) > 0:
        success_rate = success/(success+failed)*100
        logging.info(f"  [RATE] Success Rate: {success_rate:.1f}%")
    else:
        logging.info(f"  [RATE] Success Rate: N/A")
    
    if failed_tickers:
        logging.error(f"[FAILED TICKERS] {failed_tickers}")
    
    if not_found_tickers:
        logging.warning(f"[NOT FOUND TICKERS] {not_found_tickers}")
    
    service.close()
    print("\nScript completed successfully!")
    logging.info("Script completed")


if __name__ == "__main__":
    fill_fundamentals_for_all() 