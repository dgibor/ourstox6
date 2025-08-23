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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the daily_run directory to the path
daily_run_path = Path(__file__).parent / "daily_run"
sys.path.insert(0, str(daily_run_path))

# Load environment variables
load_dotenv(daily_run_path / ".env")

class MultiAccountAnalystCollection:
    """Collect analyst data using multiple Finnhub accounts"""
    
    def __init__(self):
        """Initialize the multi-account collector"""
        # Load all 4 API keys
        self.api_keys = []
        for i in range(1, 5):
            key = os.getenv(f'FINNHUB_API_KEY_{i}')
            if key:
                self.api_keys.append(key)
            else:
                logger.warning(f"⚠️ Warning: FINNHUB_API_KEY_{i} not found in .env")
        
        if not self.api_keys:
            raise ValueError("No Finnhub API keys found in environment")
        
        logger.info(f"✅ Loaded {len(self.api_keys)} Finnhub API keys")
        
        # Account limits
        self.calls_per_minute = int(os.getenv('FINNHUB_CALLS_PER_MINUTE', 60))
        self.calls_per_day = int(os.getenv('FINNHUB_CALLS_PER_DAY', 1000))
        self.accounts_count = len(self.api_keys)
        
        # Account usage tracking
        self.account_usage = {i: {'daily_calls': 0, 'last_reset': datetime.now().date()} for i in range(self.accounts_count)}
        self.account_rate_limits = {i: {'last_call': 0, 'calls_this_minute': 0} for i in range(self.accounts_count)}
        
        # Stock allocation strategy
        self.stocks_per_account = 175
        
        # Load actual stocks from database
        self.stocks = self._load_stocks_from_database()
        
        # Distribute stocks across accounts
        self.stock_allocation = self._allocate_stocks()
        
        logger.info(f"📊 Distributed {len(self.stocks)} stocks across {self.accounts_count} accounts")
    
    def _load_stocks_from_database(self):
        """Load actual stock tickers from the database"""
        try:
            # Import database manager
            from daily_run.database import DatabaseManager
            
            logger.info("🔍 Loading stocks from database...")
            
            # Initialize database connection
            db = DatabaseManager()
            
            # Use the context manager properly
            with db.get_dict_cursor() as cursor:
                cursor.execute("SELECT ticker FROM stocks ORDER BY ticker")
                results = cursor.fetchall()
            
            # Extract tickers
            tickers = [row['ticker'] for row in results if row['ticker']]
            
            logger.info(f"✅ Loaded {len(tickers)} stocks from database")
            
            if len(tickers) == 0:
                logger.warning("⚠️ No stocks found in database, using fallback list")
                # Fallback to a basic list if database is empty
                return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
            
            return tickers
            
        except Exception as e:
            logger.error(f"❌ Error loading stocks from database: {e}")
            logger.warning("⚠️ Using fallback stock list")
            # Fallback to a basic list if database connection fails
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
    
    def _allocate_stocks(self):
        """Allocate stocks evenly across accounts"""
        allocation = {}
        
        for account_id in range(self.accounts_count):
            start_idx = account_id * self.stocks_per_account
            end_idx = start_idx + self.stocks_per_account
            
            # Add extra stocks to first few accounts if there are remaining stocks
            remaining = len(self.stocks) - (self.accounts_count * self.stocks_per_account)
            if account_id < remaining:
                end_idx += 1
            
            allocation[account_id] = self.stocks[start_idx:end_idx]
        
        return allocation
    
    def get_available_account(self, stock_ticker=None):
        """Get the best available account for API calls"""
        current_time = time.time()
        current_date = datetime.now().date()
        
        # Reset daily counters if it's a new day
        for account_id in self.account_usage:
            if self.account_usage[account_id]['last_reset'] != current_date:
                self.account_usage[account_id]['daily_calls'] = 0
                self.account_usage[account_id]['last_reset'] = current_date
                self.account_rate_limits[account_id]['calls_this_minute'] = 0
        
        # Find accounts with available daily calls
        available_accounts = []
        for account_id in range(self.accounts_count):
            if self.account_usage[account_id]['daily_calls'] < self.calls_per_day:
                available_accounts.append(account_id)
        
        if not available_accounts:
            raise Exception("All accounts have reached daily limits")
        
        # If stock ticker is provided, find the account that owns it
        if stock_ticker:
            for account_id, stocks in self.stock_allocation.items():
                if stock_ticker in stocks and account_id in available_accounts:
                    return account_id
        
        # Otherwise, find the account with the most remaining calls
        best_account = max(available_accounts, key=lambda x: self.calls_per_day - self.account_usage[x]['daily_calls'])
        
        return best_account
    
    def make_api_call(self, endpoint, params=None, stock_ticker=None):
        """Make an API call using the best available account"""
        account_id = self.get_available_account(stock_ticker)
        api_key = self.api_keys[account_id]
        
        # Check rate limiting
        current_time = time.time()
        rate_limit = self.account_rate_limits[account_id]
        
        # Reset minute counter if a minute has passed
        if current_time - rate_limit['last_call'] >= 60:
            rate_limit['calls_this_minute'] = 0
        
        # Check if we can make a call this minute
        if rate_limit['calls_this_minute'] >= self.calls_per_minute:
            # Wait until next minute
            wait_time = 60 - (current_time - rate_limit['last_call'])
            if wait_time > 0:
                logger.info(f"⏳ Account {account_id + 1} rate limited, waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                current_time = time.time()
                rate_limit['calls_this_minute'] = 0
        
        # Make the API call
        try:
            import requests
            
            # Construct URL
            base_url = "https://finnhub.io/api/v1"
            url = f"{base_url}/{endpoint}"
            
            # Add API key to params
            if params is None:
                params = {}
            params['token'] = api_key
            
            # Make request
            response = requests.get(url, params=params, timeout=10)
            
            # Update usage tracking
            self.account_usage[account_id]['daily_calls'] += 1
            rate_limit['last_call'] = current_time
            rate_limit['calls_this_minute'] += 1
            
            return {
                'success': True,
                'account_id': account_id,
                'response': response,
                'data': response.json() if response.status_code == 200 else None,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'account_id': account_id,
                'error': str(e)
            }
    
    def get_analyst_data(self, ticker):
        """Get analyst data for a stock"""
        logger.info(f"🔍 Getting analyst data for {ticker}...")
        
        try:
            # Get analyst recommendations
            result = self.make_api_call('stock/recommendation', {'symbol': ticker}, ticker)
            
            if result['success'] and result['status_code'] == 200:
                data = result['data']
                account = result['account_id'] + 1
                
                if data and len(data) > 0:
                    # Extract analyst data
                    latest = data[0] if isinstance(data, list) else data
                    
                    analyst_data = {
                        'ticker': ticker,
                        'strong_buy': latest.get('strongBuy', 0),
                        'buy': latest.get('buy', 0),
                        'hold': latest.get('hold', 0),
                        'sell': latest.get('sell', 0),
                        'strong_sell': latest.get('strongSell', 0),
                        'data_source': 'finnhub',
                        'account_used': account
                    }
                    
                    # Calculate total analysts
                    analyst_data['total_analysts'] = (
                        analyst_data['strong_buy'] + 
                        analyst_data['buy'] + 
                        analyst_data['hold'] + 
                        analyst_data['sell'] + 
                        analyst_data['strong_sell']
                    )
                    
                    logger.info(f"  ✅ Success (Account {account}): {analyst_data['total_analysts']} analysts")
                    return analyst_data
                else:
                    logger.warning(f"  ⚠️ No analyst data returned for {ticker}")
                    return None
            else:
                error_msg = result.get('error', f'Status {result.get("status_code", "Unknown")}')
                logger.error(f"  ❌ API Error: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"  ❌ Exception: {e}")
            return None
    
    def run_collection_sample(self, num_stocks=40):
        """Run collection on a sample of stocks"""
        logger.info(f"🚀 RUNNING ANALYST COLLECTION ON {num_stocks} STOCKS")
        logger.info("=" * 60)
        
        # Get stocks from first account as sample
        sample_stocks = self.stock_allocation[0][:num_stocks]
        
        successful = 0
        failed = 0
        
        for i, ticker in enumerate(sample_stocks, 1):
            logger.info(f"\n[{i:2d}/{num_stocks}] Processing {ticker}...")
            
            try:
                analyst_data = self.get_analyst_data(ticker)
                if analyst_data:
                    successful += 1
                else:
                    failed += 1
                
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {ticker}: {e}")
                failed += 1
        
        # Summary
        logger.info(f"\n📊 COLLECTION SUMMARY")
        logger.info("=" * 30)
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📈 Success Rate: {(successful / num_stocks) * 100:.1f}%")
        
    def show_account_status(self):
        """Show current status of all accounts"""
        current_date = datetime.now().date()
        
        logger.info("📊 FINNHUB MULTI-ACCOUNT STATUS")
        logger.info("=" * 50)
        
        for account_id in range(self.accounts_count):
            usage = self.account_usage[account_id]
            rate_limit = self.account_rate_limits[account_id]
            
            # Reset daily counter if it's a new day
            if usage['last_reset'] != current_date:
                usage['daily_calls'] = 0
                usage['last_reset'] = current_date
            
            remaining_daily = self.calls_per_day - usage['daily_calls']
            remaining_minute = self.calls_per_minute - rate_limit['calls_this_minute']
            
            logger.info(f"🔑 Account {account_id + 1}:")
            logger.info(f"  • Daily Calls: {usage['daily_calls']}/{self.calls_per_day} ({remaining_daily} remaining)")
            logger.info(f"  • Minute Calls: {rate_limit['calls_this_minute']}/{self.calls_per_minute} ({remaining_minute} remaining)")
            logger.info(f"  • Stocks: {len(self.stock_allocation[account_id])}")
            logger.info(f"  • Sample: {', '.join(self.stock_allocation[account_id][:5])}...")
            logger.info("")

def main():
    """Main function"""
    logger.info("🚀 MULTI-ACCOUNT ANALYST COLLECTION")
    logger.info("=" * 60)
    logger.info("Using 4 Finnhub accounts")
    logger.info("")
    
    try:
        # Initialize collector
        collector = MultiAccountAnalystCollection()
        
        # Show initial status
        collector.show_account_status()
        
        # Run collection
        collector.run_collection_sample(40)
        
        # Show final status
        logger.info("\n📊 FINAL ACCOUNT USAGE")
        logger.info("=" * 40)
        collector.show_account_status()
        
        logger.info("\n🎉 COLLECTION COMPLETE!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
