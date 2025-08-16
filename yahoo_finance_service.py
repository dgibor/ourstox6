import yfinance as yf
import pandas as pd
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooFinanceService:
    """
    Yahoo Finance API service for fetching fundamental data
    Handles rate limiting and provides fallback mechanisms
    """
    
    def __init__(self):
        self.session = self._create_session()
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
        
    def _create_session(self):
        """Create a session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive fundamental data for a ticker
        Returns None if data cannot be fetched
        """
        try:
            self._rate_limit()
            
            # Create ticker object
            ticker_obj = yf.Ticker(ticker)
            
            # Get financial data
            info = ticker_obj.info
            
            if not info or len(info) < 10:  # Basic validation
                logger.warning(f"Insufficient data for {ticker}")
                return None
            
            # Extract and calculate fundamental ratios
            fundamental_data = self._extract_fundamental_ratios(info, ticker_obj)
            
            if fundamental_data:
                logger.info(f"Successfully fetched fundamental data for {ticker}")
                return fundamental_data
            else:
                logger.warning(f"Failed to extract fundamental data for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def _extract_fundamental_ratios(self, info: Dict[str, Any], ticker_obj: yf.Ticker) -> Optional[Dict[str, Any]]:
        """Extract and calculate fundamental ratios from Yahoo Finance data"""
        try:
            # Get financial statements for additional calculations
            balance_sheet = ticker_obj.balance_sheet
            income_stmt = ticker_obj.income_stmt
            cash_flow = ticker_obj.cashflow
            
            # Extract basic ratios from info
            ratios = {
                'ticker': info.get('symbol', ''),
                'pe_ratio': self._safe_float(info.get('trailingPE')),
                'pb_ratio': self._safe_float(info.get('priceToBook')),
                'roe': self._safe_float(info.get('returnOnEquity')) * 100 if info.get('returnOnEquity') else None,
                'roa': self._safe_float(info.get('returnOnAssets')) * 100 if info.get('returnOnAssets') else None,
                'debt_to_equity': self._safe_float(info.get('debtToEquity')),
                'current_ratio': self._safe_float(info.get('currentRatio')),
                'gross_margin': self._safe_float(info.get('grossMargins')) * 100 if info.get('grossMargins') else None,
                'operating_margin': self._safe_float(info.get('operatingMargins')) * 100 if info.get('operatingMargins') else None,
                'net_margin': self._safe_float(info.get('profitMargins')) * 100 if info.get('profitMargins') else None,
                'market_cap': self._safe_float(info.get('marketCap')),
                'enterprise_value': self._safe_float(info.get('enterpriseValue')),
                'total_revenue': self._safe_float(info.get('totalRevenue')),
                'net_income': self._safe_float(info.get('netIncomeToCommon')),
                'ebitda': self._safe_float(info.get('ebitda')),
                'total_assets': self._safe_float(info.get('totalAssets')),
                'total_equity': self._safe_float(info.get('totalEquity')),
                'total_debt': self._safe_float(info.get('totalDebt')),
                'current_assets': self._safe_float(info.get('currentAssets')),
                'current_liabilities': self._safe_float(info.get('currentLiabilities')),
                'book_value_per_share': self._safe_float(info.get('bookValue')),
                'earnings_per_share': self._safe_float(info.get('trailingEps')),
                'revenue_per_share': self._safe_float(info.get('revenuePerShare')),
                'price_to_sales': self._safe_float(info.get('priceToSalesTrailing12Months')),
                'price_to_cash_flow': self._safe_float(info.get('priceToCashflow')),
                'enterprise_to_revenue': self._safe_float(info.get('enterpriseToRevenue')),
                'enterprise_to_ebitda': self._safe_float(info.get('enterpriseToEbitda')),
            }
            
            # Calculate additional ratios from financial statements
            ratios.update(self._calculate_additional_ratios(balance_sheet, income_stmt, cash_flow, ratios))
            
            # Calculate growth rates
            ratios.update(self._calculate_growth_rates(ticker_obj, ratios))
            
            # Calculate EV/EBITDA if missing
            if not ratios.get('ev_ebitda') and ratios.get('enterprise_value') and ratios.get('ebitda'):
                ebitda = ratios['ebitda']
                if ebitda and ebitda != 0:
                    ratios['ev_ebitda'] = ratios['enterprise_value'] / ebitda
                else:
                    logger.warning(f"EBITDA is zero or None, skipping EV/EBITDA calculation")
            
            # Remove None values and return
            return {k: v for k, v in ratios.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Error extracting ratios: {str(e)}")
            return None
    
    def _calculate_additional_ratios(self, balance_sheet: pd.DataFrame, income_stmt: pd.DataFrame, 
                                   cash_flow: pd.DataFrame, ratios: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional ratios from financial statements"""
        additional_ratios = {}
        
        try:
            if not balance_sheet.empty and not income_stmt.empty:
                # Get most recent data
                latest_bs = balance_sheet.iloc[:, 0] if not balance_sheet.empty else pd.Series()
                latest_is = income_stmt.iloc[:, 0] if not income_stmt.empty else pd.Series()
                
                # Calculate ratios if base data is available
                if 'Total Assets' in latest_bs and 'Net Income' in latest_is:
                    if not ratios.get('roa'):
                        total_assets = latest_bs['Total Assets']
                        if total_assets and total_assets != 0:
                            additional_ratios['roa'] = (latest_is['Net Income'] / total_assets) * 100
                        else:
                            logger.warning(f"Total Assets is zero or None, skipping ROA calculation")
                
                if 'Total Stockholder Equity' in latest_bs and 'Net Income' in latest_is:
                    if not ratios.get('roe'):
                        total_equity = latest_bs['Total Stockholder Equity']
                        if total_equity and total_equity != 0:
                            additional_ratios['roe'] = (latest_is['Net Income'] / total_equity) * 100
                        else:
                            logger.warning(f"Total Stockholder Equity is zero or None, skipping ROE calculation")
                
                if 'Total Current Assets' in latest_bs and 'Total Current Liabilities' in latest_bs:
                    if not ratios.get('current_ratio'):
                        current_assets = latest_bs['Total Current Assets']
                        current_liabilities = latest_bs['Total Current Liabilities']
                        if current_assets and current_liabilities and current_liabilities != 0:
                            additional_ratios['current_ratio'] = current_assets / current_liabilities
                        else:
                            logger.warning(f"Current Assets or Liabilities are zero or None, skipping current ratio calculation")
                
                if 'Total Revenue' in latest_is and 'Gross Profit' in latest_is:
                    if not ratios.get('gross_margin'):
                        total_revenue = latest_is['Total Revenue']
                        if total_revenue and total_revenue != 0:
                            additional_ratios['gross_margin'] = (latest_is['Gross Profit'] / total_revenue) * 100
                        else:
                            logger.warning(f"Total Revenue is zero or None, skipping gross margin calculation")
                
                if 'Total Revenue' in latest_is and 'Operating Income' in latest_is:
                    if not ratios.get('operating_margin'):
                        total_revenue = latest_is['Total Revenue']
                        if total_revenue and total_revenue != 0:
                            additional_ratios['operating_margin'] = (latest_is['Operating Income'] / total_revenue) * 100
                        else:
                            logger.warning(f"Total Revenue is zero or None, skipping operating margin calculation")
                
                if 'Total Revenue' in latest_is and 'Net Income' in latest_is:
                    if not ratios.get('net_margin'):
                        total_revenue = latest_is['Total Revenue']
                        if total_revenue and total_revenue != 0:
                            additional_ratios['net_margin'] = (latest_is['Net Income'] / total_revenue) * 100
                        else:
                            logger.warning(f"Total Revenue is zero or None, skipping net margin calculation")
                        
        except Exception as e:
            logger.warning(f"Error calculating additional ratios: {str(e)}")
        
        return additional_ratios
    
    def _calculate_growth_rates(self, ticker_obj: yf.Ticker, ratios: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate growth rates from historical data"""
        growth_rates = {}
        
        try:
            # Get historical financial data
            income_stmt = ticker_obj.income_stmt
            
            if not income_stmt.empty and len(income_stmt.columns) >= 2:
                # Calculate revenue growth
                if 'Total Revenue' in income_stmt.index:
                    current_revenue = income_stmt.loc['Total Revenue'].iloc[0]
                    previous_revenue = income_stmt.loc['Total Revenue'].iloc[1]
                    if previous_revenue and previous_revenue != 0:
                        growth_rates['revenue_growth_yoy'] = ((current_revenue - previous_revenue) / previous_revenue) * 100
                
                # Calculate earnings growth
                if 'Net Income' in income_stmt.index:
                    current_earnings = income_stmt.loc['Net Income'].iloc[0]
                    previous_earnings = income_stmt.loc['Net Income'].iloc[1]
                    if previous_earnings and previous_earnings != 0:
                        growth_rates['earnings_growth_yoy'] = ((current_earnings - previous_earnings) / previous_earnings) * 100
                        
        except Exception as e:
            logger.warning(f"Error calculating growth rates: {str(e)}")
        
        return growth_rates
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_data_confidence(self, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate data confidence metrics for the fetched data"""
        if not fundamental_data:
            return {'confidence': 0, 'missing_count': 12, 'warnings': ['No data available']}
        
        # Define required metrics and their weights
        required_metrics = {
            'pe_ratio': 1.0,
            'pb_ratio': 1.0,
            'roe': 1.0,
            'roa': 1.0,
            'debt_to_equity': 1.0,
            'current_ratio': 1.0,
            'ev_ebitda': 1.0,
            'gross_margin': 1.0,
            'operating_margin': 1.0,
            'net_margin': 1.0,
            'revenue_growth_yoy': 1.0,
            'earnings_growth_yoy': 1.0
        }
        
        available_metrics = 0
        missing_metrics = []
        warnings = []
        
        for metric, weight in required_metrics.items():
            if fundamental_data.get(metric) is not None:
                available_metrics += weight
            else:
                missing_metrics.append(metric)
        
        total_weight = sum(required_metrics.values())
        confidence = (available_metrics / total_weight) * 100 if total_weight > 0 else 0
        
        # Add warnings for missing critical metrics
        critical_metrics = ['pe_ratio', 'roe', 'debt_to_equity']
        for metric in critical_metrics:
            if metric in missing_metrics:
                warnings.append(f'Missing critical metric: {metric}')
        
        return {
            'confidence': round(confidence, 2),
            'missing_count': len(missing_metrics),
            'warnings': warnings,
            'available_metrics': list(fundamental_data.keys())
        }

def main():
    """Test the Yahoo Finance service"""
    service = YahooFinanceService()
    
    # Test with a few tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        data = service.get_fundamental_data(ticker)
        
        if data:
            confidence = service.get_data_confidence(data)
            print(f"Data confidence: {confidence['confidence']}%")
            print(f"Missing metrics: {confidence['missing_count']}")
            print(f"Available metrics: {len(data)}")
            print(f"Sample ratios: PE={data.get('pe_ratio')}, ROE={data.get('roe')}, Debt/Equity={data.get('debt_to_equity')}")
        else:
            print(f"No data available for {ticker}")

if __name__ == "__main__":
    main() 