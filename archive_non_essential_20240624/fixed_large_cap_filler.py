#!/usr/bin/env python3
"""
Fixed Large Cap Fundamentals Filler
Process all large cap companies (market cap $10B+) missing fundamental data
Uses single-ticker requests with proper rate limiting (300 calls/minute)
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

class FixedLargeCapFundamentalsFiller:
    """Fill fundamental data for large cap companies using single-ticker requests"""
    
    def __init__(self):
        """Initialize the filler"""
        self.db = DatabaseManager()
        
        # Processing configuration
        self.batch_size = 50  # Process in batches of 50 for progress tracking
        self.max_retries = 3
        self.request_timeout = 30
        
        # Rate limiting: 200 calls per minute = 1 call every 0.3 seconds
        self.calls_per_minute = 200
        self.min_delay_between_calls = 60.0 / self.calls_per_minute  # 0.3 seconds
        
        # Progress tracking
        self.total_tickers = 0
        self.processed_tickers = 0
        self.successful_updates = 0
        self.failed_updates = 0
        self.start_time = None
        
        # Rate limiting tracking
        self.api_calls_made = 0
        self.last_request_time = 0
        
        logger.info("Fixed Large Cap Fundamentals Filler initialized")
        logger.info(f"Rate limit: {self.calls_per_minute} calls per minute")
        logger.info(f"Delay between calls: {self.min_delay_between_calls:.2f} seconds")
    
    def setup_api_key(self):
        """Setup FMP API key if not already set"""
        global FMP_API_KEY
        
        if not FMP_API_KEY:
            print("\n🔑 FMP API Key Setup Required")
            print("=" * 40)
            print("You need to set your FMP API key to proceed.")
            print("You can get your API key from: https://financialmodelingprep.com/developer/docs/")
            print()
            
            try:
                api_key = input("Enter your FMP API key: ").strip()
                if api_key:
                    # Set environment variable for current session
                    os.environ['FMP_API_KEY'] = api_key
                    FMP_API_KEY = api_key
                    logger.info("✅ FMP API key set for current session")
                    
                    # Test the API key
                    if self.test_api_key(api_key):
                        logger.info("✅ FMP API key is valid")
                        return True
                    else:
                        logger.error("❌ FMP API key is invalid")
                        return False
                else:
                    logger.error("❌ No API key provided")
                    return False
            except KeyboardInterrupt:
                logger.info("Setup cancelled by user")
                return False
        else:
            logger.info("✅ FMP API key already set")
            return True
    
    def test_api_key(self, api_key):
        """Test if the FMP API key is valid"""
        try:
            # Test with a simple API call
            url = f"{FMP_BASE_URL}/profile/AAPL"
            params = {'apikey': api_key}
            
            response = requests.get(url, params=params, timeout=10)
            self.api_calls_made += 1
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"API test failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing API key: {e}")
            return False
    
    def get_large_cap_missing_tickers(self) -> List[Dict]:
        """Get large cap tickers (market cap $10B+) missing fundamental data"""
        try:
            # Get large cap tickers missing fundamental data
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
            
            logger.info(f"Found {len(tickers)} large cap tickers missing fundamental data")
            
            # Log top 20 by market cap
            if tickers:
                logger.info("Top 20 large cap missing tickers by market cap:")
                for i, ticker_info in enumerate(tickers[:20]):
                    market_cap_b = ticker_info['market_cap'] / 1_000_000_000
                    logger.info(f"  {i+1:2d}. {ticker_info['ticker']}: ${market_cap_b:.1f}B - {ticker_info['company_name']}")
            
            return tickers
            
        except Exception as e:
            logger.error(f"Error getting large cap missing tickers: {e}")
            return []
    
    def wait_for_rate_limit(self):
        """Wait between requests to respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay_between_calls:
            sleep_time = self.min_delay_between_calls - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def make_api_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make API request with rate limiting"""
        self.wait_for_rate_limit()
        
        try:
            response = requests.get(url, params=params, timeout=self.request_timeout)
            self.api_calls_made += 1
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.status_code} - {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error making API request: {e} - {url}")
            return None
    
    def fetch_single_ticker_financials(self, ticker: str) -> Optional[Dict]:
        """Fetch all financial data for a single ticker"""
        try:
            logger.debug(f"Fetching financials for {ticker}")
            
            # 1. Fetch income statement
            income_url = f"{FMP_BASE_URL}/income-statement/{ticker}"
            income_params = {'apikey': FMP_API_KEY, 'limit': 4}
            income_data = self.make_api_request(income_url, income_params)
            
            if not income_data or not isinstance(income_data, list):
                logger.warning(f"No income statement data for {ticker}")
                return None
            
            # 2. Fetch balance sheet
            balance_url = f"{FMP_BASE_URL}/balance-sheet-statement/{ticker}"
            balance_params = {'apikey': FMP_API_KEY, 'limit': 4}
            balance_data = self.make_api_request(balance_url, balance_params)
            
            if not balance_data or not isinstance(balance_data, list):
                logger.warning(f"No balance sheet data for {ticker}")
                return None
            
            # 3. Fetch cash flow
            cash_url = f"{FMP_BASE_URL}/cash-flow-statement/{ticker}"
            cash_params = {'apikey': FMP_API_KEY, 'limit': 4}
            cash_data = self.make_api_request(cash_url, cash_params)
            
            if not cash_data or not isinstance(cash_data, list):
                logger.warning(f"No cash flow data for {ticker}")
                return None
            
            # 4. Get current price
            current_price = self._get_current_price(ticker)
            
            # 5. Combine and process data
            financial_data = self._combine_financial_data(ticker, income_data, balance_data, cash_data, current_price)
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error fetching financials for {ticker}: {e}")
            return None
    
    def _combine_financial_data(self, ticker: str, income_data: List[Dict], 
                               balance_data: List[Dict], cash_data: List[Dict], 
                               current_price: float) -> Optional[Dict]:
        """Combine financial statement data for a ticker"""
        try:
            # Calculate TTM values from income statement
            ttm_values = self._calculate_ttm_values(income_data)
            
            # Get latest balance sheet data
            latest_balance = balance_data[0] if balance_data else {}
            
            # Get latest cash flow data
            latest_cash = cash_data[0] if cash_data else {}
            
            return {
                'ticker': ticker,
                'ttm_values': ttm_values,
                'latest_balance': latest_balance,
                'latest_cash_flow': latest_cash,
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
    
    def update_fundamental_record(self, ticker: str, data: Dict) -> bool:
        """Update fundamental record in database"""
        try:
            ttm_values = data.get('ttm_values', {})
            latest_balance = data.get('latest_balance', {})
            latest_cash = data.get('latest_cash_flow', {})
            current_price = data.get('current_price', 0)
            
            # Calculate ratios
            ratios = self._calculate_ratios(ttm_values, latest_balance, current_price)
            
            # Update or insert fundamental record
            query = """INSERT INTO company_fundamentals (
                ticker, report_date, period_type, fiscal_year, fiscal_quarter, revenue, gross_profit, operating_income, net_income, ebitda, total_assets, total_debt, total_equity, free_cash_flow, shares_outstanding, price_to_earnings, price_to_book, debt_to_equity_ratio, current_ratio, return_on_equity, return_on_assets, gross_margin, operating_margin, net_margin, data_source, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (ticker, report_date, period_type) DO UPDATE SET
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
                last_updated = EXCLUDED.last_updated"""
            
            # Get fiscal year and quarter from latest data
            fiscal_year = datetime.now().year
            fiscal_quarter = 1
            
            if latest_balance:
                try:
                    calendar_year = latest_balance.get('calendarYear')
                    if calendar_year and str(calendar_year).isdigit():
                        fiscal_year = int(calendar_year)
                    
                    period = latest_balance.get('period')
                    if period and str(period).isdigit():
                        fiscal_quarter = int(period)
                except (ValueError, TypeError):
                    pass
            
            values = (
                ticker,
                datetime.now().date(),  # report_date
                'TTM',  # period_type
                fiscal_year,
                fiscal_quarter,
                ttm_values.get('revenue', 0),
                ttm_values.get('gross_profit', 0),
                ttm_values.get('operating_income', 0),
                ttm_values.get('net_income', 0),
                ttm_values.get('ebitda', 0),
                latest_balance.get('totalAssets', 0),
                latest_balance.get('totalDebt', 0),
                latest_balance.get('totalStockholdersEquity', 0),
                latest_cash.get('freeCashFlow', 0),
                latest_balance.get('totalSharesOutstanding', 0),
                ratios.get('pe_ratio', 0),
                ratios.get('pb_ratio', 0),
                ratios.get('debt_to_equity', 0),
                ratios.get('current_ratio', 0),
                ratios.get('roe', 0),
                ratios.get('roa', 0),
                ratios.get('gross_margin', 0),
                ratios.get('operating_margin', 0),
                ratios.get('net_margin', 0),
                'fmp_single',  # data_source
                datetime.now()  # last_updated
            )
            
            self.db.execute_update(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error updating fundamental record for {ticker}: {e}")
            return False
    
    def _calculate_ratios(self, ttm_values: Dict, balance_data: Dict, current_price: float) -> Dict[str, float]:
        """Calculate financial ratios"""
        ratios = {}
        
        try:
            revenue = ttm_values.get('revenue', 0)
            net_income = ttm_values.get('net_income', 0)
            gross_profit = ttm_values.get('gross_profit', 0)
            operating_income = ttm_values.get('operating_income', 0)
            total_assets = balance_data.get('totalAssets', 0)
            total_equity = balance_data.get('totalStockholdersEquity', 0)
            total_debt = balance_data.get('totalDebt', 0)
            current_assets = balance_data.get('totalCurrentAssets', 0)
            current_liabilities = balance_data.get('totalCurrentLiabilities', 0)
            shares_outstanding = balance_data.get('totalSharesOutstanding', 0)
            
            # P/E Ratio
            if net_income > 0 and shares_outstanding > 0 and current_price > 0:
                eps = net_income / shares_outstanding
                ratios['pe_ratio'] = current_price / eps if eps > 0 else 0
            else:
                ratios['pe_ratio'] = 0
            
            # P/B Ratio
            if total_equity > 0 and shares_outstanding > 0 and current_price > 0:
                book_value_per_share = total_equity / shares_outstanding
                ratios['pb_ratio'] = current_price / book_value_per_share if book_value_per_share > 0 else 0
            else:
                ratios['pb_ratio'] = 0
            
            # Debt to Equity
            if total_equity > 0:
                ratios['debt_to_equity'] = total_debt / total_equity
            else:
                ratios['debt_to_equity'] = 0
            
            # Current Ratio
            if current_liabilities > 0:
                ratios['current_ratio'] = current_assets / current_liabilities
            else:
                ratios['current_ratio'] = 0
            
            # ROE
            if total_equity > 0:
                ratios['roe'] = net_income / total_equity
            else:
                ratios['roe'] = 0
            
            # ROA
            if total_assets > 0:
                ratios['roa'] = net_income / total_assets
            else:
                ratios['roa'] = 0
            
            # Margins
            if revenue > 0:
                ratios['gross_margin'] = gross_profit / revenue
                ratios['operating_margin'] = operating_income / revenue
                ratios['net_margin'] = net_income / revenue
            else:
                ratios['gross_margin'] = 0
                ratios['operating_margin'] = 0
                ratios['net_margin'] = 0
                
        except Exception as e:
            logger.error(f"Error calculating ratios: {e}")
            ratios = {key: 0 for key in ['pe_ratio', 'pb_ratio', 'debt_to_equity', 'current_ratio', 'roe', 'roa', 'gross_margin', 'operating_margin', 'net_margin']}
        
        return ratios
    
    def process_large_cap_fundamentals(self) -> Dict[str, Any]:
        """Process all large cap tickers missing fundamental data"""
        logger.info("🚀 Starting fixed large cap fundamentals filling process")
        
        self.start_time = time.time()
        
        # Setup API key if needed
        if not self.setup_api_key():
            logger.error("Cannot proceed without valid FMP API key")
            return self._get_empty_results()
        
        # Get large cap tickers missing fundamental data
        ticker_info_list = self.get_large_cap_missing_tickers()
        
        self.total_tickers = len(ticker_info_list)
        
        if not ticker_info_list:
            logger.info("No large cap tickers missing fundamental data")
            return self._get_empty_results()
        
        logger.info(f"Processing {self.total_tickers} large cap tickers missing fundamental data")
        logger.info(f"Estimated API calls needed: {self.total_tickers * 3} (3 per ticker)")
        logger.info(f"Estimated time: {self.total_tickers * 3 * self.min_delay_between_calls / 60:.1f} minutes")
        
        # Process tickers one by one
        results = {
            'successful': [],
            'failed': [],
            'api_calls_used': 0,
            'market_cap_processed': 0
        }
        
        for i, ticker_info in enumerate(ticker_info_list):
            ticker = ticker_info['ticker']
            market_cap = ticker_info['market_cap']
            
            try:
                logger.info(f"Processing {i+1}/{self.total_tickers}: {ticker} (${market_cap/1_000_000_000:.1f}B)")
                
                # Fetch financial data for this ticker
                financial_data = self.fetch_single_ticker_financials(ticker)
                
                if financial_data:
                    # Update database
                    if self.update_fundamental_record(ticker, financial_data):
                        self.successful_updates += 1
                        results['successful'].append({
                            'ticker': ticker,
                            'market_cap': market_cap,
                            'company_name': ticker_info['company_name']
                        })
                        logger.info(f"✅ Successfully updated {ticker}")
                    else:
                        self.failed_updates += 1
                        results['failed'].append({
                            'ticker': ticker,
                            'market_cap': market_cap,
                            'company_name': ticker_info['company_name']
                        })
                        logger.error(f"❌ Failed to update database for {ticker}")
                else:
                    self.failed_updates += 1
                    results['failed'].append({
                        'ticker': ticker,
                        'market_cap': market_cap,
                        'company_name': ticker_info['company_name']
                    })
                    logger.error(f"❌ No financial data available for {ticker}")
                
                self.processed_tickers += 1
                results['market_cap_processed'] += market_cap
                results['api_calls_used'] = self.api_calls_made
                
                # Progress logging every 10 tickers
                if (i + 1) % 10 == 0:
                    progress = (self.processed_tickers / self.total_tickers) * 100
                    success_rate = (self.successful_updates / self.processed_tickers) * 100
                    logger.info(f"Progress: {progress:.1f}% ({self.processed_tickers}/{self.total_tickers})")
                    logger.info(f"Success rate: {success_rate:.1f}% ({self.successful_updates} successful, {self.failed_updates} failed)")
                    logger.info(f"API calls used: {self.api_calls_made}")
                
            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {e}")
                self.failed_updates += 1
                results['failed'].append({
                    'ticker': ticker,
                    'market_cap': market_cap,
                    'company_name': ticker_info['company_name']
                })
                self.processed_tickers += 1
                results['market_cap_processed'] += market_cap
        
        # Final summary
        processing_time = time.time() - self.start_time
        results['processing_time'] = processing_time
        results['efficiency_metrics'] = self._calculate_efficiency_metrics()
        
        logger.info("✅ Fixed large cap fundamentals filling completed")
        logger.info(f"  - Total tickers: {self.total_tickers}")
        logger.info(f"  - Successful updates: {self.successful_updates}")
        logger.info(f"  - Failed updates: {self.failed_updates}")
        logger.info(f"  - Processing time: {processing_time:.2f}s")
        logger.info(f"  - API calls used: {self.api_calls_made}")
        
        return results
    
    def _calculate_efficiency_metrics(self) -> Dict[str, Any]:
        """Calculate processing efficiency metrics"""
        if self.total_tickers == 0:
            return {}
        
        processing_time = time.time() - self.start_time
        
        # Calculate metrics
        success_rate = (self.successful_updates / self.total_tickers) * 100
        tickers_per_minute = (self.total_tickers / processing_time) * 60
        api_calls_per_ticker = self.api_calls_made / max(self.total_tickers, 1)
        
        return {
            'success_rate_percent': success_rate,
            'tickers_per_minute': tickers_per_minute,
            'api_calls_per_ticker': api_calls_per_ticker,
            'processing_time_seconds': processing_time,
            'total_tickers': self.total_tickers,
            'successful_updates': self.successful_updates,
            'failed_updates': self.failed_updates,
            'api_calls_used': self.api_calls_made
        }
    
    def _get_empty_results(self) -> Dict[str, Any]:
        """Get empty results structure"""
        return {
            'successful': [],
            'failed': [],
            'api_calls_used': 0,
            'market_cap_processed': 0,
            'processing_time': 0,
            'efficiency_metrics': {}
        }

def main():
    """Main function to run the fixed large cap fundamentals filling process"""
    print("🚀 Starting Fixed Large Cap Fundamentals Filling Process")
    print("=" * 60)
    print("Processing all large cap companies (market cap $10B+) missing fundamental data")
    print("Using single-ticker requests with 300 calls/minute rate limiting")
    print()
    
    try:
        filler = FixedLargeCapFundamentalsFiller()
        
        # First, show what large cap companies are missing
        missing_tickers = filler.get_large_cap_missing_tickers()
        
        if not missing_tickers:
            print("✅ No large cap tickers missing fundamental data!")
            return
        
        print(f"📊 Found {len(missing_tickers)} large cap tickers missing fundamental data")
        print()
        
        # Show top 10 by market cap
        print("📈 TOP 10 LARGE CAP MISSING TICKERS BY MARKET CAP:")
        print("=" * 60)
        
        for i, ticker_info in enumerate(missing_tickers[:10]):
            market_cap_b = ticker_info['market_cap'] / 1_000_000_000
            print(f"{i+1:2d}. {ticker_info['ticker']:6s} - ${market_cap_b:8.1f}B - {ticker_info['company_name']}")
        
        print()
        
        # Calculate total market cap
        total_market_cap = sum(t['market_cap'] for t in missing_tickers)
        total_market_cap_b = total_market_cap / 1_000_000_000
        print(f"💰 Total market cap of missing companies: ${total_market_cap_b:.1f}B")
        print()
        
        # Calculate estimated time
        estimated_calls = len(missing_tickers) * 3
        estimated_minutes = estimated_calls * 0.2 / 60  # 0.2 seconds per call
        print(f"⏱️  Estimated API calls needed: {estimated_calls}")
        print(f"⏱️  Estimated processing time: {estimated_minutes:.1f} minutes")
        print()
        
        # Ask for confirmation
        print("This will process ALL large cap companies missing fundamental data.")
        print("Using single-ticker requests (more reliable than batch)")
        print()
        
        try:
            confirm = input("Proceed with processing all large cap companies? (y/N): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                # Process all large cap tickers
                results = filler.process_large_cap_fundamentals()
                
                # Print summary
                print(f"\n📊 Processing Summary:")
                print(f"  - Total tickers: {results.get('efficiency_metrics', {}).get('total_tickers', 0)}")
                print(f"  - Successful updates: {len(results['successful'])}")
                print(f"  - Failed updates: {len(results['failed'])}")
                print(f"  - Processing time: {results['processing_time']:.2f}s")
                
                # Show efficiency
                efficiency = results.get('efficiency_metrics', {})
                if efficiency:
                    print(f"  - Success rate: {efficiency.get('success_rate_percent', 0):.1f}%")
                    print(f"  - Tickers per minute: {efficiency.get('tickers_per_minute', 0):.1f}")
                    print(f"  - API calls used: {efficiency.get('api_calls_used', 0)}")
                
                # Show successful updates (top 10 by market cap)
                successful = results.get('successful', [])
                if successful:
                    print(f"\n✅ Successfully updated tickers (top 10 by market cap):")
                    for i, ticker_info in enumerate(successful[:10]):
                        market_cap_b = ticker_info['market_cap'] / 1_000_000_000
                        print(f"  {i+1:2d}. {ticker_info['ticker']}: ${market_cap_b:.1f}B - {ticker_info['company_name']}")
                    if len(successful) > 10:
                        print(f"  ... and {len(successful) - 10} more")
                
                # Show failed updates (top 10 by market cap)
                failed = results.get('failed', [])
                if failed:
                    print(f"\n❌ Failed tickers (top 10 by market cap):")
                    for i, ticker_info in enumerate(failed[:10]):
                        market_cap_b = ticker_info['market_cap'] / 1_000_000_000
                        print(f"  {i+1:2d}. {ticker_info['ticker']}: ${market_cap_b:.1f}B - {ticker_info['company_name']}")
                    if len(failed) > 10:
                        print(f"  ... and {len(failed) - 10} more")
                
                print("\n✅ Fixed large cap fundamentals filling completed")
                
            else:
                print("❌ Process cancelled by user")
                
        except KeyboardInterrupt:
            print("\n❌ Process cancelled by user")
        except Exception as e:
            print(f"\n❌ Process failed: {e}")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main() 