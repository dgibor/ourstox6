#!/usr/bin/env python3
"""
System Monitoring and Health Check System
Provides comprehensive monitoring of system health, performance, and data quality
"""

import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
import json
from common_imports import psycopg2, DB_CONFIG, setup_logging
from error_handler import ErrorHandler

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    timestamp: datetime

@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time: float
    error_count: int
    last_check: datetime
    details: Dict[str, Any]

@dataclass
class DataQualityMetrics:
    """Data quality metrics"""
    total_records: int
    missing_data_count: int
    duplicate_count: int
    invalid_data_count: int
    last_updated: datetime
    data_freshness_hours: float

class SystemMonitor:
    """System monitoring and health check system"""
    
    def __init__(self):
        self.error_handler = ErrorHandler("system_monitor")
        self.logger = logging.getLogger("system_monitor")
        self.metrics_history: List[SystemMetrics] = []
        self.service_health: Dict[str, ServiceHealth] = {}
        self.max_history_size = 1000
        
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                timestamp=datetime.now()
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            self.error_handler.handle_error(e, {'operation': 'get_system_metrics'})
            raise
    
    def check_database_health(self) -> ServiceHealth:
        """Check database connection and performance"""
        start_time = time.time()
        status = "healthy"
        error_count = 0
        details = {}
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Test basic query
            cur.execute("SELECT 1")
            result = cur.fetchone()
            
            # Check connection pool
            cur.execute("SELECT count(*) FROM pg_stat_activity")
            active_connections = cur.fetchone()[0]
            
            # Check database size
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                       pg_database_size(current_database()) as db_size_bytes
            """)
            db_size_info = cur.fetchone()
            
            details = {
                'active_connections': active_connections,
                'database_size': db_size_info[0],
                'database_size_bytes': db_size_info[1]
            }
            
            cur.close()
            conn.close()
            
        except Exception as e:
            status = "unhealthy"
            error_count = 1
            details = {'error': str(e)}
            self.error_handler.handle_error(e, {'operation': 'check_database_health'})
        
        response_time = time.time() - start_time
        
        health = ServiceHealth(
            service_name="database",
            status=status,
            response_time=response_time,
            error_count=error_count,
            last_check=datetime.now(),
            details=details
        )
        
        self.service_health["database"] = health
        return health
    
    def record_metric(self, metric_name: str, value: float):
        """
        Record a custom metric for monitoring.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        try:
            # Store metric in a simple dictionary for now
            if not hasattr(self, '_custom_metrics'):
                self._custom_metrics = {}
            
            self._custom_metrics[metric_name] = {
                'value': value,
                'timestamp': datetime.now()
            }
            
            self.logger.debug(f"Recorded metric {metric_name}: {value}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {'operation': 'record_metric', 'metric_name': metric_name})
    
    def get_metric(self, metric_name: str) -> Optional[float]:
        """
        Get a recorded metric value.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Metric value or None if not found
        """
        try:
            if hasattr(self, '_custom_metrics') and metric_name in self._custom_metrics:
                return self._custom_metrics[metric_name]['value']
            return None
            
        except Exception as e:
            self.error_handler.handle_error(e, {'operation': 'get_metric', 'metric_name': metric_name})
            return None
    
    def check_api_service_health(self, service_name: str, test_func: callable) -> ServiceHealth:
        """Check health of an API service"""
        start_time = time.time()
        status = "healthy"
        error_count = 0
        details = {}
        
        try:
            result = test_func()
            details = {'test_result': result}
            
        except Exception as e:
            status = "unhealthy"
            error_count = 1
            details = {'error': str(e)}
            self.error_handler.handle_error(e, {'operation': f'check_{service_name}_health'})
        
        response_time = time.time() - start_time
        
        health = ServiceHealth(
            service_name=service_name,
            status=status,
            response_time=response_time,
            error_count=error_count,
            last_check=datetime.now(),
            details=details
        )
        
        self.service_health[service_name] = health
        return health
    
    def check_data_quality(self, table_name: str) -> DataQualityMetrics:
        """Check data quality for a specific table"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Get total records
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cur.fetchone()[0]
            
            # Check for missing data (NULL values in key columns)
            cur.execute(f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE ticker IS NULL OR ticker = ''
            """)
            missing_data_count = cur.fetchone()[0]
            
            # Check for duplicates
            cur.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT ticker, COUNT(*) 
                    FROM {table_name} 
                    GROUP BY ticker 
                    HAVING COUNT(*) > 1
                ) as duplicates
            """)
            duplicate_count = cur.fetchone()[0]
            
            # Check last update time
            cur.execute(f"""
                SELECT MAX(last_updated) FROM {table_name}
            """)
            last_updated_result = cur.fetchone()
            last_updated = last_updated_result[0] if last_updated_result[0] else datetime.now()
            
            data_freshness_hours = (datetime.now() - last_updated).total_seconds() / 3600
            
            # Check for invalid data based on table structure
            if table_name == 'stocks':
                # Check for negative values in stocks table columns
                cur.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE market_cap < 0 OR revenue_ttm < 0 OR net_income_ttm < 0
                """)
                invalid_data_count = cur.fetchone()[0]
            elif table_name == 'company_fundamentals':
                # Check for negative values in fundamentals table columns
                cur.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE revenue < 0 OR net_income < 0 OR total_assets < 0
                """)
                invalid_data_count = cur.fetchone()[0]
            else:
                # Generic check for other tables - just check for negative market cap
                cur.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE market_cap < 0
                """)
                invalid_data_count = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return DataQualityMetrics(
                total_records=total_records,
                missing_data_count=missing_data_count,
                duplicate_count=duplicate_count,
                invalid_data_count=invalid_data_count,
                last_updated=last_updated,
                data_freshness_hours=data_freshness_hours
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, {'operation': 'check_data_quality', 'table': table_name})
            raise
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary"""
        try:
            # Get current system metrics
            current_metrics = self.get_system_metrics()
            
            # Check database health
            db_health = self.check_database_health()
            
            # Check data quality for main tables
            stocks_quality = self.check_data_quality('stocks')
            fundamentals_quality = self.check_data_quality('company_fundamentals')
            
            # Determine overall system status
            overall_status = "healthy"
            if (current_metrics.cpu_percent > 80 or 
                current_metrics.memory_percent > 90 or
                current_metrics.disk_usage_percent > 90 or
                db_health.status == "unhealthy"):
                overall_status = "degraded"
            
            if (current_metrics.cpu_percent > 95 or 
                current_metrics.memory_percent > 95 or
                current_metrics.disk_usage_percent > 95 or
                db_health.status == "unhealthy"):
                overall_status = "unhealthy"
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': overall_status,
                'system_metrics': asdict(current_metrics),
                'database_health': asdict(db_health),
                'data_quality': {
                    'stocks': asdict(stocks_quality),
                    'fundamentals': asdict(fundamentals_quality)
                },
                'service_health': {
                    name: asdict(health) for name, health in self.service_health.items()
                },
                'alerts': self._generate_alerts(current_metrics, db_health, stocks_quality, fundamentals_quality)
            }
            
            return summary
            
        except Exception as e:
            self.error_handler.handle_error(e, {'operation': 'get_system_health_summary'})
            raise
    
    def _generate_alerts(self, metrics: SystemMetrics, db_health: ServiceHealth, 
                        stocks_quality: DataQualityMetrics, 
                        fundamentals_quality: DataQualityMetrics) -> List[Dict[str, Any]]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        # System alerts
        if metrics.cpu_percent > 80:
            alerts.append({
                'level': 'warning',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics.memory_percent > 90:
            alerts.append({
                'level': 'critical',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics.disk_usage_percent > 90:
            alerts.append({
                'level': 'critical',
                'message': f'High disk usage: {metrics.disk_usage_percent:.1f}%',
                'timestamp': datetime.now().isoformat()
            })
        
        # Database alerts
        if db_health.status == "unhealthy":
            alerts.append({
                'level': 'critical',
                'message': 'Database connection unhealthy',
                'timestamp': datetime.now().isoformat()
            })
        
        # Data quality alerts
        if stocks_quality.data_freshness_hours > 24:
            alerts.append({
                'level': 'warning',
                'message': f'Stocks data is {stocks_quality.data_freshness_hours:.1f} hours old',
                'timestamp': datetime.now().isoformat()
            })
        
        if fundamentals_quality.data_freshness_hours > 168:  # 1 week
            alerts.append({
                'level': 'critical',
                'message': f'Fundamentals data is {fundamentals_quality.data_freshness_hours:.1f} hours old',
                'timestamp': datetime.now().isoformat()
            })
        
        if stocks_quality.missing_data_count > stocks_quality.total_records * 0.1:
            alerts.append({
                'level': 'warning',
                'message': f'High missing data rate in stocks table: {stocks_quality.missing_data_count} records',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def save_health_report(self, filename: str = None):
        """Save health report to file"""
        if filename is None:
            filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            summary = self.get_system_health_summary()
            
            with open(f"logs/{filename}", 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            self.logger.info(f"Health report saved to logs/{filename}")
            
        except Exception as e:
            self.error_handler.handle_error(e, {'operation': 'save_health_report'})
            raise

class PerformanceMonitor:
    """Performance monitoring for specific operations"""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
        self.error_handler = ErrorHandler("performance_monitor")
        self.logger = logging.getLogger("performance_monitor")
    
    def record_operation_time(self, operation: str, duration: float):
        """Record operation duration"""
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        
        self.operation_times[operation].append(duration)
        
        # Keep only last 100 measurements
        if len(self.operation_times[operation]) > 100:
            self.operation_times[operation].pop(0)
    
    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation"""
        if operation not in self.operation_times:
            return {}
        
        times = self.operation_times[operation]
        if not times:
            return {}
        
        return {
            'count': len(times),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'total_time': sum(times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations"""
        return {
            operation: self.get_operation_stats(operation)
            for operation in self.operation_times.keys()
        }

# Global instances
system_monitor = SystemMonitor()
performance_monitor = PerformanceMonitor()

def get_system_health() -> Dict[str, Any]:
    """Get current system health status"""
    return system_monitor.get_system_health_summary()

def monitor_operation(operation_name: str):
    """Decorator to monitor operation performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_operation_time(operation_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_operation_time(operation_name, duration)
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    setup_logging("monitoring")
    
    # Test monitoring system
    print("Testing System Monitor...")
    health = get_system_health()
    print(json.dumps(health, indent=2, default=str))
    
    # Save health report
    system_monitor.save_health_report() 