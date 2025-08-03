#!/usr/bin/env python3
"""
Enhanced Financial Modeling Prep (FMP) Service for comprehensive fundamental data
"""

import os
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from typing import Dict, Optional, List, Any
from .database import DatabaseManager

# API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', 5432)
}

class EnhancedFMPService:
    """Enhanced Financial Modeling Prep API service for comprehensive fundamental data"""
    
    def __init__(self):
        """Initialize database connection"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.db = DatabaseManager()
        self.max_retries = 3
        self.base_delay = 2  # seconds
        
        if not FMP_API_KEY:
            logging.error("FMP_API_KEY not found in environment variables")
            raise ValueError("FMP_API_KEY is required")

    def fetch_comprehensive_financial_data(self, ticker: str) -> Optional[Dict]:
        """Fetch comprehensive financial data from FMP API"""
        try:
            logging.info(f"Fetching comprehensive financial data for {ticker}")
            
            # Fetch all required data
            income_data = self._fetch_income_statement(ticker)
            balance_data = self._fetch_balance_sheet(ticker)
            cash_flow_data = self._fetch_cash_flow_statement(ticker)
            key_metrics_data = self._fetch_key_metrics(ticker)
            profile_data = self._fetch_company_profile(ticker)
            
            # Parse and combine all data
            comprehensive_data = self._parse_comprehensive_data(
                ticker, income_data, balance_data, cash_flow_data, 
                key_metrics_data, profile_data
            )
            
            if comprehensive_data:
                logging.info(f"Successfully fetched comprehensive data for {ticker}")
                return comprehensive_data
            else:
                logging.warning(f"No comprehensive data available for {ticker}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching comprehensive financial data for {ticker}: {e}")
            return None

    def _fetch_income_statement(self, ticker: str) -> Optional[List]:
        """Fetch income statement data"""
        try:
            url = f"{FMP_BASE_URL}/income-statement/{ticker}"
            params = {'apikey': FMP_API_KEY, 'limit': 4}
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logging.warning(f"Failed to fetch income statement for {ticker}: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching income statement for {ticker}: {e}")
            return None

    def _fetch_balance_sheet(self, ticker: str) -> Optional[List]:
        """Fetch balance sheet data"""
        try:
            url = f"{FMP_BASE_URL}/balance-sheet-statement/{ticker}"
            params = {'apikey': FMP_API_KEY, 'limit': 4}
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logging.warning(f"Failed to fetch balance sheet for {ticker}: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching balance sheet for {ticker}: {e}")
            return None

    def _fetch_cash_flow_statement(self, ticker: str) -> Optional[List]:
        """Fetch cash flow statement data"""
        try:
            url = f"{FMP_BASE_URL}/cash-flow-statement/{ticker}"
            params = {'apikey': FMP_API_KEY, 'limit': 4}
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logging.warning(f"Failed to fetch cash flow for {ticker}: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching cash flow for {ticker}: {e}")
            return None

    def _fetch_key_metrics(self, ticker: str) -> Optional[List]:
        """Fetch key metrics data"""
        try:
            url = f"{FMP_BASE_URL}/key-metrics/{ticker}"
            params = {'apikey': FMP_API_KEY, 'limit': 4}
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logging.warning(f"Failed to fetch key metrics for {ticker}: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching key metrics for {ticker}: {e}")
            return None

    def _fetch_company_profile(self, ticker: str) -> Optional[Dict]:
        """Fetch company profile data"""
        try:
            url = f"{FMP_BASE_URL}/profile/{ticker}"
            params = {'apikey': FMP_API_KEY}
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data[0] if isinstance(data, list) and data else data
            else:
                logging.warning(f"Failed to fetch company profile for {ticker}: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching company profile for {ticker}: {e}")
            return None

    def _parse_comprehensive_data(self, ticker: str, income_data: List, balance_data: List, 
                                 cash_flow_data: List, key_metrics_data: List, profile_data: Dict) -> Optional[Dict]:
        """Parse and combine all financial data"""
        try:
            if not income_data:
                logging.warning(f"No income statement data for {ticker}")
                return None
            
            # Get latest data
            latest_income = income_data[0]
            latest_balance = balance_data[0] if balance_data else {}
            latest_cash_flow = cash_flow_data[0] if cash_flow_data else {}
            latest_metrics = key_metrics_data[0] if key_metrics_data else {}
            
            # Parse fiscal year
            fiscal_year = datetime.now().year
            try:
                calendar_year = latest_income.get('calendarYear')
                if calendar_year and str(calendar_year).isdigit():
                    fiscal_year = int(calendar_year)
            except (ValueError, TypeError):
                pass
            
            # Extract all required fields
            comprehensive_data = {
                'ticker': ticker,
                'data_source': 'fmp',
                'last_updated': datetime.now(),
                'fiscal_year': fiscal_year,
                'fiscal_quarter': 1,
                'period_type': 'ttm',
                
                # Income Statement
                'revenue': safe_get_numeric(latest_income.get('revenue')),
                'gross_profit': safe_get_numeric(latest_income.get('grossProfit')),
                'operating_income': safe_get_numeric(latest_income.get('operatingIncome')),
                'net_income': safe_get_numeric(latest_income.get('netIncome')),
                'ebitda': safe_get_numeric(latest_income.get('ebitda')),
                'cost_of_goods_sold': safe_get_numeric(latest_income.get('costOfRevenue')),
                
                # Balance Sheet
                'total_assets': safe_get_numeric(latest_balance.get('totalAssets')),
                'total_debt': safe_get_numeric(latest_balance.get('totalDebt')),
                'total_equity': safe_get_numeric(latest_balance.get('totalStockholdersEquity')),
                'cash_and_equivalents': safe_get_numeric(latest_balance.get('cashAndCashEquivalents')),
                'current_assets': safe_get_numeric(latest_balance.get('totalCurrentAssets')),
                'current_liabilities': safe_get_numeric(latest_balance.get('totalCurrentLiabilities')),
                'inventory': safe_get_numeric(latest_balance.get('inventory')),
                'accounts_receivable': safe_get_numeric(latest_balance.get('netReceivables')),
                'accounts_payable': safe_get_numeric(latest_balance.get('accountPayables')),
                'retained_earnings': safe_get_numeric(latest_balance.get('retainedEarnings')),
                
                # Cash Flow
                'operating_cash_flow': safe_get_numeric(latest_cash_flow.get('operatingCashFlow')),
                'free_cash_flow': safe_get_numeric(latest_cash_flow.get('freeCashFlow')),
                'capex': safe_get_numeric(latest_cash_flow.get('capitalExpenditure')),
                
                # Key Metrics (Per Share)
                'eps_diluted': safe_get_numeric(latest_metrics.get('epsDiluted')),
                'book_value_per_share': safe_get_numeric(latest_metrics.get('bookValuePerShare')),
                'shares_outstanding': safe_get_numeric(profile_data.get('mktCap')) / safe_get_numeric(profile_data.get('price')) if profile_data.get('mktCap') and profile_data.get('price') else None,
                'shares_float': safe_get_numeric(profile_data.get('sharesFloat')),
                
                # Market Data
                'market_cap': safe_get_numeric(profile_data.get('mktCap')),
                'enterprise_value': safe_get_numeric(profile_data.get('enterpriseValue')),
            }
            
            # Calculate missing fields if possible
            if comprehensive_data['revenue'] and comprehensive_data['gross_profit'] and not comprehensive_data['cost_of_goods_sold']:
                comprehensive_data['cost_of_goods_sold'] = comprehensive_data['revenue'] - comprehensive_data['gross_profit']
                logging.info(f"{ticker}: Calculated COGS from revenue and gross profit")
            
            if comprehensive_data['market_cap'] and comprehensive_data['total_debt'] and not comprehensive_data['enterprise_value']:
                comprehensive_data['enterprise_value'] = comprehensive_data['market_cap'] + comprehensive_data['total_debt']
                logging.info(f"{ticker}: Calculated enterprise value from market cap and total debt")
            
            # Log data collection summary
            non_null_fields = sum(1 for v in comprehensive_data.values() if v is not None)
            total_fields = len(comprehensive_data)
            logging.info(f"{ticker}: Collected {non_null_fields}/{total_fields} fields ({non_null_fields/total_fields*100:.1f}%)")
            
            return comprehensive_data
            
        except Exception as e:
            logging.error(f"Error parsing comprehensive data for {ticker}: {e}")
            return None

    def store_comprehensive_data(self, ticker: str, data: Dict) -> bool:
        """Store comprehensive fundamental data in the database"""
        try:
            if not data:
                logging.warning(f"No data to store for {ticker}")
                return False
            
            # Prepare data for company_fundamentals table
            insert_query = """
            INSERT INTO company_fundamentals (
                ticker, report_date, period_type, fiscal_year, fiscal_quarter,
                revenue, gross_profit, operating_income, net_income, ebitda,
                cost_of_goods_sold, total_assets, total_debt, total_equity,
                cash_and_equivalents, current_assets, current_liabilities,
                inventory, accounts_receivable, accounts_payable, retained_earnings,
                operating_cash_flow, free_cash_flow, capex,
                eps_diluted, book_value_per_share, shares_outstanding, shares_float,
                market_cap, enterprise_value, data_source, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker) DO UPDATE SET
                report_date = EXCLUDED.report_date,
                fiscal_year = EXCLUDED.fiscal_year,
                fiscal_quarter = EXCLUDED.fiscal_quarter,
                revenue = EXCLUDED.revenue,
                gross_profit = EXCLUDED.gross_profit,
                operating_income = EXCLUDED.operating_income,
                net_income = EXCLUDED.net_income,
                ebitda = EXCLUDED.ebitda,
                cost_of_goods_sold = EXCLUDED.cost_of_goods_sold,
                total_assets = EXCLUDED.total_assets,
                total_debt = EXCLUDED.total_debt,
                total_equity = EXCLUDED.total_equity,
                cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                current_assets = EXCLUDED.current_assets,
                current_liabilities = EXCLUDED.current_liabilities,
                inventory = EXCLUDED.inventory,
                accounts_receivable = EXCLUDED.accounts_receivable,
                accounts_payable = EXCLUDED.accounts_payable,
                retained_earnings = EXCLUDED.retained_earnings,
                operating_cash_flow = EXCLUDED.operating_cash_flow,
                free_cash_flow = EXCLUDED.free_cash_flow,
                capex = EXCLUDED.capex,
                eps_diluted = EXCLUDED.eps_diluted,
                book_value_per_share = EXCLUDED.book_value_per_share,
                shares_outstanding = EXCLUDED.shares_outstanding,
                shares_float = EXCLUDED.shares_float,
                market_cap = EXCLUDED.market_cap,
                enterprise_value = EXCLUDED.enterprise_value,
                data_source = EXCLUDED.data_source,
                last_updated = EXCLUDED.last_updated
            """
            
            values = (
                data['ticker'], data['last_updated'], data['period_type'], 
                data['fiscal_year'], data['fiscal_quarter'],
                data['revenue'], data['gross_profit'], data['operating_income'], 
                data['net_income'], data['ebitda'], data['cost_of_goods_sold'],
                data['total_assets'], data['total_debt'], data['total_equity'],
                data['cash_and_equivalents'], data['current_assets'], data['current_liabilities'],
                data['inventory'], data['accounts_receivable'], data['accounts_payable'], 
                data['retained_earnings'], data['operating_cash_flow'], data['free_cash_flow'], 
                data['capex'], data['eps_diluted'], data['book_value_per_share'],
                data['shares_outstanding'], data['shares_float'], data['market_cap'], 
                data['enterprise_value'], data['data_source'], data['last_updated']
            )
            
            self.cur.execute(insert_query, values)
            self.conn.commit()
            
            logging.info(f"Successfully stored comprehensive fundamental data for {ticker}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing comprehensive data for {ticker}: {e}")
            self.conn.rollback()
            return False

    def get_comprehensive_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive fundamental data for a ticker"""
        try:
            # Fetch data
            data = self.fetch_comprehensive_financial_data(ticker)
            
            if data:
                # Store data
                storage_success = self.store_comprehensive_data(ticker, data)
                if storage_success:
                    return data
                else:
                    logging.error(f"Failed to store comprehensive data for {ticker}")
                    return None
            else:
                logging.warning(f"No comprehensive data available for {ticker}")
                return None
                
        except Exception as e:
            logging.error(f"Error getting comprehensive fundamental data for {ticker}: {e}")
            return None

    def close(self):
        """Close database connections"""
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
        except Exception as e:
            logging.error(f"Error closing connections: {e}")

def safe_get_numeric(value):
    """Safely convert value to numeric, returning None if conversion fails"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None 