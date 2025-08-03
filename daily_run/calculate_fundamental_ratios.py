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


# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
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
        self.calculator = EnhancedRatioCalculatorV5()
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
                dc.close as current_price,
                s.fundamentals_last_update,
                s.next_earnings_date,
                s.data_priority,
                fr.calculation_date as last_ratio_calculation
            FROM stocks s
            INNER JOIN (
                SELECT ticker, close, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
                FROM daily_charts
            ) dc ON s.ticker = dc.ticker AND dc.rn = 1
            LEFT JOIN (
                SELECT ticker, MAX(calculation_date) as calculation_date
                FROM financial_ratios
                GROUP BY ticker
            ) fr ON s.ticker = fr.ticker
            WHERE dc.close > 0
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
            
            companies = self.db.fetch_all_dict(query)
                
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
                s.shares_outstanding,
                (SELECT close FROM daily_charts WHERE ticker = cf.ticker ORDER BY date DESC LIMIT 1) as current_price
            FROM company_fundamentals cf
            JOIN stocks s ON cf.ticker = s.ticker
                    WHERE cf.ticker = %s
        AND cf.period_type = 'ttm'
            ORDER BY cf.report_date DESC
            LIMIT 1
            """
            
            results = self.db.fetch_all_dict(query, (ticker,))
            result = results[0] if results else None
            
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
                net_income as net_income_previous,
                free_cash_flow as free_cash_flow_previous,
                cost_of_goods_sold as cost_of_goods_sold_previous,
                current_assets as current_assets_previous,
                current_liabilities as current_liabilities_previous
            FROM company_fundamentals
            WHERE ticker = %s
            AND period_type = 'ttm'
            ORDER BY report_date DESC
            LIMIT 1 OFFSET 1
            """
            
            result = self.db.fetch_one(query, (ticker,))
            
            if result:
                return {
                    'revenue_previous': result[0],
                    'total_assets_previous': result[1],
                    'net_income_previous': result[2],
                    'free_cash_flow_previous': result[3],
                    'cost_of_goods_sold_previous': result[4],
                    'current_assets_previous': result[5],
                    'current_liabilities_previous': result[6]
                }
            
            return None
            
        except Exception as e:
            self.error_handler.handle_exception(e, {'ticker': ticker, 'operation': 'get_historical_fundamental_data'})
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
            # Update ratios in company_fundamentals table
            update_query = """
            UPDATE company_fundamentals 
            SET 
                price_to_earnings = %s,
                price_to_book = %s,
                price_to_sales = %s,
                ev_to_ebitda = %s,
                peg_ratio = %s,
                return_on_equity = %s,
                return_on_assets = %s,
                return_on_invested_capital = %s,
                gross_margin = %s,
                operating_margin = %s,
                net_margin = %s,
                debt_to_equity_ratio = %s,
                current_ratio = %s,
                quick_ratio = %s,
                interest_coverage = %s,
                altman_z_score = %s,
                asset_turnover = %s,
                inventory_turnover = %s,
                receivables_turnover = %s,
                revenue_growth_yoy = %s,
                earnings_growth_yoy = %s,
                fcf_growth_yoy = %s,
                fcf_to_net_income = %s,
                cash_conversion_cycle = %s,
                graham_number = %s,
                last_updated = CURRENT_DATE
            WHERE ticker = %s AND period_type = 'ttm'
            """
            
            values = (
                ratios.get('price_to_earnings'), ratios.get('price_to_book'), ratios.get('price_to_sales'),
                ratios.get('ev_to_ebitda'), ratios.get('peg_ratio'),
                ratios.get('return_on_equity'), ratios.get('return_on_assets'), ratios.get('return_on_invested_capital'),
                ratios.get('gross_margin'), ratios.get('operating_margin'), ratios.get('net_margin'),
                ratios.get('debt_to_equity_ratio'), ratios.get('current_ratio'), ratios.get('quick_ratio'),
                ratios.get('interest_coverage'), ratios.get('altman_z_score'),
                ratios.get('asset_turnover'), ratios.get('inventory_turnover'), ratios.get('receivables_turnover'),
                ratios.get('revenue_growth_yoy'), ratios.get('earnings_growth_yoy'), ratios.get('fcf_growth_yoy'),
                ratios.get('fcf_to_net_income'), ratios.get('cash_conversion_cycle'),
                ratios.get('graham_number'),
                ticker
            )
            
            self.db.execute_update(update_query, values)
            logger.info(f"Successfully stored {len(ratios)} ratios for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing ratios for {ticker}: {e}")
            return False
    
    def process_all_companies(self) -> Dict:
        """
        Process ratio calculations for all companies needing updates
        
        Returns:
            Dictionary with processing results
        """
        logger.info("📊 FUNDAMENTAL RATIO CALCULATIONS STARTED")
        logger.info("🔍 STEP 1: Getting companies needing ratio updates...")
        
        # Get companies needing updates
        companies = self.get_companies_needing_ratio_updates()
        logger.info(f"✅ Found {len(companies)} companies needing ratio updates")
        
        if not companies:
            logger.info("ℹ️ No companies need ratio updates")
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
        logger.info(f"📈 STEP 2: Processing {len(companies)} companies...")
        for i, company in enumerate(companies, 1):
            logger.info(f"📊 Processing company {i}/{len(companies)}: {company.get('ticker', 'Unknown')}")
            result = self.calculate_ratios_for_company(company)
            
            if result['status'] == 'success':
                results['successful'] += 1
                logger.info(f"✅ Successfully calculated ratios for {company.get('ticker', 'Unknown')}")
            else:
                results['failed'] += 1
                results['errors'].append({
                    'ticker': result['ticker'],
                    'error': result.get('error', 'Unknown error')
                })
                logger.warning(f"❌ Failed to calculate ratios for {company.get('ticker', 'Unknown')}: {result.get('error', 'Unknown error')}")
        
        logger.info(f"✅ STEP 3: Completed processing all companies")
        
        # Log summary with enhanced details
        logger.info(f"📊 FUNDAMENTAL RATIO CALCULATION SUMMARY:")
        logger.info(f"   • Total Companies Processed: {results['total_processed']}")
        logger.info(f"   • Successful Calculations: {results['successful']}")
        logger.info(f"   • Failed Calculations: {results['failed']}")
        logger.info(f"   • Success Rate: {(results['successful']/results['total_processed']*100):.1f}%" if results['total_processed'] > 0 else "N/A")
        
        if results['errors']:
            logger.info(f"   ❌ Companies with Errors ({len(results['errors'])}):")
            for error in results['errors'][:10]:  # Show first 10 errors
                logger.info(f"     • {error['ticker']}: {error['error']}")
            if len(results['errors']) > 10:
                logger.info(f"     ... and {len(results['errors']) - 10} more errors")
        
        # Update monitoring
        self.monitoring.record_metric(
            'fundamental_ratios_calculated',
            results['successful']
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