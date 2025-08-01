"""
Daily Fundamental Ratio Calculator

This script runs as part of the daily workflow to calculate fundamental ratios
for companies that have updated fundamental data after earnings reports.
"""

import logging
import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from improved_ratio_calculator_v5 import ImprovedRatioCalculatorV5
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor

logger = logging.getLogger(__name__)

class DailyFundamentalRatioCalculator:
    """
    Calculates fundamental ratios for companies with updated fundamental data
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.calculator = ImprovedRatioCalculatorV5()
        self.error_handler = ErrorHandler("daily_fundamental_ratio_calculator")
        self.monitoring = SystemMonitor()
        
    def get_companies_needing_ratio_updates(self) -> List[Dict]:
        """
        Get companies that need ratio calculations based on:
        1. Have updated fundamental data after earnings
        2. Missing or outdated ratio calculations
        3. Recent earnings reports
        
        Returns:
            List of company data dictionaries
        """
        try:
            query = """
            SELECT DISTINCT 
                s.ticker,
                s.company_name,
                s.current_price,
                s.fundamentals_last_update,
                s.next_earnings_date,
                s.data_priority,
                fr.calculation_date as last_ratio_calculation
            FROM stocks s
            LEFT JOIN (
                SELECT ticker, MAX(calculation_date) as calculation_date
                FROM financial_ratios
                GROUP BY ticker
            ) fr ON s.ticker = fr.ticker
            WHERE s.current_price > 0
            AND s.fundamentals_last_update IS NOT NULL
            AND (
                -- Companies with no ratio calculations
                fr.calculation_date IS NULL
                OR 
                -- Companies with outdated ratio calculations (more than 1 day old)
                fr.calculation_date < CURRENT_DATE - INTERVAL '1 day'
                OR
                -- Companies with recent fundamental updates (within last 7 days)
                s.fundamentals_last_update >= CURRENT_DATE - INTERVAL '7 days'
                OR
                -- Companies with recent earnings (within last 30 days)
                s.next_earnings_date >= CURRENT_DATE - INTERVAL '30 days'
            )
            ORDER BY s.data_priority DESC, s.fundamentals_last_update DESC NULLS LAST
            LIMIT 100
            """
            
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                companies = cursor.fetchall()
                
            logger.info(f"Found {len(companies)} companies needing ratio updates")
            return companies
            
        except Exception as e:
            logger.error(f"Error getting companies needing ratio updates: {e}")
            self.error_handler.handle_error(
                "Failed to get companies needing ratio updates", e, ErrorSeverity.HIGH
            )
            return []
    
    def get_latest_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """
        Get the latest fundamental data for a ticker
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Dictionary with fundamental data or None if not found
        """
        try:
            query = """
            SELECT 
                cf.*,
                s.current_price,
                s.shares_outstanding
            FROM company_fundamentals cf
            JOIN stocks s ON cf.ticker = s.ticker
            WHERE cf.ticker = %s
            AND cf.period_type = 'annual'
            ORDER BY cf.report_date DESC
            LIMIT 1
            """
            
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (ticker,))
                result = cursor.fetchone()
                
            if result:
                # Convert to regular dict and handle numeric types
                fundamental_data = dict(result)
                for key, value in fundamental_data.items():
                    if isinstance(value, (int, float)) and value is not None:
                        fundamental_data[key] = float(value)
                return fundamental_data
            else:
                logger.warning(f"No fundamental data found for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting fundamental data for {ticker}: {e}")
            return None
    
    def get_historical_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """
        Get historical fundamental data for growth calculations
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Dictionary with historical data or None if not found
        """
        try:
            query = """
            SELECT 
                revenue as revenue_previous,
                total_assets as total_assets_previous,
                inventory as inventory_previous,
                accounts_receivable as accounts_receivable_previous,
                retained_earnings as retained_earnings_previous
            FROM company_fundamentals
            WHERE ticker = %s
            AND period_type = 'annual'
            ORDER BY report_date DESC
            LIMIT 1 OFFSET 1
            """
            
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (ticker,))
                result = cursor.fetchone()
                
            if result:
                historical_data = dict(result)
                for key, value in historical_data.items():
                    if isinstance(value, (int, float)) and value is not None:
                        historical_data[key] = float(value)
                return historical_data
            else:
                logger.warning(f"No historical fundamental data found for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data for {ticker}: {e}")
            return None
    
    def calculate_ratios_for_company(self, company_data: Dict) -> Dict:
        """
        Calculate all fundamental ratios for a single company
        
        Args:
            company_data: Dictionary with company information
            
        Returns:
            Dictionary with calculation results
        """
        ticker = company_data['ticker']
        current_price = float(company_data['current_price'])
        
        try:
            logger.info(f"Calculating ratios for {ticker}")
            
            # Get fundamental data
            fundamental_data = self.get_latest_fundamental_data(ticker)
            if not fundamental_data:
                return {
                    'ticker': ticker,
                    'status': 'failed',
                    'error': 'No fundamental data available',
                    'ratios_calculated': 0
                }
            
            # Get historical data for growth calculations
            historical_data = self.get_historical_fundamental_data(ticker)
            
            # Calculate all ratios
            ratios = self.calculator.calculate_all_ratios(
                ticker, fundamental_data, current_price, historical_data
            )
            
            if not ratios:
                return {
                    'ticker': ticker,
                    'status': 'failed',
                    'error': 'No ratios calculated',
                    'ratios_calculated': 0
                }
            
            # Store ratios in database
            storage_success = self.store_ratios(ticker, ratios)
            
            if storage_success:
                logger.info(f"Successfully calculated and stored {len(ratios)} ratios for {ticker}")
                return {
                    'ticker': ticker,
                    'status': 'success',
                    'ratios_calculated': len(ratios),
                    'ratios': ratios
                }
            else:
                return {
                    'ticker': ticker,
                    'status': 'storage_failed',
                    'error': 'Failed to store ratios',
                    'ratios_calculated': len(ratios)
                }
                
        except Exception as e:
            logger.error(f"Error calculating ratios for {ticker}: {e}")
            self.error_handler.handle_error(
                f"Failed to calculate ratios for {ticker}", e, ErrorSeverity.MEDIUM
            )
            return {
                'ticker': ticker,
                'status': 'error',
                'error': str(e),
                'ratios_calculated': 0
            }
    
    def store_ratios(self, ticker: str, ratios: Dict[str, float]) -> bool:
        """
        Store calculated ratios in the database
        
        Args:
            ticker: Stock symbol
            ratios: Dictionary of calculated ratios
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, delete any existing ratios for today
            delete_query = """
            DELETE FROM financial_ratios 
            WHERE ticker = %s AND calculation_date = CURRENT_DATE
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(delete_query, (ticker,))
            
            # Insert new ratios
            insert_query = """
            INSERT INTO financial_ratios (
                ticker, calculation_date,
                pe_ratio, pb_ratio, ps_ratio, ev_ebitda, peg_ratio,
                roe, roa, roic, gross_margin, operating_margin, net_margin,
                debt_to_equity, current_ratio, quick_ratio, interest_coverage, altman_z_score,
                asset_turnover, inventory_turnover, receivables_turnover,
                revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
                fcf_to_net_income, cash_conversion_cycle,
                market_cap, enterprise_value, graham_number
            ) VALUES (
                %s, CURRENT_DATE,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s
            )
            """
            
            values = (
                ticker,
                ratios.get('pe_ratio'), ratios.get('pb_ratio'), ratios.get('ps_ratio'),
                ratios.get('ev_ebitda'), ratios.get('peg_ratio'),
                ratios.get('roe'), ratios.get('roa'), ratios.get('roic'),
                ratios.get('gross_margin'), ratios.get('operating_margin'), ratios.get('net_margin'),
                ratios.get('debt_to_equity'), ratios.get('current_ratio'), ratios.get('quick_ratio'),
                ratios.get('interest_coverage'), ratios.get('altman_z_score'),
                ratios.get('asset_turnover'), ratios.get('inventory_turnover'), ratios.get('receivables_turnover'),
                ratios.get('revenue_growth_yoy'), ratios.get('earnings_growth_yoy'), ratios.get('fcf_growth_yoy'),
                ratios.get('fcf_to_net_income'), ratios.get('cash_conversion_cycle'),
                ratios.get('market_cap'), ratios.get('enterprise_value'), ratios.get('graham_number')
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(insert_query, values)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing ratios for {ticker}: {e}")
            self.db.rollback()
            return False
    
    def process_all_companies(self) -> Dict:
        """
        Process ratio calculations for all companies needing updates
        
        Returns:
            Dictionary with processing results
        """
        logger.info("Starting daily fundamental ratio calculations")
        
        # Get companies needing updates
        companies = self.get_companies_needing_ratio_updates()
        
        if not companies:
            logger.info("No companies need ratio updates")
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'errors': []
            }
        
        results = {
            'total_processed': len(companies),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Process each company
        for company in companies:
            result = self.calculate_ratios_for_company(company)
            
            if result['status'] == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'ticker': result['ticker'],
                    'error': result.get('error', 'Unknown error')
                })
        
        # Log summary
        logger.info(f"Ratio calculation summary: {results['successful']} successful, {results['failed']} failed")
        
        # Update monitoring
        self.monitoring.record_metric(
            'fundamental_ratios_calculated',
            results['successful'],
            {'total_processed': results['total_processed']}
        )
        
        return results

def main():
    """Main function for standalone execution"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize database connection
        db = DatabaseManager()
        
        # Create calculator
        calculator = DailyFundamentalRatioCalculator(db)
        
        # Process all companies
        results = calculator.process_all_companies()
        
        # Log final results
        logger.info(f"Daily fundamental ratio calculation completed")
        logger.info(f"Results: {results}")
        
        # Exit with appropriate code
        if results['failed'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in daily fundamental ratio calculation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 