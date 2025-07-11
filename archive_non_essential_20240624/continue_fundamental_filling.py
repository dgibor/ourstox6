#!/usr/bin/env python3
"""
Continue Fundamental Data Filling for All Remaining Tickers
Processes all tickers missing fundamental data, prioritizing by market cap
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from fmp_service import FMPService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fundamental_filling_continue.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FundamentalFiller:
    def __init__(self, rate_limit: int = 200):
        self.db = DatabaseManager()
        self.fmp = FMPService()
        self.rate_limit = rate_limit
        self.delay = 60 / rate_limit  # Delay between requests
        
    def get_missing_tickers(self) -> List[Dict[str, Any]]:
        """Get all tickers missing fundamental data, ordered by market cap"""
        query = """
        SELECT DISTINCT s.ticker, s.company_name, s.market_cap, s.sector
        FROM stocks s
        LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
        WHERE cf.ticker IS NULL 
           OR cf.total_assets IS NULL 
           OR cf.total_equity IS NULL
           OR cf.total_debt IS NULL
           OR cf.free_cash_flow IS NULL
           OR cf.shares_outstanding IS NULL
           OR cf.total_assets = 0
           OR cf.total_equity = 0
           OR cf.shares_outstanding = 0
        ORDER BY s.market_cap DESC NULLS LAST
        """
        
        try:
            result = self.db.execute_query(query)
            logger.info(f"Found {len(result)} tickers missing fundamental data")
            return result
        except Exception as e:
            logger.error(f"Error getting missing tickers: {e}")
            return []
    
    def get_missing_tickers_by_market_cap(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group missing tickers by market cap category"""
        tickers = self.get_missing_tickers()
        
        categories = {
            'large_cap': [],
            'mid_cap': [],
            'small_cap': [],
            'micro_cap': [],
            'unknown': []
        }
        
        for ticker in tickers:
            # Handle both dict and tuple results from database
            if isinstance(ticker, tuple):
                # Convert tuple to dict with column names
                ticker = {
                    'ticker': ticker[0],
                    'company_name': ticker[1],
                    'market_cap': ticker[2],
                    'sector': ticker[3]
                }
            
            market_cap = ticker.get('market_cap', 0) or 0
            
            if market_cap >= 10_000_000_000:  # $10B+
                categories['large_cap'].append(ticker)
            elif market_cap >= 2_000_000_000:  # $2B-$10B
                categories['mid_cap'].append(ticker)
            elif market_cap >= 300_000_000:   # $300M-$2B
                categories['small_cap'].append(ticker)
            elif market_cap > 0:              # $0-$300M
                categories['micro_cap'].append(ticker)
            else:
                categories['unknown'].append(ticker)
        
        return categories
    
    def process_ticker(self, ticker: str, company_name: str) -> bool:
        """Process a single ticker to fetch and store fundamental data"""
        try:
            logger.info(f"Processing {ticker} ({company_name})")
            
            # Fetch fundamental data
            fundamental_data = self.fmp.get_fundamental_data(ticker)
            
            if not fundamental_data:
                logger.warning(f"No fundamental data found for {ticker}")
                return False
            
            # Store in database
            success = self.fmp.store_fundamental_data(ticker, fundamental_data)
            
            if success:
                logger.info(f"Successfully updated {ticker}")
                return True
            else:
                logger.error(f"Failed to store data for {ticker}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            return False
    
    def process_batch(self, tickers: List[Dict[str, Any]], batch_name: str) -> Dict[str, int]:
        """Process a batch of tickers"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {batch_name}: {len(tickers)} tickers")
        logger.info(f"{'='*60}")
        
        successful = 0
        failed = 0
        skipped = 0
        
        for i, ticker_data in enumerate(tickers, 1):
            ticker = ticker_data['ticker']
            company_name = ticker_data.get('company_name', 'Unknown')
            market_cap = ticker_data.get('market_cap', 0)
            
            # Skip ETFs and special tickers
            if any(keyword in company_name.lower() for keyword in ['etf', 'fund', 'trust', 'index']):
                logger.info(f"Skipping ETF/Fund: {ticker} ({company_name})")
                skipped += 1
                continue
            
            logger.info(f"[{i}/{len(tickers)}] Processing {ticker} (Market Cap: ${market_cap:,.0f})")
            
            success = self.process_ticker(ticker, company_name)
            
            if success:
                successful += 1
            else:
                failed += 1
            
            # Rate limiting
            time.sleep(self.delay)
            
            # Progress update every 10 tickers
            if i % 10 == 0:
                success_rate = (successful / i) * 100
                logger.info(f"Progress: {i}/{len(tickers)} ({success_rate:.1f}% success rate)")
        
        return {
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'total': len(tickers)
        }
    
    def run_complete_filling(self):
        """Run the complete fundamental filling process"""
        logger.info("Starting complete fundamental data filling process")
        logger.info(f"Rate limit: {self.rate_limit} calls/minute")
        
        # Get missing tickers by market cap
        categories = self.get_missing_tickers_by_market_cap()
        
        total_stats = {
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0
        }
        
        # Process each category in order of priority
        for category, tickers in categories.items():
            if not tickers:
                logger.info(f"No {category} tickers to process")
                continue
            
            logger.info(f"\nProcessing {category} tickers: {len(tickers)} found")
            
            # Process in smaller batches for better monitoring
            batch_size = 50
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(tickers) + batch_size - 1) // batch_size
                
                batch_name = f"{category} batch {batch_num}/{total_batches}"
                stats = self.process_batch(batch, batch_name)
                
                # Update total stats
                for key in total_stats:
                    total_stats[key] += stats[key]
                
                # Summary after each batch
                logger.info(f"\nBatch Summary ({batch_name}):")
                logger.info(f"  Successful: {stats['successful']}")
                logger.info(f"  Failed: {stats['failed']}")
                logger.info(f"  Skipped: {stats['skipped']}")
                logger.info(f"  Success Rate: {(stats['successful'] / stats['total'] * 100):.1f}%")
                
                # Overall progress
                overall_success_rate = (total_stats['successful'] / total_stats['total'] * 100) if total_stats['total'] > 0 else 0
                logger.info(f"\nOverall Progress:")
                logger.info(f"  Total Processed: {total_stats['total']}")
                logger.info(f"  Total Successful: {total_stats['successful']}")
                logger.info(f"  Total Failed: {total_stats['failed']}")
                logger.info(f"  Overall Success Rate: {overall_success_rate:.1f}%")
                
                # Brief pause between batches
                if i + batch_size < len(tickers):
                    logger.info("Pausing 30 seconds between batches...")
                    time.sleep(30)
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("FUNDAMENTAL FILLING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tickers Processed: {total_stats['total']}")
        logger.info(f"Successful Updates: {total_stats['successful']}")
        logger.info(f"Failed Updates: {total_stats['failed']}")
        logger.info(f"Skipped (ETFs/Funds): {total_stats['skipped']}")
        
        if total_stats['total'] > 0:
            final_success_rate = (total_stats['successful'] / total_stats['total'] * 100)
            logger.info(f"Final Success Rate: {final_success_rate:.1f}%")
        
        # Check remaining missing tickers
        remaining = self.get_missing_tickers()
        logger.info(f"Remaining Missing Tickers: {len(remaining)}")
        
        if remaining:
            logger.info("Top 10 remaining missing tickers:")
            for i, ticker in enumerate(remaining[:10], 1):
                market_cap = ticker.get('market_cap', 0) or 0
                logger.info(f"  {i}. {ticker['ticker']} - ${market_cap:,.0f}")

def main():
    """Main execution function"""
    fmp_api_key = Config.get_api_key('fmp')
    if not fmp_api_key:
        logger.error("FMP_API_KEY not set in environment variables")
        return
    
    # Create filler instance with rate limiting
    filler = FundamentalFiller(rate_limit=200)  # 200 calls/minute for Starter plan
    
    try:
        filler.run_complete_filling()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 