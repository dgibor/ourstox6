"""
Enhanced Daily Fundamental Ratio Calculator

This script runs as part of the daily workflow to calculate fundamental ratios
for companies that have updated fundamental data after earnings reports.
Enhanced with better error handling, transaction safety, and batch processing.
"""

import logging
import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import modules using absolute paths
try:
    from improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
    from data_validator import FundamentalDataValidator
    from database import DatabaseManager
    from error_handler import ErrorHandler, ErrorSeverity
    from monitoring import SystemMonitor
except ImportError as e:
    # Fallback to relative imports if absolute imports fail
    from .improved_ratio_calculator_v5_enhanced import EnhancedRatioCalculatorV5
    from .data_validator import FundamentalDataValidator
    from .database import DatabaseManager
    from .error_handler import ErrorHandler, ErrorSeverity
    from .monitoring import SystemMonitor

logger = logging.getLogger(__name__)

class EnhancedDailyFundamentalRatioCalculator:
    """
    Enhanced calculator with improved error handling, transaction safety, and batch processing
    """
    
    def __init__(self, db_connection, batch_size: int = 50, max_retries: int = 3):
        self.db = db_connection
        self.calculator = EnhancedRatioCalculatorV5()
        self.validator = FundamentalDataValidator()
        self.error_handler = ErrorHandler("enhanced_daily_fundamental_ratio_calculator")
        self.monitoring = SystemMonitor()
        self.batch_size = batch_size
        self.max_retries = max_retries
        
    def get_companies_needing_ratio_updates(self) -> List[Dict]:
        """
        Get companies that need ratio calculations with enhanced error handling
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
            LIMIT %s
            """
            
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (self.batch_size,))
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
        Get the latest fundamental data for a ticker with validation
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
                # Convert to regular dict and validate
                fundamental_data = dict(result)
                validated_data = self.validator.validate_fundamental_data(fundamental_data)
                
                if validated_data:
                    return validated_data
                else:
                    logger.warning(f"Invalid fundamental data for {ticker}")
                    return None
            else:
                logger.warning(f"No fundamental data found for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting fundamental data for {ticker}: {e}")
            return None
    
    def get_historical_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """
        Get historical fundamental data for growth calculations with validation
        """
        try:
            query = """
            SELECT 
                revenue as revenue_previous,
                total_assets as total_assets_previous,
                inventory as inventory_previous,
                accounts_receivable as accounts_receivable_previous,
                retained_earnings as retained_earnings_previous,
                net_income as net_income_previous,
                free_cash_flow as free_cash_flow_previous
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
                validated_data = self.validator.validate_historical_data(historical_data)
                return validated_data
            else:
                logger.warning(f"No historical fundamental data found for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data for {ticker}: {e}")
            return None
    
    def store_ratios_safe(self, ticker: str, ratios: Dict[str, float]) -> bool:
        """
        Store calculated ratios with transaction safety and retry logic
        """
        for attempt in range(self.max_retries):
            try:
                # Start transaction
                self.db.begin_transaction()
                
                # Check if we already have ratios for today
                check_query = """
                SELECT COUNT(*) FROM financial_ratios 
                WHERE ticker = %s AND calculation_date = CURRENT_DATE
                """
                
                with self.db.cursor() as cursor:
                    cursor.execute(check_query, (ticker,))
                    existing_count = cursor.fetchone()[0]
                
                if existing_count > 0:
                    # Update existing record
                    update_query = """
                    UPDATE financial_ratios SET
                        pe_ratio = %s, pb_ratio = %s, ps_ratio = %s, ev_ebitda = %s, peg_ratio = %s,
                        roe = %s, roa = %s, roic = %s, gross_margin = %s, operating_margin = %s, net_margin = %s,
                        debt_to_equity = %s, current_ratio = %s, quick_ratio = %s, interest_coverage = %s, altman_z_score = %s,
                        asset_turnover = %s, inventory_turnover = %s, receivables_turnover = %s,
                        revenue_growth_yoy = %s, earnings_growth_yoy = %s, fcf_growth_yoy = %s,
                        fcf_to_net_income = %s, cash_conversion_cycle = %s,
                        market_cap = %s, enterprise_value = %s, graham_number = %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE ticker = %s AND calculation_date = CURRENT_DATE
                    """
                else:
                    # Insert new record
                    update_query = """
                    INSERT INTO financial_ratios (
                        ticker, calculation_date,
                        pe_ratio, pb_ratio, ps_ratio, ev_ebitda, peg_ratio,
                        roe, roa, roic, gross_margin, operating_margin, net_margin,
                        debt_to_equity, current_ratio, quick_ratio, interest_coverage, altman_z_score,
                        asset_turnover, inventory_turnover, receivables_turnover,
                        revenue_growth_yoy, earnings_growth_yoy, fcf_growth_yoy,
                        fcf_to_net_income, cash_conversion_cycle,
                        market_cap, enterprise_value, graham_number,
                        last_updated
                    ) VALUES (
                        %s, CURRENT_DATE,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        CURRENT_TIMESTAMP
                    )
                    """
                
                # Prepare values
                values = (
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
                
                if existing_count > 0:
                    values = values + (ticker,)
                else:
                    values = (ticker,) + values
                
                # Execute query
                with self.db.cursor() as cursor:
                    cursor.execute(update_query, values)
                
                # Commit transaction
                self.db.commit()
                logger.info(f"Successfully stored {len(ratios)} ratios for {ticker}")
                return True
                
            except Exception as e:
                # Rollback transaction
                self.db.rollback()
                logger.error(f"Attempt {attempt + 1} failed for {ticker}: {e}")
                
                if attempt < self.max_retries - 1:
                    # Wait before retry
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {ticker}")
                    return False
        
        return False
    
    def calculate_ratios_for_company(self, company_data: Dict) -> Dict:
        """
        Calculate all fundamental ratios for a single company with enhanced error handling
        """
        # Validate company data
        validated_company = self.validator.validate_company_data(company_data)
        if not validated_company:
            return {
                'ticker': company_data.get('ticker', 'UNKNOWN'),
                'status': 'failed',
                'error': 'Invalid company data',
                'ratios_calculated': 0
            }
        
        ticker = validated_company['ticker']
        current_price = validated_company['current_price']
        
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
            
            # Store ratios in database with transaction safety
            storage_success = self.store_ratios_safe(ticker, ratios)
            
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
                    'error': 'Failed to store ratios after retries',
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
    
    def process_all_companies(self) -> Dict:
        """
        Process ratio calculations for all companies with batch processing and enhanced monitoring
        """
        logger.info("Starting enhanced daily fundamental ratio calculations")
        
        # Get companies needing updates
        companies = self.get_companies_needing_ratio_updates()
        
        if not companies:
            logger.info("No companies need ratio updates")
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'errors': [],
                'processing_time': 0
            }
        
        start_time = time.time()
        results = {
            'total_processed': len(companies),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processing_time': 0
        }
        
        # Process companies in batches
        for i in range(0, len(companies), self.batch_size):
            batch = companies[i:i + self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(companies) + self.batch_size - 1)//self.batch_size}")
            
            for company in batch:
                result = self.calculate_ratios_for_company(company)
                
                if result['status'] == 'success':
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'ticker': result['ticker'],
                        'error': result.get('error', 'Unknown error'),
                        'status': result['status']
                    })
        
        # Calculate processing time
        results['processing_time'] = time.time() - start_time
        
        # Log summary
        logger.info(f"Enhanced ratio calculation summary: {results['successful']} successful, {results['failed']} failed in {results['processing_time']:.2f}s")
        
        # Update monitoring
        self.monitoring.record_metric(
            'enhanced_fundamental_ratios_calculated',
            results['successful'],
            {
                'total_processed': results['total_processed'],
                'processing_time': results['processing_time'],
                'success_rate': results['successful'] / results['total_processed'] if results['total_processed'] > 0 else 0
            }
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
        
        # Create enhanced calculator
        calculator = EnhancedDailyFundamentalRatioCalculator(db, batch_size=50, max_retries=3)
        
        # Process all companies
        results = calculator.process_all_companies()
        
        # Log final results
        logger.info(f"Enhanced daily fundamental ratio calculation completed")
        logger.info(f"Results: {results}")
        
        # Exit with appropriate code
        if results['failed'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in enhanced daily fundamental ratio calculation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 