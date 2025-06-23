#!/usr/bin/env python3
"""
Update fundamental data daily for tickers that need updates
"""

import os
import psycopg2
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Import existing services (local imports)
from multi_service_fundamentals import MultiServiceFundamentals
from earnings_calendar_service import EarningsCalendarService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/update_fundamentals_daily.log'),
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

class DailyFundamentalsUpdater:
    """Update fundamental data daily for tickers that need updates"""
    
    def __init__(self):
        """Initialize services and database connection"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.fundamentals_service = MultiServiceFundamentals()
        self.earnings_service = EarningsCalendarService()
        self.today = date.today()
        
    def get_tickers_needing_updates(self, max_tickers: int = 50) -> List[Dict]:
        """Get tickers that need fundamental updates, prioritized by:
        1. Upcoming earnings (within 7 days)
        2. Missing fundamental data
        3. Stale data (older than 30 days)
        4. Low priority updates (older than 7 days)
        """
        try:
            self.cur.execute("""
                SELECT 
                    s.ticker,
                    f.last_updated,
                    f.next_earnings_date,
                    f.next_update_priority,
                    CASE 
                        WHEN f.next_earnings_date IS NOT NULL 
                             AND f.next_earnings_date BETWEEN %s AND %s THEN 1
                        WHEN f.revenue_ttm IS NULL OR f.market_cap IS NULL THEN 2
                        WHEN f.last_updated IS NULL OR f.last_updated < %s THEN 3
                        WHEN f.last_updated < %s THEN 4
                        ELSE 5
                    END as priority_score
                FROM stocks s
                LEFT JOIN financials f ON s.ticker = f.ticker
                WHERE s.is_active = true
                ORDER BY priority_score ASC, f.next_update_priority ASC, s.ticker
                LIMIT %s
            """, (
                self.today, 
                self.today + timedelta(days=7),
                self.today - timedelta(days=30),
                self.today - timedelta(days=7),
                max_tickers
            ))
            
            results = []
            for row in self.cur.fetchall():
                results.append({
                    'ticker': row[0],
                    'last_updated': row[1],
                    'next_earnings_date': row[2],
                    'next_update_priority': row[3],
                    'priority_score': row[4]
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Error getting tickers needing updates: {e}")
            return []
    
    def update_earnings_calendar(self, ticker: str) -> bool:
        """Update earnings calendar data for a ticker"""
        try:
            earnings_data = self.earnings_service.get_earnings_calendar(ticker)
            if earnings_data and len(earnings_data) > 0:
                next_earnings = earnings_data[0]  # Most recent upcoming earnings
                
                self.cur.execute("""
                    UPDATE financials 
                    SET 
                        next_earnings_date = %s,
                        earnings_time = %s,
                        eps_estimate = %s,
                        revenue_estimate = %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE ticker = %s
                """, (
                    next_earnings.get('date'),
                    next_earnings.get('time'),
                    next_earnings.get('eps_estimate'),
                    next_earnings.get('revenue_estimate'),
                    ticker
                ))
                
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error updating earnings calendar for {ticker}: {e}")
            return False
    
    def update_fundamental_data(self, ticker: str) -> bool:
        """Update fundamental data for a ticker"""
        try:
            # Get fundamental data from multiple services
            fundamental_data = self.fundamentals_service.get_fundamental_data(ticker)
            
            if not fundamental_data:
                logging.warning(f"No fundamental data retrieved for {ticker}")
                return False
            
            # Update financials table
            self.cur.execute("""
                INSERT INTO financials (
                    ticker, market_cap, shares_outstanding, current_price,
                    revenue_ttm, gross_profit_ttm, operating_income_ttm, net_income_ttm,
                    ebitda_ttm, diluted_eps_ttm, book_value_per_share,
                    total_assets, total_debt, shareholders_equity, cash_and_equivalents,
                    current_assets, current_liabilities, operating_cash_flow_ttm,
                    free_cash_flow_ttm, capex_ttm, data_source, last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                ) ON CONFLICT (ticker) DO UPDATE SET
                    market_cap = EXCLUDED.market_cap,
                    shares_outstanding = EXCLUDED.shares_outstanding,
                    current_price = EXCLUDED.current_price,
                    revenue_ttm = EXCLUDED.revenue_ttm,
                    gross_profit_ttm = EXCLUDED.gross_profit_ttm,
                    operating_income_ttm = EXCLUDED.operating_income_ttm,
                    net_income_ttm = EXCLUDED.net_income_ttm,
                    ebitda_ttm = EXCLUDED.ebitda_ttm,
                    diluted_eps_ttm = EXCLUDED.diluted_eps_ttm,
                    book_value_per_share = EXCLUDED.book_value_per_share,
                    total_assets = EXCLUDED.total_assets,
                    total_debt = EXCLUDED.total_debt,
                    shareholders_equity = EXCLUDED.shareholders_equity,
                    cash_and_equivalents = EXCLUDED.cash_and_equivalents,
                    current_assets = EXCLUDED.current_assets,
                    current_liabilities = EXCLUDED.current_liabilities,
                    operating_cash_flow_ttm = EXCLUDED.operating_cash_flow_ttm,
                    free_cash_flow_ttm = EXCLUDED.free_cash_flow_ttm,
                    capex_ttm = EXCLUDED.capex_ttm,
                    data_source = EXCLUDED.data_source,
                    last_updated = CURRENT_TIMESTAMP
            """, (
                ticker,
                fundamental_data.get('market_cap'),
                fundamental_data.get('shares_outstanding'),
                fundamental_data.get('current_price'),
                fundamental_data.get('revenue_ttm'),
                fundamental_data.get('gross_profit_ttm'),
                fundamental_data.get('operating_income_ttm'),
                fundamental_data.get('net_income_ttm'),
                fundamental_data.get('ebitda_ttm'),
                fundamental_data.get('diluted_eps_ttm'),
                fundamental_data.get('book_value_per_share'),
                fundamental_data.get('total_assets'),
                fundamental_data.get('total_debt'),
                fundamental_data.get('shareholders_equity'),
                fundamental_data.get('cash_and_equivalents'),
                fundamental_data.get('current_assets'),
                fundamental_data.get('current_liabilities'),
                fundamental_data.get('operating_cash_flow_ttm'),
                fundamental_data.get('free_cash_flow_ttm'),
                fundamental_data.get('capex_ttm'),
                fundamental_data.get('data_source', 'multi_service')
            ))
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating fundamental data for {ticker}: {e}")
            return False
    
    def log_update(self, ticker: str, update_type: str, status: str, execution_time_ms: int, error_message: str = None):
        """Log update to update_log table"""
        try:
            self.cur.execute("""
                INSERT INTO update_log (
                    ticker, update_type, status, execution_time_ms, error_message, started_at, completed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                ticker, update_type, status, execution_time_ms, error_message,
                datetime.now(), datetime.now()
            ))
        except Exception as e:
            logging.error(f"Error logging update for {ticker}: {e}")
    
    def run_daily_update(self, max_tickers: int = 50):
        """Run daily fundamental updates"""
        start_time = datetime.now()
        logging.info("🚀 Starting daily fundamental updates...")
        
        tickers = self.get_tickers_needing_updates(max_tickers)
        logging.info(f"📊 Found {len(tickers)} tickers needing updates")
        
        successful = 0
        failed = 0
        
        for ticker_info in tickers:
            ticker = ticker_info['ticker']
            ticker_start_time = datetime.now()
            
            try:
                logging.info(f"🔄 Processing {ticker} (priority: {ticker_info['priority_score']})")
                
                # Update earnings calendar if needed
                if ticker_info['next_earnings_date'] is None:
                    self.update_earnings_calendar(ticker)
                
                # Update fundamental data
                if self.update_fundamental_data(ticker):
                    ticker_execution_time = int((datetime.now() - ticker_start_time).total_seconds() * 1000)
                    self.log_update(ticker, 'fundamentals', 'success', ticker_execution_time)
                    
                    logging.info(f"✅ {ticker}: Fundamentals updated successfully")
                    successful += 1
                else:
                    self.log_update(ticker, 'fundamentals', 'failed', 0, 'No data retrieved')
                    logging.warning(f"⚠️  {ticker}: Failed to update fundamentals")
                    failed += 1
                    
            except Exception as e:
                logging.error(f"❌ Error processing {ticker}: {e}")
                self.log_update(ticker, 'fundamentals', 'failed', 0, str(e))
                failed += 1
        
        total_execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        logging.info(f"🎉 Daily fundamental updates completed!")
        logging.info(f"   ✅ Successful: {successful}")
        logging.info(f"   ❌ Failed: {failed}")
        logging.info(f"   ⏱️  Total execution time: {total_execution_time}ms")
        
        # Log overall update
        self.cur.execute("""
            INSERT INTO update_log (
                ticker, update_type, status, records_updated, execution_time_ms, started_at, completed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            None, 'daily_fundamentals', 'success', successful, total_execution_time,
            start_time, datetime.now()
        ))
        
        self.conn.commit()
    
    def close(self):
        """Close database connections"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def main():
    """Main function"""
    updater = DailyFundamentalsUpdater()
    try:
        updater.run_daily_update()
    finally:
        updater.close()

if __name__ == "__main__":
    main() 