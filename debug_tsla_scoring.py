#!/usr/bin/env python3
"""
Debug script to examine TSLA's scoring calculations
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

class TSLAFundamentalDebugger:
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
    
    def get_tsla_fundamental_data(self) -> Dict[str, Any]:
        """Get TSLA's fundamental data"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get latest fundamental data
                cursor.execute("""
                    SELECT * FROM company_fundamentals 
                    WHERE ticker = 'TSLA' 
                    ORDER BY last_updated DESC 
                    LIMIT 1
                """)
                fundamental_data = cursor.fetchone()
                
                if fundamental_data:
                    return dict(fundamental_data)
                return {}
    
    def get_tsla_financial_ratios(self) -> Dict[str, Any]:
        """Get TSLA's financial ratios"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM financial_ratios 
                    WHERE ticker = 'TSLA' 
                    ORDER BY calculation_date DESC 
                    LIMIT 1
                """)
                ratio_data = cursor.fetchone()
                
                if ratio_data:
                    return dict(ratio_data)
                return {}
    
    def get_tsla_current_price(self) -> float:
        """Get TSLA's current price"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT close FROM daily_charts 
                    WHERE ticker = 'TSLA' 
                    ORDER BY date DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                return result['close'] if result else None
    
    def calculate_missing_ratios(self, fundamental_data: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """Calculate missing ratios for TSLA"""
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
            
            print(f"\n=== TSLA Raw Data ===")
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
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating ratios: {e}")
            return {}
    
    def calculate_risk_assessment_score_debug(self, data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Debug version of risk assessment score calculation"""
        components = {}
        
        print(f"\n=== Risk Assessment Score Calculation ===")
        
        # Debt Risk (35% weight)
        debt_equity = data.get('debt_to_equity', None)
        print(f"Debt-to-Equity Ratio: {debt_equity}")
        
        if debt_equity is not None:
            if debt_equity <= 0.5:
                debt_risk = 0
                print(f"Debt Risk: 0 (Low Risk - D/E <= 0.5)")
            elif debt_equity <= 1.0:
                debt_risk = 25
                print(f"Debt Risk: 25 (Moderate Risk - D/E 0.5-1.0)")
            elif debt_equity <= 1.5:
                debt_risk = 50
                print(f"Debt Risk: 50 (High Risk - D/E 1.0-1.5)")
            elif debt_equity <= 2.0:
                debt_risk = 75
                print(f"Debt Risk: 75 (Very High Risk - D/E 1.5-2.0)")
            else:
                debt_risk = 100
                print(f"Debt Risk: 100 (Extreme Risk - D/E > 2.0)")
        else:
            debt_risk = 50
            print(f"Debt Risk: 50 (Default - No data)")
        
        components['debt_risk'] = debt_risk
        
        # Liquidity Risk (30% weight)
        current_ratio = data.get('current_ratio', None)
        print(f"Current Ratio: {current_ratio}")
        
        if current_ratio is not None:
            if current_ratio >= 2.0:
                liquidity_risk = 0
                print(f"Liquidity Risk: 0 (Low Risk - CR >= 2.0)")
            elif current_ratio >= 1.5:
                liquidity_risk = 25
                print(f"Liquidity Risk: 25 (Moderate Risk - CR 1.5-2.0)")
            elif current_ratio >= 1.0:
                liquidity_risk = 50
                print(f"Liquidity Risk: 50 (High Risk - CR 1.0-1.5)")
            elif current_ratio >= 0.8:
                liquidity_risk = 75
                print(f"Liquidity Risk: 75 (Very High Risk - CR 0.8-1.0)")
            else:
                liquidity_risk = 100
                print(f"Liquidity Risk: 100 (Extreme Risk - CR < 0.8)")
        else:
            liquidity_risk = 50
            print(f"Liquidity Risk: 50 (Default - No data)")
        
        components['liquidity_risk'] = liquidity_risk
        
        # Profitability Risk (20% weight)
        roe = data.get('roe', None)
        print(f"ROE: {roe}%")
        
        if roe is not None:
            if roe >= 15:
                profitability_risk = 0
                print(f"Profitability Risk: 0 (Low Risk - ROE >= 15%)")
            elif roe >= 10:
                profitability_risk = 25
                print(f"Profitability Risk: 25 (Moderate Risk - ROE 10-15%)")
            elif roe >= 5:
                profitability_risk = 50
                print(f"Profitability Risk: 50 (High Risk - ROE 5-10%)")
            elif roe >= 0:
                profitability_risk = 75
                print(f"Profitability Risk: 75 (Very High Risk - ROE 0-5%)")
            else:
                profitability_risk = 100
                print(f"Profitability Risk: 100 (Extreme Risk - ROE < 0%)")
        else:
            profitability_risk = 50
            print(f"Profitability Risk: 50 (Default - No data)")
        
        components['profitability_risk'] = profitability_risk
        
        # Growth Risk (15% weight) - Simplified for now
        growth_risk = 50  # Default
        print(f"Growth Risk: 50 (Default - Not implemented)")
        components['growth_risk'] = growth_risk
        
        # Calculate weighted score
        risk_score = (
            debt_risk * 0.35 +
            liquidity_risk * 0.30 +
            profitability_risk * 0.20 +
            growth_risk * 0.15
        )
        
        print(f"\n=== Risk Score Components ===")
        print(f"Debt Risk: {debt_risk} * 0.35 = {debt_risk * 0.35:.1f}")
        print(f"Liquidity Risk: {liquidity_risk} * 0.30 = {liquidity_risk * 0.30:.1f}")
        print(f"Profitability Risk: {profitability_risk} * 0.20 = {profitability_risk * 0.20:.1f}")
        print(f"Growth Risk: {growth_risk} * 0.15 = {growth_risk * 0.15:.1f}")
        print(f"Total Risk Score: {risk_score:.1f}")
        
        return risk_score, components
    
    def normalize_score_to_5_levels_debug(self, score: float, score_type: str) -> Tuple[int, str, str]:
        """Debug version of score normalization"""
        print(f"\n=== Normalization for {score_type} ===")
        print(f"Original Score: {score:.1f}")
        
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
        
        print(f"Normalized Score: {normalized} ({grade} - {description})")
        return normalized, grade, description
    
    def debug_tsla_scoring(self):
        """Main debug function"""
        print("=== TSLA SCORING DEBUG ===")
        
        # Get fundamental data
        fundamental_data = self.get_tsla_fundamental_data()
        if not fundamental_data:
            print("ERROR: No fundamental data found for TSLA")
            return
        
        # Get financial ratios
        ratio_data = self.get_tsla_financial_ratios()
        
        # Get current price
        current_price = self.get_tsla_current_price()
        if not current_price:
            print("ERROR: No current price found for TSLA")
            return
        
        # Calculate missing ratios
        missing_ratios = self.calculate_missing_ratios(fundamental_data, current_price)
        
        # Combine all data
        all_data = {**fundamental_data, **ratio_data, **missing_ratios}
        
        # Calculate risk assessment score
        risk_score, risk_components = self.calculate_risk_assessment_score_debug(all_data)
        
        # Normalize the score
        normalized_score, grade, description = self.normalize_score_to_5_levels_debug(risk_score, 'risk_assessment')
        
        print(f"\n=== FINAL RESULT ===")
        print(f"TSLA Risk Assessment Score: {risk_score:.1f}")
        print(f"Normalized: {normalized_score} ({grade} - {description})")
        
        # Check if this matches the professor's expectations
        print(f"\n=== PROFESSOR ANALYSIS ===")
        print("Expected: TSLA should be HIGH RISK due to:")
        print("- High PE ratio (if available)")
        print("- Declining sales (if data shows this)")
        print("- High volatility and growth stock characteristics")
        print("- Potential debt issues")
        
        if normalized_score >= 4:
            print("❌ PROBLEM: TSLA got a 'Buy' or 'Strong Buy' risk score, which is incorrect!")
            print("This suggests the risk assessment algorithm is not properly accounting for:")
            print("1. Missing or incorrect PE ratio data")
            print("2. Sales growth/decline data not being used")
            print("3. Growth stock risk factors not being considered")
            print("4. Market volatility factors not being included")
        else:
            print("✅ RESULT: TSLA got an appropriate risk score")

if __name__ == "__main__":
    debugger = TSLAFundamentalDebugger()
    debugger.debug_tsla_scoring() 