#!/usr/bin/env python3
"""
Standardized Logging Configuration for Daily Run System

Provides consistent logging format and configuration across all modules.
"""

import logging
import os
from datetime import datetime


def setup_logging(module_name: str, log_level: str = 'INFO') -> logging.Logger:
    """
    Set up standardized logging for a module.
    
    Args:
        module_name: Name of the module requesting logging
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(module_name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # File handler (detailed format)
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(
        os.path.join(logs_dir, f'daily_run_{today}.log'),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        module_name: Name of the module requesting logging
        
    Returns:
        Logger instance
    """
    return logging.getLogger(module_name)


# Standard log message formats
class LogFormats:
    """Standardized log message formats for consistency"""
    
    # System status
    SYSTEM_START = "🚀 Starting {system_name}"
    SYSTEM_COMPLETE = "✅ {system_name} completed successfully"
    SYSTEM_FAILED = "❌ {system_name} failed: {error}"
    
    # Progress indicators
    PROGRESS = "📊 [{current}/{total}] {message}"
    PROGRESS_PERCENT = "📊 Progress: {current}/{total} ({percent:.1f}%)"
    
    # Status indicators
    SUCCESS = "✅ {message}"
    WARNING = "⚠️ {message}"
    ERROR = "❌ {message}"
    INFO = "📋 {message}"
    DEBUG = "🔍 {message}"
    
    # Data processing
    DATA_PROCESSING = "📈 Processing {data_type} for {ticker}"
    DATA_SUCCESS = "✅ {ticker}: {message}"
    DATA_FAILED = "❌ {ticker}: {message}"
    
    # API operations
    API_CALL = "🌐 API call to {service} for {ticker}"
    API_SUCCESS = "✅ {service} API call successful for {ticker}"
    API_FAILED = "❌ {service} API call failed for {ticker}: {error}"
    
    # Database operations
    DB_OPERATION = "💾 Database {operation} for {ticker}"
    DB_SUCCESS = "✅ Database {operation} successful for {ticker}"
    DB_FAILED = "❌ Database {operation} failed for {ticker}: {error}"
    
    # Time tracking
    TIME_ELAPSED = "⏱️ {operation} completed in {time:.2f}s"
    TIME_ETA = "⏱️ ETA: {eta:.1f} minutes"
    
    # Priority levels
    PRIORITY_START = "🎯 PRIORITY {level}: {description}"
    PRIORITY_COMPLETE = "✅ PRIORITY {level} completed: {description}"
    PRIORITY_SKIP = "⏭️ PRIORITY {level} skipped: {reason}"
    
    # Step indicators
    STEP_START = "📋 STEP {number}: {description}"
    STEP_COMPLETE = "✅ STEP {number} completed: {description}"
    STEP_FAILED = "❌ STEP {number} failed: {description}"


def log_system_start(logger: logging.Logger, system_name: str):
    """Log system start with standardized format"""
    logger.info(LogFormats.SYSTEM_START.format(system_name=system_name))


def log_system_complete(logger: logging.Logger, system_name: str):
    """Log system completion with standardized format"""
    logger.info(LogFormats.SYSTEM_COMPLETE.format(system_name=system_name))


def log_system_failed(logger: logging.Logger, system_name: str, error: str):
    """Log system failure with standardized format"""
    logger.error(LogFormats.SYSTEM_FAILED.format(system_name=system_name, error=error))


def log_progress(logger: logging.Logger, current: int, total: int, message: str):
    """Log progress with standardized format"""
    logger.info(LogFormats.PROGRESS.format(current=current, total=total, message=message))


def log_success(logger: logging.Logger, message: str):
    """Log success with standardized format"""
    logger.info(LogFormats.SUCCESS.format(message=message))


def log_warning(logger: logging.Logger, message: str):
    """Log warning with standardized format"""
    logger.warning(LogFormats.WARNING.format(message=message))


def log_error(logger: logging.Logger, message: str):
    """Log error with standardized format"""
    logger.error(LogFormats.ERROR.format(message=message))


def log_info(logger: logging.Logger, message: str):
    """Log info with standardized format"""
    logger.info(LogFormats.INFO.format(message=message))


def log_debug(logger: logging.Logger, message: str):
    """Log debug with standardized format"""
    logger.debug(LogFormats.DEBUG.format(message=message))
