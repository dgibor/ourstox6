#!/usr/bin/env python3
"""
Fix for the risk assessment algorithm to properly handle growth stocks like TSLA
"""

import os
import sys
import logging
from typing import Dict, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedRiskAssessmentCalculator:
    def __init__(self):
        self.db_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '38837'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
    
    def get_connection(self):
        return psycopg2.connect(**self.db_params)
    
    def get_historical_revenue_data(self, ticker: str) -> Dict[str, float]:
        """Get historical revenue data for growth analysis"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT revenue, last_updated 
                    FROM company_fundamentals 
                    WHERE ticker = %s 
                    ORDER BY last_updated DESC 
                    LIMIT 4
                """, (ticker,))
                results = cursor.fetchall()
                
                if len(results) >= 2:
                    current_revenue = results[0]['revenue']
                    previous_revenue = results[1]['revenue']
                    
                    if previous_revenue and previous_revenue > 0:
                        revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
                    else:
                        revenue_growth = 0
                    
                    return {
                        'current_revenue': current_revenue,
                        'previous_revenue': previous_revenue,
                        'revenue_growth': revenue_growth
                    }
                return {}
    
    def get_market_cap_data(self, ticker: str) -> Dict[str, Any]:
        """Get market cap and related data"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT market_cap, sector 
                    FROM stocks 
                    WHERE ticker = %s
                """, (ticker,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'market_cap': result['market_cap'],
                        'sector': result['sector']
                    }
                return {}
    
    def calculate_enhanced_risk_assessment_score(self, data: Dict[str, Any], ticker: str) -> Tuple[float, Dict[str, Any]]:
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
        
        print(f"\n=== Enhanced Risk Assessment for {ticker} ===")
        
        # 1. Valuation Risk (25% weight)
        pe_ratio = data.get('pe_ratio', None)
        pb_ratio = data.get('pb_ratio', None)
        market_cap_data = self.get_market_cap_data(ticker)
        market_cap = market_cap_data.get('market_cap', 0)
        sector = market_cap_data.get('sector', '')
        
        valuation_risk = 0
        if pe_ratio is not None:
            if pe_ratio > 50:
                valuation_risk = 100
                print(f"Valuation Risk: 100 (Extreme - PE > 50: {pe_ratio:.1f})")
            elif pe_ratio > 30:
                valuation_risk = 80
                print(f"Valuation Risk: 80 (Very High - PE 30-50: {pe_ratio:.1f})")
            elif pe_ratio > 20:
                valuation_risk = 60
                print(f"Valuation Risk: 60 (High - PE 20-30: {pe_ratio:.1f})")
            elif pe_ratio > 15:
                valuation_risk = 40
                print(f"Valuation Risk: 40 (Moderate - PE 15-20: {pe_ratio:.1f})")
            elif pe_ratio > 10:
                valuation_risk = 20
                print(f"Valuation Risk: 20 (Low - PE 10-15: {pe_ratio:.1f})")
            else:
                valuation_risk = 0
                print(f"Valuation Risk: 0 (Very Low - PE < 10: {pe_ratio:.1f})")
        else:
            # If PE is missing, check if it's a growth stock by sector/market cap
            if sector in ['Technology', 'Consumer Cyclical'] and market_cap > 10000000000:  # > $10B
                valuation_risk = 70  # Assume high PE for large tech/growth stocks
                print(f"Valuation Risk: 70 (Assumed High - Missing PE, Large {sector} stock)")
            else:
                valuation_risk = 50
                print(f"Valuation Risk: 50 (Default - Missing PE)")
        
        # Add PB ratio consideration
        if pb_ratio is not None and pb_ratio > 10:
            valuation_risk = min(100, valuation_risk + 20)
            print(f"Valuation Risk adjusted: +20 for high PB ratio ({pb_ratio:.1f})")
        
        components['valuation_risk'] = valuation_risk
        
        # 2. Debt Risk (20% weight)
        debt_equity = data.get('debt_to_equity', None)
        if debt_equity is not None:
            if debt_equity <= 0.3:
                debt_risk = 0
                print(f"Debt Risk: 0 (Low - D/E <= 0.3: {debt_equity:.2f})")
            elif debt_equity <= 0.5:
                debt_risk = 20
                print(f"Debt Risk: 20 (Moderate - D/E 0.3-0.5: {debt_equity:.2f})")
            elif debt_equity <= 1.0:
                debt_risk = 40
                print(f"Debt Risk: 40 (High - D/E 0.5-1.0: {debt_equity:.2f})")
            elif debt_equity <= 1.5:
                debt_risk = 60
                print(f"Debt Risk: 60 (Very High - D/E 1.0-1.5: {debt_equity:.2f})")
            else:
                debt_risk = 80
                print(f"Debt Risk: 80 (Extreme - D/E > 1.5: {debt_equity:.2f})")
        else:
            debt_risk = 40
            print(f"Debt Risk: 40 (Default - No data)")
        
        components['debt_risk'] = debt_risk
        
        # 3. Liquidity Risk (15% weight)
        current_ratio = data.get('current_ratio', None)
        if current_ratio is not None:
            if current_ratio >= 2.0:
                liquidity_risk = 0
                print(f"Liquidity Risk: 0 (Low - CR >= 2.0: {current_ratio:.2f})")
            elif current_ratio >= 1.5:
                liquidity_risk = 20
                print(f"Liquidity Risk: 20 (Moderate - CR 1.5-2.0: {current_ratio:.2f})")
            elif current_ratio >= 1.0:
                liquidity_risk = 40
                print(f"Liquidity Risk: 40 (High - CR 1.0-1.5: {current_ratio:.2f})")
            elif current_ratio >= 0.8:
                liquidity_risk = 60
                print(f"Liquidity Risk: 60 (Very High - CR 0.8-1.0: {current_ratio:.2f})")
            else:
                liquidity_risk = 80
                print(f"Liquidity Risk: 80 (Extreme - CR < 0.8: {current_ratio:.2f})")
        else:
            liquidity_risk = 40
            print(f"Liquidity Risk: 40 (Default - No data)")
        
        components['liquidity_risk'] = liquidity_risk
        
        # 4. Profitability Risk (15% weight)
        roe = data.get('roe', None)
        if roe is not None:
            if roe >= 20:
                profitability_risk = 0
                print(f"Profitability Risk: 0 (Low - ROE >= 20%: {roe:.1f}%)")
            elif roe >= 15:
                profitability_risk = 20
                print(f"Profitability Risk: 20 (Moderate - ROE 15-20%: {roe:.1f}%)")
            elif roe >= 10:
                profitability_risk = 40
                print(f"Profitability Risk: 40 (High - ROE 10-15%: {roe:.1f}%)")
            elif roe >= 5:
                profitability_risk = 60
                print(f"Profitability Risk: 60 (Very High - ROE 5-10%: {roe:.1f}%)")
            elif roe >= 0:
                profitability_risk = 80
                print(f"Profitability Risk: 80 (Extreme - ROE 0-5%: {roe:.1f}%)")
            else:
                profitability_risk = 100
                print(f"Profitability Risk: 100 (Critical - ROE < 0%: {roe:.1f}%)")
        else:
            profitability_risk = 50
            print(f"Profitability Risk: 50 (Default - No data)")
        
        components['profitability_risk'] = profitability_risk
        
        # 5. Growth Risk (15% weight)
        revenue_data = self.get_historical_revenue_data(ticker)
        revenue_growth = revenue_data.get('revenue_growth', 0)
        
        if revenue_growth < -10:
            growth_risk = 100
            print(f"Growth Risk: 100 (Critical - Revenue declining > 10%: {revenue_growth:.1f}%)")
        elif revenue_growth < -5:
            growth_risk = 80
            print(f"Growth Risk: 80 (Very High - Revenue declining 5-10%: {revenue_growth:.1f}%)")
        elif revenue_growth < 0:
            growth_risk = 60
            print(f"Growth Risk: 60 (High - Revenue declining 0-5%: {revenue_growth:.1f}%)")
        elif revenue_growth < 5:
            growth_risk = 40
            print(f"Growth Risk: 40 (Moderate - Revenue growth 0-5%: {revenue_growth:.1f}%)")
        elif revenue_growth < 15:
            growth_risk = 20
            print(f"Growth Risk: 20 (Low - Revenue growth 5-15%: {revenue_growth:.1f}%)")
        else:
            growth_risk = 0
            print(f"Growth Risk: 0 (Very Low - Revenue growth > 15%: {revenue_growth:.1f}%)")
        
        components['growth_risk'] = growth_risk
        
        # 6. Volatility Risk (10% weight)
        volatility_risk = 0
        
        # High volatility sectors
        if sector in ['Technology', 'Consumer Cyclical', 'Communication Services']:
            volatility_risk += 30
            print(f"Volatility Risk: +30 (High volatility sector: {sector})")
        
        # Large market cap growth stocks
        if market_cap > 100000000000:  # > $100B
            volatility_risk += 20
            print(f"Volatility Risk: +20 (Large cap growth stock)")
        elif market_cap > 10000000000:  # > $10B
            volatility_risk += 10
            print(f"Volatility Risk: +10 (Mid-large cap)")
        
        # High PE stocks (even if PE is missing, assume high for large tech)
        if pe_ratio is None and sector in ['Technology', 'Consumer Cyclical'] and market_cap > 10000000000:
            volatility_risk += 20
            print(f"Volatility Risk: +20 (Assumed high PE growth stock)")
        elif pe_ratio and pe_ratio > 30:
            volatility_risk += 30
            print(f"Volatility Risk: +30 (Very high PE: {pe_ratio:.1f})")
        elif pe_ratio and pe_ratio > 20:
            volatility_risk += 20
            print(f"Volatility Risk: +20 (High PE: {pe_ratio:.1f})")
        
        volatility_risk = min(100, volatility_risk)
        print(f"Final Volatility Risk: {volatility_risk}")
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
        
        print(f"\n=== Enhanced Risk Score Components ===")
        print(f"Valuation Risk: {valuation_risk} * 0.25 = {valuation_risk * 0.25:.1f}")
        print(f"Debt Risk: {debt_risk} * 0.20 = {debt_risk * 0.20:.1f}")
        print(f"Liquidity Risk: {liquidity_risk} * 0.15 = {liquidity_risk * 0.15:.1f}")
        print(f"Profitability Risk: {profitability_risk} * 0.15 = {profitability_risk * 0.15:.1f}")
        print(f"Growth Risk: {growth_risk} * 0.15 = {growth_risk * 0.15:.1f}")
        print(f"Volatility Risk: {volatility_risk} * 0.10 = {volatility_risk * 0.10:.1f}")
        print(f"Total Enhanced Risk Score: {risk_score:.1f}")
        
        return risk_score, components
    
    def normalize_score_to_5_levels(self, score: float, score_type: str) -> Tuple[int, str, str]:
        """Normalize score to 5 levels"""
        if score_type == 'risk_assessment':
            # For risk assessment, lower is better (less risk)
            if score <= 20:
                normalized = 5
                grade = "Strong Buy"
                description = "Very low risk"
            elif score <= 40:
                normalized = 4
                grade = "Buy"
                description = "Low risk"
            elif score <= 60:
                normalized = 3
                grade = "Neutral"
                description = "Moderate risk"
            elif score <= 80:
                normalized = 2
                grade = "Sell"
                description = "High risk"
            else:
                normalized = 1
                grade = "Strong Sell"
                description = "Very high risk"
        else:
            # For other scores, higher is better
            if score >= 80:
                normalized = 5
                grade = "Strong Buy"
                description = "Excellent"
            elif score >= 60:
                normalized = 4
                grade = "Buy"
                description = "Good"
            elif score >= 40:
                normalized = 3
                grade = "Neutral"
                description = "Average"
            elif score >= 20:
                normalized = 2
                grade = "Sell"
                description = "Poor"
            else:
                normalized = 1
                grade = "Strong Sell"
                description = "Very poor"
        
        return normalized, grade, description
    
    def test_enhanced_risk_assessment(self, ticker: str):
        """Test the enhanced risk assessment for a specific ticker"""
        print(f"\n{'='*80}")
        print(f"ENHANCED RISK ASSESSMENT TEST FOR {ticker}")
        print(f"{'='*80}")
        
        # Get fundamental data (simplified for testing)
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM company_fundamentals 
                    WHERE ticker = %s 
                    ORDER BY last_updated DESC 
                    LIMIT 1
                """, (ticker,))
                fundamental_data = cursor.fetchone()
                
                if not fundamental_data:
                    print(f"ERROR: No fundamental data found for {ticker}")
                    return
                
                fundamental_data = dict(fundamental_data)
                
                # Get current price
                cursor.execute("""
                    SELECT close FROM daily_charts 
                    WHERE ticker = %s 
                    ORDER BY date DESC 
                    LIMIT 1
                """, (ticker,))
                price_result = cursor.fetchone()
                current_price = price_result['close'] if price_result else None
                
                if not current_price:
                    print(f"ERROR: No current price found for {ticker}")
                    return
        
        # Calculate basic ratios
        ratios = {}
        try:
            revenue = fundamental_data.get('revenue', 0)
            net_income = fundamental_data.get('net_income', 0)
            total_assets = fundamental_data.get('total_assets', 0)
            total_equity = fundamental_data.get('total_equity', 0)
            total_debt = fundamental_data.get('total_debt', 0)
            current_assets = fundamental_data.get('current_assets', 0)
            current_liabilities = fundamental_data.get('current_liabilities', 0)
            book_value_per_share = fundamental_data.get('book_value_per_share', 0)
            earnings_per_share = fundamental_data.get('earnings_per_share', 0)
            
            print(f"\n=== {ticker} Raw Data ===")
            print(f"Revenue: ${revenue:,.0f}")
            print(f"Net Income: ${net_income:,.0f}")
            print(f"Total Assets: ${total_assets:,.0f}")
            print(f"Total Equity: ${total_equity:,.0f}")
            print(f"Total Debt: ${total_debt:,.0f}")
            print(f"Current Assets: ${current_assets:,.0f}")
            print(f"Current Liabilities: ${current_liabilities:,.0f}")
            print(f"Book Value per Share: ${book_value_per_share if book_value_per_share else 'None'}")
            print(f"Earnings per Share: ${earnings_per_share if earnings_per_share else 'None'}")
            print(f"Current Price: ${current_price if current_price else 'None'}")
            
            # Calculate ratios
            if earnings_per_share and earnings_per_share > 0 and current_price:
                ratios['pe_ratio'] = current_price / earnings_per_share
                print(f"Calculated PE Ratio: {ratios['pe_ratio']:.2f}")
            else:
                ratios['pe_ratio'] = None
                print(f"PE Ratio: Cannot calculate (EPS: {earnings_per_share}, Price: {current_price})")
            
            if book_value_per_share and book_value_per_share > 0 and current_price:
                ratios['pb_ratio'] = current_price / book_value_per_share
                print(f"Calculated PB Ratio: {ratios['pb_ratio']:.2f}")
            else:
                ratios['pb_ratio'] = None
                print(f"PB Ratio: Cannot calculate (BVPS: {book_value_per_share}, Price: {current_price})")
            
            if total_equity and total_equity > 0:
                ratios['roe'] = (net_income / total_equity) * 100
                print(f"Calculated ROE: {ratios['roe']:.2f}%")
            else:
                ratios['roe'] = None
                print(f"ROE: Cannot calculate (Equity: {total_equity})")
            
            if total_assets and total_assets > 0:
                ratios['roa'] = (net_income / total_assets) * 100
                print(f"Calculated ROA: {ratios['roa']:.2f}%")
            else:
                ratios['roa'] = None
                print(f"ROA: Cannot calculate (Assets: {total_assets})")
            
            if total_equity and total_equity > 0 and total_debt:
                ratios['debt_to_equity'] = total_debt / total_equity
                print(f"Calculated Debt-to-Equity: {ratios['debt_to_equity']:.2f}")
            else:
                ratios['debt_to_equity'] = None
                print(f"Debt-to-Equity: Cannot calculate (Debt: {total_debt}, Equity: {total_equity})")
            
            if current_liabilities and current_liabilities > 0 and current_assets:
                ratios['current_ratio'] = current_assets / current_liabilities
                print(f"Calculated Current Ratio: {ratios['current_ratio']:.2f}")
            else:
                ratios['current_ratio'] = None
                print(f"Current Ratio: Cannot calculate (CA: {current_assets}, CL: {current_liabilities})")
            
        except Exception as e:
            logger.error(f"Error calculating ratios: {e}")
            return
        
        # Combine all data
        all_data = {**fundamental_data, **ratios}
        
        # Calculate enhanced risk assessment score
        risk_score, risk_components = self.calculate_enhanced_risk_assessment_score(all_data, ticker)
        
        # Normalize the score
        normalized_score, grade, description = self.normalize_score_to_5_levels(risk_score, 'risk_assessment')
        
        print(f"\n=== FINAL ENHANCED RESULT ===")
        print(f"{ticker} Enhanced Risk Assessment Score: {risk_score:.1f}")
        print(f"Normalized: {normalized_score} ({grade} - {description})")
        
        # Professor analysis
        print(f"\n=== PROFESSOR ANALYSIS ===")
        if normalized_score >= 4:
            print(f"❌ PROBLEM: {ticker} got a 'Buy' or 'Strong Buy' risk score, which may be incorrect!")
        elif normalized_score <= 2:
            print(f"✅ RESULT: {ticker} got an appropriate high-risk score")
        else:
            print(f"⚠️  MODERATE: {ticker} got a neutral risk score")

if __name__ == "__main__":
    calculator = EnhancedRiskAssessmentCalculator()
    
    # Test with TSLA and a few other stocks
    test_tickers = ['TSLA', 'AAPL', 'MSFT', 'NVDA']
    
    for ticker in test_tickers:
        calculator.test_enhanced_risk_assessment(ticker) 