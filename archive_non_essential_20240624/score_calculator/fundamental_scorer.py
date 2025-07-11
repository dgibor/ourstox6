"""
Fundamental Scorer

Calculates fundamental scores using existing ratios from financial_ratios table
and applies FUND-DASH scoring logic for different investor types.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import date
from ..database import DatabaseManager
from .database_manager import ScoreDatabaseManager

logger = logging.getLogger(__name__)


class FundamentalScorer:
    """Calculates fundamental scores using existing financial ratios"""
    
    def __init__(self, db: DatabaseManager = None, score_db: ScoreDatabaseManager = None):
        self.db = db or DatabaseManager()
        self.score_db = score_db or ScoreDatabaseManager(db)
        
        # FUND-DASH scoring weights (from Value-dash-2.md)
        self.card_weights = {
            'valuation': 0.20,      # Card 1: Valuation & Income
            'quality': 0.20,        # Card 2: Quality & Profitability  
            'growth': 0.20,         # Card 3: Growth Momentum
            'financial_health': 0.20, # Card 4: Financial Strength
            'moat': 0.10,           # Card 5: Moat & Competitive Position
            'risk': 0.10            # Card 6: Risk Flags
        }
        
        # Investor type weights (from FUND-DASH spec)
        self.investor_weights = {
            'conservative': {
                'valuation': 0.30,
                'quality': 0.15,
                'growth': 0.10,
                'financial_health': 0.30,
                'moat': 0.10,
                'risk': 0.05
            },
            'garp': {
                'valuation': 0.20,
                'quality': 0.20,
                'growth': 0.20,
                'financial_health': 0.20,
                'moat': 0.10,
                'risk': 0.10
            },
            'deep_value': {
                'valuation': 0.40,
                'quality': 0.10,
                'growth': 0.05,
                'financial_health': 0.35,
                'moat': 0.05,
                'risk': 0.05
            }
        }
    
    def get_latest_ratios(self, ticker: str) -> Optional[Dict]:
        """Get latest financial ratios, preferring company_fundamentals, fallback to financial_ratios"""
        try:
            # 1. Try company_fundamentals first
            query_cf = """
            SELECT last_updated, price_to_earnings, price_to_book, price_to_sales, ev_to_ebitda, peg_ratio,
                   return_on_equity, return_on_assets, return_on_invested_capital, gross_margin, operating_margin, net_margin,
                   debt_to_equity_ratio, current_ratio, quick_ratio, interest_coverage, altman_z_score,
                   asset_turnover, inventory_turnover, receivables_turnover,
                   revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
                   fcf_to_net_income, cash_conversion_cycle, market_cap, enterprise_value,
                   graham_number
            FROM company_fundamentals
            WHERE ticker = %s
            ORDER BY last_updated DESC
            LIMIT 1
            """
            result = self.db.execute_query(query_cf, (ticker,))
            if result:
                row = result[0]
                # Map company_fundamentals columns to expected keys
                return {
                    'calculation_date': row[0],
                    'pe_ratio': row[1],
                    'pb_ratio': row[2],
                    'ps_ratio': row[3],
                    'ev_ebitda': row[4],
                    'peg_ratio': row[5],
                    'roe': row[6],
                    'roa': row[7],
                    'roic': row[8],
                    'gross_margin': row[9],
                    'operating_margin': row[10],
                    'net_margin': row[11],
                    'debt_to_equity': row[12],
                    'current_ratio': row[13],
                    'quick_ratio': row[14],
                    'interest_coverage': row[15],
                    'altman_z_score': row[16],
                    'asset_turnover': row[17],
                    'inventory_turnover': row[18],
                    'receivables_turnover': row[19],
                    'revenue_growth_yoy': row[20],
                    'earnings_growth_yoy': row[21],
                    'fcf_growth_yoy': row[22],
                    'fcf_to_net_income': row[23],
                    'cash_conversion_cycle': row[24],
                    'market_cap': row[25],
                    'enterprise_value': row[26],
                    'graham_number': row[27]
                }
            # 2. Fallback to financial_ratios if no data in company_fundamentals
            query_fr = """
            SELECT 
                calculation_date, pe_ratio, pb_ratio, ps_ratio, ev_ebitda, peg_ratio,
                roe, roa, roic, gross_margin, operating_margin, net_margin,
                debt_to_equity, current_ratio, quick_ratio, interest_coverage, altman_z_score,
                asset_turnover, inventory_turnover, receivables_turnover,
                revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
                fcf_to_net_income, cash_conversion_cycle, market_cap, enterprise_value,
                graham_number
            FROM financial_ratios 
            WHERE ticker = %s 
            ORDER BY calculation_date DESC 
            LIMIT 1
            """
            result = self.db.execute_query(query_fr, (ticker,))
            if not result:
                return None
            row = result[0]
            return {
                'calculation_date': row[0],
                'pe_ratio': row[1],
                'pb_ratio': row[2],
                'ps_ratio': row[3],
                'ev_ebitda': row[4],
                'peg_ratio': row[5],
                'roe': row[6],
                'roa': row[7],
                'roic': row[8],
                'gross_margin': row[9],
                'operating_margin': row[10],
                'net_margin': row[11],
                'debt_to_equity': row[12],
                'current_ratio': row[13],
                'quick_ratio': row[14],
                'interest_coverage': row[15],
                'altman_z_score': row[16],
                'asset_turnover': row[17],
                'inventory_turnover': row[18],
                'receivables_turnover': row[19],
                'revenue_growth_yoy': row[20],
                'earnings_growth_yoy': row[21],
                'fcf_growth_yoy': row[22],
                'fcf_to_net_income': row[23],
                'cash_conversion_cycle': row[24],
                'market_cap': row[25],
                'enterprise_value': row[26],
                'graham_number': row[27]
            }
        except Exception as e:
            logger.error(f"Error getting ratios for {ticker}: {e}")
            return None
    
    def get_sector_info(self, ticker: str) -> Tuple[str, str]:
        """Get sector and industry information for a ticker"""
        try:
            query = """
            SELECT sector, industry 
            FROM stocks 
            WHERE ticker = %s
            """
            
            result = self.db.execute_query(query, (ticker,))
            if result:
                return result[0][0] or 'Unknown', result[0][1] or 'Unknown'
            return 'Unknown', 'Unknown'
            
        except Exception as e:
            logger.error(f"Error getting sector info for {ticker}: {e}")
            return 'Unknown', 'Unknown'
    
    def get_sector_thresholds(self, sector: str, industry: str) -> Dict:
        """Get sector-specific thresholds for scoring"""
        try:
            query = """
            SELECT * FROM sector_thresholds 
            WHERE sector = %s AND industry = %s
            """
            
            result = self.db.execute_query(query, (sector, industry))
            if result:
                # Return thresholds if available
                return dict(zip([col[0] for col in self.db.cursor.description], result[0]))
            
            # Return default thresholds if not available
            return self._get_default_thresholds()
            
        except Exception as e:
            logger.error(f"Error getting sector thresholds: {e}")
            return self._get_default_thresholds()
    
    def _get_default_thresholds(self) -> Dict:
        """Get default scoring thresholds"""
        return {
            'pe_ratio_good_threshold': 15,
            'pe_ratio_bad_threshold': 25,
            'pb_ratio_good_threshold': 1.5,
            'pb_ratio_bad_threshold': 3.0,
            'roe_good_threshold': 15,
            'roe_bad_threshold': 8,
            'debt_equity_good_threshold': 0.5,
            'debt_equity_bad_threshold': 1.0,
            'current_ratio_good_threshold': 1.5,
            'current_ratio_bad_threshold': 1.0,
            'altman_z_good_threshold': 2.5,
            'altman_z_bad_threshold': 1.8,
            'revenue_growth_good_threshold': 10,
            'revenue_growth_bad_threshold': 0,
            'earnings_growth_good_threshold': 10,
            'earnings_growth_bad_threshold': 0
        }
    
    def calculate_valuation_score(self, ratios: Dict, thresholds: Dict) -> int:
        """Calculate valuation score (0-100)"""
        try:
            score = 0
            factors = 0
            
            # P/E Ratio scoring
            pe_ratio = ratios.get('pe_ratio')
            if pe_ratio and pe_ratio > 0:
                factors += 1
                if pe_ratio <= thresholds['pe_ratio_good_threshold']:
                    score += 100
                elif pe_ratio <= thresholds['pe_ratio_bad_threshold']:
                    score += 60
                else:
                    score += 20
            
            # P/B Ratio scoring
            pb_ratio = ratios.get('pb_ratio')
            if pb_ratio and pb_ratio > 0:
                factors += 1
                if pb_ratio <= thresholds['pb_ratio_good_threshold']:
                    score += 100
                elif pb_ratio <= thresholds['pb_ratio_bad_threshold']:
                    score += 60
                else:
                    score += 20
            
            # EV/EBITDA scoring
            ev_ebitda = ratios.get('ev_ebitda')
            if ev_ebitda and ev_ebitda > 0:
                factors += 1
                if ev_ebitda <= 10:
                    score += 100
                elif ev_ebitda <= 15:
                    score += 60
                else:
                    score += 20
            
            # P/S Ratio scoring (if available)
            ps_ratio = ratios.get('ps_ratio')
            if ps_ratio and ps_ratio > 0:
                factors += 1
                if ps_ratio <= 2:
                    score += 100
                elif ps_ratio <= 4:
                    score += 60
                else:
                    score += 20
            
            return int(score / factors) if factors > 0 else 50
            
        except Exception as e:
            logger.error(f"Error calculating valuation score: {e}")
            return 50
    
    def calculate_quality_score(self, ratios: Dict) -> int:
        """Calculate quality score (0-100)"""
        try:
            score = 0
            factors = 0
            
            # ROE scoring
            roe = ratios.get('roe')
            if roe is not None:
                factors += 1
                if roe >= 20:
                    score += 100
                elif roe >= 15:
                    score += 80
                elif roe >= 10:
                    score += 60
                elif roe >= 5:
                    score += 40
                else:
                    score += 20
            
            # ROIC scoring
            roic = ratios.get('roic')
            if roic is not None:
                factors += 1
                if roic >= 20:
                    score += 100
                elif roic >= 15:
                    score += 80
                elif roic >= 10:
                    score += 60
                elif roic >= 5:
                    score += 40
                else:
                    score += 20
            
            # Gross Margin scoring
            gross_margin = ratios.get('gross_margin')
            if gross_margin is not None:
                factors += 1
                if gross_margin >= 50:
                    score += 100
                elif gross_margin >= 30:
                    score += 80
                elif gross_margin >= 20:
                    score += 60
                elif gross_margin >= 10:
                    score += 40
                else:
                    score += 20
            
            # Operating Margin scoring
            operating_margin = ratios.get('operating_margin')
            if operating_margin is not None:
                factors += 1
                if operating_margin >= 20:
                    score += 100
                elif operating_margin >= 15:
                    score += 80
                elif operating_margin >= 10:
                    score += 60
                elif operating_margin >= 5:
                    score += 40
                else:
                    score += 20
            
            return int(score / factors) if factors > 0 else 50
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 50
    
    def calculate_growth_score(self, ratios: Dict, thresholds: Dict) -> int:
        """Calculate growth score (0-100)"""
        try:
            score = 0
            factors = 0
            
            # Revenue Growth scoring
            revenue_growth = ratios.get('revenue_growth_yoy')
            if revenue_growth is not None:
                factors += 1
                if revenue_growth >= thresholds['revenue_growth_good_threshold']:
                    score += 100
                elif revenue_growth >= thresholds['revenue_growth_bad_threshold']:
                    score += 60
                else:
                    score += 20
            
            # Earnings Growth scoring
            earnings_growth = ratios.get('earnings_growth_yoy')
            if earnings_growth is not None:
                factors += 1
                if earnings_growth >= thresholds['earnings_growth_good_threshold']:
                    score += 100
                elif earnings_growth >= thresholds['earnings_growth_bad_threshold']:
                    score += 60
                else:
                    score += 20
            
            # FCF Growth scoring
            fcf_growth = ratios.get('fcf_growth_yoy')
            if fcf_growth is not None:
                factors += 1
                if fcf_growth >= 10:
                    score += 100
                elif fcf_growth >= 0:
                    score += 60
                else:
                    score += 20
            
            return int(score / factors) if factors > 0 else 50
            
        except Exception as e:
            logger.error(f"Error calculating growth score: {e}")
            return 50
    
    def calculate_financial_health_score(self, ratios: Dict, thresholds: Dict) -> int:
        """Calculate financial health score (0-100)"""
        try:
            score = 0
            factors = 0
            
            # Debt to Equity scoring
            debt_equity = ratios.get('debt_to_equity')
            if debt_equity is not None:
                factors += 1
                if debt_equity <= thresholds['debt_equity_good_threshold']:
                    score += 100
                elif debt_equity <= thresholds['debt_equity_bad_threshold']:
                    score += 60
                else:
                    score += 20
            
            # Current Ratio scoring
            current_ratio = ratios.get('current_ratio')
            if current_ratio is not None:
                factors += 1
                if current_ratio >= thresholds['current_ratio_good_threshold']:
                    score += 100
                elif current_ratio >= thresholds['current_ratio_bad_threshold']:
                    score += 60
                else:
                    score += 20
            
            # Altman Z-Score scoring
            altman_z = ratios.get('altman_z_score')
            if altman_z is not None:
                factors += 1
                if altman_z >= thresholds['altman_z_good_threshold']:
                    score += 100
                elif altman_z >= thresholds['altman_z_bad_threshold']:
                    score += 60
                else:
                    score += 20
            
            # Interest Coverage scoring
            interest_coverage = ratios.get('interest_coverage')
            if interest_coverage is not None:
                factors += 1
                if interest_coverage >= 5:
                    score += 100
                elif interest_coverage >= 3:
                    score += 80
                elif interest_coverage >= 2:
                    score += 60
                elif interest_coverage >= 1:
                    score += 40
                else:
                    score += 20
            
            return int(score / factors) if factors > 0 else 50
            
        except Exception as e:
            logger.error(f"Error calculating financial health score: {e}")
            return 50
    
    def calculate_management_score(self, ratios: Dict) -> int:
        """Calculate management score (0-100)"""
        try:
            score = 0
            factors = 0
            
            # Asset Turnover scoring
            asset_turnover = ratios.get('asset_turnover')
            if asset_turnover is not None:
                factors += 1
                if asset_turnover >= 1.0:
                    score += 100
                elif asset_turnover >= 0.5:
                    score += 60
                else:
                    score += 20
            
            # FCF to Net Income scoring
            fcf_to_net_income = ratios.get('fcf_to_net_income')
            if fcf_to_net_income is not None:
                factors += 1
                if fcf_to_net_income >= 1.0:
                    score += 100
                elif fcf_to_net_income >= 0.8:
                    score += 80
                elif fcf_to_net_income >= 0.6:
                    score += 60
                else:
                    score += 20
            
            # Cash Conversion Cycle scoring (lower is better)
            ccc = ratios.get('cash_conversion_cycle')
            if ccc is not None:
                factors += 1
                if ccc <= 30:
                    score += 100
                elif ccc <= 60:
                    score += 80
                elif ccc <= 90:
                    score += 60
                else:
                    score += 20
            
            return int(score / factors) if factors > 0 else 50
            
        except Exception as e:
            logger.error(f"Error calculating management score: {e}")
            return 50
    
    def calculate_investor_scores(self, category_scores: Dict) -> Dict:
        """Calculate investor type composite scores"""
        try:
            investor_scores = {}
            
            for investor_type, weights in self.investor_weights.items():
                total_score = 0
                total_weight = 0
                
                for category, weight in weights.items():
                    category_score = category_scores.get(f'{category}_score', 50)
                    total_score += category_score * weight
                    total_weight += weight
                
                if total_weight > 0:
                    final_score = int(total_score / total_weight)
                    final_score = max(0, min(100, final_score))  # Clamp to 0-100
                else:
                    final_score = 50
                
                investor_scores[f'{investor_type}_investor_score'] = final_score
            
            return investor_scores
            
        except Exception as e:
            logger.error(f"Error calculating investor scores: {e}")
            return {
                'conservative_investor_score': 50,
                'garp_investor_score': 50,
                'deep_value_investor_score': 50
            }
    
    def calculate_data_quality_score(self, ratios: Dict) -> int:
        """Calculate data quality score based on available ratios"""
        try:
            required_ratios = [
                'pe_ratio', 'pb_ratio', 'roe', 'debt_to_equity', 'current_ratio',
                'revenue_growth_yoy', 'earnings_growth_yoy'
            ]
            
            available_count = 0
            for ratio in required_ratios:
                if ratios.get(ratio) is not None:
                    available_count += 1
            
            # Calculate percentage
            quality_score = int((available_count / len(required_ratios)) * 100)
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating data quality score: {e}")
            return 50
    
    def calculate_fundamental_score(self, ticker: str, calculation_date: date) -> Dict:
        """Calculate complete fundamental score for a ticker"""
        try:
            # Get latest ratios
            ratios = self.get_latest_ratios(ticker)
            if not ratios:
                return {
                    'calculation_status': 'failed',
                    'error_message': 'No ratio data available',
                    'data_quality_score': 0
                }
            
            # Get sector info and thresholds
            sector, industry = self.get_sector_info(ticker)
            thresholds = self.get_sector_thresholds(sector, industry)
            
            # Calculate category scores
            category_scores = {
                'valuation_score': self.calculate_valuation_score(ratios, thresholds),
                'quality_score': self.calculate_quality_score(ratios),
                'growth_score': self.calculate_growth_score(ratios, thresholds),
                'financial_health_score': self.calculate_financial_health_score(ratios, thresholds),
                'management_score': self.calculate_management_score(ratios)
            }
            
            # Add moat and risk scores (simplified for now)
            category_scores['moat_score'] = 50  # Placeholder
            category_scores['risk_score'] = 50  # Placeholder
            
            # Calculate investor type scores
            investor_scores = self.calculate_investor_scores(category_scores)
            
            # Calculate data quality score
            data_quality_score = self.calculate_data_quality_score(ratios)
            
            # Determine calculation status
            if data_quality_score >= 80:
                calculation_status = 'success'
            elif data_quality_score >= 50:
                calculation_status = 'partial'
            else:
                calculation_status = 'failed'
            
            # Compile final result
            result = {
                **category_scores,
                **investor_scores,
                'sector': sector,
                'industry': industry,
                'data_quality_score': data_quality_score,
                'calculation_status': calculation_status,
                'error_message': None
            }
            
            logger.info(f"Calculated fundamental score for {ticker}: {investor_scores}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score for {ticker}: {e}")
            return {
                'calculation_status': 'failed',
                'error_message': str(e),
                'data_quality_score': 0
            }
    
    def process_ticker(self, ticker: str, calculation_date: date) -> bool:
        """Process a single ticker and store the result"""
        try:
            # Calculate score
            score_data = self.calculate_fundamental_score(ticker, calculation_date)
            
            # Store in database
            success = self.score_db.store_fundamental_score(ticker, calculation_date, score_data)
            
            if success:
                logger.info(f"Stored fundamental score for {ticker}")
            else:
                logger.error(f"Failed to store fundamental score for {ticker}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing fundamental score for {ticker}: {e}")
            return False 