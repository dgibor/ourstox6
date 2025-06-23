import os
import time
import logging
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
from typing import Dict, Optional, List, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utility_functions.api_rate_limiter import APIRateLimiter
import argparse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/yahoo_finance.log'),
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

YAHOO_ENDPOINTS = {
    'financials': '/v1/finance/financials',
    'key_statistics': '/v11/finance/quoteSummary',
    'balance_sheet': '/v1/finance/balance_sheet',
    'cash_flow': '/v1/finance/cash_flow'
}

class YahooFinanceService:
    def __init__(self):
        self.api_limiter = APIRateLimiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.max_retries = 3
        self.base_delay = 2  # seconds

    def fetch_financial_statements(self, ticker: str) -> Optional[Dict]:
        """Fetch financial statements from Yahoo Finance with exponential backoff on rate limit"""
        import time
        max_retries = 3
        wait_times = [2, 4, 8]
        for attempt in range(max_retries):
            try:
                # Check API limit before making request
                provider = 'yahoo'
                endpoint = 'financials'
                if not self.api_limiter.check_limit(provider, endpoint):
                    logging.warning(f"Yahoo Finance API limit reached for {ticker}")
                    return None

                # Fetch data using yfinance
                stock = yf.Ticker(ticker)
                
                # Get financial statements
                income_stmt = stock.financials
                balance_sheet = stock.balance_sheet
                cash_flow = stock.cashflow
                
                # Record API call
                self.api_limiter.record_call(provider, endpoint)
                
                # Parse and standardize data
                financial_data = self.parse_financial_data(ticker, income_stmt, balance_sheet, cash_flow)
                
                if financial_data:
                    logging.info(f"Successfully fetched financial data for {ticker}")
                    return financial_data
                else:
                    logging.warning(f"No financial data available for {ticker}")
                    return None
                    
            except Exception as e:
                if 'rate limit' in str(e).lower() or 'too many requests' in str(e).lower():
                    if attempt < max_retries - 1:
                        logging.warning(f"Rate limited for {ticker}, retrying in {wait_times[attempt]}s...")
                        time.sleep(wait_times[attempt])
                        continue
                logging.error(f"Error fetching financial statements for {ticker}: {e}")
                break
        
        return None

    def fetch_key_statistics(self, ticker: str) -> Optional[Dict]:
        """Fetch key statistics from Yahoo Finance with exponential backoff on rate limit"""
        import time
        max_retries = 3
        wait_times = [2, 4, 8]
        for attempt in range(max_retries):
            try:
                provider = 'yahoo'
                endpoint = 'key_statistics'
                if not self.api_limiter.check_limit(provider, endpoint):
                    logging.warning(f"Yahoo Finance API limit reached for {ticker}")
                    return None

                stock = yf.Ticker(ticker)
                
                # Get key statistics
                info = stock.info
                
                # Record API call
                self.api_limiter.record_call(provider, endpoint)
                
                # Parse key statistics
                key_stats = self.parse_key_statistics(ticker, info)
                
                if key_stats:
                    logging.info(f"Successfully fetched key statistics for {ticker}")
                    return key_stats
                else:
                    logging.warning(f"No key statistics available for {ticker}")
                    return None
                    
            except Exception as e:
                if 'rate limit' in str(e).lower() or 'too many requests' in str(e).lower():
                    if attempt < max_retries - 1:
                        logging.warning(f"Rate limited for {ticker}, retrying in {wait_times[attempt]}s...")
                        time.sleep(wait_times[attempt])
                        continue
                logging.error(f"Error fetching key statistics for {ticker}: {e}")
                break
        
        return None

    def parse_financial_data(self, ticker: str, income_stmt: pd.DataFrame, 
                           balance_sheet: pd.DataFrame, cash_flow: pd.DataFrame) -> Optional[Dict]:
        """Parse and standardize financial statement data"""
        try:
            financial_data = {
                'ticker': ticker,
                'data_source': 'yahoo',
                'last_updated': datetime.now(),
                'income_statement': {},
                'balance_sheet': {},
                'cash_flow': {}
            }
            
            # Parse income statement and calculate TTM
            if not income_stmt.empty:
                # Get the last 4 quarters for TTM calculation
                columns = list(income_stmt.columns)
                if len(columns) >= 4:
                    ttm_columns = columns[:4]  # Last 4 quarters
                else:
                    ttm_columns = columns  # Use all available quarters
                
                # Calculate TTM values
                ttm_revenue = sum(self.safe_get_value(income_stmt, 'Total Revenue', col) or 0 for col in ttm_columns)
                ttm_gross_profit = sum(self.safe_get_value(income_stmt, 'Gross Profit', col) or 0 for col in ttm_columns)
                ttm_operating_income = sum(self.safe_get_value(income_stmt, 'Operating Income', col) or 0 for col in ttm_columns)
                ttm_net_income = sum(self.safe_get_value(income_stmt, 'Net Income', col) or 0 for col in ttm_columns)
                ttm_ebitda = sum(self.safe_get_value(income_stmt, 'EBITDA', col) or 0 for col in ttm_columns)
                
                # Also get annual data for comparison
                latest_year = income_stmt.columns[0]
                financial_data['income_statement'] = {
                    'revenue': ttm_revenue,  # Use TTM instead of annual
                    'revenue_annual': self.safe_get_value(income_stmt, 'Total Revenue', latest_year),
                    'gross_profit': ttm_gross_profit,
                    'operating_income': ttm_operating_income,
                    'net_income': ttm_net_income,
                    'ebitda': ttm_ebitda,
                    'fiscal_year': latest_year.year,
                    'ttm_periods': len(ttm_columns)
                }
            else:
                # Fallback to annual data if no quarterly data
                latest_year = income_stmt.columns[0] if not income_stmt.empty else None
                if latest_year:
                    financial_data['income_statement'] = {
                        'revenue': self.safe_get_value(income_stmt, 'Total Revenue', latest_year),
                        'gross_profit': self.safe_get_value(income_stmt, 'Gross Profit', latest_year),
                        'operating_income': self.safe_get_value(income_stmt, 'Operating Income', latest_year),
                        'net_income': self.safe_get_value(income_stmt, 'Net Income', latest_year),
                        'ebitda': self.safe_get_value(income_stmt, 'EBITDA', latest_year),
                        'fiscal_year': latest_year.year,
                        'ttm_periods': 1
                    }
            
            # Parse balance sheet
            if not balance_sheet.empty:
                latest_year = balance_sheet.columns[0]
                financial_data['balance_sheet'] = {
                    'total_assets': self.safe_get_value(balance_sheet, 'Total Assets', latest_year),
                    'total_debt': self.safe_get_value(balance_sheet, 'Total Debt', latest_year),
                    'total_equity': self.safe_get_value(balance_sheet, 'Total Stockholder Equity', latest_year),
                    'cash_and_equivalents': self.safe_get_value(balance_sheet, 'Cash And Cash Equivalents', latest_year),
                    'current_assets': self.safe_get_value(balance_sheet, 'Total Current Assets', latest_year),
                    'current_liabilities': self.safe_get_value(balance_sheet, 'Total Current Liabilities', latest_year),
                    'fiscal_year': latest_year.year
                }
            
            # Parse cash flow
            if not cash_flow.empty:
                latest_year = cash_flow.columns[0]
                financial_data['cash_flow'] = {
                    'operating_cash_flow': self.safe_get_value(cash_flow, 'Operating Cash Flow', latest_year),
                    'free_cash_flow': self.safe_get_value(cash_flow, 'Free Cash Flow', latest_year),
                    'capex': self.safe_get_value(cash_flow, 'Capital Expenditure', latest_year),
                    'fiscal_year': latest_year.year
                }
            
            return financial_data
            
        except Exception as e:
            logging.error(f"Error parsing financial data for {ticker}: {e}")
            return None

    def parse_key_statistics(self, ticker: str, info: Dict) -> Optional[Dict]:
        """Parse key statistics and ratios"""
        try:
            key_stats = {
                'ticker': ticker,
                'data_source': 'yahoo',
                'last_updated': datetime.now(),
                'market_data': {},
                'ratios': {},
                'per_share_metrics': {}
            }
            
            # Market data
            key_stats['market_data'] = {
                'market_cap': self.safe_get_numeric(info, 'marketCap'),
                'enterprise_value': self.safe_get_numeric(info, 'enterpriseValue'),
                'shares_outstanding': self.safe_get_numeric(info, 'sharesOutstanding'),
                'shares_float': self.safe_get_numeric(info, 'floatShares'),
                'current_price': self.safe_get_numeric(info, 'currentPrice')
            }
            
            # Key ratios
            key_stats['ratios'] = {
                'pe_ratio': self.safe_get_numeric(info, 'trailingPE'),
                'pb_ratio': self.safe_get_numeric(info, 'priceToBook'),
                'ps_ratio': self.safe_get_numeric(info, 'priceToSalesTrailing12Months'),
                'ev_ebitda': self.safe_get_numeric(info, 'enterpriseToEbitda'),
                'peg_ratio': self.safe_get_numeric(info, 'pegRatio'),
                'roe': self.safe_get_numeric(info, 'returnOnEquity'),
                'roa': self.safe_get_numeric(info, 'returnOnAssets'),
                'debt_to_equity': self.safe_get_numeric(info, 'debtToEquity'),
                'current_ratio': self.safe_get_numeric(info, 'currentRatio'),
                'quick_ratio': self.safe_get_numeric(info, 'quickRatio'),
                'gross_margin': self.safe_get_numeric(info, 'grossMargins'),
                'operating_margin': self.safe_get_numeric(info, 'operatingMargins'),
                'net_margin': self.safe_get_numeric(info, 'profitMargins')
            }
            
            # Per share metrics
            key_stats['per_share_metrics'] = {
                'eps_diluted': self.safe_get_numeric(info, 'trailingEps'),
                'book_value_per_share': self.safe_get_numeric(info, 'bookValue'),
                'cash_per_share': self.safe_get_numeric(info, 'totalCashPerShare'),
                'revenue_per_share': self.safe_get_numeric(info, 'revenuePerShare')
            }
            
            return key_stats
            
        except Exception as e:
            logging.error(f"Error parsing key statistics for {ticker}: {e}")
            return None

    def safe_get_value(self, df: pd.DataFrame, row_name: str, column) -> Optional[float]:
        """Safely get value from DataFrame with error handling"""
        try:
            if row_name in df.index:
                value = df.loc[row_name, column]
                if pd.notna(value):
                    return float(value)
            return None
        except Exception as e:
            logging.debug(f"Error getting {row_name}: {e}")
            return None

    def safe_get_numeric(self, data: Dict, key: str) -> Optional[float]:
        """Safely get numeric value from dictionary with error handling"""
        try:
            value = data.get(key)
            if value is not None and value != 'N/A':
                return float(value)
            return None
        except (ValueError, TypeError) as e:
            logging.debug(f"Error converting {key} to numeric: {e}")
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
                'fundamentals_last_update': datetime.now()
            }

            # Log TTM calculations for debugging
            if income.get('revenue'):
                logging.info(f"{ticker} TTM Revenue: ${income.get('revenue'):,.0f} (from {income.get('ttm_periods', 1)} periods)")
                if income.get('revenue_annual'):
                    logging.info(f"{ticker} Annual Revenue: ${income.get('revenue_annual'):,.0f}")
            if income.get('net_income'):
                logging.info(f"{ticker} TTM Net Income: ${income.get('net_income'):,.0f}")
            if income.get('ebitda'):
                logging.info(f"{ticker} TTM EBITDA: ${income.get('ebitda'):,.0f}")

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
                    ticker, datetime.now().date(), 'annual', income.get('fiscal_year'), income.get('fiscal_quarter'),
                    income.get('revenue'), income.get('gross_profit'),
                    income.get('operating_income'), income.get('net_income'),
                    income.get('ebitda'), 'yahoo_finance', datetime.now()
                ))
            
            self.conn.commit()
            logging.info(f"Successfully stored fundamental data for {ticker}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing fundamental data for {ticker}: {e}")
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', type=str, default='AAPL', help='Ticker symbol to fetch')
    args = parser.parse_args()
    service = YahooFinanceService()
    test_ticker = args.ticker
    result = service.get_fundamental_data(test_ticker)
    if result:
        print(f"Successfully fetched fundamental data for {test_ticker}")
        if result.get('financial_data'):
            print(f"Financial data keys: {list(result['financial_data'].keys())}")
        if result.get('key_stats'):
            print(f"Key stats keys: {list(result['key_stats'].keys())}")
    else:
        print(f"Failed to fetch fundamental data for {test_ticker}")
    service.close() 