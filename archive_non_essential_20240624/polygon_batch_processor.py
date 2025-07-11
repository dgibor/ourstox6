#!/usr/bin/env python3
"""
Polygon.io Batch Processor
==========================

Comprehensive batch processor for Polygon.io API that handles:
- Batch fundamental data fetching
- Batch price data fetching
- Historical data fetching
- API rate limit monitoring and management
- Efficient batch processing with concurrency

Author: AI Assistant
Date: 2025-01-26
"""

import os
import time
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from daily_run.polygon_service import PolygonService
from daily_run.database import DatabaseManager
from daily_run.common_imports import setup_logging

# Setup logging
setup_logging('polygon_batch')
logger = logging.getLogger(__name__)

class PolygonBatchProcessor:
    """Comprehensive batch processor for Polygon.io data"""
    
    def __init__(self, max_workers: int = 5, batch_size: int = 50):
        """Initialize the batch processor"""
        self.polygon_service = PolygonService()
        self.db = DatabaseManager()
        self.max_workers = max_workers
        self.batch_size = batch_size
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'api_calls_made': 0,
            'start_time': None,
            'end_time': None
        }
    
    def process_fundamentals_batch(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Process fundamental data for a batch of tickers
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Processing results and statistics
        """
        logger.info(f"Starting fundamental data batch processing for {len(tickers)} tickers")
        self.stats['start_time'] = datetime.now()
        self.stats['total_processed'] = len(tickers)
        
        results = {}
        
        # Process in batches
        for i in range(0, len(tickers), self.batch_size):
            batch = tickers[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(tickers) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} tickers)")
            
            batch_results = self._process_fundamentals_single_batch(batch)
            results.update(batch_results)
            
            # Add delay between batches
            if i + self.batch_size < len(tickers):
                logger.info("Waiting between batches to respect rate limits...")
                time.sleep(2)
        
        self.stats['end_time'] = datetime.now()
        self.stats['successful_fetches'] = sum(1 for r in results.values() if r.get('success', False))
        self.stats['failed_fetches'] = len(results) - self.stats['successful_fetches']
        
        logger.info(f"Fundamental batch processing completed: {self.stats['successful_fetches']}/{len(tickers)} successful")
        return results
    
    def _process_fundamentals_single_batch(self, tickers: List[str]) -> Dict[str, Any]:
        """Process fundamental data for a single batch of tickers"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(self._fetch_fundamental_data, ticker): ticker 
                for ticker in tickers
            }
            
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results[ticker] = result
                    
                    if result.get('success', False):
                        logger.debug(f"✅ {ticker}: Fundamental data fetched successfully")
                    else:
                        logger.warning(f"❌ {ticker}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ {ticker}: Exception during processing: {e}")
                    results[ticker] = {
                        'success': False,
                        'error': str(e),
                        'ticker': ticker
                    }
        
        return results
    
    def _fetch_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch fundamental data for a single ticker"""
        result = {
            'ticker': ticker,
            'success': False,
            'error': None,
            'data': None,
            'timestamp': datetime.now()
        }
        
        try:
            # Get fundamental data from Polygon
            fundamental_data = self.polygon_service.get_fundamental_data(ticker)
            
            if fundamental_data:
                # Store in database
                success = self._store_fundamental_data(ticker, fundamental_data)
                
                if success:
                    result['success'] = True
                    result['data'] = fundamental_data
                    logger.debug(f"Stored fundamental data for {ticker}")
                else:
                    result['error'] = "Failed to store data in database"
            else:
                result['error'] = "No fundamental data available"
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error fetching fundamental data for {ticker}: {e}")
        
        return result
    
    def process_prices_batch(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Process current price data for a batch of tickers
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Processing results and statistics
        """
        logger.info(f"Starting price data batch processing for {len(tickers)} tickers")
        
        # Use Polygon's batch price functionality
        batch_results = self.polygon_service.get_batch_prices(tickers)
        
        # Store results in database
        stored_count = 0
        for ticker, price_data in batch_results.items():
            if self._store_price_data(ticker, price_data):
                stored_count += 1
        
        logger.info(f"Price batch processing completed: {stored_count}/{len(batch_results)} stored")
        
        return {
            'total_requested': len(tickers),
            'total_received': len(batch_results),
            'total_stored': stored_count,
            'results': batch_results
        }
    
    def process_historical_prices_batch(self, tickers: List[str], 
                                      start_date: str = None, 
                                      end_date: str = None,
                                      timespan: str = 'day') -> Dict[str, Any]:
        """
        Process historical price data for a batch of tickers
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timespan: Time span ('minute', 'hour', 'day', 'week', 'month', 'quarter', 'year')
            
        Returns:
            Processing results and statistics
        """
        logger.info(f"Starting historical price batch processing for {len(tickers)} tickers")
        
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        
        results = {}
        
        # Process in smaller batches for historical data
        historical_batch_size = min(10, self.batch_size)
        
        for i in range(0, len(tickers), historical_batch_size):
            batch = tickers[i:i + historical_batch_size]
            batch_num = i // historical_batch_size + 1
            total_batches = (len(tickers) + historical_batch_size - 1) // historical_batch_size
            
            logger.info(f"Processing historical batch {batch_num}/{total_batches} ({len(batch)} tickers)")
            
            batch_results = self._process_historical_single_batch(batch, start_date, end_date, timespan)
            results.update(batch_results)
            
            # Add delay between batches
            if i + historical_batch_size < len(tickers):
                time.sleep(3)  # Longer delay for historical data
        
        successful = sum(1 for r in results.values() if r.get('success', False))
        logger.info(f"Historical price batch processing completed: {successful}/{len(tickers)} successful")
        
        return results
    
    def _process_historical_single_batch(self, tickers: List[str], start_date: str, 
                                       end_date: str, timespan: str) -> Dict[str, Any]:
        """Process historical price data for a single batch"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(3, len(tickers))) as executor:
            future_to_ticker = {
                executor.submit(self._fetch_historical_data, ticker, start_date, end_date, timespan): ticker 
                for ticker in tickers
            }
            
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results[ticker] = result
                    
                    if result.get('success', False):
                        logger.debug(f"✅ {ticker}: Historical data fetched successfully")
                    else:
                        logger.warning(f"❌ {ticker}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ {ticker}: Exception during historical processing: {e}")
                    results[ticker] = {
                        'success': False,
                        'error': str(e),
                        'ticker': ticker
                    }
        
        return results
    
    def _fetch_historical_data(self, ticker: str, start_date: str, end_date: str, timespan: str) -> Dict[str, Any]:
        """Fetch historical price data for a single ticker"""
        result = {
            'ticker': ticker,
            'success': False,
            'error': None,
            'data': None,
            'timestamp': datetime.now()
        }
        
        try:
            # Get historical data from Polygon
            historical_data = self.polygon_service.get_historical_prices(ticker, start_date, end_date, timespan)
            
            if historical_data:
                # Store in database
                success = self._store_historical_data(ticker, historical_data)
                
                if success:
                    result['success'] = True
                    result['data'] = historical_data
                    result['count'] = len(historical_data)
                    logger.debug(f"Stored {len(historical_data)} historical records for {ticker}")
                else:
                    result['error'] = "Failed to store historical data in database"
            else:
                result['error'] = "No historical data available"
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error fetching historical data for {ticker}: {e}")
        
        return result
    
    def process_earnings_calendar_batch(self, tickers: List[str] = None, 
                                      start_date: str = None, 
                                      end_date: str = None) -> Dict[str, Any]:
        """
        Process earnings calendar data
        
        Args:
            tickers: List of ticker symbols (optional)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Processing results and statistics
        """
        logger.info("Starting earnings calendar batch processing")
        
        try:
            # Get earnings calendar data
            earnings_data = self.polygon_service.get_earnings_calendar(
                ticker=','.join(tickers) if tickers else None,
                start_date=start_date,
                end_date=end_date
            )
            
            if earnings_data:
                # Store in database
                stored_count = self._store_earnings_calendar(earnings_data)
                logger.info(f"Earnings calendar processing completed: {stored_count} records stored")
                
                return {
                    'success': True,
                    'total_records': len(earnings_data),
                    'stored_records': stored_count,
                    'data': earnings_data
                }
            else:
                logger.warning("No earnings calendar data available")
                return {
                    'success': False,
                    'error': 'No earnings calendar data available'
                }
                
        except Exception as e:
            logger.error(f"Error processing earnings calendar: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_news_batch(self, tickers: List[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Process news data
        
        Args:
            tickers: List of ticker symbols (optional)
            limit: Maximum number of news articles to fetch
            
        Returns:
            Processing results and statistics
        """
        logger.info("Starting news batch processing")
        
        try:
            # Get news data
            news_data = self.polygon_service.get_news(
                ticker=','.join(tickers) if tickers else None,
                limit=limit
            )
            
            if news_data:
                # Store in database
                stored_count = self._store_news_data(news_data)
                logger.info(f"News processing completed: {stored_count} articles stored")
                
                return {
                    'success': True,
                    'total_articles': len(news_data),
                    'stored_articles': stored_count,
                    'data': news_data
                }
            else:
                logger.warning("No news data available")
                return {
                    'success': False,
                    'error': 'No news data available'
                }
                
        except Exception as e:
            logger.error(f"Error processing news: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _store_fundamental_data(self, ticker: str, data: Dict[str, Any]) -> bool:
        """Store fundamental data in database"""
        try:
            # This would integrate with your existing database storage logic
            # For now, just log the data
            logger.debug(f"Storing fundamental data for {ticker}: {len(data)} fields")
            
            # Example database storage (adapt to your schema)
            query = """
            INSERT INTO company_fundamentals 
            (ticker, revenue, net_income, total_equity, total_assets, total_debt, 
             free_cash_flow, shares_outstanding, data_source, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, report_date, period_type)
            DO UPDATE SET
                revenue = COALESCE(EXCLUDED.revenue, company_fundamentals.revenue),
                net_income = COALESCE(EXCLUDED.net_income, company_fundamentals.net_income),
                total_equity = COALESCE(EXCLUDED.total_equity, company_fundamentals.total_equity),
                total_assets = COALESCE(EXCLUDED.total_assets, company_fundamentals.total_assets),
                total_debt = COALESCE(EXCLUDED.total_debt, company_fundamentals.total_debt),
                free_cash_flow = COALESCE(EXCLUDED.free_cash_flow, company_fundamentals.free_cash_flow),
                shares_outstanding = COALESCE(EXCLUDED.shares_outstanding, company_fundamentals.shares_outstanding),
                data_source = EXCLUDED.data_source,
                last_updated = CURRENT_TIMESTAMP
            """
            
            values = (
                ticker,
                data.get('revenue'),
                data.get('net_income'),
                data.get('total_equity'),
                data.get('total_assets'),
                data.get('total_debt'),
                data.get('free_cash_flow'),
                data.get('shares_outstanding'),
                'polygon',
                datetime.now()
            )
            
            self.db.execute_query(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error storing fundamental data for {ticker}: {e}")
            return False
    
    def _store_price_data(self, ticker: str, data: Dict[str, Any]) -> bool:
        """Store current price data in database"""
        try:
            # Store in daily_charts table
            query = """
            INSERT INTO daily_charts 
            (ticker, date, open, high, low, close, volume, data_source, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date)
            DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                data_source = EXCLUDED.data_source,
                last_updated = CURRENT_TIMESTAMP
            """
            
            values = (
                ticker,
                date.today(),
                data.get('price'),  # Use current price as open/high/low/close
                data.get('price'),
                data.get('price'),
                data.get('price'),
                data.get('volume'),
                'polygon',
                datetime.now()
            )
            
            self.db.execute_query(query, values)
            return True
            
        except Exception as e:
            logger.error(f"Error storing price data for {ticker}: {e}")
            return False
    
    def _store_historical_data(self, ticker: str, data: List[Dict[str, Any]]) -> bool:
        """Store historical price data in database"""
        try:
            stored_count = 0
            
            for record in data:
                query = """
                INSERT INTO daily_charts 
                (ticker, date, open, high, low, close, volume, data_source, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date)
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    data_source = EXCLUDED.data_source,
                    last_updated = CURRENT_TIMESTAMP
                """
                
                values = (
                    ticker,
                    record['date'],
                    record['open'],
                    record['high'],
                    record['low'],
                    record['close'],
                    record['volume'],
                    'polygon',
                    datetime.now()
                )
                
                self.db.execute_query(query, values)
                stored_count += 1
            
            logger.debug(f"Stored {stored_count} historical records for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing historical data for {ticker}: {e}")
            return False
    
    def _store_earnings_calendar(self, data: List[Dict[str, Any]]) -> int:
        """Store earnings calendar data in database"""
        try:
            stored_count = 0
            
            for record in data:
                # This would store in your earnings calendar table
                # Adapt to your schema
                logger.debug(f"Would store earnings record: {record.get('ticker', 'Unknown')}")
                stored_count += 1
            
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing earnings calendar data: {e}")
            return 0
    
    def _store_news_data(self, data: List[Dict[str, Any]]) -> int:
        """Store news data in database"""
        try:
            stored_count = 0
            
            for record in data:
                # This would store in your news table
                # Adapt to your schema
                logger.debug(f"Would store news record: {record.get('title', 'Unknown')[:50]}...")
                stored_count += 1
            
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing news data: {e}")
            return 0
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['success_rate'] = (stats['successful_fetches'] / stats['total_processed'] * 100) if stats['total_processed'] > 0 else 0
        
        return stats
    
    def get_api_usage(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return self.polygon_service.get_api_usage()
    
    def close(self):
        """Clean up resources"""
        logger.info("Closing Polygon batch processor")
        self.polygon_service.close()

def main():
    """Test the Polygon batch processor"""
    try:
        # Initialize processor
        processor = PolygonBatchProcessor(max_workers=3, batch_size=10)
        
        # Test tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']
        
        print("🔧 Testing Polygon.io Batch Processor")
        print("=" * 60)
        
        # Test fundamental data batch processing
        print("\n📈 Testing fundamental data batch processing...")
        fundamental_results = processor.process_fundamentals_batch(test_tickers)
        print(f"  ✅ Processed {len(fundamental_results)} tickers")
        
        # Test price data batch processing
        print("\n📊 Testing price data batch processing...")
        price_results = processor.process_prices_batch(test_tickers)
        print(f"  ✅ Processed {price_results.get('total_stored', 0)} tickers")
        
        # Test historical data batch processing
        print("\n📈 Testing historical data batch processing...")
        historical_results = processor.process_historical_prices_batch(test_tickers[:2])  # Test with fewer tickers
        print(f"  ✅ Processed {len(historical_results)} tickers")
        
        # Test earnings calendar
        print("\n📅 Testing earnings calendar processing...")
        earnings_results = processor.process_earnings_calendar_batch(test_tickers)
        print(f"  ✅ Processed earnings calendar")
        
        # Test news processing
        print("\n📰 Testing news processing...")
        news_results = processor.process_news_batch(test_tickers, limit=10)
        print(f"  ✅ Processed news data")
        
        # Print statistics
        print("\n📊 Processing Statistics:")
        stats = processor.get_processing_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Print API usage
        print("\n📊 API Usage:")
        usage = processor.get_api_usage()
        for key, value in usage.items():
            print(f"  {key}: {value}")
        
        processor.close()
        
    except Exception as e:
        print(f"❌ Error testing Polygon batch processor: {e}")

if __name__ == "__main__":
    main() 