#!/usr/bin/env python3
"""
Multi-Account Analyst Collection - Use 4 Finnhub accounts to collect analyst data
"""
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the daily_run directory to the path
daily_run_path = Path(__file__).parent
sys.path.insert(0, str(daily_run_path))

# Load environment variables
load_dotenv(daily_run_path / ".env")

from finnhub_multi_account_manager import FinnhubMultiAccountManager
from database import DatabaseManager


class MultiAccountAnalystCollection:
    """Collect analyst data using multiple Finnhub accounts"""
    
    def __init__(self):
        """Initialize the multi-account collector"""
        # Initialize multi-account manager
        self.finnhub_manager = FinnhubMultiAccountManager()
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Stock allocation strategy
        self.stocks_per_account = 175
        
        # Load actual stocks from database
        self.stocks = self._load_stocks_from_database()
        
        # Distribute stocks across accounts
        self.stock_allocation = self._allocate_stocks()
        
        logger.info(f"✅ MultiAccountAnalystCollection initialized with {len(self.stocks)} stocks")
    
    def _load_stocks_from_database(self) -> List[str]:
        """Load active stocks from database"""
        try:
            query = "SELECT ticker FROM stocks WHERE active = true ORDER BY ticker"
            results = self.db.execute_query(query)
            
            if results:
                tickers = [row[0] for row in results]
                logger.info(f"📊 Loaded {len(tickers)} active stocks from database")
                return tickers
            else:
                logger.warning("⚠️ No active stocks found in database")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error loading stocks from database: {e}")
            return []
    
    def _allocate_stocks(self) -> Dict[int, List[str]]:
        """Distribute stocks across accounts for load balancing"""
        allocation = {}
        stocks_count = len(self.stocks)
        
        for account_id in range(self.finnhub_manager.accounts_count):
            start_idx = account_id * self.stocks_per_account
            end_idx = min(start_idx + self.stocks_per_account, stocks_count)
            
            if start_idx < stocks_count:
                allocation[account_id] = self.stocks[start_idx:end_idx]
            else:
                allocation[account_id] = []
        
        # Log allocation
        for account_id, stocks in allocation.items():
            logger.info(f"📊 Account {account_id + 1}: {len(stocks)} stocks")
        
        return allocation
    
    def collect_analyst_data_for_ticker(self, ticker: str) -> Dict:
        """Collect comprehensive analyst data for a single ticker"""
        try:
            logger.info(f"🔍 Collecting analyst data for {ticker}")
            
            # Get analyst recommendations
            recommendations = self.finnhub_manager.get_analyst_recommendations(ticker)
            
            # Get earnings calendar
            earnings = self.finnhub_manager.get_earnings_calendar(ticker)
            
            # Get company profile
            profile = self.finnhub_manager.get_company_profile(ticker)
            
            # Compile results
            result = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'recommendations': recommendations,
                'earnings': earnings,
                'profile': profile,
                'status': 'success'
            }
            
            logger.info(f"✅ Collected analyst data for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error collecting analyst data for {ticker}: {e}")
            return {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'status': 'failed',
                'error': str(e)
            }
    
    def collect_all_analyst_data(self, max_stocks: int = None) -> Dict:
        """Collect analyst data for all stocks using multi-account rotation"""
        try:
            start_time = datetime.now()
            stocks_to_process = self.stocks[:max_stocks] if max_stocks else self.stocks
            
            logger.info(f"🚀 Starting analyst data collection for {len(stocks_to_process)} stocks")
            
            results = []
            successful = 0
            failed = 0
            
            for i, ticker in enumerate(stocks_to_process, 1):
                logger.info(f"📊 Processing {i}/{len(stocks_to_process)}: {ticker}")
                
                # Collect data
                result = self.collect_analyst_data_for_ticker(ticker)
                results.append(result)
                
                if result['status'] == 'success':
                    successful += 1
                else:
                    failed += 1
                
                # Small delay between calls to be respectful
                time.sleep(0.1)
                
                # Progress update every 50 stocks
                if i % 50 == 0:
                    logger.info(f"📈 Progress: {i}/{len(stocks_to_process)} completed")
            
            # Compile final results
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Get performance metrics
            performance = self.finnhub_manager.get_performance_metrics()
            
            final_result = {
                'total_stocks': len(stocks_to_process),
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / len(stocks_to_process)) * 100 if stocks_to_process else 0,
                'processing_time_seconds': processing_time,
                'start_time': start_time,
                'end_time': end_time,
                'performance_metrics': performance,
                'results': results
            }
            
            logger.info(f"🎉 Analyst data collection completed!")
            logger.info(f"📊 Success: {successful}/{len(stocks_to_process)} ({final_result['success_rate']:.1f}%)")
            logger.info(f"⏱️ Processing time: {processing_time:.1f} seconds")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Error in analyst data collection: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'total_stocks': 0,
                'successful': 0,
                'failed': 0
            }
    
    def get_collection_status(self) -> Dict:
        """Get current collection status and account information"""
        try:
            account_status = self.finnhub_manager.get_account_status()
            performance = self.finnhub_manager.get_performance_metrics()
            
            return {
                'accounts_count': self.finnhub_manager.accounts_count,
                'total_stocks': len(self.stocks),
                'stocks_per_account': self.stocks_per_account,
                'account_status': account_status,
                'performance_metrics': performance,
                'collection_status': 'ready'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting collection status: {e}")
            return {
                'collection_status': 'error',
                'error': str(e)
            }
    
    def close(self):
        """Clean up resources"""
        try:
            self.finnhub_manager.close()
            logger.info("🔒 MultiAccountAnalystCollection closed")
        except Exception as e:
            logger.error(f"❌ Error closing collection: {e}")


def main():
    """Main execution function"""
    try:
        # Initialize collection system
        collector = MultiAccountAnalystCollection()
        
        # Show status
        status = collector.get_collection_status()
        logger.info(f"📊 Collection Status: {status}")
        
        # Collect data for first 10 stocks as test
        logger.info("🧪 Running test collection for first 10 stocks...")
        test_results = collector.collect_all_analyst_data(max_stocks=10)
        
        logger.info("✅ Test collection completed!")
        
        # Close resources
        collector.close()
        
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")


if __name__ == "__main__":
    main()
