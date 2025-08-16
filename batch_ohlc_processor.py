#!/usr/bin/env python3
"""
Batch OHLC Processor - Fixed Version
Uses Yahoo Finance as primary source for full OHLC data instead of FMP which only provides close prices
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import time
import traceback

# Add daily_run to path for imports
sys.path.append('daily_run')

from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor

logger = logging.getLogger(__name__)

class BatchOHLCProcessor:
    """
    Processes OHLC data for multiple tickers using Yahoo Finance batch API
    Provides full Open, High, Low, Close data instead of just close prices
    """
    
    def __init__(self, db: DatabaseManager, max_batch_size: int = 100, 
                 max_workers: int = 5, delay_between_batches: float = 1.0):
        self.db = db
        self.max_batch_size = max_batch_size
        self.max_workers = max_workers
        self.delay_between_batches = delay_between_batches
        self.error_handler = ErrorHandler("batch_ohlc_processor")
        self.monitoring = SystemMonitor()
        
        # Initialize Yahoo Finance service (primary source for OHLC)
        try:
            from daily_run.yahoo_finance_service import YahooFinanceService
            self.yahoo_service = YahooFinanceService()
            logger.info("Yahoo Finance service initialized for batch OHLC processing")
        except Exception as e:
            logger.error(f"Failed to initialize Yahoo Finance service: {e}")
            self.yahoo_service = None
        
        # Initialize fallback services
        try:
            from daily_run.alpha_vantage_service import AlphaVantageService
            self.alpha_vantage_service = AlphaVantageService()
        except:
            self.alpha_vantage_service = None
            logger.warning("Alpha Vantage service not available")
            
        try:
            from daily_run.finnhub_service import FinnhubService
            self.finnhub_service = FinnhubService()
        except:
            self.finnhub_service = None
            logger.warning("Finnhub service not available")
        
        # Service priority for OHLC data (Yahoo first for full data)
        self.service_priority = [
            ('Yahoo Finance', self._get_yahoo_batch_ohlc),
            ('Alpha Vantage', self._get_alpha_vantage_batch_ohlc),
            ('Finnhub', self._get_finnhub_batch_ohlc)
        ]
    
    def _get_yahoo_batch_ohlc(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch OHLC data from Yahoo Finance (primary source)"""
        try:
            if not self.yahoo_service:
                logger.warning("Yahoo service not available, skipping batch")
                return {}
            
            logger.info(f"Fetching batch OHLC data for {len(tickers)} tickers from Yahoo Finance")
            
            # Use yfinance batch download for full OHLC data
            import yfinance as yf
            
            # Download batch data with full OHLC
            data = yf.download(' '.join(tickers), period="1d", group_by='ticker', progress=False)
            
            if data.empty:
                logger.warning("Yahoo Finance returned empty data")
                return {}
            
            results = {}
            
            # Process multi-level columns from batch download
            if isinstance(data.columns, pd.MultiIndex):
                for ticker in tickers:
                    try:
                        if ticker in data.columns.levels[0]:
                            ticker_data = data[ticker].iloc[-1]
                            
                            # Check if we have valid OHLC data
                            if not any(pd.isna(ticker_data[field]) for field in ['Open', 'High', 'Low', 'Close']):
                                results[ticker] = {
                                    'ticker': ticker,
                                    'open': float(ticker_data['Open']),
                                    'high': float(ticker_data['High']),
                                    'low': float(ticker_data['Low']),
                                    'close': float(ticker_data['Close']),
                                    'volume': int(ticker_data['Volume']) if pd.notna(ticker_data['Volume']) else 0,
                                    'data_source': 'yahoo',
                                    'timestamp': datetime.now()
                                }
                                logger.debug(f"✅ {ticker}: O={ticker_data['Open']:.2f}, H={ticker_data['High']:.2f}, L={ticker_data['Low']:.2f}, C={ticker_data['Close']:.2f}")
                            else:
                                logger.warning(f"❌ {ticker}: Missing OHLC data from Yahoo")
                        else:
                            logger.warning(f"❌ {ticker}: Not found in Yahoo batch response")
                    except Exception as e:
                        logger.error(f"Error processing {ticker} from Yahoo batch: {e}")
                        continue
            else:
                # Single ticker case
                if len(tickers) == 1:
                    ticker = tickers[0]
                    try:
                        if not any(pd.isna(data[field].iloc[-1]) for field in ['Open', 'High', 'Low', 'Close']):
                            results[ticker] = {
                                'ticker': ticker,
                                'open': float(data['Open'].iloc[-1]),
                                'high': float(data['High'].iloc[-1]),
                                'low': float(data['Low'].iloc[-1]),
                                'close': float(data['Close'].iloc[-1]),
                                'volume': int(data['Volume'].iloc[-1]) if pd.notna(data['Volume'].iloc[-1]) else 0,
                                'data_source': 'yahoo',
                                'timestamp': datetime.now()
                            }
                            logger.debug(f"✅ {ticker}: O={data['Open'].iloc[-1]:.2f}, H={data['High'].iloc[-1]:.2f}, L={data['Low'].iloc[-1]:.2f}, C={data['Close'].iloc[-1]:.2f}")
                    except Exception as e:
                        logger.error(f"Error processing single ticker {ticker}: {e}")
            
            logger.info(f"Yahoo Finance batch: {len(results)}/{len(tickers)} successful")
            return results
            
        except Exception as e:
            logger.error(f"Yahoo Finance batch request failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {}
    
    def _get_alpha_vantage_batch_ohlc(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch OHLC data from Alpha Vantage (fallback)"""
        try:
            if not self.alpha_vantage_service:
                logger.warning("Alpha Vantage service not available")
                return {}
            
            logger.info(f"Fetching batch OHLC data for {len(tickers)} tickers from Alpha Vantage")
            
            # Alpha Vantage doesn't support true batch, so we'll process individually
            # but with proper rate limiting
            results = {}
            
            for i, ticker in enumerate(tickers):
                try:
                    # Rate limiting for Alpha Vantage
                    if i > 0:
                        time.sleep(0.2)  # 5 requests per second limit
                    
                    data = self.alpha_vantage_service.get_data(ticker)
                    if data and all(key in data for key in ['open', 'high', 'low', 'close']):
                        results[ticker] = data
                        logger.debug(f"✅ {ticker}: O={data['open']:.2f}, H={data['high']:.2f}, L={data['low']:.2f}, C={data['close']:.2f}")
                    else:
                        logger.warning(f"❌ {ticker}: Missing OHLC data from Alpha Vantage")
                        
                except Exception as e:
                    logger.error(f"Error processing {ticker} from Alpha Vantage: {e}")
                    continue
            
            logger.info(f"Alpha Vantage batch: {len(results)}/{len(tickers)} successful")
            return results
            
        except Exception as e:
            logger.error(f"Alpha Vantage batch request failed: {e}")
            return {}
    
    def _get_finnhub_batch_ohlc(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch OHLC data from Finnhub (fallback)"""
        try:
            if not self.finnhub_service:
                logger.warning("Finnhub service not available")
                return {}
            
            logger.info(f"Fetching batch OHLC data for {len(tickers)} tickers from Finnhub")
            
            # Finnhub doesn't support true batch, so we'll process individually
            results = {}
            
            for i, ticker in enumerate(tickers):
                try:
                    # Rate limiting for Finnhub
                    if i > 0:
                        time.sleep(0.1)  # 10 requests per second limit
                    
                    data = self.finnhub_service.get_data(ticker)
                    if data and all(key in data for key in ['open', 'high', 'low', 'close']):
                        results[ticker] = data
                        logger.debug(f"✅ {ticker}: O={data['open']:.2f}, H={data['high']:.2f}, L={data['low']:.2f}, C={data['close']:.2f}")
                    else:
                        logger.warning(f"❌ {ticker}: Missing OHLC data from Finnhub")
                        
                except Exception as e:
                    logger.error(f"Error processing {ticker} from Finnhub: {e}")
                    continue
            
            logger.info(f"Finnhub batch: {len(results)}/{len(tickers)} successful")
            return results
            
        except Exception as e:
            logger.error(f"Finnhub batch request failed: {e}")
            return {}
    
    def process_batch_ohlc(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Process OHLC data for multiple tickers using batch APIs where possible
        Prioritizes services that provide full OHLC data
        """
        if not tickers:
            logger.warning("No tickers provided for batch processing")
            return {}
        
        logger.info(f"Starting batch OHLC processing for {len(tickers)} tickers")
        
        # Try services in priority order until we get data
        for service_name, service_method in self.service_priority:
            try:
                logger.info(f"Trying {service_name} for batch OHLC data...")
                
                # Process in smaller batches to avoid overwhelming APIs
                all_results = {}
                
                for i in range(0, len(tickers), self.max_batch_size):
                    batch = tickers[i:i + self.max_batch_size]
                    logger.info(f"Processing batch {i//self.max_batch_size + 1}: {len(batch)} tickers")
                    
                    batch_results = service_method(batch)
                    all_results.update(batch_results)
                    
                    # Delay between batches
                    if i + self.max_batch_size < len(tickers):
                        time.sleep(self.delay_between_batches)
                
                if all_results:
                    logger.info(f"✅ {service_name} successful: {len(all_results)}/{len(tickers)} tickers")
                    return all_results
                else:
                    logger.warning(f"❌ {service_name} returned no data")
                    
            except Exception as e:
                logger.error(f"Error with {service_name}: {e}")
                continue
        
        logger.error("All services failed to provide batch OHLC data")
        return {}
    
    def store_daily_ohlc(self, ohlc_data: Dict[str, Dict]):
        """Store daily OHLC data in the database"""
        if not ohlc_data:
            logger.warning("No OHLC data to store")
            return
        
        start_time = time.time()
        logger.info(f"Storing {len(ohlc_data)} daily OHLC records...")
        
        try:
            # Prepare batch values
            batch_values = []
            today_str = date.today().strftime('%Y-%m-%d')
            
            for ticker, data in ohlc_data.items():
                try:
                    # Ensure we have all required OHLC fields
                    if all(key in data for key in ['open', 'high', 'low', 'close']):
                        # Convert to cents for database storage
                        batch_values.append((
                            ticker,
                            today_str,
                            int(round(data['open'] * 100)),
                            int(round(data['high'] * 100)),
                            int(round(data['low'] * 100)),
                            int(round(data['close'] * 100)),
                            data.get('volume', 0) or 0
                        ))
                    else:
                        logger.warning(f"Skipping {ticker}: Missing OHLC data")
                        
                except Exception as e:
                    logger.error(f"Error preparing OHLC data for {ticker}: {e}")
                    continue
            
            if not batch_values:
                logger.warning("No valid OHLC data to store after preparation")
                return
            
            logger.info(f"Prepared {len(batch_values)} records for batch insert")
            
            # Execute batch insert
            batch_query = """
                INSERT INTO daily_charts (
                    ticker, date, open, high, low, close, volume
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) 
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """
            
            successful_inserts = self.db.execute_batch(batch_query, batch_values)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Successfully stored {successful_inserts}/{len(ohlc_data)} daily OHLC records in {processing_time:.2f}s")
            
            # Verify data quality
            self._verify_ohlc_quality(ohlc_data)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error storing daily OHLC data after {processing_time:.2f}s: {e}")
            self.error_handler.handle_error(
                "Failed to store daily OHLC data", e, ErrorSeverity.HIGH
            )
    
    def _verify_ohlc_quality(self, ohlc_data: Dict[str, Dict]):
        """Verify that the stored OHLC data has proper variation"""
        try:
            # Check for any remaining identical OHLC values
            identical_count = 0
            total_count = len(ohlc_data)
            
            for ticker, data in ohlc_data.items():
                if (data.get('open') == data.get('high') == data.get('low') == data.get('close')):
                    identical_count += 1
                    logger.warning(f"⚠️  {ticker}: Still has identical OHLC values")
            
            if identical_count == 0:
                logger.info("🎉 All OHLC data has proper variation!")
            else:
                logger.warning(f"⚠️  {identical_count}/{total_count} tickers still have identical OHLC values")
                
        except Exception as e:
            logger.error(f"Error verifying OHLC quality: {e}")

def main():
    """Test the batch OHLC processor"""
    try:
        db = DatabaseManager()
        processor = BatchOHLCProcessor(db)
        
        # Test with a few tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
        
        logger.info("Testing batch OHLC processor...")
        ohlc_data = processor.process_batch_ohlc(test_tickers)
        
        if ohlc_data:
            logger.info(f"Test successful: {len(ohlc_data)} tickers processed")
            processor.store_daily_ohlc(ohlc_data)
        else:
            logger.error("Test failed: No OHLC data retrieved")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    main()
