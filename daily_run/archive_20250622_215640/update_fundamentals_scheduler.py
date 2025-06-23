import os
import time
import logging
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
from typing import List, Dict
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utility_functions.api_rate_limiter import APIRateLimiter
from daily_run.yahoo_finance_service import YahooFinanceService
from daily_run.finnhub_service import FinnhubService
from daily_run.alpha_vantage_service import AlphaVantageService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/update_fundamentals_scheduler.log'),
        logging.StreamHandler()
    ]
)

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

class CompanyPrioritizer:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def get_companies_for_update(self, limit: int = 10) -> List[Dict]:
        """Get companies that need fundamental data updates"""
        try:
            # Priority 1: Companies with earnings within 7 days and no recent update
            self.cur.execute("""
                SELECT ticker, company_name, market_cap, next_earnings_date, fundamentals_last_update
                FROM stocks 
                WHERE next_earnings_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                AND (fundamentals_last_update IS NULL OR fundamentals_last_update < CURRENT_DATE - INTERVAL '30 days')
                AND market_cap > 100000
                ORDER BY next_earnings_date ASC, market_cap DESC
                LIMIT %s
            """, (limit,))
            
            companies = self.cur.fetchall()
            if companies:
                return [{'ticker': row[0], 'company_name': row[1], 'market_cap': row[2], 
                        'next_earnings_date': row[3], 'fundamentals_last_update': row[4],
                        'priority': 'earnings_soon'} for row in companies]
            
            # Priority 2: Companies with no fundamental data
            self.cur.execute("""
                SELECT ticker, company_name, market_cap, next_earnings_date, fundamentals_last_update
                FROM stocks 
                WHERE fundamentals_last_update IS NULL
                AND market_cap > 100000
                ORDER BY market_cap DESC
                LIMIT %s
            """, (limit,))
            
            companies = self.cur.fetchall()
            if companies:
                return [{'ticker': row[0], 'company_name': row[1], 'market_cap': row[2], 
                        'next_earnings_date': row[3], 'fundamentals_last_update': row[4],
                        'priority': 'no_data'} for row in companies]
            
            # Priority 3: Companies with old data (> 90 days)
            self.cur.execute("""
                SELECT ticker, company_name, market_cap, next_earnings_date, fundamentals_last_update
                FROM stocks 
                WHERE fundamentals_last_update < CURRENT_DATE - INTERVAL '90 days'
                AND market_cap > 100000
                ORDER BY fundamentals_last_update ASC, market_cap DESC
                LIMIT %s
            """, (limit,))
            
            companies = self.cur.fetchall()
            if companies:
                return [{'ticker': row[0], 'company_name': row[1], 'market_cap': row[2], 
                        'next_earnings_date': row[3], 'fundamentals_last_update': row[4],
                        'priority': 'old_data'} for row in companies]
            
            # Priority 4: Companies with moderately old data (> 30 days)
            self.cur.execute("""
                SELECT ticker, company_name, market_cap, next_earnings_date, fundamentals_last_update
                FROM stocks 
                WHERE fundamentals_last_update < CURRENT_DATE - INTERVAL '30 days'
                AND market_cap > 100000
                ORDER BY fundamentals_last_update ASC, market_cap DESC
                LIMIT %s
            """, (limit,))
            
            companies = self.cur.fetchall()
            return [{'ticker': row[0], 'company_name': row[1], 'market_cap': row[2], 
                    'next_earnings_date': row[3], 'fundamentals_last_update': row[4],
                    'priority': 'moderate_old'} for row in companies]
        except Exception as e:
            logging.error(f"Error getting companies for update: {e}")
            return []

    def mark_updated(self, ticker: str):
        self.cur.execute(
            "UPDATE stocks SET fundamentals_last_update = CURRENT_TIMESTAMP, data_priority = 1 WHERE ticker = %s",
            (ticker,)
        )
        self.conn.commit()

class UpdateFundamentalsScheduler:
    def __init__(self, provider: str, limit: int, priority: str):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.api_limiter = APIRateLimiter()
        self.yahoo = YahooFinanceService()
        self.finnhub = FinnhubService()
        self.alpha = AlphaVantageService()
        self.prioritizer = CompanyPrioritizer(self.conn)
        self.provider = provider
        self.limit = limit
        self.priority = priority
        self.priority_mapping = {
            'high': 4,
            'medium': 3,
            'low': 2,
            'lowest': 1
        }

    def run(self):
        min_priority = self.priority_mapping.get(self.priority, 1)
        tickers = self.prioritizer.get_companies_for_update(self.limit)
        logging.info(f"Selected {len(tickers)} companies for update (priority {self.priority})")
        results = {'success': 0, 'fail': 0, 'failed_tickers': []}
        for ticker in tickers:
            updated = False
            # Try Yahoo first
            if self.provider in ['yahoo', 'mixed']:
                data = self.yahoo.get_fundamental_data(ticker['ticker'])
                if data:
                    updated = True
            # Try Finnhub if Yahoo failed
            if not updated and self.provider in ['finnhub', 'mixed']:
                data = self.finnhub.get_fundamental_data(ticker['ticker'])
                if data:
                    updated = True
            # Try Alpha Vantage if both failed
            if not updated and self.provider in ['alphavantage', 'mixed']:
                data = self.alpha.get_fundamental_data(ticker['ticker'])
                if data:
                    updated = True
            if updated:
                self.prioritizer.mark_updated(ticker['ticker'])
                results['success'] += 1
            else:
                results['fail'] += 1
                results['failed_tickers'].append(ticker['ticker'])
            time.sleep(1)  # Space out API calls
        logging.info(f"Update results: {results['success']} success, {results['fail']} failed")
        if results['failed_tickers']:
            logging.warning(f"Failed tickers: {results['failed_tickers']}")
        self.yahoo.close()
        self.finnhub.close()
        self.alpha.close()
        self.api_limiter.close()
        self.conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', type=str, default='yahoo', help='Data provider: yahoo, finnhub, alphavantage, mixed')
    parser.add_argument('--limit', type=int, default=10, help='Number of companies to update')
    parser.add_argument('--priority', type=str, default='high', help='Priority: high, medium, low, lowest')
    args = parser.parse_args()
    scheduler = UpdateFundamentalsScheduler(args.provider, args.limit, args.priority)
    scheduler.run() 