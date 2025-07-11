#!/usr/bin/env python3
"""
Finnhub Financial Data Service
"""

from common_imports import (
    os, time, logging, requests, pd, datetime, timedelta, 
    psycopg2, DB_CONFIG, setup_logging, get_api_rate_limiter, safe_get_numeric
)
from typing import Dict, Optional, List, Any
from base_service import BaseService

# Setup logging for this service
setup_logging('finnhub')

class FinnhubService(BaseService):
    def __init__(self):
        super().__init__('finnhub', os.getenv('FINNHUB_API_KEY'))
        self.base_url = 'https://finnhub.io/api/v1'
        self.api_limiter = get_api_rate_limiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.max_retries = 3
        self.base_delay = 1  # seconds

    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current price data for a ticker"""
        try:
            url = f"{self.base_url}/quote"
            params = {
                'symbol': ticker,
                'token': self.api_key
            }
            
            response = self._make_request(url, params)
            
            if response:
                return {
                    'price': response.get('c'),  # Current price
                    'volume': response.get('v'),  # Volume
                    'change': response.get('d'),  # Change
                    'change_percent': response.get('dp'),  # Change percent
                    'data_source': 'finnhub',
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting data for {ticker}: {e}")
            return None

    def get_current_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current price data for a ticker (alias for get_data)"""
        return self.get_data(ticker)

    def fetch_financial_statements(self, ticker: str) -> Optional[Dict]:
        """Fetch financial statements from Finnhub"""
        try:
            # Check API limit
            provider = 'finnhub'
            endpoint = 'financials'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Finnhub API limit reached for {ticker}")
                return None

            # Fetch income statement
            url = f"{self.base_url}/stock/financials-reported"
            params = {
                'symbol': ticker,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    return self.parse_financial_data(ticker, data['data'])
                else:
                    logging.warning(f"No financial data available for {ticker} from Finnhub")
                    return None
            else:
                logging.error(f"Finnhub API error for {ticker}: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching financial statements for {ticker}: {e}")
            return None

    def fetch_company_profile(self, ticker: str) -> Optional[Dict]:
        """Fetch company profile from Finnhub"""
        try:
            provider = 'finnhub'
            endpoint = 'profile'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Finnhub API limit reached for {ticker}")
                return None

            url = f"{self.base_url}/stock/profile2"
            params = {
                'symbol': ticker,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.api_limiter.record_call(provider, endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return self.parse_profile_data(ticker, data)
                else:
                    logging.warning(f"No profile data available for {ticker} from Finnhub")
                    return None
            else:
                logging.error(f"Finnhub API error for {ticker}: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching company profile for {ticker}: {e}")
            return None

    def parse_financial_data(self, ticker: str, data: List[Dict]) -> Optional[Dict]:
        """Parse financial statement data from Finnhub"""
        try:
            if not data:
                return None
            
            # Get the most recent financial data
            latest_data = data[0] if data else {}
            
            financial_data = {
                'ticker': ticker,
                'data_source': 'finnhub',
                'last_updated': datetime.now(),
                'income_statement': {},
                'balance_sheet': {},
                'cash_flow': {}
            }
            
            # Extract income statement data
            income_data = latest_data.get('report', {})
            financial_data['income_statement'] = {
                'revenue': self.safe_get_numeric(income_data, 'revenue'),
                'gross_profit': self.safe_get_numeric(income_data, 'grossProfit'),
                'operating_income': self.safe_get_numeric(income_data, 'operatingIncome'),
                'net_income': self.safe_get_numeric(income_data, 'netIncome'),
                'ebitda': self.safe_get_numeric(income_data, 'ebitda'),
                'fiscal_year': latest_data.get('year'),
                'fiscal_quarter': latest_data.get('quarter'),
                'ttm_periods': 1  # Finnhub provides annual data
            }
            
            # Extract balance sheet data
            balance_data = latest_data.get('report', {})
            financial_data['balance_sheet'] = {
                'total_assets': self.safe_get_numeric(balance_data, 'totalAssets'),
                'total_debt': self.safe_get_numeric(balance_data, 'totalDebt'),
                'total_equity': self.safe_get_numeric(balance_data, 'totalEquity'),
                'cash_and_equivalents': self.safe_get_numeric(balance_data, 'cashAndCashEquivalents'),
                'current_assets': self.safe_get_numeric(balance_data, 'totalCurrentAssets'),
                'current_liabilities': self.safe_get_numeric(balance_data, 'totalCurrentLiabilities'),
                'fiscal_year': latest_data.get('year')
            }
            
            return financial_data
            
        except Exception as e:
            logging.error(f"Error parsing financial data for {ticker}: {e}")
            return None

    def parse_profile_data(self, ticker: str, data: Dict) -> Optional[Dict]:
        """Parse company profile data from Finnhub"""
        try:
            profile_data = {
                'ticker': ticker,
                'data_source': 'finnhub',
                'last_updated': datetime.now(),
                'market_data': {},
                'ratios': {},
                'per_share_metrics': {}
            }
            
            # Market data
            profile_data['market_data'] = {
                'market_cap': self.safe_get_numeric(data, 'marketCapitalization'),
                'shares_outstanding': self.safe_get_numeric(data, 'shareOutstanding'),
                'current_price': self.safe_get_numeric(data, 'ticker')
            }
            
            # Key ratios (if available)
            profile_data['ratios'] = {
                'pe_ratio': self.safe_get_numeric(data, 'peRatio'),
                'pb_ratio': self.safe_get_numeric(data, 'pbRatio'),
                'ps_ratio': self.safe_get_numeric(data, 'psRatio'),
                'debt_to_equity': self.safe_get_numeric(data, 'debtToEquity')
            }
            
            # Per share metrics
            profile_data['per_share_metrics'] = {
                'eps_diluted': self.safe_get_numeric(data, 'eps'),
                'book_value_per_share': self.safe_get_numeric(data, 'bookValue')
            }
            
            return profile_data
            
        except Exception as e:
            logging.error(f"Error parsing profile data for {ticker}: {e}")
            return None

    def safe_get_numeric(self, data: Dict, key: str) -> Optional[float]:
        """Safely get numeric value from dictionary"""
        try:
            value = data.get(key)
            if value is not None and value != 'N/A' and value != '':
                return float(value)
            return None
        except (ValueError, TypeError):
            return None

    def store_fundamental_data(self, ticker: str, financial_data: Dict, profile_data: Dict) -> bool:
        """Store fundamental data in the database"""
        try:
            # Extract data
            income = financial_data.get('income_statement', {}) if financial_data else {}
            balance = financial_data.get('balance_sheet', {}) if financial_data else {}
            market_data = profile_data.get('market_data', {}) if profile_data else {}
            per_share = profile_data.get('per_share_metrics', {}) if profile_data else {}

            # Update stocks table
            update_data = {
                'market_cap': market_data.get('market_cap'),
                'shares_outstanding': market_data.get('shares_outstanding'),
                'revenue_ttm': income.get('revenue'),
                'net_income_ttm': income.get('net_income'),
                'ebitda_ttm': income.get('ebitda'),
                'diluted_eps_ttm': per_share.get('eps_diluted'),
                'book_value_per_share': per_share.get('book_value_per_share'),
                'total_debt': balance.get('total_debt'),
                'shareholders_equity': balance.get('total_equity'),
                'cash_and_equivalents': balance.get('cash_and_equivalents'),
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
            if financial_data and financial_data.get('income_statement'):
                income = financial_data['income_statement']
                
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
                    ticker, datetime.now().date(), 'annual', income.get('fiscal_year'), income.get('fiscal_quarter'),
                    income.get('revenue'), income.get('gross_profit'),
                    income.get('operating_income'), income.get('net_income'),
                    income.get('ebitda'), 'finnhub', datetime.now()
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
            # Fetch financial statements
            financial_data = self.fetch_financial_statements(ticker)
            
            # Fetch company profile
            profile_data = self.fetch_company_profile(ticker)
            
            # Store data if available
            if financial_data or profile_data:
                success = self.store_fundamental_data(ticker, financial_data, profile_data)
                if success:
                    return {
                        'financial_data': financial_data,
                        'profile_data': profile_data
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
        super().close()
        if self.api_limiter:
            self.api_limiter.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', type=str, default='AAPL', help='Ticker symbol to fetch')
    args = parser.parse_args()
    
    service = FinnhubService()
    test_ticker = args.ticker
    result = service.get_fundamental_data(test_ticker)
    if result:
        print(f"Successfully fetched fundamental data for {test_ticker}")
        if result.get('financial_data'):
            print(f"Financial data keys: {list(result['financial_data'].keys())}")
        if result.get('profile_data'):
            print(f"Profile data keys: {list(result['profile_data'].keys())}")
    else:
        print(f"Failed to fetch fundamental data for {test_ticker}")
    service.close() 