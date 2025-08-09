"""
Alpha Vantage Service

Modern Alpha Vantage API service with rate limiting and error handling.
Free tier: 5 API calls per minute, 100 calls per day.
"""

import logging
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import os

from database import DatabaseManager
from error_handler import ErrorHandler

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AlphaVantageService:
    """
    Alpha Vantage API service with intelligent rate limiting
    
    Features:
    - 5 calls per minute rate limiting (free tier)
    - Comprehensive fundamental data
    - Real-time and historical pricing
    - Automatic error handling and retries
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.error_handler = ErrorHandler("alpha_vantage_service")
        self.service_name = "Alpha Vantage"
        self.logger = logging.getLogger("alpha_vantage_service")
        
        # API configuration
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        
        # Rate limiting (free tier)
        self.calls_per_minute = 5
        self.calls_per_day = 100
        self.delay_between_requests = 12.0  # 60 seconds / 5 calls = 12 seconds
        
        # Track API usage
        self.call_history = []
        self.daily_calls = 0
        self.last_reset_date = datetime.now().date()
        
        if not self.api_key:
            self.logger.warning("⚠️ Alpha Vantage API key not found - service will be limited")
        else:
            self.logger.info("Alpha Vantage service initialized")
    
    def _check_rate_limit(self) -> bool:
        """Check if we can make an API call within rate limits"""
        now = datetime.now()
        
        # Reset daily counter if new day
        if now.date() > self.last_reset_date:
            self.daily_calls = 0
            self.last_reset_date = now.date()
        
        # Check daily limit
        if self.daily_calls >= self.calls_per_day:
            self.logger.warning(f"Daily limit reached ({self.calls_per_day} calls)")
            return False
        
        # Check minute limit
        minute_ago = now - timedelta(minutes=1)
        recent_calls = [call for call in self.call_history if call > minute_ago]
        
        if len(recent_calls) >= self.calls_per_minute:
            self.logger.warning(f"Minute limit reached ({self.calls_per_minute} calls/min)")
            return False
        
        return True
    
    def _record_api_call(self):
        """Record an API call for rate limiting"""
        now = datetime.now()
        self.call_history.append(now)
        self.daily_calls += 1
        
        # Keep only last hour of call history
        hour_ago = now - timedelta(hours=1)
        self.call_history = [call for call in self.call_history if call > hour_ago]
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        if not self._check_rate_limit():
            self.logger.info(f"Waiting {self.delay_between_requests} seconds for rate limit...")
            time.sleep(self.delay_between_requests)
    
    def _make_request(self, function: str, symbol: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make a rate-limited API request"""
        if not self.api_key:
            self.logger.error("No API key available")
            return None
        
        self._wait_for_rate_limit()
        
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            **kwargs
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            self._record_api_call()
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API limit messages
                if 'Information' in data:
                    info_msg = data['Information']
                    if 'rate limit' in info_msg.lower() or '5 calls per minute' in info_msg:
                        self.logger.warning("Rate limit hit - backing off")
                        time.sleep(self.delay_between_requests)
                        return None
                
                return data
            else:
                self.logger.error(f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"API request failed: {e}")
            return None
    
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get current pricing data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with pricing data or None if failed
        """
        try:
            self.logger.debug(f"Fetching pricing data for {ticker}")
            
            data = self._make_request('GLOBAL_QUOTE', ticker)
            if not data or 'Global Quote' not in data:
                return None
            
            quote = data['Global Quote']
            if not quote:
                return None
            
            return {
                'ticker': ticker,
                'price': float(quote.get('05. price', 0)),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'volume': int(quote.get('06. volume', 0)) if quote.get('06. volume') else 0,
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching pricing data for {ticker}: {e}")
            return None
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with fundamental data or None if failed
        """
        try:
            self.logger.debug(f"Fetching fundamental data for {ticker}")
            
            # Get company overview (includes key metrics)
            overview_data = self._make_request('OVERVIEW', ticker)
            if not overview_data:
                return None
            
            # Extract fundamental metrics
            fundamental_data = {
                'ticker': ticker,
                'market_cap': self._safe_numeric(overview_data.get('MarketCapitalization')),
                'revenue_ttm': self._safe_numeric(overview_data.get('RevenueTTM')),
                'gross_profit_ttm': self._safe_numeric(overview_data.get('GrossProfitTTM')),
                'net_income_ttm': self._safe_numeric(overview_data.get('NetIncome')),
                'ebitda': self._safe_numeric(overview_data.get('EBITDA')),
                'pe_ratio': self._safe_numeric(overview_data.get('PERatio')),
                'peg_ratio': self._safe_numeric(overview_data.get('PEGRatio')),
                'pb_ratio': self._safe_numeric(overview_data.get('PriceToBookRatio')),
                'ps_ratio': self._safe_numeric(overview_data.get('PriceToSalesRatioTTM')),
                'ev_revenue': self._safe_numeric(overview_data.get('EVToRevenue')),
                'ev_ebitda': self._safe_numeric(overview_data.get('EVToEBITDA')),
                'profit_margin': self._safe_numeric(overview_data.get('ProfitMargin')),
                'operating_margin': self._safe_numeric(overview_data.get('OperatingMarginTTM')),
                'roe': self._safe_numeric(overview_data.get('ReturnOnEquityTTM')),
                'roa': self._safe_numeric(overview_data.get('ReturnOnAssetsTTM')),
                'debt_to_equity': self._safe_numeric(overview_data.get('DebtToEquity')),
                'current_ratio': self._safe_numeric(overview_data.get('CurrentRatio')),
                'quick_ratio': self._safe_numeric(overview_data.get('QuickRatio')),
                'book_value': self._safe_numeric(overview_data.get('BookValue')),
                'shares_outstanding': self._safe_numeric(overview_data.get('SharesOutstanding')),
                'dividend_yield': self._safe_numeric(overview_data.get('DividendYield')),
                'beta': self._safe_numeric(overview_data.get('Beta')),
                'eps_ttm': self._safe_numeric(overview_data.get('EPS')),
                'data_source': 'alpha_vantage',
                'timestamp': datetime.now()
            }
            
            return fundamental_data
            
        except Exception as e:
            self.logger.error(f"Error fetching fundamental data for {ticker}: {e}")
            return None
    
    def get_batch_data(self, tickers: List[str], data_type: str = 'pricing') -> Dict[str, Dict[str, Any]]:
        """
        Get data for multiple tickers (sequential due to rate limits)
        
        Args:
            tickers: List of ticker symbols
            data_type: 'pricing' or 'fundamentals'
            
        Returns:
            Dict mapping ticker to data
        """
        results = {}
        
        # Alpha Vantage doesn't support batch requests, so we process sequentially
        self.logger.info(f"Processing {len(tickers)} tickers sequentially (rate limited)")
        
        for ticker in tickers:
            try:
                if data_type == 'pricing':
                    data = self.get_data(ticker)
                else:
                    data = self.get_fundamental_data(ticker)
                
                if data:
                    results[ticker] = data
                    
            except Exception as e:
                self.logger.error(f"Error processing {ticker}: {e}")
        
        self.logger.info(f"Successfully processed {len(results)}/{len(tickers)} tickers")
        return results
    
    def _safe_numeric(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == 'None' or value == '-':
            return None
        
        try:
            # Handle percentage strings
            if isinstance(value, str) and '%' in value:
                return float(value.replace('%', '')) / 100
            
            # Handle strings with units (e.g., "1.5B")
            if isinstance(value, str):
                value = value.replace(',', '')
                multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}
                for suffix, mult in multipliers.items():
                    if value.endswith(suffix):
                        return float(value[:-1]) * mult
            
            return float(value)
            
        except (ValueError, TypeError):
            return None
    
    def check_service_health(self) -> bool:
        """
        Check if Alpha Vantage service is available
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if not self.api_key:
                self.logger.warning("⚠️ No API key - service not available")
                return False
            
            # Test with a simple quote request
            data = self.get_data("AAPL")
            
            if data and data.get('price'):
                self.logger.info("✅ Alpha Vantage service health check passed")
                return True
            else:
                self.logger.warning("⚠️ Alpha Vantage service health check failed - no data")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Alpha Vantage service health check failed: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about this service
        
        Returns:
            Dict with service information
        """
        return {
            'name': self.service_name,
            'type': 'freemium',
            'api_key_required': True,
            'rate_limits': {
                'requests_per_minute': self.calls_per_minute,
                'requests_per_day': self.calls_per_day
            },
            'capabilities': [
                'real_time_pricing',
                'fundamental_data',
                'company_overview',
                'key_ratios',
                'financial_metrics'
            ],
            'data_types': [
                'pricing',
                'fundamentals',
                'ratios',
                'overview'
            ],
            'coverage': [
                'US_stocks',
                'international_stocks',
                'forex',
                'crypto'
            ],
            'cost_per_call': 0.0,
            'reliability_score': 0.85,
            'batch_limit': 1,  # No native batch support
            'daily_usage': self.daily_calls,
            'daily_limit': self.calls_per_day
        } 