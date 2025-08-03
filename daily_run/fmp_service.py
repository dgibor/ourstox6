#!/usr/bin/env python3
"""
Financial Modeling Prep (FMP) Service for fundamental data
"""

from common_imports import (
    os, time, logging, requests, pd, datetime, timedelta, 
    psycopg2, DB_CONFIG, setup_logging, get_api_rate_limiter, safe_get_numeric
)
from typing import Dict, Optional, List, Any
from simple_ratio_calculator import calculate_ratios, validate_ratios
from database import DatabaseManager

# Setup logging for this service
setup_logging('fmp')

# API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

class FMPService:
    """Financial Modeling Prep API service for fundamental data"""
    
    def __init__(self):
        """Initialize database connection and API rate limiter"""
        self.api_limiter = get_api_rate_limiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.db = DatabaseManager()  # Add DatabaseManager for price lookups
        self.max_retries = 3
        self.base_delay = 2  # seconds
        
        if not FMP_API_KEY:
            logging.error("FMP_API_KEY not found in environment variables")
            raise ValueError("FMP_API_KEY is required")

    def fetch_financial_statements(self, ticker: str) -> Optional[Dict]:
        """Fetch financial statements from FMP API with rate limiting (limiter bypassed for testing)"""
        for attempt in range(self.max_retries):
            try:
                provider = 'fmp'
                endpoint = 'financials'
                print(f"[DEBUG] fetch_financial_statements: ticker={ticker}, API_KEY={FMP_API_KEY[:8]}..., limiter=BYPASSED")
                # BYPASS limiter for testing
                # if self.api_limiter and not self.api_limiter.check_limit(provider, endpoint):
                #     print(f"[DEBUG] API limiter blocked call for {ticker}")
                #     logging.warning(f"FMP API limit reached for {ticker}")
                #     return None

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
        """Fetch key statistics from FMP API (limiter bypassed for testing)"""
        for attempt in range(self.max_retries):
            try:
                provider = 'fmp'
                endpoint = 'key_statistics'
                print(f"[DEBUG] fetch_key_statistics: ticker={ticker}, API_KEY={FMP_API_KEY[:8]}..., limiter=BYPASSED")
                # BYPASS limiter for testing
                # if self.api_limiter and not self.api_limiter.check_limit(provider, endpoint):
                #     print(f"[DEBUG] API limiter blocked call for {ticker}")
                #     logging.warning(f"FMP API limit reached for {ticker}")
                #     return None

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

    def fetch_batch_quotes(self, tickers: List[str]) -> Optional[List[Dict]]:
        """Fetch batch quotes for a list of tickers from FMP API."""
        symbols = ','.join(tickers)
        url = f"{FMP_BASE_URL}/quote/{symbols}"
        params = {'apikey': FMP_API_KEY}
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    else:
                        logging.warning(f"FMP batch quote response not a list: {data}")
                        return None
                else:
                    logging.warning(f"FMP batch quote failed (status {response.status_code}): {response.text}")
            except Exception as e:
                if 'rate limit' in str(e).lower() or '429' in str(e):
                    if attempt < self.max_retries - 1:
                        wait_time = self.base_delay * (2 ** attempt)
                        logging.warning(f"FMP rate limited for batch, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                logging.error(f"Error fetching FMP batch quotes: {e}")
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
                # Use latest annual data (FMP returns annual, not quarterly)
                latest_annual = income_data[0]
                
                # Use single annual values, not TTM sum
                annual_revenue = float(latest_annual.get('revenue', 0))
                annual_net_income = float(latest_annual.get('netIncome', 0))
                annual_gross_profit = float(latest_annual.get('grossProfit', 0))
                annual_operating_income = float(latest_annual.get('operatingIncome', 0))
                annual_ebitda = float(latest_annual.get('ebitda', 0))
                
                # Calculate cost of goods sold from revenue and gross profit
                cost_of_goods_sold = annual_revenue - annual_gross_profit if annual_gross_profit > 0 else 0
                
                # Fix fiscal year parsing - handle 'FY' and other non-numeric values
                fiscal_year = datetime.now().year
                try:
                    calendar_year = latest_annual.get('calendarYear')
                    if calendar_year and str(calendar_year).isdigit():
                        fiscal_year = int(calendar_year)
                except (ValueError, TypeError):
                    pass
                
                fiscal_quarter = 1
                try:
                    period = latest_annual.get('period')
                    if period and str(period).isdigit():
                        fiscal_quarter = int(period)
                except (ValueError, TypeError):
                    pass
                
                financial_data['income_statement'] = {
                    'revenue': annual_revenue,
                    'revenue_annual': annual_revenue,
                    'gross_profit': annual_gross_profit,
                    'cost_of_goods_sold': cost_of_goods_sold,  # Calculate COGS
                    'operating_income': annual_operating_income,
                    'net_income': annual_net_income,
                    'ebitda': annual_ebitda,
                    'fiscal_year': fiscal_year,
                    'fiscal_quarter': fiscal_quarter,
                    'ttm_periods': 1  # Single annual period
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
            market_cap = float(profile_data.get('mktCap', 0))
            enterprise_value = float(profile_data.get('enterpriseValue', 0))
            shares_outstanding = float(profile_data.get('sharesOutstanding', 0))
            current_price = float(profile_data.get('price', 0))
            
            # If enterprise value is missing or 0, calculate it manually
            if enterprise_value == 0 or enterprise_value is None:
                # Get total debt from balance sheet data if available
                total_debt = 0
                if hasattr(self, 'balance_data') and self.balance_data:
                    latest_balance = self.balance_data[0]
                    total_debt = float(latest_balance.get('totalDebt', 0))
                
                # Calculate enterprise value as market cap + total debt
                enterprise_value = market_cap + total_debt
                logging.info(f"{ticker} Calculated enterprise value: ${enterprise_value:,.0f} (Market Cap: ${market_cap:,.0f} + Total Debt: ${total_debt:,.0f})")
            
            key_stats['market_data'] = {
                'market_cap': market_cap,
                'enterprise_value': enterprise_value,
                'shares_outstanding': shares_outstanding,
                'current_price': current_price
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
            fmp_ratios = key_stats.get('ratios', {}) if key_stats else {}

            # Prepare a dictionary of all columns to update in the 'stocks' table
            market_cap = market_data.get('market_cap')
            enterprise_value = market_data.get('enterprise_value')
            total_debt = balance.get('total_debt')
            
            # If enterprise value is missing or 0, calculate it manually
            if (enterprise_value == 0 or enterprise_value is None) and market_cap and total_debt:
                enterprise_value = market_cap + total_debt
                logging.info(f"{ticker} Calculated enterprise value: ${enterprise_value:,.0f} (Market Cap: ${market_cap:,.0f} + Total Debt: ${total_debt:,.0f})")
            
            update_data = {
                'market_cap': market_cap,
                'enterprise_value': enterprise_value,
                'shares_outstanding': market_data.get('shares_outstanding'),
                'revenue_ttm': income.get('revenue'),
                'net_income_ttm': income.get('net_income'),
                'ebitda_ttm': income.get('ebitda'),
                'diluted_eps_ttm': per_share.get('eps_diluted'),
                'book_value_per_share': per_share.get('book_value_per_share'),
                'total_debt': total_debt,
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
            
            # Also update company_fundamentals table with UPSERT
            if income or balance or cash_flow:
                # Get shares outstanding from key_stats
                shares_outstanding = market_data.get('shares_outstanding', 0)
                
                # Use ON CONFLICT for upsert
                insert_query = """
                INSERT INTO company_fundamentals (
                    ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                    revenue, net_income, ebitda, total_assets, total_debt, 
                    total_equity, cash_and_equivalents, operating_income, free_cash_flow,
                    cost_of_goods_sold, current_assets, current_liabilities, shares_outstanding,
                    data_source, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker) DO UPDATE SET
                    report_date = EXCLUDED.report_date,
                    period_type = EXCLUDED.period_type,
                    fiscal_year = EXCLUDED.fiscal_year,
                    fiscal_quarter = EXCLUDED.fiscal_quarter,
                    revenue = EXCLUDED.revenue,
                    net_income = EXCLUDED.net_income,
                    ebitda = EXCLUDED.ebitda,
                    total_assets = EXCLUDED.total_assets,
                    total_debt = EXCLUDED.total_debt,
                    total_equity = EXCLUDED.total_equity,
                    cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                    operating_income = EXCLUDED.operating_income,
                    free_cash_flow = EXCLUDED.free_cash_flow,
                    cost_of_goods_sold = EXCLUDED.cost_of_goods_sold,
                    current_assets = EXCLUDED.current_assets,
                    current_liabilities = EXCLUDED.current_liabilities,
                    shares_outstanding = EXCLUDED.shares_outstanding,
                    data_source = EXCLUDED.data_source,
                    last_updated = EXCLUDED.last_updated
                """
                
                report_date = datetime.now().date()
                
                self.cur.execute(insert_query, (
                    ticker,
                    report_date,
                    'ttm',
                    income.get('fiscal_year', datetime.now().year),
                    income.get('fiscal_quarter', 1),
                    income.get('revenue'),
                    income.get('net_income'),
                    income.get('ebitda'),
                    balance.get('total_assets'),
                    balance.get('total_debt'),
                    balance.get('total_equity'),
                    balance.get('cash_and_equivalents'),
                    income.get('operating_income'),
                    cash_flow.get('free_cash_flow'),
                    income.get('cost_of_goods_sold'),  # Add COGS
                    balance.get('current_assets'),     # Add current assets
                    balance.get('current_liabilities'), # Add current liabilities
                    shares_outstanding,                # Add shares outstanding
                    'fmp',
                    datetime.now()
                ))

            # Note: Ratio calculation is handled by the separate calculate_fundamental_ratios.py script
            # This service focuses on populating raw fundamental data
            
            self.conn.commit()
            logging.info(f"Successfully stored FMP fundamental data for {ticker}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing FMP fundamental data for {ticker}: {e}")
            self.conn.rollback()
            return False

    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Main method to fetch and store fundamental data for a ticker"""
        print(f"[DEBUG] get_fundamental_data called for {ticker}")
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