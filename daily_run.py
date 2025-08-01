import os
import logging
import subprocess
import sys
from datetime import datetime
import pytz
from dotenv import load_dotenv
import psycopg2
from daily_run.check_market_schedule import should_run_daily_update

# Load environment variables
load_dotenv()

# Ensure logs directory exists
os.makedirs('daily_run/logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_run/logs/daily_run.log'),
        logging.StreamHandler()
    ]
)

def check_database_connection():
    """Verify database connection before starting"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False

def run_command(command, description):
    """Run a command and log its output"""
    logging.info(f"Starting: {description}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logging.info(f"Completed: {description}")
        if result.stdout:
            logging.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error in {description}: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in {description}: {e}")
        return False

def main(test_mode=False):
    start_time = datetime.now()
    logging.info("Starting daily run process")
    
    # Check: Was the market open today? (Skip if in test mode)
    if not test_mode:
        logging.info("Checking if market was open today...")
        should_run, reason = should_run_daily_update(), "Market day check"
        
        if not should_run:
            logging.info(f"Exiting daily run - {reason}")
            logging.info("Daily run process completed (skipped due to market closure)")
            sys.exit(0)
        else:
            logging.info(f"Market check passed - {reason}")
    else:
        logging.info("Test mode enabled - skipping market schedule check")
    
    # Verify database connection
    if not check_database_connection():
        logging.error("Database connection failed. Stopping process.")
        sys.exit(1)
    
    # Step 1: Get market prices (indices first)
    if not run_command(
        "python daily_run/get_market_prices.py",
        "Fetching market prices"
    ):
        logging.error("Failed to get market prices. Stopping process.")
        sys.exit(1)

    # Step 2: Get sector prices (ETFs second)
    if not run_command(
        "python daily_run/get_sector_prices.py",
        "Fetching sector prices"
    ):
        logging.error("Failed to get sector prices. Stopping process.")
        sys.exit(1)

    # Step 3: Get stock prices (individual stocks third)
    if not run_command(
        "python daily_run/get_prices.py",
        "Fetching stock prices"
    ):
        logging.error("Failed to get stock prices. Stopping process.")
        sys.exit(1)

    # Step 4: Fill market history
    if not run_command(
        "python daily_run/fill_history_market.py",
        "Filling market historical data"
    ):
        logging.error("Failed to fill market historical data. Stopping process.")
        sys.exit(1)

    # Step 5: Fill sector history
    if not run_command(
        "python daily_run/fill_history_sector.py",
        "Filling sector historical data"
    ):
        logging.error("Failed to fill sector historical data. Stopping process.")
        sys.exit(1)

    # Step 6: Fill stock history
    if not run_command(
        "python daily_run/fill_history.py",
        "Filling stock historical data"
    ):
        logging.error("Failed to fill stock historical data. Stopping process.")
        sys.exit(1)

    # Step 7: Calculate technicals for all tables
    if not run_command(
        "python daily_run/calc_all_technicals.py",
        "Calculating technical indicators"
    ):
        logging.error("Failed to calculate technical indicators.")
        sys.exit(1)

    # Step 8: Calculate fundamental ratios for companies with updated data
    if not run_command(
        "python daily_run/calculate_fundamental_ratios.py",
        "Calculating fundamental ratios"
    ):
        logging.warning("Failed to calculate fundamental ratios (non-critical, continuing)")
        # Don't exit on this failure as it's not critical to the main process

    # Step 9: Remove delisted stocks (final cleanup)
    if not run_command(
        "python daily_run/remove_delisted.py",
        "Removing delisted stocks from database"
    ):
        logging.warning("Failed to remove delisted stocks (non-critical, continuing)")
        # Don't exit on this failure as it's not critical to the main process
    
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Daily run completed successfully in {duration}")
    sys.exit(0)

if __name__ == "__main__":
    # Check if test mode is enabled
    test_mode = "--test" in sys.argv
    main(test_mode=test_mode) 