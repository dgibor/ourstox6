#!/usr/bin/env python3
"""
Daily Fundamentals Updater
Runs after price updates and only updates fundamentals for:
1. Tickers missing fundamental data
2. Tickers after earnings date
3. Respects rate limits
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import DatabaseManager
from fmp_service import FMPService
from config import Config
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_fundamentals.log'),
        logging.StreamHandler()
    ]
)

class DailyFundamentalsUpdater:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.fmp_service = FMPService()
        self.today = datetime.now().date()
        
    def get_tickers_needing_updates(self) -> List[str]:
        """Get tickers that need fundamental updates"""
        self.db.connect()
        
        try:
            # Get all tickers with their fundamental data status
            query = """
            SELECT 
                s.ticker,
                s.shares_outstanding,
                s.next_earnings_date,
                s.market_cap,
                s.revenue_ttm,
                s.net_income_ttm,
                s.total_assets,
                s.total_debt,
                s.cash_and_equivalents,
                s.current_assets,
                s.current_liabilities,
                s.operating_income,
                s.ebitda_ttm,
                s.shareholders_equity,
                s.book_value_per_share,
                s.diluted_eps_ttm,
                s.free_cash_flow,
                s.enterprise_value
            FROM stocks s
            ORDER BY s.ticker
            """
            
            results = self.db.execute_query(query)
            tickers_needing_updates = []
            
            for row in results:
                ticker = row[0]
                needs_update = False
                reason = []
                
                # Check if fundamental data is missing
                if not row[1] or row[1] == 0:  # shares_outstanding
                    needs_update = True
                    reason.append("missing shares_outstanding")
                
                if not row[2]:  # next_earnings_date
                    needs_update = True
                    reason.append("missing earnings_date")
                
                # Check if key financial data is missing
                missing_financials = []
                for i, field in enumerate(['market_cap', 'revenue_ttm', 'net_income_ttm', 'total_assets', 
                                         'total_debt', 'cash_and_equivalents', 'current_assets', 
                                         'current_liabilities', 'operating_income', 'ebitda_ttm', 
                                         'shareholders_equity', 'book_value_per_share', 'diluted_eps_ttm', 
                                         'free_cash_flow', 'enterprise_value'], 3):
                    if not row[i]:
                        missing_financials.append(field)
                
                if len(missing_financials) > 5:  # If more than 5 fields are missing
                    needs_update = True
                    reason.append(f"missing financials: {', '.join(missing_financials[:3])}...")
                
                # Check if after earnings date
                if row[2]:  # next_earnings_date
                    try:
                        earnings_date = datetime.strptime(str(row[2]), '%Y-%m-%d').date()
                        if earnings_date <= self.today:
                            needs_update = True
                            reason.append("after earnings date")
                    except (ValueError, TypeError):
                        pass
                
                if needs_update:
                    tickers_needing_updates.append({
                        'ticker': ticker,
                        'reasons': reason
                    })
            
            logging.info(f"Found {len(tickers_needing_updates)} tickers needing fundamental updates")
            return tickers_needing_updates
            
        except Exception as e:
            logging.error(f"Error getting tickers needing updates: {e}")
            return []
        finally:
            self.db.disconnect()
    
    def update_ticker_fundamentals(self, ticker: str, reasons: List[str]) -> bool:
        """Update fundamentals for a single ticker"""
        try:
            logging.info(f"Updating fundamentals for {ticker} - reasons: {', '.join(reasons)}")
            
            # Get financial statements
            financial_data = self.fmp_service.fetch_financial_statements(ticker)
            if not financial_data:
                logging.warning(f"No financial data available for {ticker}")
                return False
            
            # Get key statistics
            key_stats = self.fmp_service.fetch_key_statistics(ticker)
            if not key_stats:
                logging.warning(f"No key statistics available for {ticker}")
                return False
            
            # Store the data
            success = self.fmp_service.store_fundamental_data(ticker, financial_data, key_stats)
            
            if success:
                logging.info(f"SUCCESS: Updated fundamentals for {ticker}")
            else:
                logging.warning(f"WARNING: Failed to store fundamentals for {ticker}")
            
            return success
            
        except Exception as e:
            logging.error(f"ERROR: Error updating fundamentals for {ticker}: {e}")
            return False
    
    def run_daily_update(self, max_tickers: int = 50) -> Dict:
        """Run the daily fundamentals update"""
        logging.info("=" * 60)
        logging.info("Starting Daily Fundamentals Update")
        logging.info("=" * 60)
        
        start_time = datetime.now()
        
        # Get tickers needing updates
        tickers_needing_updates = self.get_tickers_needing_updates()
        
        if not tickers_needing_updates:
            logging.info("No tickers need fundamental updates today")
            return {
                'status': 'success',
                'message': 'No tickers need updates',
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'duration': (datetime.now() - start_time).total_seconds()
            }
        
        # Limit to max_tickers to respect rate limits
        if len(tickers_needing_updates) > max_tickers:
            logging.info(f"Limiting updates to {max_tickers} tickers (out of {len(tickers_needing_updates)} needing updates)")
            tickers_needing_updates = tickers_needing_updates[:max_tickers]
        
        successful_updates = 0
        failed_updates = 0
        
        logging.info(f"Processing {len(tickers_needing_updates)} tickers...")
        
        for i, ticker_info in enumerate(tickers_needing_updates, 1):
            ticker = ticker_info['ticker']
            reasons = ticker_info['reasons']
            
            logging.info(f"[{i}/{len(tickers_needing_updates)}] Processing {ticker}")
            
            success = self.update_ticker_fundamentals(ticker, reasons)
            
            if success:
                successful_updates += 1
            else:
                failed_updates += 1
            
            # Rate limiting - wait between requests
            if i < len(tickers_needing_updates):
                time.sleep(1)  # 1 second between requests
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logging.info("=" * 60)
        logging.info("Daily Fundamentals Update Complete")
        logging.info(f"Processed: {len(tickers_needing_updates)}")
        logging.info(f"Successful: {successful_updates}")
        logging.info(f"Failed: {failed_updates}")
        logging.info(f"Duration: {duration:.2f} seconds")
        logging.info("=" * 60)
        
        return {
            'status': 'success',
            'processed': len(tickers_needing_updates),
            'successful': successful_updates,
            'failed': failed_updates,
            'duration': duration
        }
    
    def close(self):
        """Close connections"""
        self.fmp_service.close()

if __name__ == "__main__":
    updater = DailyFundamentalsUpdater()
    try:
        result = updater.run_daily_update(max_tickers=20)  # Limit to 20 for testing
        print(f"Update result: {result}")
    finally:
        updater.close() 