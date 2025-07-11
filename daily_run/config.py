#!/usr/bin/env python3
"""
Configuration Management

Provides centralized configuration management with environment-specific settings,
validation, and fallback mechanisms.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '5432')))
    dbname: str = field(default_factory=lambda: os.getenv('DB_NAME', 'ourstox'))
    user: str = field(default_factory=lambda: os.getenv('DB_USER', 'postgres'))
    password: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    
    # Connection pool settings
    min_connections: int = field(default_factory=lambda: int(os.getenv('DB_MIN_CONNECTIONS', '1')))
    max_connections: int = field(default_factory=lambda: int(os.getenv('DB_MAX_CONNECTIONS', '10')))
    connection_timeout: int = field(default_factory=lambda: int(os.getenv('DB_TIMEOUT', '30')))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for psycopg2"""
        return {
            'host': self.host,
            'port': self.port,
            'dbname': self.dbname,
            'user': self.user,
            'password': self.password,
            'connect_timeout': self.connection_timeout
        }


@dataclass
class APIConfig:
    """API configuration for external services"""
    # API Keys
    fmp_api_key: str = field(default_factory=lambda: os.getenv('FMP_API_KEY', ''))
    alpha_vantage_api_key: str = field(default_factory=lambda: os.getenv('ALPHA_VANTAGE_API_KEY', ''))
    finnhub_api_key: str = field(default_factory=lambda: os.getenv('FINNHUB_API_KEY', ''))
    polygon_api_key: str = field(default_factory=lambda: os.getenv('POLYGON_API_KEY', ''))
    
    # Rate Limits (requests per minute)
    fmp_rate_limit: int = field(default_factory=lambda: int(os.getenv('FMP_RATE_LIMIT', '250')))
    alpha_vantage_rate_limit: int = field(default_factory=lambda: int(os.getenv('ALPHA_VANTAGE_RATE_LIMIT', '5')))
    finnhub_rate_limit: int = field(default_factory=lambda: int(os.getenv('FINNHUB_RATE_LIMIT', '60')))
    polygon_rate_limit: int = field(default_factory=lambda: int(os.getenv('POLYGON_RATE_LIMIT', '100')))
    
    # Timeout settings
    request_timeout: int = field(default_factory=lambda: int(os.getenv('API_REQUEST_TIMEOUT', '30')))
    max_retries: int = field(default_factory=lambda: int(os.getenv('API_MAX_RETRIES', '3')))
    
    # Daily usage limits
    daily_api_limit: int = field(default_factory=lambda: int(os.getenv('DAILY_API_LIMIT', '1000')))
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a specific service"""
        return getattr(self, f'{service.lower()}_api_key', '')
    
    def get_rate_limit(self, service: str) -> int:
        """Get rate limit for a specific service"""
        return getattr(self, f'{service.lower()}_rate_limit', 60)


@dataclass
class ProcessingConfig:
    """Processing configuration"""
    # Batch processing
    max_batch_size: int = field(default_factory=lambda: int(os.getenv('MAX_BATCH_SIZE', '100')))
    max_workers: int = field(default_factory=lambda: int(os.getenv('MAX_WORKERS', '5')))
    batch_delay: float = field(default_factory=lambda: float(os.getenv('BATCH_DELAY', '1.0')))
    
    # Circuit breaker settings
    circuit_failure_threshold: int = field(default_factory=lambda: int(os.getenv('CIRCUIT_FAILURE_THRESHOLD', '5')))
    circuit_recovery_timeout: int = field(default_factory=lambda: int(os.getenv('CIRCUIT_RECOVERY_TIMEOUT', '60')))
    
    # Data validation
    enable_data_validation: bool = field(default_factory=lambda: os.getenv('ENABLE_DATA_VALIDATION', 'true').lower() == 'true')
    data_quality_threshold: float = field(default_factory=lambda: float(os.getenv('DATA_QUALITY_THRESHOLD', '0.7')))
    
    # Historical data
    min_historical_days: int = field(default_factory=lambda: int(os.getenv('MIN_HISTORICAL_DAYS', '100')))
    historical_batch_size: int = field(default_factory=lambda: int(os.getenv('HISTORICAL_BATCH_SIZE', '10')))
    
    # Fundamental data
    fundamental_update_days: int = field(default_factory=lambda: int(os.getenv('FUNDAMENTAL_UPDATE_DAYS', '30')))
    earnings_window_days: int = field(default_factory=lambda: int(os.getenv('EARNINGS_WINDOW_DAYS', '7')))


@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_file: str = field(default_factory=lambda: os.getenv('LOG_FILE', 'daily_run/logs/system.log'))
    max_log_size: int = field(default_factory=lambda: int(os.getenv('MAX_LOG_SIZE', '10485760')))  # 10MB
    log_backup_count: int = field(default_factory=lambda: int(os.getenv('LOG_BACKUP_COUNT', '5')))
    
    # Enable/disable specific loggers
    enable_performance_logging: bool = field(default_factory=lambda: os.getenv('ENABLE_PERFORMANCE_LOGGING', 'true').lower() == 'true')
    enable_sql_logging: bool = field(default_factory=lambda: os.getenv('ENABLE_SQL_LOGGING', 'false').lower() == 'true')
    enable_api_logging: bool = field(default_factory=lambda: os.getenv('ENABLE_API_LOGGING', 'true').lower() == 'true')


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    environment: str = field(default_factory=lambda: os.getenv('ENVIRONMENT', 'development'))
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    testing: bool = field(default_factory=lambda: os.getenv('TESTING', 'false').lower() == 'true')
    
    # Monitoring
    enable_monitoring: bool = field(default_factory=lambda: os.getenv('ENABLE_MONITORING', 'true').lower() == 'true')
    monitoring_interval: int = field(default_factory=lambda: int(os.getenv('MONITORING_INTERVAL', '60')))
    
    # Security
    enable_ssl: bool = field(default_factory=lambda: os.getenv('ENABLE_SSL', 'false').lower() == 'true')
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == 'production'
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == 'development'
    
    @property
    def is_testing(self) -> bool:
        return self.testing or self.environment.lower() == 'testing'


class Config:
    """
    Centralized configuration management.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.database = DatabaseConfig()
            self.api = APIConfig()
            self.processing = ProcessingConfig()
            self.logging = LoggingConfig()
            self.environment = EnvironmentConfig()
            self._validate_config()
            self._initialized = True
    
    def _validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        # Database validation
        if not self.database.host:
            errors.append("Database host is required")
        if not self.database.dbname:
            errors.append("Database name is required")
        if not self.database.user:
            errors.append("Database user is required")
        
        # API validation
        api_keys_present = sum([
            bool(self.api.fmp_api_key),
            bool(self.api.alpha_vantage_api_key),
            bool(self.api.finnhub_api_key),
            bool(self.api.polygon_api_key)
        ])
        
        if api_keys_present == 0:
            errors.append("At least one API key must be configured")
        
        # Processing validation
        if self.processing.max_batch_size <= 0:
            errors.append("Max batch size must be positive")
        if self.processing.max_workers <= 0:
            errors.append("Max workers must be positive")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            if self.environment.is_production:
                raise ValueError(error_msg)
            else:
                logger.warning("Configuration errors detected, continuing in development mode")
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Get database configuration dictionary"""
        instance = cls()
        return instance.database.to_dict()
    
    @classmethod
    def get_api_config(cls) -> APIConfig:
        """Get API configuration"""
        instance = cls()
        return instance.api
    
    @classmethod
    def get_processing_config(cls) -> ProcessingConfig:
        """Get processing configuration"""
        instance = cls()
        return instance.processing
    
    @classmethod
    def get_logging_config(cls) -> LoggingConfig:
        """Get logging configuration"""
        instance = cls()
        return instance.logging
    
    @classmethod
    def get_environment_config(cls) -> EnvironmentConfig:
        """Get environment configuration"""
        instance = cls()
        return instance.environment
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service"""
        return {
            'api_key': self.api.get_api_key(service_name),
            'rate_limit': self.api.get_rate_limit(service_name),
            'timeout': self.api.request_timeout,
            'max_retries': self.api.max_retries,
            'batch_size': self.processing.max_batch_size,
            'enable_circuit_breaker': True,
            'circuit_failure_threshold': self.processing.circuit_failure_threshold,
            'circuit_recovery_timeout': self.processing.circuit_recovery_timeout
        }
    
    def get_daily_limits(self) -> Dict[str, int]:
        """Get daily usage limits"""
        return {
            'total_api_calls': self.api.daily_api_limit,
            'batch_size': self.processing.max_batch_size,
            'max_workers': self.processing.max_workers,
            'historical_batch_size': self.processing.historical_batch_size
        }
    
    def override_for_testing(self, **kwargs):
        """Override configuration for testing"""
        if not self.environment.is_testing:
            logger.warning("Configuration override attempted in non-testing environment")
            return
        
        for key, value in kwargs.items():
            if '.' in key:
                # Handle nested attributes like 'api.fmp_api_key'
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
            else:
                setattr(self, key, value)
        
        logger.info(f"Configuration overridden for testing: {kwargs}")
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration to dictionary (excluding sensitive data)"""
        config_dict = {
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'dbname': self.database.dbname,
                'user': self.database.user,
                'min_connections': self.database.min_connections,
                'max_connections': self.database.max_connections,
                'connection_timeout': self.database.connection_timeout
            },
            'api': {
                'rate_limits': {
                    'fmp': self.api.fmp_rate_limit,
                    'alpha_vantage': self.api.alpha_vantage_rate_limit,
                    'finnhub': self.api.finnhub_rate_limit,
                    'polygon': self.api.polygon_rate_limit
                },
                'request_timeout': self.api.request_timeout,
                'max_retries': self.api.max_retries,
                'daily_api_limit': self.api.daily_api_limit,
                'api_keys_configured': {
                    'fmp': bool(self.api.fmp_api_key),
                    'alpha_vantage': bool(self.api.alpha_vantage_api_key),
                    'finnhub': bool(self.api.finnhub_api_key),
                    'polygon': bool(self.api.polygon_api_key)
                }
            },
            'processing': {
                'max_batch_size': self.processing.max_batch_size,
                'max_workers': self.processing.max_workers,
                'batch_delay': self.processing.batch_delay,
                'circuit_failure_threshold': self.processing.circuit_failure_threshold,
                'circuit_recovery_timeout': self.processing.circuit_recovery_timeout,
                'enable_data_validation': self.processing.enable_data_validation,
                'data_quality_threshold': self.processing.data_quality_threshold,
                'min_historical_days': self.processing.min_historical_days,
                'historical_batch_size': self.processing.historical_batch_size,
                'fundamental_update_days': self.processing.fundamental_update_days,
                'earnings_window_days': self.processing.earnings_window_days
            },
            'logging': {
                'log_level': self.logging.log_level,
                'log_file': self.logging.log_file,
                'max_log_size': self.logging.max_log_size,
                'log_backup_count': self.logging.log_backup_count,
                'enable_performance_logging': self.logging.enable_performance_logging,
                'enable_sql_logging': self.logging.enable_sql_logging,
                'enable_api_logging': self.logging.enable_api_logging
            },
            'environment': {
                'environment': self.environment.environment,
                'debug': self.environment.debug,
                'testing': self.environment.testing,
                'is_production': self.environment.is_production,
                'is_development': self.environment.is_development,
                'is_testing': self.environment.is_testing,
                'enable_monitoring': self.environment.enable_monitoring,
                'monitoring_interval': self.environment.monitoring_interval,
                'enable_ssl': self.environment.enable_ssl
            }
        }
        
        return config_dict


def get_config() -> Config:
    """Get global configuration instance"""
    return Config()


def setup_logging_from_config():
    """Setup logging based on configuration"""
    config = get_config()
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.logging.log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, config.logging.log_level.upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                config.logging.log_file,
                maxBytes=config.logging.max_log_size,
                backupCount=config.logging.log_backup_count
            )
        ]
    )
    
    # Configure specific loggers based on config
    if not config.logging.enable_sql_logging:
        logging.getLogger('psycopg2').setLevel(logging.WARNING)
    
    if not config.logging.enable_api_logging:
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info(f"Logging configured for {config.environment.environment} environment")


def print_config_summary():
    """Print a summary of current configuration"""
    config = get_config()
    
    print("🔧 Configuration Summary")
    print("=" * 50)
    print(f"Environment: {config.environment.environment}")
    print(f"Debug Mode: {config.environment.debug}")
    print(f"Database: {config.database.host}:{config.database.port}/{config.database.dbname}")
    print(f"API Keys Configured: {sum(config.export_config()['api']['api_keys_configured'].values())}/4")
    print(f"Batch Size: {config.processing.max_batch_size}")
    print(f"Max Workers: {config.processing.max_workers}")
    print(f"Daily API Limit: {config.api.daily_api_limit}")
    print(f"Data Validation: {'Enabled' if config.processing.enable_data_validation else 'Disabled'}")
    print(f"Monitoring: {'Enabled' if config.environment.enable_monitoring else 'Disabled'}")
    print("=" * 50)


if __name__ == "__main__":
    # Test configuration
    try:
        print_config_summary()
        
        # Test configuration export
        config = get_config()
        exported = config.export_config()
        print(f"\n📋 Configuration exported with {len(exported)} sections")
        
        # Test service-specific config
        fmp_config = config.get_service_config('fmp')
        print(f"FMP Service Config: {fmp_config}")
        
        print("\n✅ Configuration test completed successfully")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc() 