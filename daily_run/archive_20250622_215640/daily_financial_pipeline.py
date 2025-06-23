#!/usr/bin/env python3
"""
Daily Financial Data Pipeline
Orchestrates the complete daily update process for financial data
"""

import os
import logging
import psycopg2
from datetime import datetime, date
from dotenv import load_dotenv

# Import our daily update modules (local imports)
from update_fundamentals_daily import DailyFundamentalsUpdater
from calculate_daily_ratios import DailyRatioCalculator
from get_market_prices import get_market_prices
from check_market_schedule import is_market_open

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_pipeline.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

class DailyFinancialPipeline:
    """Main pipeline for daily financial data updates"""
    
    def __init__(self):
        """Initialize pipeline components"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.today = date.today()
        self.pipeline_start_time = datetime.now()
        
    def log_pipeline_start(self):
        """Log pipeline start"""
        try:
            self.cur.execute("""
                INSERT INTO update_log (
                    ticker, update_type, status, started_at
                ) VALUES (%s, %s, %s, %s)
            """, (None, 'daily_pipeline', 'started', self.pipeline_start_time))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error logging pipeline start: {e}")
    
    def log_pipeline_completion(self, status: str, total_execution_time: int, summary: Dict):
        """Log pipeline completion"""
        try:
            self.cur.execute("""
                UPDATE update_log 
                SET 
                    status = %s,
                    records_updated = %s,
                    execution_time_ms = %s,
                    completed_at = %s
                WHERE update_type = 'daily_pipeline' 
                  AND started_at = %s
            """, (
                status,
                summary.get('total_updated', 0),
                total_execution_time,
                datetime.now(),
                self.pipeline_start_time
            ))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error logging pipeline completion: {e}")
    
    def check_market_status(self) -> bool:
        """Check if market is open and if we should run updates"""
        try:
            market_open = is_market_open()
            logging.info(f"📈 Market status: {'Open' if market_open else 'Closed'}")
            return market_open
        except Exception as e:
            logging.error(f"Error checking market status: {e}")
            return False
    
    def update_market_prices(self) -> Dict:
        """Update market prices for all active tickers"""
        logging.info("🔄 Step 1: Updating market prices...")
        start_time = datetime.now()
        
        try:
            # Get all active tickers
            self.cur.execute("SELECT ticker FROM stocks WHERE is_active = true")
            tickers = [row[0] for row in self.cur.fetchall()]
            
            # Update prices
            updated_count = get_market_prices(tickers)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logging.info(f"✅ Market prices updated: {updated_count} tickers in {execution_time}ms")
            
            return {
                'step': 'market_prices',
                'status': 'success',
                'updated_count': updated_count,
                'execution_time_ms': execution_time
            }
            
        except Exception as e:
            logging.error(f"❌ Error updating market prices: {e}")
            return {
                'step': 'market_prices',
                'status': 'failed',
                'error': str(e),
                'execution_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    def update_fundamentals(self, max_tickers: int = 50) -> Dict:
        """Update fundamental data for tickers that need updates"""
        logging.info("🔄 Step 2: Updating fundamental data...")
        start_time = datetime.now()
        
        try:
            updater = DailyFundamentalsUpdater()
            updater.run_daily_update(max_tickers)
            updater.close()
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Get update statistics
            self.cur.execute("""
                SELECT COUNT(*) FROM update_log 
                WHERE update_type = 'fundamentals' 
                  AND DATE(started_at) = %s 
                  AND status = 'success'
            """, (self.today,))
            successful = self.cur.fetchone()[0]
            
            self.cur.execute("""
                SELECT COUNT(*) FROM update_log 
                WHERE update_type = 'fundamentals' 
                  AND DATE(started_at) = %s 
                  AND status = 'failed'
            """, (self.today,))
            failed = self.cur.fetchone()[0]
            
            logging.info(f"✅ Fundamentals updated: {successful} successful, {failed} failed in {execution_time}ms")
            
            return {
                'step': 'fundamentals',
                'status': 'success',
                'successful': successful,
                'failed': failed,
                'execution_time_ms': execution_time
            }
            
        except Exception as e:
            logging.error(f"❌ Error updating fundamentals: {e}")
            return {
                'step': 'fundamentals',
                'status': 'failed',
                'error': str(e),
                'execution_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    def calculate_ratios(self) -> Dict:
        """Calculate daily ratios for all tickers"""
        logging.info("🔄 Step 3: Calculating daily ratios...")
        start_time = datetime.now()
        
        try:
            calculator = DailyRatioCalculator()
            calculator.run_daily_calculation()
            calculator.close()
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Get calculation statistics
            self.cur.execute("""
                SELECT COUNT(*) FROM update_log 
                WHERE update_type = 'ratios' 
                  AND DATE(started_at) = %s 
                  AND status = 'success'
            """, (self.today,))
            successful = self.cur.fetchone()[0]
            
            self.cur.execute("""
                SELECT COUNT(*) FROM update_log 
                WHERE update_type = 'ratios' 
                  AND DATE(started_at) = %s 
                  AND status = 'failed'
            """, (self.today,))
            failed = self.cur.fetchone()[0]
            
            logging.info(f"✅ Ratios calculated: {successful} successful, {failed} failed in {execution_time}ms")
            
            return {
                'step': 'ratios',
                'status': 'success',
                'successful': successful,
                'failed': failed,
                'execution_time_ms': execution_time
            }
            
        except Exception as e:
            logging.error(f"❌ Error calculating ratios: {e}")
            return {
                'step': 'ratios',
                'status': 'failed',
                'error': str(e),
                'execution_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    def generate_daily_summary(self) -> Dict:
        """Generate daily summary statistics"""
        try:
            # Get total tickers with ratios
            self.cur.execute("SELECT COUNT(*) FROM current_ratios")
            total_with_ratios = self.cur.fetchone()[0]
            
            # Get tickers with recent updates
            self.cur.execute("""
                SELECT COUNT(*) FROM financials 
                WHERE DATE(last_updated) = %s
            """, (self.today,))
            updated_today = self.cur.fetchone()[0]
            
            # Get average data quality
            self.cur.execute("""
                SELECT AVG(data_quality_score) FROM current_ratios 
                WHERE data_quality_score IS NOT NULL
            """)
            avg_quality = self.cur.fetchone()[0]
            
            # Get top value stocks (low P/E, P/B, P/S)
            self.cur.execute("""
                SELECT ticker, pe_ratio, pb_ratio, ps_ratio 
                FROM current_ratios 
                WHERE pe_ratio IS NOT NULL 
                  AND pb_ratio IS NOT NULL 
                  AND ps_ratio IS NOT NULL
                  AND pe_ratio > 0 
                  AND pb_ratio > 0 
                  AND ps_ratio > 0
                ORDER BY (pe_ratio + pb_ratio + ps_ratio) ASC 
                LIMIT 10
            """)
            top_value_stocks = self.cur.fetchall()
            
            return {
                'total_with_ratios': total_with_ratios,
                'updated_today': updated_today,
                'avg_data_quality': round(avg_quality, 1) if avg_quality else 0,
                'top_value_stocks': [
                    {'ticker': row[0], 'pe': row[1], 'pb': row[2], 'ps': row[3]} 
                    for row in top_value_stocks
                ]
            }
            
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return {}
    
    def run_pipeline(self, force_run: bool = False):
        """Run the complete daily pipeline"""
        logging.info("🚀 Starting Daily Financial Pipeline...")
        logging.info(f"📅 Date: {self.today}")
        
        self.log_pipeline_start()
        
        # Check if market is open (unless forced)
        if not force_run and not self.check_market_status():
            logging.info("📈 Market is closed. Skipping price updates.")
            market_open = False
        else:
            market_open = True
        
        pipeline_results = []
        
        # Step 1: Update market prices (only if market is open)
        if market_open:
            price_result = self.update_market_prices()
            pipeline_results.append(price_result)
        else:
            pipeline_results.append({
                'step': 'market_prices',
                'status': 'skipped',
                'reason': 'Market closed'
            })
        
        # Step 2: Update fundamentals
        fundamental_result = self.update_fundamentals()
        pipeline_results.append(fundamental_result)
        
        # Step 3: Calculate ratios
        ratio_result = self.calculate_ratios()
        pipeline_results.append(ratio_result)
        
        # Generate summary
        summary = self.generate_daily_summary()
        
        # Log completion
        total_execution_time = int((datetime.now() - self.pipeline_start_time).total_seconds() * 1000)
        
        # Determine overall status
        failed_steps = [r for r in pipeline_results if r.get('status') == 'failed']
        overall_status = 'failed' if failed_steps else 'success'
        
        self.log_pipeline_completion(overall_status, total_execution_time, summary)
        
        # Log final summary
        logging.info("🎉 Daily Pipeline Completed!")
        logging.info(f"   ⏱️  Total execution time: {total_execution_time}ms")
        logging.info(f"   📊 Tickers with ratios: {summary.get('total_with_ratios', 0)}")
        logging.info(f"   🔄 Updated today: {summary.get('updated_today', 0)}")
        logging.info(f"   📈 Average data quality: {summary.get('avg_data_quality', 0)}%")
        
        if summary.get('top_value_stocks'):
            logging.info("🏆 Top Value Stocks:")
            for stock in summary['top_value_stocks'][:5]:
                logging.info(f"   {stock['ticker']}: P/E={stock['pe']:.2f}, P/B={stock['pb']:.2f}, P/S={stock['ps']:.2f}")
        
        if failed_steps:
            logging.warning("⚠️  Failed steps:")
            for step in failed_steps:
                logging.warning(f"   {step['step']}: {step.get('error', 'Unknown error')}")
        
        return {
            'status': overall_status,
            'execution_time_ms': total_execution_time,
            'results': pipeline_results,
            'summary': summary
        }
    
    def close(self):
        """Close database connections"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def main():
    """Main function"""
    import sys
    
    # Check for force run argument
    force_run = '--force' in sys.argv
    
    pipeline = DailyFinancialPipeline()
    try:
        result = pipeline.run_pipeline(force_run=force_run)
        if result['status'] == 'success':
            logging.info("✅ Pipeline completed successfully!")
            return 0
        else:
            logging.error("❌ Pipeline completed with errors!")
            return 1
    finally:
        pipeline.close()

if __name__ == "__main__":
    exit(main()) 