"""
Polygon.io Service

Premium financial data service with high rate limits and institutional-quality data.
Paid tier: High rate limits, batch processing, comprehensive coverage.
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


class PolygonService:
    """
    Polygon.io API service with high-performance data access
    
    Features:
    - High rate limits (5 requests per second for paid plans)
    - Institutional-quality data
    - Real-time and historical pricing
    - Advanced fundamental data
    - Batch processing capabilities
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.error_handler = ErrorHandler("polygon_service")
        self.service_name = "Polygon.io"
        self.logger = logging.getLogger("polygon_service")
        
        # API configuration
        self.api_key = os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io"
        
        # Rate limiting (paid tier - 5 requests per second)
        self.calls_per_second = 5
        self.delay_between_requests = 0.2  # 1 second / 5 calls = 0.2 seconds
        
        # Track API usage
        self.call_history = []
        
        if not self.api_key:
            self.logger.warning("⚠️ Polygon.io API key not found - service will be limited")
        else:
            self.logger.info("✅ Polygon.io service initialized")
    
    def _check_rate_limit(self) -> bool:
        """Check if we can make an API call within rate limits"""
        now = datetime.now()
        
        # Check second limit
        second_ago = now - timedelta(seconds=1)
        recent_calls = [call for call in self.call_history if call > second_ago]
        
        if len(recent_calls) >= self.calls_per_second:
            return False
        
        return True
    
    def _record_api_call(self):
        """Record an API call for rate limiting"""
        now = datetime.now()
        self.call_history.append(now)
        
        # Keep only last minute of call history
        minute_ago = now - timedelta(minutes=1)
        self.call_history = [call for call in self.call_history if call > minute_ago]
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        if not self._check_rate_limit():
            time.sleep(self.delay_between_requests)
    
    def _make_request(self, endpoint: str, **params) -> Optional[Dict[str, Any]]:
        """Make a rate-limited API request"""
        if not self.api_key:
            self.logger.error("No API key available")
            return None
        
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=30)
            self._record_api_call()
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if data.get('status') == 'ERROR':
                    self.logger.error(f"API error: {data.get('error')}")
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
            
            # Get real-time quote
            data = self._make_request(f'v1/last/stocks/{ticker}')
            if not data or 'last' not in data:
                return None
            
            last = data['last']
            
            # Get daily open/high/low data
            today = datetime.now().strftime('%Y-%m-%d')
            daily_data = self._make_request(f'v1/open-close/{ticker}/{today}')
            
            result = {
                'ticker': ticker,
                'price': float(last.get('price', 0)),
                'volume': int(last.get('size', 0)),
                'timestamp_exchange': last.get('timestamp'),
                'data_source': 'polygon',
                'timestamp': datetime.now()
            }
            
            # Add daily data if available
            if daily_data and 'open' in daily_data:
                result.update({
                    'open': float(daily_data.get('open', 0)),
                    'high': float(daily_data.get('high', 0)),
                    'low': float(daily_data.get('low', 0)),
                    'close': float(daily_data.get('close', 0)),
                    'volume_daily': int(daily_data.get('volume', 0))
                })
            
            return result
            
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
            
            # Get company details
            details_data = self._make_request(f'v3/reference/tickers/{ticker}')
            if not details_data or 'results' not in details_data:
                return None
            
            results = details_data['results']
            
            # Get financials (annual)
            financials_data = self._make_request(
                f'vX/reference/financials',
                ticker=ticker,
                timeframe='annual',
                limit=1
            )
            
            fundamental_data = {
                'ticker': ticker,
                'company_name': results.get('name'),
                'description': results.get('description'),
                'market': results.get('market'),
                'locale': results.get('locale'),
                'primary_exchange': results.get('primary_exchange'),
                'type': results.get('type'),
                'currency_name': results.get('currency_name'),
                'cik': results.get('cik'),
                'composite_figi': results.get('composite_figi'),
                'share_class_figi': results.get('share_class_figi'),
                'market_cap': results.get('market_cap'),
                'phone_number': results.get('phone_number'),
                'address': self._format_address(results.get('address', {})),
                'homepage_url': results.get('homepage_url'),
                'total_employees': results.get('total_employees'),
                'list_date': results.get('list_date'),
                'branding': results.get('branding', {}),
                'share_class_shares_outstanding': results.get('share_class_shares_outstanding'),
                'weighted_shares_outstanding': results.get('weighted_shares_outstanding'),
                'data_source': 'polygon',
                'timestamp': datetime.now()
            }
            
            # Add financial data if available
            if financials_data and 'results' in financials_data and financials_data['results']:
                financial_result = financials_data['results'][0]
                financials = financial_result.get('financials', {})
                
                # Income statement
                income_statement = financials.get('income_statement', {})
                fundamental_data.update({
                    'revenue': self._safe_numeric(income_statement.get('revenue', {}).get('value')),
                    'cost_of_revenue': self._safe_numeric(income_statement.get('cost_of_revenue', {}).get('value')),
                    'gross_profit': self._safe_numeric(income_statement.get('gross_profit', {}).get('value')),
                    'operating_income': self._safe_numeric(income_statement.get('operating_income', {}).get('value')),
                    'net_income': self._safe_numeric(income_statement.get('net_income_loss', {}).get('value')),
                    'interest_expense': self._safe_numeric(income_statement.get('interest_expense', {}).get('value')),
                })
                
                # Balance sheet
                balance_sheet = financials.get('balance_sheet', {})
                fundamental_data.update({
                    'total_assets': self._safe_numeric(balance_sheet.get('assets', {}).get('value')),
                    'current_assets': self._safe_numeric(balance_sheet.get('current_assets', {}).get('value')),
                    'total_liabilities': self._safe_numeric(balance_sheet.get('liabilities', {}).get('value')),
                    'current_liabilities': self._safe_numeric(balance_sheet.get('current_liabilities', {}).get('value')),
                    'equity': self._safe_numeric(balance_sheet.get('equity', {}).get('value')),
                })
                
                # Cash flow
                cash_flow = financials.get('cash_flow_statement', {})
                fundamental_data.update({
                    'operating_cash_flow': self._safe_numeric(cash_flow.get('net_cash_flow_from_operating_activities', {}).get('value')),
                    'investing_cash_flow': self._safe_numeric(cash_flow.get('net_cash_flow_from_investing_activities', {}).get('value')),
                    'financing_cash_flow': self._safe_numeric(cash_flow.get('net_cash_flow_from_financing_activities', {}).get('value')),
                })
            
            return fundamental_data
            
        except Exception as e:
            self.logger.error(f"Error fetching fundamental data for {ticker}: {e}")
            return None
    
    def get_batch_data(self, tickers: List[str], data_type: str = 'pricing') -> Dict[str, Dict[str, Any]]:
        """
        Get data for multiple tickers with batch processing
        
        Args:
            tickers: List of ticker symbols (up to 100)
            data_type: 'pricing' or 'fundamentals'
            
        Returns:
            Dict mapping ticker to data
        """
        results = {}
        
        if len(tickers) > 100:
            self.logger.warning(f"Too many tickers ({len(tickers)}), limiting to first 100")
            tickers = tickers[:100]
        
        self.logger.info(f"Processing {len(tickers)} tickers with Polygon.io batch processing")
        
        if data_type == 'pricing':
            # Polygon supports grouped daily bars for batch pricing
            today = datetime.now().strftime('%Y-%m-%d')
            batch_data = self._make_request(
                f'v2/aggs/grouped/locale/us/market/stocks/{today}',
                adjusted='true',
                include_otc='false'
            )
            
            if batch_data and 'results' in batch_data:
                for result in batch_data['results']:
                    ticker = result.get('T')
                    if ticker in tickers:
                        results[ticker] = {
                            'ticker': ticker,
                            'price': float(result.get('c', 0)),  # Close price
                            'open': float(result.get('o', 0)),
                            'high': float(result.get('h', 0)),
                            'low': float(result.get('l', 0)),
                            'volume': int(result.get('v', 0)),
                            'vwap': float(result.get('vw', 0)),
                            'timestamp': result.get('t'),
                            'transactions': result.get('n'),
                            'data_source': 'polygon',
                            'timestamp': datetime.now()
                        }
        else:
            # For fundamentals, process individually (no batch API)
            for ticker in tickers:
                try:
                    data = self.get_fundamental_data(ticker)
                    if data:
                        results[ticker] = data
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {e}")
        
        self.logger.info(f"Successfully processed {len(results)}/{len(tickers)} tickers")
        return results
    
    def get_historical_data(self, ticker: str, days: int = 100) -> Optional[list]:
        """
        Fetch historical daily price data for a ticker from Polygon.io.
        Args:
            ticker: Stock ticker symbol
            days: Number of days of data to fetch (default: 100)
        Returns:
            List of daily bar dicts, or None if failed
        """
        try:
            if not self.api_key:
                self.logger.error("No API key available for Polygon.io")
                return None
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 20)  # Add buffer for weekends/holidays
            endpoint = f"v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {'adjusted': 'true', 'sort': 'asc', 'limit': days}
            data = self._make_request(endpoint, **params)
            if not data or 'results' not in data:
                self.logger.warning(f"No historical data returned for {ticker} from Polygon.io")
                return None
            bars = data['results']
            # Convert to standard format
            result = []
            for bar in bars[-days:]:
                result.append({
                    'date': datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d'),
                    'open': bar.get('o'),
                    'high': bar.get('h'),
                    'low': bar.get('l'),
                    'close': bar.get('c'),
                    'volume': bar.get('v'),
                    'data_source': 'polygon'
                })
            return result if result else None
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {ticker} from Polygon.io: {e}")
            return None
    
    def _format_address(self, address: Dict) -> Optional[str]:
        """Format address dictionary into string"""
        if not address:
            return None
        
        parts = []
        if address.get('address1'):
            parts.append(address['address1'])
        if address.get('city'):
            parts.append(address['city'])
        if address.get('state'):
            parts.append(address['state'])
        if address.get('postal_code'):
            parts.append(address['postal_code'])
        
        return ', '.join(parts) if parts else None
    
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
        Check if Polygon.io service is available
        
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
                self.logger.info("✅ Polygon.io service health check passed")
                return True
            else:
                self.logger.warning("⚠️ Polygon.io service health check failed - no data")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Polygon.io service health check failed: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about this service
        
        Returns:
            Dict with service information
        """
        return {
            'name': self.service_name,
            'type': 'premium',
            'api_key_required': True,
            'rate_limits': {
                'requests_per_second': self.calls_per_second,
                'daily_limit': None  # No daily limit on paid plans
            },
            'capabilities': [
                'real_time_pricing',
                'historical_data',
                'fundamental_data',
                'financial_statements',
                'company_details',
                'batch_processing'
            ],
            'data_types': [
                'pricing',
                'fundamentals',
                'company_info',
                'financial_statements'
            ],
            'coverage': [
                'US_stocks',
                'options',
                'forex',
                'crypto'
            ],
            'cost_per_call': 0.002,  # Estimated cost
            'reliability_score': 0.95,
            'batch_limit': 100
        } 