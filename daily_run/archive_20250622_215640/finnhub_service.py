import os
import time
import logging
import requests
from datetime import datetime
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
        logging.FileHandler('daily_run/logs/finnhub_service.log'),
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

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

# Finnhub data field mapping to our schema
FINNHUB_MAPPING = {
    'revenue': 'revenue',
    'net_income': 'netIncome',
    'total_debt': 'totalDebt',
    'total_assets': 'totalAssets',
    'total_equity': 'totalEquity',
    'cash': 'cash',
    'current_assets': 'totalCurrentAssets',
    'current_liabilities': 'totalCurrentLiabilities',
    'operating_income': 'operatingIncome',
    'gross_profit': 'grossProfit',
    'ebitda': 'ebitda',
    'operating_cash_flow': 'operatingCashFlow',
    'free_cash_flow': 'freeCashFlow',
    'capex': 'capitalExpenditure',
    'shares_outstanding': 'sharesOutstanding'
}

class FinnhubService:
    def __init__(self):
        self.api_limiter = APIRateLimiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.base_url = "https://finnhub.io/api/v1"
        self.max_retries = 2
        self.base_delay = 1  # seconds

    def fetch_financial_statements(self, ticker: str) -> Optional[Dict]:
        """Fetch financial statements from Finnhub with rate limiting"""
        for attempt in range(self.max_retries):
            try:
                # Check API limit before making request
                provider = 'finnhub'
                endpoint = 'financials'
                if not self.api_limiter.check_limit(provider, endpoint):
                    logging.warning(f"Finnhub API limit reached for {ticker}")
                    return None

                # Fetch income statement
                income_url = f"{self.base_url}/stock/financials-reported"
                params = {
                    'symbol': ticker,
                    'token': FINNHUB_API_KEY
                }
                
                response = requests.get(income_url, params=params)
                self.api_limiter.record_call(provider, endpoint)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and 'data' in data and data['data']:
                        financial_data = self.parse_finnhub_financials(ticker, data['data'])
                        if financial_data:
                            logging.info(f"Successfully fetched Finnhub financial data for {ticker}")
                            return financial_data
                
                logging.warning(f"No financial data available for {ticker} from Finnhub")
                return None
                    
            except Exception as e:
                delay = self.base_delay * (2 ** attempt)
                logging.error(f"Attempt {attempt + 1} failed for {ticker}: {e}")
                if attempt < self.max_retries - 1:
                    logging.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logging.error(f"All retry attempts failed for {ticker}")
                    return None
        
        return None

    def fetch_company_profile(self, ticker: str) -> Optional[Dict]:
        """Fetch company profile and key metrics from Finnhub"""
        try:
            provider = 'finnhub'
            endpoint = 'company_profile'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Finnhub API limit reached for {ticker}")
                return None

            profile_url = f"{self.base_url}/stock/profile2"
            params = {
                'symbol': ticker,
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(profile_url, params=params)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    profile_data = self.parse_company_profile(ticker, data)
                    if profile_data:
                        logging.info(f"Successfully fetched company profile for {ticker}")
                        return profile_data
            
            return None
            
        except Exception as e:
            logging.error(f"Error fetching company profile for {ticker}: {e}")
            return None

    def parse_finnhub_financials(self, ticker: str, data: List[Dict]) -> Optional[Dict]:
        """Parse Finnhub financial data using dynamic keyword matching."""
        try:
            if not data:
                return None
            
            latest_data = data[0]
            report = latest_data.get('report', {})
            
            # Create a flattened dictionary of all report items for easy searching
            all_reports = {item['label'].lower(): item['value'] for section in ['ic', 'bs', 'cf'] for item in report.get(section, [])}

            # This mapping holds keywords to dynamically find the correct label
            KEYWORD_MAP = {
                'revenue': ['revenue', 'sales'],
                'net_income': ['net income', 'netincomeloss'],
                'shareholders_equity': ['shareholder', 'equity'],
                'shares_outstanding': ['diluted (in shares)', 'shares outstanding'],
                'total_debt': ['total liabilities'],
                'cash_and_equivalents': ['cash and cash equivalents'],
                'operating_income': ['operating income'],
                'interest_expense': ['interest expense'],
                'tax_expense': ['income tax', 'provision for income taxes'],
                'depreciation_amortization': ['depreciation', 'amortization']
            }

            parsed_data = {}
            for field, keywords in KEYWORD_MAP.items():
                for keyword in keywords:
                    for label, value in all_reports.items():
                        if keyword in label:
                            parsed_data[field] = float(value)
                            break
                    if field in parsed_data:
                        break
            
            # Calculate EBITDA robustly
            oi, ie, te, da = parsed_data.get('operating_income'), parsed_data.get('interest_expense'), parsed_data.get('tax_expense'), parsed_data.get('depreciation_amortization')
            if all(isinstance(v, (int, float)) for v in [oi, ie, te, da]):
                parsed_data['ebitda'] = oi + ie + te + da # A common approximation

            return {
                'ticker': ticker,
                'data_source': 'finnhub',
                'last_updated': datetime.now(),
                'income_statement': parsed_data,
            }
            
        except Exception as e:
            logging.error(f"Error parsing Finnhub financials for {ticker}: {e}", exc_info=True)
            return None

    def parse_company_profile(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse company profile data"""
        try:
            profile_data = {
                'ticker': ticker,
                'data_source': 'finnhub',
                'last_updated': datetime.now(),
                'company_info': {},
                'market_data': {}
            }
            
            # Company information
            profile_data['company_info'] = {
                'company_name': data.get('name'),
                'sector': data.get('finnhubIndustry'),
                'industry': data.get('finnhubIndustry'),
                'country': data.get('country'),
                'currency': data.get('currency')
            }
            
            # Market data
            profile_data['market_data'] = {
                'market_cap': self.safe_get_numeric(data, 'marketCapitalization'),
                'shares_outstanding': self.safe_get_numeric(data, 'shareOutstanding'),
                'current_price': self.safe_get_numeric(data, 'ticker')
            }
            
            return profile_data
            
        except Exception as e:
            logging.error(f"Error parsing company profile for {ticker}: {e}")
            return None

    def calculate_data_quality(self, data: Dict) -> int:
        """Calculate data quality score (0-100) based on completeness"""
        try:
            required_fields = [
                'revenue', 'netIncome', 'totalAssets', 'totalEquity',
                'totalDebt', 'cash', 'operatingIncome'
            ]
            
            available_fields = 0
            for field in required_fields:
                if field in data and data[field] is not None:
                    available_fields += 1
            
            quality_score = int((available_fields / len(required_fields)) * 100)
            return quality_score
            
        except Exception as e:
            logging.error(f"Error calculating data quality: {e}")
            return 0

    def safe_get_numeric(self, data: Dict, key: str) -> Optional[float]:
        """Safely get numeric value from dictionary"""
        try:
            value = data.get(key)
            if value is not None and value != 'N/A':
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
                    income.get('ebitda'), 'finnhub', datetime.now()
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
            logging.info(f"Successfully stored Finnhub fundamental data for {ticker}")
            return True
        except Exception as e:
            logging.error(f"Error storing Finnhub fundamental data for {ticker}: {e}")
            self.conn.rollback()
            return False

    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Main method to fetch and store Finnhub fundamental data for a ticker"""
        try:
            # Fetch financial statements
            financial_data = self.fetch_financial_statements(ticker)
            
            # Fetch company profile
            profile_data = self.fetch_company_profile(ticker)
            
            # Store data if available
            if financial_data or profile_data:
                success = self.store_fundamental_data(ticker, {
                    'financial_data': financial_data,
                    'profile_data': profile_data
                })
                if success:
                    return {
                        'financial_data': financial_data,
                        'profile_data': profile_data
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting Finnhub fundamental data for {ticker}: {e}")
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
    service = FinnhubService()
    test_ticker = "AAPL"
    result = service.get_fundamental_data(test_ticker)
    if result:
        print(f"Successfully fetched Finnhub fundamental data for {test_ticker}")
        if result.get('financial_data'):
            print(f"Financial data quality score: {result['financial_data'].get('quality_score', 0)}")
        if result.get('profile_data'):
            print(f"Company info: {result['profile_data'].get('company_info', {})}")
    else:
        print(f"Failed to fetch Finnhub fundamental data for {test_ticker}")
    service.close() 