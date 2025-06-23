#!/usr/bin/env python3
"""
Batch Processing System
Provides efficient batch processing capabilities for multiple tickers
"""

import asyncio
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from common_imports import time, setup_logging
from error_handler import ErrorHandler, performance_monitor, retry_on_error

@dataclass
class BatchResult:
    """Result of batch processing operation"""
    successful: List[str]
    failed: List[str]
    errors: Dict[str, str]
    total_processed: int
    total_successful: int
    total_failed: int
    processing_time: float
    start_time: datetime
    end_time: datetime

class BatchProcessor:
    """Efficient batch processor for multiple tickers"""
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10, 
                 delay_between_batches: float = 1.0):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.error_handler = ErrorHandler("batch_processor")
        self.logger = logging.getLogger("batch_processor")
        
    @performance_monitor
    def process_batch(self, tickers: List[str], 
                     processor_func: Callable[[str], Any],
                     service_name: str = "unknown") -> BatchResult:
        """Process a batch of tickers using the provided function"""
        start_time = datetime.now()
        successful = []
        failed = []
        errors = {}
        
        self.logger.info(f"Starting batch processing for {len(tickers)} tickers using {service_name}")
        
        # Split tickers into batches
        batches = [tickers[i:i + self.batch_size] 
                  for i in range(0, len(tickers), self.batch_size)]
        
        for batch_num, batch in enumerate(batches):
            self.logger.info(f"Processing batch {batch_num + 1}/{len(batches)} with {len(batch)} tickers")
            
            # Process batch with thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks in the batch
                future_to_ticker = {
                    executor.submit(self._process_single_ticker, ticker, processor_func): ticker 
                    for ticker in batch
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        result = future.result()
                        if result is not None:
                            successful.append(ticker)
                        else:
                            failed.append(ticker)
                            errors[ticker] = "No data returned"
                    except Exception as e:
                        failed.append(ticker)
                        errors[ticker] = str(e)
                        self.error_handler.handle_error(e, {'ticker': ticker, 'service': service_name})
            
            # Delay between batches to avoid rate limiting
            if batch_num < len(batches) - 1:
                time.sleep(self.delay_between_batches)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result = BatchResult(
            successful=successful,
            failed=failed,
            errors=errors,
            total_processed=len(tickers),
            total_successful=len(successful),
            total_failed=len(failed),
            processing_time=processing_time,
            start_time=start_time,
            end_time=end_time
        )
        
        self.logger.info(f"Batch processing completed: {result.total_successful}/{result.total_processed} "
                        f"successful in {processing_time:.2f}s")
        
        return result
    
    @retry_on_error(max_retries=2, delay=0.5)
    def _process_single_ticker(self, ticker: str, processor_func: Callable[[str], Any]) -> Any:
        """Process a single ticker with retry logic"""
        try:
            return processor_func(ticker)
        except Exception as e:
            self.logger.warning(f"Error processing {ticker}: {e}")
            raise
    
    def process_with_fallback(self, tickers: List[str], 
                            primary_func: Callable[[str], Any],
                            fallback_func: Callable[[str], Any],
                            service_name: str = "unknown") -> BatchResult:
        """Process tickers with fallback to secondary function for failed ones"""
        # First attempt with primary function
        primary_result = self.process_batch(tickers, primary_func, f"{service_name}_primary")
        
        # If there are failures, try with fallback
        if primary_result.failed:
            self.logger.info(f"Retrying {len(primary_result.failed)} failed tickers with fallback")
            fallback_result = self.process_batch(primary_result.failed, fallback_func, f"{service_name}_fallback")
            
            # Combine results
            combined_successful = primary_result.successful + fallback_result.successful
            combined_failed = fallback_result.failed
            combined_errors = {**primary_result.errors, **fallback_result.errors}
            
            return BatchResult(
                successful=combined_successful,
                failed=combined_failed,
                errors=combined_errors,
                total_processed=primary_result.total_processed,
                total_successful=len(combined_successful),
                total_failed=len(combined_failed),
                processing_time=primary_result.processing_time + fallback_result.processing_time,
                start_time=primary_result.start_time,
                end_time=fallback_result.end_time
            )
        
        return primary_result
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'max_workers': self.max_workers,
            'batch_size': self.batch_size,
            'delay_between_batches': self.delay_between_batches,
            'error_summary': self.error_handler.get_error_summary()
        }

class AsyncBatchProcessor:
    """Asynchronous batch processor for better performance"""
    
    def __init__(self, max_concurrent: int = 10, batch_size: int = 20):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.error_handler = ErrorHandler("async_batch_processor")
        self.logger = logging.getLogger("async_batch_processor")
    
    async def process_batch_async(self, tickers: List[str], 
                                processor_func: Callable[[str], Any],
                                service_name: str = "unknown") -> BatchResult:
        """Process batch asynchronously"""
        start_time = datetime.now()
        successful = []
        failed = []
        errors = {}
        
        self.logger.info(f"Starting async batch processing for {len(tickers)} tickers")
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create tasks for all tickers
        tasks = [
            self._process_single_async(ticker, processor_func, semaphore)
            for ticker in tickers
        ]
        
        # Process all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            ticker = tickers[i]
            if isinstance(result, Exception):
                failed.append(ticker)
                errors[ticker] = str(result)
                self.error_handler.handle_error(result, {'ticker': ticker, 'service': service_name})
            elif result is not None:
                successful.append(ticker)
            else:
                failed.append(ticker)
                errors[ticker] = "No data returned"
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result = BatchResult(
            successful=successful,
            failed=failed,
            errors=errors,
            total_processed=len(tickers),
            total_successful=len(successful),
            total_failed=len(failed),
            processing_time=processing_time,
            start_time=start_time,
            end_time=end_time
        )
        
        self.logger.info(f"Async batch processing completed: {result.total_successful}/{result.total_processed} "
                        f"successful in {processing_time:.2f}s")
        
        return result
    
    async def _process_single_async(self, ticker: str, processor_func: Callable[[str], Any], 
                                  semaphore: asyncio.Semaphore) -> Any:
        """Process a single ticker asynchronously"""
        async with semaphore:
            try:
                # Run the processor function in a thread pool since most APIs are synchronous
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, processor_func, ticker)
            except Exception as e:
                self.logger.warning(f"Error processing {ticker}: {e}")
                raise

def create_batch_processor(max_workers: int = 5, batch_size: int = 10, 
                         use_async: bool = False) -> BatchProcessor | AsyncBatchProcessor:
    """Factory function to create appropriate batch processor"""
    if use_async:
        return AsyncBatchProcessor(max_concurrent=max_workers, batch_size=batch_size)
    else:
        return BatchProcessor(max_workers=max_workers, batch_size=batch_size)

# Example usage functions
def example_batch_processing():
    """Example of how to use the batch processor"""
    processor = BatchProcessor(max_workers=3, batch_size=5)
    
    # Example processor function
    def process_ticker(ticker: str) -> Dict[str, Any]:
        # Simulate API call
        time.sleep(0.1)
        if ticker == "FAIL":
            raise Exception("Simulated failure")
        return {"ticker": ticker, "data": "processed"}
    
    # Test tickers
    test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "FAIL", "TSLA", "NVDA", "META"]
    
    # Process batch
    result = processor.process_batch(test_tickers, process_ticker, "example_service")
    
    print(f"Processing completed:")
    print(f"  Successful: {result.total_successful}/{result.total_processed}")
    print(f"  Failed: {result.total_failed}")
    print(f"  Time: {result.processing_time:.2f}s")
    print(f"  Errors: {result.errors}")

if __name__ == "__main__":
    setup_logging("batch_processor")
    example_batch_processing() 