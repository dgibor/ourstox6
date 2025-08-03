"""
Yahoo Finance Service

Free, reliable service for both pricing and fundamental data.
No API key required - always available as primary service.
"""

import logging
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import requests
from dataclasses import dataclass
import numpy as np

from .database import DatabaseManager
from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)


@dataclass
class YahooDataResult:
    """Result from Yahoo Finance data fetch"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: str = 'yahoo'


class YahooFinanceService:
    """
    Yahoo Finance service for pricing and fundamental data.
    
    Features:
    - Free service, no API key required
    - Comprehensive pricing data (real-time and historical)
    - Full fundamental data (financial statements, ratios)
    - Batch processing capability (up to 100 symbols)
    - Global coverage (stocks, ETFs, options, forex)
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.error_handler = ErrorHandler("yahoo_finance_service")
        self.service_name = "Yahoo Finance"
        self.logger = logging.getLogger("yahoo_finance_service")
        
        # No API key required for Yahoo Finance
        self.api_key = None
        self.base_url = "https://query1.finance.yahoo.com"
        
        # Rate limiting (Yahoo is free but we should be respectful)
        self.max_requests_per_minute = 60  # Conservative limit
        self.delay_between_requests = 1.0  # 1 second between requests
        
        self.logger.info("✅ Yahoo Finance service initialized (free, no API key required)")
    
    def get_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get current pricing data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with pricing data or None if failed
        """
        try:
            self.logger.debug(f"Fetching pricing data for {ticker}")
            
            # Use yfinance to get current data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            
            if hist.empty:
                self.logger.debug(f"No pricing data found for {ticker}")
                return None
            
            latest = hist.iloc[-1]
            info = stock.info
            
            return {
                'ticker': ticker,
                'price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']) if pd.notna(latest['Volume']) else 0,
                'market_cap': info.get('marketCap'),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'data_source': 'yahoo',
                'timestamp': datetime.now(),
                'currency': info.get('currency', 'USD')
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching pricing data for {ticker}: {e}")
            return None
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with fundamental data or None if failed
        """
        try:
            self.logger.debug(f"Fetching fundamental data for {ticker}")
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                self.logger.warning(f"No fundamental data found for {ticker}")
                return None
            
            # Get financial statements
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            # Extract key fundamental metrics
            fundamental_data = {
                'ticker': ticker,
                'market_cap': info.get('marketCap'),
                'revenue_ttm': info.get('totalRevenue'),
                'net_income_ttm': info.get('netIncomeToCommon'),
                'total_debt': info.get('totalDebt'),
                'total_cash': info.get('totalCash'),
                'book_value': info.get('bookValue'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'pe_ratio': info.get('trailingPE'),
                'pb_ratio': info.get('priceToBook'),
                'ps_ratio': info.get('priceToSalesTrailing12Months'),
                'debt_to_equity': info.get('debtToEquity'),
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'gross_margin': info.get('grossMargins'),
                'dividend_yield': info.get('dividendYield'),
                'peg_ratio': info.get('pegRatio'),
                'beta': info.get('beta'),
                'enterprise_value': info.get('enterpriseValue'),
                'ev_revenue': info.get('enterpriseToRevenue'),
                'ev_ebitda': info.get('enterpriseToEbitda'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'data_source': 'yahoo',
                'timestamp': datetime.now()
            }
            
            # Clean None values and convert to proper types
            cleaned_data = {}
            for key, value in fundamental_data.items():
                if value is not None and pd.notna(value):
                    if isinstance(value, (int, float)) and not np.isinf(value):
                        cleaned_data[key] = float(value)
                    else:
                        cleaned_data[key] = value
                else:
                    cleaned_data[key] = None
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error fetching fundamental data for {ticker}: {e}")
            return None
    
    def get_batch_data(self, tickers: List[str], data_type: str = 'pricing') -> Dict[str, Dict[str, Any]]:
        """
        Get data for multiple tickers in batch
        
        Args:
            tickers: List of ticker symbols (up to 100)
            data_type: 'pricing' or 'fundamentals'
            
        Returns:
            Dict mapping ticker to data
        """
        results = {}
        
        if len(tickers) > 100:
            self.logger.warning(f"Too many tickers ({len(tickers)}), limiting to first 100")
            tickers = tickers[:100]
        
        self.logger.info(f"Fetching {data_type} data for {len(tickers)} tickers")
        
        if data_type == 'pricing':
            # Yahoo Finance supports batch pricing requests
            try:
                # Use yfinance download for batch pricing
                data = yf.download(' '.join(tickers), period="1d", group_by='ticker', progress=False)
                
                for ticker in tickers:
                    try:
                        if ticker in data.columns.levels[0]:
                            ticker_data = data[ticker].iloc[-1]
                            
                            if not ticker_data.isna().all():
                                results[ticker] = {
                                    'ticker': ticker,
                                    'price': float(ticker_data['Close']),
                                    'open': float(ticker_data['Open']),
                                    'high': float(ticker_data['High']),
                                    'low': float(ticker_data['Low']),
                                    'volume': int(ticker_data['Volume']) if pd.notna(ticker_data['Volume']) else 0,
                                    'data_source': 'yahoo',
                                    'timestamp': datetime.now()
                                }
                    except Exception as e:
                        self.logger.warning(f"Error processing batch data for {ticker}: {e}")
                        
            except Exception as e:
                self.logger.error(f"Batch pricing request failed: {e}")
                # Fallback to individual requests
                for ticker in tickers:
                    data = self.get_data(ticker)
                    if data:
                        results[ticker] = data
        
        else:  # fundamentals
            # Fundamental data requires individual requests
            for ticker in tickers:
                data = self.get_fundamental_data(ticker)
                if data:
                    results[ticker] = data
        
        self.logger.info(f"Successfully fetched data for {len(results)}/{len(tickers)} tickers")
        return results
    
    def store_fundamental_data(self, ticker: str, financial_data: Dict, key_stats: Dict = None) -> bool:
        """
        Store fundamental data in database
        
        Args:
            ticker: Stock ticker symbol
            financial_data: Financial data dict
            key_stats: Additional key statistics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Combine financial data and key stats
            if key_stats:
                financial_data.update(key_stats)
            
            # Store in company_fundamentals table
            sql = """
            INSERT INTO company_fundamentals (
                ticker, report_date, period_type, market_cap, revenue_ttm, net_income_ttm, total_debt,
                total_cash, book_value, shares_outstanding, pe_ratio, pb_ratio,
                ps_ratio, debt_to_equity, roe, roa, profit_margin, operating_margin,
                gross_margin, dividend_yield, peg_ratio, beta, enterprise_value,
                ev_revenue, ev_ebitda, current_ratio, quick_ratio, data_source,
                last_updated
            ) VALUES (
                %(ticker)s, %(report_date)s, %(period_type)s, %(market_cap)s, %(revenue_ttm)s, %(net_income_ttm)s,
                %(total_debt)s, %(total_cash)s, %(book_value)s, %(shares_outstanding)s,
                %(pe_ratio)s, %(pb_ratio)s, %(ps_ratio)s, %(debt_to_equity)s,
                %(roe)s, %(roa)s, %(profit_margin)s, %(operating_margin)s,
                %(gross_margin)s, %(dividend_yield)s, %(peg_ratio)s, %(beta)s,
                %(enterprise_value)s, %(ev_revenue)s, %(ev_ebitda)s, %(current_ratio)s,
                %(quick_ratio)s, %(data_source)s, %(timestamp)s
            )
            ON CONFLICT (ticker) DO UPDATE SET
                report_date = EXCLUDED.report_date,
                period_type = EXCLUDED.period_type,
                market_cap = EXCLUDED.market_cap,
                revenue_ttm = EXCLUDED.revenue_ttm,
                net_income_ttm = EXCLUDED.net_income_ttm,
                total_debt = EXCLUDED.total_debt,
                total_cash = EXCLUDED.total_cash,
                book_value = EXCLUDED.book_value,
                shares_outstanding = EXCLUDED.shares_outstanding,
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                ps_ratio = EXCLUDED.ps_ratio,
                debt_to_equity = EXCLUDED.debt_to_equity,
                roe = EXCLUDED.roe,
                roa = EXCLUDED.roa,
                profit_margin = EXCLUDED.profit_margin,
                operating_margin = EXCLUDED.operating_margin,
                gross_margin = EXCLUDED.gross_margin,
                dividend_yield = EXCLUDED.dividend_yield,
                peg_ratio = EXCLUDED.peg_ratio,
                beta = EXCLUDED.beta,
                enterprise_value = EXCLUDED.enterprise_value,
                ev_revenue = EXCLUDED.ev_revenue,
                ev_ebitda = EXCLUDED.ev_ebitda,
                current_ratio = EXCLUDED.current_ratio,
                quick_ratio = EXCLUDED.quick_ratio,
                data_source = EXCLUDED.data_source,
                last_updated = EXCLUDED.last_updated
            """
            
            # Prepare data for database
            db_data = financial_data.copy()
            db_data['last_updated'] = db_data.get('timestamp', datetime.now())
            
            # Add required fields for the new schema
            from datetime import date
            db_data['report_date'] = date.today()
            db_data['period_type'] = 'ttm'
            
            self.db.execute_query(sql, db_data)
            self.logger.info(f"Successfully stored fundamental data for {ticker}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing fundamental data for {ticker}: {e}")
            return False
    
    def fetch_financial_statements(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch complete financial statements for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with financial statements or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get all financial data
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            info = stock.info
            
            statements = {
                'ticker': ticker,
                'income_statement': financials.to_dict() if not financials.empty else {},
                'balance_sheet': balance_sheet.to_dict() if not balance_sheet.empty else {},
                'cash_flow': cash_flow.to_dict() if not cash_flow.empty else {},
                'key_metrics': info,
                'data_source': 'yahoo',
                'timestamp': datetime.now()
            }
            
            return statements
            
        except Exception as e:
            self.logger.error(f"Error fetching financial statements for {ticker}: {e}")
            return None
    
    def fetch_key_statistics(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch key statistics for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with key statistics or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                return None
            
            # Extract key statistics
            key_stats = {
                'ticker': ticker,
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'enterprise_value': info.get('enterpriseValue'),
                'profit_margins': info.get('profitMargins'),
                'operating_margins': info.get('operatingMargins'),
                'return_on_assets': info.get('returnOnAssets'),
                'return_on_equity': info.get('returnOnEquity'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'debt_to_equity': info.get('debtToEquity'),
                'gross_margins': info.get('grossMargins'),
                'ebitda_margins': info.get('ebitdaMargins'),
                'data_source': 'yahoo',
                'timestamp': datetime.now()
            }
            
            return key_stats
            
        except Exception as e:
            self.logger.error(f"Error fetching key statistics for {ticker}: {e}")
            return None
    
    def check_service_health(self) -> bool:
        """
        Check if Yahoo Finance service is available
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Test with a known good ticker
            test_ticker = "AAPL"
            data = self.get_data(test_ticker)
            
            if data and data.get('price'):
                self.logger.info("✅ Yahoo Finance service health check passed")
                return True
            else:
                self.logger.warning("⚠️ Yahoo Finance service health check failed - no data")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Yahoo Finance service health check failed: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about this service
        
        Returns:
            Dict with service information
        """
        return {
            'name': self.service_name,
            'type': 'free',
            'api_key_required': False,
            'rate_limits': {
                'requests_per_minute': self.max_requests_per_minute,
                'daily_limit': None  # No daily limit
            },
            'capabilities': [
                'real_time_pricing',
                'historical_pricing',
                'fundamental_data',
                'financial_statements',
                'key_statistics',
                'batch_processing',
                'global_coverage'
            ],
            'data_types': [
                'pricing',
                'fundamentals',
                'financial_statements',
                'ratios',
                'statistics'
            ],
            'coverage': [
                'US_stocks',
                'international_stocks',
                'ETFs',
                'options',
                'forex',
                'crypto'
            ],
            'cost_per_call': 0.0,
            'reliability_score': 0.95,
            'batch_limit': 100
        } 