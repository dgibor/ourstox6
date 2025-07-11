#!/usr/bin/env python3
"""
Base service class for all API services
"""

import logging
import time
import requests
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from ratelimit import limits, sleep_and_retry
from config import Config
from exceptions import ServiceError, RateLimitError, DataNotFoundError

class BaseService(ABC):
    """Base class for all API services"""
    
    def __init__(self, service_name: str, api_key: str = None):
        """Initialize base service"""
        self.service_name = service_name
        self.api_key = api_key or Config.get_api_key(service_name)
        self.rate_limit = Config.get_rate_limit(service_name)
        self.logger = logging.getLogger(f"{service_name}_service")
        
        if not self.api_key:
            self.logger.warning(f"No API key found for {service_name}")
    
    def _make_request(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Make HTTP request with error handling and rate limiting.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            RateLimitError: If rate limit is exceeded
            ServiceError: If request fails
        """
        try:
            # Add default headers if not provided
            if headers is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            
            # Make request
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Check for rate limiting
            if response.status_code == 429:
                raise RateLimitError(self.service_name, "Rate limit exceeded")
            
            # Check for other errors
            if response.status_code != 200:
                raise ServiceError(self.service_name, f"HTTP {response.status_code}: {response.text}")
            
            # Parse JSON response
            data = response.json()
            
            # Check for API-specific error indicators
            if 'error' in data:
                error_msg = data.get('error', 'Unknown error')
                if 'rate limit' in error_msg.lower() or 'quota' in error_msg.lower():
                    raise RateLimitError(self.service_name, error_msg)
                else:
                    raise ServiceError(self.service_name, error_msg)
            
            return data
            
        except requests.exceptions.Timeout:
            raise ServiceError(self.service_name, "Request timeout")
        except requests.exceptions.RequestException as e:
            raise ServiceError(self.service_name, f"Request failed: {str(e)}")
        except ValueError as e:
            raise ServiceError(self.service_name, f"Invalid JSON response: {str(e)}")
    
    @abstractmethod
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get data for a ticker - must be implemented by subclasses"""
        pass
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate ticker symbol format"""
        if not ticker or not isinstance(ticker, str):
            return False
        
        # Basic validation: alphanumeric, 1-10 characters
        if not ticker.isalnum() or len(ticker) > 10:
            return False
        
        return True
    
    def handle_response(self, response: Dict[str, Any], ticker: str) -> Optional[Dict[str, Any]]:
        """Handle API response and extract data"""
        if not response:
            raise DataNotFoundError(self.service_name, ticker)
        
        # Check for error indicators in response
        if 'error' in response:
            error_msg = response.get('error', 'Unknown error')
            if 'rate limit' in error_msg.lower():
                raise RateLimitError(self.service_name, ticker)
            else:
                raise ServiceError(self.service_name, error_msg, ticker)
        
        return response
    
    def log_request(self, ticker: str, success: bool, error: str = None):
        """Log request results"""
        if success:
            self.logger.info(f"SUCCESS {self.service_name} request for {ticker}")
        else:
            self.logger.error(f"FAILED {self.service_name} request for {ticker}: {error}")
    
    def close(self):
        """Close service connections - override if needed"""
        self.logger.info(f"Closing {self.service_name} service")
    
    def test_service(self, test_tickers: list = None) -> Dict[str, Any]:
        """Test service functionality"""
        if not test_tickers:
            test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        results = {
            'service': self.service_name,
            'total_tests': len(test_tickers),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        self.logger.info(f"🧪 Testing {self.service_name} service with {len(test_tickers)} tickers")
        
        for ticker in test_tickers:
            try:
                if not self.validate_ticker(ticker):
                    results['errors'].append(f"Invalid ticker: {ticker}")
                    results['failed'] += 1
                    continue
                
                data = self.get_data(ticker)
                if data:
                    results['successful'] += 1
                    self.log_request(ticker, True)
                else:
                    results['failed'] += 1
                    results['errors'].append(f"No data for {ticker}")
                    self.log_request(ticker, False, "No data returned")
                
                # Rate limiting delay
                time.sleep(60 / self.rate_limit)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{ticker}: {str(e)}")
                self.log_request(ticker, False, str(e))
        
        success_rate = (results['successful'] / results['total_tests']) * 100
        self.logger.info(f"📊 {self.service_name} test results: {results['successful']}/{results['total_tests']} ({success_rate:.1f}%)")
        
        return results

def test_base_service():
    """Test base service functionality"""
    print("🧪 Testing Base Service")
    print("=" * 30)
    
    # Create a mock service for testing
    class MockService(BaseService):
        def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
            if ticker == 'AAPL':
                return {'price': 150.0, 'volume': 1000000}
            elif ticker == 'INVALID!':
                return None
            else:
                raise ServiceError('mock', 'Test error', ticker)
    
    service = MockService('mock', 'test_key')
    
    # Test ticker validation
    print(f"✅ Valid ticker 'AAPL': {service.validate_ticker('AAPL')}")
    print(f"✅ Invalid ticker 'INVALID!': {service.validate_ticker('INVALID!')}")
    print(f"✅ Empty ticker: {service.validate_ticker('')}")
    
    # Test data retrieval
    try:
        data = service.get_data('AAPL')
        print(f"✅ AAPL data: {data}")
    except Exception as e:
        print(f"❌ AAPL error: {e}")
    
    # Test error handling
    try:
        data = service.get_data('INVALID!')
        print(f"✅ INVALID data: {data}")
    except Exception as e:
        print(f"✅ INVALID error (expected): {e}")
    
    # Test service
    results = service.test_service(['AAPL', 'MSFT'])
    print(f"✅ Test results: {results}")
    
    service.close()
    print("✅ Base service test completed")

if __name__ == "__main__":
    test_base_service() 