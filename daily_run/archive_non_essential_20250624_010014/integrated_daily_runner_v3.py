"""
Integrated Daily Runner v3

Uses batch price processing (100 stocks per API call) and earnings-based 
fundamental updates. Stores daily prices in daily_charts table.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import SystemMonitor
from batch_price_processor import BatchPriceProcessor
from earnings_based_fundamental_processor import EarningsBasedFundamentalProcessor
from enhanced_service_factory import EnhancedServiceFactory

logger = logging.getLogger(__name__)


class IntegratedDailyRunnerV3:
    """
    Integrated daily runner that processes:
    1. Batch price updates (100 stocks per API call)
    2. Earnings-based fundamental updates
    3. Proper data storage in correct tables
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.db = DatabaseManager()
        self.error_handler = ErrorHandler()
        self.monitoring = SystemMonitor()
        
        # Initialize processors
        self.batch_price_processor = BatchPriceProcessor(
            db=self.db,
            max_batch_size=100,  # 100 stocks per API call
            max_workers=5,
            delay_between_batches=1.0
        )
        
        self.earnings_processor = EarningsBasedFundamentalProcessor(
            db=self.db,
            max_workers=5,
            earnings_window_days=7
        )
        
        # Initialize service factory
        self.service_factory = EnhancedServiceFactory()
        
        # Performance tracking
        self.start_time = None
        self.metrics = {}
    
    def run_daily_update(self, tickers: List[str] = None) -> Dict:
        """
        Run the complete daily update process.
        
        Args:
            tickers: List of ticker symbols to process. If None, gets all active tickers.
            
        Returns:
            Dictionary with processing results and metrics
        """
        self.start_time = time.time()
        logger.info("Starting Integrated Daily Runner v3")
        
        try:
            # Get tickers if not provided
            if not tickers:
                tickers = self._get_active_tickers()
            
            logger.info(f"Processing {len(tickers)} tickers")
            
            # Phase 1: Batch Price Processing
            price_results = self._process_batch_prices(tickers)
            
            # Phase 2: Earnings-Based Fundamental Updates
            fundamental_results = self._process_earnings_based_fundamentals(tickers)
            
            # Phase 3: Calculate Financial Ratios
            ratio_results = self._calculate_financial_ratios(tickers)
            
            # Phase 4: Update System Status
            self._update_system_status()
            
            # Compile results
            results = self._compile_results(
                tickers, price_results, fundamental_results, ratio_results
            )
            
            logger.info("Integrated Daily Runner v3 completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            self.error_handler.handle_error(
                "Daily update failed", e, ErrorSeverity.CRITICAL
            )
            return self._get_error_results(tickers, e)
    
    def _get_active_tickers(self) -> List[str]:
        """Get list of active tickers from database"""
        try:
            query = """
            SELECT ticker FROM stocks 
            WHERE is_active = true 
            ORDER BY ticker
            """
            results = self.db.fetch_all(query)
            return [row['ticker'] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting active tickers: {e}")
            # Fallback to common tickers
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
    
    def _process_batch_prices(self, tickers: List[str]) -> Dict:
        """
        Process batch prices using 100 stocks per API call.
        Stores results in daily_charts table.
        """
        logger.info("Phase 1: Processing batch prices")
        
        try:
            start_time = time.time()
            
            # Process batch prices
            price_data = self.batch_price_processor.process_batch_prices(tickers)
            
            processing_time = time.time() - start_time
            
            results = {
                'phase': 'batch_price_processing',
                'total_tickers': len(tickers),
                'successful_updates': len(price_data),
                'failed_updates': len(tickers) - len(price_data),
                'success_rate': len(price_data) / len(tickers) if tickers else 0,
                'processing_time': processing_time,
                'api_calls_made': (len(tickers) + 99) // 100,  # 100 per call
                'data_stored_in': 'daily_charts'
            }
            
            logger.info(f"Batch price processing completed: {results['successful_updates']}/{results['total_tickers']} successful")
            
            # Update monitoring
            self.monitoring.record_metric('batch_price_success_rate', results['success_rate'])
            self.monitoring.record_metric('batch_price_processing_time', processing_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch price processing failed: {e}")
            self.error_handler.handle_error(
                "Batch price processing failed", e, ErrorSeverity.HIGH
            )
            return {
                'phase': 'batch_price_processing',
                'error': str(e),
                'successful_updates': 0,
                'failed_updates': len(tickers)
            }
    
    def _process_earnings_based_fundamentals(self, tickers: List[str]) -> Dict:
        """
        Process fundamental updates based on earnings calendar.
        Only updates tickers with recent earnings.
        """
        logger.info("Phase 2: Processing earnings-based fundamentals")
        
        try:
            start_time = time.time()
            
            # Get earnings summary
            earnings_summary = self.earnings_processor.get_earnings_summary(tickers)
            
            # Process earnings-based updates
            update_results = self.earnings_processor.process_earnings_based_updates(tickers)
            
            processing_time = time.time() - start_time
            
            results = {
                'phase': 'earnings_based_fundamentals',
                'total_tickers': len(tickers),
                'candidates_found': update_results['candidates_found'],
                'successful_updates': update_results['successful_updates'],
                'failed_updates': update_results['failed_updates'],
                'success_rate': update_results['successful_updates'] / update_results['candidates_found'] if update_results['candidates_found'] > 0 else 0,
                'processing_time': processing_time,
                'earnings_summary': earnings_summary,
                'update_strategy': 'earnings_based_only'
            }
            
            logger.info(f"Earnings-based fundamentals completed: {results['successful_updates']}/{results['candidates_found']} successful")
            
            # Update monitoring
            self.monitoring.record_metric('earnings_based_success_rate', results['success_rate'])
            self.monitoring.record_metric('earnings_based_processing_time', processing_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Earnings-based fundamentals failed: {e}")
            self.error_handler.handle_error(
                "Earnings-based fundamentals failed", e, ErrorSeverity.HIGH
            )
            return {
                'phase': 'earnings_based_fundamentals',
                'error': str(e),
                'successful_updates': 0,
                'failed_updates': 0
            }
    
    def _calculate_financial_ratios(self, tickers: List[str]) -> Dict:
        """
        Calculate financial ratios for tickers with updated data.
        """
        logger.info("Phase 3: Calculating financial ratios")
        
        try:
            start_time = time.time()
            
            # Get tickers with recent price and fundamental data
            valid_tickers = self._get_tickers_with_recent_data(tickers)
            
            if not valid_tickers:
                logger.warning("No tickers with recent data for ratio calculation")
                return {
                    'phase': 'financial_ratios',
                    'total_tickers': len(tickers),
                    'valid_tickers': 0,
                    'successful_calculations': 0,
                    'processing_time': 0
                }
            
            # Calculate ratios for valid tickers
            successful_calculations = 0
            
            for ticker in valid_tickers:
                try:
                    if self._calculate_single_ticker_ratios(ticker):
                        successful_calculations += 1
                except Exception as e:
                    logger.warning(f"Failed to calculate ratios for {ticker}: {e}")
            
            processing_time = time.time() - start_time
            
            results = {
                'phase': 'financial_ratios',
                'total_tickers': len(tickers),
                'valid_tickers': len(valid_tickers),
                'successful_calculations': successful_calculations,
                'success_rate': successful_calculations / len(valid_tickers) if valid_tickers else 0,
                'processing_time': processing_time
            }
            
            logger.info(f"Financial ratios completed: {results['successful_calculations']}/{results['valid_tickers']} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Financial ratios calculation failed: {e}")
            self.error_handler.handle_error(
                "Financial ratios calculation failed", e, ErrorSeverity.MEDIUM
            )
            return {
                'phase': 'financial_ratios',
                'error': str(e),
                'successful_calculations': 0
            }
    
    def _get_tickers_with_recent_data(self, tickers: List[str]) -> List[str]:
        """Get tickers that have recent price and fundamental data"""
        try:
            valid_tickers = []
            today = date.today()
            
            for ticker in tickers:
                # Check for recent daily price
                latest_price = self.batch_price_processor.get_latest_daily_price(ticker)
                if not latest_price or latest_price['date'] != today:
                    continue
                
                # Check for recent fundamental data
                fundamental_data = self._get_latest_fundamental_data(ticker)
                if not fundamental_data:
                    continue
                
                valid_tickers.append(ticker)
            
            return valid_tickers
            
        except Exception as e:
            logger.error(f"Error getting tickers with recent data: {e}")
            return []
    
    def _get_latest_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """Get latest fundamental data for a ticker"""
        try:
            query = """
            SELECT * FROM company_fundamentals 
            WHERE ticker = %s 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            return self.db.fetch_one(query, (ticker,))
            
        except Exception as e:
            logger.error(f"Error getting fundamental data for {ticker}: {e}")
            return None
    
    def _calculate_single_ticker_ratios(self, ticker: str) -> bool:
        """Calculate financial ratios for a single ticker"""
        try:
            # Get latest price and fundamental data
            latest_price = self.batch_price_processor.get_latest_daily_price(ticker)
            fundamental_data = self._get_latest_fundamental_data(ticker)
            
            if not latest_price or not fundamental_data:
                return False
            
            # Extract data
            close_price = latest_price['close_price']
            revenue = fundamental_data.get('revenue')
            net_income = fundamental_data.get('net_income')
            shareholders_equity = fundamental_data.get('shareholders_equity')
            total_assets = fundamental_data.get('total_assets')
            
            # Calculate ratios
            ratios = {}
            
            # P/E Ratio
            if net_income and net_income > 0:
                market_cap = close_price * fundamental_data.get('shares_outstanding', 0)
                ratios['pe_ratio'] = market_cap / net_income if market_cap > 0 else None
            
            # P/B Ratio
            if shareholders_equity and shareholders_equity > 0:
                market_cap = close_price * fundamental_data.get('shares_outstanding', 0)
                ratios['pb_ratio'] = market_cap / shareholders_equity if market_cap > 0 else None
            
            # ROE
            if shareholders_equity and shareholders_equity > 0 and net_income:
                ratios['roe'] = net_income / shareholders_equity
            
            # ROA
            if total_assets and total_assets > 0 and net_income:
                ratios['roa'] = net_income / total_assets
            
            # Store ratios
            if ratios:
                self._store_financial_ratios(ticker, ratios)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error calculating ratios for {ticker}: {e}")
            return False
    
    def _store_financial_ratios(self, ticker: str, ratios: Dict):
        """Store financial ratios in database"""
        try:
            query = """
            INSERT INTO financial_ratios (
                ticker, pe_ratio, pb_ratio, roe, roa, calculated_at
            ) VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (ticker) 
            DO UPDATE SET
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                roe = EXCLUDED.roe,
                roa = EXCLUDED.roa,
                updated_at = NOW()
            """
            
            values = (
                ticker,
                ratios.get('pe_ratio'),
                ratios.get('pb_ratio'),
                ratios.get('roe'),
                ratios.get('roa')
            )
            
            self.db.execute(query, values)
            
        except Exception as e:
            logger.error(f"Error storing ratios for {ticker}: {e}")
    
    def _update_system_status(self):
        """Update system status and health metrics"""
        try:
            # Update system status
            status = {
                'last_run': datetime.now(),
                'status': 'completed',
                'version': 'v3',
                'features': [
                    'batch_price_processing_100_per_call',
                    'earnings_based_fundamentals',
                    'daily_charts_storage',
                    'financial_ratios_calculation'
                ]
            }
            
            # Store status
            query = """
            INSERT INTO system_status (
                status_data, created_at
            ) VALUES (%s, NOW())
            """
            
            self.db.execute(query, (json.dumps(status),))
            
            # Update monitoring
            self.monitoring.record_metric('system_last_run', datetime.now())
            self.monitoring.record_metric('system_status', 'healthy')
            
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
    
    def _compile_results(self, tickers: List[str], price_results: Dict, 
                        fundamental_results: Dict, ratio_results: Dict) -> Dict:
        """Compile final results from all phases"""
        total_time = time.time() - self.start_time
        
        results = {
            'version': 'v3',
            'timestamp': datetime.now(),
            'total_tickers': len(tickers),
            'total_processing_time': total_time,
            'phases': {
                'batch_price_processing': price_results,
                'earnings_based_fundamentals': fundamental_results,
                'financial_ratios': ratio_results
            },
            'summary': {
                'price_success_rate': price_results.get('success_rate', 0),
                'fundamental_success_rate': fundamental_results.get('success_rate', 0),
                'ratio_success_rate': ratio_results.get('success_rate', 0),
                'total_api_calls': price_results.get('api_calls_made', 0),
                'earnings_based_updates': fundamental_results.get('candidates_found', 0)
            },
            'data_storage': {
                'daily_prices': 'daily_charts table',
                'fundamentals': 'company_fundamentals table',
                'ratios': 'financial_ratios table'
            }
        }
        
        return results
    
    def _get_error_results(self, tickers: List[str], error: Exception) -> Dict:
        """Get error results when processing fails"""
        return {
            'version': 'v3',
            'timestamp': datetime.now(),
            'status': 'error',
            'error': str(error),
            'total_tickers': len(tickers) if tickers else 0,
            'total_processing_time': time.time() - self.start_time if self.start_time else 0
        }
    
    def get_system_health(self) -> Dict:
        """Get system health status"""
        try:
            health = {
                'database': self._check_database_health(),
                'services': self._check_service_health(),
                'data_quality': self._check_data_quality(),
                'last_run': self._get_last_run_status()
            }
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {'error': str(e)}
    
    def _check_database_health(self) -> Dict:
        """Check database health"""
        try:
            # Test database connection
            test_query = "SELECT 1"
            self.db.execute(test_query)
            
            return {'status': 'healthy', 'connection': 'ok'}
            
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def _check_service_health(self) -> Dict:
        """Check service health"""
        try:
            services = ['yahoo_finance', 'alpha_vantage', 'finnhub']
            health_status = {}
            
            for service in services:
                try:
                    # Test service availability
                    service_instance = self.service_factory.get_service(service)
                    health_status[service] = {'status': 'healthy'}
                except Exception as e:
                    health_status[service] = {'status': 'unhealthy', 'error': str(e)}
            
            return health_status
            
        except Exception as e:
            return {'error': str(e)}
    
    def _check_data_quality(self) -> Dict:
        """Check data quality metrics"""
        try:
            # Check recent data availability
            today = date.today()
            
            # Daily prices
            price_query = "SELECT COUNT(*) as count FROM daily_charts WHERE date = %s"
            price_count = self.db.fetch_one(price_query, (today,))['count']
            
            # Fundamentals
            fundamental_query = "SELECT COUNT(*) as count FROM company_fundamentals WHERE DATE(created_at) = %s"
            fundamental_count = self.db.fetch_one(fundamental_query, (today,))['count']
            
            return {
                'daily_prices_today': price_count,
                'fundamentals_today': fundamental_count,
                'data_freshness': 'good' if price_count > 0 else 'poor'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_last_run_status(self) -> Dict:
        """Get last run status"""
        try:
            query = """
            SELECT status_data, created_at 
            FROM system_status 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            result = self.db.fetch_one(query)
            
            if result:
                status_data = json.loads(result['status_data'])
                return {
                    'last_run': result['created_at'],
                    'status': status_data.get('status'),
                    'version': status_data.get('version')
                }
            
            return {'last_run': None, 'status': 'unknown'}
            
        except Exception as e:
            return {'error': str(e)}


def main():
    """Test the integrated daily runner v3"""
    logging.basicConfig(level=logging.INFO)
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
    
    # Initialize runner
    runner = IntegratedDailyRunnerV3()
    
    try:
        # Run daily update
        results = runner.run_daily_update(test_tickers)
        
        print(f"\nDaily Update Results:")
        print(f"Version: {results['version']}")
        print(f"Total tickers: {results['total_tickers']}")
        print(f"Processing time: {results['total_processing_time']:.2f}s")
        
        print(f"\nPhase Results:")
        for phase, phase_results in results['phases'].items():
            print(f"{phase}: {phase_results.get('successful_updates', 0)} successful")
        
        print(f"\nSummary:")
        summary = results['summary']
        print(f"Price success rate: {summary['price_success_rate']:.2%}")
        print(f"Fundamental success rate: {summary['fundamental_success_rate']:.2%}")
        print(f"Ratio success rate: {summary['ratio_success_rate']:.2%}")
        print(f"Total API calls: {summary['total_api_calls']}")
        print(f"Earnings-based updates: {summary['earnings_based_updates']}")
        
        # Get system health
        health = runner.get_system_health()
        print(f"\nSystem Health:")
        print(f"Database: {health['database']['status']}")
        print(f"Data quality: {health['data_quality'].get('data_freshness', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        runner.db.close()


if __name__ == "__main__":
    main() 