import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Tuple

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFundamentalScoreCalculatorV2:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        # Enhanced required metrics with weights
        self.REQUIRED_METRICS = {
            'pe_ratio': {'weight': 0.15, 'critical': True},
            'pb_ratio': {'weight': 0.12, 'critical': True},
            'roe': {'weight': 0.12, 'critical': True},
            'roa': {'weight': 0.10, 'critical': False},
            'debt_to_equity': {'weight': 0.10, 'critical': True},
            'current_ratio': {'weight': 0.08, 'critical': False},
            'ev_ebitda': {'weight': 0.10, 'critical': False},
            'gross_margin': {'weight': 0.08, 'critical': False},
            'operating_margin': {'weight': 0.08, 'critical': False},
            'net_margin': {'weight': 0.07, 'critical': False},
            'revenue_growth_yoy': {'weight': 0.05, 'critical': False},
            'earnings_growth_yoy': {'weight': 0.05, 'critical': False}
        }
        
        # Enhanced sector-specific ranges with growth adjustments
        self.SECTOR_RANGES = {
            'Technology': {
                'pe_ratio': (15, 80), 'pb_ratio': (3, 25), 'roe': (-30, 60),
                'roa': (-15, 35), 'debt_to_equity': (0, 1.2), 'ev_ebitda': (15, 60),
                'growth_multiplier': 1.3, 'risk_multiplier': 1.2
            },
            'Financial': {
                'pe_ratio': (8, 35), 'pb_ratio': (0.8, 4), 'roe': (-15, 35),
                'roa': (-8, 20), 'debt_to_equity': (0.8, 4), 'ev_ebitda': (8, 25),
                'growth_multiplier': 0.9, 'risk_multiplier': 1.1
            },
            'Healthcare': {
                'pe_ratio': (20, 100), 'pb_ratio': (4, 30), 'roe': (-40, 70),
                'roa': (-20, 40), 'debt_to_equity': (0, 2.5), 'ev_ebitda': (20, 70),
                'growth_multiplier': 1.2, 'risk_multiplier': 1.3
            },
            'Consumer Discretionary': {
                'pe_ratio': (12, 45), 'pb_ratio': (1.5, 15), 'roe': (-35, 45),
                'roa': (-15, 25), 'debt_to_equity': (0, 3), 'ev_ebitda': (10, 40),
                'growth_multiplier': 1.1, 'risk_multiplier': 1.0
            },
            'Energy': {
                'pe_ratio': (8, 30), 'pb_ratio': (0.8, 10), 'roa': (-50, 25),
                'roa': (-25, 20), 'debt_to_equity': (0, 2.5), 'ev_ebitda': (5, 20),
                'growth_multiplier': 0.8, 'risk_multiplier': 1.4
            },
            'default': {
                'pe_ratio': (8, 40), 'pb_ratio': (1, 12), 'roe': (-30, 45),
                'roa': (-15, 25), 'debt_to_equity': (0, 2.5), 'ev_ebitda': (8, 35),
                'growth_multiplier': 1.0, 'risk_multiplier': 1.0
            }
        }
        
        # Enhanced conservative defaults with sector adjustments
        self.CONSERVATIVE_DEFAULTS = {
            'pe_ratio': 20, 'pb_ratio': 2.5, 'roe': 12, 'roa': 6,
            'debt_to_equity': 0.6, 'current_ratio': 1.4, 'ev_ebitda': 12,
            'gross_margin': 35, 'operating_margin': 12, 'net_margin': 8,
            'revenue_growth_yoy': 6, 'earnings_growth_yoy': 5
        }

    def get_database_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )

    def enhanced_pe_ratio_estimation(self, fundamental_data, market_cap, sector, current_price):
        """Enhanced PE ratio estimation with multiple methods"""
        if fundamental_data.get('pe_ratio'):
            return fundamental_data['pe_ratio'], False, None
        
        # Method 1: Direct calculation from EPS
        if fundamental_data.get('earnings_per_share') and current_price:
            pe_ratio = current_price / fundamental_data['earnings_per_share']
            if 5 <= pe_ratio <= 100:  # Reasonable range
                return pe_ratio, False, None
        
        # Method 2: Calculate from net income and estimated shares
        if fundamental_data.get('net_income') and market_cap and current_price:
            estimated_shares = market_cap / current_price
            if estimated_shares > 0:
                pe_ratio = (current_price * estimated_shares) / fundamental_data['net_income']
                if 5 <= pe_ratio <= 100:
                    return pe_ratio, True, "PE estimated from net income and market cap"
        
        # Method 3: Sector-based estimation
        sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
        sector_pe_range = sector_ranges['pe_ratio']
        
        # Use sector median with growth adjustment
        sector_median = (sector_pe_range[0] + sector_pe_range[1]) / 2
        growth_multiplier = sector_ranges.get('growth_multiplier', 1.0)
        
        # Adjust based on revenue growth if available
        if fundamental_data.get('revenue_growth_yoy'):
            growth_adjustment = min(1.5, max(0.7, fundamental_data['revenue_growth_yoy'] / 10))
            estimated_pe = sector_median * growth_multiplier * growth_adjustment
        else:
            estimated_pe = sector_median * growth_multiplier
        
        return estimated_pe, True, "PE estimated using sector-based calculation"

    def enhanced_missing_ratios_calculation(self, fundamental_data, market_cap, sector):
        """Enhanced missing ratio calculation with improved algorithms"""
        ratios = {}
        estimated_ratios = []
        warnings = []
        
        current_price = self.get_current_price(fundamental_data['ticker'])
        
        # Enhanced PE ratio calculation
        pe_ratio, is_estimated, pe_warning = self.enhanced_pe_ratio_estimation(
            fundamental_data, market_cap, sector, current_price
        )
        ratios['pe_ratio'] = pe_ratio
        if is_estimated:
            estimated_ratios.append('pe_ratio')
            if pe_warning:
                warnings.append(pe_warning)
        
        # Enhanced PB ratio calculation
        if not fundamental_data.get('pb_ratio'):
            if fundamental_data.get('book_value_per_share') and current_price:
                ratios['pb_ratio'] = current_price / fundamental_data['book_value_per_share']
            elif fundamental_data.get('total_equity') and market_cap:
                estimated_shares = market_cap / current_price if current_price else self.estimate_shares(market_cap, sector)
                ratios['pb_ratio'] = (current_price * estimated_shares) / fundamental_data['total_equity']
                estimated_ratios.append('pb_ratio')
                warnings.append('PB ratio estimated from total equity and market cap')
            else:
                # Sector-based PB estimation
                sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
                pb_range = sector_ranges['pb_ratio']
                ratios['pb_ratio'] = (pb_range[0] + pb_range[1]) / 2
                estimated_ratios.append('pb_ratio')
                warnings.append('PB ratio using sector-based estimation')
        else:
            ratios['pb_ratio'] = fundamental_data['pb_ratio']
        
        # Enhanced ROE calculation
        if not fundamental_data.get('roe') and fundamental_data.get('net_income') and fundamental_data.get('total_equity'):
            ratios['roe'] = (fundamental_data['net_income'] / fundamental_data['total_equity']) * 100
        elif not fundamental_data.get('roe'):
            # Sector-based ROE estimation
            sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
            roe_range = sector_ranges['roe']
            ratios['roe'] = (roe_range[0] + roe_range[1]) / 2
            estimated_ratios.append('roe')
            warnings.append('ROE using sector-based estimation')
        else:
            ratios['roe'] = fundamental_data['roe']
        
        # Calculate other ratios with enhanced logic
        self._calculate_remaining_ratios(fundamental_data, ratios, estimated_ratios, warnings, sector, market_cap)
        
        return ratios, estimated_ratios, warnings

    def _calculate_remaining_ratios(self, fundamental_data, ratios, estimated_ratios, warnings, sector, market_cap):
        """Calculate remaining ratios with enhanced logic"""
        # ROA
        if not fundamental_data.get('roa') and fundamental_data.get('net_income') and fundamental_data.get('total_assets'):
            ratios['roa'] = (fundamental_data['net_income'] / fundamental_data['total_assets']) * 100
        elif not fundamental_data.get('roa'):
            sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
            roa_range = sector_ranges['roa']
            ratios['roa'] = (roa_range[0] + roa_range[1]) / 2
            estimated_ratios.append('roa')
        
        # Debt to Equity
        if not fundamental_data.get('debt_to_equity') and fundamental_data.get('total_debt') and fundamental_data.get('total_equity'):
            ratios['debt_to_equity'] = fundamental_data['total_debt'] / fundamental_data['total_equity']
        elif not fundamental_data.get('debt_to_equity'):
            sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
            debt_range = sector_ranges['debt_to_equity']
            ratios['debt_to_equity'] = (debt_range[0] + debt_range[1]) / 2
            estimated_ratios.append('debt_to_equity')
        else:
            ratios['debt_to_equity'] = fundamental_data['debt_to_equity']
        
        # Current Ratio
        if not fundamental_data.get('current_ratio') and fundamental_data.get('current_assets') and fundamental_data.get('current_liabilities'):
            ratios['current_ratio'] = fundamental_data['current_assets'] / fundamental_data['current_liabilities']
        elif not fundamental_data.get('current_ratio'):
            ratios['current_ratio'] = self.CONSERVATIVE_DEFAULTS['current_ratio']
            estimated_ratios.append('current_ratio')
        else:
            ratios['current_ratio'] = fundamental_data['current_ratio']
        
        # EV/EBITDA
        if not fundamental_data.get('ev_ebitda') and fundamental_data.get('ebitda') and market_cap:
            ratios['ev_ebitda'] = market_cap / fundamental_data['ebitda']
        elif not fundamental_data.get('ev_ebitda'):
            sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
            ev_range = sector_ranges['ev_ebitda']
            ratios['ev_ebitda'] = (ev_range[0] + ev_range[1]) / 2
            estimated_ratios.append('ev_ebitda')
        else:
            ratios['ev_ebitda'] = fundamental_data['ev_ebitda']
        
        # Margins and Growth (use defaults if missing)
        for metric in ['gross_margin', 'operating_margin', 'net_margin', 'revenue_growth_yoy', 'earnings_growth_yoy']:
            if not fundamental_data.get(metric):
                ratios[metric] = self.CONSERVATIVE_DEFAULTS[metric]
                estimated_ratios.append(metric)
            else:
                ratios[metric] = fundamental_data[metric]

    def estimate_shares(self, market_cap, sector):
        """Enhanced share estimation based on market cap and sector"""
        if market_cap > 1000000000000:  # > $1T
            return 15000000000  # 15B shares
        elif market_cap > 100000000000:  # > $100B
            return 5000000000   # 5B shares
        elif market_cap > 10000000000:   # > $10B
            return 1000000000   # 1B shares
        elif market_cap > 1000000000:    # > $1B
            return 200000000    # 200M shares
        else:
            return 50000000     # 50M shares

    def get_current_price(self, ticker):
        """Get current stock price"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT close FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """, (ticker,))
            result = cursor.fetchone()
            return result['close'] if result else None
        finally:
            cursor.close()

    def get_fundamental_data(self, ticker):
        """Get fundamental data with enhanced validation"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT 
                    f.*,
                    s.sector,
                    s.market_cap_b
                FROM company_fundamentals f
                JOIN stocks s ON f.ticker = s.ticker
                WHERE f.ticker = %s
                ORDER BY f.report_date DESC
                LIMIT 1
            """, (ticker,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Convert to dict and handle None values
            data = dict(result)
            market_cap = data.get('market_cap_b', 0) * 1000000000 if data.get('market_cap_b') else 0
            
            # Map the actual column names to the expected names
            mapped_data = {
                'ticker': ticker,
                'sector': data.get('sector', 'default'),
                'market_cap': market_cap,
                'pe_ratio': data.get('price_to_earnings'),
                'pb_ratio': data.get('price_to_book'),
                'roe': data.get('return_on_equity'),
                'roa': data.get('return_on_assets'),
                'debt_to_equity': data.get('debt_to_equity_ratio'),
                'current_ratio': data.get('current_ratio'),
                'ev_ebitda': data.get('ev_to_ebitda'),
                'gross_margin': data.get('gross_margin'),
                'operating_margin': data.get('operating_margin'),
                'net_margin': data.get('net_margin'),
                'revenue_growth_yoy': data.get('revenue_growth_yoy'),
                'earnings_growth_yoy': data.get('earnings_growth_yoy'),
                'earnings_per_share': data.get('eps_diluted'),
                'book_value_per_share': data.get('book_value_per_share'),
                'net_income': data.get('net_income'),
                'total_equity': data.get('total_equity'),
                'total_assets': data.get('total_assets'),
                'total_debt': data.get('total_debt'),
                'current_assets': data.get('current_assets'),
                'current_liabilities': data.get('current_liabilities'),
                'ebitda': data.get('ebitda')
            }
            
            return mapped_data
        finally:
            cursor.close()

    def calculate_enhanced_data_confidence(self, fundamental_data, ratios, estimated_ratios):
        """Calculate enhanced data confidence with weighted metrics"""
        total_weight = 0
        weighted_confidence = 0
        missing_critical = 0
        
        for metric, config in self.REQUIRED_METRICS.items():
            weight = config['weight']
            is_critical = config['critical']
            
            if metric in ratios and ratios[metric] is not None:
                # Base confidence for available data
                base_confidence = 0.9 if metric not in estimated_ratios else 0.6
                
                # Validate against sector ranges
                sector = fundamental_data.get('sector', 'default')
                sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
                
                if metric in sector_ranges:
                    min_val, max_val = sector_ranges[metric]
                    if min_val <= ratios[metric] <= max_val:
                        base_confidence += 0.1  # Bonus for reasonable values
                    else:
                        base_confidence -= 0.2  # Penalty for out-of-range values
                
                weighted_confidence += base_confidence * weight
                total_weight += weight
            else:
                if is_critical:
                    missing_critical += 1
                total_weight += weight
        
        # Calculate final confidence
        if total_weight > 0:
            base_confidence = weighted_confidence / total_weight
        else:
            base_confidence = 0
        
        # Penalty for missing critical metrics
        critical_penalty = missing_critical * 0.15
        
        # Bonus for having more data
        data_completeness_bonus = min(0.1, (len(ratios) / len(self.REQUIRED_METRICS)) * 0.1)
        
        final_confidence = max(0, min(1, base_confidence - critical_penalty + data_completeness_bonus))
        
        return final_confidence

    def calculate_fundamental_scores_enhanced(self, ticker):
        """Calculate enhanced fundamental scores with improved algorithms"""
        try:
            # Get fundamental data
            fundamental_data = self.get_fundamental_data(ticker)
            if not fundamental_data:
                return {'error': f'No fundamental data found for {ticker}'}
            
            # Calculate missing ratios with enhanced algorithms
            ratios, estimated_ratios, warnings = self.enhanced_missing_ratios_calculation(
                fundamental_data, fundamental_data['market_cap'], fundamental_data['sector']
            )
            
            # Calculate enhanced data confidence
            data_confidence = self.calculate_enhanced_data_confidence(fundamental_data, ratios, estimated_ratios)
            
            # Calculate scores with confidence adjustment
            scores = self.calculate_scores_with_enhanced_confidence(ratios, data_confidence, fundamental_data['sector'])
            
            # Add metadata
            scores.update({
                'ticker': ticker,
                'data_confidence': data_confidence,
                'missing_metrics': [metric for metric in self.REQUIRED_METRICS if metric not in ratios],
                'estimated_ratios': estimated_ratios,
                'data_warnings': warnings,
                'sector': fundamental_data['sector'],
                'market_cap': fundamental_data['market_cap']
            })
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating scores for {ticker}: {e}")
            return {'error': str(e)}

    def calculate_scores_with_enhanced_confidence(self, ratios, confidence, sector):
        """Calculate scores with enhanced confidence and sector adjustments"""
        # Apply sector-specific adjustments
        sector_ranges = self.SECTOR_RANGES.get(sector, self.SECTOR_RANGES['default'])
        growth_multiplier = sector_ranges.get('growth_multiplier', 1.0)
        risk_multiplier = sector_ranges.get('risk_multiplier', 1.0)
        
        # Calculate base scores
        health_score = self.calculate_enhanced_fundamental_health_score(ratios, sector)
        value_score = self.calculate_enhanced_value_investment_score(ratios, sector)
        risk_score = self.calculate_enhanced_risk_assessment_score(ratios, sector, risk_multiplier)
        
        # Apply confidence adjustment
        confidence_factor = 0.7 + (confidence * 0.3)  # 70% base + up to 30% from confidence
        
        adjusted_health = health_score * confidence_factor
        adjusted_value = value_score * confidence_factor
        adjusted_risk = risk_score * (1 + (1 - confidence_factor) * 0.3)  # Risk increases with lower confidence
        
        # Ensure all scores are within bounds
        adjusted_health = min(100.0, max(0.0, adjusted_health))
        adjusted_value = min(100.0, max(0.0, adjusted_value))
        adjusted_risk = min(100.0, max(0.0, adjusted_risk))
        
        # Normalize to 5-level scale
        normalized_scores = self.normalize_enhanced_scores({
            'fundamental_health_score': adjusted_health,
            'value_investment_score': adjusted_value,
            'fundamental_risk_score': adjusted_risk
        })
        
        return {
            'fundamental_health_score': round(adjusted_health, 2),
            'fundamental_health_grade': normalized_scores['fundamental_health_grade'],
            'fundamental_health_description': normalized_scores['fundamental_health_description'],
            'value_investment_score': round(adjusted_value, 2),
            'value_rating': normalized_scores['value_rating'],
            'value_investment_description': normalized_scores['value_investment_description'],
            'fundamental_risk_score': round(adjusted_risk, 2),
            'fundamental_risk_level': normalized_scores['fundamental_risk_level'],
            'fundamental_risk_description': normalized_scores['fundamental_risk_description'],
            'overall_score': round((adjusted_health * 0.4 + adjusted_value * 0.4 + (100 - adjusted_risk) * 0.2), 2),
            'overall_grade': normalized_scores['overall_grade'],
            'overall_description': normalized_scores['overall_description']
        }

    def calculate_enhanced_fundamental_health_score(self, ratios, sector):
        """Calculate enhanced fundamental health score with sector adjustments"""
        health_score = 50  # Base health score
        
        # ROE-based health
        if ratios.get('roe') is not None:
            roe = float(ratios['roe']) if ratios['roe'] is not None else None
            if roe and roe > 20:
                health_score += 20
            elif roe and roe > 15:
                health_score += 15
            elif roe and roe > 10:
                health_score += 10
            elif roe and roe < 5:
                health_score -= 10
        
        # ROA-based health
        if ratios.get('roa') is not None:
            roa = float(ratios['roa']) if ratios['roa'] is not None else None
            if roa and roa > 10:
                health_score += 15
            elif roa and roa > 5:
                health_score += 10
            elif roa and roa < 2:
                health_score -= 10
        
        # Margin-based health
        if ratios.get('net_margin') is not None:
            net_margin = float(ratios['net_margin']) if ratios['net_margin'] is not None else None
            if net_margin and net_margin > 15:
                health_score += 15
            elif net_margin and net_margin > 10:
                health_score += 10
            elif net_margin and net_margin < 5:
                health_score -= 10
        
        # Growth-based health
        if ratios.get('revenue_growth_yoy') is not None:
            growth = float(ratios['revenue_growth_yoy']) if ratios['revenue_growth_yoy'] is not None else None
            if growth and growth > 10:
                health_score += 10
            elif growth and growth < -5:
                health_score -= 10
        
        # Ensure health score is within bounds (0-100)
        return min(100.0, max(0.0, health_score))

    def calculate_enhanced_value_investment_score(self, ratios, sector):
        """Calculate enhanced value investment score with sector adjustments"""
        value_score = 50  # Base value score
        
        # PE-based value
        if ratios.get('pe_ratio') is not None:
            pe_ratio = float(ratios['pe_ratio']) if ratios['pe_ratio'] is not None else None
            if pe_ratio and pe_ratio < 15:
                value_score += 20
            elif pe_ratio and pe_ratio < 20:
                value_score += 15
            elif pe_ratio and pe_ratio < 25:
                value_score += 10
            elif pe_ratio and pe_ratio > 40:
                value_score -= 15
        
        # PB-based value
        if ratios.get('pb_ratio') is not None:
            pb_ratio = float(ratios['pb_ratio']) if ratios['pb_ratio'] is not None else None
            if pb_ratio and pb_ratio < 1.5:
                value_score += 15
            elif pb_ratio and pb_ratio < 2.5:
                value_score += 10
            elif pb_ratio and pb_ratio > 5:
                value_score -= 10
        
        # EV/EBITDA-based value
        if ratios.get('ev_ebitda') is not None:
            ev_ebitda = float(ratios['ev_ebitda']) if ratios['ev_ebitda'] is not None else None
            if ev_ebitda and ev_ebitda < 10:
                value_score += 15
            elif ev_ebitda and ev_ebitda < 15:
                value_score += 10
            elif ev_ebitda and ev_ebitda > 25:
                value_score -= 10
        
        # Dividend yield (if available)
        if ratios.get('dividend_yield') is not None:
            dividend_yield = float(ratios['dividend_yield']) if ratios['dividend_yield'] is not None else None
            if dividend_yield and dividend_yield > 3:
                value_score += 10
            elif dividend_yield and dividend_yield > 2:
                value_score += 5
        
        # Ensure value score is within bounds (0-100)
        return min(100.0, max(0.0, value_score))

    def calculate_enhanced_risk_assessment_score(self, ratios, sector, risk_multiplier):
        """Calculate enhanced risk assessment score with sector and growth adjustments"""
        risk_score = 50  # Base risk score
        
        # PE-based risk (higher PE = higher risk)
        if ratios.get('pe_ratio') is not None:
            pe_ratio = float(ratios['pe_ratio']) if ratios['pe_ratio'] is not None else None
            if pe_ratio and pe_ratio > 50:
                risk_score += 25
            elif pe_ratio and pe_ratio > 30:
                risk_score += 15
            elif pe_ratio and pe_ratio > 20:
                risk_score += 10
        
        # Debt-based risk
        if ratios.get('debt_to_equity') is not None:
            debt_ratio = float(ratios['debt_to_equity']) if ratios['debt_to_equity'] is not None else None
            if debt_ratio and debt_ratio > 1.5:
                risk_score += 20
            elif debt_ratio and debt_ratio > 1.0:
                risk_score += 10
        
        # Growth-based risk (high growth can indicate higher risk)
        if ratios.get('revenue_growth_yoy') is not None:
            growth_rate = float(ratios['revenue_growth_yoy']) if ratios['revenue_growth_yoy'] is not None else None
            if growth_rate and growth_rate > 30:
                risk_score += 15
            elif growth_rate and growth_rate > 20:
                risk_score += 10
        
        # Apply sector risk multiplier
        risk_score = float(risk_score) * float(risk_multiplier)
        
        # Ensure risk score is within bounds (0-100)
        return min(100.0, max(0.0, risk_score))

    def normalize_enhanced_scores(self, scores):
        """Normalize scores to 5-level scale with enhanced thresholds"""
        result = {}
        
        # Fundamental Health Score
        health_score = scores['fundamental_health_score']
        if health_score >= 80:
            result['fundamental_health_grade'] = 'Strong Buy'
            result['fundamental_health_description'] = 'Excellent fundamental health'
        elif health_score >= 65:
            result['fundamental_health_grade'] = 'Buy'
            result['fundamental_health_description'] = 'Good fundamental health'
        elif health_score >= 45:
            result['fundamental_health_grade'] = 'Neutral'
            result['fundamental_health_description'] = 'Average fundamental health'
        elif health_score >= 25:
            result['fundamental_health_grade'] = 'Sell'
            result['fundamental_health_description'] = 'Poor fundamental health'
        else:
            result['fundamental_health_grade'] = 'Strong Sell'
            result['fundamental_health_description'] = 'Very poor fundamental health'
        
        # Value Investment Score
        value_score = scores['value_investment_score']
        if value_score >= 75:
            result['value_rating'] = 'Strong Buy'
            result['value_investment_description'] = 'Excellent value opportunity'
        elif value_score >= 60:
            result['value_rating'] = 'Buy'
            result['value_investment_description'] = 'Good value opportunity'
        elif value_score >= 40:
            result['value_rating'] = 'Neutral'
            result['value_investment_description'] = 'Fair value'
        elif value_score >= 25:
            result['value_rating'] = 'Sell'
            result['value_investment_description'] = 'Overvalued'
        else:
            result['value_rating'] = 'Strong Sell'
            result['value_investment_description'] = 'Highly overvalued'
        
        # Risk Assessment Score
        risk_score = scores['fundamental_risk_score']
        if risk_score <= 25:
            result['fundamental_risk_level'] = 'Very Low'
            result['fundamental_risk_description'] = 'Very low fundamental risk'
        elif risk_score <= 40:
            result['fundamental_risk_level'] = 'Low'
            result['fundamental_risk_description'] = 'Low fundamental risk'
        elif risk_score <= 60:
            result['fundamental_risk_level'] = 'Medium'
            result['fundamental_risk_description'] = 'Moderate fundamental risk'
        elif risk_score <= 75:
            result['fundamental_risk_level'] = 'High'
            result['fundamental_risk_description'] = 'High fundamental risk'
        else:
            result['fundamental_risk_level'] = 'Very High'
            result['fundamental_risk_description'] = 'Very high fundamental risk'
        
        # Overall Score
        overall_score = (health_score * 0.4 + value_score * 0.4 + (100 - risk_score) * 0.2)
        if overall_score >= 75:
            result['overall_grade'] = 'Strong Buy'
            result['overall_description'] = 'Strong buy recommendation'
        elif overall_score >= 60:
            result['overall_grade'] = 'Buy'
            result['overall_description'] = 'Buy recommendation'
        elif overall_score >= 40:
            result['overall_grade'] = 'Neutral'
            result['overall_description'] = 'Neutral recommendation'
        elif overall_score >= 25:
            result['overall_grade'] = 'Sell'
            result['overall_description'] = 'Sell recommendation'
        else:
            result['overall_grade'] = 'Strong Sell'
            result['overall_description'] = 'Strong sell recommendation'
        
        return result

    def store_fundamental_scores(self, ticker: str, scores: Dict[str, Any]) -> bool:
        """Store fundamental scores in database"""
        try:
            cursor = self.conn.cursor()
            
            # Prepare data for storage
            data = {
                'ticker': ticker,
                'date_calculated': date.today(),
                'fundamental_health_score': scores.get('fundamental_health_score'),
                'fundamental_health_grade': scores.get('fundamental_health_grade'),
                'fundamental_risk_score': scores.get('fundamental_risk_score'),
                'fundamental_risk_level': scores.get('fundamental_risk_level'),
                'value_investment_score': scores.get('value_investment_score'),
                'value_rating': scores.get('value_rating'),
                'overall_score': scores.get('overall_score'),
                'overall_grade': scores.get('overall_grade'),
                'data_confidence': scores.get('data_confidence'),
                'missing_metrics_count': len(scores.get('missing_metrics', [])),
                'data_warnings': json.dumps(scores.get('data_warnings', []))
            }
            
            # Insert or update scores
            cursor.execute("""
                INSERT INTO company_scores_current (
                    ticker, date_calculated, fundamental_health_score, fundamental_health_grade,
                    fundamental_risk_score, fundamental_risk_level, value_investment_score, value_rating,
                    overall_score, overall_grade, data_confidence, missing_metrics_count, data_warnings
                ) VALUES (
                    %(ticker)s, %(date_calculated)s, %(fundamental_health_score)s, %(fundamental_health_grade)s,
                    %(fundamental_risk_score)s, %(fundamental_risk_level)s, %(value_investment_score)s, %(value_rating)s,
                    %(overall_score)s, %(overall_grade)s, %(data_confidence)s, %(missing_metrics_count)s, %(data_warnings)s
                ) ON CONFLICT (ticker) DO UPDATE SET
                    date_calculated = EXCLUDED.date_calculated,
                    fundamental_health_score = EXCLUDED.fundamental_health_score,
                    fundamental_health_grade = EXCLUDED.fundamental_health_grade,
                    fundamental_risk_score = EXCLUDED.fundamental_risk_score,
                    fundamental_risk_level = EXCLUDED.fundamental_risk_level,
                    value_investment_score = EXCLUDED.value_investment_score,
                    value_rating = EXCLUDED.value_rating,
                    overall_score = EXCLUDED.overall_score,
                    overall_grade = EXCLUDED.overall_grade,
                    data_confidence = EXCLUDED.data_confidence,
                    missing_metrics_count = EXCLUDED.missing_metrics_count,
                    data_warnings = EXCLUDED.data_warnings,
                    updated_at = CURRENT_TIMESTAMP
            """, data)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing scores for {ticker}: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Test the enhanced fundamental score calculator"""
    calculator = EnhancedFundamentalScoreCalculatorV2()
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'PG', 'PFE', 'CSCO']
    
    print("🧪 Testing Enhanced Fundamental Score Calculator V2")
    print("=" * 60)
    
    for ticker in test_tickers:
        print(f"\n📊 Processing {ticker}...")
        scores = calculator.calculate_fundamental_scores_enhanced(ticker)
        
        if 'error' in scores:
            print(f"  ❌ Error: {scores['error']}")
            continue
        
        print(f"  ✅ Fundamental Health: {scores['fundamental_health_score']:.1f} ({scores['fundamental_health_grade']})")
        print(f"  ✅ Value Investment: {scores['value_investment_score']:.1f} ({scores['value_rating']})")
        print(f"  ✅ Risk Assessment: {scores['fundamental_risk_score']:.1f} ({scores['fundamental_risk_level']})")
        print(f"  ✅ Overall Score: {scores['overall_score']:.1f} ({scores['overall_grade']})")
        print(f"  📈 Data Confidence: {scores['data_confidence']:.1%}")
        print(f"  📊 Missing Metrics: {len(scores['missing_metrics'])}/{len(calculator.REQUIRED_METRICS)}")
        
        if scores['data_warnings']:
            print(f"  ⚠️  Warnings: {len(scores['data_warnings'])}")
    
    calculator.close()
    print("\n✅ Enhanced fundamental score calculation completed!")

if __name__ == "__main__":
    main() 