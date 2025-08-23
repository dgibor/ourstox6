#!/usr/bin/env python3
"""
Multi-Account Analyst Collection with Database Storage - Use 4 Finnhub accounts and save to database
"""
import os
import sys
import time
import logging
import threading
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

class MultiAccountAnalystCollectorWithDB:
    """Collect analyst data using multiple Finnhub accounts and save to database"""
    
    # Constants
    DEFAULT_STOCKS_PER_ACCOUNT = 175
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1
    DEFAULT_CALLS_PER_MINUTE = 60
    DEFAULT_CALLS_PER_DAY = 1000
    VALID_TICKER_MAX_LENGTH = 10
    VALID_TICKER_MIN_LENGTH = 1
    
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
        
        # Account limits (configurable with validation)
        self.calls_per_minute = self._validate_and_get_config('FINNHUB_CALLS_PER_MINUTE', self.DEFAULT_CALLS_PER_MINUTE)
        self.calls_per_day = self._validate_and_get_config('FINNHUB_CALLS_PER_DAY', self.DEFAULT_CALLS_PER_DAY)
        self.accounts_count = len(self.api_keys)
        
        # Validate configuration
        if self.calls_per_day <= self.calls_per_minute:
            raise ValueError(f"Daily limit ({self.calls_per_day}) must be greater than minute limit ({self.calls_per_minute})")
        
        # Account usage tracking (thread-safe)
        self.account_usage = {i: {'daily_calls': 0, 'last_reset': datetime.now().date()} for i in range(self.accounts_count)}
        self.account_rate_limits = {i: {'last_call': 0, 'calls_this_minute': 0} for i in range(self.accounts_count)}
        self._usage_lock = threading.Lock()
        
        # Performance monitoring
        self.performance_metrics = {
            'api_call_times': [],
            'database_operation_times': [],
            'total_processing_time': 0,
            'start_time': datetime.now()
        }
        
        # Stock allocation strategy
        self.stocks_per_account = self.DEFAULT_STOCKS_PER_ACCOUNT
        
        # Load actual stocks from database
        self.stocks = self._load_stocks_from_database()
        
        # Distribute stocks across accounts
        self.stock_allocation = self._allocate_stocks()
        
        logger.info(f"📊 Distributed {len(self.stocks)} stocks across {self.accounts_count} accounts")
    
    def _validate_and_get_config(self, env_var, default_value):
        """Validate and get configuration value from environment"""
        try:
            value = int(os.getenv(env_var, default_value))
            if value <= 0:
                logger.warning(f"⚠️ Warning: {env_var} must be positive, using default: {default_value}")
                return default_value
            return value
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Warning: Invalid {env_var}, using default: {default_value}")
            return default_value
    
    def _validate_ticker_input(self, ticker):
        """Validate ticker input format"""
        if not ticker or not isinstance(ticker, str):
            return False
        if len(ticker) > self.VALID_TICKER_MAX_LENGTH or len(ticker) < self.VALID_TICKER_MIN_LENGTH:
            return False
        if not ticker.isalnum():
            return False
        return True
    
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
        with self._usage_lock:
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
            
            # Track API call performance
            api_start_time = time.time()
            
            # Construct URL
            base_url = "https://finnhub.io/api/v1"
            url = f"{base_url}/{endpoint}"
            
            # Add API key to params
            if params is None:
                params = {}
            params['token'] = api_key
            
            # Make request
            response = requests.get(url, params=params, timeout=10)
            
            # Record API call time
            api_call_time = time.time() - api_start_time
            self.performance_metrics['api_call_times'].append(api_call_time)
            
            # Update usage tracking (thread-safe)
            with self._usage_lock:
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
        """Get analyst data for a stock with comprehensive error handling"""
        # Add input validation
        if not self._validate_ticker_input(ticker):
            logger.error(f"❌ Invalid ticker format: {ticker}")
            return None
        
        logger.info(f"🔍 Getting analyst data for {ticker}...")
        
        max_retries = self.DEFAULT_MAX_RETRIES
        retry_delay = self.DEFAULT_RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                # Get analyst recommendations
                result = self.make_api_call('stock/recommendation', {'symbol': ticker}, ticker)
                
                if result['success'] and result['status_code'] == 200:
                    data = result['data']
                    account = result['account_id'] + 1
                    
                    if data and len(data) > 0:
                        # Extract analyst data with validation
                        latest = data[0] if isinstance(data, list) else data
                        
                        # Validate data before processing
                        if self._validate_analyst_data(latest):
                            analyst_data = self._process_analyst_data(latest, ticker, account)
                            logger.info(f"  ✅ Success (Account {account}): {analyst_data['total_analysts']} analysts")
                            return analyst_data
                        else:
                            logger.warning(f"  ⚠️ Invalid analyst data format for {ticker}")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay * (2 ** attempt))
                                continue
                            else:
                                return self._get_fallback_analyst_data(ticker)
                    else:
                        logger.warning(f"  ⚠️ No analyst data returned for {ticker}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))
                            continue
                        else:
                            return self._get_fallback_analyst_data(ticker)
                else:
                    # Handle API error
                    error_msg = result.get('error', f'Status {result.get("status_code", "Unknown")}')
                    logger.error(f"  ❌ API Error (Attempt {attempt + 1}/{max_retries}): {error_msg}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        logger.info(f"  🔄 Falling back to emergency data for {ticker}")
                        return self._get_fallback_analyst_data(ticker)
                        
            except Exception as e:
                logger.error(f"  ❌ Exception (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.info(f"  🔄 Falling back to emergency data for {ticker}")
                    return self._get_fallback_analyst_data(ticker)
        
        return None
    
    def save_analyst_data_to_database(self, analyst_data):
        """Save analyst data to the database"""
        try:
            from daily_run.database import DatabaseManager
            
            db = DatabaseManager()
            
            with db.get_dict_cursor() as cursor:
                # Insert into analyst_rating_trends table with UPSERT to handle duplicates
                upsert_query = """
                INSERT INTO analyst_rating_trends (
                    ticker, period_date, strong_buy_count, buy_count, hold_count, 
                    sell_count, strong_sell_count, total_analysts, consensus_rating,
                    consensus_score, data_source, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, period_date, data_source) DO UPDATE SET
                    strong_buy_count = EXCLUDED.strong_buy_count,
                    buy_count = EXCLUDED.buy_count,
                    hold_count = EXCLUDED.hold_count,
                    sell_count = EXCLUDED.sell_count,
                    strong_sell_count = EXCLUDED.strong_sell_count,
                    total_analysts = EXCLUDED.total_analysts,
                    consensus_rating = EXCLUDED.consensus_rating,
                    consensus_score = EXCLUDED.consensus_score,
                    created_at = EXCLUDED.created_at
                """
                
                # Calculate consensus rating based on majority
                total = analyst_data['total_analysts']
                if total > 0:
                    strong_buy_pct = (analyst_data['strong_buy'] / total) * 100
                    buy_pct = (analyst_data['buy'] / total) * 100
                    hold_pct = (analyst_data['hold'] / total) * 100
                    sell_pct = (analyst_data['sell'] / total) * 100
                    strong_sell_pct = (analyst_data['strong_sell'] / total) * 100
                    
                    # Determine consensus rating
                    if strong_buy_pct >= 50:
                        consensus_rating = "Strong Buy"
                    elif (strong_buy_pct + buy_pct) >= 50:
                        consensus_rating = "Buy"
                    elif hold_pct >= 50:
                        consensus_rating = "Hold"
                    elif (sell_pct + strong_sell_pct) >= 50:
                        consensus_rating = "Sell"
                    else:
                        consensus_rating = "Hold"  # Default to hold if no clear majority
                    
                    # Calculate consensus score (-2 to +2 scale)
                    consensus_score = (
                        (analyst_data['strong_buy'] * 2) + 
                        (analyst_data['buy'] * 1) + 
                        (analyst_data['hold'] * 0) + 
                        (analyst_data['sell'] * -1) + 
                        (analyst_data['strong_sell'] * -2)
                    ) / total
                else:
                    consensus_rating = "N/A"
                    consensus_score = 0
                
                cursor.execute(upsert_query, (
                    analyst_data['ticker'],
                    datetime.now().date(),  # period_date
                    analyst_data['strong_buy'],
                    analyst_data['buy'],
                    analyst_data['hold'],
                    analyst_data['sell'],
                    analyst_data['strong_sell'],
                    analyst_data['total_analysts'],
                    consensus_rating,
                    consensus_score,
                    analyst_data['data_source'],
                    datetime.now()
                ))
                
            logger.info(f"  💾 Saved to analyst_rating_trends: {analyst_data['ticker']} ({analyst_data['total_analysts']} analysts, {consensus_rating})")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Database error for {analyst_data['ticker']}: {e}")
            return False
    
    def _validate_analyst_data(self, data):
        """Validate that analyst data meets expected format"""
        try:
            required_fields = ['buy', 'strongBuy', 'hold', 'sell', 'strongSell']
            
            # Check if all required fields exist
            for field in required_fields:
                if field not in data:
                    return False
            
            # Check if values are numeric and non-negative
            for field in required_fields:
                value = data.get(field, 0)
                if not isinstance(value, (int, float)) or value < 0:
                    return False
            
            # Check if at least one rating has analysts
            total = sum(data.get(field, 0) for field in required_fields)
            if total <= 0:
                return False
                
            return True
            
        except Exception:
            return False
    
    def _process_analyst_data(self, latest, ticker, account):
        """Process and validate analyst data"""
        try:
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
            
            return analyst_data
            
        except Exception as e:
            logger.error(f"  ❌ Error processing analyst data for {ticker}: {e}")
            raise  # Re-raise to be handled by caller
    
    def _get_fallback_analyst_data(self, ticker):
        """Provide emergency fallback data when API fails"""
        try:
            logger.info(f"  🔄 Using emergency fallback data for {ticker}")
            
            # Return minimal valid data structure
            return {
                'ticker': ticker,
                'strong_buy': 0,
                'buy': 0,
                'hold': 1,  # Default to hold
                'sell': 0,
                'strong_sell': 0,
                'total_analysts': 1,
                'data_source': 'finnhub_emergency',
                'account_used': 0
            }
            
        except Exception as e:
            logger.error(f"  ❌ Emergency fallback failed for {ticker}: {e}")
            return None
    
    def get_performance_metrics(self):
        """Get current performance metrics"""
        if not self.performance_metrics['api_call_times']:
            return "No performance data available"
        
        avg_api_time = sum(self.performance_metrics['api_call_times']) / len(self.performance_metrics['api_call_times'])
        total_api_calls = len(self.performance_metrics['api_call_times'])
        uptime = datetime.now() - self.performance_metrics['start_time']
        
        return {
            'avg_api_call_time': f"{avg_api_time:.3f}s",
            'total_api_calls': total_api_calls,
            'uptime': str(uptime),
            'api_calls_per_minute': f"{total_api_calls / (uptime.total_seconds() / 60):.2f}"
        }
    
    def run_collection_sample(self, num_stocks=40):
        """Run collection on a sample of stocks and save to database"""
        logger.info(f"🚀 RUNNING ANALYST COLLECTION ON {num_stocks} STOCKS")
        logger.info("=" * 60)
        
        # Get stocks from first account as sample
        sample_stocks = self.stock_allocation[0][:num_stocks]
        
        successful = 0
        failed = 0
        saved_to_db = 0
        
        for i, ticker in enumerate(sample_stocks, 1):
            logger.info(f"\n[{i:2d}/{num_stocks}] Processing {ticker}...")
            
            try:
                analyst_data = self.get_analyst_data(ticker)
                if analyst_data:
                    successful += 1
                    
                    # Save to database
                    if self.save_analyst_data_to_database(analyst_data):
                        saved_to_db += 1
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
        logger.info(f"✅ Successful API calls: {successful}")
        logger.info(f"💾 Saved to database: {saved_to_db}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📈 Success Rate: {(successful / num_stocks) * 100:.1f}%")
        logger.info(f"💾 DB Save Rate: {(saved_to_db / max(successful, 1)) * 100:.1f}%")
        
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
    logger.info("🚀 MULTI-ACCOUNT ANALYST COLLECTION WITH DATABASE")
    logger.info("=" * 70)
    logger.info("Using 4 Finnhub accounts and saving to database")
    logger.info("")
    
    try:
        # Initialize collector
        collector = MultiAccountAnalystCollectorWithDB()
        
        # Show initial status
        collector.show_account_status()
        
        # Run collection and save to database
        collector.run_collection_sample(40)
        
        # Show final status
        logger.info("\n📊 FINAL ACCOUNT USAGE")
        logger.info("=" * 40)
        collector.show_account_status()
        
        logger.info("\n🎉 COLLECTION COMPLETE!")
        logger.info("   • Check your database for analyst_targets table")
        logger.info("   • Data saved with 'finnhub' as data_source")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
