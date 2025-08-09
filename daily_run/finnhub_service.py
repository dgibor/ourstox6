"""
Finnhub Service

Modern Finnhub API service with rate limiting and error handling.
Free tier: 60 API calls per minute.
"""

import logging
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import os

try:
    from .database import DatabaseManager
except ImportError:
    from database import DatabaseManager
try:
    from .error_handler import ErrorHandler
except ImportError:
    from error_handler import ErrorHandler
from utility_functions.api_rate_limiter import APIRateLimiter

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FinnhubService:
    """
    Finnhub API service with intelligent rate limiting
    
    Features:
    - 60 calls per minute rate limiting (free tier)
    - Real-time pricing data
    - Basic fundamental data
    - Company profiles and news
    - Automatic error handling and retries
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.error_handler = ErrorHandler("finnhub_service")
        self.service_name = "Finnhub"
        self.logger = logging.getLogger("finnhub_service")
        
        # API configuration
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        
        # Use robust DB-backed rate limiter
        self.rate_limiter = APIRateLimiter()
        self.endpoint = 'quote'  # Default endpoint, can be overridden per call
        
        if not self.api_key:
            self.logger.warning("⚠️ Finnhub API key not found - service will be limited")
        else:
            self.logger.info("Finnhub service initialized")
    
    def __del__(self):
        if hasattr(self, 'rate_limiter'):
            self.rate_limiter.close()
    
    def _make_request(self, endpoint: str, **params) -> Optional[Dict[str, Any]]:
        """Make a rate-limited API request using DB-backed limiter"""
        if not self.api_key:
            self.logger.error("No API key available")
            return None
        # Check rate limit before making the call
        if not self.rate_limiter.check_limit('finnhub', endpoint):
            self.logger.warning(f"Finnhub API rate limit reached for endpoint {endpoint}. Waiting...")
            # Optionally, you can sleep until next available time or just return None
            time.sleep(1)  # Sleep 1 second and try again (simple backoff)
            if not self.rate_limiter.check_limit('finnhub', endpoint):
                self.logger.error(f"Still over Finnhub rate limit for endpoint {endpoint}. Skipping call.")
                return None
        url = f"{self.base_url}/{endpoint}"
        params['token'] = self.api_key
        try:
            response = requests.get(url, params=params, timeout=30)
            self.rate_limiter.record_call('finnhub', endpoint)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'error' in data:
                    self.logger.error(f"API error: {data['error']}")
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
            
            data = self._make_request('quote', symbol=ticker)
            if not data:
                return None
            
            # Finnhub quote response format
            if 'c' not in data or data['c'] <= 0:
                return None
            
            return {
                'ticker': ticker,
                'price': float(data['c']),  # Current price
                'open': float(data.get('o', 0)),  # Open price
                'high': float(data.get('h', 0)),  # High price
                'low': float(data.get('l', 0)),   # Low price
                'previous_close': float(data.get('pc', 0)),  # Previous close
                'change': float(data.get('d', 0)),  # Change
                'change_percent': float(data.get('dp', 0)),  # Change percent
                'volume': int(data.get('v', 0)) if data.get('v') else 0,  # Volume (from daily data)
                'data_source': 'finnhub',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching pricing data for {ticker}: {e}")
            return None
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get basic fundamental data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with fundamental data or None if failed
        """
        try:
            self.logger.debug(f"Fetching fundamental data for {ticker}")
            
            # Get company profile
            profile_data = self._make_request('stock/profile2', symbol=ticker)
            if not profile_data:
                return None
            
            # Get basic financials (annual)
            financials_data = self._make_request('stock/metric', symbol=ticker, metric='all')
            
            fundamental_data = {
                'ticker': ticker,
                'company_name': profile_data.get('name'),
                'industry': profile_data.get('finnhubIndustry'),
                'country': profile_data.get('country'),
                'currency': profile_data.get('currency'),
                'exchange': profile_data.get('exchange'),
                'market_cap': profile_data.get('marketCapitalization'),
                'shares_outstanding': profile_data.get('shareOutstanding'),
                'ipo_date': profile_data.get('ipo'),
                'website': profile_data.get('weburl'),
                'logo': profile_data.get('logo'),
                'data_source': 'finnhub',
                'timestamp': datetime.now()
            }
            
            # Add financial metrics if available
            if financials_data and 'metric' in financials_data:
                metrics = financials_data['metric']
                fundamental_data.update({
                    'pe_ratio': self._safe_numeric(metrics.get('peBasicExclExtraTTM')),
                    'pb_ratio': self._safe_numeric(metrics.get('pbQuarterly')),
                    'ps_ratio': self._safe_numeric(metrics.get('psQuarterly')),
                    'ev_ebitda': self._safe_numeric(metrics.get('evEbitdaTTM')),
                    'profit_margin': self._safe_numeric(metrics.get('netProfitMarginTTM')),
                    'operating_margin': self._safe_numeric(metrics.get('operatingMarginTTM')),
                    'roe': self._safe_numeric(metrics.get('roeTTM')),
                    'roa': self._safe_numeric(metrics.get('roaTTM')),
                    'debt_to_equity': self._safe_numeric(metrics.get('totalDebtToEquity')),
                    'current_ratio': self._safe_numeric(metrics.get('currentRatioQuarterly')),
                    'quick_ratio': self._safe_numeric(metrics.get('quickRatioQuarterly')),
                    'beta': self._safe_numeric(metrics.get('beta')),
                })
            
            return fundamental_data
            
        except Exception as e:
            self.logger.error(f"Error fetching fundamental data for {ticker}: {e}")
            return None
    
    def get_batch_data(self, tickers: List[str], data_type: str = 'pricing') -> Dict[str, Dict[str, Any]]:
        """
        Get data for multiple tickers
        
        Args:
            tickers: List of ticker symbols
            data_type: 'pricing' or 'fundamentals'
            
        Returns:
            Dict mapping ticker to data
        """
        results = {}
        
        self.logger.info(f"Processing {len(tickers)} tickers with Finnhub")
        
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
    
    def get_company_news(self, ticker: str, from_date: str = None, to_date: str = None) -> List[Dict[str, Any]]:
        """
        Get company news
        
        Args:
            ticker: Stock ticker symbol
            from_date: Start date (YYYY-MM-DD format)
            to_date: End date (YYYY-MM-DD format)
            
        Returns:
            List of news articles
        """
        try:
            params = {'symbol': ticker}
            
            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date
            
            data = self._make_request('company-news', **params)
            
            if data and isinstance(data, list):
                return [{
                    'headline': article.get('headline'),
                    'summary': article.get('summary'),
                    'url': article.get('url'),
                    'datetime': datetime.fromtimestamp(article.get('datetime', 0)),
                    'source': article.get('source'),
                    'image': article.get('image')
                } for article in data[:10]]  # Limit to 10 articles
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching news for {ticker}: {e}")
            return []
    
    def _safe_numeric(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == 'None' or value == '-' or pd.isna(value):
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def check_service_health(self) -> bool:
        """
        Check if Finnhub service is available
        
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
                self.logger.info("✅ Finnhub service health check passed")
                return True
            else:
                self.logger.warning("⚠️ Finnhub service health check failed - no data")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Finnhub service health check failed: {e}")
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
                'requests_per_minute': self.rate_limiter.get_rate_limit('finnhub', 'quote'),
                'daily_limit': None  # No daily limit on free tier
            },
            'capabilities': [
                'real_time_pricing',
                'basic_fundamental_data',
                'company_profiles',
                'financial_metrics',
                'company_news'
            ],
            'data_types': [
                'pricing',
                'fundamentals',
                'company_info',
                'news'
            ],
            'coverage': [
                'US_stocks',
                'international_stocks',
                'forex',
                'crypto'
            ],
            'cost_per_call': 0.0,
            'reliability_score': 0.80,
            'batch_limit': 1  # No native batch support
        } 