#!/usr/bin/env python3
"""
Test Service Fallback Logic for BatchPriceProcessor

This script simulates service failures and confirms that:
- Yahoo is always tried first (if available)
- Fallback to next service occurs on error or rate limit
- No service gets stuck (e.g., Finnhub)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_run'))

from daily_run.batch_price_processor import BatchPriceProcessor
from daily_run.database import DatabaseManager
import logging

# Setup logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mock_service_success(tickers):
    logger.info(f"Mock service called for: {tickers}")
    return {ticker: {'price': 100.0} for ticker in tickers}

def mock_service_fail(tickers):
    logger.info(f"Mock service FAIL for: {tickers}")
    raise Exception("Simulated service failure")

def test_fallback():
    db = DatabaseManager()
    processor = BatchPriceProcessor(db)
    # Override service_priority for test: Yahoo fails, Alpha Vantage fails, Finnhub succeeds
    processor.service_priority = [
        ('Yahoo Finance', mock_service_fail),
        ('Alpha Vantage', mock_service_fail),
        ('Finnhub', mock_service_success)
    ]
    tickers = ['AAPL', 'MSFT', 'GOOG']
    logger.info("\n=== TEST: Yahoo and Alpha Vantage fail, Finnhub succeeds ===")
    results = processor._process_single_batch(tickers, batch_num=1)
    assert results and all(t in results for t in tickers), "Fallback to Finnhub did not work"
    logger.info("Test passed: Fallback to Finnhub after Yahoo/Alpha Vantage failure")

    # Now test Yahoo succeeds immediately
    processor.service_priority = [
        ('Yahoo Finance', mock_service_success),
        ('Alpha Vantage', mock_service_fail),
        ('Finnhub', mock_service_fail)
    ]
    logger.info("\n=== TEST: Yahoo succeeds immediately ===")
    results = processor._process_single_batch(tickers, batch_num=2)
    assert results and all(t in results for t in tickers), "Yahoo should have succeeded immediately"
    logger.info("Test passed: Yahoo used as primary service")

    # Now test all fail
    processor.service_priority = [
        ('Yahoo Finance', mock_service_fail),
        ('Alpha Vantage', mock_service_fail),
        ('Finnhub', mock_service_fail)
    ]
    logger.info("\n=== TEST: All services fail ===")
    results = processor._process_single_batch(tickers, batch_num=3)
    assert not results, "Should return empty dict if all services fail"
    logger.info("Test passed: All services fail returns empty result")

if __name__ == "__main__":
    test_fallback()
    logger.info("All fallback tests completed successfully.") 