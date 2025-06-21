import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv()

class SimpleFinancialRatiosCalculator:
    """Calculate financial ratios with exact formulas and edge case handling"""
    
    def __init__(self):
        """Initialize calculator without database connection"""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def calculate_pe_ratio(self, current_price: float, diluted_eps_ttm: float) -> tuple[Optional[float], str]:
        """
        P/E = Current Market Price / Diluted EPS (TTM)
        - Use diluted EPS for conservative calculation
        - If EPS ≤ 0, return None and flag as "N/A - Negative Earnings"
        - Cap display at 999 to handle extreme cases
        """
        if diluted_eps_ttm is None or diluted_eps_ttm <= 0:
            return None, "N/A - Negative Earnings"
        
        if current_price is None or current_price <= 0:
            return None, "N/A - Invalid Price"
        
        pe_ratio = current_price / diluted_eps_ttm
        capped_ratio = min(pe_ratio, 999)  # Cap extreme values
        
        quality_flag = "Normal"
        if pe_ratio > 999:
            quality_flag = "Capped - Extreme Value"
        
        return capped_ratio, quality_flag

    def calculate_pb_ratio(self, market_cap: float, shareholders_equity: float) -> tuple[Optional[float], str]:
        """
        P/B = Market Capitalization / Total Shareholders' Equity
        - Use most recent quarterly shareholders' equity
        - If book value ≤ 0, return None and flag as "N/A - Negative Book Value"
        """
        if shareholders_equity is None or shareholders_equity <= 0:
            return None, "N/A - Negative Book Value"
        
        if market_cap is None or market_cap <= 0:
            return None, "N/A - Invalid Market Cap"
        
        pb_ratio = market_cap / shareholders_equity
        return pb_ratio, "Normal"

    def calculate_ev_ebitda(self, market_cap: float, total_debt: float, 
                           cash: float, ebitda_ttm: float) -> tuple[Optional[float], str]:
        """
        Enterprise Value = Market Cap + Total Debt - Cash and Cash Equivalents
        EV/EBITDA = Enterprise Value / EBITDA (TTM)
        - If EBITDA ≤ 0, return None and flag as "N/A - Negative EBITDA"
        """
        if ebitda_ttm is None or ebitda_ttm <= 0:
            return None, "N/A - Negative EBITDA"
        
        if market_cap is None or market_cap <= 0:
            return None, "N/A - Invalid Market Cap"
        
        # Handle None values for debt and cash
        total_debt = total_debt or 0
        cash = cash or 0
        
        enterprise_value = market_cap + total_debt - cash
        ev_ebitda_ratio = enterprise_value / ebitda_ttm
        
        return ev_ebitda_ratio, "Normal"

    def calculate_ps_ratio(self, market_cap: float, revenue_ttm: float) -> tuple[Optional[float], str]:
        """
        P/S = Market Capitalization / Revenue (TTM)
        - Always use TTM revenue for recency
        - Most reliable for loss-making companies
        - Cap at 50 for display purposes
        """
        if revenue_ttm is None or revenue_ttm <= 0:
            return None, "N/A - No Revenue"
        
        if market_cap is None or market_cap <= 0:
            return None, "N/A - Invalid Market Cap"
        
        ps_ratio = market_cap / revenue_ttm
        capped_ratio = min(ps_ratio, 50)  # Cap at 50
        
        quality_flag = "Normal"
        if ps_ratio > 50:
            quality_flag = "Capped - High P/S Ratio"
        
        return capped_ratio, quality_flag

    def calculate_graham_number(self, diluted_eps_ttm: float, book_value_per_share: float) -> tuple[Optional[float], str]:
        """
        Graham Number = √(15 × Diluted EPS (TTM) × Book Value per Share)
        
        Where:
        - 15 = Maximum P/E ratio for defensive investors
        - EPS must be positive (if negative, return None)
        - BVPS must be positive (if negative, return None)
        """
        if diluted_eps_ttm is None or diluted_eps_ttm <= 0 or book_value_per_share is None or book_value_per_share <= 0:
            return None, "N/A - Requires Positive Earnings & Book Value"
        
        graham_number = math.sqrt(15 * diluted_eps_ttm * book_value_per_share)
        return graham_number, "Normal"

    def test_calculations(self):
        """Test all ratio calculations with sample data"""
        print("Testing financial ratio calculations...")
        
        # Test P/E Ratio
        pe_ratio, pe_flag = self.calculate_pe_ratio(150.0, 2.5)
        print(f"P/E Ratio: {pe_ratio} ({pe_flag})")
        
        # Test P/B Ratio
        pb_ratio, pb_flag = self.calculate_pb_ratio(1000000000, 500000000)
        print(f"P/B Ratio: {pb_ratio} ({pb_flag})")
        
        # Test EV/EBITDA
        ev_ebitda, ev_flag = self.calculate_ev_ebitda(1000000000, 200000000, 50000000, 150000000)
        print(f"EV/EBITDA: {ev_ebitda} ({ev_flag})")
        
        # Test P/S Ratio
        ps_ratio, ps_flag = self.calculate_ps_ratio(1000000000, 800000000)
        print(f"P/S Ratio: {ps_ratio} ({ps_flag})")
        
        # Test Graham Number
        graham_number, gn_flag = self.calculate_graham_number(2.5, 25.0)
        print(f"Graham Number: {graham_number} ({gn_flag})")
        
        print("All tests completed!")

if __name__ == "__main__":
    calculator = SimpleFinancialRatiosCalculator()
    calculator.test_calculations() 