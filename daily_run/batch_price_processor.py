"""
Batch Price Processor

Handles batch price processing for up to 100 stocks per API call
and stores daily prices in the daily_charts table.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import collections
import traceback

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor

logger = logging.getLogger(__name__)

# Setup file logging for batch price processor
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'batch_price_processor.log')

# Add file handler if not already present
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(log_file) for h in logger.handlers):
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


class BatchPriceProcessor:
    """
    Processes price data for multiple tickers in batches of up to 100 per API call.
    Stores daily prices in the daily_charts table.
    """
    
    def __init__(self, db: DatabaseManager, max_batch_size: int = 100, 
                 max_workers: int = 5, delay_between_batches: float = 1.0):
        self.db = db
        self.max_batch_size = max_batch_size
        self.max_workers = max_workers
        self.delay_between_batches = delay_between_batches
        self.error_handler = ErrorHandler("batch_price_processor")
        self.monitoring = SystemMonitor()
        
        # Initialize services
        try:
            self.yahoo_service = YahooFinanceService()
        except:
            self.yahoo_service = None
            logger.warning("Yahoo Finance service not available")
            
        try:
            self.alpha_vantage_service = AlphaVantageService()
        except:
            self.alpha_vantage_service = None
            logger.warning("Alpha Vantage service not available")
            
        try:
            self.finnhub_service = FinnhubService()
        except:
            self.finnhub_service = None
            logger.warning("Finnhub service not available")
        
        # Initialize FMP service (preferred for batch operations)
        try:
            from fmp_service import FMPService
            self.fmp_service = FMPService()
            # Ensure it has required attributes
            if not hasattr(self.fmp_service, 'base_url'):
                self.fmp_service.base_url = "https://financialmodelingprep.com/api/v3"
            if not hasattr(self.fmp_service, 'api_key'):
                self.fmp_service.api_key = os.getenv('FMP_API_KEY')
            logger.info("FMP service initialized for batch processing")
        except Exception as e:
            logger.warning(f"FMP service not available: {e}")
            self.fmp_service = None
        
        # Service priority for pricing data (FMP first as requested)
        self.service_priority = [
            ('FMP', self._get_fmp_batch_prices),
            ('Alpha Vantage', self._get_alpha_vantage_batch_prices),
            ('Yahoo Finance', self._get_yahoo_batch_prices),
            ('Finnhub', self._get_finnhub_batch_prices)
        ]
    
    def process_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Process prices for multiple tickers using batch API calls.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to price data
        """
        start_time = time.time()
        logger.info(f"Starting batch price processing for {len(tickers)} tickers")
        
        results = {}
        total_batches = (len(tickers) + self.max_batch_size - 1) // self.max_batch_size
        
        # Track which service succeeded for each batch
        self._service_success_counter = collections.Counter()
        self._service_failure_counter = collections.Counter()
        self._service_last_error = {}
        
        try:
            # Split tickers into batches
            batches = [
                tickers[i:i + self.max_batch_size] 
                for i in range(0, len(tickers), self.max_batch_size)
            ]
            
            # Process batches with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_batch = {
                    executor.submit(self._process_single_batch, batch, batch_num): batch
                    for batch_num, batch in enumerate(batches, 1)
                }
                
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    batch_num = batches.index(batch) + 1
                    
                    try:
                        batch_results = future.result()
                        results.update(batch_results)
                        logger.info(f"Completed batch {batch_num}/{total_batches} with {len(batch_results)} results")
                        
                        # Rate limiting between batches
                        if batch_num < total_batches:
                            time.sleep(self.delay_between_batches)
                            
                    except Exception as e:
                        logger.error(f"Error processing batch {batch_num}: {e}")
                        self.error_handler.handle_error(
                            f"Batch processing failed for batch {batch_num}", e, ErrorSeverity.HIGH
                        )
            
            # Store results in daily_charts table
            if results:
                self.store_daily_prices(results)
            
            processing_time = time.time() - start_time
            logger.info(f"Batch price processing completed in {processing_time:.2f}s")
            logger.info(f"Successfully processed {len(results)}/{len(tickers)} tickers")
            
            # Update monitoring metrics
            self.monitoring.record_metric(
                'batch_price_processing_time', processing_time
            )
            self.monitoring.record_metric(
                'batch_price_success_rate', len(results) / len(tickers) if tickers else 0
            )
            
            # Log service summary
            logger.info(f"[SUMMARY] Service success counts: {dict(self._service_success_counter)}")
            logger.info(f"[SUMMARY] Service failure counts: {dict(self._service_failure_counter)}")
            for service, err in self._service_last_error.items():
                logger.info(f"[SUMMARY] Last error for {service}: {err}")
            return results
            
        except Exception as e:
            logger.error(f"Batch price processing failed: {e}")
            self.error_handler.handle_error(
                "Batch price processing failed", e, ErrorSeverity.CRITICAL
            )
            return {}
    
    def _process_single_batch(self, tickers: List[str], batch_num: int) -> Dict[str, Dict]:
        """
        Process a single batch of tickers using fallback services.
        Logs service order, attempts, and fallbacks for transparency.
        Yahoo Finance gets 3 retries before falling back to next service.
        Args:
            tickers: List of ticker symbols for this batch
            batch_num: Batch number for logging
        Returns:
            Dictionary mapping ticker to price data
        """
        logger.info(f"Batch {batch_num}: Service order: {[s[0] for s in self.service_priority]}")
        logger.info(f"Batch {batch_num}: Processing {len(tickers)} tickers")
        
        for service_name, service_func in self.service_priority:
            try:
                logger.info(f"Batch {batch_num}: Trying {service_name}")
                
                # Special handling for Yahoo Finance - retry 3 times
                if service_name == 'Yahoo Finance':
                    max_retries = 3
                    for attempt in range(1, max_retries + 1):
                        try:
                            logger.info(f"Batch {batch_num}: Yahoo Finance attempt {attempt}/{max_retries}")
                            results = service_func(tickers)
                            if results:
                                logger.info(f"Batch {batch_num}: Yahoo Finance succeeded on attempt {attempt} for {len(results)} tickers")
                                self._service_success_counter[service_name] += 1
                                return results
                            else:
                                logger.warning(f"Batch {batch_num}: Yahoo Finance returned no results on attempt {attempt}")
                                if attempt < max_retries:
                                    time.sleep(1)  # Wait 1 second between retries
                                    continue
                                else:
                                    logger.warning(f"Batch {batch_num}: Yahoo Finance failed all {max_retries} attempts, falling back")
                                    self._service_failure_counter[service_name] += 1
                                    self._service_last_error[service_name] = 'No results after 3 attempts.'
                        except Exception as e:
                            logger.warning(f"Batch {batch_num}: Yahoo Finance attempt {attempt} failed with error: {e}")
                            import traceback
                            logger.warning(f"Batch {batch_num}: Yahoo Finance traceback: {traceback.format_exc()}")
                            if attempt < max_retries:
                                time.sleep(1)  # Wait 1 second between retries
                                continue
                            else:
                                logger.warning(f"Batch {batch_num}: Yahoo Finance failed all {max_retries} attempts, falling back to next service")
                                self._service_failure_counter[service_name] += 1
                                self._service_last_error[service_name] = str(e)
                                break
                else:
                    # Other services get one attempt
                    try:
                        results = service_func(tickers)
                        if results:
                            logger.info(f"Batch {batch_num}: {service_name} succeeded for {len(results)} tickers")
                            self._service_success_counter[service_name] += 1
                            return results
                        else:
                            logger.warning(f"Batch {batch_num}: {service_name} returned no results, falling back")
                            self._service_failure_counter[service_name] += 1
                            self._service_last_error[service_name] = 'No results.'
                            logger.warning(f"Batch {batch_num}: {service_name} full response: {results}")
                    except Exception as e:
                        logger.warning(f"Batch {batch_num}: {service_name} failed with error: {e}. Falling back to next service.")
                        import traceback
                        logger.warning(f"Batch {batch_num}: {service_name} traceback: {traceback.format_exc()}")
                        self._service_failure_counter[service_name] += 1
                        self._service_last_error[service_name] = str(e)
                        continue
            except Exception as e:
                logger.warning(f"Batch {batch_num}: {service_name} failed with error: {e}. Falling back to next service.")
                import traceback
                logger.warning(f"Batch {batch_num}: {service_name} traceback: {traceback.format_exc()}")
                self._service_failure_counter[service_name] += 1
                self._service_last_error[service_name] = str(e)
                continue
                
        logger.error(f"Batch {batch_num}: All services failed for this batch. No price data available.")
        return {}
    
    def _get_fmp_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch prices from FMP (up to 100 symbols per call)"""
        try:
            if not self.fmp_service:
                logger.warning("FMP service not available, skipping batch")
                return {}
            
            # Small delay for FMP to be safe
            time.sleep(0.5)
            
            logger.info(f"[FMP DEBUG] Requesting batch quotes for: {tickers}")
            response = self.fmp_service.fetch_batch_quotes(tickers)
            logger.info(f"[FMP DEBUG] Raw response: {str(response)[:500]}")
            results = self._parse_fmp_batch_response(response, tickers)
            if not results:
                logger.warning(f"[FMP DEBUG] No results returned for tickers: {tickers}")
            return results
        except Exception as e:
            logger.error(f"[FMP DEBUG] FMP batch request failed: {str(e)}")
            logger.error(f"[FMP DEBUG] Full traceback: {traceback.format_exc()}")
            return {}

    def _get_yahoo_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch prices from Yahoo Finance"""
        try:
            if not self.yahoo_service:
                logger.warning("Yahoo service not available, skipping batch")
                return {}
            
            # Reduced delay since Yahoo is no longer primary
            time.sleep(1)
            
            logger.info(f"[YAHOO DEBUG] Requesting batch quotes for: {tickers}")
            results = self.yahoo_service.get_batch_data(tickers, 'pricing')
            logger.info(f"[YAHOO DEBUG] Raw response: {str(results)[:500]}")
            if not results:
                logger.warning(f"[YAHOO DEBUG] No results returned for tickers: {tickers}")
            return results
        except Exception as e:
            logger.error(f"[YAHOO DEBUG] Yahoo batch request failed: {str(e)}")
            logger.error(f"[YAHOO DEBUG] Full traceback: {traceback.format_exc()}")
            return {}

    def _get_alpha_vantage_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch prices from Alpha Vantage"""
        try:
            if not self.alpha_vantage_service:
                logger.warning("Alpha Vantage service not available, skipping batch")
                return {}
            
            # Alpha Vantage doesn't support batch quotes, so process one at a time
            results = {}
            for ticker in tickers:
                try:
                    url = f"{self.alpha_vantage_service.base_url}/query"
                    params = {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': ticker,
                        'apikey': self.alpha_vantage_service.api_key
                    }
                    logger.info(f"[ALPHA VANTAGE DEBUG] Requesting single quote for {ticker}")
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parse individual response
                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        results[ticker] = {
                            'price': float(quote.get('05. price', 0)),
                            'volume': int(quote.get('06. volume', 0)),
                            'change': float(quote.get('09. change', 0)),
                            'change_percent': quote.get('10. change percent', '').replace('%', ''),
                            'data_source': 'alpha_vantage'
                        }
                    time.sleep(0.2)  # Rate limiting
                except Exception as e:
                    logger.error(f"[ALPHA VANTAGE DEBUG] Error for {ticker}: {e}")
                    continue
            
            logger.info(f"[ALPHA VANTAGE DEBUG] Collected {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Alpha Vantage batch request failed: {e}")
            import traceback
            logger.error(f"[ALPHA VANTAGE DEBUG] Traceback: {traceback.format_exc()}")
            raise

    def _get_finnhub_batch_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get batch prices from Finnhub"""
        try:
            if not self.finnhub_service:
                logger.warning("Finnhub service not available, skipping batch")
                return {}
            results = {}
            with ThreadPoolExecutor(max_workers=min(5, len(tickers))) as executor:
                future_to_ticker = {
                    executor.submit(self._get_single_finnhub_price_with_delay, ticker): ticker 
                    for ticker in tickers
                }
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        data = future.result()
                        if data:
                            results[ticker] = data
                    except Exception as e:
                        logger.error(f"Error getting Finnhub data for {ticker}: {e}")
            return results
        except Exception as e:
            logger.error(f"Finnhub batch request failed: {e}")
            raise

    def _get_single_finnhub_price(self, ticker: str) -> Optional[Dict]:
        """Get single ticker price from Finnhub"""
        try:
            url = f"{self.finnhub_service.base_url}/api/v1/quote"
            params = {
                'symbol': ticker,
                'token': self.finnhub_service.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get('c'):  # Current price exists
                return {
                    'close_price': data.get('c'),
                    'volume': None,  # Finnhub quote doesn't include volume
                    'change': data.get('d'),
                    'change_percent': data.get('dp'),
                    'data_source': 'finnhub',
                    'timestamp': datetime.now()
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting Finnhub price for {ticker}: {e}")
            return None

    def _get_single_finnhub_price_with_delay(self, ticker: str) -> Optional[Dict]:
        """Get single ticker price from Finnhub with delay to avoid rate limit"""
        time.sleep(1)  # 1 second delay per request
        return self._get_single_finnhub_price(ticker)
    
    def _parse_fmp_batch_response(self, response: List[Dict], tickers: List[str]) -> Dict[str, Dict]:
        """Parse FMP batch response"""
        results = {}
        
        try:
            if isinstance(response, list):
                for quote in response:
                    symbol = quote.get('symbol')
                    if symbol in tickers:
                        results[symbol] = {
                            'close_price': quote.get('price'),
                            'volume': quote.get('volume'),
                            'market_cap': quote.get('marketCap'),
                            'change': quote.get('change'),
                            'change_percent': quote.get('changesPercentage'),
                            'data_source': 'fmp',
                            'timestamp': datetime.now()
                        }
            
        except Exception as e:
            logger.error(f"Error parsing FMP response: {e}")
        
        return results
    
    def _parse_yahoo_batch_response(self, response: Dict, tickers: List[str]) -> Dict[str, Dict]:
        """Parse Yahoo Finance batch response"""
        results = {}
        
        try:
            quote_response = response.get('quoteResponse', {})
            quotes = quote_response.get('result', [])
            
            for quote in quotes:
                symbol = quote.get('symbol')
                if symbol in tickers:
                    results[symbol] = {
                        'close_price': quote.get('regularMarketPrice'),
                        'volume': quote.get('regularMarketVolume'),
                        'market_cap': quote.get('marketCap'),
                        'change': quote.get('regularMarketChange'),
                        'change_percent': quote.get('regularMarketChangePercent'),
                        'data_source': 'yahoo_finance',
                        'timestamp': datetime.now()
                    }
            
        except Exception as e:
            logger.error(f"Error parsing Yahoo Finance response: {e}")
        
        return results
    
    def _parse_alpha_vantage_batch_response(self, response: Dict, tickers: List[str]) -> Dict[str, Dict]:
        """Parse Alpha Vantage batch response"""
        results = {}
        
        try:
            quotes = response.get('Stock Quotes', [])
            
            for quote in quotes:
                symbol = quote.get('1. symbol')
                if symbol in tickers:
                    results[symbol] = {
                        'close_price': safe_get_numeric(quote, '2. price'),
                        'volume': safe_get_numeric(quote, '3. volume'),
                        'change': safe_get_numeric(quote, '4. change'),
                        'change_percent': quote.get('5. change percent', '0%'),
                        'data_source': 'alpha_vantage',
                        'timestamp': datetime.now()
                    }
            
        except Exception as e:
            logger.error(f"Error parsing Alpha Vantage response: {e}")
        
        return results
    
    def store_daily_prices(self, price_data: Dict[str, Dict]):
        """
        Store daily prices in the daily_charts table using efficient batch insert.
        Args:
            price_data: Dictionary mapping ticker to price data
        """
        if not price_data:
            logger.warning("No price data to store")
            return
            
        logger.info(f"Storing {len(price_data)} daily price records")
        start_time = time.time()
        
        try:
            today_str = date.today().strftime('%Y-%m-%d')
            
            # Prepare batch data for insertion
            batch_values = []
            successful_prep = 0
            
            for ticker, data in price_data.items():
                # Handle different field names from different services
                close_val = data.get('close') or data.get('close_price') or data.get('price')
                if close_val:
                    try:
                        close_val = float(close_val)
                        # For now, use close price for all OHLC since we only have close from batch APIs
                        open_val = float(data.get('open', close_val))
                        high_val = float(data.get('high', close_val))
                        low_val = float(data.get('low', close_val))
                        volume = data.get('volume', 0) or 0
                        
                        batch_values.append((
                            ticker,
                            today_str,  # Use string format to match VARCHAR column
                            open_val,
                            high_val,
                            low_val,
                            close_val,
                            volume
                        ))
                        successful_prep += 1
                    except Exception as e:
                        logger.error(f"Error preparing price data for {ticker}: {e}")
                        continue
            
            if not batch_values:
                logger.warning("No valid price data to store after preparation")
                return
            
            logger.info(f"Prepared {successful_prep} records for batch insert")
            
            # Execute batch insert using executemany for efficiency
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
            
            # Use batch insert method from database manager
            successful_inserts = self.db.execute_batch(batch_query, batch_values)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Successfully stored {successful_inserts}/{len(price_data)} daily price records in {processing_time:.2f}s")
            self.monitoring.record_metric('daily_prices_stored', successful_inserts)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error storing daily prices after {processing_time:.2f}s: {e}")
            self.error_handler.handle_error(
                "Failed to store daily prices", e, ErrorSeverity.HIGH
            )

    def get_latest_daily_price(self, ticker: str) -> Optional[Dict]:
        """
        Get the latest daily price from daily_charts table.
        Args:
            ticker: Ticker symbol
        Returns:
            Latest price data or None
        """
        try:
            query = """
            SELECT ticker, date, close, volume
            FROM daily_charts 
            WHERE ticker = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            result = self.db.fetch_one(query, (ticker,))
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting latest daily price for {ticker}: {e}")
            return None

    def get_daily_prices_for_date(self, tickers: List[str], target_date: date) -> Dict[str, Dict]:
        """
        Get daily prices for specific tickers on a specific date.
        Args:
            tickers: List of ticker symbols
            target_date: Target date
        Returns:
            Dictionary mapping ticker to price data
        """
        try:
            placeholders = ','.join(['%s'] * len(tickers))
            query = f"""
            SELECT ticker, date, close, volume
            FROM daily_charts 
            WHERE ticker IN ({placeholders}) AND date = %s
            """
            params = tickers + [target_date]
            results = self.db.execute_query(query, params)
            return {row[0]: {
                'ticker': row[0],
                'date': row[1], 
                'close': row[2],
                'volume': row[3]
            } for row in results}
        except Exception as e:
            logger.error(f"Error getting daily prices for date {target_date}: {e}")
            return {}


def main():
    """Test the batch price processor"""
    logging.basicConfig(level=logging.INFO)
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    # Initialize database and processor
    db = DatabaseManager()
    processor = BatchPriceProcessor(db)
    
    try:
        # Process batch prices
        results = processor.process_batch_prices(test_tickers)
        
        print(f"\nResults: {len(results)} tickers processed")
        for ticker, data in results.items():
            print(f"{ticker}: ${data.get('close_price', 'N/A')}")
        
        # Get latest prices from database
        print("\nLatest prices from database:")
        for ticker in test_tickers:
            latest = processor.get_latest_daily_price(ticker)
            if latest:
                print(f"{ticker}: ${latest.get('close_price', 'N/A')} on {latest.get('date')}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        db.disconnect()


if __name__ == "__main__":
    main() 