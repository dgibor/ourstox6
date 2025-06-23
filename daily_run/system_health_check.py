"""
System Health Check

Monitors the health of the daily trading system and provides status reports.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta

from common_imports import *
from database import DatabaseManager
from error_handler import ErrorHandler, ErrorSeverity
from monitoring import Monitoring
from enhanced_service_factory import EnhancedServiceFactory

logger = logging.getLogger(__name__)


class SystemHealthCheck:
    """
    Comprehensive system health monitoring for the daily trading system.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.error_handler = ErrorHandler()
        self.monitoring = Monitoring()
        self.service_factory = EnhancedServiceFactory()
        
        # Health thresholds
        self.thresholds = {
            'min_daily_prices': 100,  # Minimum daily prices expected
            'min_fundamentals': 50,   # Minimum fundamentals expected
            'max_api_errors': 10,     # Maximum API errors per day
            'max_processing_time': 3600,  # Maximum processing time (1 hour)
            'data_freshness_hours': 24  # Data should be fresh within 24 hours
        }
    
    def run_health_check(self) -> Dict:
        """
        Run comprehensive system health check.
        
        Returns:
            Dictionary with health check results
        """
        logger.info("🏥 Starting System Health Check")
        
        try:
            health_results = {
                'timestamp': datetime.now(),
                'overall_status': 'unknown',
                'checks': {}
            }
            
            # Run individual health checks
            health_results['checks']['database'] = self._check_database_health()
            health_results['checks']['api_services'] = self._check_api_services_health()
            health_results['checks']['data_quality'] = self._check_data_quality()
            health_results['checks']['system_performance'] = self._check_system_performance()
            health_results['checks']['recent_activity'] = self._check_recent_activity()
            health_results['checks']['error_analysis'] = self._check_error_analysis()
            
            # Determine overall status
            health_results['overall_status'] = self._determine_overall_status(health_results['checks'])
            
            # Generate alerts if needed
            alerts = self._generate_alerts(health_results['checks'])
            health_results['alerts'] = alerts
            
            # Update monitoring metrics
            self._update_monitoring_metrics(health_results)
            
            logger.info(f"✅ System Health Check completed - Status: {health_results['overall_status']}")
            return health_results
            
        except Exception as e:
            logger.error(f"❌ System health check failed: {e}")
            self.error_handler.handle_error(
                "System health check failed", e, ErrorSeverity.HIGH
            )
            return {
                'timestamp': datetime.now(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _check_database_health(self) -> Dict:
        """
        Check database connectivity and performance.
        """
        logger.info("🔍 Checking database health")
        
        try:
            start_time = time.time()
            
            # Test connection
            connection_test = self.db.test_connection()
            
            # Check response time
            response_time = time.time() - start_time
            
            # Check table sizes
            table_sizes = self._get_table_sizes()
            
            # Check for recent activity
            recent_activity = self._check_database_activity()
            
            result = {
                'status': 'healthy' if connection_test else 'unhealthy',
                'connection_test': connection_test,
                'response_time': response_time,
                'table_sizes': table_sizes,
                'recent_activity': recent_activity,
                'issues': []
            }
            
            # Check for issues
            if not connection_test:
                result['issues'].append('Database connection failed')
            
            if response_time > 5.0:  # More than 5 seconds
                result['issues'].append(f'Slow database response: {response_time:.2f}s')
            
            if not recent_activity['has_recent_updates']:
                result['issues'].append('No recent database updates')
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'issues': ['Database health check failed']
            }
    
    def _get_table_sizes(self) -> Dict:
        """
        Get sizes of key tables.
        """
        try:
            tables = ['stocks', 'daily_charts', 'company_fundamentals', 'financial_ratios']
            sizes = {}
            
            for table in tables:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.db.execute_query(query)
                sizes[table] = result[0][0] if result else 0
            
            return sizes
            
        except Exception as e:
            logger.error(f"Error getting table sizes: {e}")
            return {}
    
    def _check_database_activity(self) -> Dict:
        """
        Check for recent database activity.
        """
        try:
            today = date.today()
            
            # Check daily_charts for today's data
            query = "SELECT COUNT(*) as count FROM daily_charts WHERE date = %s"
            result = self.db.execute_query(query, (today,))
            today_prices = result[0][0] if result else 0
            
            # Check recent fundamental updates
            query = """
            SELECT COUNT(*) as count FROM company_fundamentals 
            WHERE DATE(created_at) = %s
            """
            result = self.db.execute_query(query, (today,))
            today_fundamentals = result[0][0] if result else 0
            
            return {
                'has_recent_updates': today_prices > 0 or today_fundamentals > 0,
                'today_prices': today_prices,
                'today_fundamentals': today_fundamentals
            }
            
        except Exception as e:
            logger.error(f"Error checking database activity: {e}")
            return {'has_recent_updates': False}
    
    def _check_api_services_health(self) -> Dict:
        """
        Check health of API services.
        """
        logger.info("🔍 Checking API services health")
        
        try:
            services = ['yahoo_finance', 'alpha_vantage', 'finnhub', 'fmp']
            service_health = {}
            
            for service_name in services:
                try:
                    service = self.service_factory.get_service(service_name)
                    
                    # Test service availability
                    test_result = self._test_service_availability(service, service_name)
                    service_health[service_name] = test_result
                    
                except Exception as e:
                    service_health[service_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Determine overall API health
            healthy_services = sum(1 for s in service_health.values() 
                                 if s.get('status') == 'healthy')
            
            result = {
                'status': 'healthy' if healthy_services >= 2 else 'degraded',
                'services': service_health,
                'healthy_count': healthy_services,
                'total_count': len(services)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking API services health: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _test_service_availability(self, service, service_name: str) -> Dict:
        """
        Test availability of a specific service.
        """
        try:
            # Test with a simple request
            if hasattr(service, 'get_current_price'):
                test_result = service.get_current_price('AAPL')
                return {
                    'status': 'healthy',
                    'response_time': 0.1,  # Placeholder
                    'test_result': 'success'
                }
            else:
                return {
                    'status': 'unknown',
                    'error': 'Service does not support price queries'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_data_quality(self) -> Dict:
        """
        Check quality of stored data.
        """
        logger.info("🔍 Checking data quality")
        
        try:
            issues = []
            
            # Check for missing data
            missing_data = self._check_missing_data()
            if missing_data['has_missing_data']:
                issues.append(f"Missing data: {missing_data['missing_count']} tickers")
            
            # Check for stale data
            stale_data = self._check_stale_data()
            if stale_data['has_stale_data']:
                issues.append(f"Stale data: {stale_data['stale_count']} tickers")
            
            # Check for data consistency
            consistency_issues = self._check_data_consistency()
            issues.extend(consistency_issues)
            
            result = {
                'status': 'healthy' if not issues else 'degraded',
                'issues': issues,
                'missing_data': missing_data,
                'stale_data': stale_data,
                'consistency_issues': consistency_issues
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_missing_data(self) -> Dict:
        """
        Check for missing data in key tables.
        """
        try:
            # Check stocks without recent prices
            query = """
            SELECT COUNT(*) as count FROM stocks s
            WHERE s.is_active = true 
            AND NOT EXISTS (
                SELECT 1 FROM daily_charts dc 
                WHERE dc.ticker = s.ticker 
                AND dc.date = %s
            )
            """
            result = self.db.execute_query(query, (date.today(),))
            missing_prices = result[0][0] if result else 0
            
            # Check stocks without fundamentals
            query = """
            SELECT COUNT(*) as count FROM stocks s
            WHERE s.is_active = true 
            AND NOT EXISTS (
                SELECT 1 FROM company_fundamentals cf 
                WHERE cf.ticker = s.ticker
            )
            """
            result = self.db.execute_query(query)
            missing_fundamentals = result[0][0] if result else 0
            
            return {
                'has_missing_data': missing_prices > 0 or missing_fundamentals > 0,
                'missing_prices': missing_prices,
                'missing_fundamentals': missing_fundamentals,
                'missing_count': missing_prices + missing_fundamentals
            }
            
        except Exception as e:
            logger.error(f"Error checking missing data: {e}")
            return {'has_missing_data': False, 'missing_count': 0}
    
    def _check_stale_data(self) -> Dict:
        """
        Check for stale data.
        """
        try:
            # Check for old price data
            stale_threshold = date.today() - timedelta(days=7)
            
            query = """
            SELECT COUNT(*) as count FROM stocks s
            WHERE s.is_active = true 
            AND NOT EXISTS (
                SELECT 1 FROM daily_charts dc 
                WHERE dc.ticker = s.ticker 
                AND dc.date > %s
            )
            """
            result = self.db.execute_query(query, (stale_threshold,))
            stale_prices = result[0][0] if result else 0
            
            return {
                'has_stale_data': stale_prices > 0,
                'stale_prices': stale_prices,
                'stale_count': stale_prices
            }
            
        except Exception as e:
            logger.error(f"Error checking stale data: {e}")
            return {'has_stale_data': False, 'stale_count': 0}
    
    def _check_data_consistency(self) -> List[str]:
        """
        Check for data consistency issues.
        """
        issues = []
        
        try:
            # Check for negative prices
            query = "SELECT COUNT(*) as count FROM daily_charts WHERE close_price < 0"
            result = self.db.execute_query(query)
            negative_prices = result[0][0] if result else 0
            
            if negative_prices > 0:
                issues.append(f"Negative prices found: {negative_prices}")
            
            # Check for zero prices
            query = "SELECT COUNT(*) as count FROM daily_charts WHERE close_price = 0"
            result = self.db.execute_query(query)
            zero_prices = result[0][0] if result else 0
            
            if zero_prices > 0:
                issues.append(f"Zero prices found: {zero_prices}")
            
            return issues
            
        except Exception as e:
            logger.error(f"Error checking data consistency: {e}")
            return [f"Data consistency check failed: {e}"]
    
    def _check_system_performance(self) -> Dict:
        """
        Check system performance metrics.
        """
        logger.info("🔍 Checking system performance")
        
        try:
            # Check recent processing times
            recent_times = self._get_recent_processing_times()
            
            # Check API call usage
            api_usage = self._get_api_usage_stats()
            
            # Check database performance
            db_performance = self._get_database_performance()
            
            result = {
                'status': 'healthy',
                'recent_processing_times': recent_times,
                'api_usage': api_usage,
                'database_performance': db_performance,
                'issues': []
            }
            
            # Check for performance issues
            if recent_times['avg_processing_time'] > self.thresholds['max_processing_time']:
                result['issues'].append('Slow processing times')
                result['status'] = 'degraded'
            
            if api_usage['daily_usage'] > 800:  # Near limit
                result['issues'].append('High API usage')
                result['status'] = 'degraded'
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking system performance: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_recent_processing_times(self) -> Dict:
        """
        Get recent processing times from monitoring.
        """
        try:
            # This would typically come from monitoring system
            # For now, return placeholder data
            return {
                'avg_processing_time': 1800,  # 30 minutes
                'max_processing_time': 3600,  # 1 hour
                'min_processing_time': 900    # 15 minutes
            }
            
        except Exception as e:
            logger.error(f"Error getting processing times: {e}")
            return {'avg_processing_time': 0}
    
    def _get_api_usage_stats(self) -> Dict:
        """
        Get API usage statistics.
        """
        try:
            # This would typically come from API monitoring
            # For now, return placeholder data
            return {
                'daily_usage': 500,
                'weekly_usage': 3500,
                'monthly_usage': 15000,
                'limits': {
                    'yahoo_finance': 1000,
                    'alpha_vantage': 500,
                    'finnhub': 1000,
                    'fmp': 1000
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting API usage stats: {e}")
            return {'daily_usage': 0}
    
    def _get_database_performance(self) -> Dict:
        """
        Get database performance metrics.
        """
        try:
            # Check database size and performance
            query = "SELECT pg_size_pretty(pg_database_size(current_database())) as size"
            result = self.db.execute_query(query)
            db_size = result[0][0] if result else 'Unknown'
            
            return {
                'database_size': db_size,
                'connection_count': 1,  # Placeholder
                'query_performance': 'good'
            }
            
        except Exception as e:
            logger.error(f"Error getting database performance: {e}")
            return {'database_size': 'Unknown'}
    
    def _check_recent_activity(self) -> Dict:
        """
        Check recent system activity.
        """
        logger.info("🔍 Checking recent activity")
        
        try:
            # Check last successful run
            last_run = self._get_last_successful_run()
            
            # Check recent errors
            recent_errors = self._get_recent_errors()
            
            # Check system uptime
            uptime = self._get_system_uptime()
            
            result = {
                'status': 'healthy',
                'last_successful_run': last_run,
                'recent_errors': recent_errors,
                'system_uptime': uptime,
                'issues': []
            }
            
            # Check for issues
            if not last_run['has_recent_run']:
                result['issues'].append('No recent successful runs')
                result['status'] = 'degraded'
            
            if recent_errors['error_count'] > self.thresholds['max_api_errors']:
                result['issues'].append(f'High error rate: {recent_errors["error_count"]} errors')
                result['status'] = 'degraded'
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking recent activity: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_last_successful_run(self) -> Dict:
        """
        Get information about the last successful run.
        """
        try:
            # Check for recent system status entries
            query = """
            SELECT created_at, status_data 
            FROM system_status 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            result = self.db.execute_query(query)
            
            if result:
                last_run_time = result[0][0]
                hours_since_run = (datetime.now() - last_run_time).total_seconds() / 3600
                
                return {
                    'has_recent_run': hours_since_run < self.thresholds['data_freshness_hours'],
                    'last_run_time': last_run_time,
                    'hours_since_run': hours_since_run
                }
            else:
                return {
                    'has_recent_run': False,
                    'last_run_time': None,
                    'hours_since_run': float('inf')
                }
                
        except Exception as e:
            logger.error(f"Error getting last successful run: {e}")
            return {'has_recent_run': False}
    
    def _get_recent_errors(self) -> Dict:
        """
        Get recent error statistics.
        """
        try:
            # This would typically come from error logging system
            # For now, return placeholder data
            return {
                'error_count': 5,
                'critical_errors': 0,
                'high_errors': 2,
                'medium_errors': 3,
                'low_errors': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return {'error_count': 0}
    
    def _get_system_uptime(self) -> Dict:
        """
        Get system uptime information.
        """
        try:
            import psutil
            
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = uptime_seconds / 3600
            
            return {
                'uptime_hours': uptime_hours,
                'uptime_days': uptime_hours / 24,
                'system_load': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting system uptime: {e}")
            return {'uptime_hours': 0}
    
    def _check_error_analysis(self) -> Dict:
        """
        Analyze recent errors and provide insights.
        """
        logger.info("🔍 Analyzing errors")
        
        try:
            # This would analyze error logs and provide insights
            # For now, return placeholder data
            return {
                'status': 'healthy',
                'error_trends': {
                    'increasing': False,
                    'decreasing': True,
                    'stable': False
                },
                'common_errors': [
                    'API rate limiting',
                    'Network timeout',
                    'Database connection issues'
                ],
                'recommendations': [
                    'Monitor API usage more closely',
                    'Implement better retry logic',
                    'Check network connectivity'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing errors: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _determine_overall_status(self, checks: Dict) -> str:
        """
        Determine overall system status based on individual checks.
        """
        status_counts = {'healthy': 0, 'degraded': 0, 'unhealthy': 0, 'error': 0}
        
        for check_name, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
        
        # Determine overall status
        if status_counts['error'] > 0:
            return 'error'
        elif status_counts['unhealthy'] > 0:
            return 'unhealthy'
        elif status_counts['degraded'] > 0:
            return 'degraded'
        else:
            return 'healthy'
    
    def _generate_alerts(self, checks: Dict) -> List[Dict]:
        """
        Generate alerts based on health check results.
        """
        alerts = []
        
        for check_name, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            
            if status in ['unhealthy', 'error']:
                alerts.append({
                    'level': 'critical',
                    'check': check_name,
                    'message': f'{check_name} is {status}',
                    'timestamp': datetime.now()
                })
            elif status == 'degraded':
                alerts.append({
                    'level': 'warning',
                    'check': check_name,
                    'message': f'{check_name} is degraded',
                    'timestamp': datetime.now()
                })
        
        return alerts
    
    def _update_monitoring_metrics(self, health_results: Dict):
        """
        Update monitoring system with health check results.
        """
        try:
            # Record overall status
            self.monitoring.record_metric('system_health_status', 
                                        health_results['overall_status'])
            
            # Record individual check statuses
            for check_name, check_result in health_results['checks'].items():
                status = check_result.get('status', 'unknown')
                self.monitoring.record_metric(f'health_check_{check_name}', status)
            
            # Record alert count
            alert_count = len(health_results.get('alerts', []))
            self.monitoring.record_metric('health_alerts_count', alert_count)
            
        except Exception as e:
            logger.error(f"Error updating monitoring metrics: {e}")


def main():
    """Main entry point for system health check."""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Health Check')
    parser.add_argument('--detailed', action='store_true', help='Show detailed results')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run health check
    health_checker = SystemHealthCheck()
    results = health_checker.run_health_check()
    
    # Output results
    if args.json:
        import json
        print(json.dumps(results, default=str, indent=2))
    else:
        print_health_results(results, detailed=args.detailed)


def print_health_results(results: Dict, detailed: bool = False):
    """
    Print health check results in a readable format.
    """
    print("🏥 SYSTEM HEALTH CHECK RESULTS")
    print("=" * 60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print()
    
    # Print alerts
    alerts = results.get('alerts', [])
    if alerts:
        print("🚨 ALERTS:")
        for alert in alerts:
            print(f"  {alert['level'].upper()}: {alert['message']}")
        print()
    
    # Print check results
    checks = results.get('checks', {})
    for check_name, check_result in checks.items():
        status = check_result.get('status', 'unknown')
        status_icon = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'error': '💥'
        }.get(status, '❓')
        
        print(f"{status_icon} {check_name.upper()}: {status}")
        
        if detailed and 'issues' in check_result:
            issues = check_result['issues']
            if issues:
                print("    Issues:")
                for issue in issues:
                    print(f"      - {issue}")
        
        if detailed and 'error' in check_result:
            print(f"    Error: {check_result['error']}")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main() 