"""
Market Schedule Checker

Simple market schedule functionality for the trading system.
"""

import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def is_market_open(check_time: datetime = None) -> bool:
    """
    Check if the market is currently open
    
    Args:
        check_time: Time to check (defaults to now)
        
    Returns:
        True if market is open, False otherwise
    """
    if check_time is None:
        check_time = datetime.now()
    
    # Simple market hours check (9:30 AM - 4:00 PM ET, Monday-Friday)
    # This is a simplified version - production would use pandas_market_calendars
    
    # Check if it's a weekend
    if check_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if it's within market hours (simplified - assumes ET)
    hour = check_time.hour
    minute = check_time.minute
    
    # Market opens at 9:30 AM
    if hour < 9 or (hour == 9 and minute < 30):
        return False
    
    # Market closes at 4:00 PM
    if hour >= 16:
        return False
    
    return True


def is_market_day(check_date: date = None) -> bool:
    """
    Check if the given date is a market day
    
    Args:
        check_date: Date to check (defaults to today)
        
    Returns:
        True if it's a market day, False otherwise
    """
    if check_date is None:
        check_date = date.today()
    
    # Simple check - weekdays only (no holiday handling)
    return check_date.weekday() < 5


def get_next_market_day(from_date: date = None) -> date:
    """
    Get the next market day
    
    Args:
        from_date: Starting date (defaults to today)
        
    Returns:
        Next market day
    """
    if from_date is None:
        from_date = date.today()
    
    current_date = from_date
    while not is_market_day(current_date):
        current_date = date.fromordinal(current_date.toordinal() + 1)
    
    return current_date


def should_run_daily_update() -> bool:
    """
    Determine if daily update should run
    
    Returns:
        True if daily update should run, False otherwise
    """
    # Run on market days, even if market is closed (for end-of-day processing)
    return is_market_day()


class MarketSchedule:
    """Market schedule helper class"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_schedule")
    
    def is_trading_hours(self) -> bool:
        """Check if currently in trading hours"""
        return is_market_open()
    
    def is_trading_day(self) -> bool:
        """Check if today is a trading day"""
        return is_market_day()
    
    def should_process_data(self) -> bool:
        """Check if data processing should occur"""
        return should_run_daily_update() 