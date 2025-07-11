#!/usr/bin/env python3
"""
Earnings Calendar Service
"""

from common_imports import (
    os, time, logging, requests, pd, datetime, timedelta, 
    psycopg2, DB_CONFIG, setup_logging, get_api_rate_limiter, safe_get_numeric
)
import yfinance as yf
from typing import Dict, Optional, List, Any, Tuple
import argparse
from datetime import date

# Setup logging for this service
setup_logging('earnings_calendar')

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

class EarningsCalendarService:
    """
    Earnings Calendar Integration Service - BACK-010 Implementation
    
    Maintains updated earnings calendar to prioritize fundamental data updates.
    Fetches earnings dates from Yahoo Finance calendar and manages priority levels.
    """
    
    def __init__(self):
        self.api_limiter = get_api_rate_limiter()
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        self.max_retries = 3
        self.base_delay = 2  # seconds
        
        # Ensure earnings_calendar table exists
        self.create_earnings_calendar_table()
    
    def create_earnings_calendar_table(self):
        """Create earnings_calendar table if it doesn't exist"""
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS earnings_calendar (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(10) NOT NULL,
                    company_name VARCHAR(255),
                    earnings_date DATE NOT NULL,
                    earnings_time VARCHAR(20), -- 'BMO', 'AMC', 'TBD'
                    estimate_eps NUMERIC(8,4),
                    actual_eps NUMERIC(8,4),
                    estimate_revenue NUMERIC(20,2),
                    actual_revenue NUMERIC(20,2),
                    priority_level INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_source VARCHAR(50) DEFAULT 'yahoo',
                    confirmed BOOLEAN DEFAULT FALSE,
                    UNIQUE(ticker, earnings_date)
                )
            """)
            
            # Create indexes for performance (removed problematic WHERE clause)
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_earnings_date ON earnings_calendar(earnings_date);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_earnings_priority ON earnings_calendar(priority_level DESC, earnings_date);")
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_earnings_ticker ON earnings_calendar(ticker);")
            
            self.conn.commit()
            logging.info("Earnings calendar table and indexes created successfully")
            
        except Exception as e:
            logging.error(f"Error creating earnings calendar table: {e}")
            self.conn.rollback()
    
    def get_earnings_info(self, ticker: str) -> Optional[Dict]:
        """
        Get earnings information for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary containing earnings information
        """
        try:
            # Get the most recent earnings data
            query = """
            SELECT earnings_date, estimate_eps, actual_eps, estimate_revenue, actual_revenue
            FROM earnings_calendar 
            WHERE ticker = %s 
            ORDER BY earnings_date DESC 
            LIMIT 1
            """
            
            result = self.fetch_one(query, (ticker,))
            if result:
                return {
                    'last_earnings_date': result[0],
                    'estimate_eps': result[1],
                    'actual_eps': result[2],
                    'estimate_revenue': result[3],
                    'actual_revenue': result[4]
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting earnings info for {ticker}: {e}")
            return None
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Execute a query and return a single result"""
        try:
            self.cur.execute(query, params)
            return self.cur.fetchone()
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            return None

    def get_earnings_calendar(self, ticker: str) -> Optional[List[Dict]]:
        """
        Get earnings calendar data for a ticker (alias for fetch_earnings_calendar).
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of earnings calendar entries
        """
        earnings_data = self.fetch_earnings_calendar(ticker)
        if earnings_data:
            return [earnings_data]  # Return as list for compatibility
        return []

    def fetch_earnings_calendar(self, ticker: str) -> Optional[Dict]:
        """
        Fetch earnings calendar data with fallback: Yahoo → Finnhub → Alpha Vantage
        """
        # 1. Try Yahoo
        for attempt in range(self.max_retries):
            try:
                provider = 'yahoo'
                endpoint = 'earnings_calendar'
                if not self.api_limiter.check_limit(provider, endpoint):
                    logging.warning(f"Yahoo Finance API limit reached for {ticker}")
                    break
                stock = yf.Ticker(ticker)
                calendar = stock.calendar
                self.api_limiter.record_call(provider, endpoint)
                if calendar is not None and len(calendar) > 0:
                    earnings_data = self.parse_earnings_calendar(ticker, calendar)
                    if earnings_data:
                        earnings_data['data_source'] = 'yahoo'
                        logging.info(f"Successfully fetched earnings calendar for {ticker} from Yahoo")
                        return earnings_data
                else:
                    logging.warning(f"No Yahoo earnings calendar data for {ticker}")
                    break
            except Exception as e:
                if 'rate limit' in str(e).lower() or 'too many requests' in str(e).lower():
                    wait_time = self.base_delay * (2 ** attempt)
                    logging.warning(f"Yahoo rate limited for {ticker}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                logging.error(f"Yahoo error for {ticker}: {e}")
                break
        # 2. Try Finnhub
        try:
            provider = 'finnhub'
            endpoint = 'earnings_calendar'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Finnhub API limit reached for {ticker}")
            else:
                url = f"https://finnhub.io/api/v1/calendar/earnings"
                params = {'symbol': ticker, 'from': datetime.now().strftime('%Y-%m-%d'), 'to': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'), 'token': FINNHUB_API_KEY}
                response = requests.get(url, params=params, timeout=30)
                self.api_limiter.record_call(provider, endpoint)
                if response.status_code == 200:
                    data = response.json()
                    if data and 'earningsCalendar' in data and data['earningsCalendar']:
                        # Take the next earnings event
                        event = data['earningsCalendar'][0]
                        earnings_data = {
                            'ticker': ticker,
                            'earnings_date': event.get('date'),
                            'earnings_time': event.get('hour', 'TBD'),
                            'estimate_eps': event.get('epsEstimate'),
                            'actual_eps': event.get('epsActual'),
                            'estimate_revenue': event.get('revenueEstimate'),
                            'actual_revenue': event.get('revenueActual'),
                            'data_source': 'finnhub',
                            'confirmed': event.get('status', '').lower() == 'confirmed'
                        }
                        logging.info(f"Successfully fetched earnings calendar for {ticker} from Finnhub")
                        return earnings_data
                    else:
                        logging.warning(f"No Finnhub earnings calendar data for {ticker}")
        except Exception as e:
            logging.error(f"Finnhub error for {ticker}: {e}")
        # 3. Try Alpha Vantage
        try:
            provider = 'alphavantage'
            endpoint = 'EARNINGS'
            if not self.api_limiter.check_limit(provider, endpoint):
                logging.warning(f"Alpha Vantage API limit reached for {ticker}")
            else:
                url = f"https://www.alphavantage.co/query"
                params = {'function': 'EARNINGS', 'symbol': ticker, 'apikey': ALPHA_VANTAGE_API_KEY}
                response = requests.get(url, params=params, timeout=30)
                self.api_limiter.record_call(provider, endpoint)
                if response.status_code == 200:
                    data = response.json()
                    if 'quarterlyEarnings' in data and data['quarterlyEarnings']:
                        event = data['quarterlyEarnings'][0]
                        earnings_data = {
                            'ticker': ticker,
                            'earnings_date': event.get('reportedDate'),
                            'earnings_time': 'TBD',
                            'estimate_eps': event.get('estimatedEPS'),
                            'actual_eps': event.get('reportedEPS'),
                            'estimate_revenue': None,
                            'actual_revenue': None,
                            'data_source': 'alphavantage',
                            'confirmed': True
                        }
                        logging.info(f"Successfully fetched earnings calendar for {ticker} from Alpha Vantage")
                        return earnings_data
                    else:
                        logging.warning(f"No Alpha Vantage earnings calendar data for {ticker}")
        except Exception as e:
            logging.error(f"Alpha Vantage error for {ticker}: {e}")
        return None
    
    def parse_earnings_calendar(self, ticker: str, calendar: Dict) -> Optional[Dict]:
        """
        Parse earnings calendar data from Yahoo Finance
        
        Args:
            ticker: Stock ticker symbol
            calendar: Dictionary from yfinance calendar
            
        Returns:
            Dictionary containing parsed earnings data
        """
        try:
            if not calendar or len(calendar) == 0:
                return None
            
            # Get the next earnings date (first entry)
            next_earnings = calendar[0] if isinstance(calendar, list) else calendar
            
            earnings_data = {
                'ticker': ticker,
                'earnings_date': next_earnings.get('Earnings Date', None),
                'earnings_time': self.parse_earnings_time(next_earnings.get('Earnings Call Time', None)),
                'estimate_eps': self.safe_get_numeric_dict(next_earnings, 'EPS Estimate'),
                'actual_eps': self.safe_get_numeric_dict(next_earnings, 'EPS Actual'),
                'estimate_revenue': self.safe_get_numeric_dict(next_earnings, 'Revenue Estimate'),
                'actual_revenue': self.safe_get_numeric_dict(next_earnings, 'Revenue Actual'),
                'data_source': 'yahoo',
                'confirmed': True  # Yahoo data is considered confirmed
            }
            
            return earnings_data
            
        except Exception as e:
            logging.error(f"Error parsing earnings calendar for {ticker}: {e}")
            return None
    
    def parse_earnings_time(self, time_str: str) -> str:
        """Parse earnings time string to standard format"""
        if not time_str:
            return 'TBD'
        
        time_str = str(time_str).upper()
        if 'BMO' in time_str or 'BEFORE' in time_str:
            return 'BMO'  # Before Market Open
        elif 'AMC' in time_str or 'AFTER' in time_str:
            return 'AMC'  # After Market Close
        else:
            return 'TBD'  # To Be Determined
    
    def safe_get_numeric_dict(self, data: Dict, key: str) -> Optional[float]:
        """Safely extract numeric value from dictionary"""
        try:
            value = data.get(key)
            if value is None or pd.isna(value):
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def store_earnings_data(self, earnings_data: Dict) -> bool:
        """
        Store earnings calendar data in database
        
        Args:
            earnings_data: Dictionary containing earnings data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ticker = earnings_data['ticker']
            earnings_date = earnings_data['earnings_date']
            
            # Check if earnings date is valid
            if not earnings_date or pd.isna(earnings_date):
                logging.warning(f"Invalid earnings date for {ticker}")
                return False
            
            # Convert to date if it's a datetime
            if isinstance(earnings_date, pd.Timestamp):
                earnings_date = earnings_date.date()
            
            # Upsert earnings data
            self.cur.execute("""
                INSERT INTO earnings_calendar 
                (ticker, company_name, earnings_date, earnings_time, estimate_eps, 
                 actual_eps, estimate_revenue, actual_revenue, priority_level, 
                 data_source, confirmed, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (ticker, earnings_date) 
                DO UPDATE SET
                    earnings_time = EXCLUDED.earnings_time,
                    estimate_eps = EXCLUDED.estimate_eps,
                    actual_eps = EXCLUDED.actual_eps,
                    estimate_revenue = EXCLUDED.estimate_revenue,
                    actual_revenue = EXCLUDED.actual_revenue,
                    data_source = EXCLUDED.data_source,
                    confirmed = EXCLUDED.confirmed,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                ticker,
                earnings_data.get('company_name'),
                earnings_date,
                earnings_data.get('earnings_time', 'TBD'),
                earnings_data.get('estimate_eps'),
                earnings_data.get('actual_eps'),
                earnings_data.get('estimate_revenue'),
                earnings_data.get('actual_revenue'),
                earnings_data.get('priority_level', 1),
                earnings_data.get('data_source', 'yahoo'),
                earnings_data.get('confirmed', False)
            ))
            
            self.conn.commit()
            logging.info(f"Stored earnings data for {ticker} on {earnings_date}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing earnings data for {ticker}: {e}")
            self.conn.rollback()
            return False
    
    def update_earnings_priorities(self):
        """
        Update priority levels based on earnings dates
        
        Priority levels:
        5: Earnings within 7 days (highest priority)
        4: Earnings within 30 days
        3: Earnings within 90 days
        2: Earnings within 180 days
        1: All other earnings (lowest priority)
        """
        try:
            # Update priorities based on earnings proximity
            self.cur.execute("""
                UPDATE earnings_calendar 
                SET priority_level = 
                    CASE 
                        WHEN earnings_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days' THEN 5
                        WHEN earnings_date BETWEEN CURRENT_DATE + INTERVAL '8 days' AND CURRENT_DATE + INTERVAL '30 days' THEN 4
                        WHEN earnings_date BETWEEN CURRENT_DATE + INTERVAL '31 days' AND CURRENT_DATE + INTERVAL '90 days' THEN 3
                        WHEN earnings_date BETWEEN CURRENT_DATE + INTERVAL '91 days' AND CURRENT_DATE + INTERVAL '180 days' THEN 2
                        ELSE 1
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE earnings_date >= CURRENT_DATE
            """)
            
            updated_count = self.cur.rowcount
            self.conn.commit()
            logging.info(f"Updated priority levels for {updated_count} earnings records")
            
            return updated_count
            
        except Exception as e:
            logging.error(f"Error updating earnings priorities: {e}")
            self.conn.rollback()
            return 0
    
    def get_earnings_next_7_days(self) -> List[str]:
        """Get tickers with earnings in the next 7 days"""
        try:
            self.cur.execute("""
                SELECT DISTINCT ticker 
                FROM earnings_calendar 
                WHERE earnings_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                ORDER BY earnings_date ASC
            """)
            
            tickers = [row[0] for row in self.cur.fetchall()]
            logging.info(f"Found {len(tickers)} companies with earnings in next 7 days")
            return tickers
            
        except Exception as e:
            logging.error(f"Error getting earnings next 7 days: {e}")
            return []
    
    def get_earnings_older_than_30_days(self) -> List[str]:
        """Get tickers with earnings older than 30 days"""
        try:
            self.cur.execute("""
                SELECT DISTINCT ticker 
                FROM earnings_calendar 
                WHERE earnings_date < CURRENT_DATE - INTERVAL '30 days'
                ORDER BY earnings_date DESC
            """)
            
            tickers = [row[0] for row in self.cur.fetchall()]
            logging.info(f"Found {len(tickers)} companies with earnings older than 30 days")
            return tickers
            
        except Exception as e:
            logging.error(f"Error getting old earnings: {e}")
            return []
    
    def update_stocks_earnings_dates(self):
        """
        Update next_earnings_date in stocks table based on earnings_calendar
        """
        try:
            self.cur.execute("""
                UPDATE stocks s
                SET next_earnings_date = (
                    SELECT MIN(earnings_date)
                    FROM earnings_calendar ec
                    WHERE ec.ticker = s.ticker
                    AND ec.earnings_date >= CURRENT_DATE
                )
                WHERE EXISTS (
                    SELECT 1 FROM earnings_calendar ec2
                    WHERE ec2.ticker = s.ticker
                    AND ec2.earnings_date >= CURRENT_DATE
                )
            """)
            
            updated_count = self.cur.rowcount
            self.conn.commit()
            logging.info(f"Updated next_earnings_date for {updated_count} stocks")
            
            return updated_count
            
        except Exception as e:
            logging.error(f"Error updating stocks earnings dates: {e}")
            self.conn.rollback()
            return 0
    
    def get_companies_needing_earnings_update(self, limit: int = 50) -> List[Dict]:
        """
        Get companies that need earnings calendar updates
        
        Args:
            limit: Maximum number of companies to return
            
        Returns:
            List of dictionaries containing company data
        """
        try:
            self.cur.execute("""
                SELECT s.ticker, s.company_name, s.market_cap, 
                       s.next_earnings_date, s.fundamentals_last_update,
                       ec.earnings_date as calendar_earnings_date,
                       ec.updated_at as calendar_last_updated
                FROM stocks s
                LEFT JOIN earnings_calendar ec ON s.ticker = ec.ticker 
                    AND ec.earnings_date >= CURRENT_DATE
                WHERE s.market_cap > 0
                AND (
                    s.next_earnings_date IS NULL
                    OR ec.earnings_date IS NULL
                    OR ec.updated_at < CURRENT_DATE - INTERVAL '7 days'
                    OR s.next_earnings_date != ec.earnings_date
                )
                ORDER BY s.market_cap DESC
                LIMIT %s
            """, (limit,))
            
            companies = []
            for row in self.cur.fetchall():
                companies.append({
                    'ticker': row[0],
                    'company_name': row[1],
                    'market_cap': row[2],
                    'next_earnings_date': row[3],
                    'fundamentals_last_update': row[4],
                    'calendar_earnings_date': row[5],
                    'calendar_last_updated': row[6],
                    'needs_update': True
                })
            
            logging.info(f"Found {len(companies)} companies needing earnings calendar updates")
            return companies
            
        except Exception as e:
            logging.error(f"Error getting companies needing earnings update: {e}")
            return []
    
    def process_earnings_calendar_updates(self, tickers: List[str] = None, limit: int = 20):
        """
        Process earnings calendar updates for specified tickers or companies needing updates
        
        Args:
            tickers: List of specific tickers to update (if None, auto-select)
            limit: Maximum number of companies to process
        """
        if tickers is None:
            # Get companies that need updates
            companies = self.get_companies_needing_earnings_update(limit)
            tickers = [company['ticker'] for company in companies]
        
        if not tickers:
            logging.info("No companies need earnings calendar updates")
            return
        
        logging.info(f"Processing earnings calendar updates for {len(tickers)} companies")
        
        success_count = 0
        for ticker in tickers:
            try:
                # Fetch earnings calendar data
                earnings_data = self.fetch_earnings_calendar(ticker)
                
                if earnings_data:
                    # Store in database
                    if self.store_earnings_data(earnings_data):
                        success_count += 1
                        logging.info(f"Successfully updated earnings calendar for {ticker}")
                    else:
                        logging.warning(f"Failed to store earnings data for {ticker}")
                else:
                    logging.warning(f"No earnings data available for {ticker}")
                
                # Rate limiting delay
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Error processing earnings calendar for {ticker}: {e}")
                continue
        
        # Update priorities and stocks table
        self.update_earnings_priorities()
        self.update_stocks_earnings_dates()
        
        logging.info(f"Completed earnings calendar updates: {success_count}/{len(tickers)} successful")
    
    def get_earnings_summary(self) -> Dict:
        """Get summary of earnings calendar data"""
        try:
            self.cur.execute("""
                SELECT 
                    COUNT(*) as total_earnings,
                    COUNT(CASE WHEN earnings_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days' THEN 1 END) as next_7_days,
                    COUNT(CASE WHEN earnings_date BETWEEN CURRENT_DATE + INTERVAL '8 days' AND CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as next_30_days,
                    COUNT(CASE WHEN earnings_date >= CURRENT_DATE THEN 1 END) as upcoming_earnings,
                    COUNT(CASE WHEN earnings_date < CURRENT_DATE THEN 1 END) as past_earnings
                FROM earnings_calendar
            """)
            
            row = self.cur.fetchone()
            summary = {
                'total_earnings': row[0],
                'next_7_days': row[1],
                'next_30_days': row[2],
                'upcoming_earnings': row[3],
                'past_earnings': row[4],
                'last_updated': datetime.now()
            }
            
            return summary
            
        except Exception as e:
            logging.error(f"Error getting earnings summary: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Earnings Calendar Service')
    parser.add_argument('--tickers', nargs='+', help='Specific tickers to update')
    parser.add_argument('--limit', type=int, default=20, help='Maximum companies to process')
    parser.add_argument('--summary', action='store_true', help='Show earnings summary')
    parser.add_argument('--update-priorities', action='store_true', help='Update priority levels')
    
    args = parser.parse_args()
    
    service = EarningsCalendarService()
    
    try:
        if args.summary:
            summary = service.get_earnings_summary()
            print("Earnings Calendar Summary:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
        
        elif args.update_priorities:
            updated = service.update_earnings_priorities()
            print(f"Updated priority levels for {updated} earnings records")
        
        else:
            service.process_earnings_calendar_updates(args.tickers, args.limit)
    
    finally:
        service.close()

if __name__ == "__main__":
    main() 