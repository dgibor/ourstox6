#!/usr/bin/env python3
"""
Financial Modeling Prep (FMP) Service for fundamental data
"""

import os
import psycopg2
import logging
import requests
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
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

class FMPService:
    """Financial Modeling Prep API service for fundamental data"""
    
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

    def fetch_financial_statements(self, ticker: str) -> Optional[Dict]:
        """Fetch financial statements from FMP API with rate limiting"""
        for attempt in range(self.max_retries):
            try:
                # Check API limit before making request
                provider = 'fmp'
                endpoint = 'financials'
                if self.api_limiter and not self.api_limiter.check_limit(provider, endpoint):
                    logging.warning(f"FMP API limit reached for {ticker}")
                    return None

                # Fetch income statement
                income_url = f"{FMP_BASE_URL}/income-statement/{ticker}"
                params = {'apikey': FMP_API_KEY, 'limit': 4}  # Get last 4 quarters for TTM
                
                response = requests.get(income_url, params=params, timeout=30)
                
                if self.api_limiter:
                    self.api_limiter.record_call(provider, endpoint)
                
                if response.status_code == 200:
                    income_data = response.json()
                    if income_data:
                        # Fetch balance sheet
                        balance_url = f"{FMP_BASE_URL}/balance-sheet-statement/{ticker}"
                        balance_response = requests.get(balance_url, params=params, timeout=30)
                        
                        if self.api_limiter:
                            self.api_limiter.record_call(provider, 'balance_sheet')
                        
                        balance_data = balance_response.json() if balance_response.status_code == 200 else []
                        
                        # Fetch cash flow
                        cash_url = f"{FMP_BASE_URL}/cash-flow-statement/{ticker}"
                        cash_response = requests.get(cash_url, params=params, timeout=30)
                        
                        if self.api_limiter:
                            self.api_limiter.record_call(provider, 'cash_flow')
                        
                        cash_data = cash_response.json() if cash_response.status_code == 200 else []
                        
                        # Parse and standardize data
                        financial_data = self.parse_financial_data(ticker, income_data, balance_data, cash_data)
                        
                        if financial_data:
                            logging.info(f"Successfully fetched FMP financial data for {ticker}")
                            return financial_data
                
                logging.warning(f"No financial data available for {ticker} from FMP")
                return None
                    
            except Exception as e:
                if 'rate limit' in str(e).lower() or '429' in str(e):
                    if attempt < self.max_retries - 1:
                        wait_time = self.base_delay * (2 ** attempt)
                        logging.warning(f"FMP rate limited for {ticker}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logging.error(f"Error fetching FMP financial statements for {ticker}: {e}")
                break
        
        return None

    def fetch_key_statistics(self, ticker: str) -> Optional[Dict]:
        """Fetch key statistics from FMP API"""
        for attempt in range(self.max_retries):
            try:
                provider = 'fmp'
                endpoint = 'key_statistics'
                if self.api_limiter and not self.api_limiter.check_limit(provider, endpoint):
                    logging.warning(f"FMP API limit reached for {ticker}")
                    return None

                # Fetch company profile and key metrics
                profile_url = f"{FMP_BASE_URL}/profile/{ticker}"
                params = {'apikey': FMP_API_KEY}
                
                response = requests.get(profile_url, params=params, timeout=30)
                
                if self.api_limiter:
                    self.api_limiter.record_call(provider, endpoint)
                
                if response.status_code == 200:
                    profile_data = response.json()
                    
                    # Handle case where profile_data is a list
                    if isinstance(profile_data, list) and len(profile_data) > 0:
                        profile_data = profile_data[0]
                    
                    if profile_data and isinstance(profile_data, dict):
                        # Fetch key metrics
                        metrics_url = f"{FMP_BASE_URL}/key-metrics/{ticker}"
                        metrics_response = requests.get(metrics_url, params={'apikey': FMP_API_KEY, 'limit': 1}, timeout=30)
                        
                        if self.api_limiter:
                            self.api_limiter.record_call(provider, 'key_metrics')
                        
                        metrics_data = metrics_response.json() if metrics_response.status_code == 200 else []
                        
                        # Parse key statistics
                        key_stats = self.parse_key_statistics(ticker, profile_data, metrics_data)
                        
                        if key_stats:
                            logging.info(f"Successfully fetched FMP key statistics for {ticker}")
                            return key_stats
                
                logging.warning(f"No key statistics available for {ticker} from FMP")
                return None
                    
            except Exception as e:
                if 'rate limit' in str(e).lower() or '429' in str(e):
                    if attempt < self.max_retries - 1:
                        wait_time = self.base_delay * (2 ** attempt)
                        logging.warning(f"FMP rate limited for {ticker}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logging.error(f"Error fetching FMP key statistics for {ticker}: {e}")
                break
        
        return None

    def parse_financial_data(self, ticker: str, income_data: list, balance_data: list, cash_data: list) -> Optional[Dict]:
        """Parse and standardize FMP financial statement data"""
        try:
            financial_data = {
                'ticker': ticker,
                'data_source': 'fmp',
                'last_updated': datetime.now(),
                'income_statement': {},
                'balance_sheet': {},
                'cash_flow': {}
            }
            
            # Parse income statement and calculate TTM
            if income_data:
                # Calculate TTM from last 4 quarters
                ttm_revenue = sum(float(q.get('revenue', 0)) for q in income_data[:4] if q.get('revenue'))
                ttm_net_income = sum(float(q.get('netIncome', 0)) for q in income_data[:4] if q.get('netIncome'))
                ttm_gross_profit = sum(float(q.get('grossProfit', 0)) for q in income_data[:4] if q.get('grossProfit'))
                ttm_operating_income = sum(float(q.get('operatingIncome', 0)) for q in income_data[:4] if q.get('operatingIncome'))
                
                # Calculate EBITDA (approximate if not provided)
                ttm_ebitda = sum(float(q.get('ebitda', 0)) for q in income_data[:4] if q.get('ebitda'))
                if not ttm_ebitda and ttm_operating_income:
                    # Approximate EBITDA as operating income + depreciation + amortization
                    ttm_depreciation = sum(float(q.get('depreciationAndAmortization', 0)) for q in income_data[:4] if q.get('depreciationAndAmortization'))
                    ttm_ebitda = ttm_operating_income + ttm_depreciation
                
                latest_quarter = income_data[0]
                
                # Fix fiscal year parsing - handle 'FY' and other non-numeric values
                fiscal_year = datetime.now().year
                try:
                    calendar_year = latest_quarter.get('calendarYear')
                    if calendar_year and str(calendar_year).isdigit():
                        fiscal_year = int(calendar_year)
                except (ValueError, TypeError):
                    pass
                
                fiscal_quarter = 1
                try:
                    period = latest_quarter.get('period')
                    if period and str(period).isdigit():
                        fiscal_quarter = int(period)
                except (ValueError, TypeError):
                    pass
                
                financial_data['income_statement'] = {
                    'revenue': ttm_revenue,
                    'revenue_annual': float(latest_quarter.get('revenue', 0)),
                    'gross_profit': ttm_gross_profit,
                    'operating_income': ttm_operating_income,
                    'net_income': ttm_net_income,
                    'ebitda': ttm_ebitda,
                    'fiscal_year': fiscal_year,
                    'fiscal_quarter': fiscal_quarter,
                    'ttm_periods': min(len(income_data), 4)
                }
            
            # Parse balance sheet
            if balance_data:
                latest_balance = balance_data[0]
                
                # Fix fiscal year parsing for balance sheet
                balance_fiscal_year = datetime.now().year
                try:
                    calendar_year = latest_balance.get('calendarYear')
                    if calendar_year and str(calendar_year).isdigit():
                        balance_fiscal_year = int(calendar_year)
                except (ValueError, TypeError):
                    pass
                
                financial_data['balance_sheet'] = {
                    'total_assets': float(latest_balance.get('totalAssets', 0)),
                    'total_debt': float(latest_balance.get('totalDebt', 0)),
                    'total_equity': float(latest_balance.get('totalStockholdersEquity', 0)),
                    'cash_and_equivalents': float(latest_balance.get('cashAndCashEquivalents', 0)),
                    'current_assets': float(latest_balance.get('totalCurrentAssets', 0)),
                    'current_liabilities': float(latest_balance.get('totalCurrentLiabilities', 0)),
                    'fiscal_year': balance_fiscal_year
                }
            
            # Parse cash flow
            if cash_data:
                latest_cash = cash_data[0]
                
                # Fix fiscal year parsing for cash flow
                cash_fiscal_year = datetime.now().year
                try:
                    calendar_year = latest_cash.get('calendarYear')
                    if calendar_year and str(calendar_year).isdigit():
                        cash_fiscal_year = int(calendar_year)
                except (ValueError, TypeError):
                    pass
                
                financial_data['cash_flow'] = {
                    'operating_cash_flow': float(latest_cash.get('operatingCashFlow', 0)),
                    'free_cash_flow': float(latest_cash.get('freeCashFlow', 0)),
                    'capex': float(latest_cash.get('capitalExpenditure', 0)),
                    'fiscal_year': cash_fiscal_year
                }
            
            return financial_data
            
        except Exception as e:
            logging.error(f"Error parsing FMP financial data for {ticker}: {e}")
            return None

    def parse_key_statistics(self, ticker: str, profile_data: dict, metrics_data: list) -> Optional[Dict]:
        """Parse FMP key statistics and ratios"""
        try:
            key_stats = {
                'ticker': ticker,
                'data_source': 'fmp',
                'last_updated': datetime.now(),
                'market_data': {},
                'ratios': {},
                'per_share_metrics': {}
            }
            
            # Market data from profile
            key_stats['market_data'] = {
                'market_cap': float(profile_data.get('mktCap', 0)),
                'enterprise_value': float(profile_data.get('enterpriseValue', 0)),
                'shares_outstanding': float(profile_data.get('sharesOutstanding', 0)),
                'current_price': float(profile_data.get('price', 0))
            }
            
            # Key ratios from metrics - fix list object error
            if metrics_data and isinstance(metrics_data, list) and len(metrics_data) > 0:
                latest_metrics = metrics_data[0]
                if isinstance(latest_metrics, dict):
                    key_stats['ratios'] = {
                        'pe_ratio': float(latest_metrics.get('peRatio', 0)),
                        'pb_ratio': float(latest_metrics.get('pbRatio', 0)),
                        'ps_ratio': float(latest_metrics.get('priceToSalesRatio', 0)),
                        'ev_ebitda': float(latest_metrics.get('enterpriseValueOverEBITDA', 0)),
                        'roe': float(latest_metrics.get('roe', 0)),
                        'roa': float(latest_metrics.get('roa', 0)),
                        'debt_to_equity': float(latest_metrics.get('debtToEquityRatio', 0)),
                        'current_ratio': float(latest_metrics.get('currentRatio', 0)),
                        'gross_margin': float(latest_metrics.get('grossProfitMargin', 0)),
                        'operating_margin': float(latest_metrics.get('operatingProfitMargin', 0)),
                        'net_margin': float(latest_metrics.get('netProfitMargin', 0))
                    }
                    
                    key_stats['per_share_metrics'] = {
                        'eps_diluted': float(latest_metrics.get('eps', 0)),
                        'book_value_per_share': float(latest_metrics.get('bookValuePerShare', 0)),
                        'cash_per_share': float(latest_metrics.get('cashPerShare', 0)),
                        'revenue_per_share': float(latest_metrics.get('revenuePerShare', 0))
                    }
            
            return key_stats
            
        except Exception as e:
            logging.error(f"Error parsing FMP key statistics for {ticker}: {e}")
            return None

    def store_fundamental_data(self, ticker: str, financial_data: Dict, key_stats: Dict) -> bool:
        """Store comprehensive fundamental data in the database"""
        try:
            # Extract data from financial_data and key_stats for insertion
            income = financial_data.get('income_statement', {}) if financial_data else {}
            balance = financial_data.get('balance_sheet', {}) if financial_data else {}
            cash_flow = financial_data.get('cash_flow', {}) if financial_data else {}
            market_data = key_stats.get('market_data', {}) if key_stats else {}
            per_share = key_stats.get('per_share_metrics', {}) if key_stats else {}

            # Prepare a dictionary of all columns to update in the 'stocks' table
            update_data = {
                'market_cap': market_data.get('market_cap'),
                'enterprise_value': market_data.get('enterprise_value'),
                'shares_outstanding': market_data.get('shares_outstanding'),
                'revenue_ttm': income.get('revenue'),
                'net_income_ttm': income.get('net_income'),
                'ebitda_ttm': income.get('ebitda'),
                'diluted_eps_ttm': per_share.get('eps_diluted'),
                'book_value_per_share': per_share.get('book_value_per_share'),
                'total_debt': balance.get('total_debt'),
                'shareholders_equity': balance.get('total_equity'),
                'cash_and_equivalents': balance.get('cash_and_equivalents'),
                'total_assets': balance.get('total_assets'),
                'current_assets': balance.get('current_assets'),
                'current_liabilities': balance.get('current_liabilities'),
                'operating_income': income.get('operating_income'),
                'free_cash_flow': cash_flow.get('free_cash_flow'),
                'fundamentals_last_update': datetime.now()
            }

            # Log TTM calculations for debugging
            if income.get('revenue'):
                logging.info(f"{ticker} FMP TTM Revenue: ${income.get('revenue'):,.0f} (from {income.get('ttm_periods', 1)} periods)")
                if income.get('revenue_annual'):
                    logging.info(f"{ticker} FMP Annual Revenue: ${income.get('revenue_annual'):,.0f}")
            if income.get('net_income'):
                logging.info(f"{ticker} FMP TTM Net Income: ${income.get('net_income'):,.0f}")
            if income.get('ebitda'):
                logging.info(f"{ticker} FMP TTM EBITDA: ${income.get('ebitda'):,.0f}")

            # Filter out None values to avoid overwriting existing data with NULL
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                logging.warning(f"No new data to update for {ticker}")
                return False

            # Build the SET part of the SQL query dynamically
            set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
            values = list(update_data.values()) + [ticker]

            # Execute the update query
            self.cur.execute(f"""
                UPDATE stocks 
                SET {set_clause}
                WHERE ticker = %s
            """, tuple(values))

            # Store in company_fundamentals table
            if financial_data and financial_data.get('income_statement'):
                income = financial_data['income_statement']
                balance = financial_data.get('balance_sheet', {})
                cash = financial_data.get('cash_flow', {})
                
                self.cur.execute("""
                    INSERT INTO company_fundamentals 
                    (ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                     revenue, gross_profit, operating_income, net_income, ebitda,
                     data_source, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, fiscal_year, fiscal_quarter, period_type)
                    DO UPDATE SET
                        revenue = COALESCE(EXCLUDED.revenue, company_fundamentals.revenue),
                        gross_profit = COALESCE(EXCLUDED.gross_profit, company_fundamentals.gross_profit),
                        operating_income = COALESCE(EXCLUDED.operating_income, company_fundamentals.operating_income),
                        net_income = COALESCE(EXCLUDED.net_income, company_fundamentals.net_income),
                        ebitda = COALESCE(EXCLUDED.ebitda, company_fundamentals.ebitda),
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    ticker, datetime.now().date(), 'ttm', income.get('fiscal_year'), income.get('fiscal_quarter'),
                    income.get('revenue'), income.get('gross_profit'),
                    income.get('operating_income'), income.get('net_income'),
                    income.get('ebitda'), 'fmp', datetime.now()
                ))
            
            self.conn.commit()
            logging.info(f"Successfully stored FMP fundamental data for {ticker}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing FMP fundamental data for {ticker}: {e}")
            self.conn.rollback()
            return False

    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Main method to fetch and store fundamental data for a ticker"""
        try:
            # Fetch financial statements
            financial_data = self.fetch_financial_statements(ticker)
            
            # Fetch key statistics
            key_stats = self.fetch_key_statistics(ticker)
            
            # Store data if available
            if financial_data or key_stats:
                success = self.store_fundamental_data(ticker, financial_data, key_stats)
                if success:
                    return {
                        'financial_data': financial_data,
                        'key_stats': key_stats
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting FMP fundamental data for {ticker}: {e}")
            return None

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
    service = FMPService()
    test_ticker = args.ticker
    result = service.get_fundamental_data(test_ticker)
    if result:
        print(f"Successfully fetched FMP fundamental data for {test_ticker}")
        if result.get('financial_data'):
            print(f"Financial data keys: {list(result['financial_data'].keys())}")
        if result.get('key_stats'):
            print(f"Key stats keys: {list(result['key_stats'].keys())}")
    else:
        print(f"Failed to fetch FMP fundamental data for {test_ticker}")
    service.close() 