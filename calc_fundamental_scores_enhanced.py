import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
import logging
from datetime import datetime, date
from typing import Dict, Any

# Add the daily_run directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'daily_run'))

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFundamentalScoreCalculator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        # Define required metrics for confidence calculation
        self.REQUIRED_METRICS = [
            'pe_ratio', 'pb_ratio', 'roe', 'roa', 'debt_to_equity', 
            'current_ratio', 'ev_ebitda', 'gross_margin', 'operating_margin', 
            'net_margin', 'revenue_growth_yoy', 'earnings_growth_yoy'
        ]
        
        # Sector-specific ratio validation ranges
        self.SECTOR_RANGES = {
            'Technology': {
                'pe_ratio': (10, 50), 'pb_ratio': (2, 15), 'roe': (-20, 40),
                'roa': (-10, 25), 'debt_to_equity': (0, 1.5), 'ev_ebitda': (10, 40)
            },
            'Financial': {
                'pe_ratio': (5, 25), 'pb_ratio': (0.5, 3), 'roe': (-10, 25),
                'roa': (-5, 15), 'debt_to_equity': (0.5, 3), 'ev_ebitda': (5, 20)
            },
            'Healthcare': {
                'pe_ratio': (15, 60), 'pb_ratio': (3, 20), 'roe': (-30, 50),
                'roa': (-15, 30), 'debt_to_equity': (0, 2), 'ev_ebitda': (15, 50)
            },
            'Consumer Discretionary': {
                'pe_ratio': (8, 35), 'pb_ratio': (1, 12), 'roe': (-25, 35),
                'roa': (-12, 20), 'debt_to_equity': (0, 2.5), 'ev_ebitda': (8, 30)
            },
            'Energy': {
                'pe_ratio': (5, 25), 'pb_ratio': (0.5, 8), 'roe': (-40, 30),
                'roa': (-20, 15), 'debt_to_equity': (0, 2), 'ev_ebitda': (3, 15)
            },
            'default': {
                'pe_ratio': (5, 30), 'pb_ratio': (0.5, 10), 'roe': (-25, 35),
                'roa': (-12, 20), 'debt_to_equity': (0, 2), 'ev_ebitda': (5, 25)
            }
        }
        
        # Conservative defaults for missing data
        self.CONSERVATIVE_DEFAULTS = {
            'pe_ratio': 25, 'pb_ratio': 3, 'roe': 10, 'roa': 5,
            'debt_to_equity': 0.5, 'current_ratio': 1.5, 'ev_ebitda': 15,
            'gross_margin': 30, 'operating_margin': 15, 'net_margin': 10,
            'revenue_growth_yoy': 5, 'earnings_growth_yoy': 5
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

    def validate_ratio(self, ratio_name, value, company_sector):
        """Validate if a ratio is within reasonable ranges for the sector"""
        if value is None:
            return {'valid': False, 'reason': 'Missing data', 'confidence': 0.0}
        
        # Convert to float for calculations
        value = self.safe_float(value)
        
        # Get sector ranges
        ranges = self.SECTOR_RANGES.get(company_sector, self.SECTOR_RANGES['default'])
        
        if ratio_name not in ranges:
            return {'valid': True, 'reason': None, 'confidence': 0.8}
        
        min_val, max_val = ranges[ratio_name]
        
        # Check if value is within expected range
        if value < min_val or value > max_val:
            return {
                'valid': False, 
                'reason': f'Value {value:.2f} outside expected range ({min_val}-{max_val}) for {company_sector}',
                'confidence': 0.3
            }
        
        # Calculate confidence based on how close to the middle of the range
        range_mid = (min_val + max_val) / 2
        range_width = max_val - min_val
        distance_from_mid = abs(value - range_mid)
        confidence = max(0.5, 1.0 - (distance_from_mid / range_width))
        
        return {'valid': True, 'reason': None, 'confidence': confidence}

    def calculate_missing_ratios_enhanced(self, fundamental_data, market_cap, sector):
        """Enhanced missing ratio calculation with validation"""
        ratios = {}
        estimated_ratios = []
        warnings = []
        
        # Get current price
        current_price = self.get_current_price(fundamental_data['ticker'])
        
        # Calculate PE ratio if missing
        if not fundamental_data.get('pe_ratio'):
            if fundamental_data.get('earnings_per_share') and current_price:
                ratios['pe_ratio'] = current_price / fundamental_data['earnings_per_share']
            elif fundamental_data.get('net_income') and market_cap:
                # Estimate shares outstanding based on market cap and price
                estimated_shares = market_cap / current_price if current_price else self.estimate_shares(market_cap, sector)
                ratios['pe_ratio'] = (current_price * estimated_shares) / fundamental_data['net_income']
                estimated_ratios.append('pe_ratio')
                warnings.append('PE ratio estimated from net income and market cap')
            else:
                ratios['pe_ratio'] = self.CONSERVATIVE_DEFAULTS['pe_ratio']
                estimated_ratios.append('pe_ratio')
                warnings.append('PE ratio using conservative default')
        
        # Calculate PB ratio if missing
        if not fundamental_data.get('pb_ratio'):
            if fundamental_data.get('book_value_per_share') and current_price:
                ratios['pb_ratio'] = current_price / fundamental_data['book_value_per_share']
            elif fundamental_data.get('total_equity') and market_cap:
                estimated_shares = market_cap / current_price if current_price else self.estimate_shares(market_cap, sector)
                ratios['pb_ratio'] = (current_price * estimated_shares) / fundamental_data['total_equity']
                estimated_ratios.append('pb_ratio')
                warnings.append('PB ratio estimated from total equity and market cap')
            else:
                ratios['pb_ratio'] = self.CONSERVATIVE_DEFAULTS['pb_ratio']
                estimated_ratios.append('pb_ratio')
                warnings.append('PB ratio using conservative default')
        
        # Calculate other ratios if missing
        if not fundamental_data.get('roe') and fundamental_data.get('net_income') and fundamental_data.get('total_equity'):
            ratios['roe'] = (fundamental_data['net_income'] / fundamental_data['total_equity']) * 100
        elif not fundamental_data.get('roe'):
            ratios['roe'] = self.CONSERVATIVE_DEFAULTS['roe']
            estimated_ratios.append('roe')
        
        if not fundamental_data.get('roa') and fundamental_data.get('net_income') and fundamental_data.get('total_assets'):
            ratios['roa'] = (fundamental_data['net_income'] / fundamental_data['total_assets']) * 100
        elif not fundamental_data.get('roa'):
            ratios['roa'] = self.CONSERVATIVE_DEFAULTS['roa']
            estimated_ratios.append('roa')
        
        if not fundamental_data.get('debt_to_equity') and fundamental_data.get('total_debt') and fundamental_data.get('total_equity'):
            ratios['debt_to_equity'] = fundamental_data['total_debt'] / fundamental_data['total_equity']
        elif not fundamental_data.get('debt_to_equity'):
            ratios['debt_to_equity'] = self.CONSERVATIVE_DEFAULTS['debt_to_equity']
            estimated_ratios.append('debt_to_equity')
        
        if not fundamental_data.get('current_ratio') and fundamental_data.get('current_assets') and fundamental_data.get('current_liabilities'):
            ratios['current_ratio'] = fundamental_data['current_assets'] / fundamental_data['current_liabilities']
        elif not fundamental_data.get('current_ratio'):
            ratios['current_ratio'] = self.CONSERVATIVE_DEFAULTS['current_ratio']
            estimated_ratios.append('current_ratio')
        
        return ratios, estimated_ratios, warnings

    def estimate_shares(self, market_cap, sector):
        """Estimate shares outstanding based on market cap and sector"""
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
            # Get fundamental data
            cursor.execute("""
                SELECT 
                    cf.ticker,
                    cf.revenue,
                    cf.net_income,
                    cf.total_assets,
                    cf.total_equity,
                    cf.total_debt,
                    cf.current_assets,
                    cf.current_liabilities,
                    cf.gross_profit,
                    cf.operating_income,
                    cf.eps_diluted as earnings_per_share,
                    cf.book_value_per_share,
                    cf.market_cap,
                    cf.last_updated
                FROM company_fundamentals cf
                WHERE cf.ticker = %s
                ORDER BY cf.last_updated DESC
                LIMIT 1
            """, (ticker,))
            
            fundamental_data = cursor.fetchone()
            if not fundamental_data:
                return None
            
            # Get financial ratios from company_fundamentals (they're already calculated)
            ratios_data = {
                'pe_ratio': fundamental_data.get('price_to_earnings'),
                'pb_ratio': fundamental_data.get('price_to_book'),
                'roe': fundamental_data.get('return_on_equity'),
                'roa': fundamental_data.get('return_on_assets'),
                'debt_to_equity': fundamental_data.get('debt_to_equity_ratio'),
                'current_ratio': fundamental_data.get('current_ratio'),
                'ev_ebitda': fundamental_data.get('ev_to_ebitda'),
                'gross_margin': fundamental_data.get('gross_margin'),
                'operating_margin': fundamental_data.get('operating_margin'),
                'net_margin': fundamental_data.get('net_margin'),
                'revenue_growth_yoy': fundamental_data.get('revenue_growth_yoy'),
                'earnings_growth_yoy': fundamental_data.get('earnings_growth_yoy')
            }
            
            # Get sector from stocks table
            cursor.execute("""
                SELECT sector FROM stocks WHERE ticker = %s
            """, (ticker,))
            sector_result = cursor.fetchone()
            sector = sector_result['sector'] if sector_result else 'default'
            
            fundamental_data['sector'] = sector
            
            # Merge ratios data into fundamental data
            fundamental_data.update(ratios_data)
            
            return fundamental_data
            
        finally:
            cursor.close()

    def calculate_data_confidence(self, fundamental_data, ratios):
        """Calculate confidence level based on data availability and quality"""
        available_metrics = 0
        total_metrics = len(self.REQUIRED_METRICS)
        validation_results = {}
        
        for metric in self.REQUIRED_METRICS:
            value = ratios.get(metric) or fundamental_data.get(metric)
            if value is not None:
                available_metrics += 1
                # Validate the ratio
                validation = self.validate_ratio(metric, value, fundamental_data.get('sector', 'default'))
                validation_results[metric] = validation
        
        # Calculate base confidence
        base_confidence = available_metrics / total_metrics
        
        # Adjust confidence based on validation results
        avg_validation_confidence = sum(
            result.get('confidence', 0.5) for result in validation_results.values()
        ) / len(validation_results) if validation_results else 0.5
        
        final_confidence = (base_confidence * 0.7) + (avg_validation_confidence * 0.3)
        
        return final_confidence, validation_results

    def calculate_fundamental_scores_enhanced(self, ticker):
        """Calculate fundamental scores with enhanced missing data handling"""
        fundamental_data = self.get_fundamental_data(ticker)
        if not fundamental_data:
            return {
                'error': f'No fundamental data found for {ticker}',
                'confidence': 0.0,
                'missing_metrics': self.REQUIRED_METRICS
            }
        
        # Calculate missing ratios
        ratios, estimated_ratios, warnings = self.calculate_missing_ratios_enhanced(
            fundamental_data, 
            fundamental_data.get('market_cap'), 
            fundamental_data.get('sector', 'default')
        )
        
        # Merge with existing ratios
        all_ratios = {**fundamental_data, **ratios}
        
        # Calculate confidence
        confidence, validation_results = self.calculate_data_confidence(fundamental_data, all_ratios)
        
        # If confidence is too low, return warning
        if confidence < 0.5:
            return {
                'error': f'Insufficient data for {ticker} (confidence: {confidence:.1%})',
                'confidence': confidence,
                'missing_metrics': [m for m in self.REQUIRED_METRICS if not all_ratios.get(m)],
                'warnings': warnings
            }
        
        # Calculate scores with confidence adjustment
        scores = self.calculate_scores_with_confidence(all_ratios, confidence)
        
        # Add metadata
        scores.update({
            'ticker': ticker,
            'calculation_date': date.today(),
            'data_confidence': confidence,
            'missing_metrics': [m for m in self.REQUIRED_METRICS if not all_ratios.get(m)],
            'estimated_ratios': estimated_ratios,
            'data_warnings': warnings,
            'ratio_validation_status': validation_results
        })
        
        return scores

    def calculate_scores_with_confidence(self, ratios, confidence):
        """Calculate scores with confidence-based adjustments"""
        # Calculate base scores
        fundamental_health = self.calculate_fundamental_health_score(ratios)
        value_investment = self.calculate_value_investment_score(ratios)
        risk_assessment = self.calculate_risk_assessment_score(ratios)
        
        # Apply confidence adjustment
        if confidence < 0.8:
            # Apply conservative bias for low confidence
            fundamental_health = (fundamental_health * confidence) + (50 * (1 - confidence))
            value_investment = (value_investment * confidence) + (40 * (1 - confidence))
            risk_assessment = (risk_assessment * confidence) + (60 * (1 - confidence))
        
        # Normalize to 5 levels
        normalized_scores = self.normalize_score_to_5_levels({
            'fundamental_health_score': fundamental_health,
            'value_investment_score': value_investment,
            'fundamental_risk_score': risk_assessment
        })
        
        return {
            'fundamental_health_score': fundamental_health,
            'value_investment_score': value_investment,
            'fundamental_risk_score': risk_assessment,
            'fundamental_health_grade': normalized_scores['fundamental_health_grade'],
            'fundamental_health_description': normalized_scores['fundamental_health_description'],
            'value_rating': normalized_scores['value_rating'],
            'value_investment_description': normalized_scores['value_investment_description'],
            'fundamental_risk_level': normalized_scores['fundamental_risk_level'],
            'fundamental_risk_description': normalized_scores['fundamental_risk_description']
        }

    def safe_float(self, value):
        """Convert value to float, handling Decimal and None values"""
        if value is None:
            return None
        if hasattr(value, '__float__'):
            return float(value)
        return value

    def calculate_fundamental_health_score(self, ratios):
        """Calculate fundamental health score with enhanced logic"""
        score = 0
        components = 0
        
        # Profitability (30%)
        if ratios.get('roe') is not None:
            roe = self.safe_float(ratios['roe'])
            roe_score = min(100, max(0, (roe + 20) * 2))  # -20% to 30% range
            score += roe_score * 0.30
            components += 0.30
        
        if ratios.get('roa') is not None:
            roa = self.safe_float(ratios['roa'])
            roa_score = min(100, max(0, (roa + 10) * 3.33))  # -10% to 20% range
            score += roa_score * 0.20
            components += 0.20
        
        # Margins (25%)
        if ratios.get('gross_margin') is not None:
            gross = self.safe_float(ratios['gross_margin'])
            gross_score = min(100, max(0, gross * 1.67))  # 0-60% range
            score += gross_score * 0.15
            components += 0.15
        
        if ratios.get('operating_margin') is not None:
            op = self.safe_float(ratios['operating_margin'])
            op_score = min(100, max(0, op * 2))  # 0-50% range
            score += op_score * 0.10
            components += 0.10
        
        # Growth (25%)
        if ratios.get('revenue_growth_yoy') is not None:
            growth = self.safe_float(ratios['revenue_growth_yoy'])
            growth_score = min(100, max(0, (growth + 20) * 2.5))  # -20% to 20% range
            score += growth_score * 0.25
            components += 0.25
        
        # Financial Strength (20%)
        if ratios.get('debt_to_equity') is not None:
            debt = self.safe_float(ratios['debt_to_equity'])
            debt_score = max(0, min(100, 100 - (debt * 50)))  # 0-2 range
            score += debt_score * 0.20
            components += 0.20
        
        return score / components if components > 0 else 50

    def calculate_value_investment_score(self, ratios):
        """Calculate value investment score with enhanced logic"""
        score = 0
        components = 0
        
        # Valuation (40%)
        if ratios.get('pe_ratio') is not None:
            pe = self.safe_float(ratios['pe_ratio'])
            if pe > 0:
                pe_score = max(0, min(100, 100 - (pe - 10) * 2))  # 10-60 range
                score += pe_score * 0.25
                components += 0.25
        
        if ratios.get('pb_ratio') is not None:
            pb = self.safe_float(ratios['pb_ratio'])
            pb_score = max(0, min(100, 100 - (pb - 1) * 10))  # 1-11 range
            score += pb_score * 0.15
            components += 0.15
        
        # Quality (30%)
        if ratios.get('roe') is not None:
            roe = self.safe_float(ratios['roe'])
            roe_score = min(100, max(0, (roe + 20) * 2))
            score += roe_score * 0.30
            components += 0.30
        
        # Growth at Reasonable Price (30%)
        if ratios.get('revenue_growth_yoy') is not None and ratios.get('pe_ratio') is not None:
            pe = self.safe_float(ratios['pe_ratio'])
            growth = self.safe_float(ratios['revenue_growth_yoy'])
            if pe > 0:
                peg_ratio = pe / max(1, growth)
                peg_score = max(0, min(100, 100 - (peg_ratio - 1) * 25))  # 1-5 range
                score += peg_score * 0.30
                components += 0.30
        
        return score / components if components > 0 else 50

    def calculate_risk_assessment_score(self, ratios):
        """Calculate risk assessment score with enhanced logic"""
        score = 0
        components = 0
        
        # Valuation Risk (30%)
        if ratios.get('pe_ratio') is not None:
            pe = self.safe_float(ratios['pe_ratio'])
            if pe > 0:
                pe_risk = min(100, max(0, (pe - 15) * 2))  # 15-65 range
                score += pe_risk * 0.30
                components += 0.30
        
        # Financial Risk (25%)
        if ratios.get('debt_to_equity') is not None:
            debt = self.safe_float(ratios['debt_to_equity'])
            debt_risk = min(100, max(0, debt * 50))  # 0-2 range
            score += debt_risk * 0.25
            components += 0.25
        
        # Profitability Risk (25%)
        if ratios.get('roe') is not None:
            roe = self.safe_float(ratios['roe'])
            roe_risk = max(0, min(100, 50 - roe))  # -50% to 50% range
            score += roe_risk * 0.25
            components += 0.25
        
        # Growth Risk (20%)
        if ratios.get('revenue_growth_yoy') is not None:
            growth = self.safe_float(ratios['revenue_growth_yoy'])
            growth_risk = max(0, min(100, 50 - growth))  # -50% to 50% range
            score += growth_risk * 0.20
            components += 0.20
        
        return score / components if components > 0 else 50

    def normalize_score_to_5_levels(self, scores):
        """Normalize scores to 5-level scale and return appropriate grades/levels"""
        normalized = {}
        
        # Fundamental Health Score (0-100) -> 1-5 scale
        health_score = scores.get('fundamental_health_score', 50)
        if health_score >= 80:
            normalized['fundamental_health_score'] = 5
            normalized['fundamental_health_grade'] = 'Strong Buy'
            normalized['fundamental_health_description'] = 'Excellent fundamental health'
        elif health_score >= 65:
            normalized['fundamental_health_score'] = 4
            normalized['fundamental_health_grade'] = 'Buy'
            normalized['fundamental_health_description'] = 'Good fundamental health'
        elif health_score >= 50:
            normalized['fundamental_health_score'] = 3
            normalized['fundamental_health_grade'] = 'Neutral'
            normalized['fundamental_health_description'] = 'Average fundamental health'
        elif health_score >= 35:
            normalized['fundamental_health_score'] = 2
            normalized['fundamental_health_grade'] = 'Sell'
            normalized['fundamental_health_description'] = 'Poor fundamental health'
        else:
            normalized['fundamental_health_score'] = 1
            normalized['fundamental_health_grade'] = 'Strong Sell'
            normalized['fundamental_health_description'] = 'Very poor fundamental health'
        
        # Value Investment Score (0-100) -> 1-5 scale
        value_score = scores.get('value_investment_score', 50)
        if value_score >= 75:
            normalized['value_investment_score'] = 5
            normalized['value_rating'] = 'Strong Buy'
            normalized['value_investment_description'] = 'Excellent value opportunity'
        elif value_score >= 60:
            normalized['value_investment_score'] = 4
            normalized['value_rating'] = 'Buy'
            normalized['value_investment_description'] = 'Good value opportunity'
        elif value_score >= 45:
            normalized['value_investment_score'] = 3
            normalized['value_rating'] = 'Neutral'
            normalized['value_investment_description'] = 'Fair value'
        elif value_score >= 30:
            normalized['value_investment_score'] = 2
            normalized['value_rating'] = 'Sell'
            normalized['value_investment_description'] = 'Poor value'
        else:
            normalized['value_investment_score'] = 1
            normalized['value_rating'] = 'Strong Sell'
            normalized['value_investment_description'] = 'Very poor value'
        
        # Risk Assessment Score (0-100) -> 1-5 scale (inverted: lower score = lower risk)
        risk_score = scores.get('fundamental_risk_score', 50)
        if risk_score <= 25:
            normalized['fundamental_risk_score'] = 1
            normalized['fundamental_risk_level'] = 'Very Low'
            normalized['fundamental_risk_description'] = 'Very low risk profile'
        elif risk_score <= 40:
            normalized['fundamental_risk_score'] = 2
            normalized['fundamental_risk_level'] = 'Low'
            normalized['fundamental_risk_description'] = 'Low risk profile'
        elif risk_score <= 60:
            normalized['fundamental_risk_score'] = 3
            normalized['fundamental_risk_level'] = 'Medium'
            normalized['fundamental_risk_description'] = 'Medium risk profile'
        elif risk_score <= 75:
            normalized['fundamental_risk_score'] = 4
            normalized['fundamental_risk_level'] = 'High'
            normalized['fundamental_risk_description'] = 'High risk profile'
        else:
            normalized['fundamental_risk_score'] = 5
            normalized['fundamental_risk_level'] = 'Very High'
            normalized['fundamental_risk_description'] = 'Very high risk profile'
        
        return normalized

    def store_fundamental_scores(self, ticker: str, scores: Dict[str, Any]) -> bool:
        """
        Store fundamental scores in database using direct SQL INSERT/UPDATE
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    # First, try to update existing record
                    update_query = """
                    UPDATE company_scores_current SET
                        fundamental_health_score = %s,
                        fundamental_health_grade = %s,
                        fundamental_health_description = %s,
                        fundamental_risk_score = %s,
                        fundamental_risk_level = %s,
                        fundamental_risk_description = %s,
                        value_investment_score = %s,
                        value_rating = %s,
                        value_investment_description = %s,
                        data_confidence = %s,
                        missing_metrics = %s,
                        data_warnings = %s,
                        estimated_ratios = %s,
                        ratio_validation_status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ticker = %s
                    """
                    
                    cursor.execute(update_query, (
                        scores['fundamental_health_score'],
                        scores['fundamental_health_grade'],
                        scores.get('fundamental_health_description', 'No description available'),
                        scores['fundamental_risk_score'],
                        scores['fundamental_risk_level'],
                        scores.get('fundamental_risk_description', 'No description available'),
                        scores['value_investment_score'],
                        scores['value_rating'],
                        scores.get('value_investment_description', 'No description available'),
                        scores.get('data_confidence', 0.0),
                        scores.get('missing_metrics', []),
                        scores.get('data_warnings', []),
                        scores.get('estimated_ratios', []),
                        json.dumps(scores.get('ratio_validation_status', {})),
                        ticker
                    ))
                    
                    # If no rows were updated, insert new record
                    if cursor.rowcount == 0:
                        insert_query = """
                        INSERT INTO company_scores_current (
                            ticker, fundamental_health_score, fundamental_health_grade, 
                            fundamental_health_description, fundamental_risk_score, 
                            fundamental_risk_level, fundamental_risk_description,
                            value_investment_score, value_rating, value_investment_description,
                            data_confidence, missing_metrics, data_warnings, 
                            estimated_ratios, ratio_validation_status, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        """
                        
                        cursor.execute(insert_query, (
                            ticker,
                            scores['fundamental_health_score'],
                            scores['fundamental_health_grade'],
                            scores.get('fundamental_health_description', 'No description available'),
                            scores['fundamental_risk_score'],
                            scores['fundamental_risk_level'],
                            scores.get('fundamental_risk_description', 'No description available'),
                            scores['value_investment_score'],
                            scores['value_rating'],
                            scores.get('value_investment_description', 'No description available'),
                            scores.get('data_confidence', 0.0),
                            scores.get('missing_metrics', []),
                            scores.get('data_warnings', []),
                            scores.get('estimated_ratios', []),
                            json.dumps(scores.get('ratio_validation_status', {}))
                        ))
                    
                    # Also insert into historical table
                    historical_query = """
                    INSERT INTO company_scores_historical (
                        ticker, calculation_date, fundamental_health_score, fundamental_health_grade, 
                        fundamental_health_description, fundamental_risk_score, 
                        fundamental_risk_level, fundamental_risk_description,
                        value_investment_score, value_rating, value_investment_description,
                        data_confidence, missing_metrics, data_warnings, 
                        estimated_ratios, ratio_validation_status, created_at
                    ) VALUES (
                        %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                    ) ON CONFLICT (ticker, calculation_date) DO UPDATE SET
                        fundamental_health_score = EXCLUDED.fundamental_health_score,
                        fundamental_health_grade = EXCLUDED.fundamental_health_grade,
                        fundamental_health_description = EXCLUDED.fundamental_health_description,
                        fundamental_risk_score = EXCLUDED.fundamental_risk_score,
                        fundamental_risk_level = EXCLUDED.fundamental_risk_level,
                        fundamental_risk_description = EXCLUDED.fundamental_risk_description,
                        value_investment_score = EXCLUDED.value_investment_score,
                        value_rating = EXCLUDED.value_rating,
                        value_investment_description = EXCLUDED.value_investment_description,
                        data_confidence = EXCLUDED.data_confidence,
                        missing_metrics = EXCLUDED.missing_metrics,
                        data_warnings = EXCLUDED.data_warnings,
                        estimated_ratios = EXCLUDED.estimated_ratios,
                        ratio_validation_status = EXCLUDED.ratio_validation_status,
                        created_at = EXCLUDED.created_at
                    """
                    
                    cursor.execute(historical_query, (
                        ticker,
                        scores['fundamental_health_score'],
                        scores['fundamental_health_grade'],
                        scores.get('fundamental_health_description', 'No description available'),
                        scores['fundamental_risk_score'],
                        scores['fundamental_risk_level'],
                        scores.get('fundamental_risk_description', 'No description available'),
                        scores['value_investment_score'],
                        scores['value_rating'],
                        scores.get('value_investment_description', 'No description available'),
                        scores.get('data_confidence', 0.0),
                        scores.get('missing_metrics', []),
                        scores.get('data_warnings', []),
                        scores.get('estimated_ratios', []),
                        json.dumps(scores.get('ratio_validation_status', {}))
                    ))
                    
                    conn.commit()
                    logger.info(f"Fundamental scores stored for {ticker}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error storing fundamental scores for {ticker}: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Test the enhanced fundamental score calculator"""
    calculator = EnhancedFundamentalScoreCalculator()
    
    # Test tickers including large and small cap
    test_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'PG', 'PFE', 'CSCO',
        'UAL', 'XOM', 'JPM', 'JNJ', 'V', 'HD', 'DIS', 'NFLX', 'ADBE', 'CRM'
    ]
    
    print("Enhanced Fundamental Score Calculator Test")
    print("=" * 50)
    
    for ticker in test_tickers:
        print(f"\nProcessing {ticker}...")
        scores = calculator.calculate_fundamental_scores_enhanced(ticker)
        
        if 'error' in scores:
            print(f"  Error: {scores['error']}")
            continue
        
        print(f"  Fundamental Health: {scores['fundamental_health_score']:.1f} ({scores['fundamental_health_grade']})")
        print(f"  Value Investment: {scores['value_investment_score']:.1f} ({scores['value_rating']})")
        print(f"  Risk Assessment: {scores['fundamental_risk_score']:.1f} ({scores['fundamental_risk_level']})")
        print(f"  Data Confidence: {scores['data_confidence']:.1%}")
        
        if scores['missing_metrics']:
            print(f"  Missing Metrics: {', '.join(scores['missing_metrics'])}")
        
        if scores['data_warnings']:
            print(f"  Warnings: {', '.join(scores['data_warnings'])}")
        
        # Store scores
        if calculator.store_fundamental_scores(ticker, scores):
            print(f"  ✓ Stored successfully")
        else:
            print(f"  ✗ Storage failed")
    
    calculator.close()
    print("\nTest completed!")

if __name__ == "__main__":
    main() 