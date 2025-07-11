import logging
import pandas_market_calendars as mcal
from datetime import datetime, date
import pytz
from typing import Tuple

def check_market_open_today(target_date=None) -> Tuple[bool, str, dict]:
    """
    Check if the US market (NYSE) was open on a given date.
    
    Args:
        target_date: Date to check (default: today)
    
    Returns:
        Tuple containing:
        - bool: True if market was open that day, False otherwise
        - str: Detailed message about market status
        - dict: Additional details (open_time, close_time, etc.)
    """
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get NYSE calendar (represents US stock market)
        nyse = mcal.get_calendar('NYSE')
        
        # Get the target date (default to today)
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Checking market schedule for {target_date}")
        
        # Get valid trading days for the target date
        valid_days = nyse.valid_days(start_date=target_date, end_date=target_date)
        
        # Check if that date is a valid trading session
        is_trading_day = len(valid_days) > 0
        
        if not is_trading_day:
            # Check what type of non-trading day this is
            day_name = target_date.strftime('%A')
            
            # Check if it's a weekend
            if target_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                message = f"Market closed on {target_date} - Weekend ({day_name})"
                logger.info(message)
                return False, message, {
                    'date': target_date,
                    'day_name': day_name,
                    'reason': 'weekend',
                    'open_time': None,
                    'close_time': None
                }
            else:
                # It's a weekday but market is closed - must be a holiday
                message = f"Market closed on {target_date} - Holiday ({day_name})"
                logger.info(message)
                return False, message, {
                    'date': target_date,
                    'day_name': day_name,
                    'reason': 'holiday',
                    'open_time': None,
                    'close_time': None
                }
        
        # Market was open that day - get the schedule details
        schedule = nyse.schedule(start_date=target_date, end_date=target_date)
        
        if schedule.empty:
            message = f"Market closed on {target_date} - No trading session found"
            logger.warning(message)
            return False, message, {
                'date': target_date,
                'day_name': target_date.strftime('%A'),
                'reason': 'no_session',
                'open_time': None,
                'close_time': None
            }
        
        # Get market times
        market_open_utc = schedule.iloc[0]['market_open']
        market_close_utc = schedule.iloc[0]['market_close']
        
        # Convert to Eastern Time for display
        eastern = pytz.timezone('US/Eastern')
        market_open_et = market_open_utc.tz_convert(eastern)
        market_close_et = market_close_utc.tz_convert(eastern)
        
        # Check if it was an early close day
        regular_close_time = "4:00 PM"
        actual_close_time = market_close_et.strftime("%I:%M %p").lstrip('0')
        
        if actual_close_time != regular_close_time:
            early_close_note = f" (Early close at {actual_close_time})"
        else:
            early_close_note = ""
        
        message = f"Market was open on {target_date} - {market_open_et.strftime('%I:%M %p')} to {actual_close_time} ET{early_close_note}"
        logger.info(message)
        
        return True, message, {
            'date': target_date,
            'day_name': target_date.strftime('%A'),
            'reason': 'trading_day',
            'open_time': market_open_et.strftime('%I:%M %p ET'),
            'close_time': actual_close_time + ' ET',
            'was_early_close': actual_close_time != regular_close_time,
            'market_open_utc': market_open_utc,
            'market_close_utc': market_close_utc
        }
        
    except Exception as e:
        error_message = f"Error checking market schedule: {str(e)}"
        logger.error(error_message)
        return False, error_message, {
            'date': target_date if 'target_date' in locals() else date.today(),
            'day_name': target_date.strftime('%A') if 'target_date' in locals() else 'Unknown',
            'reason': 'error',
            'error': str(e),
            'open_time': None,
            'close_time': None
        }

def should_run_daily_process() -> Tuple[bool, str]:
    """
    Determine if the daily process should run based on market schedule.
    
    Returns:
        Tuple containing:
        - bool: True if daily process should run, False otherwise
        - str: Reason for the decision
    """
    
    logger = logging.getLogger(__name__)
    
    market_open, message, details = check_market_open_today()
    
    if market_open:
        decision_message = "Daily process will run - Market was open today"
        logger.info(decision_message)
        logger.info(f"Market details: {details['open_time']} to {details['close_time']}")
        return True, decision_message
    else:
        decision_message = f"Daily process will be skipped - {details['reason'].replace('_', ' ').title()}"
        logger.info(decision_message)
        logger.info(f"Market status: {message}")
        return False, decision_message

if __name__ == "__main__":
    # Test the function when run directly
    import os
    import sys
    
    # Add the parent directory to path to access utility functions if needed
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configure basic logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Testing market schedule checker...")
    
    # Test the detailed function for today
    print("\n=== Testing for TODAY ===")
    is_open, msg, details = check_market_open_today()
    print(f"Market Open: {is_open}")
    print(f"Message: {msg}")
    print(f"Details: {details}")
    
    # Test the decision function
    should_run, reason = should_run_daily_process()
    print(f"\nShould Run Process: {should_run}")
    print(f"Reason: {reason}")
    
    # Test with some specific dates
    print("\n=== Testing for DIFFERENT DATES ===")
    
    from datetime import timedelta, date as date_class
    
    def test_specific_date(test_date):
        is_open, msg, details = check_market_open_today(test_date)
        print(f"\nDate: {test_date} ({test_date.strftime('%A')})")
        print(f"Market Open: {is_open}")
        print(f"Message: {msg}")
        print(f"Reason: {details['reason']}")
    
    # Find next Saturday for testing
    today = date.today()
    current_year = today.year
    
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    next_saturday = today + timedelta(days=days_until_saturday)
    test_specific_date(next_saturday)
    
    # Find next Sunday for testing  
    next_sunday = next_saturday + timedelta(days=1)
    test_specific_date(next_sunday)
    
    # Test known holidays for current year
    # Independence Day
    july_4_current = date_class(current_year, 7, 4)
    test_specific_date(july_4_current)
    
    # Christmas
    christmas_current = date_class(current_year, 12, 25)
    test_specific_date(christmas_current)
    
    # New Year's Day (next year)
    new_years_next = date_class(current_year + 1, 1, 1)
    test_specific_date(new_years_next)
    
    print("\n=== Testing Complete ===") 