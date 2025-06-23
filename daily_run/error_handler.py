#!/usr/bin/env python3
"""
Centralized Error Handling and Logging System
Provides consistent error handling, logging, and monitoring across all services
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from enum import Enum
import json

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """Error categories for better organization"""
    API_ERROR = "API_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"

class ServiceError(Exception):
    """Base exception for service-related errors"""
    def __init__(self, service: str, message: str, ticker: str = None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.SYSTEM_ERROR):
        self.service = service
        self.message = message
        self.ticker = ticker
        self.severity = severity
        self.category = category
        self.timestamp = datetime.now()
        super().__init__(f"{service}: {message}")

class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}_error_handler")
        self.error_counts = {}
        self.performance_metrics = {}
        
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle and log errors with context"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'service': self.service_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Determine severity and category
        if isinstance(error, ServiceError):
            severity = error.severity
            category = error.category
        else:
            severity, category = self._classify_error(error)
        
        error_info['severity'] = severity.value
        error_info['category'] = category.value
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {error_info}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY ERROR: {error_info}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY ERROR: {error_info}")
        else:
            self.logger.info(f"LOW SEVERITY ERROR: {error_info}")
        
        # Update error counts
        self._update_error_counts(category, severity)
        
        # Store error for monitoring
        self._store_error(error_info)
        
        return error_info
    
    def _classify_error(self, error: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
        """Classify error based on type and message"""
        error_str = str(error).lower()
        
        # Rate limiting errors
        if any(term in error_str for term in ['rate limit', 'too many requests', '429']):
            return ErrorSeverity.MEDIUM, ErrorCategory.RATE_LIMIT_ERROR
        
        # Network errors
        if any(term in error_str for term in ['timeout', 'connection', 'network']):
            return ErrorSeverity.HIGH, ErrorCategory.NETWORK_ERROR
        
        # Database errors
        if any(term in error_str for term in ['database', 'sql', 'psycopg2']):
            return ErrorSeverity.HIGH, ErrorCategory.DATABASE_ERROR
        
        # API errors
        if any(term in error_str for term in ['api', 'http', 'response']):
            return ErrorSeverity.MEDIUM, ErrorCategory.API_ERROR
        
        # Configuration errors
        if any(term in error_str for term in ['config', 'environment', 'key']):
            return ErrorSeverity.CRITICAL, ErrorCategory.CONFIGURATION_ERROR
        
        return ErrorSeverity.MEDIUM, ErrorCategory.SYSTEM_ERROR
    
    def _update_error_counts(self, category: ErrorCategory, severity: ErrorSeverity):
        """Update error count statistics"""
        key = f"{category.value}_{severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def _store_error(self, error_info: Dict[str, Any]):
        """Store error information for monitoring"""
        # This could be extended to store in database or external monitoring system
        pass
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors for monitoring"""
        return {
            'service': self.service_name,
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts,
            'performance_metrics': self.performance_metrics
        }
    
    def reset_metrics(self):
        """Reset error counts and performance metrics"""
        self.error_counts = {}
        self.performance_metrics = {}

def error_handler(service_name: str = None):
    """Decorator for automatic error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(service_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
                handler.handle_error(e, context)
                raise
        return wrapper
    return decorator

def performance_monitor(func: Callable) -> Callable:
    """Decorator for performance monitoring"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log performance metrics
            logger = logging.getLogger(f"{func.__module__}_performance")
            logger.info(f"Function {func.__name__} executed in {execution_time:.3f}s")
            
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger = logging.getLogger(f"{func.__module__}_performance")
            logger.error(f"Function {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper

def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for automatic retry on errors"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}, "
                                      f"retrying in {wait_time}s: {e}")
                        import time
                        time.sleep(wait_time)
            
            # All retries failed
            logging.error(f"All {max_retries} attempts failed for {func.__name__}: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator

# Global error handler instance
_global_error_handler = None

def get_global_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler("global")
    return _global_error_handler

def setup_error_logging(service_name: str, log_file: str = None):
    """Setup error logging for a service"""
    if log_file is None:
        log_file = f'logs/{service_name}_errors.log'
    
    # Create error-specific logger
    error_logger = logging.getLogger(f"{service_name}_errors")
    error_logger.setLevel(logging.INFO)
    
    # File handler for errors
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    error_logger.addHandler(file_handler)
    
    return error_logger 