#!/usr/bin/env python3
"""
API Usage Monitor
================

Comprehensive monitoring system for all API services with:
- Real-time usage tracking
- Rate limit monitoring
- Usage alerts and notifications
- Historical usage analytics
- Service health monitoring

Supported Services:
- Polygon.io
- Yahoo Finance
- Alpha Vantage
- Financial Modeling Prep (FMP)
- Finnhub

Author: AI Assistant
Date: 2025-01-26
"""

import os
import time
import logging
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
from pathlib import Path

from daily_run.common_imports import setup_logging, get_api_rate_limiter

# Setup logging
setup_logging('api_usage_monitor')
logger = logging.getLogger(__name__)

class APIUsageMonitor:
    """Comprehensive API usage monitoring system"""
    
    def __init__(self, db_path: str = "api_usage.db"):
        """Initialize the API usage monitor"""
        self.db_path = db_path
        self.api_limiter = get_api_rate_limiter()
        
        # Service configurations
        self.services = {
            'polygon': {
                'name': 'Polygon.io',
                'rate_limits': {
                    'basic': 5,      # calls per minute
                    'starter': 5,    # calls per second
                    'developer': 5,  # calls per second
                    'advanced': 10,  # calls per second
                    'enterprise': 50 # calls per second
                },
                'plan': 'starter',  # Default plan
                'cost_per_call': 0.001,  # Estimated cost per API call
                'daily_limit': 100000,   # Daily call limit
                'alert_threshold': 0.8   # Alert at 80% usage
            },
            'yahoo': {
                'name': 'Yahoo Finance',
                'rate_limits': {
                    'free': 1000  # calls per minute (estimated)
                },
                'plan': 'free',
                'cost_per_call': 0.0,
                'daily_limit': 1000000,
                'alert_threshold': 0.9
            },
            'alphavantage': {
                'name': 'Alpha Vantage',
                'rate_limits': {
                    'free': 5,     # calls per minute
                    'premium': 500 # calls per minute
                },
                'plan': 'free',
                'cost_per_call': 0.0,
                'daily_limit': 500,
                'alert_threshold': 0.8
            },
            'fmp': {
                'name': 'Financial Modeling Prep',
                'rate_limits': {
                    'basic': 250,    # calls per day
                    'premium': 1000, # calls per day
                    'enterprise': 10000 # calls per day
                },
                'plan': 'basic',
                'cost_per_call': 0.1,
                'daily_limit': 250,
                'alert_threshold': 0.8
            },
            'finnhub': {
                'name': 'Finnhub',
                'rate_limits': {
                    'free': 60,     # calls per minute
                    'premium': 1000 # calls per minute
                },
                'plan': 'free',
                'cost_per_call': 0.0,
                'daily_limit': 60000,
                'alert_threshold': 0.8
            }
        }
        
        # Initialize database
        self._init_database()
        
        # Load current usage
        self.current_usage = self._load_current_usage()
        
        logger.info("API Usage Monitor initialized")
    
    def _init_database(self):
        """Initialize the SQLite database for usage tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create usage tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    response_time REAL,
                    error_message TEXT,
                    cost REAL DEFAULT 0.0
                )
            ''')
            
            # Create daily usage summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_usage_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    date DATE NOT NULL,
                    total_calls INTEGER DEFAULT 0,
                    successful_calls INTEGER DEFAULT 0,
                    failed_calls INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    avg_response_time REAL DEFAULT 0.0,
                    UNIQUE(service, date)
                )
            ''')
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def record_api_call(self, service: str, endpoint: str = 'general', 
                       success: bool = True, response_time: float = None,
                       error_message: str = None):
        """Record an API call in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate cost
            cost = self._calculate_call_cost(service)
            
            cursor.execute('''
                INSERT INTO api_usage (service, endpoint, success, response_time, error_message, cost)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (service, endpoint, success, response_time, error_message, cost))
            
            conn.commit()
            conn.close()
            
            # Update current usage
            self._update_current_usage(service, success)
            
            # Check for alerts
            self._check_alerts(service)
            
        except Exception as e:
            logger.error(f"Error recording API call: {e}")
    
    def _calculate_call_cost(self, service: str) -> float:
        """Calculate the cost of an API call"""
        if service in self.services:
            return self.services[service].get('cost_per_call', 0.0)
        return 0.0
    
    def _update_current_usage(self, service: str, success: bool):
        """Update current usage statistics"""
        if service not in self.current_usage:
            self.current_usage[service] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_cost': 0.0,
                'last_call': None
            }
        
        self.current_usage[service]['total_calls'] += 1
        if success:
            self.current_usage[service]['successful_calls'] += 1
        else:
            self.current_usage[service]['failed_calls'] += 1
        
        self.current_usage[service]['total_cost'] += self._calculate_call_cost(service)
        self.current_usage[service]['last_call'] = datetime.now()
    
    def _load_current_usage(self) -> Dict[str, Dict]:
        """Load current usage from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get today's usage for each service
            today = date.today().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT service, 
                       SUM(total_calls) as total_calls,
                       SUM(successful_calls) as successful_calls,
                       SUM(failed_calls) as failed_calls,
                       SUM(total_cost) as total_cost
                FROM daily_usage_summary
                WHERE date = ?
                GROUP BY service
            ''', (today,))
            
            usage = {}
            for row in cursor.fetchall():
                service, total_calls, successful_calls, failed_calls, total_cost = row
                usage[service] = {
                    'total_calls': total_calls or 0,
                    'successful_calls': successful_calls or 0,
                    'failed_calls': failed_calls or 0,
                    'total_cost': total_cost or 0.0,
                    'last_call': None
                }
            
            conn.close()
            return usage
            
        except Exception as e:
            logger.error(f"Error loading current usage: {e}")
            return {}
    
    def _check_alerts(self, service: str):
        """Check for usage alerts"""
        try:
            if service not in self.services or service not in self.current_usage:
                return
            
            service_config = self.services[service]
            current_usage = self.current_usage[service]
            daily_limit = service_config.get('daily_limit', 1000)
            alert_threshold = service_config.get('alert_threshold', 0.8)
            
            # Check daily limit
            usage_percentage = current_usage['total_calls'] / daily_limit
            
            if usage_percentage >= alert_threshold:
                self._create_alert(service, 'usage_limit', 
                                 f"Usage at {usage_percentage:.1%} of daily limit ({current_usage['total_calls']}/{daily_limit})")
            
            # Check error rate
            if current_usage['total_calls'] > 10:
                error_rate = current_usage['failed_calls'] / current_usage['total_calls']
                if error_rate > 0.1:  # More than 10% errors
                    self._create_alert(service, 'error_rate', 
                                     f"High error rate: {error_rate:.1%} ({current_usage['failed_calls']}/{current_usage['total_calls']})")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _create_alert(self, service: str, alert_type: str, message: str):
        """Create an alert in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_alerts (service, alert_type, message)
                VALUES (?, ?, ?)
            ''', (service, alert_type, message))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"API Alert - {service}: {message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    def get_usage_summary(self, service: str = None, days: int = 7) -> Dict[str, Any]:
        """Get usage summary for specified service(s) and time period"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if service:
                # Get usage for specific service
                cursor.execute('''
                    SELECT date, total_calls, successful_calls, failed_calls, total_cost, avg_response_time
                    FROM daily_usage_summary
                    WHERE service = ? AND date >= date('now', '-{} days')
                    ORDER BY date DESC
                '''.format(days), (service,))
            else:
                # Get usage for all services
                cursor.execute('''
                    SELECT service, date, total_calls, successful_calls, failed_calls, total_cost, avg_response_time
                    FROM daily_usage_summary
                    WHERE date >= date('now', '-{} days')
                    ORDER BY service, date DESC
                '''.format(days))
            
            results = cursor.fetchall()
            conn.close()
            
            # Process results
            summary = {}
            for row in results:
                if service:
                    date_str, total_calls, successful_calls, failed_calls, total_cost, avg_response_time = row
                    if date_str not in summary:
                        summary[date_str] = {
                            'total_calls': total_calls or 0,
                            'successful_calls': successful_calls or 0,
                            'failed_calls': failed_calls or 0,
                            'total_cost': total_cost or 0.0,
                            'avg_response_time': avg_response_time or 0.0,
                            'success_rate': (successful_calls / total_calls * 100) if total_calls else 0
                        }
                else:
                    service_name, date_str, total_calls, successful_calls, failed_calls, total_cost, avg_response_time = row
                    if service_name not in summary:
                        summary[service_name] = {}
                    
                    summary[service_name][date_str] = {
                        'total_calls': total_calls or 0,
                        'successful_calls': successful_calls or 0,
                        'failed_calls': failed_calls or 0,
                        'total_cost': total_cost or 0.0,
                        'avg_response_time': avg_response_time or 0.0,
                        'success_rate': (successful_calls / total_calls * 100) if total_calls else 0
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {}
    
    def get_current_usage(self) -> Dict[str, Dict]:
        """Get current usage for all services"""
        return self.current_usage.copy()
    
    def get_service_health(self) -> Dict[str, Dict]:
        """Get health status for all services"""
        health = {}
        
        for service, config in self.services.items():
            current_usage = self.current_usage.get(service, {})
            daily_limit = config.get('daily_limit', 1000)
            
            total_calls = current_usage.get('total_calls', 0)
            successful_calls = current_usage.get('successful_calls', 0)
            failed_calls = current_usage.get('failed_calls', 0)
            
            usage_percentage = (total_calls / daily_limit * 100) if daily_limit > 0 else 0
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 100
            error_rate = (failed_calls / total_calls * 100) if total_calls > 0 else 0
            
            # Determine health status
            if usage_percentage >= 90:
                status = 'critical'
            elif usage_percentage >= 80:
                status = 'warning'
            elif error_rate >= 10:
                status = 'error'
            elif success_rate >= 95:
                status = 'healthy'
            else:
                status = 'degraded'
            
            health[service] = {
                'name': config['name'],
                'status': status,
                'usage_percentage': usage_percentage,
                'success_rate': success_rate,
                'error_rate': error_rate,
                'total_calls': total_calls,
                'daily_limit': daily_limit,
                'total_cost': current_usage.get('total_cost', 0.0),
                'last_call': current_usage.get('last_call')
            }
        
        return health
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT service, alert_type, message, timestamp
                FROM api_alerts
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
            ''')
            
            alerts = []
            for row in cursor.fetchall():
                service, alert_type, message, timestamp = row
                alerts.append({
                    'service': service,
                    'alert_type': alert_type,
                    'message': message,
                    'timestamp': timestamp
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE api_alerts
                SET resolved = TRUE
                WHERE id = ?
            ''', (alert_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
    
    def generate_daily_summary(self):
        """Generate daily usage summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = date.today().strftime('%Y-%m-%d')
            
            # Get today's usage for each service
            cursor.execute('''
                SELECT service, 
                       COUNT(*) as total_calls,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
                       SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_calls,
                       SUM(cost) as total_cost,
                       AVG(response_time) as avg_response_time
                FROM api_usage
                WHERE DATE(timestamp) = ?
                GROUP BY service
            ''', (today,))
            
            for row in cursor.fetchall():
                service, total_calls, successful_calls, failed_calls, total_cost, avg_response_time = row
                
                # Insert or update daily summary
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_usage_summary 
                    (service, date, total_calls, successful_calls, failed_calls, total_cost, avg_response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (service, today, total_calls, successful_calls, failed_calls, total_cost, avg_response_time))
            
            conn.commit()
            conn.close()
            
            logger.info("Daily usage summary generated")
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
    
    def print_usage_report(self, service: str = None):
        """Print a formatted usage report"""
        print("\n📊 API USAGE REPORT")
        print("=" * 60)
        
        # Get current usage
        current_usage = self.get_current_usage()
        health = self.get_service_health()
        
        if service:
            # Single service report
            if service in health:
                h = health[service]
                print(f"\n🔧 {h['name']} ({service.upper()})")
                print(f"  Status: {h['status'].upper()}")
                print(f"  Usage: {h['usage_percentage']:.1f}% ({h['total_calls']}/{h['daily_limit']})")
                print(f"  Success Rate: {h['success_rate']:.1f}%")
                print(f"  Error Rate: {h['error_rate']:.1f}%")
                print(f"  Total Cost: ${h['total_cost']:.2f}")
                if h['last_call']:
                    print(f"  Last Call: {h['last_call']}")
        else:
            # All services report
            for service_id, h in health.items():
                print(f"\n🔧 {h['name']} ({service_id.upper()})")
                print(f"  Status: {h['status'].upper()}")
                print(f"  Usage: {h['usage_percentage']:.1f}% ({h['total_calls']}/{h['daily_limit']})")
                print(f"  Success Rate: {h['success_rate']:.1f}%")
                print(f"  Total Cost: ${h['total_cost']:.2f}")
        
        # Show active alerts
        alerts = self.get_active_alerts()
        if alerts:
            print(f"\n⚠️  ACTIVE ALERTS ({len(alerts)})")
            print("-" * 40)
            for alert in alerts:
                print(f"  {alert['service'].upper()}: {alert['message']}")
                print(f"    Time: {alert['timestamp']}")
        else:
            print(f"\n✅ No active alerts")
        
        # Show 7-day summary
        print(f"\n📈 7-DAY USAGE SUMMARY")
        print("-" * 40)
        summary = self.get_usage_summary(days=7)
        
        if service:
            if service in summary:
                for date_str, data in summary[service].items():
                    print(f"  {date_str}: {data['total_calls']} calls, {data['success_rate']:.1f}% success")
        else:
            for service_id, dates in summary.items():
                total_calls = sum(data['total_calls'] for data in dates.values())
                total_cost = sum(data['total_cost'] for data in dates.values())
                print(f"  {service_id.upper()}: {total_calls} calls, ${total_cost:.2f} cost")

def main():
    """Test the API usage monitor"""
    try:
        # Initialize monitor
        monitor = APIUsageMonitor()
        
        print("🔧 Testing API Usage Monitor")
        print("=" * 50)
        
        # Simulate some API calls
        print("\n📊 Simulating API calls...")
        
        # Record some test calls
        monitor.record_api_call('polygon', 'fundamentals', True, 0.5)
        monitor.record_api_call('polygon', 'prices', True, 0.3)
        monitor.record_api_call('yahoo', 'fundamentals', True, 1.2)
        monitor.record_api_call('alphavantage', 'prices', False, 2.1, "Rate limit exceeded")
        monitor.record_api_call('fmp', 'fundamentals', True, 0.8)
        
        # Generate daily summary
        monitor.generate_daily_summary()
        
        # Print usage report
        monitor.print_usage_report()
        
        # Test service health
        print(f"\n🏥 SERVICE HEALTH")
        print("=" * 30)
        health = monitor.get_service_health()
        for service, status in health.items():
            print(f"  {service}: {status['status']} ({status['usage_percentage']:.1f}% usage)")
        
    except Exception as e:
        print(f"❌ Error testing API usage monitor: {e}")

if __name__ == "__main__":
    main() 