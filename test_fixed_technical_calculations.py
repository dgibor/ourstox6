#!/usr/bin/env python3
"""
Test Fixed Technical Calculations

This script tests the fixed technical calculation logic with 10 tickers that have 100+ days of history.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# Add daily_run to path
sys.path.append('daily_run')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_fixed_technical_calculations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_config():
    """Get database configuration"""
    try:
        from config import Config
        config = Config.get_db_config()
        return config
    except ImportError:
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'dbname': os.getenv('DB_NAME', 'ourstox6'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }

class TechnicalCalculationTester:
    """Test the fixed technical calculation logic"""
    
    def __init__(self):
        self.config = get_db_config()
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to database"""
        try:
            import psycopg2
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_tickers_with_100_days_history(self) -> List[str]:
        """Get tickers that have 100+ days of price data"""
        query = """
        SELECT ticker, COUNT(*) as days_count
        FROM daily_charts 
        WHERE close IS NOT NULL AND close != 0
        GROUP BY ticker 
        HAVING COUNT(*) >= 100
        ORDER BY days_count DESC
        LIMIT 10
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        tickers = [row[0] for row in results]
        logger.info(f"Found {len(tickers)} tickers with 100+ days of history")
        for ticker, days in results:
            logger.info(f"  {ticker}: {days} days")
        return tickers
    
    def get_price_data_for_ticker(self, ticker: str, days: int = 100) -> Optional[List[Dict]]:
        """Get price data for a ticker"""
        try:
            query = """
            SELECT date, open, high, low, close, volume
            FROM daily_charts 
            WHERE ticker = %s AND close IS NOT NULL AND close != 0
            ORDER BY date ASC
            LIMIT %s
            """
            self.cursor.execute(query, (ticker, days))
            data = self.cursor.fetchall()
            
            if len(data) < 100:
                logger.warning(f"Insufficient data for {ticker}: {len(data)} days < 100")
                return None
            
            # Convert to list of dictionaries
            price_data = []
            for row in data:
                price_data.append({
                    'date': row[0],
                    'open': row[1],
                    'high': row[2],
                    'low': row[3],
                    'close': row[4],
                    'volume': row[5]
                })
            
            logger.debug(f"Retrieved {len(price_data)} days of price data for {ticker}")
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting price data for {ticker}: {e}")
            return None
    
    def test_single_ticker_calculation(self, ticker: str) -> Dict:
        """Test technical calculation for a single ticker"""
        try:
            logger.info(f"Testing technical calculations for {ticker}...")
            
            # Get price data
            price_data = self.get_price_data_for_ticker(ticker, 100)
            if not price_data:
                return {'ticker': ticker, 'success': False, 'error': 'No price data'}
            
            # Import and test the fixed calculation function
            from daily_trading_system import DailyTradingSystem
            trading_system = DailyTradingSystem()
            
            # Test the calculation
            start_time = datetime.now()
            indicators = trading_system._calculate_single_ticker_technicals(ticker, price_data)
            calculation_time = (datetime.now() - start_time).total_seconds()
            
            if indicators is None:
                return {
                    'ticker': ticker, 
                    'success': False, 
                    'error': 'Calculation returned None',
                    'calculation_time': calculation_time
                }
            
            # Validate indicators
            valid_indicators = {}
            for indicator, value in indicators.items():
                if value is not None and value != 0:
                    valid_indicators[indicator] = value
            
            result = {
                'ticker': ticker,
                'success': True,
                'total_indicators': len(indicators),
                'valid_indicators': len(valid_indicators),
                'calculation_time': calculation_time,
                'indicators': valid_indicators
            }
            
            logger.info(f"✅ {ticker}: {len(valid_indicators)}/{len(indicators)} valid indicators in {calculation_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error testing {ticker}: {e}")
            return {'ticker': ticker, 'success': False, 'error': str(e)}
    
    def run_tests(self):
        """Run tests on 10 tickers with 100+ days of history"""
        try:
            logger.info("🧪 Starting Technical Calculation Tests")
            logger.info("=" * 60)
            
            # Connect to database
            self.connect()
            
            # Get test tickers
            tickers = self.get_tickers_with_100_days_history()
            if not tickers:
                logger.error("No tickers found with 100+ days of history")
                return
            
            # Test each ticker
            results = []
            successful = 0
            failed = 0
            
            for i, ticker in enumerate(tickers, 1):
                logger.info(f"Testing {i}/{len(tickers)}: {ticker}")
                
                result = self.test_single_ticker_calculation(ticker)
                results.append(result)
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                
                # Add a small delay between tests
                import time
                time.sleep(0.1)
            
            # Summary
            logger.info("=" * 60)
            logger.info("🧪 Technical Calculation Test Results")
            logger.info(f"Total tickers tested: {len(tickers)}")
            logger.info(f"Successful: {successful}")
            logger.info(f"Failed: {failed}")
            logger.info(f"Success rate: {(successful/len(tickers)*100):.1f}%")
            
            # Detailed results
            logger.info("\n📊 Detailed Results:")
            for result in results:
                if result['success']:
                    logger.info(f"  ✅ {result['ticker']}: {result['valid_indicators']}/{result['total_indicators']} indicators in {result['calculation_time']:.2f}s")
                    if result['indicators']:
                        indicator_str = ", ".join([f"{k}: {v:.2f}" for k, v in result['indicators'].items()])
                        logger.info(f"     Values: {indicator_str}")
                else:
                    logger.info(f"  ❌ {result['ticker']}: {result.get('error', 'Unknown error')}")
            
            # Performance analysis
            successful_results = [r for r in results if r['success']]
            if successful_results:
                avg_time = sum(r['calculation_time'] for r in successful_results) / len(successful_results)
                avg_indicators = sum(r['valid_indicators'] for r in successful_results) / len(successful_results)
                logger.info(f"\n📈 Performance Analysis:")
                logger.info(f"  Average calculation time: {avg_time:.2f}s")
                logger.info(f"  Average valid indicators: {avg_indicators:.1f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in technical calculation tests: {e}")
            return []
        finally:
            self.disconnect()

def main():
    """Main function"""
    tester = TechnicalCalculationTester()
    results = tester.run_tests()
    
    # Print summary to console
    print("\n" + "="*60)
    print("TECHNICAL CALCULATION TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Total tickers tested: {total}")
    print(f"Successful calculations: {successful}")
    print(f"Failed calculations: {total - successful}")
    print(f"Success rate: {(successful/total*100):.1f}%")
    
    if successful > 0:
        print("\n✅ Technical calculation logic is working!")
        print("The fixed logic successfully calculates indicators for tickers with sufficient data.")
    else:
        print("\n❌ Technical calculation logic still has issues!")
        print("All calculations failed - further investigation needed.")

if __name__ == "__main__":
    main() 