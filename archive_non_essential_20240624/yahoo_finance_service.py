#!/usr/bin/env python3
"""
Yahoo Finance Financial Data Service
"""

from common_imports import (
    os, time, logging, requests, pd, datetime, timedelta, 
    psycopg2, DB_CONFIG, setup_logging, get_api_rate_limiter, safe_get_numeric, safe_get_value
)
import yfinance as yf
from typing import Dict, Optional, List, Any
import argparse
from base_service import BaseService

# Setup logging for this service
setup_logging('yahoo_finance')

YAHOO_ENDPOINTS = {
    'financials': '/v1/finance/financials',
    'key_statistics': '/v11/finance/quoteSummary',
    'balance_sheet': '/v1/finance/balance_sheet',
    'cash_flow': '/v1/finance/cash_flow'
}

class YahooFinanceService(BaseService):
    def __init__(self):
        super().__init__('yahoo_finance')
        self.api_limiter = get_api_rate_limiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.max_retries = 3
        self.base_delay = 2  # seconds
        self.base_url = "https://query1.finance.yahoo.com"

    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current price data for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'regularMarketPrice' not in info:
                return None
            
            return {
                'price': info.get('regularMarketPrice'),
                'volume': info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'change': info.get('regularMarketChange'),
                'change_percent': info.get('regularMarketChangePercent'),
                'data_source': 'yahoo_finance',
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Error getting data for {ticker}: {e}")
            return None

    def get_current_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current price data for a ticker (alias for get_data)"""
        return self.get_data(ticker)

    def fetch_financial_statements(self, ticker: str) -> Optional[Dict]:
        """Fetch financial statements from Yahoo Finance with exponential backoff on rate limit"""
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
        """Parse key statistics from Yahoo Finance info"""
        try:
            key_stats = {
                'ticker': ticker,
                'data_source': 'yahoo',
                'last_updated': datetime.now(),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'ev_to_ebitda': info.get('enterpriseToEbitda'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'gross_margin': info.get('grossMargins'),
                'beta': info.get('beta'),
                'dividend_yield': info.get('dividendYield'),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'insider_ownership': info.get('heldPercentInsiders'),
                'institutional_ownership': info.get('heldPercentInstitutions'),
                'short_ratio': info.get('shortRatio'),
                'short_percent_of_float': info.get('shortPercentOfFloat'),
                'average_volume': info.get('averageVolume'),
                'average_volume_10_day': info.get('averageVolume10days'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'fifty_day_average': info.get('fiftyDayAverage'),
                'two_hundred_day_average': info.get('twoHundredDayAverage')
            }
            
            return key_stats
            
        except Exception as e:
            logging.error(f"Error parsing key statistics for {ticker}: {e}")
            return None

    def safe_get_value(self, df: pd.DataFrame, row_name: str, column) -> Optional[float]:
        """Safely extract value from pandas DataFrame"""
        try:
            if row_name in df.index and column in df.columns:
                value = df.loc[row_name, column]
                if pd.notna(value) and value != '':
                    return float(value)
            return None
        except (ValueError, TypeError):
            return None

    def safe_get_numeric(self, data: Dict, key: str) -> Optional[float]:
        """Safely extract numeric value from dictionary"""
        try:
            value = data.get(key)
            if value is not None and value != '':
                return float(value)
            return None
        except (ValueError, TypeError):
            return None

    def store_fundamental_data(self, ticker: str, financial_data: Dict, key_stats: Dict) -> bool:
        """Store fundamental data in the database"""
        try:
            # Store financial statements
            if financial_data and financial_data.get('income_statement'):
                income_stmt = financial_data['income_statement']
                
                # Update fundamentals table
                query = """
                INSERT INTO fundamentals (
                    ticker, revenue, gross_profit, operating_income, net_income, ebitda,
                    total_assets, total_debt, total_equity, cash_and_equivalents,
                    current_assets, current_liabilities, operating_cash_flow, free_cash_flow,
                    capex, fiscal_year, data_source, last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (ticker) DO UPDATE SET
                    revenue = EXCLUDED.revenue,
                    gross_profit = EXCLUDED.gross_profit,
                    operating_income = EXCLUDED.operating_income,
                    net_income = EXCLUDED.net_income,
                    ebitda = EXCLUDED.ebitda,
                    total_assets = EXCLUDED.total_assets,
                    total_debt = EXCLUDED.total_debt,
                    total_equity = EXCLUDED.total_equity,
                    cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                    current_assets = EXCLUDED.current_assets,
                    current_liabilities = EXCLUDED.current_liabilities,
                    operating_cash_flow = EXCLUDED.operating_cash_flow,
                    free_cash_flow = EXCLUDED.free_cash_flow,
                    capex = EXCLUDED.capex,
                    fiscal_year = EXCLUDED.fiscal_year,
                    data_source = EXCLUDED.data_source,
                    last_updated = EXCLUDED.last_updated
                """
                
                balance_sheet = financial_data.get('balance_sheet', {})
                cash_flow = financial_data.get('cash_flow', {})
                
                self.cur.execute(query, (
                    ticker,
                    income_stmt.get('revenue'),
                    income_stmt.get('gross_profit'),
                    income_stmt.get('operating_income'),
                    income_stmt.get('net_income'),
                    income_stmt.get('ebitda'),
                    balance_sheet.get('total_assets'),
                    balance_sheet.get('total_debt'),
                    balance_sheet.get('total_equity'),
                    balance_sheet.get('cash_and_equivalents'),
                    balance_sheet.get('current_assets'),
                    balance_sheet.get('current_liabilities'),
                    cash_flow.get('operating_cash_flow'),
                    cash_flow.get('free_cash_flow'),
                    cash_flow.get('capex'),
                    income_stmt.get('fiscal_year'),
                    'yahoo',
                    datetime.now()
                ))
                
                self.conn.commit()
                logging.info(f"Stored financial data for {ticker}")
            
            # Store key statistics
            if key_stats:
                # Update key statistics table
                query = """
                INSERT INTO key_statistics (
                    ticker, market_cap, enterprise_value, pe_ratio, forward_pe, peg_ratio,
                    price_to_book, price_to_sales, ev_to_ebitda, debt_to_equity,
                    current_ratio, quick_ratio, return_on_equity, return_on_assets,
                    profit_margin, operating_margin, gross_margin, beta, dividend_yield,
                    dividend_rate, payout_ratio, shares_outstanding, float_shares,
                    insider_ownership, institutional_ownership, short_ratio,
                    short_percent_of_float, average_volume, average_volume_10_day,
                    fifty_two_week_high, fifty_two_week_low, fifty_day_average,
                    two_hundred_day_average, data_source, last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (ticker) DO UPDATE SET
                    market_cap = EXCLUDED.market_cap,
                    enterprise_value = EXCLUDED.enterprise_value,
                    pe_ratio = EXCLUDED.pe_ratio,
                    forward_pe = EXCLUDED.forward_pe,
                    peg_ratio = EXCLUDED.peg_ratio,
                    price_to_book = EXCLUDED.price_to_book,
                    price_to_sales = EXCLUDED.price_to_sales,
                    ev_to_ebitda = EXCLUDED.ev_to_ebitda,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    current_ratio = EXCLUDED.current_ratio,
                    quick_ratio = EXCLUDED.quick_ratio,
                    return_on_equity = EXCLUDED.return_on_equity,
                    return_on_assets = EXCLUDED.return_on_assets,
                    profit_margin = EXCLUDED.profit_margin,
                    operating_margin = EXCLUDED.operating_margin,
                    gross_margin = EXCLUDED.gross_margin,
                    beta = EXCLUDED.beta,
                    dividend_yield = EXCLUDED.dividend_yield,
                    dividend_rate = EXCLUDED.dividend_rate,
                    payout_ratio = EXCLUDED.payout_ratio,
                    shares_outstanding = EXCLUDED.shares_outstanding,
                    float_shares = EXCLUDED.float_shares,
                    insider_ownership = EXCLUDED.insider_ownership,
                    institutional_ownership = EXCLUDED.institutional_ownership,
                    short_ratio = EXCLUDED.short_ratio,
                    short_percent_of_float = EXCLUDED.short_percent_of_float,
                    average_volume = EXCLUDED.average_volume,
                    average_volume_10_day = EXCLUDED.average_volume_10_day,
                    fifty_two_week_high = EXCLUDED.fifty_two_week_high,
                    fifty_two_week_low = EXCLUDED.fifty_two_week_low,
                    fifty_day_average = EXCLUDED.fifty_day_average,
                    two_hundred_day_average = EXCLUDED.two_hundred_day_average,
                    data_source = EXCLUDED.data_source,
                    last_updated = EXCLUDED.last_updated
                """
                
                self.cur.execute(query, (
                    ticker,
                    key_stats.get('market_cap'),
                    key_stats.get('enterprise_value'),
                    key_stats.get('pe_ratio'),
                    key_stats.get('forward_pe'),
                    key_stats.get('peg_ratio'),
                    key_stats.get('price_to_book'),
                    key_stats.get('price_to_sales'),
                    key_stats.get('ev_to_ebitda'),
                    key_stats.get('debt_to_equity'),
                    key_stats.get('current_ratio'),
                    key_stats.get('quick_ratio'),
                    key_stats.get('return_on_equity'),
                    key_stats.get('return_on_assets'),
                    key_stats.get('profit_margin'),
                    key_stats.get('operating_margin'),
                    key_stats.get('gross_margin'),
                    key_stats.get('beta'),
                    key_stats.get('dividend_yield'),
                    key_stats.get('dividend_rate'),
                    key_stats.get('payout_ratio'),
                    key_stats.get('shares_outstanding'),
                    key_stats.get('float_shares'),
                    key_stats.get('insider_ownership'),
                    key_stats.get('institutional_ownership'),
                    key_stats.get('short_ratio'),
                    key_stats.get('short_percent_of_float'),
                    key_stats.get('average_volume'),
                    key_stats.get('average_volume_10_day'),
                    key_stats.get('fifty_two_week_high'),
                    key_stats.get('fifty_two_week_low'),
                    key_stats.get('fifty_day_average'),
                    key_stats.get('two_hundred_day_average'),
                    'yahoo',
                    datetime.now()
                ))
                
                self.conn.commit()
                logging.info(f"Stored key statistics for {ticker}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error storing fundamental data for {ticker}: {e}")
            self.conn.rollback()
            return False

    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get fundamental data for a ticker from the database"""
        try:
            # Get fundamentals
            query = "SELECT * FROM fundamentals WHERE ticker = %s"
            self.cur.execute(query, (ticker,))
            fundamentals = self.cur.fetchone()
            
            # Get key statistics
            query = "SELECT * FROM key_statistics WHERE ticker = %s"
            self.cur.execute(query, (ticker,))
            key_stats = self.cur.fetchone()
            
            if fundamentals or key_stats:
                return {
                    'fundamentals': fundamentals,
                    'key_statistics': key_stats
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

def main():
    """Main function for testing"""
    parser = argparse.ArgumentParser(description='Yahoo Finance Service')
    parser.add_argument('--ticker', required=True, help='Ticker symbol')
    parser.add_argument('--test', action='store_true', help='Test mode')
    args = parser.parse_args()
    
    service = YahooFinanceService()
    
    try:
        if args.test:
            # Test current price
            price_data = service.get_data(args.ticker)
            print(f"Current price data for {args.ticker}: {price_data}")
            
            # Test financial statements
            financial_data = service.fetch_financial_statements(args.ticker)
            print(f"Financial data for {args.ticker}: {financial_data}")
            
            # Test key statistics
            key_stats = service.fetch_key_statistics(args.ticker)
            print(f"Key statistics for {args.ticker}: {key_stats}")
        else:
            # Fetch and store data
            financial_data = service.fetch_financial_statements(args.ticker)
            key_stats = service.fetch_key_statistics(args.ticker)
            
            if financial_data or key_stats:
                success = service.store_fundamental_data(args.ticker, financial_data, key_stats)
                print(f"Data storage {'successful' if success else 'failed'} for {args.ticker}")
            else:
                print(f"No data available for {args.ticker}")
    
    finally:
        service.close()

if __name__ == "__main__":
    main() 