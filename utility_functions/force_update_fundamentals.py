import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the daily_run directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from daily_run.yahoo_finance_service import YahooFinanceService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def force_update_fundamentals():
    """
    Fetches and stores comprehensive fundamental data for a specific list of tickers.
    This script contains the CORRECT logic for storing all necessary data points
    into the 'stocks' table for ratio calculation.
    """
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 'UNH', 'V']
    yahoo_service = YahooFinanceService()
    
    logging.info(f"Starting fundamental data force-update for {len(tickers)} tickers.")

    for ticker in tickers:
        logging.info(f"--- Processing {ticker} ---")
        try:
            # 1. Fetch data using the existing service
            data = yahoo_service.get_fundamental_data(ticker)
            if not data:
                logging.warning(f"Could not retrieve any data for {ticker}. Skipping.")
                continue

            financial_data = data.get('financials')
            key_stats = data.get('stats')

            # 2. Extract all necessary data points
            income = financial_data.get('income_statement', {}) if financial_data else {}
            balance = financial_data.get('balance_sheet', {}) if financial_data else {}
            market_data = key_stats.get('market_data', {}) if key_stats else {}
            per_share = key_stats.get('per_share_metrics', {}) if key_stats else {}

            update_payload = {
                'market_cap': market_data.get('market_cap'),
                'enterprise_value': market_data.get('enterprise_value'),
                'shares_outstanding': market_data.get('shares_outstanding'),
                'revenue_ttm': income.get('revenue'),
                'net_income_ttm': income.get('net_income'),
                'ebitda_ttm': income.get('ebitda'),
                'diluted_eps_ttm': per_share.get('eps_diluted'),
                'book_value_per_share': per_share.get('book_value_per_share'),
                'total_debt': balance.get('total_debt'),
                'shareholders_equity': balance.get('total_equity'),
                'cash_and_equivalents': balance.get('cash_and_equivalents'),
                'fundamentals_last_update': datetime.now()
            }

            # Filter out any keys where the value is None
            update_payload = {k: v for k, v in update_payload.items() if v is not None}

            if not update_payload:
                logging.warning(f"No valid data to store for {ticker}. Skipping.")
                continue

            # 3. Build and execute the database update
            set_clause = ", ".join([f"{key} = %s" for key in update_payload.keys()])
            values = list(update_payload.values())
            values.append(ticker)
            
            query = f"UPDATE stocks SET {set_clause} WHERE ticker = %s"
            
            yahoo_service.cur.execute(query, tuple(values))
            yahoo_service.conn.commit()
            
            logging.info(f"Successfully stored {len(update_payload)} data points for {ticker} in the 'stocks' table.")

        except Exception as e:
            logging.error(f"An error occurred while processing {ticker}: {e}")
            if yahoo_service.conn:
                yahoo_service.conn.rollback()

    logging.info("Fundamental data force-update complete.")
    yahoo_service.close()

if __name__ == "__main__":
    force_update_fundamentals() 