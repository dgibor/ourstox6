#!/usr/bin/env python3
"""
Fill All Missing Fundamental Data - Single Ticker Processing
Optimized for large FMP quotas - processes one ticker at a time
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

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
        logging.FileHandler('fundamental_filling_single.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SingleTickerFiller:
    def __init__(self, rate_limit: int = 300):
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
    
    def process_ticker(self, ticker: str, company_name: str, market_cap: float) -> bool:
        """Process a single ticker to fetch and store fundamental data"""
        try:
            print(f"[PROCESSING] {ticker} ({company_name}) - Market Cap: ${market_cap:,.0f}")
            logger.info(f"Processing {ticker} ({company_name}) - Market Cap: ${market_cap:,.0f}")
            start_time = time.time()
            # Fetch fundamental data
            fundamental_data = self.fmp.get_fundamental_data(ticker)
            key_stats = self.fmp.fetch_key_statistics(ticker)
            fetch_time = time.time() - start_time
            print(f"[DEBUG] {ticker} API fetch time: {fetch_time:.2f}s")
            if not fundamental_data:
                print(f"[FAILED] {ticker}: No fundamental data found")
                logger.warning(f"No fundamental data found for {ticker}")
                return False
            if not key_stats:
                print(f"[FAILED] {ticker}: No key statistics found")
                logger.warning(f"No key statistics found for {ticker}")
                return False
            # Store in database
            try:
                success = self.fmp.store_fundamental_data(ticker, fundamental_data, key_stats)
            except Exception as e:
                print(f"[ERROR] {ticker}: Exception during store_fundamental_data: {e}")
                logger.error(f"Error storing data for {ticker}: {e}")
                return False
            if success:
                print(f"[SUCCESS] {ticker} updated successfully.")
                logger.info(f"Successfully updated {ticker}")
                return True
            else:
                print(f"[FAILED] {ticker}: Failed to store data.")
                logger.error(f"Failed to store data for {ticker}")
                return False
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")
            logger.error(f"Error processing {ticker}: {e}")
            return False
    
    def run_filling(self):
        """Run the fundamental filling process for missing tickers (limit to 100 for this run)"""
        missing = self.get_missing_tickers()
        # Limit to first 100 tickers for this run
        missing = missing[:100]
        total_tickers = len(missing)
        logger.info(f"Found {total_tickers} tickers missing fundamental data (processing only 100 for this run)")
        print(f"[DEBUG] Will process these tickers: {[t[0] if isinstance(t, tuple) else t.get('ticker') for t in missing]}")
        
        successful = 0
        failed = 0
        skipped = 0
        
        logger.info(f"📊 Processing {total_tickers} tickers...")
        logger.info("=" * 80)
        
        for i, ticker_data in enumerate(missing, 1):
            # Handle both dict and tuple results from database
            if isinstance(ticker_data, tuple):
                ticker_data = {
                    'ticker': ticker_data[0],
                    'company_name': ticker_data[1],
                    'market_cap': ticker_data[2],
                    'sector': ticker_data[3]
                }
            
            ticker = ticker_data['ticker']
            company_name = ticker_data.get('company_name', 'Unknown')
            market_cap = ticker_data.get('market_cap', 0) or 0
            
            # Skip ETFs and special tickers
            if any(keyword in company_name.lower() for keyword in ['etf', 'fund', 'trust', 'index']):
                logger.info(f"⏭️  Skipping ETF/Fund: {ticker} ({company_name})")
                skipped += 1
                continue
            
            # Process ticker
            success = self.process_ticker(ticker, company_name, market_cap)
            
            if success:
                successful += 1
            else:
                failed += 1
            
            # Rate limiting
            time.sleep(self.delay)
            
            # Progress update every 10 tickers
            if i % 10 == 0:
                success_rate = (successful / i) * 100
                logger.info(f"📈 Progress: {i}/{total_tickers} ({success_rate:.1f}% success rate)")
                logger.info(f"   ✅ Successful: {successful}, ❌ Failed: {failed}, ⏭️  Skipped: {skipped}")
        
        # Final summary
        logger.info("=" * 80)
        logger.info("FUNDAMENTAL FILLING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total Tickers Processed: {total_tickers}")
        logger.info(f"Successful Updates: {successful}")
        logger.info(f"Failed Updates: {failed}")
        logger.info(f"Skipped (ETFs/Funds): {skipped}")
        
        if total_tickers > 0:
            final_success_rate = (successful / total_tickers * 100)
            logger.info(f"Final Success Rate: {final_success_rate:.1f}%")
        
        # Check remaining missing tickers
        remaining = self.get_missing_tickers()
        logger.info(f"Remaining Missing Tickers: {len(remaining)}")
        
        if remaining:
            logger.info("Top 10 remaining missing tickers:")
            for i, ticker in enumerate(remaining[:10], 1):
                if isinstance(ticker, tuple):
                    ticker = {
                        'ticker': ticker[0],
                        'company_name': ticker[1],
                        'market_cap': ticker[2],
                        'sector': ticker[3]
                    }
                market_cap = ticker.get('market_cap', 0) or 0
                logger.info(f"   {i}. {ticker['ticker']} - ${market_cap:,.0f}")

def main():
    """Main execution function"""
    fmp_api_key = Config.get_api_key('fmp')
    if not fmp_api_key:
        logger.error("❌ FMP_API_KEY not set in environment variables")
        return
    
    # Create filler instance with high rate limit for large quota
    filler = SingleTickerFiller(rate_limit=300)  # 300 calls/minute for large quota
    
    try:
        filler.run_filling()
    except KeyboardInterrupt:
        logger.info("⏹️  Process interrupted by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    main() 