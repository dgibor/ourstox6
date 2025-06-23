import os
import psycopg2
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import math

# Add parent directory to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

class FinancialRatiosCalculator:
    """Calculate financial ratios with exact formulas and edge case handling"""
    
    def __init__(self):
        """Initialize database connection and API rate limiter"""
        # Configure logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Initialize connections with error handling
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cur = self.conn.cursor()
            # Try to import API rate limiter
            try:
                from utility_functions.api_rate_limiter import APIRateLimiter
                self.api_limiter = APIRateLimiter()
            except ImportError:
                self.logger.warning("API rate limiter not available")
                self.api_limiter = None
        except Exception as e:
            self.logger.warning(f"Database connection failed during initialization: {e}")
            self.conn = None
            self.cur = None
            self.api_limiter = None

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

    def get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get all required data for ratio calculations from database"""
        if not self.cur:
            self.logger.error("Database connection not available")
            return None
            
        try:
            # Get stock data
            self.cur.execute("""
                SELECT ticker, market_cap, shares_outstanding, diluted_eps_ttm, 
                       book_value_per_share, revenue_ttm, net_income_ttm, 
                       total_assets, total_debt, shareholders_equity, 
                       current_assets, current_liabilities, cash_and_equivalents,
                       operating_income, ebitda_ttm
                FROM stocks 
                WHERE ticker = %s
            """, (ticker,))
            
            stock_data = self.cur.fetchone()
            if not stock_data:
                return None
            
            # Get latest price from daily_charts
            self.cur.execute("""
                SELECT close FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """, (ticker,))
            
            price_data = self.cur.fetchone()
            current_price = price_data[0] / 100.0 if price_data and price_data[0] else None  # Convert cents to dollars
            
            # Calculate derived values
            current_assets = float(stock_data[10]) if stock_data[10] else 0
            current_liabilities = float(stock_data[11]) if stock_data[11] else 0
            working_capital = current_assets - current_liabilities
            
            return {
                'ticker': stock_data[0],
                'current_price': float(current_price) if current_price else None,
                'market_cap': float(stock_data[1]) if stock_data[1] else None,
                'shares_outstanding': float(stock_data[2]) if stock_data[2] else None,
                'diluted_eps_ttm': float(stock_data[3]) if stock_data[3] else None,
                'book_value_per_share': float(stock_data[4]) if stock_data[4] else None,
                'revenue_ttm': float(stock_data[5]) if stock_data[5] else None,
                'net_income_ttm': float(stock_data[6]) if stock_data[6] else None,
                'total_assets': float(stock_data[7]) if stock_data[7] else None,
                'total_debt': float(stock_data[8]) if stock_data[8] else None,
                'shareholders_equity': float(stock_data[9]) if stock_data[9] else None,
                'working_capital': float(working_capital),
                'cash_and_equivalents': float(stock_data[12]) if stock_data[12] else None,
                'operating_income': float(stock_data[13]) if stock_data[13] else None,
                'ebitda_ttm': float(stock_data[14]) if stock_data[14] else None,
                'sales': float(stock_data[5]) if stock_data[5] else None  # revenue_ttm
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stock data for {ticker}: {e}")
            return None

    def calculate_all_ratios(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Calculate all financial ratios for a given ticker"""
        try:
            stock_data = self.get_stock_data(ticker)
            if not stock_data:
                self.logger.warning(f"No data available for {ticker}")
                return None
            
            ratios = {}
            
            # Calculate P/E Ratio
            pe_ratio, pe_flag = self.calculate_pe_ratio(
                stock_data['current_price'], 
                stock_data['diluted_eps_ttm']
            )
            ratios['pe_ratio'] = {'value': pe_ratio, 'quality_flag': pe_flag}
            
            # Calculate P/B Ratio
            pb_ratio, pb_flag = self.calculate_pb_ratio(
                stock_data['market_cap'], 
                stock_data['shareholders_equity']
            )
            ratios['pb_ratio'] = {'value': pb_ratio, 'quality_flag': pb_flag}
            
            # Calculate EV/EBITDA
            ev_ebitda, ev_flag = self.calculate_ev_ebitda(
                stock_data['market_cap'],
                stock_data['total_debt'],
                stock_data['cash_and_equivalents'],
                stock_data['ebitda_ttm']
            )
            ratios['ev_ebitda'] = {'value': ev_ebitda, 'quality_flag': ev_flag}
            
            # Calculate P/S Ratio
            ps_ratio, ps_flag = self.calculate_ps_ratio(
                stock_data['market_cap'],
                stock_data['revenue_ttm']
            )
            ratios['ps_ratio'] = {'value': ps_ratio, 'quality_flag': ps_flag}
            
            # Calculate Graham Number
            graham_number, gn_flag = self.calculate_graham_number(
                stock_data['diluted_eps_ttm'],
                stock_data['book_value_per_share']
            )
            ratios['graham_number'] = {'value': graham_number, 'quality_flag': gn_flag}
            
            return ratios
            
        except Exception as e:
            self.logger.error(f"Error calculating ratios for {ticker}: {e}")
            return None

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

    def close(self):
        """Close database connections"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        if self.api_limiter:
            self.api_limiter.close()

if __name__ == "__main__":
    calculator = FinancialRatiosCalculator()
    calculator.test_calculations()
    calculator.close() 