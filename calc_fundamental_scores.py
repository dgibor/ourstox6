#!/usr/bin/env python3
"""
Fundamental Analysis Scoring System
Calculates fundamental scores based on financial ratios and stores in database
"""

import os
import sys
import json
import logging
import time
import math
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add daily_run to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from calc_technical_scores import TechnicalScoreCalculator

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundamentalScoreCalculator:
    """
    Calculates fundamental analysis scores based on financial ratios
    """
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.technical_calculator = TechnicalScoreCalculator()
        self.db_connection = None
        self.calculation_batch_id = f"fund_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def normalize_score_to_5_levels(self, score, score_type):
        """
        Normalize a 0-100 score to 5 levels: Strong Sell (1), Sell (2), Neutral (3), Buy (4), Strong Buy (5)
        
        Args:
            score (float): Score from 0-100
            score_type (str): Type of score for specific thresholds
            
        Returns:
            dict: Contains normalized_score (1-5), grade (string), and description
        """
        if score is None:
            return {
                'normalized_score': 3,
                'grade': 'Neutral',
                'description': 'Insufficient data for assessment'
            }
        
        # Different thresholds for different score types
        if score_type == 'fundamental_health':
            # Higher scores are better for fundamental health
            if score >= 85:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Excellent fundamental health'}
            elif score >= 70:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Good fundamental health'}
            elif score >= 50:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Average fundamental health'}
            elif score >= 30:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Poor fundamental health'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very poor fundamental health'}
        
        elif score_type == 'risk_assessment':
            # Lower scores are better for risk (less risk = better)
            if score <= 20:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Very low risk'}
            elif score <= 35:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Low risk'}
            elif score <= 55:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Moderate risk'}
            elif score <= 75:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'High risk'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very high risk'}
        
        elif score_type == 'value_investment':
            # Higher scores are better for value investment
            if score >= 80:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Excellent value opportunity'}
            elif score >= 65:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Good value opportunity'}
            elif score >= 45:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Fair value'}
            elif score >= 25:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Poor value'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very poor value'}
        
        elif score_type == 'technical_health':
            # Higher scores are better for technical health
            if score >= 80:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Excellent technical health'}
            elif score >= 65:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Good technical health'}
            elif score >= 45:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Average technical health'}
            elif score >= 25:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Poor technical health'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very poor technical health'}
        
        elif score_type == 'trading_signal':
            # Higher scores are better for trading signals
            if score >= 75:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Strong buy signal'}
            elif score >= 60:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Buy signal'}
            elif score >= 40:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Neutral signal'}
            elif score >= 25:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Sell signal'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Strong sell signal'}
        
        elif score_type == 'technical_risk':
            # Lower scores are better for technical risk (less risk = better)
            if score <= 25:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Very low technical risk'}
            elif score <= 40:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Low technical risk'}
            elif score <= 60:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Moderate technical risk'}
            elif score <= 80:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'High technical risk'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very high technical risk'}
        
        else:
            # Default normalization
            if score >= 80:
                return {'normalized_score': 5, 'grade': 'Strong Buy', 'description': 'Excellent'}
            elif score >= 60:
                return {'normalized_score': 4, 'grade': 'Buy', 'description': 'Good'}
            elif score >= 40:
                return {'normalized_score': 3, 'grade': 'Neutral', 'description': 'Average'}
            elif score >= 20:
                return {'normalized_score': 2, 'grade': 'Sell', 'description': 'Poor'}
            else:
                return {'normalized_score': 1, 'grade': 'Strong Sell', 'description': 'Very poor'}

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)

    def calculate_missing_ratios(self, fundamental_data, current_price):
        """Calculate missing financial ratios from fundamental data"""
        ratios = {}
        
        try:
            # Extract data with safe defaults
            revenue = fundamental_data.get('revenue', 0) or 0
            net_income = fundamental_data.get('net_income', 0) or 0
            total_assets = fundamental_data.get('total_assets', 0) or 0
            total_equity = fundamental_data.get('total_equity', 0) or 0
            total_debt = fundamental_data.get('total_debt', 0) or 0
            current_assets = fundamental_data.get('current_assets', 0) or 0
            current_liabilities = fundamental_data.get('current_liabilities', 0) or 0
            book_value_per_share = fundamental_data.get('book_value_per_share', 0) or 0
            earnings_per_share = fundamental_data.get('earnings_per_share', 0) or 0
            market_cap = fundamental_data.get('market_cap', 0) or 0
            sector = fundamental_data.get('sector', '') or ''
            
            # Calculate PE ratio - enhanced estimation
            if earnings_per_share > 0 and current_price:
                ratios['pe_ratio'] = current_price / earnings_per_share
            elif net_income > 0 and market_cap > 0:
                # Estimate PE ratio from market cap and net income
                estimated_pe = market_cap / net_income
                ratios['pe_ratio'] = estimated_pe
                logger.info(f"Estimated PE ratio from market cap/net income: {estimated_pe:.2f}")
            elif net_income > 0 and current_price:
                # Estimate shares outstanding - use more realistic assumptions
                if market_cap > 0:
                    # Market cap is likely in millions/billions, so we need to estimate shares more carefully
                    # For large companies, assume reasonable shares outstanding
                    if market_cap > 1000000000000:  # > $1T market cap
                        estimated_shares = 15000000000  # 15B shares (like AAPL)
                    elif market_cap > 100000000000:  # > $100B market cap
                        estimated_shares = 5000000000   # 5B shares
                    elif market_cap > 10000000000:   # > $10B market cap
                        estimated_shares = 1000000000   # 1B shares
                    else:
                        estimated_shares = 500000000    # 500M shares
                else:
                    # Assume reasonable shares outstanding based on sector
                    if sector in ['Technology', 'Consumer Cyclical']:
                        estimated_shares = 1000000000  # 1B shares for large tech
                    else:
                        estimated_shares = 500000000   # 500M shares for others
                
                estimated_eps = net_income / estimated_shares
                if estimated_eps > 0:
                    ratios['pe_ratio'] = current_price / estimated_eps
                    logger.info(f"Estimated PE ratio from estimated EPS: {ratios['pe_ratio']:.2f}")
                else:
                    ratios['pe_ratio'] = None
            else:
                ratios['pe_ratio'] = None
            
            # Calculate PB ratio - enhanced estimation
            if book_value_per_share > 0 and current_price:
                ratios['pb_ratio'] = current_price / book_value_per_share
            elif total_equity > 0 and current_price:
                # Estimate PB ratio from total equity
                if market_cap > 0:
                    # Use same realistic share estimation as PE ratio
                    if market_cap > 1000000000000:  # > $1T market cap
                        estimated_shares = 15000000000  # 15B shares (like AAPL)
                    elif market_cap > 100000000000:  # > $100B market cap
                        estimated_shares = 5000000000   # 5B shares
                    elif market_cap > 10000000000:   # > $10B market cap
                        estimated_shares = 1000000000   # 1B shares
                    else:
                        estimated_shares = 500000000    # 500M shares
                else:
                    # Use same estimation as above
                    if sector in ['Technology', 'Consumer Cyclical']:
                        estimated_shares = 1000000000
                    else:
                        estimated_shares = 500000000
                
                estimated_bvps = total_equity / estimated_shares
                if estimated_bvps > 0:
                    ratios['pb_ratio'] = current_price / estimated_bvps
                    logger.info(f"Estimated PB ratio from estimated BVPS: {ratios['pb_ratio']:.2f}")
                else:
                    ratios['pb_ratio'] = None
            else:
                ratios['pb_ratio'] = None
            
            if total_equity > 0:
                ratios['roe'] = (net_income / total_equity) * 100
            else:
                ratios['roe'] = None
            
            if total_assets > 0:
                ratios['roa'] = (net_income / total_assets) * 100
            else:
                ratios['roa'] = None
            
            if total_equity > 0 and total_debt:
                ratios['debt_to_equity'] = total_debt / total_equity
            else:
                ratios['debt_to_equity'] = None
            
            if current_liabilities > 0 and current_assets:
                ratios['current_ratio'] = current_assets / current_liabilities
            else:
                ratios['current_ratio'] = None
            
            # Calculate EV/EBITDA (simplified - using net income as proxy for EBITDA)
            if net_income > 0:
                ev_ebitda = None
                if current_price and earnings_per_share > 0:
                    # Estimate shares outstanding from EPS and net income
                    shares_outstanding = net_income / earnings_per_share
                    market_cap = current_price * shares_outstanding
                    enterprise_value = market_cap + total_debt
                    ev_ebitda = enterprise_value / net_income
                elif market_cap > 0:
                    # Use market cap directly
                    enterprise_value = market_cap + total_debt
                    ev_ebitda = enterprise_value / net_income
                ratios['ev_ebitda'] = ev_ebitda
            else:
                ratios['ev_ebitda'] = None
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating ratios: {e}")
            return {}

    def get_fundamental_data(self, ticker):
        """Get fundamental data for a ticker"""
        query = """
        SELECT 
            cf.*,
            cf.revenue as total_revenue_ttm,
            cf.net_income as net_income_ttm,
            s.market_cap,
            s.sector
        FROM company_fundamentals cf
        LEFT JOIN stocks s ON cf.ticker = s.ticker
        WHERE cf.ticker = %s
        ORDER BY cf.last_updated DESC
        LIMIT 1
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (ticker,))
                fundamental_data = cursor.fetchone()
                
                if not fundamental_data:
                    return None
                
                # Get financial ratios
                ratios_query = """
                SELECT 
                    fr.*,
                    fr.ev_ebitda as ev_ebitda_ratio
                FROM financial_ratios fr
                WHERE fr.ticker = %s
                ORDER BY fr.calculation_date DESC
                LIMIT 1
                """
                cursor.execute(ratios_query, (ticker,))
                ratios_data = cursor.fetchone()
                
                # Merge data
                if ratios_data:
                    fundamental_data.update(ratios_data)
                
                # Get current price for ratio calculations
                current_price = self.get_current_price(ticker)
                
                # Calculate missing ratios on-the-fly
                if current_price:
                    missing_ratios = self.calculate_missing_ratios(fundamental_data, current_price)
                    
                    # Update fundamental_data with calculated ratios (only if not already present)
                    for ratio_name, ratio_value in missing_ratios.items():
                        if ratio_value is not None and fundamental_data.get(ratio_name) is None:
                            fundamental_data[ratio_name] = ratio_value
                            logger.info(f"Calculated missing ratio for {ticker}: {ratio_name} = {ratio_value:.2f}")
                
                # Add ticker to data for risk assessment
                fundamental_data['ticker'] = ticker
                
                return dict(fundamental_data)

    def get_historical_fundamental_data(self, ticker, periods=4):
        """Get historical fundamental data for trend analysis"""
        query = """
        SELECT 
            cf.*,
            cf.revenue as total_revenue_ttm,
            cf.net_income as net_income_ttm
        FROM company_fundamentals cf
        WHERE cf.ticker = %s
        ORDER BY cf.last_updated DESC
        LIMIT %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (ticker, periods))
                return [dict(row) for row in cursor.fetchall()]
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for ticker"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = "SELECT close FROM daily_charts WHERE ticker = %s ORDER BY date DESC LIMIT 1"
                    cursor.execute(query, (ticker,))
                    result = cursor.fetchone()
                    return result['close'] if result else None
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return None
    
    def calculate_financial_health_component(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Financial Health Component (0-100)
        Components: Debt-to-Equity (30%), Current Ratio (25%), Quick Ratio (25%), Interest Coverage (20%)
        """
        components = {}
        
        # Debt-to-Equity (30% weight)
        debt_equity = data.get('debt_to_equity', None)
        if debt_equity is not None:
            if debt_equity <= 0.5:
                debt_equity_score = 100
            elif debt_equity <= 1.0:
                debt_equity_score = 80
            elif debt_equity <= 1.5:
                debt_equity_score = 60
            elif debt_equity <= 2.0:
                debt_equity_score = 40
            else:
                debt_equity_score = 20
        else:
            debt_equity_score = 50
        
        components['debt_to_equity'] = debt_equity_score
        
        # Current Ratio (25% weight)
        current_ratio = data.get('current_ratio', None)
        if current_ratio is not None:
            if current_ratio >= 2.0:
                current_ratio_score = 100
            elif current_ratio >= 1.5:
                current_ratio_score = 80
            elif current_ratio >= 1.0:
                current_ratio_score = 60
            elif current_ratio >= 0.8:
                current_ratio_score = 40
            else:
                current_ratio_score = 20
        else:
            current_ratio_score = 50
        
        components['current_ratio'] = current_ratio_score
        
        # Quick Ratio (25% weight)
        quick_ratio = data.get('quick_ratio', None)
        if quick_ratio is not None:
            if quick_ratio >= 1.5:
                quick_ratio_score = 100
            elif quick_ratio >= 1.0:
                quick_ratio_score = 80
            elif quick_ratio >= 0.8:
                quick_ratio_score = 60
            elif quick_ratio >= 0.5:
                quick_ratio_score = 40
            else:
                quick_ratio_score = 20
        else:
            quick_ratio_score = 50
        
        components['quick_ratio'] = quick_ratio_score
        
        # Interest Coverage (20% weight)
        interest_coverage = data.get('interest_coverage', None)
        if interest_coverage is not None:
            if interest_coverage >= 5.0:
                interest_coverage_score = 100
            elif interest_coverage >= 3.0:
                interest_coverage_score = 80
            elif interest_coverage >= 2.0:
                interest_coverage_score = 60
            elif interest_coverage >= 1.5:
                interest_coverage_score = 40
            else:
                interest_coverage_score = 20
        else:
            interest_coverage_score = 50
        
        components['interest_coverage'] = interest_coverage_score
        
        # Calculate weighted average
        financial_health = (
            debt_equity_score * 0.30 +
            current_ratio_score * 0.25 +
            quick_ratio_score * 0.25 +
            interest_coverage_score * 0.20
        )
        
        return financial_health, components
    
    def calculate_profitability_component(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Profitability Component (0-100)
        Components: ROE (30%), ROA (25%), Operating Margin (25%), Net Margin (20%)
        """
        components = {}
        
        # ROE (30% weight)
        roe = data.get('roe', None)
        if roe is not None:
            if roe >= 20:
                roe_score = 100
            elif roe >= 15:
                roe_score = 80
            elif roe >= 10:
                roe_score = 60
            elif roe >= 5:
                roe_score = 40
            else:
                roe_score = 20
        else:
            roe_score = 50
        
        components['roe'] = roe_score
        
        # ROA (25% weight)
        roa = data.get('roa', None)
        if roa is not None:
            if roa >= 10:
                roa_score = 100
            elif roa >= 7:
                roa_score = 80
            elif roa >= 5:
                roa_score = 60
            elif roa >= 3:
                roa_score = 40
            else:
                roa_score = 20
        else:
            roa_score = 50
        
        components['roa'] = roa_score
        
        # Operating Margin (25% weight)
        operating_margin = data.get('operating_margin', None)
        if operating_margin is not None:
            if operating_margin >= 20:
                operating_margin_score = 100
            elif operating_margin >= 15:
                operating_margin_score = 80
            elif operating_margin >= 10:
                operating_margin_score = 60
            elif operating_margin >= 5:
                operating_margin_score = 40
            else:
                operating_margin_score = 20
        else:
            operating_margin_score = 50
        
        components['operating_margin'] = operating_margin_score
        
        # Net Margin (20% weight)
        net_margin = data.get('net_margin', None)
        if net_margin is not None:
            if net_margin >= 15:
                net_margin_score = 100
            elif net_margin >= 10:
                net_margin_score = 80
            elif net_margin >= 5:
                net_margin_score = 60
            elif net_margin >= 2:
                net_margin_score = 40
            else:
                net_margin_score = 20
        else:
            net_margin_score = 50
        
        components['net_margin'] = net_margin_score
        
        # Calculate weighted average
        profitability = (
            roe_score * 0.30 +
            roa_score * 0.25 +
            operating_margin_score * 0.25 +
            net_margin_score * 0.20
        )
        
        return profitability, components
    
    def calculate_quality_component(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Quality Component (0-100)
        Components: Asset Turnover (30%), Inventory Turnover (25%), Receivables Turnover (25%), FCF to Net Income (20%)
        """
        components = {}
        
        # Asset Turnover (30% weight)
        asset_turnover = data.get('asset_turnover', None)
        if asset_turnover is not None:
            if asset_turnover >= 1.5:
                asset_turnover_score = 100
            elif asset_turnover >= 1.0:
                asset_turnover_score = 80
            elif asset_turnover >= 0.8:
                asset_turnover_score = 60
            elif asset_turnover >= 0.5:
                asset_turnover_score = 40
            else:
                asset_turnover_score = 20
        else:
            asset_turnover_score = 50
        
        components['asset_turnover'] = asset_turnover_score
        
        # Inventory Turnover (25% weight)
        inventory_turnover = data.get('inventory_turnover', None)
        if inventory_turnover is not None:
            if inventory_turnover >= 10:
                inventory_turnover_score = 100
            elif inventory_turnover >= 8:
                inventory_turnover_score = 80
            elif inventory_turnover >= 6:
                inventory_turnover_score = 60
            elif inventory_turnover >= 4:
                inventory_turnover_score = 40
            else:
                inventory_turnover_score = 20
        else:
            inventory_turnover_score = 50
        
        components['inventory_turnover'] = inventory_turnover_score
        
        # Receivables Turnover (25% weight)
        receivables_turnover = data.get('receivables_turnover', None)
        if receivables_turnover is not None:
            if receivables_turnover >= 12:
                receivables_turnover_score = 100
            elif receivables_turnover >= 10:
                receivables_turnover_score = 80
            elif receivables_turnover >= 8:
                receivables_turnover_score = 60
            elif receivables_turnover >= 6:
                receivables_turnover_score = 40
            else:
                receivables_turnover_score = 20
        else:
            receivables_turnover_score = 50
        
        components['receivables_turnover'] = receivables_turnover_score
        
        # FCF to Net Income (20% weight)
        fcf_to_net_income = data.get('fcf_to_net_income', None)
        if fcf_to_net_income is not None:
            if fcf_to_net_income >= 1.2:
                fcf_score = 100
            elif fcf_to_net_income >= 1.0:
                fcf_score = 80
            elif fcf_to_net_income >= 0.8:
                fcf_score = 60
            elif fcf_to_net_income >= 0.6:
                fcf_score = 40
            else:
                fcf_score = 20
        else:
            fcf_score = 50
        
        components['fcf_to_net_income'] = fcf_score
        
        # Calculate weighted average
        quality = (
            asset_turnover_score * 0.30 +
            inventory_turnover_score * 0.25 +
            receivables_turnover_score * 0.25 +
            fcf_score * 0.20
        )
        
        return quality, components
    
    def calculate_growth_component(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Growth Component (0-100)
        Components: Revenue Growth (40%), Earnings Growth (35%), FCF Growth (25%)
        """
        components = {}
        
        # Revenue Growth (40% weight)
        revenue_growth = data.get('revenue_growth_yoy', None)
        if revenue_growth is not None:
            if revenue_growth >= 20:
                revenue_growth_score = 100
            elif revenue_growth >= 15:
                revenue_growth_score = 80
            elif revenue_growth >= 10:
                revenue_growth_score = 60
            elif revenue_growth >= 5:
                revenue_growth_score = 40
            else:
                revenue_growth_score = 20
        else:
            revenue_growth_score = 50
        
        components['revenue_growth'] = revenue_growth_score
        
        # Earnings Growth (35% weight)
        earnings_growth = data.get('earnings_growth_yoy', None)
        if earnings_growth is not None:
            if earnings_growth >= 25:
                earnings_growth_score = 100
            elif earnings_growth >= 20:
                earnings_growth_score = 80
            elif earnings_growth >= 15:
                earnings_growth_score = 60
            elif earnings_growth >= 10:
                earnings_growth_score = 40
            else:
                earnings_growth_score = 20
        else:
            earnings_growth_score = 50
        
        components['earnings_growth'] = earnings_growth_score
        
        # FCF Growth (25% weight)
        fcf_growth = data.get('fcf_growth_yoy', None)
        if fcf_growth is not None:
            if fcf_growth >= 20:
                fcf_growth_score = 100
            elif fcf_growth >= 15:
                fcf_growth_score = 80
            elif fcf_growth >= 10:
                fcf_growth_score = 60
            elif fcf_growth >= 5:
                fcf_growth_score = 40
            else:
                fcf_growth_score = 20
        else:
            fcf_growth_score = 50
        
        components['fcf_growth'] = fcf_growth_score
        
        # Calculate weighted average
        growth = (
            revenue_growth_score * 0.40 +
            earnings_growth_score * 0.35 +
            fcf_growth_score * 0.25
        )
        
        return growth, components
    
    def calculate_value_investment_score(self, data: Dict[str, Any], current_price: float) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Value Investment Score (0-100)
        Components: PE Ratio (25%), PB Ratio (25%), PEG Ratio (20%), Graham Number (15%), EV/EBITDA (15%)
        """
        components = {}
        
        # PE Ratio (25% weight) - Enhanced granular scoring for better differentiation
        pe_ratio = data.get('pe_ratio', None)
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio <= 5:  # Extremely undervalued
                pe_score = 100
            elif pe_ratio <= 8:  # Very undervalued
                pe_score = 95
            elif pe_ratio <= 12:  # Undervalued
                pe_score = 85
            elif pe_ratio <= 15:  # Fair value
                pe_score = 70
            elif pe_ratio <= 18:  # Slightly overvalued
                pe_score = 55
            elif pe_ratio <= 22:  # Overvalued
                pe_score = 40
            elif pe_ratio <= 30:  # Very overvalued
                pe_score = 25
            elif pe_ratio <= 50:  # Extremely overvalued
                pe_score = 10
            else:  # Bubble territory
                pe_score = 0
        else:
            # If PE is missing, check if it's a profitable company
            net_income = data.get('net_income_ttm', None)
            if net_income is not None and net_income > 0:
                pe_score = 45  # Slightly below neutral for profitable companies without PE
            else:
                pe_score = 25  # Lower score for unprofitable companies
        
        components['pe_ratio'] = pe_score
        
        # PB Ratio (25% weight) - Enhanced granular scoring for better differentiation
        pb_ratio = data.get('pb_ratio', None)
        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio <= 0.3:  # Extremely undervalued
                pb_score = 100
            elif pb_ratio <= 0.5:  # Very undervalued
                pb_score = 95
            elif pb_ratio <= 0.8:  # Undervalued
                pb_score = 85
            elif pb_ratio <= 1.2:  # Fair value
                pb_score = 70
            elif pb_ratio <= 1.6:  # Slightly overvalued
                pb_score = 55
            elif pb_ratio <= 2.2:  # Overvalued
                pb_score = 40
            elif pb_ratio <= 3.5:  # Very overvalued
                pb_score = 25
            elif pb_ratio <= 6.0:  # Extremely overvalued
                pb_score = 10
            else:  # Bubble territory
                pb_score = 0
        else:
            # If PB is missing, check book value
            book_value = data.get('book_value_per_share', None)
            if book_value is not None and book_value > 0:
                pb_score = 45  # Slightly below neutral for companies with positive book value
            else:
                pb_score = 25  # Lower score for companies with negative book value
        
        components['pb_ratio'] = pb_score
        
        # PEG Ratio (20% weight) - More granular scoring
        peg_ratio = data.get('peg_ratio', None)
        if peg_ratio is not None and peg_ratio > 0:
            if peg_ratio <= 0.5:  # Very undervalued
                peg_score = 100
            elif peg_ratio <= 0.8:  # Undervalued
                peg_score = 90
            elif peg_ratio <= 1.0:  # Fair value
                peg_score = 75
            elif peg_ratio <= 1.3:  # Slightly overvalued
                peg_score = 60
            elif peg_ratio <= 1.8:  # Overvalued
                peg_score = 40
            elif peg_ratio <= 2.5:  # Very overvalued
                peg_score = 20
            else:  # Extremely overvalued
                peg_score = 0
        else:
            # If PEG is missing, check growth rates
            earnings_growth = data.get('earnings_growth_yoy', None)
            if earnings_growth is not None and earnings_growth > 15:
                peg_score = 60  # Higher score for high growth companies
            elif earnings_growth is not None and earnings_growth > 0:
                peg_score = 50  # Neutral for growing companies
            else:
                peg_score = 40  # Lower score for stagnant/declining companies
        
        components['peg_ratio'] = peg_score
        
        # Graham Number (15% weight) - More nuanced
        graham_number = data.get('graham_number', None)
        if graham_number is not None and current_price and graham_number > 0:
            price_vs_graham = current_price / graham_number
            if price_vs_graham <= 0.5:  # Very undervalued
                graham_score = 100
            elif price_vs_graham <= 0.7:  # Undervalued
                graham_score = 90
            elif price_vs_graham <= 0.85:  # Fair value
                graham_score = 75
            elif price_vs_graham <= 1.0:  # Slightly overvalued
                graham_score = 60
            elif price_vs_graham <= 1.3:  # Overvalued
                graham_score = 40
            elif price_vs_graham <= 1.8:  # Very overvalued
                graham_score = 20
            else:  # Extremely overvalued
                graham_score = 0
        else:
            # If Graham number is missing, check earnings and book value
            earnings = data.get('earnings_per_share', None)
            book_value = data.get('book_value_per_share', None)
            if earnings is not None and book_value is not None and earnings > 0 and book_value > 0:
                graham_score = 50  # Neutral for companies with positive earnings and book value
            else:
                graham_score = 30  # Lower score for companies without positive fundamentals
        
        components['graham_number'] = graham_score
        
        # EV/EBITDA (15% weight) - More granular scoring
        ev_ebitda = data.get('ev_ebitda_ratio', None)
        if ev_ebitda is not None and ev_ebitda > 0:
            if ev_ebitda <= 6:  # Very undervalued
                ev_ebitda_score = 100
            elif ev_ebitda <= 10:  # Undervalued
                ev_ebitda_score = 90
            elif ev_ebitda <= 14:  # Fair value
                ev_ebitda_score = 75
            elif ev_ebitda <= 18:  # Slightly overvalued
                ev_ebitda_score = 60
            elif ev_ebitda <= 25:  # Overvalued
                ev_ebitda_score = 40
            elif ev_ebitda <= 35:  # Very overvalued
                ev_ebitda_score = 20
            else:  # Extremely overvalued
                ev_ebitda_score = 0
        else:
            # If EV/EBITDA is missing, check EBITDA
            ebitda = data.get('ebitda', None)
            if ebitda is not None and ebitda > 0:
                ev_ebitda_score = 50  # Neutral for companies with positive EBITDA
            else:
                ev_ebitda_score = 30  # Lower score for companies without positive EBITDA
        
        components['ev_ebitda'] = ev_ebitda_score
        
        # Calculate weighted average
        value_score = (
            pe_score * 0.25 +
            pb_score * 0.25 +
            peg_score * 0.20 +
            graham_score * 0.15 +
            ev_ebitda_score * 0.15
        )
        
        return value_score, components
    
    def calculate_risk_assessment_score(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Enhanced Risk Assessment Score (0-100, higher = more risk)
        New Components: 
        - Valuation Risk (25%): PE, PB ratios, market cap vs fundamentals
        - Debt Risk (20%): Debt-to-equity, interest coverage
        - Liquidity Risk (15%): Current ratio, quick ratio
        - Profitability Risk (15%): ROE, ROA, margins
        - Growth Risk (15%): Revenue growth, earnings growth
        - Volatility Risk (10%): Sector volatility, growth stock characteristics
        """
        components = {}
        
        # Get additional data for enhanced assessment
        ticker = data.get('ticker', '')
        market_cap = data.get('market_cap', 0)
        sector = data.get('sector', '')
        
        # 1. Valuation Risk (25% weight)
        pe_ratio = data.get('pe_ratio', None)
        pb_ratio = data.get('pb_ratio', None)
        
        valuation_risk = 0
        if pe_ratio is not None:
            if pe_ratio > 50:
                valuation_risk = 100
            elif pe_ratio > 30:
                valuation_risk = 80
            elif pe_ratio > 20:
                valuation_risk = 60
            elif pe_ratio > 15:
                valuation_risk = 40
            elif pe_ratio > 10:
                valuation_risk = 20
            else:
                valuation_risk = 0
        else:
            # If PE is missing, check if it's a growth stock by sector/market cap
            if sector in ['Technology', 'Consumer Cyclical'] and market_cap > 10000000000:  # > $10B
                valuation_risk = 70  # Assume high PE for large tech/growth stocks
            else:
                valuation_risk = 50
        
        # Add PB ratio consideration
        if pb_ratio is not None and pb_ratio > 10:
            valuation_risk = min(100, valuation_risk + 20)
        
        components['valuation_risk'] = valuation_risk
        
        # 2. Debt Risk (20% weight)
        debt_equity = data.get('debt_to_equity', None)
        if debt_equity is not None:
            if debt_equity <= 0.3:
                debt_risk = 0
            elif debt_equity <= 0.5:
                debt_risk = 20
            elif debt_equity <= 1.0:
                debt_risk = 40
            elif debt_equity <= 1.5:
                debt_risk = 60
            else:
                debt_risk = 80
        else:
            debt_risk = 40
        
        components['debt_risk'] = debt_risk
        
        # 3. Liquidity Risk (15% weight)
        current_ratio = data.get('current_ratio', None)
        if current_ratio is not None:
            if current_ratio >= 2.0:
                liquidity_risk = 0
            elif current_ratio >= 1.5:
                liquidity_risk = 20
            elif current_ratio >= 1.0:
                liquidity_risk = 40
            elif current_ratio >= 0.8:
                liquidity_risk = 60
            else:
                liquidity_risk = 80
        else:
            liquidity_risk = 40
        
        components['liquidity_risk'] = liquidity_risk
        
        # 4. Profitability Risk (15% weight)
        roe = data.get('roe', None)
        if roe is not None:
            if roe >= 20:
                profitability_risk = 0
            elif roe >= 15:
                profitability_risk = 20
            elif roe >= 10:
                profitability_risk = 40
            elif roe >= 5:
                profitability_risk = 60
            elif roe >= 0:
                profitability_risk = 80
            else:
                profitability_risk = 100
        else:
            profitability_risk = 50
        
        components['profitability_risk'] = profitability_risk
        
        # 5. Growth Risk (15% weight)
        revenue_growth = data.get('revenue_growth_yoy', 0) or 0
        if revenue_growth < -10:
            growth_risk = 100
        elif revenue_growth < -5:
            growth_risk = 80
        elif revenue_growth < 0:
            growth_risk = 60
        elif revenue_growth < 5:
            growth_risk = 40
        elif revenue_growth < 15:
            growth_risk = 20
        else:
            growth_risk = 0
        
        components['growth_risk'] = growth_risk
        
        # 6. Volatility Risk (10% weight)
        volatility_risk = 0
        
        # High volatility sectors
        if sector in ['Technology', 'Consumer Cyclical', 'Communication Services']:
            volatility_risk += 30
        
        # Large market cap growth stocks
        if market_cap and market_cap > 100000000000:  # > $100B
            volatility_risk += 20
        elif market_cap and market_cap > 10000000000:  # > $10B
            volatility_risk += 10
        
        # High PE stocks (even if PE is missing, assume high for large tech)
        if pe_ratio is None and sector in ['Technology', 'Consumer Cyclical'] and market_cap and market_cap > 10000000000:
            volatility_risk += 20
        elif pe_ratio is not None and pe_ratio > 30:
            volatility_risk += 30
        elif pe_ratio is not None and pe_ratio > 20:
            volatility_risk += 20
        
        volatility_risk = min(100, volatility_risk)
        components['volatility_risk'] = volatility_risk
        
        # Calculate weighted score
        risk_score = (
            valuation_risk * 0.25 +
            debt_risk * 0.20 +
            liquidity_risk * 0.15 +
            profitability_risk * 0.15 +
            growth_risk * 0.15 +
            volatility_risk * 0.10
        )
        
        return risk_score, components
    
    def get_grade_from_score(self, score: float) -> str:
        """Convert score to grade"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        elif score >= 30:
            return 'D'
        else:
            return 'F'
    
    def get_value_rating(self, score: float) -> str:
        """Convert value score to rating"""
        if score >= 80:
            return 'Excellent Value'
        elif score >= 60:
            return 'Good Value'
        elif score >= 40:
            return 'Fair Value'
        elif score >= 20:
            return 'Overvalued'
        else:
            return 'Highly Overvalued'
    
    def get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score <= 20:
            return 'Low Risk'
        elif score <= 40:
            return 'Moderate Risk'
        elif score <= 60:
            return 'High Risk'
        elif score <= 80:
            return 'Very High Risk'
        else:
            return 'Extreme Risk'
    
    def detect_fundamental_alerts(self, data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Detect fundamental red and yellow flags"""
        red_flags = []
        yellow_flags = []
        
        # Red Flags
        debt_equity = data.get('debt_to_equity', None)
        if debt_equity and debt_equity > 2.0:
            red_flags.append(f"High debt-to-equity ratio ({debt_equity:.2f})")
        
        current_ratio = data.get('current_ratio', None)
        if current_ratio and current_ratio < 1.0:
            red_flags.append(f"Low current ratio ({current_ratio:.2f})")
        
        roe = data.get('roe', None)
        if roe and roe < 0:
            red_flags.append(f"Negative ROE ({roe:.1f}%)")
        
        revenue_growth = data.get('revenue_growth_yoy', None)
        if revenue_growth and revenue_growth < -10:
            red_flags.append(f"Declining revenue growth ({revenue_growth:.1f}%)")
        
        # Yellow Flags
        if debt_equity and debt_equity > 1.5:
            yellow_flags.append(f"Elevated debt-to-equity ratio ({debt_equity:.2f})")
        
        if current_ratio and current_ratio < 1.5:
            yellow_flags.append(f"Below-average current ratio ({current_ratio:.2f})")
        
        if roe and roe < 5:
            yellow_flags.append(f"Low ROE ({roe:.1f}%)")
        
        if revenue_growth and revenue_growth < 0:
            yellow_flags.append(f"Declining revenue growth ({revenue_growth:.1f}%)")
        
        return red_flags, yellow_flags
    
    def calculate_fundamental_scores(self, ticker: str) -> Dict[str, Any]:
        """
        Calculate all fundamental scores for a ticker
        """
        logger.info(f"Calculating fundamental scores for {ticker}")
        
        # Get fundamental data
        data = self.get_fundamental_data(ticker)
        if not data:
            logger.warning(f"No fundamental data available for {ticker}")
            return {}
        
        # Get current price
        current_price = self.get_current_price(ticker)
        if not current_price:
            logger.warning(f"No current price available for {ticker}")
            return {}
        
        # Calculate Fundamental Health Score
        financial_health, financial_health_components = self.calculate_financial_health_component(data)
        profitability, profitability_components = self.calculate_profitability_component(data)
        quality, quality_components = self.calculate_quality_component(data)
        growth, growth_components = self.calculate_growth_component(data)
        
        fundamental_health_score = (
            financial_health * 0.40 +
            profitability * 0.30 +
            quality * 0.20 +
            growth * 0.10
        )
        
        # Apply 5-level normalization
        fundamental_health_normalized = self.normalize_score_to_5_levels(fundamental_health_score, 'fundamental_health')
        
        # Calculate Value Investment Score
        value_score, value_components = self.calculate_value_investment_score(data, current_price)
        value_normalized = self.normalize_score_to_5_levels(value_score, 'value_investment')
        
        # Calculate Risk Assessment Score
        risk_score, risk_components = self.calculate_risk_assessment_score(data)
        risk_normalized = self.normalize_score_to_5_levels(risk_score, 'risk_assessment')
        
        # Detect alerts
        red_flags, yellow_flags = self.detect_fundamental_alerts(data)
        
        # Compile results
        results = {
            'ticker': ticker,
            'fundamental_health_score': round(fundamental_health_score, 2),
            'fundamental_health_normalized': fundamental_health_normalized['normalized_score'],
            'fundamental_health_grade': fundamental_health_normalized['grade'],
            'fundamental_health_description': fundamental_health_normalized['description'],
            'fundamental_health_components': {
                'financial_health': round(financial_health, 2),
                'profitability': round(profitability, 2),
                'quality': round(quality, 2),
                'growth': round(growth, 2),
                'components': {
                    'financial_health': financial_health_components,
                    'profitability': profitability_components,
                    'quality': quality_components,
                    'growth': growth_components
                }
            },
            'value_investment_score': round(value_score, 2),
            'value_investment_normalized': value_normalized['normalized_score'],
            'value_rating': value_normalized['grade'],
            'value_description': value_normalized['description'],
            'value_components': value_components,
            'fundamental_risk_score': round(risk_score, 2),
            'fundamental_risk_normalized': risk_normalized['normalized_score'],
            'fundamental_risk_level': risk_normalized['grade'],
            'fundamental_risk_description': risk_normalized['description'],
            'fundamental_risk_components': risk_components,
            'fundamental_red_flags': red_flags,
            'fundamental_yellow_flags': yellow_flags,
            'data_used': list(data.keys())
        }
        
        logger.info(f"Fundamental scores calculated for {ticker}: Health={fundamental_health_score:.1f}, Value={value_score:.1f}, Risk={risk_score:.1f}")
        
        return results
    
    def store_fundamental_scores(self, ticker: str, scores: Dict[str, Any], 
                               technical_scores: Dict[str, Any] = None) -> bool:
        """
        Store fundamental scores in database using upsert function
        """
        try:
            # Prepare technical scores (placeholder if not provided)
            if not technical_scores:
                technical_scores = {
                    'technical_health_score': 50.0,
                    'technical_health_grade': 'C',
                    'technical_health_components': {},
                    'trading_signal_score': 50.0,
                    'trading_signal_rating': 'Neutral',
                    'trading_signal_components': {},
                    'technical_risk_score': 50.0,
                    'technical_risk_level': 'Moderate Risk',
                    'technical_risk_components': {},
                    'technical_red_flags': [],
                    'technical_yellow_flags': []
                }
            
            # Calculate overall score (simple average for now)
            overall_score = (
                scores['fundamental_health_score'] + 
                technical_scores['technical_health_score']
            ) / 2
            overall_grade = self.get_grade_from_score(overall_score)
            
            # Use a separate connection without RealDictCursor for the function call
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'ourstox6'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD')
            )
            
            with conn.cursor() as cursor:
                # Insert into historical table
                historical_query = """
                INSERT INTO company_scores_historical (
                    ticker, date_calculated,
                    fundamental_health_score, fundamental_health_grade, fundamental_health_components,
                    fundamental_risk_score, fundamental_risk_level, fundamental_risk_components,
                    value_investment_score, value_rating, value_components,
                    technical_health_score, technical_health_grade, technical_health_components,
                    trading_signal_score, trading_signal_rating, trading_signal_components,
                    technical_risk_score, technical_risk_level, technical_risk_components,
                    overall_score, overall_grade,
                    fundamental_red_flags, fundamental_yellow_flags,
                    technical_red_flags, technical_yellow_flags
                ) VALUES (
                    %s, CURRENT_DATE,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s
                )
                ON CONFLICT (ticker, date_calculated) DO UPDATE SET
                    fundamental_health_score = EXCLUDED.fundamental_health_score,
                    fundamental_health_grade = EXCLUDED.fundamental_health_grade,
                    fundamental_health_components = EXCLUDED.fundamental_health_components,
                    fundamental_risk_score = EXCLUDED.fundamental_risk_score,
                    fundamental_risk_level = EXCLUDED.fundamental_risk_level,
                    fundamental_risk_components = EXCLUDED.fundamental_risk_components,
                    value_investment_score = EXCLUDED.value_investment_score,
                    value_rating = EXCLUDED.value_rating,
                    value_components = EXCLUDED.value_components,
                    technical_health_score = EXCLUDED.technical_health_score,
                    technical_health_grade = EXCLUDED.technical_health_grade,
                    technical_health_components = EXCLUDED.technical_health_components,
                    trading_signal_score = EXCLUDED.trading_signal_score,
                    trading_signal_rating = EXCLUDED.trading_signal_rating,
                    trading_signal_components = EXCLUDED.trading_signal_components,
                    technical_risk_score = EXCLUDED.technical_risk_score,
                    technical_risk_level = EXCLUDED.technical_risk_level,
                    technical_risk_components = EXCLUDED.technical_risk_components,
                    overall_score = EXCLUDED.overall_score,
                    overall_grade = EXCLUDED.overall_grade,
                    fundamental_red_flags = EXCLUDED.fundamental_red_flags,
                    fundamental_yellow_flags = EXCLUDED.fundamental_yellow_flags,
                    technical_red_flags = EXCLUDED.technical_red_flags,
                    technical_yellow_flags = EXCLUDED.technical_yellow_flags,
                    created_at = CURRENT_TIMESTAMP
                """
                
                # Update current table
                current_query = """
                UPDATE company_scores_current SET
                    date_calculated = CURRENT_DATE,
                    fundamental_health_score = %s,
                    fundamental_health_grade = %s,
                    fundamental_health_components = %s,
                    fundamental_risk_score = %s,
                    fundamental_risk_level = %s,
                    fundamental_risk_components = %s,
                    value_investment_score = %s,
                    value_rating = %s,
                    value_components = %s,
                    technical_health_score = %s,
                    technical_health_grade = %s,
                    technical_health_components = %s,
                    trading_signal_score = %s,
                    trading_signal_rating = %s,
                    trading_signal_components = %s,
                    technical_risk_score = %s,
                    technical_risk_level = %s,
                    technical_risk_components = %s,
                    overall_score = %s,
                    overall_grade = %s,
                    fundamental_red_flags = %s,
                    fundamental_yellow_flags = %s,
                    technical_red_flags = %s,
                    technical_yellow_flags = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ticker = %s
                """
                
                # Prepare parameters for historical insert
                historical_params = (
                    ticker,
                    scores['fundamental_health_score'],
                    scores['fundamental_health_grade'],
                    json.dumps(scores['fundamental_health_components']),
                    scores['fundamental_risk_score'],
                    scores['fundamental_risk_level'],
                    json.dumps(scores['fundamental_risk_components']),
                    scores['value_investment_score'],
                    scores['value_rating'],
                    json.dumps(scores['value_components']),
                    technical_scores['technical_health_score'],
                    technical_scores['technical_health_grade'],
                    json.dumps(technical_scores['technical_health_components']),
                    technical_scores['trading_signal_score'],
                    technical_scores['trading_signal_rating'],
                    json.dumps(technical_scores['trading_signal_components']),
                    technical_scores['technical_risk_score'],
                    technical_scores['technical_risk_level'],
                    json.dumps(technical_scores['technical_risk_components']),
                    overall_score,
                    overall_grade,
                    json.dumps(scores['fundamental_red_flags']),
                    json.dumps(scores['fundamental_yellow_flags']),
                    json.dumps(technical_scores['technical_red_flags']),
                    json.dumps(technical_scores['technical_yellow_flags'])
                )
                
                # Prepare parameters for current update
                current_params = (
                    scores['fundamental_health_score'],
                    scores['fundamental_health_grade'],
                    json.dumps(scores['fundamental_health_components']),
                    scores['fundamental_risk_score'],
                    scores['fundamental_risk_level'],
                    json.dumps(scores['fundamental_risk_components']),
                    scores['value_investment_score'],
                    scores['value_rating'],
                    json.dumps(scores['value_components']),
                    technical_scores['technical_health_score'],
                    technical_scores['technical_health_grade'],
                    json.dumps(technical_scores['technical_health_components']),
                    technical_scores['trading_signal_score'],
                    technical_scores['trading_signal_rating'],
                    json.dumps(technical_scores['trading_signal_components']),
                    technical_scores['technical_risk_score'],
                    technical_scores['technical_risk_level'],
                    json.dumps(technical_scores['technical_risk_components']),
                    overall_score,
                    overall_grade,
                    json.dumps(scores['fundamental_red_flags']),
                    json.dumps(scores['fundamental_yellow_flags']),
                    json.dumps(technical_scores['technical_red_flags']),
                    json.dumps(technical_scores['technical_yellow_flags']),
                    ticker
                )
                
                logger.info(f"Debug: Inserting historical data for {ticker}")
                
                try:
                    # Insert into historical table
                    cursor.execute(historical_query, historical_params)
                    logger.info(f"Historical data inserted for {ticker}")
                    
                    # Update current table
                    cursor.execute(current_query, current_params)
                    logger.info(f"Current data updated for {ticker}")
                    
                    # If no rows updated, insert new record
                    if cursor.rowcount == 0:
                        insert_current_query = """
                        INSERT INTO company_scores_current (
                            ticker, date_calculated,
                            fundamental_health_score, fundamental_health_grade, fundamental_health_components,
                            fundamental_risk_score, fundamental_risk_level, fundamental_risk_components,
                            value_investment_score, value_rating, value_components,
                            technical_health_score, technical_health_grade, technical_health_components,
                            trading_signal_score, trading_signal_rating, trading_signal_components,
                            technical_risk_score, technical_risk_level, technical_risk_components,
                            overall_score, overall_grade,
                            fundamental_red_flags, fundamental_yellow_flags,
                            technical_red_flags, technical_yellow_flags
                        ) VALUES (
                            %s, CURRENT_DATE,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s
                        )
                        """
                        cursor.execute(insert_current_query, historical_params)
                        logger.info(f"Current data inserted for {ticker}")
                    
                    conn.commit()
                    logger.info(f"Transaction committed for {ticker}")
                    logger.info(f"Fundamental scores stored for {ticker}")
                    return True
                    
                except Exception as execute_error:
                    logger.error(f"Error during database operations for {ticker}: {execute_error}")
                    import traceback
                    traceback.print_exc()
                    return False
                    
        except Exception as e:
            logger.error(f"Error storing fundamental scores for {ticker}: {e}")
            return False
    
    def calculate_scores_for_tickers(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Calculate fundamental scores for multiple tickers
        """
        results = {
            'successful': [],
            'failed': [],
            'summary': {}
        }
        
        start_time = time.time()
        
        for ticker in tickers:
            try:
                scores = self.calculate_fundamental_scores(ticker)
                if scores:
                    # Store in database
                    if self.store_fundamental_scores(ticker, scores):
                        results['successful'].append({
                            'ticker': ticker,
                            'scores': scores
                        })
                    else:
                        results['failed'].append(ticker)
                else:
                    results['failed'].append(ticker)
                    
            except Exception as e:
                logger.error(f"Error calculating scores for {ticker}: {e}")
                results['failed'].append(ticker)
        
        # Calculate summary
        total_time = time.time() - start_time
        results['summary'] = {
            'total_tickers': len(tickers),
            'successful': len(results['successful']),
            'failed': len(results['failed']),
            'success_rate': len(results['successful']) / len(tickers) * 100,
            'total_time_seconds': round(total_time, 2),
            'average_time_per_ticker': round(total_time / len(tickers), 3)
        }
        
        return results

def main():
    """Main function for testing"""
    calculator = FundamentalScoreCalculator()
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
    
    print("🧪 Testing Fundamental Score Calculator")
    print("=" * 50)
    
    results = calculator.calculate_scores_for_tickers(test_tickers)
    
    print(f"\n📊 Results Summary:")
    print(f"Total tickers: {results['summary']['total_tickers']}")
    print(f"Successful: {results['summary']['successful']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Success rate: {results['summary']['success_rate']:.1f}%")
    print(f"Total time: {results['summary']['total_time_seconds']}s")
    print(f"Average time per ticker: {results['summary']['average_time_per_ticker']}s")
    
    print(f"\n✅ Successful Calculations:")
    for result in results['successful']:
        ticker = result['ticker']
        scores = result['scores']
        print(f"  {ticker}: Health={scores['fundamental_health_score']:.1f} ({scores['fundamental_health_grade']}), "
              f"Value={scores['value_investment_score']:.1f} ({scores['value_rating']}), "
              f"Risk={scores['fundamental_risk_score']:.1f} ({scores['fundamental_risk_level']})")
    
    if results['failed']:
        print(f"\n❌ Failed Calculations:")
        for ticker in results['failed']:
            print(f"  {ticker}")

if __name__ == "__main__":
    main() 