import os
import logging
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

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

def check_market_hours():
    """Check if it's a valid time to run (after market close)"""
    now = datetime.now()
    # Check if it's a weekday
    if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        logging.info("Skipping run - weekend")
        return False
    # Check if it's after market close (4:00 PM ET = 8:00 PM UTC)
    if now.hour < 20:
        logging.info("Skipping run - before market close")
        return False
    return True

def main(test_mode=False):
    start_time = datetime.now()
    logging.info("Starting daily run process")
    
    # Check if it's a valid time to run (skip if in test mode)
    if not test_mode and not check_market_hours():
        logging.info("Exiting - not a valid time to run")
        sys.exit(0)
    
    # Verify database connection
    if not check_database_connection():
        logging.error("Database connection failed. Stopping process.")
        sys.exit(1)
    
    # Step 1: Get latest prices
    if not run_command(
        "python daily_run/get_prices.py",
        "Fetching latest prices"
    ):
        logging.error("Failed to get latest prices. Stopping process.")
        sys.exit(1)

    # Step 1b: Get sector prices
    if not run_command(
        "python daily_run/get_sector_prices.py",
        "Fetching sector prices"
    ):
        logging.error("Failed to get sector prices. Stopping process.")
        sys.exit(1)

    # Step 2: Fill history for any missing data
    if not run_command(
        "python daily_run/fill_history.py",
        "Filling historical data"
    ):
        logging.error("Failed to fill historical data. Stopping process.")
        sys.exit(1)

    # Step 2b: Fill sector history
    if not run_command(
        "python daily_run/fill_history_sector.py",
        "Filling sector historical data"
    ):
        logging.error("Failed to fill sector historical data. Stopping process.")
        sys.exit(1)

    # Step 2c: Get market prices
    if not run_command(
        "python daily_run/get_market_prices.py",
        "Fetching market prices"
    ):
        logging.error("Failed to get market prices. Stopping process.")
        sys.exit(1)

    # Step 2d: Fill market history
    if not run_command(
        "python daily_run/fill_history_market.py",
        "Filling market historical data"
    ):
        logging.error("Failed to fill market historical data. Stopping process.")
        sys.exit(1)

    # Step 3: Calculate technicals for all tables
    if not run_command(
        "python daily_run/calc_all_technicals.py",
        "Calculating technical indicators"
    ):
        logging.error("Failed to calculate technical indicators.")
        sys.exit(1)
    
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Daily run completed in {duration}")
    sys.exit(0)

if __name__ == "__main__":
    # Check if test mode is enabled
    test_mode = "--test" in sys.argv
    main(test_mode=test_mode) 