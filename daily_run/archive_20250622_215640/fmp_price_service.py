#!/usr/bin/env python3
"""
Financial Modeling Prep (FMP) Price Service
"""

import os
import psycopg2
import logging
import requests
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

class FMPPriceService:
    """Financial Modeling Prep API service for price data"""
    
    def __init__(self):
        """Initialize database connection and API rate limiter"""
        self.api_limiter = None
        try:
            from utility_functions.api_rate_limiter import APIRateLimiter
            self.api_limiter = APIRateLimiter()
        except ImportError:
            logging.warning("API rate limiter not available")
        
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.max_retries = 3
        self.base_delay = 2  # seconds
        
        if not FMP_API_KEY:
            logging.error("FMP_API_KEY not found in environment variables")
            raise ValueError("FMP_API_KEY is required")

    def get_fmp_price(self, ticker: str) -> Optional[Dict]:
        """Get price from FMP API with rate limiting"""
        provider = 'fmp'
        endpoint = 'quote'
        
        if self.api_limiter and not self.api_limiter.check_limit(provider, endpoint):
            logging.warning(f"FMP API limit reached, skipping {ticker}")
            return None
            
        try:
            url = f"{FMP_BASE_URL}/quote/{ticker}"
            params = {'apikey': FMP_API_KEY}
            
            response = requests.get(url, params=params, timeout=30)
            
            if self.api_limiter:
                self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0]  # Return first (and usually only) quote
                elif data and isinstance(data, dict):
                    return data
            return None
            
        except Exception as e:
            logging.error(f"FMP API error for {ticker}: {e}")
            return None

    def collect_fmp_prices(self, tickers: List[str]) -> Tuple[Dict[str, dict], List[str]]:
        """Collect prices using FMP API and return price data"""
        prices_data = {}
        failed = []
        
        for ticker in tickers[:500]:  # Limit to 500 calls to preserve quota
            try:
                data = self.get_fmp_price(ticker)
                if data and data.get('price') is not None:
                    # Convert FMP data to our format
                    prices_data[ticker] = {
                        'open': int(round(float(data.get('open', data.get('price', 0))) * 100)),
                        'high': int(round(float(data.get('dayHigh', data.get('price', 0))) * 100)),
                        'low': int(round(float(data.get('dayLow', data.get('price', 0))) * 100)),
                        'close': int(round(float(data.get('price', 0)) * 100)),
                        'volume': int(data.get('volume', 0)) if data.get('volume') else None
                    }
                    logging.info(f"Successfully got FMP price for {ticker}")
                else:
                    failed.append(ticker)
                time.sleep(2)  # Rate limiting - 2 seconds between calls
            except Exception as e:
                logging.error(f"Error processing {ticker} with FMP: {e}")
                failed.append(ticker)
        
        return prices_data, failed

    def get_fmp_historical_price(self, ticker: str, start_date: str, end_date: str) -> Optional[Dict]:
        """Get historical price data from FMP API"""
        provider = 'fmp'
        endpoint = 'historical_price'
        
        if self.api_limiter and not self.api_limiter.check_limit(provider, endpoint):
            logging.warning(f"FMP API limit reached for historical data, skipping {ticker}")
            return None
            
        try:
            url = f"{FMP_BASE_URL}/historical-price-full/{ticker}"
            params = {
                'apikey': FMP_API_KEY,
                'from': start_date,
                'to': end_date
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if self.api_limiter:
                self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'historical' in data:
                    return data['historical']
            return None
            
        except Exception as e:
            logging.error(f"FMP historical API error for {ticker}: {e}")
            return None

    def update_database(self, prices_data: Dict):
        """Update database with collected prices"""
        try:
            self.cur.execute("BEGIN")
            
            for ticker, data in prices_data.items():
                self.cur.execute("""
                    INSERT INTO daily_charts (ticker, date, open, high, low, close, volume)
                    VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """, (
                    ticker,
                    data.get('open'),
                    data.get('high'),
                    data.get('low'),
                    data.get('close'),
                    data.get('volume')
                ))
            
            self.conn.commit()
            logging.info(f"Successfully updated {len(prices_data)} FMP price records in database")
            
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Database update error: {e}")
            raise

    def get_api_remaining_quota(self, provider: str, endpoint: str) -> int:
        """Utility to check remaining quota for a provider/endpoint"""
        if not self.api_limiter:
            return 1000  # Default FMP free tier limit
            
        today = datetime.utcnow().date()
        self.api_limiter.cur.execute(
            "SELECT calls_made, calls_limit FROM api_usage_tracking WHERE api_provider=%s AND date=%s AND endpoint=%s",
            (provider, today, endpoint)
        )
        row = self.api_limiter.cur.fetchone()
        if row:
            calls_made, calls_limit = row
            return max(0, calls_limit - calls_made)
        else:
            return 1000  # Default FMP free tier limit

    def close(self):
        """Close database connections"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        if self.api_limiter:
            self.api_limiter.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', type=str, default='AAPL', help='Ticker symbol to fetch')
    args = parser.parse_args()
    
    service = FMPPriceService()
    test_ticker = args.ticker
    
    # Test single price fetch
    price_data = service.get_fmp_price(test_ticker)
    if price_data:
        print(f"Successfully fetched FMP price for {test_ticker}:")
        print(f"  Price: ${price_data.get('price', 0):.2f}")
        print(f"  Open: ${price_data.get('open', 0):.2f}")
        print(f"  High: ${price_data.get('dayHigh', 0):.2f}")
        print(f"  Low: ${price_data.get('dayLow', 0):.2f}")
        print(f"  Volume: {price_data.get('volume', 0):,}")
    else:
        print(f"Failed to fetch FMP price for {test_ticker}")
    
    service.close() 