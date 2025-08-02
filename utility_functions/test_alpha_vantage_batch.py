#!/usr/bin/env python3
"""
Test script to fetch a batch of prices from Alpha Vantage and log the response.
"""
import os
import sys
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TEST - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_alpha_vantage_batch():
    logger.info("🧪 Testing Alpha Vantage Batch Price Fetch")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        daily_run_dir = os.path.join(current_dir, 'daily_run')
        sys.path.insert(0, daily_run_dir)
        from daily_run.alpha_vantage_service import AlphaVantageService
        service = AlphaVantageService()
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        logger.info(f"Fetching batch prices for: {test_tickers}")
        symbols = ','.join(test_tickers)
        url = f"{service.base_url}/query"
        params = {
            'function': 'BATCH_STOCK_QUOTES',
            'symbols': symbols,
            'apikey': service.api_key
        }
        logger.info(f"[ALPHA VANTAGE DEBUG] Requesting: {url} with params: {params}")
        response = service.session.get(url, params=params)
        logger.info(f"[ALPHA VANTAGE DEBUG] Status: {response.status_code}, Response: {str(response.text)[:500]}")
        response.raise_for_status()
        data = response.json()
        logger.info(f"[ALPHA VANTAGE DEBUG] Parsed JSON: {str(data)[:500]}")
        if 'Stock Quotes' in data:
            logger.info(f"✅ Alpha Vantage returned {len(data['Stock Quotes'])} quotes.")
        else:
            logger.warning(f"⚠️  Alpha Vantage did not return 'Stock Quotes' in response.")
        return True
    except Exception as e:
        logger.error(f"❌ Alpha Vantage batch test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_alpha_vantage_batch()
    sys.exit(0 if success else 1) 