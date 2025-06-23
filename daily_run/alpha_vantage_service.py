#!/usr/bin/env python3
"""
Alpha Vantage Financial Data Service
"""

from common_imports import (
    os, time, logging, requests, pd, datetime, timedelta, 
    psycopg2, DB_CONFIG, setup_logging, get_api_rate_limiter, safe_get_numeric
)
from dotenv import load_dotenv
from typing import Dict, Optional, List, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

# Setup logging for this service
setup_logging('alpha_vantage')

class AlphaVantageService:
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self.api_limiter = get_api_rate_limiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.max_retries = 3
        self.base_delay = 1  # seconds

    def fetch_income_statement(self, ticker: str) -> Optional[Dict]:
        """Fetch income statement from Alpha Vantage"""
        try:
            # Check API limit
            provider = 'alphavantage'
            endpoint = 'income_statement'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
                return None

            url = self.base_url
            params = {
                'function': 'INCOME_STATEMENT',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if 'annualReports' in data and data['annualReports']:
                    return self.parse_income_statement(ticker, data['annualReports'][0])
                else:
                    logging.warning(f"No income statement data available for {ticker} from Alpha Vantage")
                    return None
            else:
                logging.error(f"Alpha Vantage API error for {ticker}: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching income statement for {ticker}: {e}")
            return None

    def fetch_balance_sheet(self, ticker: str) -> Optional[Dict]:
        """Fetch balance sheet from Alpha Vantage"""
        try:
            provider = 'alphavantage'
            endpoint = 'balance_sheet'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
                return None

            url = self.base_url
            params = {
                'function': 'BALANCE_SHEET',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if 'annualReports' in data and data['annualReports']:
                    return self.parse_balance_sheet(ticker, data['annualReports'][0])
                else:
                    logging.warning(f"No balance sheet data available for {ticker} from Alpha Vantage")
                    return None
            else:
                logging.error(f"Alpha Vantage API error for {ticker}: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching balance sheet for {ticker}: {e}")
            return None

    def fetch_cash_flow(self, ticker: str) -> Optional[Dict]:
        """Fetch cash flow statement from Alpha Vantage"""
        try:
            provider = 'alphavantage'
            endpoint = 'cash_flow'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
                return None

            url = self.base_url
            params = {
                'function': 'CASH_FLOW',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if 'annualReports' in data and data['annualReports']:
                    return self.parse_cash_flow(ticker, data['annualReports'][0])
                else:
                    logging.warning(f"No cash flow data available for {ticker} from Alpha Vantage")
                    return None
            else:
                logging.error(f"Alpha Vantage API error for {ticker}: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching cash flow for {ticker}: {e}")
            return None

    def fetch_overview(self, ticker: str) -> Optional[Dict]:
        """Fetch company overview from Alpha Vantage"""
        try:
            provider = 'alphavantage'
            endpoint = 'overview'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
                return None

            url = self.base_url
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'Symbol' in data:
                    return self.parse_overview(ticker, data)
                else:
                    logging.warning(f"No overview data available for {ticker} from Alpha Vantage")
                    return None
            else:
                logging.error(f"Alpha Vantage API error for {ticker}: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching overview for {ticker}: {e}")
            return None

    def parse_income_statement(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse income statement data from Alpha Vantage"""
        try:
            income_statement = {
                'ticker': ticker,
                'data_source': 'alphavantage',
                'last_updated': datetime.now(),
                'revenue': self.safe_get_numeric(data, 'totalRevenue'),
                'gross_profit': self.safe_get_numeric(data, 'grossProfit'),
                'operating_income': self.safe_get_numeric(data, 'operatingIncome'),
                'net_income': self.safe_get_numeric(data, 'netIncome'),
                'ebitda': self.safe_get_numeric(data, 'ebitda'),
                'fiscal_year': int(data.get('fiscalDateEnding', '').split('-')[0]) if data.get('fiscalDateEnding') else None,
                'fiscal_quarter': None,
                'ttm_periods': 1  # Alpha Vantage provides annual data
            }
            
            return income_statement
            
        except Exception as e:
            logging.error(f"Error parsing income statement for {ticker}: {e}")
            return None

    def parse_balance_sheet(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse balance sheet data from Alpha Vantage"""
        try:
            balance_sheet = {
                'ticker': ticker,
                'data_source': 'alphavantage',
                'last_updated': datetime.now(),
                'total_assets': self.safe_get_numeric(data, 'totalAssets'),
                'total_debt': self.safe_get_numeric(data, 'totalDebt'),
                'total_equity': self.safe_get_numeric(data, 'totalShareholderEquity'),
                'cash_and_equivalents': self.safe_get_numeric(data, 'cashAndCashEquivalentsAtCarryingValue'),
                'current_assets': self.safe_get_numeric(data, 'totalCurrentAssets'),
                'current_liabilities': self.safe_get_numeric(data, 'totalCurrentLiabilities'),
                'fiscal_year': int(data.get('fiscalDateEnding', '').split('-')[0]) if data.get('fiscalDateEnding') else None
            }
            
            return balance_sheet
            
        except Exception as e:
            logging.error(f"Error parsing balance sheet for {ticker}: {e}")
            return None

    def parse_cash_flow(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse cash flow data from Alpha Vantage"""
        try:
            cash_flow = {
                'ticker': ticker,
                'data_source': 'alphavantage',
                'last_updated': datetime.now(),
                'operating_cash_flow': self.safe_get_numeric(data, 'operatingCashflow'),
                'free_cash_flow': self.safe_get_numeric(data, 'operatingCashflow') - self.safe_get_numeric(data, 'capitalExpenditures'),
                'capex': self.safe_get_numeric(data, 'capitalExpenditures'),
                'fiscal_year': int(data.get('fiscalDateEnding', '').split('-')[0]) if data.get('fiscalDateEnding') else None
            }
            
            return cash_flow
            
        except Exception as e:
            logging.error(f"Error parsing cash flow for {ticker}: {e}")
            return None

    def parse_overview(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse company overview data from Alpha Vantage"""
        try:
            overview = {
                'ticker': ticker,
                'data_source': 'alphavantage',
                'last_updated': datetime.now(),
                'market_data': {
                    'market_cap': self.safe_get_numeric(data, 'MarketCapitalization'),
                    'shares_outstanding': self.safe_get_numeric(data, 'SharesOutstanding'),
                    'current_price': self.safe_get_numeric(data, 'LatestPrice')
                },
                'ratios': {
                    'pe_ratio': self.safe_get_numeric(data, 'PERatio'),
                    'pb_ratio': self.safe_get_numeric(data, 'PriceToBookRatio'),
                    'ps_ratio': self.safe_get_numeric(data, 'PriceToSalesRatio'),
                    'debt_to_equity': self.safe_get_numeric(data, 'DebtToEquityRatio')
                },
                'per_share_metrics': {
                    'eps_diluted': self.safe_get_numeric(data, 'EPS'),
                    'book_value_per_share': self.safe_get_numeric(data, 'BookValue')
                }
            }
            
            return overview
            
        except Exception as e:
            logging.error(f"Error parsing overview for {ticker}: {e}")
            return None

    def safe_get_numeric(self, data: Dict, key: str) -> Optional[float]:
        """Safely get numeric value from dictionary"""
        try:
            value = data.get(key)
            if value is not None and value != 'N/A' and value != '' and value != 'None':
                return float(value)
            return None
        except (ValueError, TypeError):
            return None

    def store_fundamental_data(self, ticker: str, income_stmt: Dict, balance_sheet: Dict, 
                              cash_flow: Dict, overview: Dict) -> bool:
        """Store fundamental data in the database"""
        try:
            # Extract data
            market_data = overview.get('market_data', {}) if overview else {}
            per_share = overview.get('per_share_metrics', {}) if overview else {}

            # Update stocks table
            update_data = {
                'market_cap': market_data.get('market_cap'),
                'shares_outstanding': market_data.get('shares_outstanding'),
                'revenue_ttm': income_stmt.get('revenue') if income_stmt else None,
                'net_income_ttm': income_stmt.get('net_income') if income_stmt else None,
                'ebitda_ttm': income_stmt.get('ebitda') if income_stmt else None,
                'diluted_eps_ttm': per_share.get('eps_diluted'),
                'book_value_per_share': per_share.get('book_value_per_share'),
                'total_debt': balance_sheet.get('total_debt') if balance_sheet else None,
                'shareholders_equity': balance_sheet.get('total_equity') if balance_sheet else None,
                'cash_and_equivalents': balance_sheet.get('cash_and_equivalents') if balance_sheet else None,
                'fundamentals_last_update': datetime.now()
            }

            # Filter out None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if update_data:
                set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
                values = list(update_data.values()) + [ticker]

                self.cur.execute(f"""
                    UPDATE stocks 
                    SET {set_clause}
                    WHERE ticker = %s
                """, tuple(values))

            # Store in company_fundamentals table
            if income_stmt:
                self.cur.execute("""
                    INSERT INTO company_fundamentals 
                    (ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                     revenue, gross_profit, operating_income, net_income, ebitda,
                     data_source, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, report_date, period_type)
                    DO UPDATE SET
                        revenue = COALESCE(EXCLUDED.revenue, company_fundamentals.revenue),
                        gross_profit = COALESCE(EXCLUDED.gross_profit, company_fundamentals.gross_profit),
                        operating_income = COALESCE(EXCLUDED.operating_income, company_fundamentals.operating_income),
                        net_income = COALESCE(EXCLUDED.net_income, company_fundamentals.net_income),
                        ebitda = COALESCE(EXCLUDED.ebitda, company_fundamentals.ebitda),
                        fiscal_year = EXCLUDED.fiscal_year,
                        fiscal_quarter = EXCLUDED.fiscal_quarter,
                        data_source = EXCLUDED.data_source,
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    ticker, datetime.now().date(), 'annual', income_stmt.get('fiscal_year'), income_stmt.get('fiscal_quarter'),
                    income_stmt.get('revenue'), income_stmt.get('gross_profit'),
                    income_stmt.get('operating_income'), income_stmt.get('net_income'),
                    income_stmt.get('ebitda'), 'alphavantage', datetime.now()
                ))
            
            self.conn.commit()
            logging.info(f"Successfully stored fundamental data for {ticker}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing fundamental data for {ticker}: {e}")
            self.conn.rollback()
            return False

    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Main method to fetch and store fundamental data"""
        try:
            # Fetch all financial data
            income_stmt = self.fetch_income_statement(ticker)
            balance_sheet = self.fetch_balance_sheet(ticker)
            cash_flow = self.fetch_cash_flow(ticker)
            overview = self.fetch_overview(ticker)
            
            # Store data if available
            if any([income_stmt, balance_sheet, cash_flow, overview]):
                success = self.store_fundamental_data(ticker, income_stmt, balance_sheet, cash_flow, overview)
                if success:
                    return {
                        'income_statement': income_stmt,
                        'balance_sheet': balance_sheet,
                        'cash_flow': cash_flow,
                        'overview': overview
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting fundamental data for {ticker}: {e}")
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
    
    service = AlphaVantageService()
    test_ticker = args.ticker
    result = service.get_fundamental_data(test_ticker)
    if result:
        print(f"Successfully fetched fundamental data for {test_ticker}")
        if result.get('income_statement'):
            print(f"Income statement keys: {list(result['income_statement'].keys())}")
        if result.get('balance_sheet'):
            print(f"Balance sheet keys: {list(result['balance_sheet'].keys())}")
        if result.get('cash_flow'):
            print(f"Cash flow keys: {list(result['cash_flow'].keys())}")
        if result.get('overview'):
            print(f"Overview keys: {list(result['overview'].keys())}")
    else:
        print(f"Failed to fetch fundamental data for {test_ticker}")
    service.close() 