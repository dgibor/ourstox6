"""
Simple Error Handler Module

Provides basic error handling functionality for the daily trading system.
"""

import logging
from enum import Enum
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorHandler:
    """Simple error handler for logging and error management"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.logger = logging.getLogger(f"{module_name}.error_handler")
    
    def log_error(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR, 
                  exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        """Log an error with appropriate severity"""
        log_message = f"[{self.module_name}] {message}"
        
        if context:
            log_message += f" | Context: {context}"
        
        if exception:
            log_message += f" | Exception: {str(exception)}"
        
        if severity == ErrorSeverity.DEBUG:
            self.logger.debug(log_message)
        elif severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
    
    def handle_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Handle an exception with logging"""
        self.log_error(f"Exception occurred: {type(exception).__name__}", 
                      ErrorSeverity.ERROR, exception, context)
    
    def validate_data(self, data: Any, data_type: str) -> bool:
        """Validate data and log errors if invalid"""
        if data is None:
            self.log_error(f"Invalid {data_type}: data is None", ErrorSeverity.WARNING)
            return False
        
        if isinstance(data, (list, dict)) and len(data) == 0:
            self.log_error(f"Invalid {data_type}: data is empty", ErrorSeverity.WARNING)
            return False
        
        return True
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Handle an error with logging (alias for handle_exception)"""
        self.handle_exception(error, context) 