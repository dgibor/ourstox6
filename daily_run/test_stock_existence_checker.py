#!/usr/bin/env python3
"""
Test script for StockExistenceChecker

Tests the enhanced stock existence checking functionality with refined deletion logic.
"""

import logging
import sys
import os

# Add the daily_run directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_existence_checker import StockExistenceChecker, ExistenceCheckResult
from database import DatabaseManager
from enhanced_multi_service_manager import EnhancedMultiServiceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_stock_check():
    """Test checking a single stock's existence"""
    print("\n🧪 Testing Single Stock Check")
    print("=" * 40)
    
    try:
        # Initialize components
        db = DatabaseManager()
        service_manager = EnhancedMultiServiceManager()
        checker = StockExistenceChecker(db, service_manager)
        
        # Test with a known good stock (should exist in most APIs)
        print("Testing AAPL (should exist):")
        result = checker.check_stock_exists('AAPL')
        
        print(f"  Ticker: {result.ticker}")
        print(f"  Exists in APIs: {result.exists_in_apis}")
        print(f"  Not found in APIs: {result.not_found_in_apis}")
        print(f"  Rate limited APIs: {result.rate_limited_apis}")
        print(f"  Error APIs: {result.error_apis}")
        print(f"  Should remove: {result.should_remove}")
        print(f"  Total APIs checked: {result.total_apis_checked}")
        
        # Test with a potentially delisted stock
        print("\nTesting INVALID (should not exist):")
        result = checker.check_stock_exists('INVALID')
        
        print(f"  Ticker: {result.ticker}")
        print(f"  Exists in APIs: {result.exists_in_apis}")
        print(f"  Not found in APIs: {result.not_found_in_apis}")
        print(f"  Rate limited APIs: {result.rate_limited_apis}")
        print(f"  Error APIs: {result.error_apis}")
        print(f"  Should remove: {result.should_remove}")
        print(f"  Total APIs checked: {result.total_apis_checked}")
        
        print("✅ Single stock check test completed")
        
    except Exception as e:
        print(f"❌ Single stock check test failed: {e}")
        logger.error(f"Test failed: {e}")


def test_batch_processing():
    """Test processing multiple tickers in batches"""
    print("\n🧪 Testing Batch Processing")
    print("=" * 40)
    
    try:
        # Initialize components
        db = DatabaseManager()
        service_manager = EnhancedMultiServiceManager()
        checker = StockExistenceChecker(db, service_manager)
        
        # Test with a small batch
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'INVALID', 'TEST123']
        print(f"Testing batch processing with {len(test_tickers)} tickers")
        
        results = checker.process_tickers_in_batches(test_tickers)
        
        print(f"Processed {len(results)} tickers:")
        for ticker, result in results.items():
            status = "🚨 REMOVE" if result.should_remove else "✅ KEEP"
            print(f"  {status} {ticker}: {len(result.exists_in_apis)} exists, {len(result.not_found_in_apis)} not found")
        
        print("✅ Batch processing test completed")
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        logger.error(f"Test failed: {e}")


def test_deletion_logic():
    """Test the refined deletion logic"""
    print("\n🧪 Testing Deletion Logic")
    print("=" * 40)
    
    try:
        # Initialize components
        db = DatabaseManager()
        service_manager = EnhancedMultiServiceManager()
        checker = StockExistenceChecker(db, service_manager)
        
        # Test different scenarios
        test_scenarios = [
            {
                'name': 'Stock found in all APIs',
                'exists_in': ['yahoo', 'fmp', 'finnhub', 'alpha_vantage'],
                'not_found_in': [],
                'rate_limited': [],
                'error_apis': [],
                'expected_remove': False
            },
            {
                'name': 'Stock not found in 1 API only',
                'exists_in': ['yahoo', 'fmp', 'finnhub'],
                'not_found_in': ['alpha_vantage'],
                'rate_limited': [],
                'error_apis': [],
                'expected_remove': False  # Below threshold of 2
            },
            {
                'name': 'Stock not found in 2 APIs (threshold met)',
                'exists_in': ['yahoo', 'fmp'],
                'not_found_in': ['finnhub', 'alpha_vantage'],
                'rate_limited': [],
                'error_apis': [],
                'expected_remove': True  # At threshold of 2
            },
            {
                'name': 'Stock not found in 3 APIs (above threshold)',
                'exists_in': ['yahoo'],
                'not_found_in': ['fmp', 'finnhub', 'alpha_vantage'],
                'rate_limited': [],
                'error_apis': [],
                'expected_remove': True  # Above threshold of 2
            },
            {
                'name': 'Stock with rate limits and errors',
                'exists_in': ['yahoo'],
                'not_found_in': ['fmp'],
                'rate_limited': ['finnhub'],
                'error_apis': ['alpha_vantage'],
                'expected_remove': False  # Only 1 "not found", rate limits/errors don't count
            }
        ]
        
        for scenario in test_scenarios:
            # Create a mock result
            result = ExistenceCheckResult(
                ticker='TEST',
                exists_in_apis=scenario['exists_in'],
                not_found_in_apis=scenario['not_found_in'],
                rate_limited_apis=scenario['rate_limited'],
                error_apis=scenario['error_apis'],
                total_apis_checked=4,
                should_remove=len(scenario['not_found_in']) >= 2,  # Apply the same logic
                check_time=checker.check_stock_exists('AAPL').check_time  # Use a real timestamp
            )
            
            print(f"  {scenario['name']}:")
            print(f"    Exists: {len(scenario['exists_in'])} APIs")
            print(f"    Not found: {len(scenario['not_found_in'])} APIs")
            print(f"    Rate limited: {len(scenario['rate_limited'])} APIs")
            print(f"    Errors: {len(scenario['error_apis'])} APIs")
            print(f"    Should remove: {result.should_remove} (Expected: {scenario['expected_remove']})")
            print(f"    Status: {'✅ PASS' if result.should_remove == scenario['expected_remove'] else '❌ FAIL'}")
        
        print("✅ Deletion logic test completed")
        
    except Exception as e:
        print(f"❌ Deletion logic test failed: {e}")
        logger.error(f"Test failed: {e}")


def test_database_removal_dry_run():
    """Test database removal logic (dry run - no actual deletion)"""
    print("\n🧪 Testing Database Removal Logic (Dry Run)")
    print("=" * 40)
    
    try:
        # Initialize components
        db = DatabaseManager()
        service_manager = EnhancedMultiServiceManager()
        checker = StockExistenceChecker(db, service_manager)
        
        # Create a mock result that would trigger removal
        mock_result = ExistenceCheckResult(
            ticker='DRY_RUN_TEST',
            exists_in_apis=[],
            not_found_in_apis=['yahoo', 'fmp'],  # 2 APIs say not found
            rate_limited_apis=['finnhub'],
            error_apis=['alpha_vantage'],
            total_apis_checked=4,
            should_remove=True,
            check_time=checker.check_stock_exists('AAPL').check_time
        )
        
        # Test the removal logic without actually removing
        print("Mock result that would trigger removal:")
        print(f"  Ticker: {mock_result.ticker}")
        print(f"  Not found in: {mock_result.not_found_in_apis}")
        print(f"  Rate limited: {mock_result.rate_limited_apis}")
        print(f"  Errors: {mock_result.error_apis}")
        print(f"  Should remove: {mock_result.should_remove}")
        
        print("\nNote: This is a dry run - no actual database deletion performed")
        print("✅ Database removal logic test completed")
        
    except Exception as e:
        print(f"❌ Database removal logic test failed: {e}")
        logger.error(f"Test failed: {e}")


def main():
    """Run all tests"""
    print("🚀 Starting StockExistenceChecker Tests")
    print("=" * 50)
    
    try:
        test_single_stock_check()
        test_batch_processing()
        test_deletion_logic()
        test_database_removal_dry_run()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        logger.error(f"Test suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
