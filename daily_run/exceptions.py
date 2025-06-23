#!/usr/bin/env python3
"""
Standardized exception handling for daily_run module
"""

class DailyRunError(Exception):
    """Base exception for daily_run module"""
    pass

class ServiceError(DailyRunError):
    """Base exception for service-related errors"""
    def __init__(self, service: str, message: str, ticker: str = None):
        self.service = service
        self.ticker = ticker
        super().__init__(f"{service}: {message}")

class RateLimitError(ServiceError):
    """Raised when API rate limit is exceeded"""
    def __init__(self, service: str, ticker: str = None):
        super().__init__(service, "Rate limit exceeded", ticker)

class DataNotFoundError(ServiceError):
    """Raised when no data is found for a ticker"""
    def __init__(self, service: str, ticker: str):
        super().__init__(service, f"No data found for {ticker}", ticker)

class InvalidTickerError(ServiceError):
    """Raised when ticker symbol is invalid"""
    def __init__(self, ticker: str):
        super().__init__("validation", f"Invalid ticker symbol: {ticker}", ticker)

class DatabaseError(DailyRunError):
    """Raised when database operations fail"""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"Database {operation}: {message}")

class ConfigurationError(DailyRunError):
    """Raised when configuration is invalid or missing"""
    def __init__(self, missing_item: str):
        super().__init__(f"Configuration error: {missing_item}")

def handle_service_error(error: Exception, service: str, ticker: str = None) -> str:
    """Standardized error handling for services"""
    if isinstance(error, RateLimitError):
        return f"Rate limit exceeded for {service}"
    elif isinstance(error, DataNotFoundError):
        return f"No data available for {ticker} from {service}"
    elif isinstance(error, ServiceError):
        return str(error)
    else:
        return f"Unexpected error with {service}: {str(error)}"

def test_exceptions():
    """Test exception handling system"""
    print("🧪 Testing Exception Handling System")
    print("=" * 40)
    
    # Test ServiceError
    try:
        raise ServiceError("yahoo", "API timeout", "AAPL")
    except ServiceError as e:
        print(f"✅ ServiceError: {e}")
    
    # Test RateLimitError
    try:
        raise RateLimitError("finnhub", "AAPL")
    except RateLimitError as e:
        print(f"✅ RateLimitError: {e}")
    
    # Test DataNotFoundError
    try:
        raise DataNotFoundError("alpha_vantage", "INVALID")
    except DataNotFoundError as e:
        print(f"✅ DataNotFoundError: {e}")
    
    # Test InvalidTickerError
    try:
        raise InvalidTickerError("INVALID!")
    except InvalidTickerError as e:
        print(f"✅ InvalidTickerError: {e}")
    
    # Test DatabaseError
    try:
        raise DatabaseError("insert", "Connection failed")
    except DatabaseError as e:
        print(f"✅ DatabaseError: {e}")
    
    # Test ConfigurationError
    try:
        raise ConfigurationError("API_KEY")
    except ConfigurationError as e:
        print(f"✅ ConfigurationError: {e}")
    
    # Test error handler
    error_msg = handle_service_error(RateLimitError("yahoo"), "yahoo", "AAPL")
    print(f"✅ Error Handler: {error_msg}")
    
    print("✅ All exception tests passed!")

if __name__ == "__main__":
    test_exceptions() 