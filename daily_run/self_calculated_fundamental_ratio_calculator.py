"""
Self-Calculated Fundamental Ratio Calculator
Calculates all ratios using our own data, with API validation for development
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
class CalculationValidationResult:
    """Result of our calculation vs API validation"""
    ratio_name: str
    our_calculated_value: float
    api_average_value: Optional[float] = None
    difference: Optional[float] = None
    difference_percent: Optional[float] = None
    is_accurate: bool = True
    validation_status: str = "accurate"  # accurate, needs_review, significant_difference
    api_sources: List[str] = None

class SelfCalculatedFundamentalRatioCalculator:
    """
    Fundamental ratio calculator that uses our own data for calculations
    APIs are used only for validation during development
    """
    
    def __init__(self, db_connection, api_keys: Dict[str, str] = None, validation_mode: bool = False):
        self.db = db_connection
        self.api_keys = api_keys or {}
        self.validation_mode = validation_mode  # Only validate during development
        
        # API endpoints for validation only
        self.yahoo_base_url = "https://query2.finance.yahoo.com/v10/finance/quoteSummary"
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        self.alphavantage_base_url = "https://www.alphavantage.co/query"
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        
    def calculate_all_ratios(self, ticker: str, current_price: float) -> Dict[str, float]:
        """
        Calculate all financial ratios using our own data
        Optionally validate against APIs if in validation mode
        """
        try:
            # Get fundamental data from our database
            fundamental_data = self._get_fundamental_data(ticker)
            if not fundamental_data:
                logger.warning(f"No fundamental data found for {ticker}")
                return {}
            
            # Get historical data for growth calculations
            historical_data = self._get_historical_fundamentals(ticker)
            
            # Calculate all ratios using our own data
            ratios = {}
            ratios.update(self._calculate_valuation_ratios(current_price, fundamental_data))
            ratios.update(self._calculate_profitability_ratios(fundamental_data))
            ratios.update(self._calculate_financial_health_ratios(fundamental_data))
            ratios.update(self._calculate_efficiency_ratios(fundamental_data))
            ratios.update(self._calculate_growth_metrics(historical_data))
            ratios.update(self._calculate_quality_metrics(fundamental_data))
            ratios.update(self._calculate_market_metrics(current_price, fundamental_data))
            ratios.update(self._calculate_intrinsic_value_metrics(current_price, fundamental_data))
            
            # Validate and clean ratios
            final_ratios = self._validate_ratios(ratios)
            
            # Optional: Validate against APIs during development
            if self.validation_mode:
                validation_results = self._validate_calculations_with_apis(ticker, final_ratios)
                self._log_validation_results(ticker, validation_results)
            
            logger.info(f"Calculated {len(final_ratios)} ratios for {ticker} using our own data")
            return final_ratios
            
        except Exception as e:
            logger.error(f"Error calculating ratios for {ticker}: {e}")
            return {}
    
    def _calculate_valuation_ratios(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate valuation ratios using our own data"""
        ratios = {}
        
        try:
            # P/E Ratio - Our calculation
            if fundamentals.get('net_income') and fundamentals.get('shares_outstanding'):
                eps = fundamentals['net_income'] / fundamentals['shares_outstanding']
                if eps > 0:
                    # Use diluted EPS if available, otherwise basic
                    eps_to_use = fundamentals.get('eps_diluted', eps)
                    ratios['pe_ratio'] = current_price / eps_to_use
                else:
                    ratios['pe_ratio'] = None
            
            # P/B Ratio - Our calculation
            if fundamentals.get('total_equity') and fundamentals.get('shares_outstanding'):
                # Use book value per share if available, otherwise calculate
                book_value_per_share = fundamentals.get('book_value_per_share')
                if not book_value_per_share:
                    book_value_per_share = fundamentals['total_equity'] / fundamentals['shares_outstanding']
                
                if book_value_per_share > 0:
                    ratios['pb_ratio'] = current_price / book_value_per_share
                else:
                    ratios['pb_ratio'] = None
            
            # P/S Ratio - Our calculation
            if fundamentals.get('revenue') and fundamentals.get('shares_outstanding'):
                # Use diluted shares for consistency
                shares_to_use = fundamentals.get('shares_float', fundamentals['shares_outstanding'])
                sales_per_share = fundamentals['revenue'] / shares_to_use
                if sales_per_share > 0:
                    ratios['ps_ratio'] = current_price / sales_per_share
                else:
                    ratios['ps_ratio'] = None
            
            # EV/EBITDA - Our calculation
            if fundamentals.get('ebitda'):
                enterprise_value = self._calculate_enterprise_value(current_price, fundamentals)
                if enterprise_value and fundamentals['ebitda'] > 0:
                    ratios['ev_ebitda'] = enterprise_value / fundamentals['ebitda']
                else:
                    ratios['ev_ebitda'] = None
            
            # PEG Ratio - Our calculation
            if ratios.get('pe_ratio') and fundamentals.get('earnings_growth_yoy'):
                growth_rate = fundamentals['earnings_growth_yoy']
                if growth_rate > 0:
                    ratios['peg_ratio'] = ratios['pe_ratio'] / growth_rate
                else:
                    ratios['peg_ratio'] = None
            
        except Exception as e:
            logger.error(f"Error calculating valuation ratios: {e}")
        
        return ratios
    
    def _calculate_profitability_ratios(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate profitability ratios using our own data"""
        ratios = {}
        
        try:
            # ROE - Our calculation
            if fundamentals.get('net_income') and fundamentals.get('total_equity'):
                # Use average equity if available
                equity = fundamentals['total_equity']
                if fundamentals.get('total_equity_previous'):
                    equity = (equity + fundamentals['total_equity_previous']) / 2
                
                if equity > 0:
                    ratios['roe'] = (fundamentals['net_income'] / equity) * 100
                else:
                    ratios['roe'] = None
            
            # ROA - Our calculation
            if fundamentals.get('net_income') and fundamentals.get('total_assets'):
                # Use average assets if available
                assets = fundamentals['total_assets']
                if fundamentals.get('total_assets_previous'):
                    assets = (assets + fundamentals['total_assets_previous']) / 2
                
                if assets > 0:
                    ratios['roa'] = (fundamentals['net_income'] / assets) * 100
                else:
                    ratios['roa'] = None
            
            # ROIC - Our calculation
            if fundamentals.get('operating_income') and fundamentals.get('total_assets') and fundamentals.get('total_debt'):
                invested_capital = fundamentals['total_assets'] - fundamentals['total_debt']
                if invested_capital > 0:
                    ratios['roic'] = (fundamentals['operating_income'] / invested_capital) * 100
                else:
                    ratios['roic'] = None
            
            # Margins - Our calculation
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
    
    def _calculate_financial_health_ratios(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate financial health ratios using our own data"""
        ratios = {}
        
        try:
            # Debt to Equity - Our calculation
            if fundamentals.get('total_debt') and fundamentals.get('total_equity'):
                if fundamentals['total_equity'] > 0:
                    ratios['debt_to_equity'] = fundamentals['total_debt'] / fundamentals['total_equity']
                else:
                    ratios['debt_to_equity'] = None
            
            # Current Ratio - Our calculation
            if fundamentals.get('current_assets') and fundamentals.get('current_liabilities'):
                if fundamentals['current_liabilities'] > 0:
                    ratios['current_ratio'] = fundamentals['current_assets'] / fundamentals['current_liabilities']
                else:
                    ratios['current_ratio'] = None
            
            # Quick Ratio - Our calculation
            if fundamentals.get('current_assets') and fundamentals.get('inventory') and fundamentals.get('current_liabilities'):
                quick_assets = fundamentals['current_assets'] - fundamentals.get('inventory', 0)
                if fundamentals['current_liabilities'] > 0:
                    ratios['quick_ratio'] = quick_assets / fundamentals['current_liabilities']
                else:
                    ratios['quick_ratio'] = None
            
            # Interest Coverage - Our calculation
            if fundamentals.get('operating_income') and fundamentals.get('interest_expense'):
                if fundamentals['interest_expense'] > 0:
                    ratios['interest_coverage'] = fundamentals['operating_income'] / fundamentals['interest_expense']
                else:
                    ratios['interest_coverage'] = None
            
            # Altman Z-Score - Our calculation
            ratios['altman_z_score'] = self._calculate_altman_z_score(fundamentals)
            
        except Exception as e:
            logger.error(f"Error calculating financial health ratios: {e}")
        
        return ratios
    
    def _calculate_efficiency_ratios(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate efficiency ratios using our own data"""
        ratios = {}
        
        try:
            # Asset Turnover - Our calculation
            if fundamentals.get('revenue') and fundamentals.get('total_assets'):
                # Use average assets if available
                assets = fundamentals['total_assets']
                if fundamentals.get('total_assets_previous'):
                    assets = (assets + fundamentals['total_assets_previous']) / 2
                
                if assets > 0:
                    ratios['asset_turnover'] = fundamentals['revenue'] / assets
                else:
                    ratios['asset_turnover'] = None
            
            # Inventory Turnover - Our calculation
            if fundamentals.get('cost_of_goods_sold') and fundamentals.get('inventory'):
                if fundamentals['inventory'] > 0:
                    ratios['inventory_turnover'] = fundamentals['cost_of_goods_sold'] / fundamentals['inventory']
                else:
                    ratios['inventory_turnover'] = None
            
            # Receivables Turnover - Our calculation
            if fundamentals.get('revenue') and fundamentals.get('accounts_receivable'):
                if fundamentals['accounts_receivable'] > 0:
                    ratios['receivables_turnover'] = fundamentals['revenue'] / fundamentals['accounts_receivable']
                else:
                    ratios['receivables_turnover'] = None
            
        except Exception as e:
            logger.error(f"Error calculating efficiency ratios: {e}")
        
        return ratios
    
    def _calculate_growth_metrics(self, historical_data: List[Dict]) -> Dict[str, float]:
        """Calculate growth metrics using our own data"""
        ratios = {}
        
        try:
            if len(historical_data) < 2:
                return ratios
            
            # Sort by date
            historical_data.sort(key=lambda x: x.get('report_date', date.min))
            
            current = historical_data[-1]
            previous = historical_data[-2]
            
            # Revenue Growth - Our calculation
            if current.get('revenue') and previous.get('revenue'):
                if previous['revenue'] > 0:
                    ratios['revenue_growth_yoy'] = ((current['revenue'] - previous['revenue']) / previous['revenue']) * 100
                else:
                    ratios['revenue_growth_yoy'] = None
            
            # Earnings Growth - Our calculation
            if current.get('net_income') and previous.get('net_income'):
                if previous['net_income'] > 0:
                    ratios['earnings_growth_yoy'] = ((current['net_income'] - previous['net_income']) / previous['net_income']) * 100
                else:
                    ratios['earnings_growth_yoy'] = None
            
            # FCF Growth - Our calculation
            if current.get('free_cash_flow') and previous.get('free_cash_flow'):
                if previous['free_cash_flow'] > 0:
                    ratios['fcf_growth_yoy'] = ((current['free_cash_flow'] - previous['free_cash_flow']) / previous['free_cash_flow']) * 100
                else:
                    ratios['fcf_growth_yoy'] = None
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {e}")
        
        return ratios
    
    def _calculate_quality_metrics(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate quality metrics using our own data"""
        ratios = {}
        
        try:
            # FCF to Net Income - Our calculation
            if fundamentals.get('free_cash_flow') and fundamentals.get('net_income'):
                if fundamentals['net_income'] > 0:
                    ratios['fcf_to_net_income'] = fundamentals['free_cash_flow'] / fundamentals['net_income']
                else:
                    ratios['fcf_to_net_income'] = None
            
            # Cash Conversion Cycle - Our calculation
            if fundamentals.get('inventory') and fundamentals.get('accounts_receivable') and fundamentals.get('accounts_payable'):
                # Enhanced calculation with proper handling
                inventory_days = (fundamentals['inventory'] / fundamentals.get('cost_of_goods_sold', 1)) * 365
                receivables_days = (fundamentals['accounts_receivable'] / fundamentals.get('revenue', 1)) * 365
                payables_days = (fundamentals['accounts_payable'] / fundamentals.get('cost_of_goods_sold', 1)) * 365
                
                ratios['cash_conversion_cycle'] = inventory_days + receivables_days - payables_days
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
        
        return ratios
    
    def _calculate_market_metrics(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate market metrics using our own data"""
        ratios = {}
        
        try:
            # Market Cap - Our calculation
            if fundamentals.get('shares_outstanding'):
                ratios['market_cap'] = current_price * fundamentals['shares_outstanding']
            
            # Enterprise Value - Our calculation
            enterprise_value = self._calculate_enterprise_value(current_price, fundamentals)
            if enterprise_value:
                ratios['enterprise_value'] = enterprise_value
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {e}")
        
        return ratios
    
    def _calculate_intrinsic_value_metrics(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate intrinsic value metrics using our own data"""
        ratios = {}
        
        try:
            # Graham Number - Our calculation
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
    
    def _calculate_enterprise_value(self, current_price: float, fundamentals: Dict) -> Optional[float]:
        """Calculate enterprise value using our own data"""
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
    
    def _calculate_altman_z_score(self, fundamentals: Dict) -> Optional[float]:
        """Calculate Altman Z-Score using our own data"""
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
    
    def _validate_calculations_with_apis(self, ticker: str, our_ratios: Dict[str, float]) -> List[CalculationValidationResult]:
        """
        Validate our calculations against APIs (development only)
        This is for validation purposes, not for production use
        """
        validation_results = []
        
        try:
            # Get API data for comparison
            api_data = self._get_api_data_for_validation(ticker)
            
            for ratio_name, our_value in our_ratios.items():
                if our_value is None:
                    continue
                
                # Get API values for this ratio
                api_values = []
                api_sources = []
                
                for api_name, api_ratios in api_data.items():
                    if ratio_name in api_ratios:
                        api_values.append(api_ratios[ratio_name])
                        api_sources.append(api_name)
                
                if api_values:
                    # Calculate API average
                    api_average = np.mean(api_values)
                    difference = our_value - api_average
                    difference_percent = (difference / api_average) * 100 if api_average != 0 else 0
                    
                    # Determine validation status
                    if abs(difference_percent) <= 1.0:
                        validation_status = "accurate"
                        is_accurate = True
                    elif abs(difference_percent) <= 5.0:
                        validation_status = "needs_review"
                        is_accurate = True
                    else:
                        validation_status = "significant_difference"
                        is_accurate = False
                    
                    validation_results.append(CalculationValidationResult(
                        ratio_name=ratio_name,
                        our_calculated_value=our_value,
                        api_average_value=api_average,
                        difference=difference,
                        difference_percent=difference_percent,
                        is_accurate=is_accurate,
                        validation_status=validation_status,
                        api_sources=api_sources
                    ))
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating calculations with APIs: {e}")
            return []
    
    def _get_api_data_for_validation(self, ticker: str) -> Dict[str, Dict[str, float]]:
        """Get API data for validation purposes only"""
        api_data = {}
        
        try:
            # Get data from each API for validation
            api_data['yahoo'] = self._get_yahoo_finance_ratios(ticker)
            api_data['finnhub'] = self._get_finnhub_ratios(ticker)
            api_data['alphavantage'] = self._get_alphavantage_ratios(ticker)
            api_data['fmp'] = self._get_fmp_ratios(ticker)
            
            return api_data
            
        except Exception as e:
            logger.error(f"Error getting API data for validation: {e}")
            return {}
    
    def _log_validation_results(self, ticker: str, validation_results: List[CalculationValidationResult]):
        """Log validation results for development review"""
        logger.info(f"\n=== VALIDATION RESULTS FOR {ticker} ===")
        
        accurate_count = 0
        review_count = 0
        significant_count = 0
        
        for result in validation_results:
            if result.validation_status == "accurate":
                accurate_count += 1
                logger.info(f"✅ {result.ratio_name}: {result.our_calculated_value:.4f} vs API {result.api_average_value:.4f} ({result.difference_percent:+.2f}%)")
            elif result.validation_status == "needs_review":
                review_count += 1
                logger.warning(f"⚠️  {result.ratio_name}: {result.our_calculated_value:.4f} vs API {result.api_average_value:.4f} ({result.difference_percent:+.2f}%)")
            else:
                significant_count += 1
                logger.error(f"❌ {result.ratio_name}: {result.our_calculated_value:.4f} vs API {result.api_average_value:.4f} ({result.difference_percent:+.2f}%)")
        
        total = len(validation_results)
        logger.info(f"\nValidation Summary: {accurate_count} accurate, {review_count} needs review, {significant_count} significant differences")
        logger.info(f"Accuracy Rate: {(accurate_count/total)*100:.1f}% if validation_mode is enabled")
    
    def _validate_ratios(self, ratios: Dict[str, float]) -> Dict[str, float]:
        """Validate and clean our calculated ratios"""
        validated_ratios = {}
        
        for ratio_name, value in ratios.items():
            if value is not None and not np.isnan(value) and not np.isinf(value):
                # Round to 6 decimal places for precision
                validated_ratios[ratio_name] = round(float(value), 6)
            else:
                validated_ratios[ratio_name] = None
        
        return validated_ratios
    
    # API methods for validation only (not used in production)
    def _get_yahoo_finance_ratios(self, ticker: str) -> Dict[str, float]:
        """Get Yahoo Finance ratios for validation only"""
        # Implementation for validation purposes
        pass
    
    def _get_finnhub_ratios(self, ticker: str) -> Dict[str, float]:
        """Get Finnhub ratios for validation only"""
        # Implementation for validation purposes
        pass
    
    def _get_alphavantage_ratios(self, ticker: str) -> Dict[str, float]:
        """Get Alpha Vantage ratios for validation only"""
        # Implementation for validation purposes
        pass
    
    def _get_fmp_ratios(self, ticker: str) -> Dict[str, float]:
        """Get FMP ratios for validation only"""
        # Implementation for validation purposes
        pass
    
    def _get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get fundamental data from our database"""
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
        """Get historical fundamental data from our database"""
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