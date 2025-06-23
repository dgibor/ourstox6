#!/usr/bin/env python3
"""
Quick Stability Test
Validates that the stability improvements are working correctly
"""

import time
from datetime import datetime
from common_imports import setup_logging, get_system_monitor
from enhanced_service_factory import get_enhanced_service_factory
from batch_processor import BatchProcessor
from error_handler import ErrorHandler

def test_monitoring_fix():
    """Test that monitoring works without the column error"""
    print("🧪 Testing Monitoring Fix")
    
    monitor = get_system_monitor()
    if not monitor:
        print("❌ System monitor not available")
        return False
    
    try:
        # Test system metrics
        metrics = monitor.get_system_metrics()
        print(f"✅ System Metrics: CPU {metrics.cpu_percent:.1f}%, Memory {metrics.memory_percent:.1f}%")
        
        # Test database health
        db_health = monitor.check_database_health()
        print(f"✅ Database Health: {db_health.status}")
        
        # Test data quality for stocks table (should not fail now)
        stocks_quality = monitor.check_data_quality('stocks')
        print(f"✅ Stocks Data Quality: {stocks_quality.total_records} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        return False

def test_enhanced_services_fix():
    """Test that enhanced services work correctly"""
    print("🧪 Testing Enhanced Services Fix")
    
    factory = get_enhanced_service_factory()
    
    try:
        # Test service creation
        yahoo_service = factory.create_service("yahoo")
        print("✅ Yahoo service created")
        
        # Test service health (should not fail with datetime error)
        health = factory.test_service_health("yahoo")
        print(f"✅ Service health: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced services test failed: {e}")
        return False

def test_batch_processing():
    """Test batch processing performance"""
    print("🧪 Testing Batch Processing")
    
    processor = BatchProcessor(max_workers=3, batch_size=5)
    
    def test_func(ticker: str):
        time.sleep(0.05)  # Simulate API call
        return {"ticker": ticker, "data": "test"}
    
    test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    try:
        result = processor.process_batch(test_tickers, test_func, "quick_test")
        print(f"✅ Batch processing: {result.total_successful}/{result.total_processed} successful")
        return result.total_successful > 0
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False

def test_error_handling():
    """Test error handling system"""
    print("🧪 Testing Error Handling")
    
    error_handler = ErrorHandler("quick_test")
    
    try:
        # Test error classification
        raise Exception("Test rate limit error")
    except Exception as e:
        error_info = error_handler.handle_error(e, {'test': True})
        print(f"✅ Error handled: {error_info['category']} - {error_info['severity']}")
        
        summary = error_handler.get_error_summary()
        print(f"✅ Error summary: {summary['total_errors']} errors")
        
        return True

def main():
    """Run quick stability tests"""
    print("🚀 Quick Stability Tests")
    print("=" * 40)
    
    setup_logging("quick_stability_test")
    
    tests = [
        ("Monitoring Fix", test_monitoring_fix),
        ("Enhanced Services Fix", test_enhanced_services_fix),
        ("Batch Processing", test_batch_processing),
        ("Error Handling", test_error_handling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} {test_name}")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*40)
    print("📊 QUICK TEST SUMMARY")
    print("="*40)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All quick tests passed! Stability improvements are working.")
    else:
        print("⚠️ Some quick tests failed. Review the output above.")

if __name__ == "__main__":
    main() 