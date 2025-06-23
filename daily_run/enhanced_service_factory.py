#!/usr/bin/env python3
"""
Enhanced Service Factory
Provides centralized service creation with integrated error handling, monitoring, and batch processing
"""

from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
import logging
import time
from datetime import datetime
from common_imports import (
    setup_logging, get_error_handler, get_batch_processor, 
    get_system_monitor, monitor_performance, handle_errors, retry_on_failure
)

class ServiceInterface(ABC):
    """Base interface for all services"""
    
    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data for a ticker"""
        pass
    
    @abstractmethod
    def get_price_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get price data for a ticker"""
        pass
    
    @abstractmethod
    def close(self):
        """Close service connections"""
        pass

class EnhancedServiceFactory:
    """Enhanced service factory with monitoring and error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger("enhanced_service_factory")
        self.error_handler = get_error_handler("service_factory")
        self.system_monitor = get_system_monitor()
        self.services: Dict[str, ServiceInterface] = {}
        self.service_health: Dict[str, Dict[str, Any]] = {}
        
        # Setup logging
        setup_logging("enhanced_service_factory")
        
    @monitor_performance
    def create_service(self, service_type: str, **kwargs) -> ServiceInterface:
        """Create a service with enhanced error handling and monitoring"""
        try:
            if service_type == "yahoo":
                from yahoo_finance_service import YahooFinanceService
                service = YahooFinanceService()
            elif service_type == "finnhub":
                from finnhub_service import FinnhubService
                service = FinnhubService()
            elif service_type == "alpha_vantage":
                from alpha_vantage_service import AlphaVantageService
                service = AlphaVantageService()
            elif service_type == "fmp":
                from fmp_service import FMPService
                service = FMPService()
            else:
                raise ValueError(f"Unknown service type: {service_type}")
            
            # Wrap service with enhanced functionality
            enhanced_service = EnhancedServiceWrapper(service, service_type, self.error_handler)
            self.services[service_type] = enhanced_service
            
            self.logger.info(f"Created enhanced {service_type} service")
            return enhanced_service
            
        except Exception as e:
            self.error_handler.handle_error(e, {'operation': 'create_service', 'service_type': service_type})
            raise
    
    @monitor_performance
    def get_service(self, service_type: str) -> ServiceInterface:
        """Get existing service or create new one"""
        if service_type not in self.services:
            return self.create_service(service_type)
        return self.services[service_type]
    
    @monitor_performance
    def get_all_services(self) -> Dict[str, ServiceInterface]:
        """Get all available services"""
        return self.services.copy()
    
    @monitor_performance
    def test_service_health(self, service_type: str) -> Dict[str, Any]:
        """Test health of a specific service"""
        try:
            service = self.get_service(service_type)
            test_ticker = "AAPL"  # Use reliable test ticker
            
            # Test fundamental data retrieval
            start_time = time.time()
            fundamental_data = service.get_fundamental_data(test_ticker)
            fundamental_time = time.time() - start_time
            
            # Test price data retrieval
            start_time = time.time()
            price_data = service.get_price_data(test_ticker)
            price_time = time.time() - start_time
            
            health_status = {
                'service_type': service_type,
                'status': 'healthy',
                'fundamental_data_available': fundamental_data is not None,
                'price_data_available': price_data is not None,
                'fundamental_response_time': fundamental_time,
                'price_response_time': price_time,
                'last_test': datetime.now().isoformat()
            }
            
            # Determine overall status
            if not fundamental_data and not price_data:
                health_status['status'] = 'unhealthy'
            elif not fundamental_data or not price_data:
                health_status['status'] = 'degraded'
            
            self.service_health[service_type] = health_status
            return health_status
            
        except Exception as e:
            health_status = {
                'service_type': service_type,
                'status': 'unhealthy',
                'error': str(e),
                'last_test': datetime.now().isoformat()
            }
            self.service_health[service_type] = health_status
            self.error_handler.handle_error(e, {'operation': 'test_service_health', 'service_type': service_type})
            return health_status
    
    @monitor_performance
    def test_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Test health of all services"""
        results = {}
        for service_type in ['yahoo', 'finnhub', 'alpha_vantage', 'fmp']:
            try:
                results[service_type] = self.test_service_health(service_type)
            except Exception as e:
                self.error_handler.handle_error(e, {'operation': 'test_all_services', 'service_type': service_type})
                results[service_type] = {
                    'service_type': service_type,
                    'status': 'error',
                    'error': str(e)
                }
        return results
    
    @monitor_performance
    def get_best_service(self, service_types: List[str] = None) -> Optional[str]:
        """Get the best performing service"""
        if service_types is None:
            service_types = ['yahoo', 'finnhub', 'alpha_vantage', 'fmp']
        
        best_service = None
        best_score = 0
        
        for service_type in service_types:
            health = self.service_health.get(service_type)
            if health and health.get('status') == 'healthy':
                # Calculate score based on response times and data availability
                score = 0
                if health.get('fundamental_data_available'):
                    score += 50
                if health.get('price_data_available'):
                    score += 30
                
                # Lower response time = higher score
                fundamental_time = health.get('fundamental_response_time', 10)
                price_time = health.get('price_response_time', 10)
                score += max(0, 20 - fundamental_time - price_time)
                
                if score > best_score:
                    best_score = score
                    best_service = service_type
        
        return best_service
    
    def close_all_services(self):
        """Close all services"""
        for service_type, service in self.services.items():
            try:
                service.close()
                self.logger.info(f"Closed {service_type} service")
            except Exception as e:
                self.error_handler.handle_error(e, {'operation': 'close_service', 'service_type': service_type})
        
        self.services.clear()

class EnhancedServiceWrapper(ServiceInterface):
    """Wrapper for services with enhanced functionality"""
    
    def __init__(self, service: Any, service_type: str, error_handler):
        self.service = service
        self.service_type = service_type
        self.error_handler = error_handler
        self.logger = logging.getLogger(f"enhanced_{service_type}_service")
        self.batch_processor = get_batch_processor()
    
    @monitor_performance
    @handle_errors()
    @retry_on_failure(max_retries=2)
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data with enhanced error handling"""
        try:
            # Check if service has the method
            if hasattr(self.service, 'get_fundamental_data'):
                return self.service.get_fundamental_data(ticker)
            elif hasattr(self.service, 'fetch_financial_statements'):
                return self.service.fetch_financial_statements(ticker)
            else:
                raise NotImplementedError(f"Service {self.service_type} does not support fundamental data")
        except Exception as e:
            self.error_handler.handle_error(e, {
                'operation': 'get_fundamental_data',
                'service_type': self.service_type,
                'ticker': ticker
            })
            raise
    
    @monitor_performance
    @handle_errors()
    @retry_on_failure(max_retries=2)
    def get_price_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get price data with enhanced error handling"""
        try:
            # Check if service has the method
            if hasattr(self.service, 'get_price_data'):
                return self.service.get_price_data(ticker)
            elif hasattr(self.service, 'get_data'):
                return self.service.get_data(ticker)
            else:
                raise NotImplementedError(f"Service {self.service_type} does not support price data")
        except Exception as e:
            self.error_handler.handle_error(e, {
                'operation': 'get_price_data',
                'service_type': self.service_type,
                'ticker': ticker
            })
            raise
    
    def get_fundamental_data_batch(self, tickers: List[str]) -> Dict[str, Any]:
        """Get fundamental data for multiple tickers using batch processing"""
        if not self.batch_processor:
            # Fallback to sequential processing
            results = {}
            for ticker in tickers:
                try:
                    data = self.get_fundamental_data(ticker)
                    if data:
                        results[ticker] = data
                except Exception as e:
                    self.logger.warning(f"Failed to get data for {ticker}: {e}")
            return results
        
        # Use batch processor
        batch_result = self.batch_processor.process_batch(
            tickers, 
            self.get_fundamental_data, 
            f"{self.service_type}_fundamentals"
        )
        
        # Convert to dictionary format
        results = {}
        for ticker in batch_result.successful:
            try:
                data = self.get_fundamental_data(ticker)
                if data:
                    results[ticker] = data
            except Exception as e:
                self.logger.warning(f"Failed to get data for {ticker} after batch processing: {e}")
        
        return results
    
    def close(self):
        """Close the wrapped service"""
        try:
            if hasattr(self.service, 'close'):
                self.service.close()
        except Exception as e:
            self.error_handler.handle_error(e, {
                'operation': 'close_service',
                'service_type': self.service_type
            })

# Global factory instance
_enhanced_factory = None

def get_enhanced_service_factory() -> EnhancedServiceFactory:
    """Get global enhanced service factory instance"""
    global _enhanced_factory
    if _enhanced_factory is None:
        _enhanced_factory = EnhancedServiceFactory()
    return _enhanced_factory

def test_enhanced_factory():
    """Test the enhanced service factory"""
    print("Testing Enhanced Service Factory...")
    
    factory = get_enhanced_service_factory()
    
    # Test service creation
    try:
        yahoo_service = factory.create_service("yahoo")
        print("✅ Yahoo service created successfully")
        
        # Test service health
        health = factory.test_service_health("yahoo")
        print(f"✅ Yahoo service health: {health['status']}")
        
        # Test data retrieval
        data = yahoo_service.get_fundamental_data("AAPL")
        if data:
            print("✅ Yahoo fundamental data retrieval successful")
        else:
            print("⚠️ Yahoo fundamental data retrieval returned None")
        
        # Test batch processing
        batch_data = yahoo_service.get_fundamental_data_batch(["AAPL", "MSFT", "GOOGL"])
        print(f"✅ Batch processing completed: {len(batch_data)} successful")
        
        # Test all services
        all_health = factory.test_all_services()
        print(f"✅ All services tested: {len(all_health)} services")
        
        # Get best service
        best_service = factory.get_best_service()
        print(f"✅ Best service: {best_service}")
        
        # Close services
        factory.close_all_services()
        print("✅ All services closed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_factory() 