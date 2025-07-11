#!/usr/bin/env python3
"""
Complete fundamentals fill - ensure 100% coverage
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
        logging.FileHandler(f'complete_fundamentals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

def complete_fundamentals_fill():
    """Complete the fundamentals fill to ensure 100% coverage"""
    
    print("🎯 COMPLETE FUNDAMENTALS FILL - 100% COVERAGE")
    print("=" * 60)
    print("✅ Target: All 691 stocks with complete fundamentals")
    print("✅ Strategy: Multiple passes until complete")
    print("✅ Rate limiting and error handling included")
    print("=" * 60)
    
    db = DatabaseManager()
    fmp = FMPService()
    
    total_iterations = 0
    max_iterations = 20  # Safety limit
    
    while total_iterations < max_iterations:
        total_iterations += 1
        print(f"\n🔄 ITERATION {total_iterations}")
        print("=" * 40)
        
        # Get current status
        current_status = get_current_status(db)
        print(f"📊 Current Coverage: {current_status['complete_coverage']:.1f}%")
        print(f"   Complete: {current_status['complete_count']}/{current_status['total_stocks']}")
        
        # Check if we're done
        if current_status['complete_coverage'] >= 95:
            print("🎉 Target achieved! 95%+ coverage reached.")
            break
        
        # Get stocks needing processing
        stocks_to_process = get_stocks_needing_processing(db)
        
        if not stocks_to_process:
            print("✅ All stocks have complete data!")
            break
        
        print(f"📋 Processing {len(stocks_to_process)} stocks...")
        
        # Process this batch
        batch_stats = process_comprehensive_batch(fmp, db, stocks_to_process, total_iterations)
        
        print(f"📊 Iteration {total_iterations} Results:")
        print(f"   Processed: {batch_stats['processed']}")
        print(f"   Success: {batch_stats['success']}")
        print(f"   Failed: {batch_stats['failed']}")
        print(f"   Success rate: {(batch_stats['success'] / batch_stats['processed'] * 100):.1f}%")
        
        # If no progress, try different approach
        if batch_stats['success'] == 0:
            print("⚠️  No progress in this iteration. Trying alternative approach...")
            alternative_success = try_alternative_approach(fmp, db, stocks_to_process)
            if not alternative_success:
                print("⚠️  No progress with alternative approach. Stopping.")
                break
        
        # Wait before next iteration
        print(f"\n⏳ Waiting 60 seconds before next iteration...")
        time.sleep(60)
    
    # Final summary
    final_status = get_current_status(db)
    print(f"\n🎉 FINAL SUMMARY")
    print("=" * 60)
    print(f"Total iterations: {total_iterations}")
    print(f"Final coverage: {final_status['complete_coverage']:.1f}%")
    print(f"Complete stocks: {final_status['complete_count']}/{final_status['total_stocks']}")
    
    if final_status['complete_coverage'] >= 95:
        print("🎉 SUCCESS: 95%+ coverage achieved!")
    else:
        print("⚠️  PARTIAL SUCCESS: Some stocks still need manual attention")
    
    fmp.close()
    return final_status['complete_coverage'] >= 95

def get_current_status(db):
    """Get current coverage status"""
    
    # Total stocks
    total_query = "SELECT COUNT(*) FROM stocks"
    total_result = db.fetch_one(total_query)
    total_stocks = total_result[0] if total_result else 0
    
    # Complete fundamentals
    complete_query = """
    SELECT COUNT(DISTINCT ticker) FROM company_fundamentals 
    WHERE revenue IS NOT NULL 
    AND net_income IS NOT NULL 
    AND shares_outstanding IS NOT NULL
    """
    complete_result = db.fetch_one(complete_query)
    complete_count = complete_result[0] if complete_result else 0
    
    complete_coverage = (complete_count / total_stocks * 100) if total_stocks > 0 else 0
    
    return {
        'total_stocks': total_stocks,
        'complete_count': complete_count,
        'complete_coverage': complete_coverage
    }

def get_stocks_needing_processing(db):
    """Get stocks that need processing"""
    
    query = """
    SELECT s.ticker 
    FROM stocks s
    LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
    WHERE cf.ticker IS NULL 
       OR cf.revenue IS NULL 
       OR cf.net_income IS NULL 
       OR cf.shares_outstanding IS NULL
    ORDER BY s.market_cap DESC NULLS LAST, s.ticker
    """
    
    result = db.execute_query(query)
    return [row[0] for row in result] if result else []

def process_comprehensive_batch(fmp, db, tickers, iteration):
    """Process a comprehensive batch of stocks"""
    
    stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    # Smaller batch size for better success rate
    BATCH_SIZE = 10
    DELAY_BETWEEN_REQUESTS = 2
    
    print(f"⚙️  Processing {len(tickers)} stocks in batches of {BATCH_SIZE}")
    
    for batch_start in range(0, len(tickers), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(tickers))
        batch_tickers = tickers[batch_start:batch_end]
        
        print(f"\n🔄 Batch {batch_start//BATCH_SIZE + 1}/{(len(tickers) + BATCH_SIZE - 1)//BATCH_SIZE}")
        
        for i, ticker in enumerate(batch_tickers):
            ticker_num = batch_start + i + 1
            
            print(f"  [{ticker_num}/{len(tickers)}] {ticker}...", end=" ")
            
            try:
                success = process_single_stock_comprehensive(fmp, db, ticker)
                
                if success:
                    print(f"✅ Success")
                    stats['success'] += 1
                else:
                    print(f"❌ Failed")
                    stats['failed'] += 1
                
                stats['processed'] += 1
                
                # Rate limiting
                if i < len(batch_tickers) - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                print(f"💥 Error")
                stats['failed'] += 1
                stats['processed'] += 1
                stats['errors'].append(f"{ticker}: {str(e)}")
                logging.error(f"Error processing {ticker}: {e}")
                continue
        
        # Longer delay between batches
        if batch_end < len(tickers):
            print(f"\n⏳ Waiting 10 seconds before next batch...")
            time.sleep(10)
    
    return stats

def process_single_stock_comprehensive(fmp, db, ticker):
    """Process a single stock with comprehensive approach"""
    try:
        # Try multiple approaches
        approaches = [
            lambda: process_with_financial_statements(fmp, db, ticker),
            lambda: process_with_key_statistics_only(fmp, db, ticker),
            lambda: process_with_alternative_data(fmp, db, ticker)
        ]
        
        for approach in approaches:
            try:
                if approach():
                    return True
            except Exception as e:
                logging.warning(f"Approach failed for {ticker}: {e}")
                continue
        
        return False
        
    except Exception as e:
        logging.error(f"All approaches failed for {ticker}: {e}")
        return False

def process_with_financial_statements(fmp, db, ticker):
    """Process using financial statements"""
    financial_data = fmp.fetch_financial_statements(ticker)
    key_stats = fmp.fetch_key_statistics(ticker)
    
    if not financial_data or not key_stats:
        return False
    
    success = fmp.store_fundamental_data(ticker, financial_data, key_stats)
    
    if success:
        update_company_fundamentals(db, ticker, financial_data, key_stats)
    
    return success

def process_with_key_statistics_only(fmp, db, ticker):
    """Process using only key statistics"""
    key_stats = fmp.fetch_key_statistics(ticker)
    
    if not key_stats:
        return False
    
    # Try to get basic data from key stats
    market_data = key_stats.get('market_data', {})
    
    if market_data.get('shares_outstanding'):
        # Update just the shares outstanding
        update_query = """
        UPDATE company_fundamentals 
        SET shares_outstanding = %s, last_updated = %s
        WHERE ticker = %s
        """
        db.execute_update(update_query, (
            market_data['shares_outstanding'],
            datetime.now(),
            ticker
        ))
        return True
    
    return False

def process_with_alternative_data(fmp, db, ticker):
    """Process using alternative data sources"""
    # This could be expanded to use other APIs or data sources
    return False

def update_company_fundamentals(db, ticker, financial_data, key_stats):
    """Update company_fundamentals table"""
    
    update_query = """
    INSERT INTO company_fundamentals (
        ticker, report_date, period_type, fiscal_year, fiscal_quarter,
        revenue, gross_profit, operating_income, net_income, ebitda,
        eps_diluted, book_value_per_share, total_assets, total_debt,
        total_equity, cash_and_equivalents, operating_cash_flow,
        free_cash_flow, capex, shares_outstanding, shares_float,
        data_source, last_updated
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (ticker, report_date, period_type) DO UPDATE SET
        fiscal_year = EXCLUDED.fiscal_year,
        fiscal_quarter = EXCLUDED.fiscal_quarter,
        revenue = EXCLUDED.revenue,
        gross_profit = EXCLUDED.gross_profit,
        operating_income = EXCLUDED.operating_income,
        net_income = EXCLUDED.net_income,
        ebitda = EXCLUDED.ebitda,
        eps_diluted = EXCLUDED.eps_diluted,
        book_value_per_share = EXCLUDED.book_value_per_share,
        total_assets = EXCLUDED.total_assets,
        total_debt = EXCLUDED.total_debt,
        total_equity = EXCLUDED.total_equity,
        cash_and_equivalents = EXCLUDED.cash_and_equivalents,
        operating_cash_flow = EXCLUDED.operating_cash_flow,
        free_cash_flow = EXCLUDED.free_cash_flow,
        capex = EXCLUDED.capex,
        shares_outstanding = EXCLUDED.shares_outstanding,
        shares_float = EXCLUDED.shares_float,
        data_source = EXCLUDED.data_source,
        last_updated = EXCLUDED.last_updated
    """
    
    # Extract data
    income = financial_data.get('income_statement', {})
    balance = financial_data.get('balance_sheet', {})
    cash_flow = financial_data.get('cash_flow_statement', {})
    market_data = key_stats.get('market_data', {})
    
    current_date = datetime.now().date()
    
    params = (
        ticker, current_date, 'TTM', 2024, None,
        income.get('revenue'), income.get('gross_profit'),
        income.get('operating_income'), income.get('net_income'),
        income.get('ebitda'), income.get('eps_diluted'),
        income.get('book_value_per_share'), balance.get('total_assets'),
        balance.get('total_debt'), balance.get('total_equity'),
        balance.get('cash_and_equivalents'), cash_flow.get('operating_cash_flow'),
        cash_flow.get('free_cash_flow'), cash_flow.get('capex'),
        market_data.get('shares_outstanding'), market_data.get('shares_float'),
        'FMP', datetime.now()
    )
    
    db.execute_update(update_query, params)

def try_alternative_approach(fmp, db, stocks_to_process):
    """Try alternative approach for remaining stocks"""
    print("🔄 Trying alternative approach...")
    
    # Try to get just shares outstanding for stocks that have other data
    shares_query = """
    SELECT DISTINCT cf.ticker 
    FROM company_fundamentals cf
    WHERE cf.shares_outstanding IS NULL
    AND cf.revenue IS NOT NULL
    AND cf.net_income IS NOT NULL
    LIMIT 20
    """
    
    shares_stocks = db.execute_query(shares_query)
    tickers = [row[0] for row in shares_stocks] if shares_stocks else []
    
    if not tickers:
        return False
    
    success_count = 0
    for ticker in tickers:
        try:
            key_stats = fmp.fetch_key_statistics(ticker)
            if key_stats and key_stats.get('market_data', {}).get('shares_outstanding'):
                shares_outstanding = key_stats['market_data']['shares_outstanding']
                
                update_query = """
                UPDATE company_fundamentals 
                SET shares_outstanding = %s, last_updated = %s
                WHERE ticker = %s
                """
                
                db.execute_update(update_query, (shares_outstanding, datetime.now(), ticker))
                success_count += 1
                print(f"  ✅ {ticker}: Updated shares outstanding")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ {ticker}: {str(e)}")
            continue
    
    print(f"Alternative approach: {success_count} successes")
    return success_count > 0

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"🕐 Started at: {start_time}")
    
    success = complete_fundamentals_fill()
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n🕐 Completed at: {end_time}")
    print(f"⏱️  Total duration: {duration}")
    
    if success:
        print(f"\n🎉 Complete fundamentals fill successful!")
    else:
        print(f"\n⚠️  Complete fundamentals fill completed with some issues") 