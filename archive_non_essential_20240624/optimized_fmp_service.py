#!/usr/bin/env python3
"""
Optimized Financial Modeling Prep (FMP) Service
Enhanced for FMP Starter membership with batch processing and advanced rate limiting
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from common_imports import (
    os, time, logging, requests, pd, datetime, timedelta, 
    psycopg2, DB_CONFIG, setup_logging, safe_get_numeric
)
from advanced_rate_limiter import get_advanced_rate_limiter, AdvancedRateLimiter
from database import DatabaseManager
from ratio_calculator import calculate_ratios, validate_ratios

# Setup logging
setup_logging('optimized_fmp')
logger = logging.getLogger(__name__)

# API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

class OptimizedFMPService:
    """
    Optimized FMP service with batch processing, intelligent caching,
    and advanced rate limiting for FMP Starter membership
    """
    
    def __init__(self):
        """Initialize the optimized FMP service"""
        if not FMP_API_KEY:
            raise ValueError("FMP_API_KEY environment variable is required")
        
        self.api_key = FMP_API_KEY
        self.rate_limiter = get_advanced_rate_limiter()
        self.db = DatabaseManager()
        
        # FMP-specific configuration
        self.max_batch_size = 100  # FMP allows up to 100 symbols per batch
        self.max_workers = 3       # Conservative concurrency for rate limiting
        self.request_timeout = 30
        
        # Cache configuration
        self.cache_duration = {
            'profile': timedelta(days=7),      # Company profiles change rarely
            'financials': timedelta(days=1),   # Financials update quarterly
            'ratios': timedelta(days=1),       # Ratios update with financials
            'quotes': timedelta(minutes=5)     # Real-time quotes
        }
        
        logger.info("Optimized FMP Service initialized")
    
    def fetch_batch_profiles(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch company profiles for multiple tickers in a single batch request
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to profile data
        """
        if not tickers:
            return {}
        
        # Optimize batch size based on available quota
        batch_size = self.rate_limiter.get_batch_size('fmp')
        batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
        
        results = {}
        
        for batch in batches:
            try:
                # Check rate limit
                if not self.rate_limiter.can_make_request('fmp', 'profile'):
                    logger.warning("FMP rate limit reached for profile batch")
                    break
                
                # Wait if needed
                self.rate_limiter.wait_if_needed('fmp')
                
                # Make batch request
                symbols = ','.join(batch)
                url = f"{FMP_BASE_URL}/profile/{symbols}"
                params = {'apikey': self.api_key}
                
                response = requests.get(url, params=params, timeout=self.request_timeout)
                
                # Record the request
                usage = self.rate_limiter.record_request('fmp', 'profile', batch_size=len(batch))
                logger.debug(f"FMP batch profile request: {usage}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle both single object and array responses
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'symbol' in item:
                                results[item['symbol']] = item
                    elif isinstance(data, dict) and 'symbol' in data:
                        results[data['symbol']] = data
                    
                    logger.info(f"Successfully fetched profiles for {len(data)} tickers")
                else:
                    logger.error(f"FMP profile batch request failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error fetching batch profiles: {e}")
                continue
        
        return results
    
    def fetch_batch_financials(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch financial statements for multiple tickers using batch processing
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to financial data
        """
        if not tickers:
            return {}
        
        # Optimize batch size
        batch_size = self.rate_limiter.get_batch_size('fmp')
        batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
        
        results = {}
        
        for batch in batches:
            try:
                # Check rate limit
                if not self.rate_limiter.can_make_request('fmp', 'financials'):
                    logger.warning("FMP rate limit reached for financials batch")
                    break
                
                # Wait if needed
                self.rate_limiter.wait_if_needed('fmp')
                
                # Fetch income statements in batch
                symbols = ','.join(batch)
                income_url = f"{FMP_BASE_URL}/income-statement/{symbols}"
                params = {'apikey': self.api_key, 'limit': 4}
                
                response = requests.get(income_url, params=params, timeout=self.request_timeout)
                
                # Record the request
                usage = self.rate_limiter.record_request('fmp', 'income_statement', batch_size=len(batch))
                logger.debug(f"FMP batch income request: {usage}")
                
                if response.status_code == 200:
                    income_data = response.json()
                    
                    # Process each ticker's income data
                    for item in income_data:
                        if isinstance(item, dict) and 'symbol' in item:
                            ticker = item['symbol']
                            
                            # Fetch balance sheet and cash flow for this ticker
                            balance_data = self._fetch_single_balance_sheet(ticker)
                            cash_data = self._fetch_single_cash_flow(ticker)
                            
                            # Combine financial data
                            financial_data = self._combine_financial_data(ticker, item, balance_data, cash_data)
                            if financial_data:
                                results[ticker] = financial_data
                
                else:
                    logger.error(f"FMP financials batch request failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error fetching batch financials: {e}")
                continue
        
        return results
    
    def _fetch_single_balance_sheet(self, ticker: str) -> List[Dict]:
        """Fetch balance sheet for a single ticker"""
        try:
            if not self.rate_limiter.can_make_request('fmp', 'balance_sheet'):
                return []
            
            self.rate_limiter.wait_if_needed('fmp')
            
            url = f"{FMP_BASE_URL}/balance-sheet-statement/{ticker}"
            params = {'apikey': self.api_key, 'limit': 4}
            
            response = requests.get(url, params=params, timeout=self.request_timeout)
            self.rate_limiter.record_request('fmp', 'balance_sheet', batch_size=1)
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching balance sheet for {ticker}: {e}")
        
        return []
    
    def _fetch_single_cash_flow(self, ticker: str) -> List[Dict]:
        """Fetch cash flow for a single ticker"""
        try:
            if not self.rate_limiter.can_make_request('fmp', 'cash_flow'):
                return []
            
            self.rate_limiter.wait_if_needed('fmp')
            
            url = f"{FMP_BASE_URL}/cash-flow-statement/{ticker}"
            params = {'apikey': self.api_key, 'limit': 4}
            
            response = requests.get(url, params=params, timeout=self.request_timeout)
            self.rate_limiter.record_request('fmp', 'cash_flow', batch_size=1)
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching cash flow for {ticker}: {e}")
        
        return []
    
    def _combine_financial_data(self, ticker: str, income_data: List[Dict], 
                               balance_data: List[Dict], cash_data: List[Dict]) -> Optional[Dict]:
        """Combine financial statement data for a ticker"""
        try:
            # Calculate TTM values from income statement
            ttm_values = self._calculate_ttm_values(income_data)
            
            # Get latest balance sheet data
            latest_balance = balance_data[0] if balance_data else {}
            
            # Get latest cash flow data
            latest_cash = cash_data[0] if cash_data else {}
            
            # Get current price from database
            current_price = self._get_current_price(ticker)
            
            # Calculate financial ratios
            ratios = calculate_ratios(
                revenue_ttm=ttm_values.get('revenue', 0),
                net_income_ttm=ttm_values.get('net_income', 0),
                total_assets=latest_balance.get('totalAssets', 0),
                total_equity=latest_balance.get('totalStockholdersEquity', 0),
                total_debt=latest_balance.get('totalDebt', 0),
                current_assets=latest_balance.get('totalCurrentAssets', 0),
                current_liabilities=latest_balance.get('totalCurrentLiabilities', 0),
                free_cash_flow=latest_cash.get('freeCashFlow', 0),
                shares_outstanding=latest_balance.get('totalSharesOutstanding', 0),
                current_price=current_price
            )
            
            return {
                'ticker': ticker,
                'data_source': 'fmp_optimized',
                'last_updated': datetime.now(),
                'ttm_values': ttm_values,
                'latest_balance': latest_balance,
                'latest_cash_flow': latest_cash,
                'calculated_ratios': ratios,
                'current_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Error combining financial data for {ticker}: {e}")
            return None
    
    def _calculate_ttm_values(self, income_data: List[Dict]) -> Dict[str, float]:
        """Calculate trailing twelve months values from quarterly data"""
        ttm_values = {
            'revenue': 0.0,
            'net_income': 0.0,
            'gross_profit': 0.0,
            'operating_income': 0.0,
            'ebitda': 0.0
        }
        
        # Sum last 4 quarters for TTM
        for quarter in income_data[:4]:
            ttm_values['revenue'] += float(quarter.get('revenue', 0))
            ttm_values['net_income'] += float(quarter.get('netIncome', 0))
            ttm_values['gross_profit'] += float(quarter.get('grossProfit', 0))
            ttm_values['operating_income'] += float(quarter.get('operatingIncome', 0))
            ttm_values['ebitda'] += float(quarter.get('ebitda', 0))
        
        return ttm_values
    
    def _get_current_price(self, ticker: str) -> float:
        """Get current price from daily_charts table"""
        try:
            query = """
                SELECT close FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """
            result = self.db.execute_query(query, (ticker,))
            if result and result[0][0]:
                return float(result[0][0])
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
        
        return 0.0
    
    def process_tickers_batch(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Process multiple tickers efficiently using batch processing
        
        Args:
            tickers: List of ticker symbols to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing {len(tickers)} tickers with optimized FMP service")
        
        start_time = time.time()
        results = {
            'successful': {},
            'failed': [],
            'usage_summary': {},
            'processing_time': 0
        }
        
        try:
            # Step 1: Fetch profiles in batch
            logger.info("Step 1: Fetching company profiles")
            profiles = self.fetch_batch_profiles(tickers)
            results['successful'].update(profiles)
            
            # Step 2: Fetch financials in batch
            logger.info("Step 2: Fetching financial statements")
            financials = self.fetch_batch_financials(tickers)
            
            # Merge financial data with profiles
            for ticker, financial_data in financials.items():
                if ticker in results['successful']:
                    results['successful'][ticker].update(financial_data)
                else:
                    results['successful'][ticker] = financial_data
            
            # Step 3: Store data in database
            logger.info("Step 3: Storing data in database")
            stored_count = 0
            for ticker, data in results['successful'].items():
                if self._store_fundamental_data(ticker, data):
                    stored_count += 1
                else:
                    results['failed'].append(ticker)
            
            # Step 4: Get usage summary
            results['usage_summary'] = self.rate_limiter.get_usage_summary('fmp')
            
            processing_time = time.time() - start_time
            results['processing_time'] = processing_time
            
            logger.info(f"Batch processing completed:")
            logger.info(f"  - Successful: {len(results['successful'])}")
            logger.info(f"  - Failed: {len(results['failed'])}")
            logger.info(f"  - Stored: {stored_count}")
            logger.info(f"  - Processing time: {processing_time:.2f}s")
            logger.info(f"  - FMP usage: {results['usage_summary']}")
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            results['failed'].extend(tickers)
        
        return results
    
    def _store_fundamental_data(self, ticker: str, data: Dict) -> bool:
        """Store fundamental data in database"""
        try:
            # Extract key metrics
            ttm_values = data.get('ttm_values', {})
            ratios = data.get('calculated_ratios', {})
            profile = data.get('profile', {})
            
            # Prepare data for storage
            fundamental_data = {
                'ticker': ticker,
                'revenue_ttm': ttm_values.get('revenue', 0),
                'net_income_ttm': ttm_values.get('net_income', 0),
                'gross_profit_ttm': ttm_values.get('gross_profit', 0),
                'operating_income_ttm': ttm_values.get('operating_income', 0),
                'ebitda_ttm': ttm_values.get('ebitda', 0),
                'total_assets': data.get('latest_balance', {}).get('totalAssets', 0),
                'total_equity': data.get('latest_balance', {}).get('totalStockholdersEquity', 0),
                'total_debt': data.get('latest_balance', {}).get('totalDebt', 0),
                'current_assets': data.get('latest_balance', {}).get('totalCurrentAssets', 0),
                'current_liabilities': data.get('latest_balance', {}).get('totalCurrentLiabilities', 0),
                'free_cash_flow': data.get('latest_cash_flow', {}).get('freeCashFlow', 0),
                'shares_outstanding': data.get('latest_balance', {}).get('totalSharesOutstanding', 0),
                'current_price': data.get('current_price', 0),
                'market_cap': profile.get('mktCap', 0),
                'pe_ratio': ratios.get('pe_ratio', 0),
                'pb_ratio': ratios.get('pb_ratio', 0),
                'debt_to_equity': ratios.get('debt_to_equity', 0),
                'current_ratio': ratios.get('current_ratio', 0),
                'roe': ratios.get('roe', 0),
                'roa': ratios.get('roa', 0),
                'gross_margin': ratios.get('gross_margin', 0),
                'operating_margin': ratios.get('operating_margin', 0),
                'net_margin': ratios.get('net_margin', 0),
                'data_source': 'fmp_optimized',
                'last_updated': datetime.now()
            }
            
            # Store in company_fundamentals table
            query = """
                INSERT INTO company_fundamentals (
                    ticker, revenue_ttm, net_income_ttm, gross_profit_ttm, operating_income_ttm,
                    ebitda_ttm, total_assets, total_equity, total_debt, current_assets,
                    current_liabilities, free_cash_flow, shares_outstanding, current_price,
                    market_cap, pe_ratio, pb_ratio, debt_to_equity, current_ratio,
                    roe, roa, gross_margin, operating_margin, net_margin,
                    data_source, last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (ticker) DO UPDATE SET
                    revenue_ttm = EXCLUDED.revenue_ttm,
                    net_income_ttm = EXCLUDED.net_income_ttm,
                    gross_profit_ttm = EXCLUDED.gross_profit_ttm,
                    operating_income_ttm = EXCLUDED.operating_income_ttm,
                    ebitda_ttm = EXCLUDED.ebitda_ttm,
                    total_assets = EXCLUDED.total_assets,
                    total_equity = EXCLUDED.total_equity,
                    total_debt = EXCLUDED.total_debt,
                    current_assets = EXCLUDED.current_assets,
                    current_liabilities = EXCLUDED.current_liabilities,
                    free_cash_flow = EXCLUDED.free_cash_flow,
                    shares_outstanding = EXCLUDED.shares_outstanding,
                    current_price = EXCLUDED.current_price,
                    market_cap = EXCLUDED.market_cap,
                    pe_ratio = EXCLUDED.pe_ratio,
                    pb_ratio = EXCLUDED.pb_ratio,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    current_ratio = EXCLUDED.current_ratio,
                    roe = EXCLUDED.roe,
                    roa = EXCLUDED.roa,
                    gross_margin = EXCLUDED.gross_margin,
                    operating_margin = EXCLUDED.operating_margin,
                    net_margin = EXCLUDED.net_margin,
                    data_source = EXCLUDED.data_source,
                    last_updated = EXCLUDED.last_updated
                )
            """
            
            values = (
                fundamental_data['ticker'], fundamental_data['revenue_ttm'],
                fundamental_data['net_income_ttm'], fundamental_data['gross_profit_ttm'],
                fundamental_data['operating_income_ttm'], fundamental_data['ebitda_ttm'],
                fundamental_data['total_assets'], fundamental_data['total_equity'],
                fundamental_data['total_debt'], fundamental_data['current_assets'],
                fundamental_data['current_liabilities'], fundamental_data['free_cash_flow'],
                fundamental_data['shares_outstanding'], fundamental_data['current_price'],
                fundamental_data['market_cap'], fundamental_data['pe_ratio'],
                fundamental_data['pb_ratio'], fundamental_data['debt_to_equity'],
                fundamental_data['current_ratio'], fundamental_data['roe'],
                fundamental_data['roa'], fundamental_data['gross_margin'],
                fundamental_data['operating_margin'], fundamental_data['net_margin'],
                fundamental_data['data_source'], fundamental_data['last_updated']
            )
            
            self.db.execute_query(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error storing fundamental data for {ticker}: {e}")
            return False
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        return self.rate_limiter.get_usage_summary('fmp')
    
    def get_alerts(self) -> List[Dict]:
        """Get rate limit alerts"""
        return self.rate_limiter.get_alerts('fmp')

def test_optimized_fmp_service():
    """Test the optimized FMP service"""
    print("🧪 Testing Optimized FMP Service")
    print("=" * 50)
    
    try:
        service = OptimizedFMPService()
        
        # Test with a small batch
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        print(f"Testing with {len(test_tickers)} tickers: {test_tickers}")
        
        # Process batch
        results = service.process_tickers_batch(test_tickers)
        
        print(f"\nResults:")
        print(f"  - Successful: {len(results['successful'])}")
        print(f"  - Failed: {len(results['failed'])}")
        print(f"  - Processing time: {results['processing_time']:.2f}s")
        
        # Show usage summary
        usage = service.get_usage_summary()
        print(f"\nFMP Usage Summary:")
        for key, value in usage.items():
            print(f"  - {key}: {value}")
        
        # Show alerts
        alerts = service.get_alerts()
        if alerts:
            print(f"\nAlerts:")
            for alert in alerts:
                print(f"  - {alert['alert_type']}: {alert['message']}")
        
        print("\n✅ Optimized FMP Service test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_optimized_fmp_service() 