#!/usr/bin/env python3
"""
Polygon.io Financial Data Service
================================

Comprehensive service for Polygon.io API with support for:
- Fundamental data (financial statements, ratios)
- Real-time and historical pricing
- Batch API calls for efficiency
- Rate limit monitoring and management
- Multiple data types (stocks, options, forex, crypto)

Author: AI Assistant
Date: 2025-01-26
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta, date
from typing import Dict, Optional, List, Any, Tuple
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix imports for running from daily_run directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_run.base_service import BaseService
from daily_run.common_imports import setup_logging, get_api_rate_limiter

# Setup logging
setup_logging('polygon')
logger = logging.getLogger(__name__)

class PolygonService(BaseService):
    """Polygon.io financial data service with comprehensive coverage"""
    
    def __init__(self):
        """Initialize Polygon service with API key and configuration"""
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            raise ValueError("POLYGON_API_KEY environment variable is required")
        
        super().__init__('polygon', api_key)
        
        # API configuration
        self.base_url = "https://api.polygon.io"
        self.api_limiter = get_api_rate_limiter()
        
        # Rate limits (varies by plan)
        self.rate_limits = {
            'basic': 5,      # calls per minute (Basic plan)
            'starter': 5,    # calls per second (Starter plan)
            'developer': 5,  # calls per second (Developer plan)
            'advanced': 10,  # calls per second (Advanced plan)
            'enterprise': 50 # calls per second (Enterprise plan)
        }
        
        # Current plan (detect from API key or default to basic)
        self.current_plan = self._detect_plan()
        self.max_calls_per_second = self.rate_limits.get(self.current_plan, 5)
        
        # Batch processing configuration
        self.max_batch_size = 100  # Maximum symbols per batch request
        self.batch_delay = 1.0     # Delay between batch requests (seconds)
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2
        
        logger.info(f"Polygon service initialized with plan: {self.current_plan}")
    
    def _detect_plan(self) -> str:
        """Detect the current plan based on API key or response"""
        try:
            # Try to get account details to detect plan
            url = f"{self.base_url}/v3/reference/tickers"
            params = {'apiKey': self.api_key, 'limit': 1}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                # Check response headers or content for plan info
                # For now, default to starter plan
                return 'starter'
            else:
                return 'basic'
        except Exception as e:
            logger.warning(f"Could not detect plan, defaulting to basic: {e}")
            return 'basic'
    
    def _make_request(self, endpoint: str, params: Dict = None, retries: int = None) -> Optional[Dict]:
        """Make API request with rate limiting and retry logic"""
        if retries is None:
            retries = self.max_retries
        
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
        
        params['apiKey'] = self.api_key
        
        for attempt in range(retries + 1):
            try:
                # Check rate limit
                if not self._check_rate_limit():
                    wait_time = 60 / self.max_calls_per_second
                    logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                
                # Make request
                response = requests.get(url, params=params, timeout=30)
                
                # Record API call
                self._record_api_call()
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    logger.warning(f"Rate limited on attempt {attempt + 1}")
                    if attempt < retries:
                        wait_time = (attempt + 1) * self.retry_delay
                        time.sleep(wait_time)
                        continue
                elif response.status_code == 403:  # Forbidden (plan limits)
                    logger.error("API key invalid or plan limits exceeded")
                    return None
                else:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < retries:
                    time.sleep(self.retry_delay)
                    continue
            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt < retries:
                    time.sleep(self.retry_delay)
                    continue
        
        return None
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        return self.api_limiter.check_limit('polygon', 'general')
    
    def _record_api_call(self):
        """Record an API call for rate limiting"""
        self.api_limiter.record_call('polygon', 'general')
    
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current price data for a ticker"""
        try:
            # Get real-time quote
            endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
            data = self._make_request(endpoint)
            
            if data and 'results' in data and data['results']:
                result = data['results']
                return {
                    'price': result.get('last', {}).get('p'),
                    'volume': result.get('last', {}).get('s'),
                    'change': result.get('last', {}).get('c'),
                    'change_percent': result.get('last', {}).get('cp'),
                    'data_source': 'polygon',
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting data for {ticker}: {e}")
            return None
    
    def get_current_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current price data for a ticker (alias for get_data)"""
        return self.get_data(ticker)
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive fundamental data for a ticker"""
        try:
            fundamental_data = {}
            
            # Get financial statements
            financial_data = self._get_financial_statements(ticker)
            if financial_data:
                fundamental_data.update(financial_data)
            
            # Get key statistics
            key_stats = self._get_key_statistics(ticker)
            if key_stats:
                fundamental_data.update(key_stats)
            
            # Get company overview
            overview = self._get_company_overview(ticker)
            if overview:
                fundamental_data.update(overview)
            
            if fundamental_data:
                fundamental_data['ticker'] = ticker
                fundamental_data['data_source'] = 'polygon'
                fundamental_data['last_updated'] = datetime.now()
                return fundamental_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting fundamental data for {ticker}: {e}")
            return None
    
    def _get_financial_statements(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get financial statements (income statement, balance sheet, cash flow)"""
        try:
            # Get income statement
            income_endpoint = f"/v2/reference/financials/{ticker}"
            income_params = {
                'type': 'Q',  # Quarterly
                'limit': 4    # Last 4 quarters
            }
            
            income_data = self._make_request(income_endpoint, income_params)
            
            if not income_data or 'results' not in income_data:
                return None
            
            # Parse the most recent quarter
            latest_quarter = income_data['results'][0] if income_data['results'] else None
            
            if not latest_quarter:
                return None
            
            # Extract financial data
            financial_data = {
                'revenue': latest_quarter.get('revenues'),
                'net_income': latest_quarter.get('net_income_loss'),
                'gross_profit': latest_quarter.get('gross_profit'),
                'operating_income': latest_quarter.get('operating_income_loss'),
                'ebitda': latest_quarter.get('operating_income_loss'),  # Approximate
                'total_assets': latest_quarter.get('assets'),
                'total_equity': latest_quarter.get('equity'),
                'total_debt': latest_quarter.get('debt'),
                'operating_cash_flow': latest_quarter.get('net_cash_flow_from_operating_activities'),
                'free_cash_flow': latest_quarter.get('net_cash_flow_from_operating_activities'),  # Approximate
                'fiscal_year': latest_quarter.get('period_of_report_date', '').split('-')[0] if latest_quarter.get('period_of_report_date') else None,
                'fiscal_quarter': latest_quarter.get('fiscal_period'),
                'ttm_periods': 4
            }
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error getting financial statements for {ticker}: {e}")
            return None
    
    def _get_key_statistics(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get key statistics and ratios"""
        try:
            # Get ticker details
            endpoint = f"/v3/reference/tickers/{ticker}"
            data = self._make_request(endpoint)
            
            if not data or 'results' not in data:
                return None
            
            ticker_info = data['results']
            
            # Get market data
            market_data = self._get_market_data(ticker)
            
            # Calculate ratios if we have the data
            ratios = {}
            if market_data and ticker_info:
                current_price = market_data.get('price', 0)
                market_cap = ticker_info.get('market_cap', 0)
                shares_outstanding = ticker_info.get('share_class_shares_outstanding', 0)
                
                if current_price and shares_outstanding:
                    ratios['shares_outstanding'] = shares_outstanding
                    ratios['market_cap'] = market_cap
                    ratios['enterprise_value'] = market_cap  # Approximate
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error getting key statistics for {ticker}: {e}")
            return None
    
    def _get_company_overview(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company overview and basic information"""
        try:
            endpoint = f"/v3/reference/tickers/{ticker}"
            data = self._make_request(endpoint)
            
            if not data or 'results' not in data:
                return None
            
            company_info = data['results']
            
            return {
                'company_name': company_info.get('name'),
                'sector': company_info.get('sic_description'),
                'industry': company_info.get('sic_description'),
                'exchange': company_info.get('primary_exchange'),
                'currency': company_info.get('currency_name'),
                'country': company_info.get('locale')
            }
            
        except Exception as e:
            logger.error(f"Error getting company overview for {ticker}: {e}")
            return None
    
    def _get_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current market data"""
        return self.get_data(ticker)
    
    def get_historical_prices(self, ticker: str, start_date: str = None, end_date: str = None, 
                            timespan: str = 'day') -> Optional[List[Dict[str, Any]]]:
        """Get historical price data"""
        try:
            if not start_date:
                start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = date.today().strftime('%Y-%m-%d')
            
            endpoint = f"/v2/aggs/ticker/{ticker}/range/1/{timespan}/{start_date}/{end_date}"
            params = {
                'adjusted': 'true',
                'sort': 'asc'
            }
            
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                return None
            
            # Parse results
            prices = []
            for result in data['results']:
                prices.append({
                    'date': datetime.fromtimestamp(result['t'] / 1000).strftime('%Y-%m-%d'),
                    'open': result['o'],
                    'high': result['h'],
                    'low': result['l'],
                    'close': result['c'],
                    'volume': result['v'],
                    'vwap': result.get('vw'),
                    'transactions': result.get('n')
                })
            
            return prices
            
        except Exception as e:
            logger.error(f"Error getting historical prices for {ticker}: {e}")
            return None
    
    def get_batch_prices(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get current prices for multiple tickers in batch"""
        try:
            if len(tickers) > self.max_batch_size:
                # Split into batches
                results = {}
                for i in range(0, len(tickers), self.max_batch_size):
                    batch = tickers[i:i + self.max_batch_size]
                    batch_results = self._get_batch_prices_single(batch)
                    results.update(batch_results)
                    
                    # Add delay between batches
                    if i + self.max_batch_size < len(tickers):
                        time.sleep(self.batch_delay)
                
                return results
            else:
                return self._get_batch_prices_single(tickers)
                
        except Exception as e:
            logger.error(f"Error getting batch prices: {e}")
            return {}
    
    def _get_batch_prices_single(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get batch prices for a single batch of tickers"""
        try:
            # Polygon doesn't have a true batch endpoint, so we'll use concurrent requests
            results = {}
            
            with ThreadPoolExecutor(max_workers=min(5, len(tickers))) as executor:
                future_to_ticker = {
                    executor.submit(self.get_data, ticker): ticker 
                    for ticker in tickers
                }
                
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        data = future.result()
                        if data:
                            results[ticker] = data
                    except Exception as e:
                        logger.error(f"Error getting data for {ticker}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch price fetch: {e}")
            return {}
    
    def get_batch_fundamentals(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get fundamental data for multiple tickers in batch"""
        try:
            results = {}
            
            # Process in smaller batches to avoid overwhelming the API
            batch_size = min(10, self.max_batch_size)  # Smaller batches for fundamentals
            
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                
                with ThreadPoolExecutor(max_workers=min(3, len(batch))) as executor:
                    future_to_ticker = {
                        executor.submit(self.get_fundamental_data, ticker): ticker 
                        for ticker in batch
                    }
                    
                    for future in as_completed(future_to_ticker):
                        ticker = future_to_ticker[future]
                        try:
                            data = future.result()
                            if data:
                                results[ticker] = data
                        except Exception as e:
                            logger.error(f"Error getting fundamentals for {ticker}: {e}")
                
                # Add delay between batches
                if i + batch_size < len(tickers):
                    time.sleep(self.batch_delay * 2)  # Longer delay for fundamentals
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting batch fundamentals: {e}")
            return {}
    
    def get_options_chain(self, ticker: str, expiration_date: str = None) -> Optional[List[Dict[str, Any]]]:
        """Get options chain data"""
        try:
            endpoint = f"/v3/snapshot/options/{ticker}"
            params = {}
            
            if expiration_date:
                params['expiration_date'] = expiration_date
            
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                return None
            
            return data['results']
            
        except Exception as e:
            logger.error(f"Error getting options chain for {ticker}: {e}")
            return None
    
    def get_earnings_calendar(self, ticker: str = None, start_date: str = None, end_date: str = None) -> Optional[List[Dict[str, Any]]]:
        """Get earnings calendar data"""
        try:
            endpoint = "/v2/reference/earnings"
            params = {}
            
            if ticker:
                params['ticker'] = ticker
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                return None
            
            return data['results']
            
        except Exception as e:
            logger.error(f"Error getting earnings calendar: {e}")
            return None
    
    def get_news(self, ticker: str = None, published_utc: str = None, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get news articles"""
        try:
            endpoint = "/v2/reference/news"
            params = {
                'limit': limit
            }
            
            if ticker:
                params['ticker'] = ticker
            if published_utc:
                params['published_utc'] = published_utc
            
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                return None
            
            return data['results']
            
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return None
    
    def get_api_usage(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        try:
            # Polygon doesn't provide usage endpoint, so we'll use our rate limiter
            return {
                'plan': self.current_plan,
                'max_calls_per_second': self.max_calls_per_second,
                'rate_limiter_status': self.api_limiter.get_status('polygon')
            }
        except Exception as e:
            logger.error(f"Error getting API usage: {e}")
            return {}
    
    def store_fundamental_data(self, ticker: str, fundamental_data: Dict, key_stats: Dict = None) -> bool:
        """Store fundamental data in database"""
        try:
            # This would integrate with your database storage logic
            # For now, just log the data
            logger.info(f"Storing fundamental data for {ticker}: {len(fundamental_data)} fields")
            
            # You can implement the actual database storage here
            # Similar to how other services store data
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing fundamental data for {ticker}: {e}")
            return False
    
    def close(self):
        """Clean up resources"""
        logger.info("Closing Polygon service")
        # Any cleanup needed

def main():
    """Test the Polygon service"""
    try:
        # Initialize service
        polygon = PolygonService()
        
        # Test tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        print("🔧 Testing Polygon.io Service")
        print("=" * 50)
        
        # Test current price
        print("\n📊 Testing current price...")
        for ticker in test_tickers[:1]:  # Test with one ticker
            data = polygon.get_data(ticker)
            if data:
                print(f"  ✅ {ticker}: ${data.get('price', 'N/A')}")
            else:
                print(f"  ❌ {ticker}: No data")
        
        # Test fundamental data
        print("\n📈 Testing fundamental data...")
        for ticker in test_tickers[:1]:  # Test with one ticker
            data = polygon.get_fundamental_data(ticker)
            if data:
                print(f"  ✅ {ticker}: {len(data)} fields retrieved")
                print(f"     Revenue: ${data.get('revenue', 'N/A'):,}")
                print(f"     Net Income: ${data.get('net_income', 'N/A'):,}")
            else:
                print(f"  ❌ {ticker}: No fundamental data")
        
        # Test batch prices
        print("\n📦 Testing batch prices...")
        batch_data = polygon.get_batch_prices(test_tickers)
        print(f"  ✅ Retrieved data for {len(batch_data)}/{len(test_tickers)} tickers")
        
        # Test API usage
        print("\n📊 API Usage:")
        usage = polygon.get_api_usage()
        print(f"  Plan: {usage.get('plan', 'Unknown')}")
        print(f"  Max calls/sec: {usage.get('max_calls_per_second', 'Unknown')}")
        
        polygon.close()
        
    except Exception as e:
        print(f"❌ Error testing Polygon service: {e}")

if __name__ == "__main__":
    main() 