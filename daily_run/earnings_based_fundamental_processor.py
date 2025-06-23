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
        self.earnings_calendar = EarningsCalendarService()
        
        # Initialize fundamental services
        self.yahoo_service = YahooFinanceService()
        self.fmp_service = FMPService()
        self.alpha_vantage_service = AlphaVantageService()
    
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
            # Check each ticker's earnings status
            for ticker in tickers:
                if self._should_update_fundamentals(ticker, today):
                    candidates.append(ticker)
            
            logger.info(f"Found {len(candidates)} tickers needing fundamental updates")
            return candidates
            
        except Exception as e:
            logger.error(f"Error checking earnings candidates: {e}")
            self.error_handler.handle_error(
                "Failed to check earnings candidates", e, ErrorSeverity.HIGH
            )
            return []
    
    def _should_update_fundamentals(self, ticker: str, check_date: date) -> bool:
        """
        Check if fundamentals should be updated for a ticker based on earnings.
        
        Args:
            ticker: Ticker symbol
            check_date: Date to check against
            
        Returns:
            True if fundamentals should be updated
        """
        try:
            # Get earnings information
            earnings_info = self._get_earnings_info(ticker)
            if not earnings_info:
                return False
            
            # Check if earnings were recently released
            last_earnings_date = earnings_info.get('last_earnings_date')
            if not last_earnings_date:
                return False
            
            # Check if earnings were within the window
            days_since_earnings = (check_date - last_earnings_date).days
            if 0 <= days_since_earnings <= self.earnings_window_days:
                logger.debug(f"{ticker}: Earnings {days_since_earnings} days ago - updating fundamentals")
                return True
            
            # Check if earnings are scheduled soon (pre-emptive update)
            next_earnings_date = earnings_info.get('next_earnings_date')
            if next_earnings_date:
                days_until_earnings = (next_earnings_date - check_date).days
                if 0 <= days_until_earnings <= 2:  # Update 2 days before earnings
                    logger.debug(f"{ticker}: Earnings in {days_until_earnings} days - pre-emptive update")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking earnings status for {ticker}: {e}")
            return False
    
    def _get_earnings_info(self, ticker: str) -> Optional[Dict]:
        """
        Get earnings information for a ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Earnings information dictionary
        """
        try:
            # First check database cache
            cached_info = self._get_cached_earnings_info(ticker)
            if cached_info and self._is_earnings_cache_fresh(cached_info):
                return cached_info
            
            # Fetch from API if needed
            api_info = self.earnings_calendar.get_earnings_info(ticker)
            if api_info:
                self._store_earnings_cache(ticker, api_info)
                return api_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting earnings info for {ticker}: {e}")
            return None
    
    def _get_cached_earnings_info(self, ticker: str) -> Optional[Dict]:
        """Get cached earnings information from database"""
        try:
            query = """
            SELECT last_earnings_date, next_earnings_date, last_updated
            FROM earnings_calendar 
            WHERE ticker = %s
            """
            return self.db.fetch_one(query, (ticker,))
            
        except Exception as e:
            logger.error(f"Error getting cached earnings info for {ticker}: {e}")
            return None
    
    def _is_earnings_cache_fresh(self, earnings_info: Dict) -> bool:
        """Check if cached earnings data is fresh (within 1 day)"""
        try:
            last_updated = earnings_info.get('last_updated')
            if not last_updated:
                return False
            
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            
            days_old = (datetime.now() - last_updated).days
            return days_old <= 1
            
        except Exception as e:
            logger.error(f"Error checking earnings cache freshness: {e}")
            return False
    
    def _store_earnings_cache(self, ticker: str, earnings_info: Dict):
        """Store earnings information in database cache"""
        try:
            query = """
            INSERT INTO earnings_calendar (
                ticker, last_earnings_date, next_earnings_date, last_updated
            ) VALUES (%s, %s, %s, NOW())
            ON CONFLICT (ticker) 
            DO UPDATE SET
                last_earnings_date = EXCLUDED.last_earnings_date,
                next_earnings_date = EXCLUDED.next_earnings_date,
                last_updated = NOW()
            """
            
            values = (
                ticker,
                earnings_info.get('last_earnings_date'),
                earnings_info.get('next_earnings_date')
            )
            
            self.db.execute(query, values)
            
        except Exception as e:
            logger.error(f"Error storing earnings cache for {ticker}: {e}")
    
    def process_earnings_based_updates(self, tickers: List[str]) -> Dict[str, int]:
        """
        Process fundamental updates for tickers with recent earnings.
        
        Args:
            tickers: List of ticker symbols to check
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.time()
        logger.info(f"Starting earnings-based fundamental updates for {len(tickers)} tickers")
        
        # Get candidates that need updates
        candidates = self.get_earnings_update_candidates(tickers)
        
        if not candidates:
            logger.info("No tickers need fundamental updates based on earnings")
            return {
                'total_tickers': len(tickers),
                'candidates_found': 0,
                'successful_updates': 0,
                'failed_updates': 0,
                'processing_time': time.time() - start_time
            }
        
        logger.info(f"Processing fundamental updates for {len(candidates)} tickers")
        
        successful_updates = 0
        failed_updates = 0
        
        try:
            # Process candidates with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_ticker = {
                    executor.submit(self._update_single_fundamental, ticker): ticker
                    for ticker in candidates
                }
                
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    
                    try:
                        success = future.result()
                        if success:
                            successful_updates += 1
                            logger.debug(f"Successfully updated fundamentals for {ticker}")
                        else:
                            failed_updates += 1
                            logger.warning(f"Failed to update fundamentals for {ticker}")
                            
                    except Exception as e:
                        failed_updates += 1
                        logger.error(f"Error updating fundamentals for {ticker}: {e}")
                        self.error_handler.handle_error(
                            f"Failed to update fundamentals for {ticker}", e, ErrorSeverity.MEDIUM
                        )
            
            processing_time = time.time() - start_time
            logger.info(f"Earnings-based updates completed in {processing_time:.2f}s")
            logger.info(f"Success: {successful_updates}, Failed: {failed_updates}")
            
            # Update monitoring metrics
            self.monitoring.record_metric(
                'earnings_based_update_time', processing_time
            )
            self.monitoring.record_metric(
                'earnings_based_success_rate', 
                successful_updates / len(candidates) if candidates else 0
            )
            
            return {
                'total_tickers': len(tickers),
                'candidates_found': len(candidates),
                'successful_updates': successful_updates,
                'failed_updates': failed_updates,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Earnings-based updates failed: {e}")
            self.error_handler.handle_error(
                "Earnings-based fundamental updates failed", e, ErrorSeverity.CRITICAL
            )
            return {
                'total_tickers': len(tickers),
                'candidates_found': len(candidates),
                'successful_updates': 0,
                'failed_updates': len(candidates),
                'processing_time': time.time() - start_time
            }
    
    def _update_single_fundamental(self, ticker: str) -> bool:
        """
        Update fundamental data for a single ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            True if update was successful
        """
        try:
            logger.debug(f"Updating fundamentals for {ticker}")
            
            # Try services in order of preference
            services = [
                ('Yahoo Finance', self._update_with_yahoo),
                ('FMP', self._update_with_fmp),
                ('Alpha Vantage', self._update_with_alpha_vantage)
            ]
            
            for service_name, service_func in services:
                try:
                    logger.debug(f"Trying {service_name} for {ticker}")
                    success = service_func(ticker)
                    
                    if success:
                        logger.info(f"Successfully updated {ticker} with {service_name}")
                        return True
                        
                except Exception as e:
                    logger.warning(f"{service_name} failed for {ticker}: {e}")
                    continue
            
            logger.error(f"All services failed for {ticker}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating fundamentals for {ticker}: {e}")
            return False
    
    def _update_with_yahoo(self, ticker: str) -> bool:
        """Update fundamentals using Yahoo Finance"""
        try:
            # Get fundamental data from Yahoo
            fundamental_data = self.yahoo_service.get_fundamental_data(ticker)
            if not fundamental_data:
                return False
            
            # Store in database
            return self._store_fundamental_data(ticker, fundamental_data, 'yahoo_finance')
            
        except Exception as e:
            logger.error(f"Yahoo Finance update failed for {ticker}: {e}")
            return False
    
    def _update_with_fmp(self, ticker: str) -> bool:
        """Update fundamentals using FMP"""
        try:
            # Get fundamental data from FMP
            fundamental_data = self.fmp_service.get_fundamental_data(ticker)
            if not fundamental_data:
                return False
            
            # Store in database
            return self._store_fundamental_data(ticker, fundamental_data, 'fmp')
            
        except Exception as e:
            logger.error(f"FMP update failed for {ticker}: {e}")
            return False
    
    def _update_with_alpha_vantage(self, ticker: str) -> bool:
        """Update fundamentals using Alpha Vantage"""
        try:
            # Get fundamental data from Alpha Vantage
            fundamental_data = self.alpha_vantage_service.get_fundamental_data(ticker)
            if not fundamental_data:
                return False
            
            # Store in database
            return self._store_fundamental_data(ticker, fundamental_data, 'alpha_vantage')
            
        except Exception as e:
            logger.error(f"Alpha Vantage update failed for {ticker}: {e}")
            return False
    
    def _store_fundamental_data(self, ticker: str, data: Dict, source: str) -> bool:
        """
        Store fundamental data in the database.
        
        Args:
            ticker: Ticker symbol
            data: Fundamental data dictionary
            source: Data source name
            
        Returns:
            True if storage was successful
        """
        try:
            # Update company_fundamentals table
            query = """
            INSERT INTO company_fundamentals (
                ticker, revenue, net_income, total_assets, total_liabilities,
                shareholders_equity, cash_and_equivalents, total_debt,
                operating_cash_flow, free_cash_flow, data_source, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (ticker, data_source) 
            DO UPDATE SET
                revenue = EXCLUDED.revenue,
                net_income = EXCLUDED.net_income,
                total_assets = EXCLUDED.total_assets,
                total_liabilities = EXCLUDED.total_liabilities,
                shareholders_equity = EXCLUDED.shareholders_equity,
                cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                total_debt = EXCLUDED.total_debt,
                operating_cash_flow = EXCLUDED.operating_cash_flow,
                free_cash_flow = EXCLUDED.free_cash_flow,
                updated_at = NOW()
            """
            
            values = (
                ticker,
                data.get('revenue'),
                data.get('net_income'),
                data.get('total_assets'),
                data.get('total_liabilities'),
                data.get('shareholders_equity'),
                data.get('cash_and_equivalents'),
                data.get('total_debt'),
                data.get('operating_cash_flow'),
                data.get('free_cash_flow'),
                source
            )
            
            self.db.execute(query, values)
            
            # Update stocks table with key metrics
            self._update_stocks_table(ticker, data, source)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing fundamental data for {ticker}: {e}")
            return False
    
    def _update_stocks_table(self, ticker: str, data: Dict, source: str):
        """Update stocks table with key fundamental metrics"""
        try:
            query = """
            UPDATE stocks 
            SET 
                revenue = %s,
                market_cap = %s,
                pe_ratio = %s,
                pb_ratio = %s,
                debt_to_equity = %s,
                updated_at = NOW()
            WHERE ticker = %s
            """
            
            # Calculate ratios
            market_cap = data.get('market_cap')
            net_income = data.get('net_income')
            shareholders_equity = data.get('shareholders_equity')
            total_debt = data.get('total_debt')
            
            pe_ratio = market_cap / net_income if market_cap and net_income and net_income > 0 else None
            pb_ratio = market_cap / shareholders_equity if market_cap and shareholders_equity and shareholders_equity > 0 else None
            debt_to_equity = total_debt / shareholders_equity if total_debt and shareholders_equity and shareholders_equity > 0 else None
            
            values = (
                data.get('revenue'),
                market_cap,
                pe_ratio,
                pb_ratio,
                debt_to_equity,
                ticker
            )
            
            self.db.execute(query, values)
            
        except Exception as e:
            logger.error(f"Error updating stocks table for {ticker}: {e}")
    
    def get_earnings_summary(self, tickers: List[str]) -> Dict:
        """
        Get summary of earnings status for tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary with earnings summary
        """
        summary = {
            'total_tickers': len(tickers),
            'recent_earnings': [],
            'upcoming_earnings': [],
            'no_earnings_data': []
        }
        
        for ticker in tickers:
            earnings_info = self._get_earnings_info(ticker)
            if not earnings_info:
                summary['no_earnings_data'].append(ticker)
                continue
            
            today = date.today()
            
            # Check recent earnings
            last_earnings = earnings_info.get('last_earnings_date')
            if last_earnings:
                days_since = (today - last_earnings).days
                if 0 <= days_since <= self.earnings_window_days:
                    summary['recent_earnings'].append({
                        'ticker': ticker,
                        'days_since': days_since,
                        'date': last_earnings
                    })
            
            # Check upcoming earnings
            next_earnings = earnings_info.get('next_earnings_date')
            if next_earnings:
                days_until = (next_earnings - today).days
                if 0 <= days_until <= 30:  # Next 30 days
                    summary['upcoming_earnings'].append({
                        'ticker': ticker,
                        'days_until': days_until,
                        'date': next_earnings
                    })
        
        return summary


def main():
    """Test the earnings-based fundamental processor"""
    logging.basicConfig(level=logging.INFO)
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
    
    # Initialize database and processor
    db = DatabaseManager()
    processor = EarningsBasedFundamentalProcessor(db)
    
    try:
        # Get earnings summary
        summary = processor.get_earnings_summary(test_tickers)
        
        print(f"\nEarnings Summary:")
        print(f"Total tickers: {summary['total_tickers']}")
        print(f"Recent earnings: {len(summary['recent_earnings'])}")
        print(f"Upcoming earnings: {len(summary['upcoming_earnings'])}")
        print(f"No earnings data: {len(summary['no_earnings_data'])}")
        
        # Process earnings-based updates
        results = processor.process_earnings_based_updates(test_tickers)
        
        print(f"\nUpdate Results:")
        print(f"Candidates found: {results['candidates_found']}")
        print(f"Successful updates: {results['successful_updates']}")
        print(f"Failed updates: {results['failed_updates']}")
        print(f"Processing time: {results['processing_time']:.2f}s")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main() 