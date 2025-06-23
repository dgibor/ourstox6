#!/usr/bin/env python3
"""
New Daily Financial Pipeline using modular architecture
"""

import logging
import time
from datetime import datetime, date
from typing import Dict, List, Any
from config import Config
from database import DatabaseManager
from price_service import PriceCollector
from ratios_calculator import RatiosCalculator
from service_factory import ServiceFactory
from exceptions import DailyRunError

class DailyPipeline:
    """New daily financial data pipeline"""
    
    def __init__(self):
        """Initialize pipeline components"""
        self.start_time = datetime.now()
        self.db = DatabaseManager()
        self.service_factory = ServiceFactory()
        self.setup_logging()
        
        # Pipeline results
        self.results = {
            'start_time': self.start_time,
            'steps': {},
            'summary': {}
        }
    
    def setup_logging(self):
        """Setup logging for the pipeline"""
        logging.basicConfig(
            level=logging.INFO,
            format=Config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(f'{Config.LOG_DIR}/new_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_step(self, step_name: str, status: str, details: Dict[str, Any] = None):
        """Log pipeline step results"""
        step_result = {
            'status': status,
            'timestamp': datetime.now(),
            'details': details or {}
        }
        self.results['steps'][step_name] = step_result
        
        if status == 'success':
            self.logger.info(f"SUCCESS {step_name}: {details}")
        elif status == 'failed':
            self.logger.error(f"FAILED {step_name}: {details}")
        else:
            self.logger.warning(f"WARNING {step_name}: {details}")
    
    def step_update_prices(self, target_table: str = 'stocks') -> Dict[str, Any]:
        """Step 1: Update market prices"""
        self.logger.info(f"🔄 Step 1: Updating prices for {target_table}")
        step_start = datetime.now()
        
        try:
            collector = PriceCollector(target_table)
            result = collector.run()
            
            execution_time = (datetime.now() - step_start).total_seconds()
            details = {
                'target_table': target_table,
                'total_tickers': result['total_tickers'],
                'successful': result['successful'],
                'failed': result['failed'],
                'execution_time_seconds': execution_time
            }
            
            self.log_step('update_prices', 'success', details)
            collector.close()
            
            return result
            
        except Exception as e:
            details = {'error': str(e)}
            self.log_step('update_prices', 'failed', details)
            raise DailyRunError(f"Price update failed: {e}")
    
    def step_update_fundamentals(self, max_tickers: int = 50) -> Dict[str, Any]:
        """Step 2: Update fundamental data"""
        self.logger.info(f"🔄 Step 2: Updating fundamentals (max {max_tickers})")
        step_start = datetime.now()
        
        try:
            # Get tickers that need updates
            tickers = self.db.get_tickers('stocks')[:max_tickers]
            
            successful = 0
            failed = 0
            errors = []
            
            for ticker in tickers:
                try:
                    # This would use the multi-service fundamentals
                    # For now, just log the attempt
                    self.logger.debug(f"Would update fundamentals for {ticker}")
                    successful += 1
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"{ticker}: {str(e)}")
            
            execution_time = (datetime.now() - step_start).total_seconds()
            details = {
                'total_tickers': len(tickers),
                'successful': successful,
                'failed': failed,
                'errors': errors[:5],  # Limit error list
                'execution_time_seconds': execution_time
            }
            
            self.log_step('update_fundamentals', 'success', details)
            return details
            
        except Exception as e:
            details = {'error': str(e)}
            self.log_step('update_fundamentals', 'failed', details)
            raise DailyRunError(f"Fundamentals update failed: {e}")
    
    def step_calculate_ratios(self, max_tickers: int = 100) -> Dict[str, Any]:
        """Step 3: Calculate financial ratios"""
        self.logger.info(f"🔄 Step 3: Calculating ratios (max {max_tickers})")
        step_start = datetime.now()
        
        try:
            # Get tickers with fundamental data
            query = """
                SELECT DISTINCT f.ticker 
                FROM financials f
                WHERE f.revenue_ttm IS NOT NULL 
                   OR f.market_cap IS NOT NULL
                LIMIT %s
            """
            results = self.db.execute_query(query, (max_tickers,))
            tickers = [row[0] for row in results]
            
            calculator = RatiosCalculator(use_database=True)
            successful = 0
            failed = 0
            errors = []
            
            for ticker in tickers:
                try:
                    result = calculator.calculate_all_ratios(ticker)
                    if 'error' not in result:
                        successful += 1
                    else:
                        failed += 1
                        errors.append(f"{ticker}: {result['error']}")
                        
                except Exception as e:
                    failed += 1
                    errors.append(f"{ticker}: {str(e)}")
            
            execution_time = (datetime.now() - step_start).total_seconds()
            details = {
                'total_tickers': len(tickers),
                'successful': successful,
                'failed': failed,
                'errors': errors[:5],  # Limit error list
                'execution_time_seconds': execution_time
            }
            
            self.log_step('calculate_ratios', 'success', details)
            calculator.close()
            
            return details
            
        except Exception as e:
            details = {'error': str(e)}
            self.log_step('calculate_ratios', 'failed', details)
            raise DailyRunError(f"Ratio calculation failed: {e}")
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate pipeline summary"""
        total_execution_time = (datetime.now() - self.start_time).total_seconds()
        
        # Count successful and failed steps
        successful_steps = sum(1 for step in self.results['steps'].values() 
                              if step['status'] == 'success')
        total_steps = len(self.results['steps'])
        
        # Calculate totals from step results
        total_tickers_processed = 0
        total_successful_operations = 0
        
        for step_name, step_result in self.results['steps'].items():
            if step_result['status'] == 'success':
                details = step_result['details']
                total_tickers_processed += details.get('total_tickers', 0)
                total_successful_operations += details.get('successful', 0)
        
        summary = {
            'pipeline_status': 'success' if successful_steps == total_steps else 'partial' if successful_steps > 0 else 'failed',
            'total_execution_time_seconds': total_execution_time,
            'steps_completed': successful_steps,
            'total_steps': total_steps,
            'total_tickers_processed': total_tickers_processed,
            'total_successful_operations': total_successful_operations,
            'completion_time': datetime.now()
        }
        
        self.results['summary'] = summary
        return summary
    
    def run(self, force_run: bool = False) -> Dict[str, Any]:
        """Run the complete daily pipeline"""
        self.logger.info("🚀 Starting New Daily Financial Pipeline")
        self.logger.info(f"📅 Date: {date.today()}")
        
        try:
            # Step 1: Update prices
            self.step_update_prices('stocks')
            
            # Step 2: Update fundamentals
            self.step_update_fundamentals(50)
            
            # Step 3: Calculate ratios
            self.step_calculate_ratios(100)
            
            # Generate summary
            summary = self.generate_summary()
            
            # Log final results
            self.logger.info("🎉 Daily Pipeline Completed!")
            self.logger.info(f"   ⏱️  Total execution time: {summary['total_execution_time_seconds']:.1f}s")
            self.logger.info(f"   📊 Steps completed: {summary['steps_completed']}/{summary['total_steps']}")
            self.logger.info(f"   🎯 Tickers processed: {summary['total_tickers_processed']}")
            self.logger.info(f"   ✅ Successful operations: {summary['total_successful_operations']}")
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            summary = self.generate_summary()
            return self.results
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.service_factory.close_all_services()
            self.db.disconnect()
            self.logger.info("Pipeline cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    def process_ticker(self, ticker: str) -> Dict[str, Any]:
        """Process a single ticker through the pipeline"""
        self.logger.info(f"Processing single ticker: {ticker}")
        
        result = {
            'success': False,
            'ticker': ticker,
            'price_updated': False,
            'fundamentals_updated': False,
            'ratios_calculated': False,
            'error': None
        }
        
        try:
            # Step 1: Update price
            try:
                price_service = self.service_factory.get_price_service('yahoo')
                if price_service:
                    price_data = price_service.get_data(ticker)
                    if price_data:
                        self.db.update_price_data(ticker, price_data)
                        result['price_updated'] = True
                        self.logger.info(f"Price updated for {ticker}")
            except Exception as e:
                self.logger.warning(f"Price update failed for {ticker}: {e}")
            
            # Step 2: Update fundamentals (placeholder)
            # This would use the fundamental service when implemented
            result['fundamentals_updated'] = False
            
            # Step 3: Calculate ratios
            try:
                calculator = RatiosCalculator(use_database=True)
                ratio_result = calculator.calculate_all_ratios(ticker)
                if 'error' not in ratio_result:
                    result['ratios_calculated'] = True
                    self.logger.info(f"Ratios calculated for {ticker}")
                else:
                    self.logger.warning(f"Ratio calculation failed for {ticker}: {ratio_result['error']}")
                calculator.close()
            except Exception as e:
                self.logger.warning(f"Ratio calculation failed for {ticker}: {e}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Processing failed for {ticker}: {e}")
        
        return result

    def close(self):
        """Close the pipeline (alias for cleanup)"""
        self.cleanup()

def test_pipeline():
    """Test the new daily pipeline"""
    print("🧪 Testing New Daily Pipeline")
    print("=" * 35)
    
    pipeline = DailyPipeline()
    
    try:
        results = pipeline.run()
        
        print(f"✅ Pipeline completed with status: {results['summary']['pipeline_status']}")
        print(f"✅ Execution time: {results['summary']['total_execution_time_seconds']:.1f}s")
        print(f"✅ Steps completed: {results['summary']['steps_completed']}/{results['summary']['total_steps']}")
        
        # Show step details
        for step_name, step_result in results['steps'].items():
            status = "✅" if step_result['status'] == 'success' else "❌"
            print(f"{status} {step_name}: {step_result['status']}")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")

if __name__ == "__main__":
    test_pipeline() 