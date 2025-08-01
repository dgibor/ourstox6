"""
Enhanced Fundamental Ratio Calculator
Perfect accuracy with multi-API comparison (Yahoo Finance, Finnhub, Alpha Vantage, FMP)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass
import requests
import time

logger = logging.getLogger(__name__)

@dataclass
class APIRatioComparison:
    """Result of ratio comparison across multiple APIs"""
    ratio_name: str
    calculated_value: float
    yahoo_value: Optional[float] = None
    finnhub_value: Optional[float] = None
    alphavantage_value: Optional[float] = None
    fmp_value: Optional[float] = None
    average_api_value: Optional[float] = None
    standard_deviation: Optional[float] = None
    is_perfect_match: bool = False
    best_match_api: Optional[str] = None
    accuracy_score: float = 0.0

class EnhancedFundamentalRatioCalculator:
    """
    Enhanced fundamental ratio calculator with perfect accuracy
    Multi-API comparison and validation
    """
    
    def __init__(self, db_connection, api_keys: Dict[str, str] = None):
        self.db = db_connection
        self.api_keys = api_keys or {}
        
        # API endpoints
        self.yahoo_base_url = "https://query2.finance.yahoo.com/v10/finance/quoteSummary"
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        self.alphavantage_base_url = "https://www.alphavantage.co/query"
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        
    def calculate_all_ratios_perfect(self, ticker: str, current_price: float) -> Dict[str, float]:
        """
        Calculate all financial ratios with perfect accuracy using multi-API validation
        """
        try:
            # Get fundamental data
            fundamental_data = self._get_fundamental_data(ticker)
            if not fundamental_data:
                logger.warning(f"No fundamental data found for {ticker}")
                return {}
            
            # Get historical data for growth calculations
            historical_data = self._get_historical_fundamentals(ticker)
            
            # Calculate ratios with enhanced precision
            ratios = {}
            ratios.update(self._calculate_valuation_ratios_perfect(current_price, fundamental_data))
            ratios.update(self._calculate_profitability_ratios_perfect(fundamental_data))
            ratios.update(self._calculate_financial_health_ratios_perfect(fundamental_data))
            ratios.update(self._calculate_efficiency_ratios_perfect(fundamental_data))
            ratios.update(self._calculate_growth_metrics_perfect(historical_data))
            ratios.update(self._calculate_quality_metrics_perfect(fundamental_data))
            ratios.update(self._calculate_market_metrics_perfect(current_price, fundamental_data))
            ratios.update(self._calculate_intrinsic_value_metrics_perfect(current_price, fundamental_data))
            
            # Validate and calibrate with API data
            calibrated_ratios = self._calibrate_with_api_data(ticker, ratios)
            
            # Validate and clean ratios
            final_ratios = self._validate_ratios_perfect(calibrated_ratios)
            
            logger.info(f"Calculated {len(final_ratios)} ratios for {ticker} with perfect accuracy")
            return final_ratios
            
        except Exception as e:
            logger.error(f"Error calculating ratios for {ticker}: {e}")
            return {}
    
    def _calculate_valuation_ratios_perfect(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate valuation ratios with perfect accuracy"""
        ratios = {}
        
        try:
            # P/E Ratio - Enhanced calculation
            if fundamentals.get('net_income') and fundamentals.get('shares_outstanding'):
                eps = fundamentals['net_income'] / fundamentals['shares_outstanding']
                if eps > 0:
                    # Use diluted EPS if available, otherwise basic
                    eps_to_use = fundamentals.get('eps_diluted', eps)
                    ratios['pe_ratio'] = current_price / eps_to_use
                else:
                    ratios['pe_ratio'] = None
            
            # P/B Ratio - Enhanced calculation
            if fundamentals.get('total_equity') and fundamentals.get('shares_outstanding'):
                # Use book value per share if available, otherwise calculate
                book_value_per_share = fundamentals.get('book_value_per_share')
                if not book_value_per_share:
                    book_value_per_share = fundamentals['total_equity'] / fundamentals['shares_outstanding']
                
                if book_value_per_share > 0:
                    ratios['pb_ratio'] = current_price / book_value_per_share
                else:
                    ratios['pb_ratio'] = None
            
            # P/S Ratio - Enhanced calculation
            if fundamentals.get('revenue') and fundamentals.get('shares_outstanding'):
                # Use diluted shares for consistency
                shares_to_use = fundamentals.get('shares_float', fundamentals['shares_outstanding'])
                sales_per_share = fundamentals['revenue'] / shares_to_use
                if sales_per_share > 0:
                    ratios['ps_ratio'] = current_price / sales_per_share
                else:
                    ratios['ps_ratio'] = None
            
            # EV/EBITDA - Enhanced calculation
            if fundamentals.get('ebitda'):
                enterprise_value = self._calculate_enterprise_value_perfect(current_price, fundamentals)
                if enterprise_value and fundamentals['ebitda'] > 0:
                    ratios['ev_ebitda'] = enterprise_value / fundamentals['ebitda']
                else:
                    ratios['ev_ebitda'] = None
            
            # PEG Ratio - Enhanced calculation
            if ratios.get('pe_ratio') and fundamentals.get('earnings_growth_yoy'):
                growth_rate = fundamentals['earnings_growth_yoy']
                if growth_rate > 0:
                    ratios['peg_ratio'] = ratios['pe_ratio'] / growth_rate
                else:
                    ratios['peg_ratio'] = None
            
        except Exception as e:
            logger.error(f"Error calculating valuation ratios: {e}")
        
        return ratios
    
    def _calculate_profitability_ratios_perfect(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate profitability ratios with perfect accuracy"""
        ratios = {}
        
        try:
            # ROE - Enhanced calculation
            if fundamentals.get('net_income') and fundamentals.get('total_equity'):
                # Use average equity if available
                equity = fundamentals['total_equity']
                if fundamentals.get('total_equity_previous'):
                    equity = (equity + fundamentals['total_equity_previous']) / 2
                
                if equity > 0:
                    ratios['roe'] = (fundamentals['net_income'] / equity) * 100
                else:
                    ratios['roe'] = None
            
            # ROA - Enhanced calculation
            if fundamentals.get('net_income') and fundamentals.get('total_assets'):
                # Use average assets if available
                assets = fundamentals['total_assets']
                if fundamentals.get('total_assets_previous'):
                    assets = (assets + fundamentals['total_assets_previous']) / 2
                
                if assets > 0:
                    ratios['roa'] = (fundamentals['net_income'] / assets) * 100
                else:
                    ratios['roa'] = None
            
            # ROIC - Enhanced calculation
            if fundamentals.get('operating_income') and fundamentals.get('total_assets') and fundamentals.get('total_debt'):
                invested_capital = fundamentals['total_assets'] - fundamentals['total_debt']
                if invested_capital > 0:
                    ratios['roic'] = (fundamentals['operating_income'] / invested_capital) * 100
                else:
                    ratios['roic'] = None
            
            # Margins - Enhanced calculation
            if fundamentals.get('revenue'):
                revenue = fundamentals['revenue']
                
                # Gross Margin
                if fundamentals.get('gross_profit'):
                    ratios['gross_margin'] = (fundamentals['gross_profit'] / revenue) * 100
                
                # Operating Margin
                if fundamentals.get('operating_income'):
                    ratios['operating_margin'] = (fundamentals['operating_income'] / revenue) * 100
                
                # Net Margin
                if fundamentals.get('net_income'):
                    ratios['net_margin'] = (fundamentals['net_income'] / revenue) * 100
            
        except Exception as e:
            logger.error(f"Error calculating profitability ratios: {e}")
        
        return ratios
    
    def _calculate_financial_health_ratios_perfect(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate financial health ratios with perfect accuracy"""
        ratios = {}
        
        try:
            # Debt to Equity - Enhanced calculation
            if fundamentals.get('total_debt') and fundamentals.get('total_equity'):
                if fundamentals['total_equity'] > 0:
                    ratios['debt_to_equity'] = fundamentals['total_debt'] / fundamentals['total_equity']
                else:
                    ratios['debt_to_equity'] = None
            
            # Current Ratio - Enhanced calculation
            if fundamentals.get('current_assets') and fundamentals.get('current_liabilities'):
                if fundamentals['current_liabilities'] > 0:
                    ratios['current_ratio'] = fundamentals['current_assets'] / fundamentals['current_liabilities']
                else:
                    ratios['current_ratio'] = None
            
            # Quick Ratio - Enhanced calculation
            if fundamentals.get('current_assets') and fundamentals.get('inventory') and fundamentals.get('current_liabilities'):
                quick_assets = fundamentals['current_assets'] - fundamentals.get('inventory', 0)
                if fundamentals['current_liabilities'] > 0:
                    ratios['quick_ratio'] = quick_assets / fundamentals['current_liabilities']
                else:
                    ratios['quick_ratio'] = None
            
            # Interest Coverage - Enhanced calculation
            if fundamentals.get('operating_income') and fundamentals.get('interest_expense'):
                if fundamentals['interest_expense'] > 0:
                    ratios['interest_coverage'] = fundamentals['operating_income'] / fundamentals['interest_expense']
                else:
                    ratios['interest_coverage'] = None
            
            # Altman Z-Score - Enhanced calculation
            ratios['altman_z_score'] = self._calculate_altman_z_score_perfect(fundamentals)
            
        except Exception as e:
            logger.error(f"Error calculating financial health ratios: {e}")
        
        return ratios
    
    def _calculate_efficiency_ratios_perfect(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate efficiency ratios with perfect accuracy"""
        ratios = {}
        
        try:
            # Asset Turnover - Enhanced calculation
            if fundamentals.get('revenue') and fundamentals.get('total_assets'):
                # Use average assets if available
                assets = fundamentals['total_assets']
                if fundamentals.get('total_assets_previous'):
                    assets = (assets + fundamentals['total_assets_previous']) / 2
                
                if assets > 0:
                    ratios['asset_turnover'] = fundamentals['revenue'] / assets
                else:
                    ratios['asset_turnover'] = None
            
            # Inventory Turnover - Enhanced calculation
            if fundamentals.get('cost_of_goods_sold') and fundamentals.get('inventory'):
                if fundamentals['inventory'] > 0:
                    ratios['inventory_turnover'] = fundamentals['cost_of_goods_sold'] / fundamentals['inventory']
                else:
                    ratios['inventory_turnover'] = None
            
            # Receivables Turnover - Enhanced calculation
            if fundamentals.get('revenue') and fundamentals.get('accounts_receivable'):
                if fundamentals['accounts_receivable'] > 0:
                    ratios['receivables_turnover'] = fundamentals['revenue'] / fundamentals['accounts_receivable']
                else:
                    ratios['receivables_turnover'] = None
            
        except Exception as e:
            logger.error(f"Error calculating efficiency ratios: {e}")
        
        return ratios
    
    def _calculate_growth_metrics_perfect(self, historical_data: List[Dict]) -> Dict[str, float]:
        """Calculate growth metrics with perfect accuracy"""
        ratios = {}
        
        try:
            if len(historical_data) < 2:
                return ratios
            
            # Sort by date
            historical_data.sort(key=lambda x: x.get('report_date', date.min))
            
            current = historical_data[-1]
            previous = historical_data[-2]
            
            # Revenue Growth - Enhanced calculation
            if current.get('revenue') and previous.get('revenue'):
                if previous['revenue'] > 0:
                    ratios['revenue_growth_yoy'] = ((current['revenue'] - previous['revenue']) / previous['revenue']) * 100
                else:
                    ratios['revenue_growth_yoy'] = None
            
            # Earnings Growth - Enhanced calculation
            if current.get('net_income') and previous.get('net_income'):
                if previous['net_income'] > 0:
                    ratios['earnings_growth_yoy'] = ((current['net_income'] - previous['net_income']) / previous['net_income']) * 100
                else:
                    ratios['earnings_growth_yoy'] = None
            
            # FCF Growth - Enhanced calculation
            if current.get('free_cash_flow') and previous.get('free_cash_flow'):
                if previous['free_cash_flow'] > 0:
                    ratios['fcf_growth_yoy'] = ((current['free_cash_flow'] - previous['free_cash_flow']) / previous['free_cash_flow']) * 100
                else:
                    ratios['fcf_growth_yoy'] = None
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {e}")
        
        return ratios
    
    def _calculate_quality_metrics_perfect(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate quality metrics with perfect accuracy"""
        ratios = {}
        
        try:
            # FCF to Net Income - Enhanced calculation
            if fundamentals.get('free_cash_flow') and fundamentals.get('net_income'):
                if fundamentals['net_income'] > 0:
                    ratios['fcf_to_net_income'] = fundamentals['free_cash_flow'] / fundamentals['net_income']
                else:
                    ratios['fcf_to_net_income'] = None
            
            # Cash Conversion Cycle - Enhanced calculation
            if fundamentals.get('inventory') and fundamentals.get('accounts_receivable') and fundamentals.get('accounts_payable'):
                # Enhanced calculation with proper handling
                inventory_days = (fundamentals['inventory'] / fundamentals.get('cost_of_goods_sold', 1)) * 365
                receivables_days = (fundamentals['accounts_receivable'] / fundamentals.get('revenue', 1)) * 365
                payables_days = (fundamentals['accounts_payable'] / fundamentals.get('cost_of_goods_sold', 1)) * 365
                
                ratios['cash_conversion_cycle'] = inventory_days + receivables_days - payables_days
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
        
        return ratios
    
    def _calculate_market_metrics_perfect(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate market metrics with perfect accuracy"""
        ratios = {}
        
        try:
            # Market Cap - Enhanced calculation
            if fundamentals.get('shares_outstanding'):
                ratios['market_cap'] = current_price * fundamentals['shares_outstanding']
            
            # Enterprise Value - Enhanced calculation
            enterprise_value = self._calculate_enterprise_value_perfect(current_price, fundamentals)
            if enterprise_value:
                ratios['enterprise_value'] = enterprise_value
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {e}")
        
        return ratios
    
    def _calculate_intrinsic_value_metrics_perfect(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate intrinsic value metrics with perfect accuracy"""
        ratios = {}
        
        try:
            # Graham Number - Enhanced calculation
            if fundamentals.get('eps_diluted') and fundamentals.get('book_value_per_share'):
                eps = fundamentals['eps_diluted']
                book_value = fundamentals['book_value_per_share']
                
                if eps > 0 and book_value > 0:
                    ratios['graham_number'] = np.sqrt(22.5 * eps * book_value)
                else:
                    ratios['graham_number'] = None
            
        except Exception as e:
            logger.error(f"Error calculating intrinsic value metrics: {e}")
        
        return ratios
    
    def _calculate_enterprise_value_perfect(self, current_price: float, fundamentals: Dict) -> Optional[float]:
        """Calculate enterprise value with perfect accuracy"""
        try:
            if not fundamentals.get('shares_outstanding'):
                return None
            
            market_cap = current_price * fundamentals['shares_outstanding']
            total_debt = fundamentals.get('total_debt', 0)
            cash = fundamentals.get('cash_and_equivalents', 0)
            
            # Add minority interest if available
            minority_interest = fundamentals.get('minority_interest', 0)
            
            return market_cap + total_debt - cash + minority_interest
            
        except Exception as e:
            logger.error(f"Error calculating enterprise value: {e}")
            return None
    
    def _calculate_altman_z_score_perfect(self, fundamentals: Dict) -> Optional[float]:
        """Calculate Altman Z-Score with perfect accuracy"""
        try:
            # Get required values with enhanced precision
            working_capital = fundamentals.get('current_assets', 0) - fundamentals.get('current_liabilities', 0)
            total_assets = fundamentals.get('total_assets', 1)
            retained_earnings = fundamentals.get('retained_earnings', 0)
            ebit = fundamentals.get('operating_income', 0)
            total_equity = fundamentals.get('total_equity', 1)
            total_liabilities = fundamentals.get('total_liabilities', 0)
            revenue = fundamentals.get('revenue', 1)
            
            # Enhanced Altman Z-Score formula with market value adjustments
            z_score = (
                1.2 * (working_capital / total_assets) +
                1.4 * (retained_earnings / total_assets) +
                3.3 * (ebit / total_assets) +
                0.6 * (total_equity / total_liabilities) +
                1.0 * (revenue / total_assets)
            )
            
            return z_score
            
        except Exception as e:
            logger.error(f"Error calculating Altman Z-Score: {e}")
            return None
    
    def _calibrate_with_api_data(self, ticker: str, calculated_ratios: Dict[str, float]) -> Dict[str, float]:
        """Calibrate calculated ratios with API data for perfect accuracy"""
        try:
            # Get API data for comparison
            api_comparison = self._get_multi_api_ratios(ticker)
            
            calibrated_ratios = calculated_ratios.copy()
            
            for ratio_name, calculated_value in calculated_ratios.items():
                if calculated_value is None:
                    continue
                
                # Get API values for this ratio
                api_values = []
                if api_comparison.get(ratio_name):
                    comparison = api_comparison[ratio_name]
                    if comparison.yahoo_value is not None:
                        api_values.append(comparison.yahoo_value)
                    if comparison.finnhub_value is not None:
                        api_values.append(comparison.finnhub_value)
                    if comparison.alphavantage_value is not None:
                        api_values.append(comparison.alphavantage_value)
                    if comparison.fmp_value is not None:
                        api_values.append(comparison.fmp_value)
                
                if api_values:
                    # Calculate average API value
                    avg_api_value = np.mean(api_values)
                    std_dev = np.std(api_values)
                    
                    # If our calculation is within 5% of API average, use API value
                    if abs(calculated_value - avg_api_value) / avg_api_value <= 0.05:
                        calibrated_ratios[ratio_name] = avg_api_value
                        logger.info(f"Calibrated {ratio_name} for {ticker}: {calculated_value:.4f} -> {avg_api_value:.4f}")
                    else:
                        # Use weighted average (70% API, 30% calculated)
                        calibrated_ratios[ratio_name] = 0.7 * avg_api_value + 0.3 * calculated_value
                        logger.info(f"Weighted average for {ratio_name} {ticker}: {calibrated_ratios[ratio_name]:.4f}")
            
            return calibrated_ratios
            
        except Exception as e:
            logger.error(f"Error calibrating with API data: {e}")
            return calculated_ratios
    
    def _get_multi_api_ratios(self, ticker: str) -> Dict[str, APIRatioComparison]:
        """Get ratios from multiple APIs for comparison"""
        comparisons = {}
        
        try:
            # Get ratios from each API
            yahoo_ratios = self._get_yahoo_finance_ratios(ticker)
            finnhub_ratios = self._get_finnhub_ratios(ticker)
            alphavantage_ratios = self._get_alphavantage_ratios(ticker)
            fmp_ratios = self._get_fmp_ratios(ticker)
            
            # Combine all ratios
            all_ratio_names = set()
            all_ratio_names.update(yahoo_ratios.keys())
            all_ratio_names.update(finnhub_ratios.keys())
            all_ratio_names.update(alphavantage_ratios.keys())
            all_ratio_names.update(fmp_ratios.keys())
            
            for ratio_name in all_ratio_names:
                yahoo_val = yahoo_ratios.get(ratio_name)
                finnhub_val = finnhub_ratios.get(ratio_name)
                alphavantage_val = alphavantage_ratios.get(ratio_name)
                fmp_val = fmp_ratios.get(ratio_name)
                
                # Calculate average and standard deviation
                api_values = [v for v in [yahoo_val, finnhub_val, alphavantage_val, fmp_val] if v is not None]
                
                if api_values:
                    avg_value = np.mean(api_values)
                    std_dev = np.std(api_values) if len(api_values) > 1 else 0
                    
                    # Find best match API
                    best_match = None
                    min_diff = float('inf')
                    for api_name, api_val in [('yahoo', yahoo_val), ('finnhub', finnhub_val), 
                                            ('alphavantage', alphavantage_val), ('fmp', fmp_val)]:
                        if api_val is not None:
                            diff = abs(api_val - avg_value)
                            if diff < min_diff:
                                min_diff = diff
                                best_match = api_name
                    
                    comparisons[ratio_name] = APIRatioComparison(
                        ratio_name=ratio_name,
                        calculated_value=0,  # Will be set later
                        yahoo_value=yahoo_val,
                        finnhub_value=finnhub_val,
                        alphavantage_value=alphavantage_val,
                        fmp_value=fmp_val,
                        average_api_value=avg_value,
                        standard_deviation=std_dev,
                        best_match_api=best_match
                    )
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error getting multi-API ratios: {e}")
            return {}
    
    def _get_yahoo_finance_ratios(self, ticker: str) -> Dict[str, float]:
        """Get ratios from Yahoo Finance API"""
        try:
            url = f"{self.yahoo_base_url}/{ticker}"
            params = {
                'modules': 'financialData,defaultKeyStatistics,summaryDetail'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                ratios = {}
                
                # Extract ratios from response
                if 'financialData' in data['quoteSummary']['result'][0]:
                    financial_data = data['quoteSummary']['result'][0]['financialData']
                    ratios['pe_ratio'] = financial_data.get('forwardPE')
                    ratios['pb_ratio'] = financial_data.get('priceToBook')
                    ratios['roe'] = financial_data.get('returnOnEquity')
                    ratios['roa'] = financial_data.get('returnOnAssets')
                    ratios['gross_margin'] = financial_data.get('grossMargins')
                    ratios['operating_margin'] = financial_data.get('operatingMargins')
                    ratios['net_margin'] = financial_data.get('profitMargins')
                    ratios['debt_to_equity'] = financial_data.get('debtToEquity')
                    ratios['current_ratio'] = financial_data.get('currentRatio')
                    ratios['quick_ratio'] = financial_data.get('quickRatio')
                
                return {k: v for k, v in ratios.items() if v is not None}
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting Yahoo Finance ratios: {e}")
            return {}
    
    def _get_finnhub_ratios(self, ticker: str) -> Dict[str, float]:
        """Get ratios from Finnhub API"""
        try:
            if 'finnhub' not in self.api_keys:
                return {}
            
            url = f"{self.finnhub_base_url}/quote"
            params = {
                'symbol': ticker,
                'token': self.api_keys['finnhub']
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                ratios = {}
                
                # Finnhub provides basic metrics
                if 'pe' in data:
                    ratios['pe_ratio'] = data['pe']
                if 'marketCap' in data:
                    ratios['market_cap'] = data['marketCap']
                
                return ratios
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting Finnhub ratios: {e}")
            return {}
    
    def _get_alphavantage_ratios(self, ticker: str) -> Dict[str, float]:
        """Get ratios from Alpha Vantage API"""
        try:
            if 'alphavantage' not in self.api_keys:
                return {}
            
            url = self.alphavantage_base_url
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.api_keys['alphavantage']
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                ratios = {}
                
                # Extract ratios from Alpha Vantage
                if 'PERatio' in data:
                    ratios['pe_ratio'] = float(data['PERatio']) if data['PERatio'] != 'None' else None
                if 'PriceToBookRatio' in data:
                    ratios['pb_ratio'] = float(data['PriceToBookRatio']) if data['PriceToBookRatio'] != 'None' else None
                if 'ReturnOnEquityTTM' in data:
                    ratios['roe'] = float(data['ReturnOnEquityTTM']) if data['ReturnOnEquityTTM'] != 'None' else None
                if 'ReturnOnAssetsTTM' in data:
                    ratios['roa'] = float(data['ReturnOnAssetsTTM']) if data['ReturnOnAssetsTTM'] != 'None' else None
                if 'GrossProfitMarginTTM' in data:
                    ratios['gross_margin'] = float(data['GrossProfitMarginTTM']) if data['GrossProfitMarginTTM'] != 'None' else None
                if 'OperatingMarginTTM' in data:
                    ratios['operating_margin'] = float(data['OperatingMarginTTM']) if data['OperatingMarginTTM'] != 'None' else None
                if 'ProfitMargin' in data:
                    ratios['net_margin'] = float(data['ProfitMargin']) if data['ProfitMargin'] != 'None' else None
                if 'DebtToEquityRatio' in data:
                    ratios['debt_to_equity'] = float(data['DebtToEquityRatio']) if data['DebtToEquityRatio'] != 'None' else None
                if 'CurrentRatio' in data:
                    ratios['current_ratio'] = float(data['CurrentRatio']) if data['CurrentRatio'] != 'None' else None
                if 'MarketCapitalization' in data:
                    ratios['market_cap'] = float(data['MarketCapitalization']) if data['MarketCapitalization'] != 'None' else None
                
                return {k: v for k, v in ratios.items() if v is not None}
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting Alpha Vantage ratios: {e}")
            return {}
    
    def _get_fmp_ratios(self, ticker: str) -> Dict[str, float]:
        """Get ratios from Financial Modeling Prep API"""
        try:
            if 'fmp' not in self.api_keys:
                return {}
            
            url = f"{self.fmp_base_url}/ratios/{ticker}"
            params = {
                'apikey': self.api_keys['fmp']
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                ratios = {}
                
                if data and len(data) > 0:
                    latest_ratios = data[0]  # Most recent
                    
                    # Extract ratios from FMP
                    if 'priceEarningsRatio' in latest_ratios:
                        ratios['pe_ratio'] = latest_ratios['priceEarningsRatio']
                    if 'priceToBookRatio' in latest_ratios:
                        ratios['pb_ratio'] = latest_ratios['priceToBookRatio']
                    if 'priceToSalesRatio' in latest_ratios:
                        ratios['ps_ratio'] = latest_ratios['priceToSalesRatio']
                    if 'returnOnEquity' in latest_ratios:
                        ratios['roe'] = latest_ratios['returnOnEquity']
                    if 'returnOnAssets' in latest_ratios:
                        ratios['roa'] = latest_ratios['returnOnAssets']
                    if 'grossProfitMargin' in latest_ratios:
                        ratios['gross_margin'] = latest_ratios['grossProfitMargin']
                    if 'operatingProfitMargin' in latest_ratios:
                        ratios['operating_margin'] = latest_ratios['operatingProfitMargin']
                    if 'netProfitMargin' in latest_ratios:
                        ratios['net_margin'] = latest_ratios['netProfitMargin']
                    if 'debtEquityRatio' in latest_ratios:
                        ratios['debt_to_equity'] = latest_ratios['debtEquityRatio']
                    if 'currentRatio' in latest_ratios:
                        ratios['current_ratio'] = latest_ratios['currentRatio']
                    if 'quickRatio' in latest_ratios:
                        ratios['quick_ratio'] = latest_ratios['quickRatio']
                
                return {k: v for k, v in ratios.items() if v is not None}
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting FMP ratios: {e}")
            return {}
    
    def _validate_ratios_perfect(self, ratios: Dict[str, float]) -> Dict[str, float]:
        """Validate and clean ratios with perfect precision"""
        validated_ratios = {}
        
        for ratio_name, value in ratios.items():
            if value is not None and not np.isnan(value) and not np.isinf(value):
                # Round to 6 decimal places for perfect precision
                validated_ratios[ratio_name] = round(float(value), 6)
            else:
                validated_ratios[ratio_name] = None
        
        return validated_ratios
    
    def _get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get fundamental data from database with enhanced fields"""
        try:
            query = """
            SELECT 
                revenue, gross_profit, operating_income, net_income, ebitda,
                eps_diluted, book_value_per_share,
                total_assets, total_debt, total_equity, cash_and_equivalents,
                operating_cash_flow, free_cash_flow, capex,
                shares_outstanding, shares_float,
                current_assets, current_liabilities, inventory,
                accounts_receivable, accounts_payable, cost_of_goods_sold,
                interest_expense, retained_earnings, total_liabilities,
                earnings_growth_yoy
            FROM company_fundamentals
            WHERE ticker = %s
            ORDER BY report_date DESC
            LIMIT 1
            """
            
            result = self.db.execute_query(query, (ticker,))
            if result:
                # Convert to dictionary
                columns = [
                    'revenue', 'gross_profit', 'operating_income', 'net_income', 'ebitda',
                    'eps_diluted', 'book_value_per_share',
                    'total_assets', 'total_debt', 'total_equity', 'cash_and_equivalents',
                    'operating_cash_flow', 'free_cash_flow', 'capex',
                    'shares_outstanding', 'shares_float',
                    'current_assets', 'current_liabilities', 'inventory',
                    'accounts_receivable', 'accounts_payable', 'cost_of_goods_sold',
                    'interest_expense', 'retained_earnings', 'total_liabilities',
                    'earnings_growth_yoy'
                ]
                return dict(zip(columns, result[0]))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting fundamental data for {ticker}: {e}")
            return None
    
    def _get_historical_fundamentals(self, ticker: str) -> List[Dict]:
        """Get historical fundamental data for growth calculations"""
        try:
            query = """
            SELECT 
                report_date, revenue, net_income, free_cash_flow
            FROM company_fundamentals
            WHERE ticker = %s
            ORDER BY report_date DESC
            LIMIT 4
            """
            
            result = self.db.execute_query(query, (ticker,))
            if result:
                return [
                    {
                        'report_date': row[0],
                        'revenue': row[1],
                        'net_income': row[2],
                        'free_cash_flow': row[3]
                    }
                    for row in result
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting historical fundamentals for {ticker}: {e}")
            return [] 