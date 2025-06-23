#!/usr/bin/env python3
"""
Centralized configuration management for daily_run module
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration for all daily_run components"""
    
    # Database configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    # API Keys
    API_KEYS = {
        'finnhub': os.getenv('FINNHUB_API_KEY'),
        'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
        'fmp': os.getenv('FMP_API_KEY')
    }
    
    # Rate limits (calls per minute)
    RATE_LIMITS = {
        'finnhub': 60,
        'alpha_vantage': 5,
        'fmp': 300,
        'yahoo': 100  # Conservative estimate
    }
    
    # Batch processing settings
    BATCH_SIZE = 500
    MAX_RETRIES = 2
    
    # Logging configuration
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    
    # File paths
    LOG_DIR = 'logs'
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        return cls.DB_CONFIG.copy()
    
    @classmethod
    def get_api_key(cls, service: str) -> str:
        """Get API key for specific service"""
        return cls.API_KEYS.get(service)
    
    @classmethod
    def get_rate_limit(cls, service: str) -> int:
        """Get rate limit for specific service"""
        return cls.RATE_LIMITS.get(service, 60)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
        required_env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        required_api_keys = ['FINNHUB_API_KEY', 'ALPHA_VANTAGE_API_KEY', 'FMP_API_KEY']
        all_ok = True
        
        for var in required_env_vars:
            if not os.getenv(var):
                print(f"❌ Missing required environment variable: {var}")
                all_ok = False
        for key in required_api_keys:
            if not os.getenv(key):
                print(f"❌ Missing required API key: {key}")
                all_ok = False
        if all_ok:
            print("✅ Configuration validation passed")
        return all_ok

def test_config():
    """Test configuration loading and validation"""
    print("🧪 Testing Configuration Management")
    print("=" * 40)
    
    # Test database config
    db_config = Config.get_db_config()
    print(f"Database Host: {db_config.get('host', 'Not set')}")
    print(f"Database Name: {db_config.get('dbname', 'Not set')}")
    
    # Test API keys
    for service in ['finnhub', 'alpha_vantage', 'fmp']:
        key = Config.get_api_key(service)
        status = "✅ Set" if key else "❌ Not set"
        print(f"{service.title()} API Key: {status}")
    
    # Test rate limits
    for service in ['finnhub', 'alpha_vantage', 'fmp', 'yahoo']:
        limit = Config.get_rate_limit(service)
        print(f"{service.title()} Rate Limit: {limit} calls/min")
    
    # Validate configuration
    Config.validate_config()

if __name__ == "__main__":
    test_config() 