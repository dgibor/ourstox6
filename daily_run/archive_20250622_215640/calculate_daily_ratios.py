#!/usr/bin/env python3
"""
Calculate daily financial ratios for all tickers in the database
"""

import os
import psycopg2
import logging
import math
from typing import Dict, Optional, List
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/calculate_daily_ratios.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

class DailyRatioCalculator:
    """Calculate daily financial ratios for all tickers"""
    
    def __init__(self):
        """Initialize database connection"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.today = date.today()
        
    def get_tickers_with_fundamentals(self) -> List[str]:
        """Get all tickers that have fundamental data"""
        try:
            self.cur.execute("""
                SELECT DISTINCT f.ticker 
                FROM financials f
                WHERE f.revenue_ttm IS NOT NULL 
                   OR f.market_cap IS NOT NULL
                ORDER BY f.ticker
            """)
            return [row[0] for row in self.cur.fetchall()]
        except Exception as e:
            logging.error(f"Error getting tickers: {e}")
            return []
    
    def get_latest_price(self, ticker: str) -> Optional[float]:
        """Get the latest price for a ticker from daily_charts"""
        try:
            self.cur.execute("""
                SELECT close FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """, (ticker,))
            result = self.cur.fetchone()
            if result and result[0]:
                return float(result[0]) / 100.0  # Convert cents to dollars
            return None
        except Exception as e:
            logging.error(f"Error getting price for {ticker}: {e}")
            return None
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get fundamental data for a ticker"""
        try:
            self.cur.execute("""
                SELECT 
                    market_cap, shares_outstanding, revenue_ttm, net_income_ttm,
                    ebitda_ttm, total_debt, shareholders_equity, cash_and_equivalents,
                    diluted_eps_ttm, book_value_per_share, total_assets,
                    current_assets, current_liabilities, operating_income_ttm
                FROM financials 
                WHERE ticker = %s
            """, (ticker,))
            
            result = self.cur.fetchone()
            if not result:
                return None
                
            return {
                'market_cap': float(result[0]) if result[0] else None,
                'shares_outstanding': float(result[1]) if result[1] else None,
                'revenue_ttm': float(result[2]) if result[2] else None,
                'net_income_ttm': float(result[3]) if result[3] else None,
                'ebitda_ttm': float(result[4]) if result[4] else None,
                'total_debt': float(result[5]) if result[5] else None,
                'shareholders_equity': float(result[6]) if result[6] else None,
                'cash_and_equivalents': float(result[7]) if result[7] else None,
                'diluted_eps_ttm': float(result[8]) if result[8] else None,
                'book_value_per_share': float(result[9]) if result[9] else None,
                'total_assets': float(result[10]) if result[10] else None,
                'current_assets': float(result[11]) if result[11] else None,
                'current_liabilities': float(result[12]) if result[12] else None,
                'operating_income_ttm': float(result[13]) if result[13] else None
            }
        except Exception as e:
            logging.error(f"Error getting fundamental data for {ticker}: {e}")
            return None
    
    def calculate_ratios(self, ticker: str, fundamental_data: Dict, current_price: float) -> Dict:
        """Calculate all financial ratios"""
        ratios = {}
        notes = []
        
        # Extract data
        market_cap = fundamental_data.get('market_cap')
        shares_outstanding = fundamental_data.get('shares_outstanding')
        revenue_ttm = fundamental_data.get('revenue_ttm')
        net_income_ttm = fundamental_data.get('net_income_ttm')
        ebitda_ttm = fundamental_data.get('ebitda_ttm')
        total_debt = fundamental_data.get('total_debt', 0)
        shareholders_equity = fundamental_data.get('shareholders_equity')
        cash_and_equivalents = fundamental_data.get('cash_and_equivalents', 0)
        diluted_eps_ttm = fundamental_data.get('diluted_eps_ttm')
        book_value_per_share = fundamental_data.get('book_value_per_share')
        current_assets = fundamental_data.get('current_assets')
        current_liabilities = fundamental_data.get('current_liabilities')
        operating_income_ttm = fundamental_data.get('operating_income_ttm')
        
        # 1. P/E Ratio
        if diluted_eps_ttm and diluted_eps_ttm > 0 and current_price:
            ratios['pe_ratio'] = current_price / diluted_eps_ttm
        else:
            ratios['pe_ratio'] = None
            if diluted_eps_ttm and diluted_eps_ttm <= 0:
                notes.append("Negative EPS")
        
        # 2. P/B Ratio
        if shareholders_equity and shareholders_equity > 0 and market_cap:
            ratios['pb_ratio'] = market_cap / shareholders_equity
        else:
            ratios['pb_ratio'] = None
            if shareholders_equity and shareholders_equity <= 0:
                notes.append("Negative book value")
        
        # 3. P/S Ratio
        if revenue_ttm and revenue_ttm > 0 and market_cap:
            ratios['ps_ratio'] = market_cap / revenue_ttm
        else:
            ratios['ps_ratio'] = None
            if not revenue_ttm or revenue_ttm <= 0:
                notes.append("No revenue data")
        
        # 4. EV/EBITDA
        if ebitda_ttm and ebitda_ttm > 0 and market_cap:
            enterprise_value = market_cap + total_debt - cash_and_equivalents
            ratios['ev_ebitda'] = enterprise_value / ebitda_ttm
            ratios['enterprise_value'] = enterprise_value
        else:
            ratios['ev_ebitda'] = None
            ratios['enterprise_value'] = None
            if not ebitda_ttm or ebitda_ttm <= 0:
                notes.append("Negative EBITDA")
        
        # 5. ROE (Return on Equity)
        if shareholders_equity and shareholders_equity > 0 and net_income_ttm:
            ratios['roe'] = (net_income_ttm / shareholders_equity) * 100
        else:
            ratios['roe'] = None
        
        # 6. ROA (Return on Assets)
        if total_assets and total_assets > 0 and net_income_ttm:
            ratios['roa'] = (net_income_ttm / total_assets) * 100
        else:
            ratios['roa'] = None
        
        # 7. Debt to Equity
        if shareholders_equity and shareholders_equity > 0 and total_debt:
            ratios['debt_to_equity'] = total_debt / shareholders_equity
        else:
            ratios['debt_to_equity'] = None
        
        # 8. Current Ratio
        if current_liabilities and current_liabilities > 0 and current_assets:
            ratios['current_ratio'] = current_assets / current_liabilities
        else:
            ratios['current_ratio'] = None
        
        # 9. Gross Margin
        if revenue_ttm and revenue_ttm > 0 and operating_income_ttm:
            ratios['gross_margin'] = (operating_income_ttm / revenue_ttm) * 100
        else:
            ratios['gross_margin'] = None
        
        # 10. Operating Margin
        if revenue_ttm and revenue_ttm > 0 and operating_income_ttm:
            ratios['operating_margin'] = (operating_income_ttm / revenue_ttm) * 100
        else:
            ratios['operating_margin'] = None
        
        # 11. Net Margin
        if revenue_ttm and revenue_ttm > 0 and net_income_ttm:
            ratios['net_margin'] = (net_income_ttm / revenue_ttm) * 100
        else:
            ratios['net_margin'] = None
        
        # 12. Graham Number
        if diluted_eps_ttm and diluted_eps_ttm > 0 and book_value_per_share and book_value_per_share > 0:
            ratios['graham_number'] = math.sqrt(15 * diluted_eps_ttm * book_value_per_share)
        else:
            ratios['graham_number'] = None
            if not (diluted_eps_ttm and diluted_eps_ttm > 0 and book_value_per_share and book_value_per_share > 0):
                notes.append("Cannot calculate Graham Number")
        
        # Calculate data quality score (1-100)
        data_quality_score = self.calculate_data_quality_score(fundamental_data, ratios)
        
        return {
            'ratios': ratios,
            'notes': notes,
            'data_quality_score': data_quality_score,
            'price_used': current_price
        }
    
    def calculate_data_quality_score(self, fundamental_data: Dict, ratios: Dict) -> int:
        """Calculate data quality score based on available data"""
        score = 0
        total_fields = 0
        
        # Check fundamental data completeness
        fundamental_fields = [
            'market_cap', 'shares_outstanding', 'revenue_ttm', 'net_income_ttm',
            'ebitda_ttm', 'total_debt', 'shareholders_equity', 'cash_and_equivalents',
            'diluted_eps_ttm', 'book_value_per_share'
        ]
        
        for field in fundamental_fields:
            total_fields += 1
            if fundamental_data.get(field) is not None:
                score += 1
        
        # Check ratio calculation success
        ratio_fields = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'roe', 'graham_number']
        for field in ratio_fields:
            total_fields += 1
            if ratios.get(field) is not None:
                score += 1
        
        return int((score / total_fields) * 100) if total_fields > 0 else 0
    
    def store_ratios(self, ticker: str, calculation_result: Dict):
        """Store calculated ratios in current_ratios table"""
        try:
            ratios = calculation_result['ratios']
            notes = calculation_result['notes']
            data_quality_score = calculation_result['data_quality_score']
            price_used = calculation_result['price_used']
            
            self.cur.execute("""
                INSERT INTO current_ratios (
                    ticker, calculation_date, price_used, data_quality_score, calculation_notes,
                    pe_ratio, pb_ratio, ps_ratio, ev_ebitda, roe, roa, debt_to_equity,
                    current_ratio, gross_margin, operating_margin, net_margin,
                    graham_number, enterprise_value
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (ticker) DO UPDATE SET
                    calculation_date = EXCLUDED.calculation_date,
                    price_used = EXCLUDED.price_used,
                    data_quality_score = EXCLUDED.data_quality_score,
                    calculation_notes = EXCLUDED.calculation_notes,
                    pe_ratio = EXCLUDED.pe_ratio,
                    pb_ratio = EXCLUDED.pb_ratio,
                    ps_ratio = EXCLUDED.ps_ratio,
                    ev_ebitda = EXCLUDED.ev_ebitda,
                    roe = EXCLUDED.roe,
                    roa = EXCLUDED.roa,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    current_ratio = EXCLUDED.current_ratio,
                    gross_margin = EXCLUDED.gross_margin,
                    operating_margin = EXCLUDED.operating_margin,
                    net_margin = EXCLUDED.net_margin,
                    graham_number = EXCLUDED.graham_number,
                    enterprise_value = EXCLUDED.enterprise_value,
                    last_updated = CURRENT_TIMESTAMP
            """, (
                ticker, self.today, price_used, data_quality_score, notes,
                ratios.get('pe_ratio'), ratios.get('pb_ratio'), ratios.get('ps_ratio'),
                ratios.get('ev_ebitda'), ratios.get('roe'), ratios.get('roa'),
                ratios.get('debt_to_equity'), ratios.get('current_ratio'),
                ratios.get('gross_margin'), ratios.get('operating_margin'),
                ratios.get('net_margin'), ratios.get('graham_number'),
                ratios.get('enterprise_value')
            ))
            
            return True
            
        except Exception as e:
            logging.error(f"Error storing ratios for {ticker}: {e}")
            return False
    
    def log_update(self, ticker: str, status: str, execution_time_ms: int, error_message: str = None):
        """Log update to update_log table"""
        try:
            self.cur.execute("""
                INSERT INTO update_log (
                    ticker, update_type, status, execution_time_ms, error_message, started_at, completed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                ticker, 'ratios', status, execution_time_ms, error_message,
                datetime.now(), datetime.now()
            ))
        except Exception as e:
            logging.error(f"Error logging update for {ticker}: {e}")
    
    def run_daily_calculation(self):
        """Run daily ratio calculation for all tickers"""
        start_time = datetime.now()
        logging.info("🚀 Starting daily ratio calculation...")
        
        tickers = self.get_tickers_with_fundamentals()
        logging.info(f"📊 Found {len(tickers)} tickers with fundamental data")
        
        successful = 0
        failed = 0
        
        for ticker in tickers:
            ticker_start_time = datetime.now()
            
            try:
                # Get latest price
                current_price = self.get_latest_price(ticker)
                if not current_price:
                    logging.warning(f"⚠️  No price data for {ticker}, skipping")
                    self.log_update(ticker, 'failed', 0, 'No price data')
                    failed += 1
                    continue
                
                # Get fundamental data
                fundamental_data = self.get_fundamental_data(ticker)
                if not fundamental_data:
                    logging.warning(f"⚠️  No fundamental data for {ticker}, skipping")
                    self.log_update(ticker, 'failed', 0, 'No fundamental data')
                    failed += 1
                    continue
                
                # Calculate ratios
                calculation_result = self.calculate_ratios(ticker, fundamental_data, current_price)
                
                # Store ratios
                if self.store_ratios(ticker, calculation_result):
                    ticker_execution_time = int((datetime.now() - ticker_start_time).total_seconds() * 1000)
                    self.log_update(ticker, 'success', ticker_execution_time)
                    
                    # Log successful calculation
                    ratios = calculation_result['ratios']
                    quality_score = calculation_result['data_quality_score']
                    logging.info(f"✅ {ticker}: P/E={ratios.get('pe_ratio', 'N/A'):.2f}, "
                               f"P/B={ratios.get('pb_ratio', 'N/A'):.2f}, "
                               f"P/S={ratios.get('ps_ratio', 'N/A'):.2f}, "
                               f"Quality={quality_score}%")
                    
                    successful += 1
                else:
                    self.log_update(ticker, 'failed', 0, 'Database storage failed')
                    failed += 1
                    
            except Exception as e:
                logging.error(f"❌ Error processing {ticker}: {e}")
                self.log_update(ticker, 'failed', 0, str(e))
                failed += 1
        
        total_execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        logging.info(f"🎉 Daily ratio calculation completed!")
        logging.info(f"   ✅ Successful: {successful}")
        logging.info(f"   ❌ Failed: {failed}")
        logging.info(f"   ⏱️  Total execution time: {total_execution_time}ms")
        
        # Log overall update
        self.cur.execute("""
            INSERT INTO update_log (
                ticker, update_type, status, records_updated, execution_time_ms, started_at, completed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            None, 'daily_ratios', 'success', successful, total_execution_time,
            start_time, datetime.now()
        ))
        
        self.conn.commit()
    
    def close(self):
        """Close database connections"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def main():
    """Main function"""
    calculator = DailyRatioCalculator()
    try:
        calculator.run_daily_calculation()
    finally:
        calculator.close()

if __name__ == "__main__":
    main() 