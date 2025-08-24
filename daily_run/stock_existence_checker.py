#!/usr/bin/env python3
"""
Stock Existence Checker

Checks if stocks exist across multiple APIs to identify delisted securities.
Automatically removes stocks that can't be found in at least two APIs.
"""

import logging
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from .enhanced_multi_service_manager import EnhancedMultiServiceManager
    from .database import DatabaseManager
    from .error_handler import ErrorHandler, ErrorSeverity
    from .exceptions import DataNotFoundError, RateLimitError, ServiceError
except ImportError:
    from enhanced_multi_service_manager import EnhancedMultiServiceManager
    from database import DatabaseManager
    from error_handler import ErrorHandler, ErrorSeverity
    from exceptions import DataNotFoundError, RateLimitError, ServiceError

logger = logging.getLogger(__name__)


@dataclass
class ExistenceCheckResult:
    """Result of checking if a stock exists across APIs"""
    ticker: str
    exists_in_apis: List[str]
    not_found_in_apis: List[str]
    rate_limited_apis: List[str]
    error_apis: List[str]
    total_apis_checked: int
    should_remove: bool
    check_time: datetime


class StockExistenceChecker:
    """Checks stock existence across multiple APIs and manages delisted stock removal"""
    
    def __init__(self, db: DatabaseManager, service_manager: EnhancedMultiServiceManager = None):
        self.db = db
        self.service_manager = service_manager or EnhancedMultiServiceManager()
        self.error_handler = ErrorHandler("stock_existence_checker")
        
        # APIs to check in order of reliability - Finnhub first as it's the best API
        self.apis_to_check = ['finnhub', 'yahoo', 'fmp', 'alpha_vantage']
        
        # Batch processing configuration
        self.batch_size = 50
        self.delay_between_batches = 2  # seconds
        
        # Minimum number of APIs that must explicitly report "not found" to trigger removal
        self.min_not_found_apis = 2
        
    def check_stock_exists(self, ticker: str) -> ExistenceCheckResult:
        """Check if a stock exists across all available APIs"""
        exists_in = []
        not_found_in = []
        rate_limited_apis = []
        error_apis = []
        
        logger.debug(f"Checking existence for {ticker} across {len(self.apis_to_check)} APIs")
        
        for api_name in self.apis_to_check:
            try:
                result = self._check_single_api(ticker, api_name)
                if result == 'exists':
                    exists_in.append(api_name)
                elif result == 'not_found':
                    not_found_in.append(api_name)
                elif result == 'rate_limited':
                    rate_limited_apis.append(api_name)
                elif result == 'error':
                    error_apis.append(api_name)
                    
                # Small delay between API calls to be respectful
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Unexpected error checking {ticker} in {api_name}: {e}")
                error_apis.append(api_name)
        
        # Determine if stock should be removed
        # Only remove if at least 2 APIs explicitly reported "not found"
        # Rate limits and other errors don't count toward removal
        should_remove = len(not_found_in) >= self.min_not_found_apis
        
        if should_remove:
            logger.warning(f"🚨 {ticker} not found in {len(not_found_in)} APIs - marked for removal")
        elif len(not_found_in) > 0:
            logger.info(f"⚠️ {ticker} not found in {len(not_found_in)} APIs, but below removal threshold ({self.min_not_found_apis})")
        
        return ExistenceCheckResult(
            ticker=ticker,
            exists_in_apis=exists_in,
            not_found_in_apis=not_found_in,
            rate_limited_apis=rate_limited_apis,
            error_apis=error_apis,
            total_apis_checked=len(self.apis_to_check),
            should_remove=should_remove,
            check_time=datetime.now()
        )
    
    def _check_single_api(self, ticker: str, api_name: str) -> str:
        """
        Check if a stock exists in a specific API
        
        Returns:
            'exists': Stock found and data returned
            'not_found': API explicitly reported stock doesn't exist
            'rate_limited': API rate limit exceeded
            'error': Other API error occurred
        """
        try:
            if api_name == 'yahoo':
                return self._check_yahoo_finance(ticker)
            elif api_name == 'fmp':
                return self._check_fmp(ticker)
            elif api_name == 'finnhub':
                return self._check_finnhub(ticker)
            elif api_name == 'alpha_vantage':
                return self._check_alpha_vantage(ticker)
            else:
                logger.warning(f"Unknown API: {api_name}")
                return 'error'
                
        except Exception as e:
            logger.debug(f"Error checking {ticker} in {api_name}: {e}")
            return 'error'
    
    def _check_yahoo_finance(self, ticker: str) -> str:
        """Check if stock exists in Yahoo Finance"""
        try:
            service = self.service_manager.get_service('yahoo')
            if not service:
                return 'error'
            
            data = service.get_data(ticker)
            
            if data is not None and len(data) > 0:
                return 'exists'
            else:
                return 'not_found'
                
        except DataNotFoundError:
            # API explicitly reported stock doesn't exist
            return 'not_found'
        except RateLimitError:
            # API rate limit exceeded
            return 'rate_limited'
        except ServiceError:
            # Other service error
            return 'error'
        except Exception:
            # Unexpected error
            return 'error'
    
    def _check_fmp(self, ticker: str) -> str:
        """Check if stock exists in FMP"""
        try:
            service = self.service_manager.get_service('fmp')
            if not service:
                return 'error'
            
            data = service.get_data(ticker)
            
            if data is not None and len(data) > 0:
                return 'exists'
            else:
                return 'not_found'
                
        except DataNotFoundError:
            # API explicitly reported stock doesn't exist
            return 'not_found'
        except RateLimitError:
            # API rate limit exceeded
            return 'rate_limited'
        except ServiceError:
            # Other service error
            return 'error'
        except Exception:
            # Unexpected error
            return 'error'
    
    def _check_finnhub(self, ticker: str) -> str:
        """Check if stock exists in Finnhub"""
        try:
            service = self.service_manager.get_service('finnhub')
            if not service:
                return 'error'
            
            data = service.get_data(ticker)
            
            if data is not None and len(data) > 0:
                return 'exists'
            else:
                return 'not_found'
                
        except DataNotFoundError:
            # API explicitly reported stock doesn't exist
            return 'not_found'
        except RateLimitError:
            # API rate limit exceeded
            return 'rate_limited'
        except ServiceError:
            # Other service error
            return 'error'
        except Exception:
            # Unexpected error
            return 'error'
    
    def _check_alpha_vantage(self, ticker: str) -> str:
        """Check if stock exists in Alpha Vantage"""
        try:
            service = self.service_manager.get_service('alpha_vantage')
            if not service:
                return 'error'
            
            data = service.get_data(ticker)
            
            if data is not None and len(data) > 0:
                return 'exists'
            else:
                return 'not_found'
                
        except DataNotFoundError:
            # API explicitly reported stock doesn't exist
            return 'not_found'
        except RateLimitError:
            # API rate limit exceeded
            return 'rate_limited'
        except ServiceError:
            # Other service error
            return 'error'
        except Exception:
            # Unexpected error
            return 'error'
    
    def process_tickers_in_batches(self, tickers: List[str]) -> Dict[str, ExistenceCheckResult]:
        """Process multiple tickers in batches to check existence"""
        logger.info(f"Processing {len(tickers)} tickers in batches of {self.batch_size}")
        
        results = {}
        total_batches = (len(tickers) + self.batch_size - 1) // self.batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(tickers))
            batch_tickers = tickers[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches}: {len(batch_tickers)} tickers")
            
            for ticker in batch_tickers:
                try:
                    result = self.check_stock_exists(ticker)
                    results[ticker] = result
                    
                    if result.should_remove:
                        logger.warning(f"🚨 {ticker} not found in {len(result.not_found_in_apis)} APIs - marked for removal")
                    else:
                        logger.debug(f"✅ {ticker} found in {len(result.exists_in_apis)} APIs")
                        
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
                    # Mark as should remove if we can't check it
                    results[ticker] = ExistenceCheckResult(
                        ticker=ticker,
                        exists_in_apis=[],
                        not_found_in_apis=self.apis_to_check,
                        rate_limited_apis=[],
                        error_apis=[],
                        total_apis_checked=len(self.apis_to_check),
                        should_remove=True,
                        check_time=datetime.now()
                    )
            
            # Delay between batches to respect rate limits
            if batch_num < total_batches - 1:
                logger.debug(f"Waiting {self.delay_between_batches}s before next batch")
                time.sleep(self.delay_between_batches)
        
        return results
    
    def remove_delisted_stocks(self, check_results: Dict[str, ExistenceCheckResult]) -> Dict[str, int]:
        """Remove stocks that should be deleted based on existence check results"""
        to_remove = [ticker for ticker, result in check_results.items() if result.should_remove]
        
        if not to_remove:
            logger.info("No stocks to remove")
            return {'removed': 0, 'errors': 0}
        
        logger.info(f"Removing {len(to_remove)} delisted stocks from database")
        
        removed_count = 0
        error_count = 0
        
        for ticker in to_remove:
            try:
                if self._remove_stock_from_database(ticker):
                    removed_count += 1
                    logger.info(f"✅ Successfully removed {ticker}")
                else:
                    error_count += 1
                    logger.error(f"❌ Failed to remove {ticker}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error removing {ticker}: {e}")
                self.error_handler.handle_error(
                    f"Failed to remove delisted stock {ticker}", e, ErrorSeverity.MEDIUM
                )
        
        logger.info(f"Delisted stock removal completed: {removed_count} removed, {error_count} errors")
        return {'removed': removed_count, 'errors': error_count}
    
    def _remove_stock_from_database(self, ticker: str) -> bool:
        """Remove a stock from all database tables, respecting foreign key constraints"""
        try:
            # Order matters due to foreign key constraints
            tables_to_clean = [
                'daily_charts',
                'technical_indicators', 
                'company_fundamentals',
                'stocks'
            ]
            
            for table in tables_to_clean:
                try:
                    # Check if table exists
                    check_query = """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """
                    table_exists = self.db.fetch_one(check_query, (table,))
                    
                    if table_exists and table_exists[0]:
                        # Delete from table
                        delete_query = f"DELETE FROM {table} WHERE ticker = %s"
                        self.db.execute_update(delete_query, (ticker,))
                        logger.debug(f"Removed {ticker} from {table}")
                        
                except Exception as e:
                    logger.warning(f"Could not remove {ticker} from {table}: {e}")
                    # Continue with other tables
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing {ticker} from database: {e}")
            return False
