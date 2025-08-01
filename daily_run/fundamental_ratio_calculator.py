"""
Fundamental Ratio Calculator
Calculates all financial ratios for stock analysis
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RatioCalculationResult:
    """Result of ratio calculation with validation"""
    ratio_name: str
    calculated_value: float
    yahoo_value: Optional[float] = None
    difference: Optional[float] = None
    difference_percent: Optional[float] = None
    is_valid: bool = True
    error_message: Optional[str] = None

class FundamentalRatioCalculator:
    """
    Comprehensive fundamental ratio calculator
    Calculates all financial ratios defined in the database schema
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def calculate_all_ratios(self, ticker: str, current_price: float) -> Dict[str, float]:
        """
        Calculate all financial ratios for a ticker
        
        Args:
            ticker: Stock symbol
            current_price: Current stock price
            
        Returns:
            Dictionary of all calculated ratios
        """
        try:
            # Get fundamental data
            fundamental_data = self._get_fundamental_data(ticker)
            if not fundamental_data:
                logger.warning(f"No fundamental data found for {ticker}")
                return {}
            
            # Get historical data for growth calculations
            historical_data = self._get_historical_fundamentals(ticker)
            
            ratios = {}
            
            # Calculate all ratio categories
            ratios.update(self.calculate_valuation_ratios(current_price, fundamental_data))
            ratios.update(self.calculate_profitability_ratios(fundamental_data))
            ratios.update(self.calculate_financial_health_ratios(fundamental_data))
            ratios.update(self.calculate_efficiency_ratios(fundamental_data))
            ratios.update(self.calculate_growth_metrics(historical_data))
            ratios.update(self.calculate_quality_metrics(fundamental_data))
            ratios.update(self.calculate_market_metrics(current_price, fundamental_data))
            ratios.update(self.calculate_intrinsic_value_metrics(current_price, fundamental_data))
            
            # Validate and clean ratios
            ratios = self._validate_ratios(ratios)
            
            logger.info(f"Calculated {len(ratios)} ratios for {ticker}")
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating ratios for {ticker}: {e}")
            return {}
    
    def calculate_valuation_ratios(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate valuation ratios"""
        ratios = {}
        
        try:
            # P/E Ratio
            if fundamentals.get('net_income') and fundamentals.get('shares_outstanding'):
                eps = fundamentals['net_income'] / fundamentals['shares_outstanding']
                if eps > 0:
                    ratios['pe_ratio'] = current_price / eps
                else:
                    ratios['pe_ratio'] = None
            
            # P/B Ratio
            if fundamentals.get('total_equity') and fundamentals.get('shares_outstanding'):
                book_value_per_share = fundamentals['total_equity'] / fundamentals['shares_outstanding']
                if book_value_per_share > 0:
                    ratios['pb_ratio'] = current_price / book_value_per_share
                else:
                    ratios['pb_ratio'] = None
            
            # P/S Ratio
            if fundamentals.get('revenue') and fundamentals.get('shares_outstanding'):
                sales_per_share = fundamentals['revenue'] / fundamentals['shares_outstanding']
                if sales_per_share > 0:
                    ratios['ps_ratio'] = current_price / sales_per_share
                else:
                    ratios['ps_ratio'] = None
            
            # EV/EBITDA
            if fundamentals.get('ebitda'):
                enterprise_value = self._calculate_enterprise_value(current_price, fundamentals)
                if enterprise_value and fundamentals['ebitda'] > 0:
                    ratios['ev_ebitda'] = enterprise_value / fundamentals['ebitda']
                else:
                    ratios['ev_ebitda'] = None
            
            # PEG Ratio
            if ratios.get('pe_ratio') and fundamentals.get('earnings_growth_yoy'):
                if fundamentals['earnings_growth_yoy'] > 0:
                    ratios['peg_ratio'] = ratios['pe_ratio'] / fundamentals['earnings_growth_yoy']
                else:
                    ratios['peg_ratio'] = None
            
        except Exception as e:
            logger.error(f"Error calculating valuation ratios: {e}")
        
        return ratios
    
    def calculate_profitability_ratios(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate profitability ratios"""
        ratios = {}
        
        try:
            # ROE (Return on Equity)
            if fundamentals.get('net_income') and fundamentals.get('total_equity'):
                if fundamentals['total_equity'] > 0:
                    ratios['roe'] = (fundamentals['net_income'] / fundamentals['total_equity']) * 100
                else:
                    ratios['roe'] = None
            
            # ROA (Return on Assets)
            if fundamentals.get('net_income') and fundamentals.get('total_assets'):
                if fundamentals['total_assets'] > 0:
                    ratios['roa'] = (fundamentals['net_income'] / fundamentals['total_assets']) * 100
                else:
                    ratios['roa'] = None
            
            # ROIC (Return on Invested Capital)
            if fundamentals.get('operating_income') and fundamentals.get('total_assets') and fundamentals.get('total_debt'):
                invested_capital = fundamentals['total_assets'] - fundamentals['total_debt']
                if invested_capital > 0:
                    ratios['roic'] = (fundamentals['operating_income'] / invested_capital) * 100
                else:
                    ratios['roic'] = None
            
            # Margins
            if fundamentals.get('revenue'):
                # Gross Margin
                if fundamentals.get('gross_profit'):
                    ratios['gross_margin'] = (fundamentals['gross_profit'] / fundamentals['revenue']) * 100
                
                # Operating Margin
                if fundamentals.get('operating_income'):
                    ratios['operating_margin'] = (fundamentals['operating_income'] / fundamentals['revenue']) * 100
                
                # Net Margin
                if fundamentals.get('net_income'):
                    ratios['net_margin'] = (fundamentals['net_income'] / fundamentals['revenue']) * 100
            
        except Exception as e:
            logger.error(f"Error calculating profitability ratios: {e}")
        
        return ratios
    
    def calculate_financial_health_ratios(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate financial health ratios"""
        ratios = {}
        
        try:
            # Debt to Equity
            if fundamentals.get('total_debt') and fundamentals.get('total_equity'):
                if fundamentals['total_equity'] > 0:
                    ratios['debt_to_equity'] = fundamentals['total_debt'] / fundamentals['total_equity']
                else:
                    ratios['debt_to_equity'] = None
            
            # Current Ratio
            if fundamentals.get('current_assets') and fundamentals.get('current_liabilities'):
                if fundamentals['current_liabilities'] > 0:
                    ratios['current_ratio'] = fundamentals['current_assets'] / fundamentals['current_liabilities']
                else:
                    ratios['current_ratio'] = None
            
            # Quick Ratio
            if fundamentals.get('current_assets') and fundamentals.get('inventory') and fundamentals.get('current_liabilities'):
                quick_assets = fundamentals['current_assets'] - fundamentals.get('inventory', 0)
                if fundamentals['current_liabilities'] > 0:
                    ratios['quick_ratio'] = quick_assets / fundamentals['current_liabilities']
                else:
                    ratios['quick_ratio'] = None
            
            # Interest Coverage
            if fundamentals.get('operating_income') and fundamentals.get('interest_expense'):
                if fundamentals['interest_expense'] > 0:
                    ratios['interest_coverage'] = fundamentals['operating_income'] / fundamentals['interest_expense']
                else:
                    ratios['interest_coverage'] = None
            
            # Altman Z-Score
            ratios['altman_z_score'] = self._calculate_altman_z_score(fundamentals)
            
        except Exception as e:
            logger.error(f"Error calculating financial health ratios: {e}")
        
        return ratios
    
    def calculate_efficiency_ratios(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate efficiency ratios"""
        ratios = {}
        
        try:
            # Asset Turnover
            if fundamentals.get('revenue') and fundamentals.get('total_assets'):
                if fundamentals['total_assets'] > 0:
                    ratios['asset_turnover'] = fundamentals['revenue'] / fundamentals['total_assets']
                else:
                    ratios['asset_turnover'] = None
            
            # Inventory Turnover
            if fundamentals.get('cost_of_goods_sold') and fundamentals.get('inventory'):
                if fundamentals['inventory'] > 0:
                    ratios['inventory_turnover'] = fundamentals['cost_of_goods_sold'] / fundamentals['inventory']
                else:
                    ratios['inventory_turnover'] = None
            
            # Receivables Turnover
            if fundamentals.get('revenue') and fundamentals.get('accounts_receivable'):
                if fundamentals['accounts_receivable'] > 0:
                    ratios['receivables_turnover'] = fundamentals['revenue'] / fundamentals['accounts_receivable']
                else:
                    ratios['receivables_turnover'] = None
            
        except Exception as e:
            logger.error(f"Error calculating efficiency ratios: {e}")
        
        return ratios
    
    def calculate_growth_metrics(self, historical_data: List[Dict]) -> Dict[str, float]:
        """Calculate year-over-year growth metrics"""
        ratios = {}
        
        try:
            if len(historical_data) < 2:
                return ratios
            
            # Sort by date
            historical_data.sort(key=lambda x: x.get('report_date', date.min))
            
            current = historical_data[-1]
            previous = historical_data[-2]
            
            # Revenue Growth
            if current.get('revenue') and previous.get('revenue'):
                if previous['revenue'] > 0:
                    ratios['revenue_growth_yoy'] = ((current['revenue'] - previous['revenue']) / previous['revenue']) * 100
                else:
                    ratios['revenue_growth_yoy'] = None
            
            # Earnings Growth
            if current.get('net_income') and previous.get('net_income'):
                if previous['net_income'] > 0:
                    ratios['earnings_growth_yoy'] = ((current['net_income'] - previous['net_income']) / previous['net_income']) * 100
                else:
                    ratios['earnings_growth_yoy'] = None
            
            # FCF Growth
            if current.get('free_cash_flow') and previous.get('free_cash_flow'):
                if previous['free_cash_flow'] > 0:
                    ratios['fcf_growth_yoy'] = ((current['free_cash_flow'] - previous['free_cash_flow']) / previous['free_cash_flow']) * 100
                else:
                    ratios['fcf_growth_yoy'] = None
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {e}")
        
        return ratios
    
    def calculate_quality_metrics(self, fundamentals: Dict) -> Dict[str, float]:
        """Calculate quality metrics"""
        ratios = {}
        
        try:
            # FCF to Net Income
            if fundamentals.get('free_cash_flow') and fundamentals.get('net_income'):
                if fundamentals['net_income'] > 0:
                    ratios['fcf_to_net_income'] = fundamentals['free_cash_flow'] / fundamentals['net_income']
                else:
                    ratios['fcf_to_net_income'] = None
            
            # Cash Conversion Cycle
            if fundamentals.get('inventory') and fundamentals.get('accounts_receivable') and fundamentals.get('accounts_payable'):
                # Simplified calculation
                inventory_days = (fundamentals['inventory'] / fundamentals.get('cost_of_goods_sold', 1)) * 365
                receivables_days = (fundamentals['accounts_receivable'] / fundamentals.get('revenue', 1)) * 365
                payables_days = (fundamentals['accounts_payable'] / fundamentals.get('cost_of_goods_sold', 1)) * 365
                
                ratios['cash_conversion_cycle'] = inventory_days + receivables_days - payables_days
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
        
        return ratios
    
    def calculate_market_metrics(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate market-related metrics"""
        ratios = {}
        
        try:
            # Market Cap
            if fundamentals.get('shares_outstanding'):
                ratios['market_cap'] = current_price * fundamentals['shares_outstanding']
            
            # Enterprise Value
            enterprise_value = self._calculate_enterprise_value(current_price, fundamentals)
            if enterprise_value:
                ratios['enterprise_value'] = enterprise_value
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {e}")
        
        return ratios
    
    def calculate_intrinsic_value_metrics(self, current_price: float, fundamentals: Dict) -> Dict[str, float]:
        """Calculate intrinsic value metrics"""
        ratios = {}
        
        try:
            # Graham Number
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
        """Calculate enterprise value"""
        try:
            if not fundamentals.get('shares_outstanding'):
                return None
            
            market_cap = current_price * fundamentals['shares_outstanding']
            total_debt = fundamentals.get('total_debt', 0)
            cash = fundamentals.get('cash_and_equivalents', 0)
            
            return market_cap + total_debt - cash
            
        except Exception as e:
            logger.error(f"Error calculating enterprise value: {e}")
            return None
    
    def _calculate_altman_z_score(self, fundamentals: Dict) -> Optional[float]:
        """Calculate Altman Z-Score for bankruptcy risk"""
        try:
            # Get required values
            working_capital = fundamentals.get('current_assets', 0) - fundamentals.get('current_liabilities', 0)
            total_assets = fundamentals.get('total_assets', 1)
            retained_earnings = fundamentals.get('retained_earnings', 0)
            ebit = fundamentals.get('operating_income', 0)
            total_equity = fundamentals.get('total_equity', 1)
            total_liabilities = fundamentals.get('total_liabilities', 0)
            revenue = fundamentals.get('revenue', 1)
            
            # Altman Z-Score formula
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
    
    def _get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get fundamental data from database"""
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
    
    def _validate_ratios(self, ratios: Dict[str, float]) -> Dict[str, float]:
        """Validate and clean ratio values"""
        validated_ratios = {}
        
        for ratio_name, value in ratios.items():
            if value is not None and not np.isnan(value) and not np.isinf(value):
                # Round to 4 decimal places
                validated_ratios[ratio_name] = round(float(value), 4)
            else:
                validated_ratios[ratio_name] = None
        
        return validated_ratios
    
    def compare_with_yahoo_finance(self, ticker: str, ratios: Dict[str, float]) -> List[RatioCalculationResult]:
        """
        Compare calculated ratios with Yahoo Finance data
        This is a placeholder - you'll need to implement Yahoo Finance API calls
        """
        results = []
        
        # This would require Yahoo Finance API integration
        # For now, return empty results
        logger.info(f"Yahoo Finance comparison not implemented yet for {ticker}")
        
        return results
    
    def store_ratios(self, ticker: str, ratios: Dict[str, float]) -> bool:
        """Store calculated ratios in database"""
        try:
            # Prepare data for insertion
            calculation_date = datetime.now().date()
            
            # Map ratios to database columns
            ratio_data = {
                'ticker': ticker,
                'calculation_date': calculation_date,
                'pe_ratio': ratios.get('pe_ratio'),
                'pb_ratio': ratios.get('pb_ratio'),
                'ps_ratio': ratios.get('ps_ratio'),
                'ev_ebitda': ratios.get('ev_ebitda'),
                'peg_ratio': ratios.get('peg_ratio'),
                'roe': ratios.get('roe'),
                'roa': ratios.get('roa'),
                'roic': ratios.get('roic'),
                'gross_margin': ratios.get('gross_margin'),
                'operating_margin': ratios.get('operating_margin'),
                'net_margin': ratios.get('net_margin'),
                'debt_to_equity': ratios.get('debt_to_equity'),
                'current_ratio': ratios.get('current_ratio'),
                'quick_ratio': ratios.get('quick_ratio'),
                'interest_coverage': ratios.get('interest_coverage'),
                'altman_z_score': ratios.get('altman_z_score'),
                'asset_turnover': ratios.get('asset_turnover'),
                'inventory_turnover': ratios.get('inventory_turnover'),
                'receivables_turnover': ratios.get('receivables_turnover'),
                'revenue_growth_yoy': ratios.get('revenue_growth_yoy'),
                'earnings_growth_yoy': ratios.get('earnings_growth_yoy'),
                'fcf_growth_yoy': ratios.get('fcf_growth_yoy'),
                'fcf_to_net_income': ratios.get('fcf_to_net_income'),
                'cash_conversion_cycle': ratios.get('cash_conversion_cycle'),
                'market_cap': ratios.get('market_cap'),
                'enterprise_value': ratios.get('enterprise_value'),
                'graham_number': ratios.get('graham_number'),
                'last_updated': datetime.now()
            }
            
            # Build INSERT/UPDATE query
            columns = list(ratio_data.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            
            query = f"""
            INSERT INTO financial_ratios ({column_names})
            VALUES ({placeholders})
            ON CONFLICT (ticker, calculation_date)
            DO UPDATE SET
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                ps_ratio = EXCLUDED.ps_ratio,
                ev_ebitda = EXCLUDED.ev_ebitda,
                peg_ratio = EXCLUDED.peg_ratio,
                roe = EXCLUDED.roe,
                roa = EXCLUDED.roa,
                roic = EXCLUDED.roic,
                gross_margin = EXCLUDED.gross_margin,
                operating_margin = EXCLUDED.operating_margin,
                net_margin = EXCLUDED.net_margin,
                debt_to_equity = EXCLUDED.debt_to_equity,
                current_ratio = EXCLUDED.current_ratio,
                quick_ratio = EXCLUDED.quick_ratio,
                interest_coverage = EXCLUDED.interest_coverage,
                altman_z_score = EXCLUDED.altman_z_score,
                asset_turnover = EXCLUDED.asset_turnover,
                inventory_turnover = EXCLUDED.inventory_turnover,
                receivables_turnover = EXCLUDED.receivables_turnover,
                revenue_growth_yoy = EXCLUDED.revenue_growth_yoy,
                earnings_growth_yoy = EXCLUDED.earnings_growth_yoy,
                fcf_growth_yoy = EXCLUDED.fcf_growth_yoy,
                fcf_to_net_income = EXCLUDED.fcf_to_net_income,
                cash_conversion_cycle = EXCLUDED.cash_conversion_cycle,
                market_cap = EXCLUDED.market_cap,
                enterprise_value = EXCLUDED.enterprise_value,
                graham_number = EXCLUDED.graham_number,
                last_updated = EXCLUDED.last_updated
            """
            
            values = tuple(ratio_data.values())
            self.db.execute_query(query, values)
            
            logger.info(f"Stored {len(ratios)} ratios for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing ratios for {ticker}: {e}")
            return False 