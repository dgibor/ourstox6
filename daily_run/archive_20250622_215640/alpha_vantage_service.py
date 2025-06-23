import os
import time
import logging
import requests
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
from typing import Dict, Optional, List, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utility_functions.api_rate_limiter import APIRateLimiter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/alpha_vantage_service.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

class AlphaVantageService:
    def __init__(self):
        self.api_limiter = APIRateLimiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.base_url = "https://www.alphavantage.co/query"
        self.max_retries = 1  # Minimal retries due to rate limits
        self.cache_duration = timedelta(hours=24)  # 24-hour cache

    def check_cache(self, ticker: str) -> Optional[Dict]:
        """Check if we have recent cached data for this ticker"""
        try:
            self.cur.execute("""
                SELECT last_updated FROM company_fundamentals 
                WHERE ticker = %s AND data_source = 'alphavantage'
                ORDER BY last_updated DESC LIMIT 1
            """, (ticker,))
            
            result = self.cur.fetchone()
            if result:
                last_updated = result[0]
                if datetime.now() - last_updated < self.cache_duration:
                    logging.info(f"Using cached Alpha Vantage data for {ticker}")
                    return {'cached': True, 'last_updated': last_updated}
            
            return None
            
        except Exception as e:
            logging.error(f"Error checking cache for {ticker}: {e}")
            return None

    def fetch_income_statement(self, ticker: str) -> Optional[Dict]:
        """Fetch annual income statement from Alpha Vantage"""
        try:
            # Check API limit before making request
            provider = 'alphavantage'
            endpoint = 'INCOME_STATEMENT'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
                return None

            params = {
                'function': 'INCOME_STATEMENT',
                'symbol': ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(self.base_url, params=params)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if 'annualReports' in data and data['annualReports']:
                    # Get most recent annual report
                    annual_data = data['annualReports'][0]
                    return self.parse_income_statement(ticker, annual_data)
            
            return None
            
        except Exception as e:
            logging.error(f"Error fetching income statement for {ticker}: {e}")
            return None

    def fetch_balance_sheet(self, ticker: str) -> Optional[Dict]:
        """Fetch annual balance sheet from Alpha Vantage"""
        try:
            provider = 'alphavantage'
            endpoint = 'BALANCE_SHEET'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
                return None

            params = {
                'function': 'BALANCE_SHEET',
                'symbol': ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(self.base_url, params=params)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if 'annualReports' in data and data['annualReports']:
                    # Get most recent annual report
                    annual_data = data['annualReports'][0]
                    return self.parse_balance_sheet(ticker, annual_data)
            
            return None
            
        except Exception as e:
            logging.error(f"Error fetching balance sheet for {ticker}: {e}")
            return None

    def fetch_cash_flow(self, ticker: str) -> Optional[Dict]:
        """Fetch annual cash flow statement from Alpha Vantage"""
        try:
            provider = 'alphavantage'
            endpoint = 'CASH_FLOW'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
                return None

            params = {
                'function': 'CASH_FLOW',
                'symbol': ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(self.base_url, params=params)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if 'annualReports' in data and data['annualReports']:
                    # Get most recent annual report
                    annual_data = data['annualReports'][0]
                    return self.parse_cash_flow(ticker, annual_data)
            
            return None
            
        except Exception as e:
            logging.error(f"Error fetching cash flow for {ticker}: {e}")
            return None

    def parse_income_statement(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse Alpha Vantage income statement data"""
        try:
            income_data = {
                'ticker': ticker,
                'data_source': 'alphavantage',
                'last_updated': datetime.now(),
                'fiscal_year': int(data.get('fiscalDateEnding', '2023').split('-')[0]),
                'revenue': self.safe_get_numeric(data, 'totalRevenue'),
                'gross_profit': self.safe_get_numeric(data, 'grossProfit'),
                'operating_income': self.safe_get_numeric(data, 'operatingIncome'),
                'net_income': self.safe_get_numeric(data, 'netIncome'),
                'ebitda': self.safe_get_numeric(data, 'ebitda')
            }
            
            return income_data
            
        except Exception as e:
            logging.error(f"Error parsing income statement for {ticker}: {e}")
            return None

    def parse_balance_sheet(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse Alpha Vantage balance sheet data"""
        try:
            balance_data = {
                'ticker': ticker,
                'data_source': 'alphavantage',
                'last_updated': datetime.now(),
                'fiscal_year': int(data.get('fiscalDateEnding', '2023').split('-')[0]),
                'total_assets': self.safe_get_numeric(data, 'totalAssets'),
                'total_debt': self.safe_get_numeric(data, 'totalLiabilities'),
                'total_equity': self.safe_get_numeric(data, 'totalShareholderEquity'),
                'cash_and_equivalents': self.safe_get_numeric(data, 'cashAndCashEquivalentsAtCarryingValue'),
                'current_assets': self.safe_get_numeric(data, 'totalCurrentAssets'),
                'current_liabilities': self.safe_get_numeric(data, 'totalCurrentLiabilities'),
                'shares_outstanding': self.safe_get_numeric(data, 'commonStockSharesOutstanding')
            }
            
            return balance_data
            
        except Exception as e:
            logging.error(f"Error parsing balance sheet for {ticker}: {e}")
            return None

    def parse_cash_flow(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse Alpha Vantage cash flow data"""
        try:
            cash_flow_data = {
                'ticker': ticker,
                'data_source': 'alphavantage',
                'last_updated': datetime.now(),
                'fiscal_year': int(data.get('fiscalDateEnding', '2023').split('-')[0]),
                'operating_cash_flow': self.safe_get_numeric(data, 'operatingCashflow'),
                'free_cash_flow': self.safe_get_numeric(data, 'operatingCashflow'),  # Approximate
                'capex': self.safe_get_numeric(data, 'capitalExpenditures')
            }
            
            return cash_flow_data
            
        except Exception as e:
            logging.error(f"Error parsing cash flow for {ticker}: {e}")
            return None

    def safe_get_numeric(self, data: Dict, key: str) -> Optional[float]:
        """Safely get numeric value from Alpha Vantage data"""
        try:
            value = data.get(key)
            if value is not None and value != 'None' and value != '':
                return float(value)
            return None
        except (ValueError, TypeError) as e:
            logging.debug(f"Error converting {key} to numeric: {e}")
            return None

    def store_fundamental_data(self, ticker: str, data: dict) -> bool:
        """Store fundamental data in the database"""
        try:
            # Store in company_fundamentals table
            if 'income_statement' in data and data['income_statement']:
                income = data['income_statement']
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
                    ticker, income.get('report_date'), income.get('period_type'),
                    income.get('fiscal_year'), income.get('fiscal_quarter'),
                    income.get('revenue'), income.get('gross_profit'),
                    income.get('operating_income'), income.get('net_income'),
                    income.get('ebitda'), 'alpha_vantage', datetime.now()
                ))

            # Store in stocks table for shares_outstanding
            if 'key_stats' in data and data['key_stats']:
                key_stats = data['key_stats']
                shares_outstanding = key_stats.get('shares_outstanding')
                if shares_outstanding:
                    self.cur.execute("""
                        UPDATE stocks 
                        SET shares_outstanding = %s, last_updated = CURRENT_TIMESTAMP
                        WHERE ticker = %s
                    """, (shares_outstanding, ticker))

            self.conn.commit()
            logging.info(f"Successfully stored Alpha Vantage fundamental data for {ticker}")
            return True
        except Exception as e:
            logging.error(f"Error storing Alpha Vantage fundamental data for {ticker}: {e}")
            self.conn.rollback()
            return False

    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Main method to fetch and store Alpha Vantage fundamental data for a ticker"""
        try:
            # Check cache first
            cached_data = self.check_cache(ticker)
            if cached_data:
                return {'cached': True, 'data': cached_data}
            
            # Fetch data from Alpha Vantage (annual only)
            income_data = self.fetch_income_statement(ticker)
            balance_data = self.fetch_balance_sheet(ticker)
            cash_flow_data = self.fetch_cash_flow(ticker)
            
            # Store data if any is available
            if income_data or balance_data or cash_flow_data:
                success = self.store_fundamental_data(ticker, {
                    'income_statement': income_data,
                    'balance_sheet': balance_data,
                    'cash_flow': cash_flow_data
                })
                if success:
                    return {
                        'income_statement': income_data,
                        'balance_sheet': balance_data,
                        'cash_flow': cash_flow_data
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting Alpha Vantage fundamental data for {ticker}: {e}")
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
    # Test the service
    service = AlphaVantageService()
    test_ticker = "AAPL"
    result = service.get_fundamental_data(test_ticker)
    if result:
        if result.get('cached'):
            print(f"Using cached Alpha Vantage data for {test_ticker}")
        else:
            print(f"Successfully fetched Alpha Vantage fundamental data for {test_ticker}")
            if result.get('income_statement'):
                print(f"Income data available: {list(result['income_statement'].keys())}")
            if result.get('balance_sheet'):
                print(f"Balance data available: {list(result['balance_sheet'].keys())}")
    else:
        print(f"Failed to fetch Alpha Vantage fundamental data for {test_ticker}")
    service.close() 