#!/usr/bin/env python3
"""
Advanced Rate Limiting System for Financial Data APIs
Optimized for FMP Starter membership and multi-service architecture
"""

import os
import time
import logging
import psycopg2
from datetime import datetime, timedelta, date
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from threading import Lock
import json

# Setup logging
logger = logging.getLogger(__name__)

class ServiceTier(Enum):
    """Service subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class RateLimitConfig:
    """Rate limit configuration for a service"""
    daily_limit: int
    minute_limit: int
    second_limit: int
    batch_size: int
    tier: ServiceTier
    cost_per_call: float
    reset_time: str = "00:00"  # UTC reset time
    retry_delay: float = 1.0
    max_retries: int = 3

class AdvancedRateLimiter:
    """
    Advanced rate limiting system with daily quota management,
    batch processing optimization, and intelligent retry logic
    """
    
    def __init__(self, db_config: Dict = None):
        """Initialize the advanced rate limiter"""
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Service configurations based on research
        self.service_configs = {
            'fmp': RateLimitConfig(
                daily_limit=1000,      # FMP Starter: 1000 calls/day
                minute_limit=300,      # 5 calls/second = 300/minute
                second_limit=5,        # 5 calls per second
                batch_size=100,        # Up to 100 symbols per batch call
                tier=ServiceTier.PREMIUM,
                cost_per_call=0.02,    # $19.99 / 1000 calls
                retry_delay=0.2,       # 200ms between calls
                max_retries=3
            ),
            'yahoo': RateLimitConfig(
                daily_limit=2000,      # Conservative estimate
                minute_limit=100,      # Conservative estimate
                second_limit=1,        # 1 call per second
                batch_size=1,          # No batch support
                tier=ServiceTier.FREE,
                cost_per_call=0.0,
                retry_delay=1.0,       # 1 second between calls
                max_retries=3
            ),
            'finnhub': RateLimitConfig(
                daily_limit=60000,     # Free tier: 60,000 calls/day
                minute_limit=60,       # 60 calls per minute
                second_limit=1,        # 1 call per second
                batch_size=1,          # No batch support
                tier=ServiceTier.FREE,
                cost_per_call=0.0,
                retry_delay=1.0,
                max_retries=3
            ),
            'alpha_vantage': RateLimitConfig(
                daily_limit=500,       # Free tier: 500 calls/day
                minute_limit=5,        # 5 calls per minute
                second_limit=1,        # 1 call per 12 seconds
                batch_size=1,          # No batch support
                tier=ServiceTier.FREE,
                cost_per_call=0.0,
                retry_delay=12.0,      # 12 seconds between calls
                max_retries=3
            ),
            'polygon': RateLimitConfig(
                daily_limit=300,       # 5 calls/min * 60 min * 24 hours
                minute_limit=5,        # 5 calls per minute
                second_limit=1,        # 1 call per second
                batch_size=1,          # No batch support
                tier=ServiceTier.FREE,
                cost_per_call=0.0,
                retry_delay=1.0,
                max_retries=3
            )
        }
        
        # Initialize database connection
        self.db_conn = None
        self.db_cursor = None
        self._init_database()
        
        # Thread safety
        self.locks = {service: Lock() for service in self.service_configs}
        
        # In-memory tracking for performance
        self.daily_usage = {}
        self.last_call_times = {}
        self.batch_queues = {}
        
        logger.info("Advanced Rate Limiter initialized")
    
    def _init_database(self):
        """Initialize database connection and create tables if needed"""
        try:
            self.db_conn = psycopg2.connect(**self.db_config)
            self.db_cursor = self.db_conn.cursor()
            
            # Create API usage tracking table
            self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_tracking (
                    id SERIAL PRIMARY KEY,
                    service VARCHAR(50) NOT NULL,
                    date DATE NOT NULL,
                    endpoint VARCHAR(100),
                    calls_made INTEGER DEFAULT 0,
                    calls_limit INTEGER NOT NULL,
                    total_cost DECIMAL(10,4) DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service, date, endpoint)
                )
            """)
            
            # Create rate limit alerts table
            self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limit_alerts (
                    id SERIAL PRIMARY KEY,
                    service VARCHAR(50) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    threshold_value DECIMAL(10,2),
                    current_value DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    is_resolved BOOLEAN DEFAULT FALSE
                )
            """)
            
            self.db_conn.commit()
            logger.info("Database tables initialized for rate limiting")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Fallback to in-memory only mode
            self.db_conn = None
            self.db_cursor = None
    
    def can_make_request(self, service: str, endpoint: str = "default") -> bool:
        """
        Check if we can make a request without exceeding limits
        
        Args:
            service: Service name (fmp, yahoo, etc.)
            endpoint: Specific endpoint being called
            
        Returns:
            True if request can be made, False otherwise
        """
        if service not in self.service_configs:
            logger.warning(f"Unknown service: {service}")
            return False
        
        config = self.service_configs[service]
        today = date.today()
        
        with self.locks[service]:
            # Check daily limit
            daily_key = f"{service}_{today}"
            daily_usage = self.daily_usage.get(daily_key, 0)
            
            if daily_usage >= config.daily_limit:
                logger.warning(f"Daily limit reached for {service}: {daily_usage}/{config.daily_limit}")
                self._create_alert(service, "daily_limit_exceeded", 
                                 f"Daily limit exceeded: {daily_usage}/{config.daily_limit}")
                return False
            
            # Check rate limiting
            last_call = self.last_call_times.get(service, 0)
            time_since_last = time.time() - last_call
            
            if time_since_last < (1.0 / config.second_limit):
                wait_time = (1.0 / config.second_limit) - time_since_last
                logger.debug(f"Rate limit for {service}, need to wait {wait_time:.2f}s")
                return False
            
            return True
    
    def record_request(self, service: str, endpoint: str = "default", 
                      batch_size: int = 1, success: bool = True) -> Dict[str, Any]:
        """
        Record an API request
        
        Args:
            service: Service name
            endpoint: Endpoint being called
            batch_size: Number of items in batch (for cost calculation)
            success: Whether the request was successful
            
        Returns:
            Dictionary with usage statistics
        """
        if service not in self.service_configs:
            return {}
        
        config = self.service_configs[service]
        today = date.today()
        
        with self.locks[service]:
            # Update in-memory tracking
            daily_key = f"{service}_{today}"
            self.daily_usage[daily_key] = self.daily_usage.get(daily_key, 0) + 1
            self.last_call_times[service] = time.time()
            
            # Calculate cost
            cost = config.cost_per_call * batch_size
            
            # Update database
            if self.db_cursor:
                try:
                    self.db_cursor.execute("""
                        INSERT INTO api_usage_tracking 
                        (service, date, endpoint, calls_made, calls_limit, total_cost)
                        VALUES (%s, %s, %s, 1, %s, %s)
                        ON CONFLICT (service, date, endpoint)
                        DO UPDATE SET 
                            calls_made = api_usage_tracking.calls_made + 1,
                            total_cost = api_usage_tracking.total_cost + %s,
                            updated_at = CURRENT_TIMESTAMP
                    """, (service, today, endpoint, config.daily_limit, cost, cost))
                    
                    self.db_conn.commit()
                except Exception as e:
                    logger.error(f"Failed to record API usage: {e}")
            
            # Check for alerts
            current_usage = self.daily_usage[daily_key]
            usage_percentage = current_usage / config.daily_limit
            
            if usage_percentage >= 0.8:  # 80% threshold
                self._create_alert(service, "usage_warning", 
                                 f"Usage at {usage_percentage:.1%}: {current_usage}/{config.daily_limit}")
            
            return {
                'service': service,
                'daily_usage': current_usage,
                'daily_limit': config.daily_limit,
                'usage_percentage': usage_percentage,
                'cost': cost,
                'batch_size': batch_size
            }
    
    def get_batch_size(self, service: str, available_quota: int = None) -> int:
        """
        Get optimal batch size for a service
        
        Args:
            service: Service name
            available_quota: Available daily quota (optional)
            
        Returns:
            Optimal batch size
        """
        if service not in self.service_configs:
            return 1
        
        config = self.service_configs[service]
        
        if available_quota is None:
            today = date.today()
            daily_key = f"{service}_{today}"
            used = self.daily_usage.get(daily_key, 0)
            available_quota = config.daily_limit - used
        
        # For FMP, use batch processing when possible
        if service == 'fmp' and available_quota > 0:
            return min(config.batch_size, available_quota)
        
        return 1
    
    def wait_if_needed(self, service: str) -> float:
        """
        Wait if rate limiting is needed
        
        Args:
            service: Service name
            
        Returns:
            Time waited in seconds
        """
        if service not in self.service_configs:
            return 0.0
        
        config = self.service_configs[service]
        last_call = self.last_call_times.get(service, 0)
        time_since_last = time.time() - last_call
        required_interval = 1.0 / config.second_limit
        
        if time_since_last < required_interval:
            wait_time = required_interval - time_since_last
            logger.debug(f"Waiting {wait_time:.2f}s for {service} rate limit")
            time.sleep(wait_time)
            return wait_time
        
        return 0.0
    
    def get_usage_summary(self, service: str = None) -> Dict[str, Any]:
        """
        Get usage summary for service(s)
        
        Args:
            service: Specific service or None for all
            
        Returns:
            Usage summary dictionary
        """
        today = date.today()
        summary = {}
        
        services = [service] if service else self.service_configs.keys()
        
        for svc in services:
            if svc not in self.service_configs:
                continue
            
            config = self.service_configs[svc]
            daily_key = f"{svc}_{today}"
            used = self.daily_usage.get(daily_key, 0)
            
            summary[svc] = {
                'daily_used': used,
                'daily_limit': config.daily_limit,
                'usage_percentage': used / config.daily_limit,
                'remaining': config.daily_limit - used,
                'tier': config.tier.value,
                'cost_per_call': config.cost_per_call,
                'total_cost': used * config.cost_per_call
            }
        
        return summary if service else summary
    
    def optimize_batch_requests(self, service: str, tickers: List[str]) -> List[List[str]]:
        """
        Optimize batch requests for maximum efficiency
        
        Args:
            service: Service name
            tickers: List of tickers to process
            
        Returns:
            List of optimized batches
        """
        if service not in self.service_configs:
            return [[ticker] for ticker in tickers]
        
        config = self.service_configs[service]
        today = date.today()
        daily_key = f"{service}_{today}"
        used = self.daily_usage.get(daily_key, 0)
        remaining = config.daily_limit - used
        
        if remaining <= 0:
            logger.warning(f"No remaining quota for {service}")
            return []
        
        # Calculate optimal batch size
        optimal_batch_size = min(config.batch_size, remaining)
        
        if optimal_batch_size <= 1:
            return [[ticker] for ticker in tickers[:remaining]]
        
        # Create batches
        batches = []
        for i in range(0, len(tickers), optimal_batch_size):
            batch = tickers[i:i + optimal_batch_size]
            batches.append(batch)
            
            # Check if we have enough quota for this batch
            if len(batches) * optimal_batch_size > remaining:
                break
        
        logger.info(f"Created {len(batches)} batches for {service} with {optimal_batch_size} items per batch")
        return batches
    
    def _create_alert(self, service: str, alert_type: str, message: str, 
                     threshold_value: float = None, current_value: float = None):
        """Create a rate limit alert"""
        if self.db_cursor:
            try:
                self.db_cursor.execute("""
                    INSERT INTO rate_limit_alerts 
                    (service, alert_type, message, threshold_value, current_value)
                    VALUES (%s, %s, %s, %s, %s)
                """, (service, alert_type, message, threshold_value, current_value))
                self.db_conn.commit()
                logger.warning(f"Rate limit alert created: {service} - {alert_type}: {message}")
            except Exception as e:
                logger.error(f"Failed to create alert: {e}")
    
    def get_alerts(self, service: str = None, resolved: bool = False) -> List[Dict]:
        """Get rate limit alerts"""
        if not self.db_cursor:
            return []
        
        try:
            query = """
                SELECT service, alert_type, message, threshold_value, current_value, 
                       created_at, is_resolved
                FROM rate_limit_alerts
                WHERE is_resolved = %s
            """
            params = [resolved]
            
            if service:
                query += " AND service = %s"
                params.append(service)
            
            query += " ORDER BY created_at DESC"
            
            self.db_cursor.execute(query, params)
            alerts = []
            
            for row in self.db_cursor.fetchall():
                alerts.append({
                    'service': row[0],
                    'alert_type': row[1],
                    'message': row[2],
                    'threshold_value': row[3],
                    'current_value': row[4],
                    'created_at': row[5],
                    'is_resolved': row[6]
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
    
    def reset_daily_usage(self):
        """Reset daily usage counters (call at midnight UTC)"""
        today = date.today()
        for service in self.service_configs:
            daily_key = f"{service}_{today}"
            self.daily_usage[daily_key] = 0
        logger.info("Daily usage counters reset")
    
    def close(self):
        """Close database connections"""
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_conn:
            self.db_conn.close()
        logger.info("Advanced Rate Limiter closed")

# Global instance
_advanced_rate_limiter = None

def get_advanced_rate_limiter() -> AdvancedRateLimiter:
    """Get global advanced rate limiter instance"""
    global _advanced_rate_limiter
    if _advanced_rate_limiter is None:
        _advanced_rate_limiter = AdvancedRateLimiter()
    return _advanced_rate_limiter

def test_advanced_rate_limiter():
    """Test the advanced rate limiter"""
    print("🧪 Testing Advanced Rate Limiter")
    print("=" * 50)
    
    limiter = get_advanced_rate_limiter()
    
    # Test FMP configuration
    fmp_config = limiter.service_configs['fmp']
    print(f"FMP Daily Limit: {fmp_config.daily_limit}")
    print(f"FMP Batch Size: {fmp_config.batch_size}")
    print(f"FMP Cost per Call: ${fmp_config.cost_per_call}")
    
    # Test usage tracking
    print(f"\nCan make FMP request: {limiter.can_make_request('fmp')}")
    
    # Record a request
    usage = limiter.record_request('fmp', 'profile', batch_size=50)
    print(f"Usage after request: {usage}")
    
    # Test batch optimization
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'] * 20  # 100 tickers
    batches = limiter.optimize_batch_requests('fmp', tickers)
    print(f"Optimized batches: {len(batches)} batches")
    print(f"First batch size: {len(batches[0]) if batches else 0}")
    
    # Get usage summary
    summary = limiter.get_usage_summary('fmp')
    print(f"FMP Usage Summary: {summary}")
    
    print("\n✅ Advanced Rate Limiter test completed")

if __name__ == "__main__":
    test_advanced_rate_limiter() 