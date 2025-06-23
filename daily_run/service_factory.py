#!/usr/bin/env python3
"""
Service factory for creating and managing API services
"""

from typing import Dict, List, Optional, Any
from base_service import BaseService
from price_service import YahooPriceService, FinnhubPriceService, FMPPriceService
from fundamental_service import FundamentalService
from config import Config

class ServiceFactory:
    """Factory for creating and managing API services"""
    
    def __init__(self):
        """Initialize service factory"""
        self.services: Dict[str, BaseService] = {}
        self.service_registry = {
            'price': {
                'yahoo': YahooPriceService,
                'finnhub': FinnhubPriceService,
                'fmp': FMPPriceService
            },
            'fundamental': {
                'consolidated': FundamentalService
            }
        }
    
    def create_service(self, service_type: str, provider: str) -> Optional[BaseService]:
        """Create a service instance"""
        if service_type not in self.service_registry:
            print(f"❌ Unknown service type: {service_type}")
            return None
        
        if provider not in self.service_registry[service_type]:
            print(f"❌ Unknown provider: {provider} for {service_type}")
            return None
        
        try:
            service_class = self.service_registry[service_type][provider]
            service = service_class()
            
            # Check if service has required API key
            if not service.api_key:
                print(f"⚠️  No API key for {provider}")
                return None
            
            self.services[f"{service_type}_{provider}"] = service
            print(f"✅ Created {service_type} service: {provider}")
            return service
            
        except Exception as e:
            print(f"❌ Error creating {service_type} service {provider}: {e}")
            return None
    
    def get_service(self, service_type: str, provider: str) -> Optional[BaseService]:
        """Get existing service or create new one"""
        service_key = f"{service_type}_{provider}"
        
        if service_key in self.services:
            return self.services[service_key]
        
        return self.create_service(service_type, provider)
    
    def get_available_services(self, service_type: str) -> List[str]:
        """Get list of available providers for a service type"""
        if service_type not in self.service_registry:
            return []
        
        available = []
        for provider in self.service_registry[service_type]:
            service = self.create_service(service_type, provider)
            if service:
                available.append(provider)
        
        return available
    
    def test_service(self, service_type: str, provider: str, test_ticker: str = 'AAPL') -> Dict[str, Any]:
        """Test a specific service"""
        service = self.get_service(service_type, provider)
        if not service:
            return {'error': f'Service {service_type}:{provider} not available'}
        
        try:
            result = service.get_data(test_ticker)
            return {
                'service': f"{service_type}:{provider}",
                'ticker': test_ticker,
                'success': result is not None,
                'data': result
            }
        except Exception as e:
            return {
                'service': f"{service_type}:{provider}",
                'ticker': test_ticker,
                'success': False,
                'error': str(e)
            }
    
    def test_all_services(self, service_type: str, test_ticker: str = 'AAPL') -> Dict[str, Any]:
        """Test all available services of a type"""
        results = {
            'service_type': service_type,
            'test_ticker': test_ticker,
            'total_services': 0,
            'successful': 0,
            'failed': 0,
            'results': {}
        }
        
        if service_type not in self.service_registry:
            results['error'] = f'Unknown service type: {service_type}'
            return results
        
        for provider in self.service_registry[service_type]:
            results['total_services'] += 1
            test_result = self.test_service(service_type, provider, test_ticker)
            results['results'][provider] = test_result
            
            if test_result.get('success'):
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {
            'total_services': len(self.services),
            'services': {}
        }
        
        for service_key, service in self.services.items():
            status['services'][service_key] = {
                'name': service.service_name,
                'has_api_key': bool(service.api_key),
                'rate_limit': service.rate_limit
            }
        
        return status
    
    def close_all_services(self):
        """Close all service connections"""
        for service_key, service in self.services.items():
            try:
                service.close()
                print(f"✅ Closed service: {service_key}")
            except Exception as e:
                print(f"❌ Error closing {service_key}: {e}")
        
        self.services.clear()

    def get_price_service(self, provider: str = 'yahoo'):
        """Get a price service (default: yahoo)"""
        return self.get_service('price', provider)

    def get_fundamental_service(self, provider: str = 'consolidated'):
        """Get a fundamental service"""
        return self.get_service('fundamental', provider)

def test_service_factory():
    """Test service factory functionality"""
    print("🧪 Testing Service Factory")
    print("=" * 30)
    
    factory = ServiceFactory()
    
    # Test available services
    available_price_services = factory.get_available_services('price')
    print(f"✅ Available price services: {available_price_services}")
    
    # Test individual service creation
    yahoo_service = factory.create_service('price', 'yahoo')
    if yahoo_service:
        print(f"✅ Yahoo service created: {yahoo_service.service_name}")
    
    # Test service retrieval
    finnhub_service = factory.get_service('price', 'finnhub')
    if finnhub_service:
        print(f"✅ Finnhub service retrieved: {finnhub_service.service_name}")
    
    # Test service status
    status = factory.get_service_status()
    print(f"✅ Service status: {status['total_services']} services active")
    
    # Test all services
    test_results = factory.test_all_services('price', 'AAPL')
    print(f"✅ Test results: {test_results['successful']}/{test_results['total_services']} successful")
    
    # Close all services
    factory.close_all_services()
    print("✅ Service factory test completed")

if __name__ == "__main__":
    test_service_factory() 