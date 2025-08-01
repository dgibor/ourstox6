"""
Integration script for fundamental ratio calculator
Shows how to integrate into existing daily workflow
"""

import logging
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from fundamental_ratio_calculator import FundamentalRatioCalculator
from database import Database

logger = logging.getLogger(__name__)

class FundamentalRatioIntegrator:
    """
    Integrates fundamental ratio calculations into daily workflow
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.calculator = FundamentalRatioCalculator(db_connection)
        
    def process_ticker_ratios(self, ticker: str, current_price: float) -> Dict:
        """
        Process fundamental ratios for a single ticker
        
        Args:
            ticker: Stock symbol
            current_price: Current stock price
            
        Returns:
            Dictionary with results and status
        """
        try:
            logger.info(f"Processing fundamental ratios for {ticker}")
            
            # Calculate all ratios
            ratios = self.calculator.calculate_all_ratios(ticker, current_price)
            
            if not ratios:
                logger.warning(f"No ratios calculated for {ticker}")
                return {
                    'ticker': ticker,
                    'status': 'failed',
                    'ratios_calculated': 0,
                    'error': 'No ratios calculated'
                }
            
            # Store ratios in database
            storage_success = self.calculator.store_ratios(ticker, ratios)
            
            if storage_success:
                logger.info(f"Successfully processed {len(ratios)} ratios for {ticker}")
                return {
                    'ticker': ticker,
                    'status': 'success',
                    'ratios_calculated': len(ratios),
                    'ratios': ratios
                }
            else:
                logger.error(f"Failed to store ratios for {ticker}")
                return {
                    'ticker': ticker,
                    'status': 'storage_failed',
                    'ratios_calculated': len(ratios),
                    'error': 'Database storage failed'
                }
                
        except Exception as e:
            logger.error(f"Error processing ratios for {ticker}: {e}")
            return {
                'ticker': ticker,
                'status': 'error',
                'ratios_calculated': 0,
                'error': str(e)
            }
    
    def process_batch_ratios(self, tickers: List[str], current_prices: Dict[str, float]) -> Dict:
        """
        Process fundamental ratios for multiple tickers
        
        Args:
            tickers: List of stock symbols
            current_prices: Dictionary of current prices by ticker
            
        Returns:
            Dictionary with batch results
        """
        logger.info(f"Processing fundamental ratios for {len(tickers)} tickers")
        
        results = {
            'total_tickers': len(tickers),
            'successful': 0,
            'failed': 0,
            'total_ratios': 0,
            'ticker_results': {}
        }
        
        for ticker in tickers:
            current_price = current_prices.get(ticker, 0)
            if current_price <= 0:
                logger.warning(f"No valid price for {ticker}, skipping")
                results['ticker_results'][ticker] = {
                    'status': 'skipped',
                    'error': 'No valid price'
                }
                results['failed'] += 1
                continue
            
            # Process single ticker
            ticker_result = self.process_ticker_ratios(ticker, current_price)
            results['ticker_results'][ticker] = ticker_result
            
            if ticker_result['status'] == 'success':
                results['successful'] += 1
                results['total_ratios'] += ticker_result['ratios_calculated']
            else:
                results['failed'] += 1
        
        logger.info(f"Batch processing complete: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def get_tickers_needing_ratios(self) -> List[str]:
        """
        Get list of tickers that need ratio calculations
        """
        try:
            query = """
            SELECT DISTINCT s.ticker
            FROM stocks s
            LEFT JOIN financial_ratios fr ON s.ticker = fr.ticker 
                AND fr.calculation_date = CURRENT_DATE
            WHERE s.active = true 
                AND fr.ticker IS NULL
            ORDER BY s.ticker
            """
            
            result = self.db.execute_query(query)
            return [row[0] for row in result] if result else []
            
        except Exception as e:
            logger.error(f"Error getting tickers needing ratios: {e}")
            return []
    
    def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """
        Get current prices for tickers
        """
        try:
            if not tickers:
                return {}
            
            # Build query for multiple tickers
            placeholders = ','.join(['%s'] * len(tickers))
            query = f"""
            SELECT ticker, close
            FROM daily_charts
            WHERE ticker IN ({placeholders})
                AND date = (
                    SELECT MAX(date) 
                    FROM daily_charts dc2 
                    WHERE dc2.ticker = daily_charts.ticker
                )
            """
            
            result = self.db.execute_query(query, tickers)
            return {row[0]: float(row[1]) for row in result} if result else {}
            
        except Exception as e:
            logger.error(f"Error getting current prices: {e}")
            return {}

def integrate_with_daily_workflow():
    """
    Example integration with daily workflow
    """
    try:
        # Initialize database connection
        db = Database()
        
        # Initialize integrator
        integrator = FundamentalRatioIntegrator(db)
        
        # Get tickers needing ratio calculations
        tickers = integrator.get_tickers_needing_ratios()
        
        if not tickers:
            logger.info("No tickers need ratio calculations")
            return
        
        logger.info(f"Found {len(tickers)} tickers needing ratio calculations")
        
        # Get current prices
        current_prices = integrator.get_current_prices(tickers)
        
        if not current_prices:
            logger.warning("No current prices found, cannot calculate ratios")
            return
        
        logger.info(f"Found prices for {len(current_prices)} tickers")
        
        # Process ratios
        results = integrator.process_batch_ratios(list(current_prices.keys()), current_prices)
        
        # Log results
        logger.info(f"Ratio calculation complete:")
        logger.info(f"  Total tickers: {results['total_tickers']}")
        logger.info(f"  Successful: {results['successful']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info(f"  Total ratios calculated: {results['total_ratios']}")
        
        # Log failed tickers
        failed_tickers = [
            ticker for ticker, result in results['ticker_results'].items()
            if result['status'] != 'success'
        ]
        
        if failed_tickers:
            logger.warning(f"Failed tickers: {failed_tickers}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in daily workflow integration: {e}")
        return None

def add_to_daily_trading_system():
    """
    Example of how to add to existing daily_trading_system.py
    """
    integration_code = '''
# Add to daily_trading_system.py

def _calculate_fundamentals_and_technicals(self):
    """Calculate fundamentals and technical indicators"""
    
    # Existing technical calculations...
    technical_result = self._calculate_technical_indicators(tickers)
    
    # NEW: Add fundamental ratio calculations
    fundamental_result = self._calculate_fundamental_ratios(tickers)
    
    return {
        'technical': technical_result,
        'fundamental': fundamental_result
    }

def _calculate_fundamental_ratios(self, tickers: List[str]) -> Dict:
    """Calculate fundamental ratios for tickers"""
    try:
        # Get current prices
        current_prices = self._get_current_prices(tickers)
        
        # Initialize ratio calculator
        ratio_integrator = FundamentalRatioIntegrator(self.db)
        
        # Process ratios
        results = ratio_integrator.process_batch_ratios(tickers, current_prices)
        
        logger.info(f"Fundamental ratios calculated: {results['successful']} successful, {results['failed']} failed")
        
        return results
        
    except Exception as e:
        logger.error(f"Error calculating fundamental ratios: {e}")
        return {'status': 'error', 'error': str(e)}
    '''
    
    return integration_code

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run integration example
    print("🔧 FUNDAMENTAL RATIO INTEGRATION EXAMPLE")
    print("=" * 50)
    
    # Show integration code
    print("\n📝 Integration Code for daily_trading_system.py:")
    print("-" * 50)
    print(add_to_daily_trading_system())
    
    print("\n✅ Integration example completed!")
    print("The fundamental ratio calculator is ready to be integrated into your daily workflow.") 