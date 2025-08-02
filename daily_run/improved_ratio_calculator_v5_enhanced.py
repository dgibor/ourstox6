"""
Enhanced Ratio Calculator V5 - With improved error handling and partial results
"""

import logging
import math
from typing import Dict, Optional, List, Tuple
from data_validator import FundamentalDataValidator

logger = logging.getLogger(__name__)

class EnhancedRatioCalculatorV5:
    """Enhanced ratio calculator with improved error handling and partial results"""
    
    def __init__(self):
        self.validator = FundamentalDataValidator()
        
    def calculate_all_ratios(self, ticker: str, fundamental_data: Dict, current_price: float, historical_data: Dict = None) -> Dict[str, float]:
        """Calculate all 27 ratios with enhanced error handling and partial results"""
        
        # Validate inputs
        validated_fundamental = self.validator.validate_fundamental_data(fundamental_data)
        validated_historical = self.validator.validate_historical_data(historical_data or {})
        
        if not validated_fundamental:
            logger.error(f"Invalid fundamental data for {ticker}")
            return {}
            
        # Calculate ratios with individual error handling
        all_ratios = {}
        calculation_errors = []
        
        # Define calculation methods with their dependencies
        calculation_methods = [
            ('valuation', self._calculate_valuation_ratios, ['eps_diluted', 'book_value_per_share', 'revenue', 'shares_outstanding']),
            ('profitability', self._calculate_profitability_ratios, ['net_income', 'total_equity', 'total_assets', 'revenue', 'cost_of_goods_sold', 'operating_income']),
            ('financial_health', self._calculate_financial_health_ratios, ['total_debt', 'total_equity', 'current_assets', 'current_liabilities', 'inventory']),
            ('efficiency', self._calculate_efficiency_ratios, ['revenue', 'total_assets', 'inventory', 'cost_of_goods_sold', 'accounts_receivable']),
            ('growth', self._calculate_growth_metrics, ['revenue']),
            ('quality', self._calculate_quality_metrics, ['free_cash_flow', 'net_income']),
            ('market', self._calculate_market_data, ['shares_outstanding']),
            ('intrinsic', self._calculate_intrinsic_value, ['eps_diluted', 'book_value_per_share'])
        ]
        
        for category, method, dependencies in calculation_methods:
            try:
                # Check if we have minimum required data
                if self._has_minimum_data(validated_fundamental, dependencies):
                    # Call method with correct parameters based on signature
                    if category == 'profitability':
                        ratios = method(ticker, validated_fundamental)
                    elif category == 'quality':
                        ratios = method(ticker, validated_fundamental)
                    elif category in ['efficiency', 'growth']:
                        ratios = method(ticker, validated_fundamental, validated_historical)
                    else:
                        ratios = method(ticker, validated_fundamental, current_price)
                    
                    if ratios:
                        all_ratios.update(ratios)
                        logger.debug(f"{ticker}: Calculated {len(ratios)} {category} ratios")
                    else:
                        logger.warning(f"{ticker}: No {category} ratios calculated")
                else:
                    missing_fields = [dep for dep in dependencies if not validated_fundamental.get(dep)]
                    logger.warning(f"{ticker}: Missing data for {category} ratios: {missing_fields}")
                    
            except Exception as e:
                error_msg = f"Error calculating {category} ratios for {ticker}: {e}"
                logger.error(error_msg)
                calculation_errors.append(error_msg)
                # Continue with other calculations
        
        # Validate final ratios
        validated_ratios = self.validator.validate_ratios(all_ratios)
        
        # Log summary
        if calculation_errors:
            logger.warning(f"{ticker}: {len(calculation_errors)} calculation errors, {len(validated_ratios)} ratios calculated")
        else:
            logger.info(f"{ticker}: Successfully calculated {len(validated_ratios)} ratios")
            
        return validated_ratios
    
    def _has_minimum_data(self, fundamental_data: Dict, required_fields: List[str]) -> bool:
        """Check if we have minimum required data for calculations"""
        return all(fundamental_data.get(field) is not None for field in required_fields)
    
    def _safe_division(self, numerator: float, denominator: float, ratio_name: str) -> Optional[float]:
        """Safely perform division with error handling"""
        if denominator is None or denominator == 0:
            logger.warning(f"{ratio_name}: Division by zero or None denominator")
            return None
            
        if numerator is None:
            logger.warning(f"{ratio_name}: None numerator")
            return None
            
        try:
            result = numerator / denominator
            if math.isnan(result) or math.isinf(result):
                logger.warning(f"{ratio_name}: Result is {result}")
                return None
            return result
        except Exception as e:
            logger.error(f"{ratio_name}: Division error: {e}")
            return None
    
    def _calculate_valuation_ratios(self, ticker: str, fundamental_data: Dict, current_price: float) -> Dict[str, float]:
        """Calculate valuation ratios with enhanced error handling"""
        ratios = {}
        
        # P/E Ratio
        eps = fundamental_data.get('eps_diluted')
        if eps and eps > 0:  # Only calculate for positive EPS
            pe_ratio = self._safe_division(current_price, eps, 'P/E ratio')
            if pe_ratio is not None:
                ratios['pe_ratio'] = pe_ratio
        
        # P/B Ratio
        book_value = fundamental_data.get('book_value_per_share')
        if book_value and book_value > 0:  # Only calculate for positive book value
            pb_ratio = self._safe_division(current_price, book_value, 'P/B ratio')
            if pb_ratio is not None:
                ratios['pb_ratio'] = pb_ratio
        
        # P/S Ratio
        revenue = fundamental_data.get('revenue')
        shares = fundamental_data.get('shares_outstanding')
        if revenue and shares and shares > 0:
            sales_per_share = self._safe_division(revenue, shares, 'Sales per share')
            if sales_per_share and sales_per_share > 0:
                ps_ratio = self._safe_division(current_price, sales_per_share, 'P/S ratio')
                if ps_ratio is not None:
                    ratios['ps_ratio'] = ps_ratio
        
        # EV/EBITDA
        ebitda = fundamental_data.get('ebitda')
        if ebitda and ebitda > 0:
            market_cap = current_price * fundamental_data.get('shares_outstanding', 0)
            total_debt = fundamental_data.get('total_debt', 0)
            cash = fundamental_data.get('cash_and_equivalents', 0)
            enterprise_value = market_cap + total_debt - cash
            
            if enterprise_value > 0:
                ev_ebitda = self._safe_division(enterprise_value, ebitda, 'EV/EBITDA')
                if ev_ebitda is not None:
                    ratios['ev_ebitda'] = ev_ebitda
        
        # PEG Ratio
        if 'pe_ratio' in ratios:
            # For PEG, we need earnings growth rate
            # This would require historical data or analyst estimates
            # For now, we'll skip this calculation
            pass
        
        return ratios
    
    def _calculate_profitability_ratios(self, ticker: str, fundamental_data: Dict) -> Dict[str, float]:
        """Calculate profitability ratios with enhanced error handling"""
        ratios = {}
        
        # Return on Equity (ROE)
        net_income = fundamental_data.get('net_income')
        total_equity = fundamental_data.get('total_equity')
        if net_income and total_equity and total_equity > 0:
            roe = self._safe_division(net_income, total_equity, 'ROE')
            if roe is not None:
                ratios['return_on_equity'] = roe
        
        # Return on Assets (ROA)
        total_assets = fundamental_data.get('total_assets')
        if net_income and total_assets and total_assets > 0:
            roa = self._safe_division(net_income, total_assets, 'ROA')
            if roa is not None:
                ratios['return_on_assets'] = roa
        
        # Return on Invested Capital (ROIC)
        operating_income = fundamental_data.get('operating_income')
        total_debt = fundamental_data.get('total_debt', 0)
        total_equity = fundamental_data.get('total_equity')
        if operating_income and total_assets and total_debt and total_equity:
            invested_capital = total_assets - total_debt + total_equity
            if invested_capital > 0:
                roic = self._safe_division(operating_income, invested_capital, 'ROIC')
                if roic is not None:
                    ratios['return_on_invested_capital'] = roic
        
        # Gross Margin
        revenue = fundamental_data.get('revenue')
        cost_of_goods_sold = fundamental_data.get('cost_of_goods_sold')
        if revenue and cost_of_goods_sold and revenue > 0:
            gross_margin = self._safe_division(revenue - cost_of_goods_sold, revenue, 'Gross margin')
            if gross_margin is not None:
                ratios['gross_margin'] = gross_margin
        
        # Operating Margin
        if operating_income and revenue and revenue > 0:
            operating_margin = self._safe_division(operating_income, revenue, 'Operating margin')
            if operating_margin is not None:
                ratios['operating_margin'] = operating_margin
        
        # Net Margin
        if net_income and revenue and revenue > 0:
            net_margin = self._safe_division(net_income, revenue, 'Net margin')
            if net_margin is not None:
                ratios['net_margin'] = net_margin
        
        return ratios
    
    def _calculate_financial_health_ratios(self, ticker: str, fundamental_data: Dict, current_price: float) -> Dict[str, float]:
        """Calculate financial health ratios with enhanced error handling"""
        ratios = {}
        
        # Debt-to-Equity
        total_debt = fundamental_data.get('total_debt', 0)
        total_equity = fundamental_data.get('total_equity')
        if total_equity and total_equity > 0:
            debt_equity = self._safe_division(total_debt, total_equity, 'Debt-to-equity')
            if debt_equity is not None:
                ratios['debt_to_equity'] = debt_equity
        
        # Current Ratio
        current_assets = fundamental_data.get('current_assets')
        current_liabilities = fundamental_data.get('current_liabilities')
        if current_assets and current_liabilities and current_liabilities > 0:
            current_ratio = self._safe_division(current_assets, current_liabilities, 'Current ratio')
            if current_ratio is not None:
                ratios['current_ratio'] = current_ratio
        
        # Quick Ratio (Acid Test)
        inventory = fundamental_data.get('inventory', 0)
        if current_assets and current_liabilities and current_liabilities > 0:
            quick_assets = current_assets - inventory
            quick_ratio = self._safe_division(quick_assets, current_liabilities, 'Quick ratio')
            if quick_ratio is not None:
                ratios['quick_ratio'] = quick_ratio
        
        return ratios
    
    def _calculate_efficiency_ratios(self, ticker: str, fundamental_data: Dict, historical_data: Dict) -> Dict[str, float]:
        """Calculate efficiency ratios with enhanced error handling"""
        ratios = {}
        
        # Asset Turnover
        revenue = fundamental_data.get('revenue')
        total_assets = fundamental_data.get('total_assets')
        if revenue and total_assets and total_assets > 0:
            asset_turnover = self._safe_division(revenue, total_assets, 'Asset turnover')
            if asset_turnover is not None:
                ratios['asset_turnover'] = asset_turnover
        
        # Inventory Turnover (if inventory data exists)
        inventory = fundamental_data.get('inventory')
        cost_of_goods_sold = fundamental_data.get('cost_of_goods_sold')
        if inventory and cost_of_goods_sold and inventory > 0:
            inventory_turnover = self._safe_division(cost_of_goods_sold, inventory, 'Inventory turnover')
            if inventory_turnover is not None:
                ratios['inventory_turnover'] = inventory_turnover
        
        # Receivables Turnover (if accounts_receivable data exists)
        accounts_receivable = fundamental_data.get('accounts_receivable')
        if accounts_receivable and revenue and accounts_receivable > 0:
            receivables_turnover = self._safe_division(revenue, accounts_receivable, 'Receivables turnover')
            if receivables_turnover is not None:
                ratios['receivables_turnover'] = receivables_turnover
        
        return ratios
    
    def _calculate_growth_metrics(self, ticker: str, fundamental_data: Dict, historical_data: Dict) -> Dict[str, float]:
        """Calculate growth metrics with enhanced error handling"""
        ratios = {}
        
        if not historical_data:
            return ratios
        
        # Revenue Growth
        current_revenue = fundamental_data.get('revenue')
        previous_revenue = historical_data.get('revenue_previous')
        if current_revenue and previous_revenue and previous_revenue > 0:
            revenue_growth = self._safe_division(current_revenue - previous_revenue, previous_revenue, 'Revenue growth')
            if revenue_growth is not None:
                ratios['revenue_growth_yoy'] = revenue_growth * 100
        
        # Earnings Growth
        current_net_income = fundamental_data.get('net_income')
        previous_net_income = historical_data.get('net_income_previous')
        if current_net_income and previous_net_income and previous_net_income > 0:
            earnings_growth = self._safe_division(current_net_income - previous_net_income, previous_net_income, 'Earnings growth')
            if earnings_growth is not None:
                ratios['earnings_growth_yoy'] = earnings_growth * 100
        
        # FCF Growth
        current_fcf = fundamental_data.get('free_cash_flow')
        previous_fcf = historical_data.get('free_cash_flow_previous')
        if current_fcf and previous_fcf and previous_fcf > 0:
            fcf_growth = self._safe_division(current_fcf - previous_fcf, previous_fcf, 'FCF growth')
            if fcf_growth is not None:
                ratios['fcf_growth_yoy'] = fcf_growth * 100
        
        return ratios
    
    def _calculate_quality_metrics(self, ticker: str, fundamental_data: Dict) -> Dict[str, float]:
        """Calculate quality metrics with enhanced error handling"""
        ratios = {}
        
        # FCF to Net Income
        fcf = fundamental_data.get('free_cash_flow')
        net_income = fundamental_data.get('net_income')
        if fcf and net_income and net_income > 0:
            fcf_to_net_income = self._safe_division(fcf, net_income, 'FCF to net income')
            if fcf_to_net_income is not None:
                ratios['fcf_to_net_income'] = fcf_to_net_income
        
        # Cash Conversion Cycle (simplified)
        # This requires more complex calculation, skipping for now
        # ratios['cash_conversion_cycle'] = self._calculate_cash_conversion_cycle(fundamental_data)
        
        return ratios
    
    def _calculate_market_data(self, ticker: str, fundamental_data: Dict, current_price: float) -> Dict[str, float]:
        """Calculate market data with enhanced error handling"""
        ratios = {}
        
        # Market Cap
        shares_outstanding = fundamental_data.get('shares_outstanding')
        if shares_outstanding and shares_outstanding > 0:
            market_cap = current_price * shares_outstanding
            ratios['market_cap'] = market_cap
        
        # Enterprise Value
        if 'market_cap' in ratios:
            total_debt = fundamental_data.get('total_debt', 0)
            cash = fundamental_data.get('cash_and_equivalents', 0)
            enterprise_value = ratios['market_cap'] + total_debt - cash
            ratios['enterprise_value'] = enterprise_value
        
        return ratios
    
    def _calculate_intrinsic_value(self, ticker: str, fundamental_data: Dict, current_price: float) -> Dict[str, float]:
        """Calculate intrinsic value metrics with enhanced error handling"""
        ratios = {}
        
        # Graham Number
        eps = fundamental_data.get('eps_diluted')
        book_value = fundamental_data.get('book_value_per_share')
        if eps and eps > 0 and book_value and book_value > 0:
            graham_number = math.sqrt(22.5 * eps * book_value)
            if not math.isnan(graham_number) and not math.isinf(graham_number):
                ratios['graham_number'] = graham_number
        
        return ratios 