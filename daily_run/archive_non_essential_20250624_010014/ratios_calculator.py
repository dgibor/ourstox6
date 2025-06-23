#!/usr/bin/env python3
"""
Consolidated financial ratios calculator
"""

import math
from typing import Dict, Optional, Tuple, Any
from database import DatabaseManager
from config import Config

class RatiosCalculator:
    """Calculate financial ratios with exact formulas and edge case handling"""
    
    def __init__(self, use_database: bool = True):
        """Initialize calculator"""
        self.use_database = use_database
        self.db = DatabaseManager() if use_database else None
    
    def calculate_pe_ratio(self, current_price: float, diluted_eps_ttm: float) -> Tuple[Optional[float], str]:
        """P/E = Current Market Price / Diluted EPS (TTM)"""
        if diluted_eps_ttm is None or diluted_eps_ttm <= 0:
            return None, "N/A - Negative Earnings"
        
        if current_price is None or current_price <= 0:
            return None, "N/A - Invalid Price"
        
        pe_ratio = current_price / diluted_eps_ttm
        capped_ratio = min(pe_ratio, 999)
        
        quality_flag = "Normal"
        if pe_ratio > 999:
            quality_flag = "Capped - Extreme Value"
        
        return round(capped_ratio, 2), quality_flag
    
    def calculate_pb_ratio(self, market_cap: float, shareholders_equity: float) -> Tuple[Optional[float], str]:
        """P/B = Market Capitalization / Total Shareholders' Equity"""
        if shareholders_equity is None or shareholders_equity <= 0:
            return None, "N/A - Negative Book Value"
        
        if market_cap is None or market_cap <= 0:
            return None, "N/A - Invalid Market Cap"
        
        pb_ratio = market_cap / shareholders_equity
        return round(pb_ratio, 2), "Normal"
    
    def calculate_ps_ratio(self, market_cap: float, revenue_ttm: float) -> Tuple[Optional[float], str]:
        """P/S = Market Capitalization / Revenue (TTM)"""
        if revenue_ttm is None or revenue_ttm <= 0:
            return None, "N/A - No Revenue"
        
        if market_cap is None or market_cap <= 0:
            return None, "N/A - Invalid Market Cap"
        
        ps_ratio = market_cap / revenue_ttm
        capped_ratio = min(ps_ratio, 50)
        
        quality_flag = "Normal"
        if ps_ratio > 50:
            quality_flag = "Capped - High P/S Ratio"
        
        return round(capped_ratio, 2), quality_flag
    
    def calculate_ev_ebitda(self, market_cap: float, total_debt: float, 
                           cash: float, ebitda_ttm: float) -> Tuple[Optional[float], str]:
        """EV/EBITDA = (Market Cap + Total Debt - Cash) / EBITDA (TTM)"""
        if ebitda_ttm is None or ebitda_ttm <= 0:
            return None, "N/A - Negative EBITDA"
        
        if market_cap is None or market_cap <= 0:
            return None, "N/A - Invalid Market Cap"
        
        total_debt = total_debt or 0
        cash = cash or 0
        
        enterprise_value = market_cap + total_debt - cash
        ev_ebitda_ratio = enterprise_value / ebitda_ttm
        
        return round(ev_ebitda_ratio, 2), "Normal"
    
    def calculate_roe(self, net_income_ttm: float, shareholders_equity: float) -> Tuple[Optional[float], str]:
        """ROE = Net Income (TTM) / Shareholders' Equity * 100"""
        if shareholders_equity is None or shareholders_equity <= 0:
            return None, "N/A - Negative Book Value"
        
        if net_income_ttm is None:
            return None, "N/A - No Net Income Data"
        
        roe = (net_income_ttm / shareholders_equity) * 100
        return round(roe, 2), "Normal"
    
    def calculate_roa(self, net_income_ttm: float, total_assets: float) -> Tuple[Optional[float], str]:
        """ROA = Net Income (TTM) / Total Assets * 100"""
        if total_assets is None or total_assets <= 0:
            return None, "N/A - Invalid Total Assets"
        
        if net_income_ttm is None:
            return None, "N/A - No Net Income Data"
        
        roa = (net_income_ttm / total_assets) * 100
        return round(roa, 2), "Normal"
    
    def calculate_debt_to_equity(self, total_debt: float, shareholders_equity: float) -> Tuple[Optional[float], str]:
        """Debt to Equity = Total Debt / Shareholders' Equity"""
        if shareholders_equity is None or shareholders_equity <= 0:
            return None, "N/A - Negative Book Value"
        
        if total_debt is None:
            total_debt = 0
        
        debt_to_equity = total_debt / shareholders_equity
        return round(debt_to_equity, 2), "Normal"
    
    def calculate_current_ratio(self, current_assets: float, current_liabilities: float) -> Tuple[Optional[float], str]:
        """Current Ratio = Current Assets / Current Liabilities"""
        if current_liabilities is None or current_liabilities <= 0:
            return None, "N/A - No Current Liabilities"
        
        if current_assets is None:
            return None, "N/A - No Current Assets"
        
        current_ratio = current_assets / current_liabilities
        return round(current_ratio, 2), "Normal"
    
    def calculate_graham_number(self, diluted_eps_ttm: float, book_value_per_share: float) -> Tuple[Optional[float], str]:
        """Graham Number = √(15 × EPS × Book Value per Share)"""
        if (diluted_eps_ttm is None or diluted_eps_ttm <= 0 or 
            book_value_per_share is None or book_value_per_share <= 0):
            return None, "N/A - Requires Positive Earnings & Book Value"
        
        graham_number = math.sqrt(15 * diluted_eps_ttm * book_value_per_share)
        return round(graham_number, 2), "Normal"
    
    def get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get stock data from database"""
        if not self.use_database or not self.db:
            return None
        
        try:
            # Get fundamental data from financials table
            query = """
                SELECT 
                    market_cap, shares_outstanding, revenue_ttm, net_income_ttm,
                    ebitda_ttm, total_debt, shareholders_equity, cash_and_equivalents,
                    diluted_eps_ttm, book_value_per_share, total_assets,
                    current_assets, current_liabilities, operating_income_ttm
                FROM financials 
                WHERE ticker = %s
            """
            results = self.db.execute_query(query, (ticker,))
            
            if not results:
                return None
            
            row = results[0]
            
            # Get latest price
            current_price = self.db.get_latest_price(ticker)
            
            return {
                'current_price': current_price,
                'market_cap': float(row[0]) if row[0] else None,
                'shares_outstanding': float(row[1]) if row[1] else None,
                'revenue_ttm': float(row[2]) if row[2] else None,
                'net_income_ttm': float(row[3]) if row[3] else None,
                'ebitda_ttm': float(row[4]) if row[4] else None,
                'total_debt': float(row[5]) if row[5] else None,
                'shareholders_equity': float(row[6]) if row[6] else None,
                'cash_and_equivalents': float(row[7]) if row[7] else None,
                'diluted_eps_ttm': float(row[8]) if row[8] else None,
                'book_value_per_share': float(row[9]) if row[9] else None,
                'total_assets': float(row[10]) if row[10] else None,
                'current_assets': float(row[11]) if row[11] else None,
                'current_liabilities': float(row[12]) if row[12] else None,
                'operating_income_ttm': float(row[13]) if row[13] else None
            }
            
        except Exception as e:
            print(f"Error getting stock data for {ticker}: {e}")
            return None
    
    def calculate_all_ratios(self, ticker: str = None, stock_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate all financial ratios"""
        if not stock_data:
            if ticker:
                stock_data = self.get_stock_data(ticker)
            else:
                raise ValueError("Either ticker or stock_data must be provided")
        
        if not stock_data:
            return {'error': 'No stock data available'}
        
        ratios = {}
        notes = []
        
        # Extract data
        current_price = stock_data.get('current_price')
        market_cap = stock_data.get('market_cap')
        revenue_ttm = stock_data.get('revenue_ttm')
        net_income_ttm = stock_data.get('net_income_ttm')
        ebitda_ttm = stock_data.get('ebitda_ttm')
        total_debt = stock_data.get('total_debt')
        shareholders_equity = stock_data.get('shareholders_equity')
        cash_and_equivalents = stock_data.get('cash_and_equivalents')
        diluted_eps_ttm = stock_data.get('diluted_eps_ttm')
        book_value_per_share = stock_data.get('book_value_per_share')
        total_assets = stock_data.get('total_assets')
        current_assets = stock_data.get('current_assets')
        current_liabilities = stock_data.get('current_liabilities')
        
        # Calculate ratios
        ratios['pe_ratio'], pe_note = self.calculate_pe_ratio(current_price, diluted_eps_ttm)
        if pe_note != "Normal":
            notes.append(f"P/E: {pe_note}")
        
        ratios['pb_ratio'], pb_note = self.calculate_pb_ratio(market_cap, shareholders_equity)
        if pb_note != "Normal":
            notes.append(f"P/B: {pb_note}")
        
        ratios['ps_ratio'], ps_note = self.calculate_ps_ratio(market_cap, revenue_ttm)
        if ps_note != "Normal":
            notes.append(f"P/S: {ps_note}")
        
        ratios['ev_ebitda'], ev_note = self.calculate_ev_ebitda(market_cap, total_debt, cash_and_equivalents, ebitda_ttm)
        if ev_note != "Normal":
            notes.append(f"EV/EBITDA: {ev_note}")
        
        ratios['roe'], roe_note = self.calculate_roe(net_income_ttm, shareholders_equity)
        if roe_note != "Normal":
            notes.append(f"ROE: {roe_note}")
        
        ratios['roa'], roa_note = self.calculate_roa(net_income_ttm, total_assets)
        if roa_note != "Normal":
            notes.append(f"ROA: {roa_note}")
        
        ratios['debt_to_equity'], dte_note = self.calculate_debt_to_equity(total_debt, shareholders_equity)
        if dte_note != "Normal":
            notes.append(f"Debt/Equity: {dte_note}")
        
        ratios['current_ratio'], cr_note = self.calculate_current_ratio(current_assets, current_liabilities)
        if cr_note != "Normal":
            notes.append(f"Current Ratio: {cr_note}")
        
        ratios['graham_number'], gn_note = self.calculate_graham_number(diluted_eps_ttm, book_value_per_share)
        if gn_note != "Normal":
            notes.append(f"Graham Number: {gn_note}")
        
        # Calculate enterprise value
        if market_cap and total_debt is not None and cash_and_equivalents is not None:
            ratios['enterprise_value'] = market_cap + total_debt - cash_and_equivalents
        
        # Calculate data quality score
        valid_ratios = sum(1 for ratio in ratios.values() if ratio is not None)
        total_ratios = len(ratios)
        data_quality_score = int((valid_ratios / total_ratios) * 100) if total_ratios > 0 else 0
        
        return {
            'ratios': ratios,
            'notes': notes,
            'data_quality_score': data_quality_score,
            'price_used': current_price
        }
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.disconnect()

def test_ratios_calculator():
    """Test ratios calculator functionality"""
    print("🧪 Testing Ratios Calculator")
    print("=" * 30)
    
    # Test without database
    calculator = RatiosCalculator(use_database=False)
    
    # Test individual calculations
    pe_ratio, pe_note = calculator.calculate_pe_ratio(150.0, 2.5)
    print(f"✅ P/E Ratio: {pe_ratio} ({pe_note})")
    
    pb_ratio, pb_note = calculator.calculate_pb_ratio(1000000000, 500000000)
    print(f"✅ P/B Ratio: {pb_ratio} ({pb_note})")
    
    ps_ratio, ps_note = calculator.calculate_ps_ratio(1000000000, 800000000)
    print(f"✅ P/S Ratio: {ps_ratio} ({ps_note})")
    
    ev_ebitda, ev_note = calculator.calculate_ev_ebitda(1000000000, 200000000, 50000000, 150000000)
    print(f"✅ EV/EBITDA: {ev_ebitda} ({ev_note})")
    
    graham_number, gn_note = calculator.calculate_graham_number(2.5, 25.0)
    print(f"✅ Graham Number: {graham_number} ({gn_note})")
    
    # Test with database
    db_calculator = RatiosCalculator(use_database=True)
    try:
        result = db_calculator.calculate_all_ratios('AAPL')
        if 'error' not in result:
            print(f"✅ AAPL ratios calculated: {result['data_quality_score']}% quality")
            print(f"  P/E: {result['ratios'].get('pe_ratio', 'N/A')}")
            print(f"  P/B: {result['ratios'].get('pb_ratio', 'N/A')}")
            print(f"  P/S: {result['ratios'].get('ps_ratio', 'N/A')}")
        else:
            print(f"⚠️  AAPL calculation failed: {result['error']}")
    except Exception as e:
        print(f"❌ Database calculation error: {e}")
    finally:
        db_calculator.close()
    
    calculator.close()
    print("✅ Ratios calculator test completed")

if __name__ == "__main__":
    test_ratios_calculator() 