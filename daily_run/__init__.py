"""
Daily Run Package

Financial trading system daily operations and services.
"""

__version__ = "1.0.0"
__author__ = "Trading System"

# Package-level imports for easier access
try:
    from .database import DatabaseManager
    from .error_handler import ErrorHandler
    from .monitoring import SystemMonitor
except ImportError:
    # Graceful fallback for development
    pass 