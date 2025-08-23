#!/usr/bin/env python3
"""
Finnhub Multi-Account Manager

Manages multiple Finnhub API accounts with intelligent key rotation,
rate limiting, and load balancing to maximize API usage.
"""

import os
import time
import logging
import threading
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FinnhubMultiAccountManager:
    """
    Manages multiple Finnhub API accounts with intelligent rotation
    
    Features:
    - 4 API key rotation to avoid rate limits
    - Per-minute and per-day rate limiting
    - Load balancing across accounts
    - Automatic fallback and retry logic
    - Performance monitoring and metrics
    """
    
    # Default configuration
    DEFAULT_CALLS_PER_MINUTE = 60
    DEFAULT_CALLS_PER_DAY = 1000
    DEFAULT_STOCKS_PER_ACCOUNT = 175
    DEFAULT_RATE_LIMIT_SLEEP = 60  # seconds to wait when rate limited
    DEFAULT_MINUTE_RESET = 60      # seconds for minute rate limit reset
    
    def __init__(self):
        """Initialize the multi-account manager"""
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
        
        # Timing configuration (configurable with validation)
        self.rate_limit_sleep = self._validate_and_get_config('FINNHUB_RATE_LIMIT_SLEEP', self.DEFAULT_RATE_LIMIT_SLEEP)
        self.minute_reset = self._validate_and_get_config('FINNHUB_MINUTE_RESET', self.DEFAULT_MINUTE_RESET)
        
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
            'total_processing_time': 0,
            'start_time': datetime.now(),
            'calls_per_account': {i: 0 for i in range(self.accounts_count)}
        }
        
        # Limit API call times to prevent memory leaks
        self.MAX_CALL_TIMES = 1000
        
        # Stock allocation strategy
        self.stocks_per_account = self.DEFAULT_STOCKS_PER_ACCOUNT
        
        logger.info(f"✅ FinnhubMultiAccountManager initialized with {self.accounts_count} accounts")
        logger.info(f"📊 Rate limits: {self.calls_per_minute}/min, {self.calls_per_day}/day per account")
    
    def _validate_and_get_config(self, env_var: str, default: int) -> int:
        """Validate and get configuration value from environment"""
        try:
            value = int(os.getenv(env_var, default))
            if value <= 0:
                logger.warning(f"⚠️ {env_var} must be positive, using default: {default}")
                return default
            return value
        except ValueError:
            logger.warning(f"⚠️ Invalid {env_var}, using default: {default}")
            return default
    
    def get_available_account(self, stock_ticker: str = None, retry_count: int = 0) -> int:
        """
        Get the best available account for API calls
        
        Strategy:
        1. First try to find accounts under minute rate limit
        2. Then find accounts under daily rate limit
        3. Finally, find account with most remaining calls
        """
        MAX_RETRIES = 3
        
        with self._usage_lock:
            current_time = time.time()
            today = datetime.now().date()
            
            # Reset daily counters if needed
            for account_id in range(self.accounts_count):
                if self.account_usage[account_id]['last_reset'] != today:
                    self.account_usage[account_id]['daily_calls'] = 0
                    self.account_usage[account_id]['last_reset'] = today
            
            # Find accounts under minute rate limit
            available_accounts = []
            for account_id in range(self.accounts_count):
                rate_limit = self.account_rate_limits[account_id]
                
                # Reset minute counter if a minute has passed
                if current_time - rate_limit['last_call'] >= self.minute_reset:
                    rate_limit['calls_this_minute'] = 0
                
                # Check if under minute limit
                if rate_limit['calls_this_minute'] < self.calls_per_minute:
                    available_accounts.append(account_id)
            
            if not available_accounts:
                # Check retry limit to prevent infinite recursion
                if retry_count >= MAX_RETRIES:
                    logger.error(f"❌ All accounts rate limited after {MAX_RETRIES} retries. Raising exception.")
                    raise RuntimeError(f"All Finnhub accounts rate limited after {MAX_RETRIES} retries")
                
                # All accounts are rate limited, wait and retry
                logger.warning(f"⚠️ All accounts rate limited, retry {retry_count + 1}/{MAX_RETRIES}, waiting for reset...")
                time.sleep(self.rate_limit_sleep)
                return self.get_available_account(stock_ticker, retry_count + 1)
            
            # Find accounts under daily limit
            daily_available = [acc for acc in available_accounts 
                             if self.account_usage[acc]['daily_calls'] < self.calls_per_day]
            
            if daily_available:
                # Use account with most remaining daily calls
                best_account = max(daily_available, 
                                 key=lambda x: self.calls_per_day - self.account_usage[x]['daily_calls'])
                return best_account
            
            # Otherwise, find the account with the most remaining calls
            best_account = max(available_accounts, 
                             key=lambda x: self.calls_per_day - self.account_usage[x]['daily_calls'])
            return best_account
    
    def make_api_call(self, endpoint: str, params: Dict = None, stock_ticker: str = None) -> Optional[Dict]:
        """
        Make an API call using the best available account
        
        Args:
            endpoint: API endpoint (e.g., 'quote', 'analyst-recommendations')
            params: Query parameters
            stock_ticker: Stock ticker for logging purposes
        
        Returns:
            API response data or None if failed
        """
        import requests
        
        account_id = self.get_available_account(stock_ticker)
        api_key = self.api_keys[account_id]
        
        # Check rate limiting
        current_time = time.time()
        rate_limit = self.account_rate_limits[account_id]
        
        # Reset minute counter if a minute has passed
        if current_time - rate_limit['last_call'] >= self.minute_reset:
            rate_limit['calls_this_minute'] = 0
        
        # Check if we can make a call this minute
        if rate_limit['calls_this_minute'] >= self.calls_per_minute:
            # Wait until next minute
            wait_time = self.minute_reset - (current_time - rate_limit['last_call'])
            if wait_time > 0:
                logger.info(f"⏳ Account {account_id + 1} rate limited, waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                current_time = time.time()
                rate_limit['calls_this_minute'] = 0
        
        # Make the API call
        try:
            url = f"https://finnhub.io/api/v1/{endpoint}"
            if params is None:
                params = {}
            params['token'] = api_key
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            call_time = time.time() - start_time
            
            # Update usage tracking
            with self._usage_lock:
                self.account_usage[account_id]['daily_calls'] += 1
                rate_limit['calls_this_minute'] += 1
                rate_limit['last_call'] = current_time
                self.performance_metrics['calls_per_account'][account_id] += 1
                
                # Add call time with rolling window limit
                self.performance_metrics['api_call_times'].append(call_time)
                if len(self.performance_metrics['api_call_times']) > self.MAX_CALL_TIMES:
                    # Keep only the most recent call times
                    self.performance_metrics['api_call_times'] = self.performance_metrics['api_call_times'][-self.MAX_CALL_TIMES:]
            
            if response.status_code == 200:
                # Check if response has content before parsing
                if response.content:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and 'error' in data:
                            logger.error(f"API error from account {account_id + 1}: {data['error']}")
                            return None
                        
                        logger.debug(f"✅ API call successful from account {account_id + 1} in {call_time:.2f}s")
                        return data
                    except Exception as json_error:
                        logger.error(f"JSON parsing error from account {account_id + 1}: {json_error}")
                        return None
                else:
                    logger.warning(f"Empty response from account {account_id + 1}")
                    return None
            else:
                logger.error(f"❌ HTTP {response.status_code} from account {account_id + 1}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ API call failed from account {account_id + 1}: {e}")
            return None
    
    def get_analyst_recommendations(self, ticker: str) -> Optional[Dict]:
        """Get analyst recommendations using the multi-account system"""
        return self.make_api_call('analyst-recommendations', {'symbol': ticker}, ticker)
    
    def get_earnings_calendar(self, ticker: str) -> Optional[Dict]:
        """Get earnings calendar using the multi-account system"""
        return self.make_api_call('calendar/earnings', {'symbol': ticker}, ticker)
    
    def get_quote(self, ticker: str) -> Optional[Dict]:
        """Get quote data using the multi-account system"""
        return self.make_api_call('quote', {'symbol': ticker}, ticker)
    
    def get_company_profile(self, ticker: str) -> Optional[Dict]:
        """Get company profile using the multi-account system"""
        return self.make_api_call('stock/profile2', {'symbol': ticker}, ticker)
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        with self._usage_lock:
            total_calls = sum(self.performance_metrics['calls_per_account'].values())
            avg_call_time = (sum(self.performance_metrics['api_call_times']) / 
                           len(self.performance_metrics['api_call_times'])) if self.performance_metrics['api_call_times'] else 0
            
            return {
                'total_calls': total_calls,
                'calls_per_account': self.performance_metrics['calls_per_account'].copy(),
                'average_call_time': avg_call_time,
                'uptime': (datetime.now() - self.performance_metrics['start_time']).total_seconds(),
                'account_usage': self.account_usage.copy(),
                'rate_limits': self.account_rate_limits.copy()
            }
    
    def reset_daily_counters(self):
        """Reset daily call counters for all accounts"""
        with self._usage_lock:
            today = datetime.now().date()
            for account_id in range(self.accounts_count):
                self.account_usage[account_id]['daily_calls'] = 0
                self.account_usage[account_id]['last_reset'] = today
            logger.info("✅ Daily call counters reset for all accounts")
    
    def get_account_status(self) -> Dict:
        """Get detailed status of all accounts"""
        with self._usage_lock:
            current_time = time.time()
            status = {}
            
            for account_id in range(self.accounts_count):
                rate_limit = self.account_rate_limits[account_id]
                usage = self.account_usage[account_id]
                
                # Calculate remaining calls
                remaining_minute = max(0, self.calls_per_minute - rate_limit['calls_this_minute'])
                remaining_daily = max(0, self.calls_per_day - usage['daily_calls'])
                
                # Calculate time until reset
                time_since_last = current_time - rate_limit['last_call']
                time_until_reset = max(0, self.minute_reset - time_since_last) if rate_limit['calls_this_minute'] >= self.calls_per_minute else 0
                
                status[account_id] = {
                    'api_key': f"{self.api_keys[account_id][:8]}...",
                    'calls_this_minute': rate_limit['calls_this_minute'],
                    'calls_today': usage['daily_calls'],
                    'remaining_minute': remaining_minute,
                    'remaining_daily': remaining_daily,
                    'time_until_reset': time_until_reset,
                    'last_call': datetime.fromtimestamp(rate_limit['last_call']).strftime('%H:%M:%S'),
                    'status': 'available' if remaining_minute > 0 and remaining_daily > 0 else 'limited'
                }
            
            return status
    
    def close(self):
        """Clean up resources"""
        logger.info("🔒 FinnhubMultiAccountManager closed")
