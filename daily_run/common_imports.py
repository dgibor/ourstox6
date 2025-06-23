#!/usr/bin/env python3
"""
Common imports for all service files
This file centralizes the most commonly used imports across the daily_run services
to reduce duplication and maintain consistency.
"""

# Standard library imports
import os
import time
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

# Third-party imports
import requests
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path for utility imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Common logging configuration
def setup_logging(service_name: str, log_file: str = None):
    """Setup logging for a service"""
    if log_file is None:
        log_file = f'daily_run/logs/{service_name}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Common API rate limiter import
def get_api_rate_limiter():
    """Get API rate limiter instance"""
    try:
        from utility_functions.api_rate_limiter import APIRateLimiter
        return APIRateLimiter()
    except ImportError:
        logging.warning("API rate limiter not available")
        return None

# Error handling imports
def get_error_handler(service_name: str):
    """Get error handler instance"""
    try:
        from error_handler import ErrorHandler
        return ErrorHandler(service_name)
    except ImportError:
        logging.warning("Error handler not available")
        return None

def get_batch_processor(max_workers: int = 5, batch_size: int = 10):
    """Get batch processor instance"""
    try:
        from batch_processor import BatchProcessor
        return BatchProcessor(max_workers=max_workers, batch_size=batch_size)
    except ImportError:
        logging.warning("Batch processor not available")
        return None

def get_system_monitor():
    """Get system monitor instance"""
    try:
        from monitoring import system_monitor
        return system_monitor
    except ImportError:
        logging.warning("System monitor not available")
        return None

# Common error handling
def safe_get_numeric(data: Dict, key: str) -> Optional[float]:
    """Safely extract numeric value from dictionary"""
    try:
        value = data.get(key)
        if value is not None and value != '':
            return float(value)
        return None
    except (ValueError, TypeError):
        return None

def safe_get_value(df: pd.DataFrame, row_name: str, column) -> Optional[float]:
    """Safely extract value from pandas DataFrame"""
    try:
        if row_name in df.index and column in df.columns:
            value = df.loc[row_name, column]
            if pd.notna(value) and value != '':
                return float(value)
        return None
    except (ValueError, TypeError):
        return None

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    try:
        from monitoring import monitor_operation
        return monitor_operation(func.__name__)(func)
    except ImportError:
        return func

# Error handling decorator
def handle_errors(service_name: str = None):
    """Decorator to handle errors consistently"""
    try:
        from error_handler import error_handler
        return error_handler(service_name)
    except ImportError:
        def decorator(func):
            return func
        return decorator

# Retry decorator
def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry operations on failure"""
    try:
        from error_handler import retry_on_error
        return retry_on_error(max_retries=max_retries, delay=delay)
    except ImportError:
        def decorator(func):
            return func
        return decorator

# Service imports
try:
    from yahoo_finance_service import YahooFinanceService
    from alpha_vantage_service import AlphaVantageService
    from finnhub_service import FinnhubService
    from fmp_service import FMPService
except ImportError as e:
    logging.warning(f"Some service imports failed: {e}")
    # Create placeholder classes if imports fail
    class YahooFinanceService:
        def __init__(self): pass
    class AlphaVantageService:
        def __init__(self): pass
    class FinnhubService:
        def __init__(self): pass
    class FMPService:
        def __init__(self): pass 