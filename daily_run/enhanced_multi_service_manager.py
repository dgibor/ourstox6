"""
Enhanced Multi-Service Manager
Provides intelligent API service management with fallbacks, rate limiting, and monitoring
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor
from circuit_breaker import CircuitBreaker, CircuitState


class ServicePriority(Enum):
    """Service priority levels"""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3
    EMERGENCY = 4


@dataclass
class ServiceConfig:
    """Configuration for individual services"""
    name: str
    priority: ServicePriority
    rate_limit_per_minute: int
    rate_limit_per_day: int
    cost_per_call: float = 0.0
    reliability_score: float = 1.0
    capabilities: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class APICallMetrics:
    """Metrics for API calls"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limited_calls: int = 0
    last_call_time: Optional[datetime] = None
    daily_calls_count: int = 0
    daily_reset_time: Optional[datetime] = None
    response_times: List[float] = field(default_factory=list)
    cost_today: float = 0.0


class EnhancedMultiServiceManager:
    """Enhanced multi-service manager with intelligent fallbacks and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger("enhanced_multi_service")
        self.db = DatabaseManager()
        self.error_handler = ErrorHandler("multi_service_manager")
        self.monitor = SystemMonitor()
        
        # Service configurations
        self.service_configs = self._initialize_service_configs()
        self.service_instances = {}
        self.api_metrics = {}
        self.circuit_breakers = {}
        
        # Rate limiting
        self.rate_limits = {}
        self.daily_counters = {}
        
        # Initialize services
        self._initialize_services()
        self._initialize_rate_limiting()
        self._initialize_circuit_breakers()
    
    def _initialize_service_configs(self) -> Dict[str, ServiceConfig]:
        """Initialize service configurations based on existing implementations"""
        return {
            'yahoo': ServiceConfig(
                name='Yahoo Finance',
                priority=ServicePriority.PRIMARY,
                rate_limit_per_minute=60,
                rate_limit_per_day=None,  # No daily limit
                cost_per_call=0.0,
                reliability_score=0.95,
                capabilities=['fundamentals', 'pricing', 'batch'],
                enabled=True  # Always enabled - no API key required
            ),
            'fmp': ServiceConfig(
                name='Financial Modeling Prep',
                priority=ServicePriority.SECONDARY,
                rate_limit_per_minute=10,
                rate_limit_per_day=1000,
                cost_per_call=0.001,
                reliability_score=0.95,
                capabilities=['fundamentals', 'pricing', 'batch'],
                enabled=bool(os.getenv('FMP_API_KEY'))
            ),
            'alpha_vantage': ServiceConfig(
                name='Alpha Vantage',
                priority=ServicePriority.FALLBACK,
                rate_limit_per_minute=5,
                rate_limit_per_day=100,
                cost_per_call=0.0,
                reliability_score=0.85,
                capabilities=['fundamentals', 'pricing'],
                enabled=bool(os.getenv('ALPHA_VANTAGE_API_KEY'))
            ),
            'finnhub': ServiceConfig(
                name='Finnhub',
                priority=ServicePriority.EMERGENCY,
                rate_limit_per_minute=60,
                rate_limit_per_day=None,
                cost_per_call=0.0,
                reliability_score=0.80,
                capabilities=['pricing', 'fundamentals', 'news'],
                enabled=bool(os.getenv('FINNHUB_API_KEY'))
            ),
            'polygon': ServiceConfig(
                name='Polygon.io',
                priority=ServicePriority.EMERGENCY,
                rate_limit_per_minute=300,  # 5 per second = 300 per minute
                rate_limit_per_day=None,
                cost_per_call=0.002,
                reliability_score=0.95,
                capabilities=['fundamentals', 'pricing', 'batch', 'premium'],
                enabled=bool(os.getenv('POLYGON_API_KEY'))
            )
        }
    
    def _initialize_services(self):
        """Initialize all available services"""
        self.logger.info("Initializing enhanced multi-service manager")
        
        for service_id, config in self.service_configs.items():
            if not config.enabled:
                self.logger.warning(f"⚠️  {config.name} disabled (missing API key)")
                continue
                
            try:
                service = self._create_service_instance(service_id)
                if service:
                    self.service_instances[service_id] = service
                    self.api_metrics[service_id] = APICallMetrics()
                    self.logger.info(f"{config.name} initialized")
                else:
                    self.logger.warning(f"⚠️  {config.name} failed to initialize")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize {config.name}: {e}")
    
    def _create_service_instance(self, service_id: str):
        """Create service instance based on existing implementations"""
        try:
            if service_id == 'yahoo':
                # Use the proper Yahoo Finance service
                from yahoo_finance_service import YahooFinanceService
                return YahooFinanceService()
            elif service_id == 'alpha_vantage':
                # Use the Alpha Vantage service
                from alpha_vantage_service import AlphaVantageService
                return AlphaVantageService()
            elif service_id == 'finnhub':
                # Use the Finnhub service
                from finnhub_service import FinnhubService
                return FinnhubService()
            elif service_id == 'polygon':
                # Use the Polygon.io service
                from polygon_service import PolygonService
                return PolygonService()
            elif service_id == 'fmp':
                # Create a simple FMP wrapper since the full service has dependency issues
                return self._create_simple_fmp_service()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating {service_id} service: {e}")
            return None
    
    def _create_simple_fmp_service(self):
        """Create simple FMP service wrapper without dependencies"""
        class SimpleFMPServiceWrapper:
            def __init__(self):
                self.api_key = os.getenv('FMP_API_KEY')
                self.base_url = "https://financialmodelingprep.com/api/v3"
                self.logger = logging.getLogger("fmp_service")
            
            def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import requests
                    url = f"{self.base_url}/quote/{ticker}"
                    params = {'apikey': self.api_key}
                    
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            quote = data[0]
                            return {
                                'price': quote.get('price'),
                                'volume': quote.get('volume'),
                                'open': quote.get('open'),
                                'high': quote.get('dayHigh'),
                                'low': quote.get('dayLow'),
                                'data_source': 'fmp',
                                'timestamp': datetime.now()
                            }
                    return None
                except Exception as e:
                    self.logger.error(f"FMP error for {ticker}: {e}")
                    return None
            
            def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import requests
                    url = f"{self.base_url}/profile/{ticker}"
                    params = {'apikey': self.api_key}
                    
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            profile = data[0]
                            return {
                                'market_cap': profile.get('mktCap'),
                                'pe_ratio': profile.get('pe'),
                                'revenue_ttm': profile.get('revenue'),
                                'employees': profile.get('fullTimeEmployees'),
                                'sector': profile.get('sector'),
                                'industry': profile.get('industry'),
                                'data_source': 'fmp',
                                'timestamp': datetime.now()
                            }
                    return None
                except Exception as e:
                    self.logger.error(f"FMP fundamental error for {ticker}: {e}")
                    return None
        
        return SimpleFMPServiceWrapper()
    
    def _create_simple_alpha_vantage_service(self):
        """Create simple Alpha Vantage service wrapper"""
        class SimpleAlphaVantageWrapper:
            def __init__(self):
                self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
                self.base_url = 'https://www.alphavantage.co/query'
                self.logger = logging.getLogger("alpha_vantage_service")
            
            def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import requests
                    params = {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': ticker,
                        'apikey': self.api_key
                    }
                    
                    response = requests.get(self.base_url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if 'Global Quote' in data:
                            quote = data['Global Quote']
                            return {
                                'price': float(quote.get('05. price', 0)),
                                'volume': int(quote.get('06. volume', 0)),
                                'change': float(quote.get('09. change', 0)),
                                'change_percent': quote.get('10. change percent', '0%'),
                                'data_source': 'alpha_vantage',
                                'timestamp': datetime.now()
                            }
                    return None
                except Exception as e:
                    self.logger.error(f"Alpha Vantage error for {ticker}: {e}")
                    return None
            
            def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import requests
                    params = {
                        'function': 'OVERVIEW',
                        'symbol': ticker,
                        'apikey': self.api_key
                    }
                    
                    response = requests.get(self.base_url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if 'Symbol' in data:
                            return {
                                'market_cap': data.get('MarketCapitalization'),
                                'pe_ratio': data.get('PERatio'),
                                'revenue_ttm': data.get('RevenueTTM'),
                                'gross_profit_ttm': data.get('GrossProfitTTM'),
                                'eps': data.get('EPS'),
                                'book_value': data.get('BookValue'),
                                'data_source': 'alpha_vantage',
                                'timestamp': datetime.now()
                            }
                    return None
                except Exception as e:
                    self.logger.error(f"Alpha Vantage fundamental error for {ticker}: {e}")
                    return None
        
        return SimpleAlphaVantageWrapper()
    
    def _create_yahoo_service(self):
        """Create Yahoo Finance service wrapper"""
        class YahooServiceWrapper:
            def __init__(self):
                self.logger = logging.getLogger("yahoo_service")
            
            def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import yfinance as yf
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="1d")
                    
                    if hist.empty:
                        return None
                    
                    latest = hist.iloc[-1]
                    return {
                        'price': float(latest['Close']),
                        'volume': int(latest['Volume']),
                        'open': float(latest['Open']),
                        'high': float(latest['High']),
                        'low': float(latest['Low']),
                        'data_source': 'yahoo',
                        'timestamp': datetime.now()
                    }
                except Exception as e:
                    self.logger.error(f"Yahoo error for {ticker}: {e}")
                    return None
                    
            def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import yfinance as yf
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    if not info:
                        return None
                    
                    return {
                        'market_cap': info.get('marketCap'),
                        'pe_ratio': info.get('trailingPE'),
                        'revenue_ttm': info.get('totalRevenue'),
                        'net_income_ttm': info.get('netIncomeToCommon'),
                        'data_source': 'yahoo',
                        'timestamp': datetime.now()
                    }
                except Exception as e:
                    self.logger.error(f"Yahoo fundamental error for {ticker}: {e}")
                    return None
        
        return YahooServiceWrapper()
    
    def _create_finnhub_service(self):
        """Create Finnhub service wrapper"""
        class FinnhubServiceWrapper:
            def __init__(self):
                self.api_key = os.getenv('FINNHUB_API_KEY')
                self.base_url = 'https://finnhub.io/api/v1'
                self.logger = logging.getLogger("finnhub_service")
            
            def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import requests
                    url = f"{self.base_url}/quote"
                    params = {'symbol': ticker, 'token': self.api_key}
                    
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            'price': data.get('c'),  # current price
                            'volume': data.get('v'),  # volume
                            'high': data.get('h'),   # high
                            'low': data.get('l'),    # low
                            'open': data.get('o'),   # open
                            'data_source': 'finnhub',
                            'timestamp': datetime.now()
                        }
                    return None
                except Exception as e:
                    self.logger.error(f"Finnhub error for {ticker}: {e}")
                    return None
        
        return FinnhubServiceWrapper()
    
    def _create_polygon_service(self):
        """Create Polygon.io service wrapper"""
        class PolygonServiceWrapper:
            def __init__(self):
                self.api_key = os.getenv('POLYGON_API_KEY')
                self.base_url = 'https://api.polygon.io/v1'
                self.logger = logging.getLogger("polygon_service")
            
            def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import requests
                    url = f"{self.base_url}/meta/symbols/{ticker}/company"
                    params = {'apiKey': self.api_key}
                    
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data and data.get('status') == 'OK':
                            return {
                                'market_cap': data.get('marketCap'),
                                'pe_ratio': data.get('peRatio'),
                                'revenue_ttm': data.get('revenueTTM'),
                                'eps': data.get('eps'),
                                'book_value': data.get('bookValue'),
                                'data_source': 'polygon',
                                'timestamp': datetime.now()
                            }
                    return None
                except Exception as e:
                    self.logger.error(f"Polygon error for {ticker}: {e}")
                    return None
            
            def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                try:
                    import requests
                    url = f"{self.base_url}/meta/symbols/{ticker}/company"
                    params = {'apiKey': self.api_key}
                    
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data and data.get('status') == 'OK':
                            return {
                                'market_cap': data.get('marketCap'),
                                'pe_ratio': data.get('peRatio'),
                                'revenue_ttm': data.get('revenueTTM'),
                                'eps': data.get('eps'),
                                'book_value': data.get('bookValue'),
                                'data_source': 'polygon',
                                'timestamp': datetime.now()
                            }
                    return None
                except Exception as e:
                    self.logger.error(f"Polygon fundamental error for {ticker}: {e}")
                    return None
        
        return PolygonServiceWrapper()
    
    def _initialize_rate_limiting(self):
        """Initialize rate limiting for all services"""
        for service_id, config in self.service_configs.items():
            if service_id in self.service_instances:
                self.rate_limits[service_id] = {
                    'minute_calls': [],
                    'daily_calls': 0,
                    'daily_reset': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                }
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for all services"""
        for service_id in self.service_instances:
            self.circuit_breakers[service_id] = CircuitBreaker(
                service_name=service_id,
                failure_threshold=5,
                recovery_timeout=300  # 5 minutes
            )
    
    def get_optimal_service_order(self, data_type: str = 'pricing', tickers_count: int = 1) -> List[str]:
        """Get optimal service order based on data type, availability, and current status"""
        available_services = []
        
        for service_id, config in self.service_configs.items():
            if (service_id in self.service_instances and 
                config.enabled and 
                data_type in config.capabilities and
                self._is_service_available(service_id)):
                
                # Calculate service score
                score = self._calculate_service_score(service_id, tickers_count)
                available_services.append((service_id, score))
        
        # Sort by score (higher is better)
        available_services.sort(key=lambda x: x[1], reverse=True)
        
        service_order = [service_id for service_id, _ in available_services]
        self.logger.info(f"📋 Optimal service order for {data_type}: {' → '.join(service_order)}")
        
        return service_order
    
    def _is_service_available(self, service_id: str) -> bool:
        """Check if service is available (not rate limited or circuit broken)"""
        # Check circuit breaker
        if service_id in self.circuit_breakers:
            cb = self.circuit_breakers[service_id]
            if cb.state != CircuitState.CLOSED:
                return False
        
        # Check rate limits
        if service_id in self.rate_limits:
            config = self.service_configs[service_id]
            rate_data = self.rate_limits[service_id]
            
            # Check daily limit
            if config.rate_limit_per_day is not None and rate_data['daily_calls'] >= config.rate_limit_per_day:
                return False
            
            # Check minute limit
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            rate_data['minute_calls'] = [call_time for call_time in rate_data['minute_calls'] if call_time > minute_ago]
            
            if len(rate_data['minute_calls']) >= config.rate_limit_per_minute:
                return False
        
        return True
    
    def _calculate_service_score(self, service_id: str, tickers_count: int) -> float:
        """Calculate service score based on multiple factors"""
        config = self.service_configs[service_id]
        metrics = self.api_metrics[service_id]
        
        # Base score from priority
        priority_scores = {
            ServicePriority.PRIMARY: 100,
            ServicePriority.SECONDARY: 80,
            ServicePriority.FALLBACK: 60,
            ServicePriority.EMERGENCY: 40
        }
        score = priority_scores[config.priority]
        
        # Adjust for reliability
        score *= config.reliability_score
        
        # Adjust for success rate
        if metrics.total_calls > 0:
            success_rate = metrics.successful_calls / metrics.total_calls
            score *= success_rate
        
        # Adjust for response time
        if metrics.response_times:
            avg_response_time = sum(metrics.response_times[-10:]) / len(metrics.response_times[-10:])
            # Prefer faster services (penalize slow ones)
            if avg_response_time > 5.0:
                score *= 0.8
            elif avg_response_time < 2.0:
                score *= 1.2
        
        # Adjust for cost (prefer free services)
        if config.cost_per_call > 0:
            score *= 0.9
        
        # Adjust for batch capabilities
        if tickers_count > 10 and 'batch' in config.capabilities:
            score *= 1.3
        
        return score
    
    def fetch_data_with_fallback(self, ticker: str, data_type: str = 'pricing') -> Tuple[Optional[Dict[str, Any]], str]:
        """Fetch data with intelligent service fallback"""
        
        # Input validation
        if not ticker or ticker is None:
            self.logger.error(f"❌ Invalid ticker: {ticker}")
            return None, "invalid_ticker"
        
        if not isinstance(ticker, str):
            self.logger.error(f"❌ Ticker must be string, got {type(ticker)}")
            return None, "invalid_ticker_type"
        
        ticker = ticker.strip().upper()
        if len(ticker) == 0 or len(ticker) > 10:
            self.logger.error(f"❌ Invalid ticker length: {ticker}")
            return None, "invalid_ticker_length"
        
        # Basic ticker format validation
        if not ticker.replace('.', '').replace('-', '').isalnum():
            self.logger.error(f"❌ Invalid ticker format: {ticker}")
            return None, "invalid_ticker_format"
        
        service_order = self.get_optimal_service_order(data_type, 1)
        
        if not service_order:
            self.logger.error(f"❌ No available services for {data_type} data")
            return None, "no_services_available"
        
        last_error = None
        
        for service_id in service_order:
            try:
                self.logger.info(f"🔄 Trying {service_id} for {ticker} ({data_type})")
                
                # Check circuit breaker state
                cb = self.circuit_breakers[service_id]
                if cb.state != CircuitState.CLOSED:
                    self.logger.warning(f"⚡ Circuit breaker open for {service_id}")
                    continue
                
                # Record rate limit
                self._record_api_call(service_id)
                
                # Make the API call
                start_time = time.time()
                
                result = None
                service = self.service_instances[service_id]
                
                if data_type == 'pricing':
                    result = service.get_data(ticker)
                elif data_type == 'fundamentals':
                    if hasattr(service, 'get_fundamental_data'):
                        result = service.get_fundamental_data(ticker)
                    else:
                        self.logger.warning(f"⚠️  {service_id} doesn't support fundamental data")
                        continue
                
                response_time = time.time() - start_time
                
                # Validate result
                if result and self._validate_result(result, data_type):
                    # Success
                    self._record_successful_call(service_id, response_time)
                    cb._on_success(response_time)
                    self.logger.info(f"✅ Successfully fetched {data_type} for {ticker} from {service_id}")
                    return result, service_id
                else:
                    # No data or invalid data
                    self._record_failed_call(service_id, "no_valid_data")
                    self.logger.warning(f"⚠️  No valid {data_type} data for {ticker} from {service_id}")
                    
            except Exception as e:
                last_error = e
                response_time = time.time() - start_time if 'start_time' in locals() else 0
                
                # Record failure
                self._record_failed_call(service_id, str(e))
                cb._on_failure(e)
                
                # Check if it's a rate limit error
                if 'rate limit' in str(e).lower() or '429' in str(e):
                    self._record_rate_limit(service_id)
                    self.logger.warning(f"🚦 Rate limited by {service_id} for {ticker}")
                else:
                    self.logger.error(f"❌ Error from {service_id} for {ticker}: {e}")
                
                continue
        
        # All services failed
        context = {
            'ticker': ticker,
            'data_type': data_type,
            'services_tried': service_order,
            'last_error': str(last_error) if last_error else None
        }
        self.error_handler.handle_error(last_error or Exception(f"All services failed for {ticker} ({data_type})"), context)
        
        return None, "all_services_failed"

    def get_service(self, service_name: str):
        """
        Get a specific service instance by name.
        
        This method provides compatibility with the daily trading system
        that expects to call service_manager.get_service('fmp') etc.
        
        Args:
            service_name: Name of the service ('fmp', 'yahoo_finance', 'alpha_vantage', etc.)
            
        Returns:
            Service instance or None if not available
        """
        # Map service names to internal service IDs
        service_name_mapping = {
            'fmp': 'fmp',
            'yahoo_finance': 'yahoo',
            'yahoo': 'yahoo',
            'alpha_vantage': 'alpha_vantage',
            'finnhub': 'finnhub',
            'polygon': 'polygon'
        }
        
        # Get the internal service ID
        service_id = service_name_mapping.get(service_name.lower(), service_name.lower())
        
        # Check if service exists and is available
        if service_id in self.service_instances:
            service = self.service_instances[service_id]
            
            # Create a wrapper that provides the expected interface
            class ServiceWrapper:
                def __init__(self, service_instance, service_id, manager):
                    self.service = service_instance
                    self.service_id = service_id
                    self.manager = manager
                    self.logger = logging.getLogger(f"service_wrapper_{service_id}")
                
                def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                    """Get fundamental data using the service"""
                    try:
                        if hasattr(self.service, 'get_fundamental_data'):
                            return self.service.get_fundamental_data(ticker)
                        else:
                            self.logger.warning(f"Service {self.service_id} doesn't support fundamental data")
                            return None
                    except Exception as e:
                        self.logger.error(f"Error getting fundamental data from {self.service_id}: {e}")
                        return None
                
                def get_historical_data(self, ticker: str, days: int = 100) -> Optional[List[Dict]]:
                    """Get historical data using the service"""
                    try:
                        if hasattr(self.service, 'get_historical_data'):
                            return self.service.get_historical_data(ticker, days)
                        elif hasattr(self.service, 'get_data'):
                            # Use fallback method for services that only have get_data
                            result = self.service.get_data(ticker)
                            if result:
                                # Convert single data point to historical format
                                return [{
                                    'date': datetime.now().strftime('%Y-%m-%d'),
                                    'open': result.get('open', result.get('price')),
                                    'high': result.get('high', result.get('price')),
                                    'low': result.get('low', result.get('price')),
                                    'close': result.get('close', result.get('price')),
                                    'volume': result.get('volume', 0)
                                }]
                            return None
                        else:
                            self.logger.warning(f"Service {self.service_id} doesn't support historical data")
                            return None
                    except Exception as e:
                        self.logger.error(f"Error getting historical data from {self.service_id}: {e}")
                        return None
                
                def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
                    """Get current data using the service"""
                    try:
                        if hasattr(self.service, 'get_data'):
                            return self.service.get_data(ticker)
                        else:
                            self.logger.warning(f"Service {self.service_id} doesn't support get_data")
                            return None
                    except Exception as e:
                        self.logger.error(f"Error getting data from {self.service_id}: {e}")
                        return None
            
            self.logger.debug(f"Returning service wrapper for {service_id}")
            return ServiceWrapper(service, service_id, self)
        
        else:
            self.logger.warning(f"Service '{service_name}' not available (mapped to '{service_id}')")
            self.logger.debug(f"Available services: {list(self.service_instances.keys())}")
            return None
    
    def _validate_result(self, result: Dict[str, Any], data_type: str) -> bool:
        """Validate API result data"""
        if not isinstance(result, dict):
            return False
        
        if data_type == 'pricing':
            # Price data should have a valid price
            price = result.get('price')
            if price is None or price <= 0:
                return False
            # Volume can be None/0 for some markets, so don't validate it strictly
            
        elif data_type == 'fundamentals':
            # Fundamental data should have at least one meaningful metric
            meaningful_fields = ['market_cap', 'pe_ratio', 'revenue_ttm', 'eps']
            has_data = any(result.get(field) for field in meaningful_fields)
            if not has_data:
                return False
        
        return True
    
    def _record_api_call(self, service_id: str):
        """Record an API call for rate limiting"""
        now = datetime.now()
        
        # Update rate limits
        if service_id in self.rate_limits:
            rate_data = self.rate_limits[service_id]
            rate_data['minute_calls'].append(now)
            rate_data['daily_calls'] += 1
            
            # Reset daily counter if needed
            if now >= rate_data['daily_reset']:
                rate_data['daily_calls'] = 1
                rate_data['daily_reset'] = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Update metrics
        if service_id in self.api_metrics:
            metrics = self.api_metrics[service_id]
            metrics.total_calls += 1
            metrics.last_call_time = now
            
            # Update daily counters
            if metrics.daily_reset_time is None or now >= metrics.daily_reset_time:
                metrics.daily_calls_count = 1
                metrics.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                metrics.cost_today = 0.0
            else:
                metrics.daily_calls_count += 1
            
            # Add cost
            config = self.service_configs[service_id]
            metrics.cost_today += config.cost_per_call
    
    def _record_successful_call(self, service_id: str, response_time: float):
        """Record a successful API call"""
        if service_id in self.api_metrics:
            metrics = self.api_metrics[service_id]
            metrics.successful_calls += 1
            metrics.response_times.append(response_time)
            
            # Keep only last 100 response times
            if len(metrics.response_times) > 100:
                metrics.response_times = metrics.response_times[-100:]
    
    def _record_failed_call(self, service_id: str, error: str):
        """Record a failed API call"""
        if service_id in self.api_metrics:
            metrics = self.api_metrics[service_id]
            metrics.failed_calls += 1
    
    def _record_rate_limit(self, service_id: str):
        """Record a rate limit hit"""
        if service_id in self.api_metrics:
            metrics = self.api_metrics[service_id]
            metrics.rate_limited_calls += 1
    
    def get_service_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive service status report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {
                'total_services': len(self.service_instances),
                'available_services': 0,
                'total_calls_today': 0,
                'total_cost_today': 0.0,
                'average_success_rate': 0.0
            }
        }
        
        total_success_rate = 0
        service_count = 0
        
        for service_id, metrics in self.api_metrics.items():
            config = self.service_configs[service_id]
            is_available = self._is_service_available(service_id)
            
            success_rate = 0
            if metrics.total_calls > 0:
                success_rate = (metrics.successful_calls / metrics.total_calls) * 100
            
            avg_response_time = 0
            if metrics.response_times:
                avg_response_time = sum(metrics.response_times[-10:]) / len(metrics.response_times[-10:])
            
            circuit_status = "CLOSED"
            if service_id in self.circuit_breakers:
                cb = self.circuit_breakers[service_id]
                circuit_status = cb.state.name
            
            report['services'][service_id] = {
                'name': config.name,
                'available': is_available,
                'circuit_breaker_status': circuit_status,
                'total_calls': metrics.total_calls,
                'successful_calls': metrics.successful_calls,
                'failed_calls': metrics.failed_calls,
                'rate_limited_calls': metrics.rate_limited_calls,
                'success_rate_percent': success_rate,
                'daily_calls': metrics.daily_calls_count,
                'daily_limit': config.rate_limit_per_day,
                'cost_today': metrics.cost_today,
                'avg_response_time': avg_response_time,
                'last_call': metrics.last_call_time.isoformat() if metrics.last_call_time else None
            }
            
            if is_available:
                report['summary']['available_services'] += 1
            
            report['summary']['total_calls_today'] += metrics.daily_calls_count
            report['summary']['total_cost_today'] += metrics.cost_today
            
            if metrics.total_calls > 0:
                total_success_rate += success_rate
                service_count += 1
        
        if service_count > 0:
            report['summary']['average_success_rate'] = total_success_rate / service_count
        
        return report
    
    def close_all_services(self):
        """Close all services and clean up resources"""
        self.logger.info("🔄 Closing all services and cleaning up resources")
        
        try:
            # Close individual service instances
            for service_id, service in self.service_instances.items():
                try:
                    if hasattr(service, 'close'):
                        service.close()
                    elif hasattr(service, 'cleanup'):
                        service.cleanup()
                    self.logger.debug(f"Closed service: {service_id}")
                except Exception as e:
                    self.logger.warning(f"Error closing service {service_id}: {e}")
            
            # Clear all tracking data
            self.service_instances.clear()
            self.api_metrics.clear()
            self.circuit_breakers.clear()
            self.rate_limits.clear()
            self.daily_counters.clear()
            
            self.logger.info("✅ All services closed and resources cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup on garbage collection"""
        try:
            self.close_all_services()
        except:
            pass  # Don't raise exceptions in destructor


# Singleton instance with proper cleanup
_multi_service_manager = None
_manager_lock = None

def get_multi_service_manager() -> EnhancedMultiServiceManager:
    """Get singleton instance of enhanced multi-service manager"""
    global _multi_service_manager, _manager_lock
    
    if _manager_lock is None:
        import threading
        _manager_lock = threading.Lock()
    
    if _multi_service_manager is None:
        with _manager_lock:
            if _multi_service_manager is None:  # Double-check locking
                _multi_service_manager = EnhancedMultiServiceManager()
    
    return _multi_service_manager

def reset_multi_service_manager():
    """Reset the singleton for testing purposes"""
    global _multi_service_manager
    if _multi_service_manager:
        _multi_service_manager.close_all_services()
        _multi_service_manager = None


def test_multi_service_manager():
    """Test the enhanced multi-service manager"""
    print("🧪 Testing Enhanced Multi-Service Manager")
    print("=" * 50)
    
    manager = get_multi_service_manager()
    
    # Test service availability
    print("\n📊 Service Status:")
    report = manager.get_service_status_report()
    for service_id, status in report['services'].items():
        availability = "✅ Available" if status['available'] else "❌ Unavailable"
        print(f"  {service_id}: {availability} ({status['circuit_breaker_status']})")
    
    # Test data fetching
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    print(f"\n🔍 Testing data fetching for {test_tickers}")
    
    for ticker in test_tickers:
        print(f"\n  Testing {ticker}:")
        
        # Test pricing data
        result, service_used = manager.fetch_data_with_fallback(ticker, 'pricing')
        if result:
            print(f"    ✅ Pricing: ${result.get('price', 'N/A')} (from {service_used})")
        else:
            print(f"    ❌ Pricing: Failed ({service_used})")
        
        # Test fundamental data
        result, service_used = manager.fetch_data_with_fallback(ticker, 'fundamentals')
        if result:
            print(f"    ✅ Fundamentals: Available (from {service_used})")
        else:
            print(f"    ❌ Fundamentals: Failed ({service_used})")
        
        time.sleep(1)  # Rate limiting
    
    # Final report
    print("\n📈 Final Service Report:")
    final_report = manager.get_service_status_report()
    summary = final_report['summary']
    print(f"  Available Services: {summary['available_services']}/{summary['total_services']}")
    print(f"  Total Calls Today: {summary['total_calls_today']}")
    print(f"  Average Success Rate: {summary['average_success_rate']:.1f}%")
    print(f"  Total Cost Today: ${summary['total_cost_today']:.4f}")


if __name__ == "__main__":
    test_multi_service_manager() 