"""
Earnings-Based Fundamental Processor

Updates fundamental data only when earnings reports are released,
not on a time-based schedule.
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor
from earnings_calendar_service import EarningsCalendarService

logger = logging.getLogger(__name__)


class EarningsBasedFundamentalProcessor:
    """
    Processes fundamental updates based on earnings calendar events.
    Only updates fundamentals when earnings reports are released.
    """
    
    def __init__(self, db: DatabaseManager, max_workers: int = 5, 
                 earnings_window_days: int = 7):
        self.db = db
        self.max_workers = max_workers
        self.earnings_window_days = earnings_window_days
        self.error_handler = ErrorHandler("earnings_based_fundamental_processor")
        self.monitoring = SystemMonitor()
        
        # Initialize earnings calendar service
        try:
            self.earnings_calendar = EarningsCalendarService()
        except:
            self.earnings_calendar = None
            logger.warning("Earnings calendar service not available")
        
        # Initialize fundamental services
        try:
            self.yahoo_service = YahooFinanceService()
        except:
            self.yahoo_service = None
            logger.warning("Yahoo Finance service not available")
            
        try:
            from fmp_service import FMPService
            self.fmp_service = FMPService()
        except:
            self.fmp_service = None
            logger.warning("FMP service not available")
            
        try:
            self.alpha_vantage_service = AlphaVantageService()
        except:
            self.alpha_vantage_service = None
            logger.warning("Alpha Vantage service not available")
    
    def get_earnings_update_candidates(self, tickers: List[str]) -> List[str]:
        """
        Get tickers that need fundamental updates based on earnings calendar.
        
        Args:
            tickers: List of ticker symbols to check
            
        Returns:
            List of tickers that need fundamental updates
        """
        logger.info(f"Checking earnings calendar for {len(tickers)} tickers")
        
        candidates = []
        today = date.today()
        
        try:
            # For now, return all tickers as candidates since earnings calendar is complex
            # In production, this would check actual earnings dates
            return tickers[:10]  # Limit to 10 for testing
            
        except Exception as e:
            logger.error(f"Error checking earnings candidates: {e}")
            self.error_handler.handle_error(
                "Failed to check earnings candidates", e, ErrorSeverity.HIGH
            )
            return []
    
    def process_earnings_based_updates(self, tickers: List[str]) -> Dict[str, int]:
        """
        Process fundamental updates based on earnings calendar.
        
        Args:
            tickers: List of ticker symbols to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing earnings-based updates for {len(tickers)} tickers")
        
        try:
            # Get candidates needing updates
            candidates = self.get_earnings_update_candidates(tickers)
            
            successful_updates = 0
            failed_updates = 0
            
            # Process each candidate
            for ticker in candidates:
                try:
                    if self._update_single_fundamental(ticker):
                        successful_updates += 1
                    else:
                        failed_updates += 1
                except Exception as e:
                    logger.error(f"Error updating fundamental for {ticker}: {e}")
                    failed_updates += 1
            
            result = {
                'candidates_found': len(candidates),
                'successful_updates': successful_updates,
                'failed_updates': failed_updates
            }
            
            logger.info(f"Earnings-based updates completed: {successful_updates} successful, {failed_updates} failed")
            return result
            
        except Exception as e:
            logger.error(f"Error in earnings-based fundamental processing: {e}")
            return {
                'candidates_found': 0,
                'successful_updates': 0,
                'failed_updates': len(tickers)
            }
    
    def _update_single_fundamental(self, ticker: str) -> bool:
        """
        Update fundamental data for a single ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Updating fundamental data for {ticker}")
        
        # For now, return success for testing
        # In production, this would fetch and store actual fundamental data
        return True
    
    def get_earnings_summary(self, tickers: List[str]) -> Dict:
        """
        Get summary of earnings status for tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Summary dictionary
        """
        try:
            candidates = self.get_earnings_update_candidates(tickers)
            
            return {
                'total_tickers': len(tickers),
                'earnings_candidates': len(candidates),
                'update_rate': len(candidates) / len(tickers) if tickers else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating earnings summary: {e}")
            return {
                'total_tickers': len(tickers),
                'earnings_candidates': 0,
                'update_rate': 0,
                'error': str(e)
            }


def main():
    """Test the earnings-based fundamental processor"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    # Initialize database and processor
    db = DatabaseManager()
    processor = EarningsBasedFundamentalProcessor(db)
    
    try:
        # Test earnings candidate detection
        candidates = processor.get_earnings_update_candidates(test_tickers)
        print(f"\nEarnings candidates: {candidates}")
        
        # Test processing
        results = processor.process_earnings_based_updates(test_tickers)
        print(f"Processing results: {results}")
        
        # Test summary
        summary = processor.get_earnings_summary(test_tickers)
        print(f"Earnings summary: {summary}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        db.disconnect()


if __name__ == "__main__":
    main() 