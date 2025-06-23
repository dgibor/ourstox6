#!/usr/bin/env python3
"""
Comprehensive Test Script for Stability and Performance Improvements
Tests all new systems: error handling, batch processing, monitoring, and enhanced services
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any
from common_imports import setup_logging, get_system_monitor
from enhanced_service_factory import get_enhanced_service_factory
from batch_processor import BatchProcessor
from error_handler import ErrorHandler, ServiceError, ErrorSeverity, ErrorCategory

def test_error_handling():
    """Test error handling system"""
    print("\n🧪 Testing Error Handling System")
    print("=" * 50)
    
    error_handler = ErrorHandler("test_service")
    
    # Test error classification
    test_errors = [
        ("Rate limit exceeded", "rate limit"),
        ("Connection timeout", "timeout"),
        ("Database connection failed", "database"),
        ("API key invalid", "config"),
        ("Unknown error", "system")
    ]
    
    for error_msg, expected_category in test_errors:
        try:
            raise Exception(error_msg)
        except Exception as e:
            error_info = error_handler.handle_error(e, {'test': True})
            print(f"✅ Error: {error_msg}")
            print(f"   Category: {error_info['category']}")
            print(f"   Severity: {error_info['severity']}")
    
    # Test custom service error
    try:
        raise ServiceError("test_service", "Test error", "AAPL", 
                          ErrorSeverity.HIGH, ErrorCategory.API_ERROR)
    except ServiceError as e:
        error_info = error_handler.handle_error(e, {'test': True})
        print(f"✅ Custom Service Error: {e.message}")
        print(f"   Category: {error_info['category']}")
        print(f"   Severity: {error_info['severity']}")
    
    # Get error summary
    summary = error_handler.get_error_summary()
    print(f"✅ Error Summary: {summary['total_errors']} total errors")
    
    return True

def test_batch_processing():
    """Test batch processing system"""
    print("\n🧪 Testing Batch Processing System")
    print("=" * 50)
    
    processor = BatchProcessor(max_workers=3, batch_size=5)
    
    # Test function that simulates API calls
    def test_processor(ticker: str) -> Dict[str, Any]:
        time.sleep(0.1)  # Simulate API delay
        if ticker == "FAIL":
            raise Exception("Simulated failure")
        return {"ticker": ticker, "data": "processed", "timestamp": datetime.now().isoformat()}
    
    # Test tickers
    test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "FAIL", "TSLA", "NVDA", "META", "NFLX", "ADBE"]
    
    print(f"Processing {len(test_tickers)} tickers...")
    result = processor.process_batch(test_tickers, test_processor, "test_service")
    
    print(f"✅ Batch Processing Results:")
    print(f"   Total: {result.total_processed}")
    print(f"   Successful: {result.total_successful}")
    print(f"   Failed: {result.total_failed}")
    print(f"   Processing Time: {result.processing_time:.2f}s")
    print(f"   Success Rate: {(result.total_successful/result.total_processed)*100:.1f}%")
    
    if result.errors:
        print(f"   Errors: {list(result.errors.keys())}")
    
    return result.total_successful > 0

def test_monitoring():
    """Test monitoring system"""
    print("\n🧪 Testing Monitoring System")
    print("=" * 50)
    
    monitor = get_system_monitor()
    
    if not monitor:
        print("⚠️ System monitor not available")
        return False
    
    # Test system metrics
    try:
        metrics = monitor.get_system_metrics()
        print(f"✅ System Metrics:")
        print(f"   CPU: {metrics.cpu_percent:.1f}%")
        print(f"   Memory: {metrics.memory_percent:.1f}%")
        print(f"   Disk: {metrics.disk_usage_percent:.1f}%")
    except Exception as e:
        print(f"❌ System metrics failed: {e}")
        return False
    
    # Test database health
    try:
        db_health = monitor.check_database_health()
        print(f"✅ Database Health: {db_health.status}")
        print(f"   Response Time: {db_health.response_time:.3f}s")
        print(f"   Active Connections: {db_health.details.get('active_connections', 'N/A')}")
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False
    
    # Test data quality
    try:
        stocks_quality = monitor.check_data_quality('stocks')
        print(f"✅ Stocks Data Quality:")
        print(f"   Total Records: {stocks_quality.total_records}")
        print(f"   Missing Data: {stocks_quality.missing_data_count}")
        print(f"   Duplicates: {stocks_quality.duplicate_count}")
        print(f"   Data Freshness: {stocks_quality.data_freshness_hours:.1f} hours")
    except Exception as e:
        print(f"❌ Data quality check failed: {e}")
        return False
    
    # Get system health summary
    try:
        health_summary = monitor.get_system_health_summary()
        print(f"✅ Overall System Status: {health_summary['overall_status']}")
        
        if health_summary['alerts']:
            print(f"   Alerts: {len(health_summary['alerts'])}")
            for alert in health_summary['alerts'][:3]:  # Show first 3 alerts
                print(f"     - {alert['level']}: {alert['message']}")
        
        # Save health report
        monitor.save_health_report("test_health_report.json")
        print("✅ Health report saved")
        
    except Exception as e:
        print(f"❌ Health summary failed: {e}")
        return False
    
    return True

def test_enhanced_services():
    """Test enhanced service factory"""
    print("\n🧪 Testing Enhanced Service Factory")
    print("=" * 50)
    
    factory = get_enhanced_service_factory()
    
    # Test service creation
    try:
        yahoo_service = factory.create_service("yahoo")
        print("✅ Yahoo service created successfully")
    except Exception as e:
        print(f"❌ Yahoo service creation failed: {e}")
        return False
    
    # Test service health
    try:
        health = factory.test_service_health("yahoo")
        print(f"✅ Yahoo service health: {health['status']}")
        print(f"   Fundamental Data: {health.get('fundamental_data_available', False)}")
        print(f"   Price Data: {health.get('price_data_available', False)}")
        print(f"   Response Time: {health.get('fundamental_response_time', 0):.3f}s")
    except Exception as e:
        print(f"❌ Service health test failed: {e}")
        return False
    
    # Test data retrieval
    try:
        data = yahoo_service.get_fundamental_data("AAPL")
        if data:
            print("✅ Fundamental data retrieval successful")
            print(f"   Data keys: {list(data.keys())}")
        else:
            print("⚠️ Fundamental data retrieval returned None")
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
        return False
    
    # Test batch processing with service
    try:
        batch_data = yahoo_service.get_fundamental_data_batch(["AAPL", "MSFT"])
        print(f"✅ Batch processing: {len(batch_data)} successful")
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return False
    
    # Test all services
    try:
        all_health = factory.test_all_services()
        print(f"✅ All services tested: {len(all_health)} services")
        for service_type, health in all_health.items():
            print(f"   {service_type}: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ All services test failed: {e}")
        return False
    
    # Get best service
    try:
        best_service = factory.get_best_service()
        print(f"✅ Best service: {best_service}")
    except Exception as e:
        print(f"❌ Best service selection failed: {e}")
        return False
    
    # Close services
    try:
        factory.close_all_services()
        print("✅ All services closed")
    except Exception as e:
        print(f"❌ Service cleanup failed: {e}")
        return False
    
    return True

def test_integration():
    """Test integration of all systems"""
    print("\n🧪 Testing System Integration")
    print("=" * 50)
    
    # Test that all systems work together
    try:
        # Create factory
        factory = get_enhanced_service_factory()
        
        # Get monitoring
        monitor = get_system_monitor()
        
        # Create batch processor
        processor = BatchProcessor(max_workers=2, batch_size=3)
        
        # Test end-to-end workflow
        test_tickers = ["AAPL", "MSFT", "GOOGL"]
        
        # Get service
        service = factory.get_service("yahoo")
        
        # Process batch
        def process_ticker(ticker: str):
            return service.get_fundamental_data(ticker)
        
        result = processor.process_batch(test_tickers, process_ticker, "integration_test")
        
        print(f"✅ Integration Test Results:")
        print(f"   Processed: {result.total_processed}")
        print(f"   Successful: {result.total_successful}")
        print(f"   Failed: {result.total_failed}")
        
        # Get system health
        health = monitor.get_system_health_summary()
        print(f"   System Status: {health['overall_status']}")
        
        # Cleanup
        factory.close_all_services()
        
        return result.total_successful > 0
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_performance_benchmark():
    """Run performance benchmark"""
    print("\n🧪 Performance Benchmark")
    print("=" * 50)
    
    # Test different batch sizes
    batch_sizes = [5, 10, 20]
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "ADBE", "CRM"]
    
    def benchmark_processor(ticker: str):
        time.sleep(0.05)  # Simulate API call
        return {"ticker": ticker, "data": "processed"}
    
    results = {}
    
    for batch_size in batch_sizes:
        processor = BatchProcessor(max_workers=3, batch_size=batch_size)
        start_time = time.time()
        
        result = processor.process_batch(tickers, benchmark_processor, f"benchmark_{batch_size}")
        
        total_time = time.time() - start_time
        throughput = len(tickers) / total_time
        
        results[batch_size] = {
            'total_time': total_time,
            'throughput': throughput,
            'success_rate': (result.total_successful / result.total_processed) * 100
        }
        
        print(f"✅ Batch Size {batch_size}:")
        print(f"   Time: {total_time:.2f}s")
        print(f"   Throughput: {throughput:.1f} tickers/sec")
        print(f"   Success Rate: {results[batch_size]['success_rate']:.1f}%")
    
    return results

def main():
    """Run all tests"""
    print("🚀 Starting Stability and Performance Tests")
    print("=" * 60)
    
    # Setup logging
    setup_logging("stability_tests")
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Error Handling", test_error_handling),
        ("Batch Processing", test_batch_processing),
        ("Monitoring", test_monitoring),
        ("Enhanced Services", test_enhanced_services),
        ("Integration", test_integration)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            test_results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} {test_name}")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results[test_name] = False
            import traceback
            traceback.print_exc()
    
    # Run performance benchmark
    try:
        benchmark_results = run_performance_benchmark()
        test_results["Performance Benchmark"] = True
    except Exception as e:
        print(f"❌ Performance benchmark failed: {e}")
        test_results["Performance Benchmark"] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! System is stable and performing well.")
    else:
        print("⚠️ Some tests failed. Review the output above for details.")
    
    # Save test results
    try:
        with open("logs/stability_test_results.json", "w") as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': test_results,
                'summary': {
                    'passed': passed,
                    'total': total,
                    'success_rate': passed/total*100
                }
            }, f, indent=2)
        print("✅ Test results saved to logs/stability_test_results.json")
    except Exception as e:
        print(f"❌ Failed to save test results: {e}")

if __name__ == "__main__":
    main() 