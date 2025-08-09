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

class AlphaVantageService:
    """
    Alpha Vantage API service for fetching fundamental data
    Used as the final fallback option when other APIs are insufficient
    """
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12.0  # 12 seconds between requests (free tier limit)
        self.last_request_time = 0
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not found in environment variables")
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with error handling"""
        if not self.api_key:
            logger.error("Alpha Vantage API key not available")
            return None
        
        try:
            self._rate_limit()
            
            params['apikey'] = self.api_key
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpha Vantage API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Alpha Vantage request: {str(e)}")
            return None
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive fundamental data for a ticker
        Returns None if data cannot be fetched
        """
        try:
            # Get company overview
            overview = self._get_company_overview(ticker)
            if not overview:
                return None
            
            # Get income statement
            income_stmt = self._get_income_statement(ticker)
            
            # Get balance sheet
            balance_sheet = self._get_balance_sheet(ticker)
            
            # Get cash flow statement
            cash_flow = self._get_cash_flow_statement(ticker)
            
            # Get earnings
            earnings = self._get_earnings(ticker)
            
            # Combine all data
            fundamental_data = self._combine_fundamental_data(
                overview, income_stmt, balance_sheet, cash_flow, earnings
            )
            
            if fundamental_data:
                logger.info(f"Successfully fetched Alpha Vantage fundamental data for {ticker}")
                return fundamental_data
            else:
                logger.warning(f"Failed to extract Alpha Vantage fundamental data for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {ticker}: {str(e)}")
            return None
    
    def _get_company_overview(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company overview information"""
        params = {
            'function': 'OVERVIEW',
            'symbol': ticker
        }
        return self._make_request(params)
    
    def _get_income_statement(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get income statement"""
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': ticker
        }
        return self._make_request(params)
    
    def _get_balance_sheet(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get balance sheet"""
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': ticker
        }
        return self._make_request(params)
    
    def _get_cash_flow_statement(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cash flow statement"""
        params = {
            'function': 'CASH_FLOW',
            'symbol': ticker
        }
        return self._make_request(params)
    
    def _get_earnings(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get earnings data"""
        params = {
            'function': 'EARNINGS',
            'symbol': ticker
        }
        return self._make_request(params)
    
    def _combine_fundamental_data(self, overview: Dict[str, Any], income_stmt: Dict[str, Any], 
                                 balance_sheet: Dict[str, Any], cash_flow: Dict[str, Any], 
                                 earnings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Combine all financial data into a single dictionary"""
        try:
            combined_data = {
                'ticker': overview.get('Symbol', ''),
                'sector': overview.get('Sector', ''),
                'industry': overview.get('Industry', ''),
                'market_cap': self._safe_float(overview.get('MarketCapitalization')),
                'pe_ratio': self._safe_float(overview.get('PERatio')),
                'pb_ratio': self._safe_float(overview.get('PriceToBookRatio')),
                'roe': self._safe_float(overview.get('ReturnOnEquityTTM')) * 100,
                'roa': self._safe_float(overview.get('ReturnOnAssetsTTM')) * 100,
                'debt_to_equity': self._safe_float(overview.get('DebtToEquityRatio')),
                'current_ratio': self._safe_float(overview.get('CurrentRatio')),
                'gross_margin': self._safe_float(overview.get('GrossProfitMarginTTM')) * 100,
                'operating_margin': self._safe_float(overview.get('OperatingMarginTTM')) * 100,
                'net_margin': self._safe_float(overview.get('ProfitMargin')) * 100,
                'price_to_sales': self._safe_float(overview.get('PriceToSalesRatioTTM')),
                'price_to_cash_flow': self._safe_float(overview.get('PriceToCashFlowRatioTTM')),
                'enterprise_to_revenue': self._safe_float(overview.get('EnterpriseToRevenue')),
                'enterprise_to_ebitda': self._safe_float(overview.get('EnterpriseToEBITDA')),
                'book_value_per_share': self._safe_float(overview.get('BookValue')),
                'earnings_per_share': self._safe_float(overview.get('EPS')),
                'revenue_per_share': self._safe_float(overview.get('RevenuePerShareTTM')),
            }
            
            # Extract data from financial statements
            if income_stmt and 'annualReports' in income_stmt and income_stmt['annualReports']:
                latest_income = income_stmt['annualReports'][0]
                combined_data.update({
                    'total_revenue': self._safe_float(latest_income.get('totalRevenue')),
                    'net_income': self._safe_float(latest_income.get('netIncome')),
                    'gross_profit': self._safe_float(latest_income.get('grossProfit')),
                    'operating_income': self._safe_float(latest_income.get('operatingIncome')),
                })
                
                # Calculate growth rates if we have multiple periods
                if len(income_stmt['annualReports']) >= 2:
                    previous_income = income_stmt['annualReports'][1]
                    current_revenue = self._safe_float(latest_income.get('totalRevenue'))
                    previous_revenue = self._safe_float(previous_income.get('totalRevenue'))
                    current_earnings = self._safe_float(latest_income.get('netIncome'))
                    previous_earnings = self._safe_float(previous_income.get('netIncome'))
                    
                    if current_revenue and previous_revenue and previous_revenue != 0:
                        combined_data['revenue_growth_yoy'] = ((current_revenue - previous_revenue) / previous_revenue) * 100
                    
                    if current_earnings and previous_earnings and previous_earnings != 0:
                        combined_data['earnings_growth_yoy'] = ((current_earnings - previous_earnings) / previous_earnings) * 100
            
            if balance_sheet and 'annualReports' in balance_sheet and balance_sheet['annualReports']:
                latest_balance = balance_sheet['annualReports'][0]
                combined_data.update({
                    'total_assets': self._safe_float(latest_balance.get('totalAssets')),
                    'total_equity': self._safe_float(latest_balance.get('totalShareholderEquity')),
                    'total_debt': self._safe_float(latest_balance.get('totalDebt')),
                    'current_assets': self._safe_float(latest_balance.get('totalCurrentAssets')),
                    'current_liabilities': self._safe_float(latest_balance.get('totalCurrentLiabilities')),
                })
            
            if cash_flow and 'annualReports' in cash_flow and cash_flow['annualReports']:
                latest_cash_flow = cash_flow['annualReports'][0]
                combined_data.update({
                    'operating_cash_flow': self._safe_float(latest_cash_flow.get('operatingCashflow')),
                    'free_cash_flow': self._safe_float(latest_cash_flow.get('freeCashFlow')),
                })
            
            # Calculate additional ratios from available data
            combined_data.update(self._calculate_additional_ratios(combined_data))
            
            # Remove None values and return
            return {k: v for k, v in combined_data.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Error combining Alpha Vantage data: {str(e)}")
            return None
    
    def _calculate_additional_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional ratios from available data"""
        additional_ratios = {}
        
        try:
            # Calculate EV/EBITDA if missing
            if not data.get('enterprise_to_ebitda') and data.get('market_cap') and data.get('operating_income'):
                # Estimate enterprise value as market cap + debt
                enterprise_value = data['market_cap'] + (data.get('total_debt', 0))
                # Estimate EBITDA as operating income (rough approximation)
                ebitda = data['operating_income']
                additional_ratios['ev_ebitda'] = enterprise_value / ebitda
            
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
            logger.warning(f"Error calculating additional Alpha Vantage ratios: {str(e)}")
        
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
    """Test the Alpha Vantage service"""
    service = AlphaVantageService()
    
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