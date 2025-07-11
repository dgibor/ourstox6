#!/usr/bin/env python3
"""
Debug Large Cap Fundamentals Filler
Identify why the main filler isn't working
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests

from database import DatabaseManager
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FMP API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

class DebugLargeCapFiller:
    """Debug version to identify issues with the main filler"""
    
    def __init__(self):
        """Initialize the debug filler"""
        self.db = DatabaseManager()
        self.daily_calls = 0
        self.last_request_time = 0
        
        logger.info("Debug Large Cap Filler initialized")
    
    def test_api_key(self):
        """Test if the FMP API key is valid"""
        if not FMP_API_KEY:
            logger.error("❌ FMP_API_KEY not set in environment")
            return False
        
        try:
            url = f"{FMP_BASE_URL}/profile/AAPL"
            params = {'apikey': FMP_API_KEY}
            
            response = requests.get(url, params=params, timeout=10)
            self.daily_calls += 1
            
            if response.status_code == 200:
                logger.info("✅ FMP API key is valid")
                return True
            else:
                logger.error(f"❌ API test failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing API key: {e}")
            return False
    
    def get_test_tickers(self) -> List[Dict]:
        """Get a small sample of large cap tickers for testing"""
        try:
            query = """
                SELECT DISTINCT s.ticker, s.company_name, s.market_cap, s.sector, s.industry
                FROM stocks s
                LEFT JOIN company_fundamentals cf ON s.ticker = cf.ticker
                WHERE s.ticker IS NOT NULL 
                AND s.market_cap IS NOT NULL 
                AND s.market_cap >= 10000000000  -- $10B minimum
                AND (cf.ticker IS NULL OR 
                     cf.revenue IS NULL OR cf.revenue = 0 OR
                     cf.total_assets IS NULL OR cf.total_assets = 0 OR
                     cf.total_equity IS NULL OR cf.total_equity = 0 OR
                     cf.shares_outstanding IS NULL OR cf.shares_outstanding = 0 OR
                     cf.last_updated < %s)
                ORDER BY s.market_cap DESC
                LIMIT 5
            """
            cutoff_date = datetime.now() - timedelta(days=7)
            result = self.db.execute_query(query, (cutoff_date,))
            
            tickers = []
            for row in result:
                tickers.append({
                    'ticker': row[0],
                    'company_name': row[1],
                    'market_cap': row[2],
                    'sector': row[3],
                    'industry': row[4]
                })
            
            logger.info(f"Found {len(tickers)} test tickers")
            return tickers
            
        except Exception as e:
            logger.error(f"Error getting test tickers: {e}")
            return []
    
    def test_batch_income_statement(self, tickers: List[str]) -> Dict[str, Any]:
        """Test batch income statement API call"""
        if not tickers:
            return {}
        
        try:
            symbols = ','.join(tickers)
            url = f"{FMP_BASE_URL}/income-statement/{symbols}"
            params = {'apikey': FMP_API_KEY, 'limit': 4}
            
            logger.info(f"Testing batch income statement API call for: {symbols}")
            logger.info(f"URL: {url}")
            
            response = requests.get(url, params=params, timeout=30)
            self.daily_calls += 1
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data type: {type(data)}")
                logger.info(f"Response data length: {len(data) if isinstance(data, list) else 'Not a list'}")
                
                if isinstance(data, list):
                    logger.info(f"First item keys: {list(data[0].keys()) if data else 'No data'}")
                    
                    # Count data by ticker
                    ticker_counts = {}
                    for item in data:
                        if isinstance(item, dict) and 'symbol' in item:
                            ticker = item['symbol']
                            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
                    
                    logger.info(f"Data counts by ticker: {ticker_counts}")
                
                return data
            else:
                logger.error(f"API request failed: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error testing batch income statement: {e}")
            return {}
    
    def test_single_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        """Test single balance sheet API call"""
        try:
            url = f"{FMP_BASE_URL}/balance-sheet-statement/{ticker}"
            params = {'apikey': FMP_API_KEY, 'limit': 4}
            
            logger.info(f"Testing balance sheet API call for: {ticker}")
            
            response = requests.get(url, params=params, timeout=30)
            self.daily_calls += 1
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Balance sheet data type: {type(data)}")
                logger.info(f"Balance sheet data length: {len(data) if isinstance(data, list) else 'Not a list'}")
                
                if isinstance(data, list) and data:
                    logger.info(f"Latest balance sheet keys: {list(data[0].keys())}")
                    logger.info(f"Total assets: {data[0].get('totalAssets', 'Not found')}")
                    logger.info(f"Total equity: {data[0].get('totalStockholdersEquity', 'Not found')}")
                    logger.info(f"Shares outstanding: {data[0].get('totalSharesOutstanding', 'Not found')}")
                
                return data
            else:
                logger.error(f"Balance sheet API request failed: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error testing balance sheet for {ticker}: {e}")
            return {}
    
    def test_database_update(self, ticker: str, test_data: Dict) -> bool:
        """Test database update with sample data"""
        try:
            logger.info(f"Testing database update for {ticker}")
            
            # Create a simple test record
            query = """
                INSERT INTO company_fundamentals (
                    ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                    revenue, gross_profit, operating_income, net_income, ebitda,
                    total_assets, total_debt, total_equity, free_cash_flow, shares_outstanding,
                    price_to_earnings, price_to_book, debt_to_equity_ratio, current_ratio,
                    return_on_equity, return_on_assets, gross_margin, operating_margin, net_margin,
                    data_source, last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (ticker) DO UPDATE SET
                    revenue = EXCLUDED.revenue,
                    gross_profit = EXCLUDED.gross_profit,
                    operating_income = EXCLUDED.operating_income,
                    net_income = EXCLUDED.net_income,
                    ebitda = EXCLUDED.ebitda,
                    total_assets = EXCLUDED.total_assets,
                    total_debt = EXCLUDED.total_debt,
                    total_equity = EXCLUDED.total_equity,
                    free_cash_flow = EXCLUDED.free_cash_flow,
                    shares_outstanding = EXCLUDED.shares_outstanding,
                    price_to_earnings = EXCLUDED.price_to_earnings,
                    price_to_book = EXCLUDED.price_to_book,
                    debt_to_equity_ratio = EXCLUDED.debt_to_equity_ratio,
                    current_ratio = EXCLUDED.current_ratio,
                    return_on_equity = EXCLUDED.return_on_equity,
                    return_on_assets = EXCLUDED.return_on_assets,
                    gross_margin = EXCLUDED.gross_margin,
                    operating_margin = EXCLUDED.operating_margin,
                    net_margin = EXCLUDED.net_margin,
                    data_source = EXCLUDED.data_source,
                    last_updated = EXCLUDED.last_updated
                )
            """
            
            values = (
                ticker,
                datetime.now().date(),  # report_date
                'TTM',  # period_type
                2024,  # fiscal_year
                1,  # fiscal_quarter
                1000000000,  # revenue
                500000000,  # gross_profit
                200000000,  # operating_income
                150000000,  # net_income
                250000000,  # ebitda
                5000000000,  # total_assets
                1000000000,  # total_debt
                3000000000,  # total_equity
                100000000,  # free_cash_flow
                100000000,  # shares_outstanding
                15.0,  # price_to_earnings
                2.5,  # price_to_book
                0.33,  # debt_to_equity_ratio
                1.5,  # current_ratio
                0.05,  # return_on_equity
                0.03,  # return_on_assets
                0.50,  # gross_margin
                0.20,  # operating_margin
                0.15,  # net_margin
                'debug_test',  # data_source
                datetime.now()  # last_updated
            )
            
            self.db.execute_query(query, values)
            logger.info(f"✅ Database update test successful for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database update test failed for {ticker}: {e}")
            return False
    
    def run_debug_tests(self):
        """Run all debug tests"""
        logger.info("🔍 Starting debug tests for large cap fundamentals filler")
        logger.info("=" * 60)
        
        # Test 1: API Key
        logger.info("\n📋 Test 1: FMP API Key")
        logger.info("-" * 30)
        if not self.test_api_key():
            logger.error("❌ API key test failed - cannot proceed")
            return
        
        # Test 2: Get test tickers
        logger.info("\n📋 Test 2: Get Test Tickers")
        logger.info("-" * 30)
        test_tickers = self.get_test_tickers()
        if not test_tickers:
            logger.error("❌ No test tickers found - cannot proceed")
            return
        
        logger.info(f"✅ Found {len(test_tickers)} test tickers")
        for ticker_info in test_tickers:
            market_cap_b = ticker_info['market_cap'] / 1_000_000_000
            logger.info(f"  - {ticker_info['ticker']}: ${market_cap_b:.1f}B - {ticker_info['company_name']}")
        
        # Test 3: Batch income statement
        logger.info("\n📋 Test 3: Batch Income Statement API")
        logger.info("-" * 30)
        ticker_symbols = [t['ticker'] for t in test_tickers]
        income_data = self.test_batch_income_statement(ticker_symbols)
        
        if not income_data:
            logger.error("❌ Batch income statement test failed")
            return
        
        # Test 4: Single balance sheet
        logger.info("\n📋 Test 4: Single Balance Sheet API")
        logger.info("-" * 30)
        test_ticker = test_tickers[0]['ticker']
        balance_data = self.test_single_balance_sheet(test_ticker)
        
        if not balance_data:
            logger.error("❌ Balance sheet test failed")
            return
        
        # Test 5: Database update
        logger.info("\n📋 Test 5: Database Update")
        logger.info("-" * 30)
        if not self.test_database_update(test_ticker, {}):
            logger.error("❌ Database update test failed")
            return
        
        # Summary
        logger.info("\n📊 Debug Test Summary")
        logger.info("=" * 60)
        logger.info(f"✅ API Key: Valid")
        logger.info(f"✅ Test Tickers: {len(test_tickers)} found")
        logger.info(f"✅ Batch Income API: Working")
        logger.info(f"✅ Balance Sheet API: Working")
        logger.info(f"✅ Database Update: Working")
        logger.info(f"📈 API Calls Used: {self.daily_calls}")
        
        logger.info("\n🎯 Debug tests completed successfully!")
        logger.info("The main filler should work. Check the main script for other issues.")

def main():
    """Main debug function"""
    print("🔍 Debug Large Cap Fundamentals Filler")
    print("=" * 50)
    print("This will test each component to identify issues")
    print()
    
    try:
        debugger = DebugLargeCapFiller()
        debugger.run_debug_tests()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 