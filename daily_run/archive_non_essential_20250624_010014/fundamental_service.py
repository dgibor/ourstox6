#!/usr/bin/env python3
"""
Fundamental data service with multi-provider support
"""

import logging
import time
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from base_service import BaseService
from yahoo_finance_service import YahooFinanceService
from fmp_service import FMPService
from config import Config
from exceptions import ServiceError, RateLimitError, DataNotFoundError

class FundamentalService:
    """Consolidated fundamental data service with fallback providers"""
    
    def __init__(self):
        """Initialize fundamental service with multiple providers"""
        self.logger = logging.getLogger(__name__)
        self.providers = {
            'yahoo': YahooFinanceService(),
            'fmp': FMPService()
        }
        self.provider_order = ['yahoo', 'fmp']  # Priority order
        self.rate_limits = Config.RATE_LIMITS
        # Add api_key attribute for ServiceFactory compatibility
        self.api_key = "consolidated"  # Dummy value since this service doesn't need a single API key
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data with fallback providers"""
        self.logger.info(f"Fetching fundamental data for {ticker}")
        
        for provider_name in self.provider_order:
            try:
                self.logger.debug(f"Trying {provider_name} for {ticker}")
                
                if provider_name == 'yahoo':
                    data = self._get_yahoo_data(ticker)
                elif provider_name == 'fmp':
                    data = self._get_fmp_data(ticker)
                else:
                    continue
                
                if data:
                    self.logger.info(f"Successfully fetched data from {provider_name} for {ticker}")
                    return {
                        'ticker': ticker,
                        'provider': provider_name,
                        'data': data,
                        'timestamp': datetime.now()
                    }
                
            except RateLimitError:
                self.logger.warning(f"Rate limit reached for {provider_name}, trying next provider")
                continue
            except Exception as e:
                self.logger.warning(f"Error with {provider_name} for {ticker}: {e}")
                continue
        
        self.logger.error(f"All providers failed for {ticker}")
        return None
    
    def _get_yahoo_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get data from Yahoo Finance"""
        try:
            yahoo_service = self.providers['yahoo']
            financial_data = yahoo_service.fetch_financial_statements(ticker)
            key_stats = yahoo_service.fetch_key_statistics(ticker)
            
            if financial_data or key_stats:
                return self._merge_yahoo_data(financial_data, key_stats)
            
            return None
            
        except Exception as e:
            raise ServiceError('yahoo', str(e), ticker)
    
    def _get_fmp_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get data from Financial Modeling Prep"""
        try:
            fmp_service = self.providers['fmp']
            return fmp_service.get_fundamental_data(ticker)
            
        except Exception as e:
            raise ServiceError('fmp', str(e), ticker)
    
    def _merge_yahoo_data(self, financial_data: Dict, key_stats: Dict) -> Dict[str, Any]:
        """Merge Yahoo financial and key statistics data"""
        merged = {}
        
        # Merge income statement data
        if financial_data and 'income_statement' in financial_data:
            merged.update(financial_data['income_statement'])
        
        # Merge balance sheet data
        if financial_data and 'balance_sheet' in financial_data:
            merged.update(financial_data['balance_sheet'])
        
        # Merge key statistics
        if key_stats:
            merged.update(key_stats)
        
        return merged
    
    def store_fundamental_data(self, ticker: str, data: Dict[str, Any]) -> bool:
        """Store fundamental data in database"""
        try:
            # Use Yahoo service to store data (it has the database methods)
            yahoo_service = self.providers['yahoo']
            return yahoo_service.store_fundamental_data(ticker, data, {})
            
        except Exception as e:
            self.logger.error(f"Error storing fundamental data for {ticker}: {e}")
            return False
    
    def get_fundamental_data_with_storage(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get and store fundamental data"""
        data = self.get_fundamental_data(ticker)
        
        if data:
            if self.store_fundamental_data(ticker, data['data']):
                self.logger.info(f"Successfully stored fundamental data for {ticker}")
            else:
                self.logger.warning(f"Failed to store fundamental data for {ticker}")
        
        return data
    
    def get_tickers_needing_fundamentals(self, max_age_days: int = 30) -> List[str]:
        """Get tickers that need fundamental data updates"""
        from database import DatabaseManager
        
        db = DatabaseManager()
        try:
            # Get tickers with missing or old fundamental data
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            query = """
                SELECT DISTINCT s.ticker 
                FROM stocks s 
                LEFT JOIN company_fundamentals f ON s.ticker = f.ticker 
                WHERE f.ticker IS NULL 
                   OR f.last_updated < %s 
                   OR f.revenue IS NULL 
                   OR f.net_income IS NULL
                ORDER BY f.last_updated ASC NULLS FIRST
            """
            
            results = db.execute_query(query, (cutoff_date,))
            tickers = [row[0] for row in results]
            
            self.logger.info(f"Found {len(tickers)} tickers needing fundamental updates")
            return tickers
            
        except Exception as e:
            self.logger.error(f"Error getting tickers needing fundamentals: {e}")
            return []
        finally:
            db.disconnect()
    
    def get_priority_tickers(self, limit: int = 50) -> List[str]:
        """Get priority tickers for daily updates (missing data first, then oldest)"""
        from database import DatabaseManager
        
        db = DatabaseManager()
        try:
            # Get tickers with missing fundamental data first
            missing_query = """
                SELECT DISTINCT s.ticker 
                FROM stocks s 
                LEFT JOIN company_fundamentals f ON s.ticker = f.ticker 
                WHERE f.ticker IS NULL 
                   OR f.revenue IS NULL 
                   OR f.net_income IS NULL
                LIMIT %s
            """
            
            missing_results = db.execute_query(missing_query, (limit,))
            missing_tickers = [row[0] for row in missing_results]
            
            # If we need more, get oldest updated tickers
            remaining_limit = limit - len(missing_tickers)
            if remaining_limit > 0:
                oldest_query = """
                    SELECT ticker 
                    FROM company_fundamentals 
                    WHERE ticker NOT IN %s
                    ORDER BY last_updated ASC 
                    LIMIT %s
                """
                
                if missing_tickers:
                    oldest_results = db.execute_query(oldest_query, (tuple(missing_tickers), remaining_limit))
                else:
                    oldest_results = db.execute_query("SELECT ticker FROM company_fundamentals ORDER BY last_updated ASC LIMIT %s", (remaining_limit,))
                
                oldest_tickers = [row[0] for row in oldest_results]
                missing_tickers.extend(oldest_tickers)
            
            return missing_tickers[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting priority tickers: {e}")
            return []
        finally:
            db.disconnect()
    
    def batch_update_fundamentals(self, tickers: List[str], max_concurrent: int = 5) -> Dict[str, Any]:
        """Update fundamentals for multiple tickers with batch processing"""
        results = {
            'total': len(tickers),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Try batch requests first (where supported)
        batch_results = self._try_batch_fundamental_requests(tickers)
        results['successful'] += batch_results['successful']
        results['failed'] += batch_results['failed']
        results['errors'].extend(batch_results['errors'])
        
        # Get remaining tickers that weren't processed in batch
        processed_tickers = set(batch_results['processed_tickers'])
        remaining_tickers = [t for t in tickers if t not in processed_tickers]
        
        # Process remaining tickers individually
        for i, ticker in enumerate(remaining_tickers):
            try:
                self.logger.info(f"Processing {i+1}/{len(remaining_tickers)}: {ticker}")
                
                data = self.get_fundamental_data_with_storage(ticker)
                if data:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"{ticker}: No data available")
                
                # Rate limiting
                if i % max_concurrent == 0 and i > 0:
                    time.sleep(2)
                
            except Exception as e:
                results['failed'] += 1
                error_msg = f"{ticker}: {str(e)}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        return results
    
    def _try_batch_fundamental_requests(self, tickers: List[str]) -> Dict[str, Any]:
        """Try to get fundamental data for multiple tickers in batch requests"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processed_tickers': []
        }
        
        # FMP supports batch fundamental data
        try:
            fmp_batch = self._get_fmp_batch_fundamentals(tickers)
            results['successful'] += fmp_batch['successful']
            results['failed'] += fmp_batch['failed']
            results['errors'].extend(fmp_batch['errors'])
            results['processed_tickers'].extend(fmp_batch['processed_tickers'])
        except Exception as e:
            self.logger.error(f"FMP batch fundamental request failed: {e}")
        
        return results
    
    def _get_fmp_batch_fundamentals(self, tickers: List[str]) -> Dict[str, Any]:
        """Get batch fundamental data from FMP"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processed_tickers': []
        }
        
        if not tickers:
            return results
        
        try:
            # Process tickers in smaller batches (FMP has limits)
            batch_size = 10
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                
                for ticker in batch:
                    try:
                        data = self._get_fmp_data(ticker)
                        if data and self.store_fundamental_data(ticker, data):
                            results['successful'] += 1
                            results['processed_tickers'].append(ticker)
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"{ticker}: No FMP data")
                        
                        # Rate limiting between individual requests
                        time.sleep(0.2)  # 5 requests per second
                        
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"{ticker}: {str(e)}")
                
                # Rate limiting between batches
                time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"FMP batch fundamental request error: {e}")
        
        return results
    
    def daily_gradual_update(self, max_tickers: int = 100) -> Dict[str, Any]:
        """Perform daily gradual update of fundamental data"""
        self.logger.info(f"Starting daily gradual fundamental update (max {max_tickers} tickers)")
        
        # Get priority tickers for today's update
        priority_tickers = self.get_priority_tickers(max_tickers)
        
        if not priority_tickers:
            self.logger.info("No tickers need fundamental updates today")
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'errors': []
            }
        
        # Perform batch update
        results = self.batch_update_fundamentals(priority_tickers)
        
        self.logger.info(f"Daily gradual update completed: {results['successful']}/{results['total']} successful")
        return results
    
    def close(self):
        """Close all provider connections"""
        for provider_name, provider in self.providers.items():
            try:
                if hasattr(provider, 'close'):
                    provider.close()
                self.logger.info(f"Closed {provider_name} provider")
            except Exception as e:
                self.logger.error(f"Error closing {provider_name}: {e}")

def test_fundamental_service():
    """Test fundamental service functionality"""
    print("Testing Fundamental Service")
    print("=" * 30)
    
    service = FundamentalService()
    
    try:
        # Test with AAPL
        result = service.get_fundamental_data('AAPL')
        if result:
            print(f"Successfully fetched data from {result['provider']}")
            print(f"   Ticker: {result['ticker']}")
            print(f"   Data keys: {list(result['data'].keys())}")
        else:
            print("Failed to fetch fundamental data")
        
        # Test priority tickers
        priority_tickers = service.get_priority_tickers(5)
        print(f"Priority tickers: {priority_tickers}")
        
        # Test batch update
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        batch_result = service.batch_update_fundamentals(test_tickers)
        print(f"Batch update: {batch_result['successful']}/{batch_result['total']} successful")
        
        # Test daily gradual update
        daily_result = service.daily_gradual_update(10)
        print(f"Daily update: {daily_result['successful']}/{daily_result['total']} successful")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        service.close()
        print("Fundamental service test completed")

if __name__ == "__main__":
    test_fundamental_service() 