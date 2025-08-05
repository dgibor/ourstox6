import requests
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FMPService:
    """
    Financial Modeling Prep (FMP) API service for fetching fundamental data
    Used as a fallback when Yahoo Finance data is insufficient
    """
    
    def __init__(self):
        self.api_key = os.getenv('FMP_API_KEY')
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.last_request_time = 0
        
        if not self.api_key:
            logger.warning("FMP API key not found in environment variables")
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make API request with error handling"""
        if not self.api_key:
            logger.error("FMP API key not available")
            return None
        
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/{endpoint}"
            params = params or {}
            params['apikey'] = self.api_key
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"FMP API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in FMP request: {str(e)}")
            return None
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive fundamental data for a ticker
        Returns None if data cannot be fetched
        """
        try:
            # Get company profile
            profile = self._get_company_profile(ticker)
            if not profile:
                return None
            
            # Get financial ratios
            ratios = self._get_financial_ratios(ticker)
            
            # Get income statement
            income_stmt = self._get_income_statement(ticker)
            
            # Get balance sheet
            balance_sheet = self._get_balance_sheet(ticker)
            
            # Get cash flow statement
            cash_flow = self._get_cash_flow_statement(ticker)
            
            # Combine all data
            fundamental_data = self._combine_fundamental_data(
                profile, ratios, income_stmt, balance_sheet, cash_flow
            )
            
            if fundamental_data:
                logger.info(f"Successfully fetched FMP fundamental data for {ticker}")
                return fundamental_data
            else:
                logger.warning(f"Failed to extract FMP fundamental data for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching FMP data for {ticker}: {str(e)}")
            return None
    
    def _get_company_profile(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company profile information"""
        endpoint = f"profile/{ticker}"
        data = self._make_request(endpoint)
        
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None
    
    def _get_financial_ratios(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """Get financial ratios"""
        endpoint = f"ratios/{ticker}"
        data = self._make_request(endpoint)
        
        if data and isinstance(data, list):
            return data
        return None
    
    def _get_income_statement(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """Get income statement"""
        endpoint = f"income-statement/{ticker}"
        params = {'limit': 4}  # Get last 4 quarters
        data = self._make_request(endpoint, params)
        
        if data and isinstance(data, list):
            return data
        return None
    
    def _get_balance_sheet(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """Get balance sheet"""
        endpoint = f"balance-sheet-statement/{ticker}"
        params = {'limit': 4}  # Get last 4 quarters
        data = self._make_request(endpoint, params)
        
        if data and isinstance(data, list):
            return data
        return None
    
    def _get_cash_flow_statement(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """Get cash flow statement"""
        endpoint = f"cash-flow-statement/{ticker}"
        params = {'limit': 4}  # Get last 4 quarters
        data = self._make_request(endpoint, params)
        
        if data and isinstance(data, list):
            return data
        return None
    
    def _combine_fundamental_data(self, profile: Dict[str, Any], ratios: List[Dict[str, Any]], 
                                 income_stmt: List[Dict[str, Any]], balance_sheet: List[Dict[str, Any]], 
                                 cash_flow: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Combine all financial data into a single dictionary"""
        try:
            combined_data = {
                'ticker': profile.get('symbol', ''),
                'market_cap': self._safe_float(profile.get('mktCap')),
                'enterprise_value': self._safe_float(profile.get('enterpriseValue')),
                'sector': profile.get('sector', ''),
                'industry': profile.get('industry', ''),
            }
            
            # Extract ratios from financial ratios endpoint
            if ratios and len(ratios) > 0:
                latest_ratios = ratios[0]  # Most recent
                combined_data.update({
                    'pe_ratio': self._safe_float(latest_ratios.get('priceEarningsRatio')),
                    'pb_ratio': self._safe_float(latest_ratios.get('priceToBookRatio')),
                    'roe': self._safe_float(latest_ratios.get('returnOnEquity')) * 100,
                    'roa': self._safe_float(latest_ratios.get('returnOnAssets')) * 100,
                    'debt_to_equity': self._safe_float(latest_ratios.get('debtEquityRatio')),
                    'current_ratio': self._safe_float(latest_ratios.get('currentRatio')),
                    'gross_margin': self._safe_float(latest_ratios.get('grossProfitMargin')) * 100,
                    'operating_margin': self._safe_float(latest_ratios.get('operatingProfitMargin')) * 100,
                    'net_margin': self._safe_float(latest_ratios.get('netProfitMargin')) * 100,
                    'ev_ebitda': self._safe_float(latest_ratios.get('enterpriseValueMultiple')),
                    'price_to_sales': self._safe_float(latest_ratios.get('priceToSalesRatio')),
                    'price_to_cash_flow': self._safe_float(latest_ratios.get('priceCashFlowRatio')),
                })
            
            # Extract data from financial statements
            if income_stmt and len(income_stmt) > 0:
                latest_income = income_stmt[0]
                combined_data.update({
                    'total_revenue': self._safe_float(latest_income.get('revenue')),
                    'net_income': self._safe_float(latest_income.get('netIncome')),
                    'gross_profit': self._safe_float(latest_income.get('grossProfit')),
                    'operating_income': self._safe_float(latest_income.get('operatingIncome')),
                    'ebitda': self._safe_float(latest_income.get('ebitda')),
                })
                
                # Calculate growth rates if we have multiple periods
                if len(income_stmt) >= 2:
                    previous_income = income_stmt[1]
                    current_revenue = self._safe_float(latest_income.get('revenue'))
                    previous_revenue = self._safe_float(previous_income.get('revenue'))
                    current_earnings = self._safe_float(latest_income.get('netIncome'))
                    previous_earnings = self._safe_float(previous_income.get('netIncome'))
                    
                    if current_revenue and previous_revenue and previous_revenue != 0:
                        combined_data['revenue_growth_yoy'] = ((current_revenue - previous_revenue) / previous_revenue) * 100
                    
                    if current_earnings and previous_earnings and previous_earnings != 0:
                        combined_data['earnings_growth_yoy'] = ((current_earnings - previous_earnings) / previous_earnings) * 100
            
            if balance_sheet and len(balance_sheet) > 0:
                latest_balance = balance_sheet[0]
                combined_data.update({
                    'total_assets': self._safe_float(latest_balance.get('totalAssets')),
                    'total_equity': self._safe_float(latest_balance.get('totalStockholdersEquity')),
                    'total_debt': self._safe_float(latest_balance.get('totalDebt')),
                    'current_assets': self._safe_float(latest_balance.get('totalCurrentAssets')),
                    'current_liabilities': self._safe_float(latest_balance.get('totalCurrentLiabilities')),
                    'book_value_per_share': self._safe_float(latest_balance.get('bookValuePerShare')),
                })
            
            if cash_flow and len(cash_flow) > 0:
                latest_cash_flow = cash_flow[0]
                combined_data.update({
                    'operating_cash_flow': self._safe_float(latest_cash_flow.get('operatingCashFlow')),
                    'free_cash_flow': self._safe_float(latest_cash_flow.get('freeCashFlow')),
                })
            
            # Calculate additional ratios if base data is available
            combined_data.update(self._calculate_additional_ratios(combined_data))
            
            # Remove None values and return
            return {k: v for k, v in combined_data.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Error combining FMP data: {str(e)}")
            return None
    
    def _calculate_additional_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional ratios from available data"""
        additional_ratios = {}
        
        try:
            # Calculate EV/EBITDA if missing
            if not data.get('ev_ebitda') and data.get('enterprise_value') and data.get('ebitda'):
                additional_ratios['ev_ebitda'] = data['enterprise_value'] / data['ebitda']
            
            # Calculate ROE if missing
            if not data.get('roe') and data.get('net_income') and data.get('total_equity'):
                additional_ratios['roe'] = (data['net_income'] / data['total_equity']) * 100
            
            # Calculate ROA if missing
            if not data.get('roa') and data.get('net_income') and data.get('total_assets'):
                additional_ratios['roa'] = (data['net_income'] / data['total_assets']) * 100
            
            # Calculate debt to equity if missing
            if not data.get('debt_to_equity') and data.get('total_debt') and data.get('total_equity'):
                additional_ratios['debt_to_equity'] = data['total_debt'] / data['total_equity']
            
            # Calculate current ratio if missing
            if not data.get('current_ratio') and data.get('current_assets') and data.get('current_liabilities'):
                additional_ratios['current_ratio'] = data['current_assets'] / data['current_liabilities']
            
            # Calculate margins if missing
            if not data.get('gross_margin') and data.get('gross_profit') and data.get('total_revenue'):
                additional_ratios['gross_margin'] = (data['gross_profit'] / data['total_revenue']) * 100
            
            if not data.get('operating_margin') and data.get('operating_income') and data.get('total_revenue'):
                additional_ratios['operating_margin'] = (data['operating_income'] / data['total_revenue']) * 100
            
            if not data.get('net_margin') and data.get('net_income') and data.get('total_revenue'):
                additional_ratios['net_margin'] = (data['net_income'] / data['total_revenue']) * 100
                
        except Exception as e:
            logger.warning(f"Error calculating additional FMP ratios: {str(e)}")
        
        return additional_ratios
    
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
    """Test the FMP service"""
    service = FMPService()
    
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