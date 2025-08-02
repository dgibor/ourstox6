#!/usr/bin/env python3
"""
Improved Error Handling and Monitoring System

This script provides comprehensive error handling and monitoring for:
1. Technical indicator calculations
2. Historical data backfill
3. Database operations
4. API service failures
5. Data quality issues
"""

import os
import sys
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

# Add daily_run to path
sys.path.append('daily_run')

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    TECHNICAL_CALCULATION = "technical_calculation"
    HISTORICAL_DATA = "historical_data"
    DATABASE = "database"
    API_SERVICE = "api_service"
    DATA_QUALITY = "data_quality"
    SYSTEM = "system"

class ImprovedErrorHandler:
    """Improved error handling and monitoring system"""
    
    def __init__(self):
        self.error_log_file = Path("logs/error_monitoring.json")
        self.error_log_file.parent.mkdir(exist_ok=True)
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # Alert immediately
            ErrorSeverity.HIGH: 5,      # Alert after 5 errors
            ErrorSeverity.MEDIUM: 10,   # Alert after 10 errors
            ErrorSeverity.LOW: 20       # Alert after 20 errors
        }
        self.error_counts = {severity: 0 for severity in ErrorSeverity}
        self.recent_errors = []
        self.max_recent_errors = 100
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # File handler for all errors
        file_handler = logging.FileHandler('logs/error_monitoring.log')
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler for critical errors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Root logger configuration
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, 
                    message: str, 
                    error: Exception, 
                    severity: ErrorSeverity,
                    category: ErrorCategory,
                    context: Dict = None) -> Dict:
        """Handle an error with comprehensive logging and monitoring"""
        
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'severity': severity.value,
            'category': category.value,
            'context': context or {}
        }
        
        # Add to recent errors
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # Update error counts
        self.error_counts[severity] += 1
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {message} - {error}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY ERROR: {message} - {error}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY ERROR: {message} - {error}")
        else:
            self.logger.info(f"LOW SEVERITY ERROR: {message} - {error}")
        
        # Check if we need to send alerts
        self.check_alert_thresholds(severity)
        
        # Save error log
        self.save_error_log()
        
        return error_info
    
    def check_alert_thresholds(self, severity: ErrorSeverity):
        """Check if we need to send alerts based on error thresholds"""
        threshold = self.alert_thresholds[severity]
        current_count = self.error_counts[severity]
        
        if current_count >= threshold:
            self.send_alert(severity, current_count)
    
    def send_alert(self, severity: ErrorSeverity, count: int):
        """Send alert for error threshold exceeded"""
        alert_message = f"ALERT: {severity.value.upper()} errors exceeded threshold. Count: {count}"
        
        if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self.logger.critical(alert_message)
            # Here you could add email/SMS notifications
            print(f"🚨 {alert_message}")
        else:
            self.logger.warning(alert_message)
            print(f"⚠️ {alert_message}")
    
    def save_error_log(self):
        """Save error log to file"""
        error_data = {
            'last_updated': datetime.now().isoformat(),
            'error_counts': {severity.value: count for severity, count in self.error_counts.items()},
            'recent_errors': self.recent_errors[-20:]  # Keep last 20 errors
        }
        
        with open(self.error_log_file, 'w') as f:
            json.dump(error_data, f, indent=2)
    
    def get_error_summary(self) -> Dict:
        """Get summary of current error status"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': {severity.value: count for severity, count in self.error_counts.items()},
            'recent_error_count': len(self.recent_errors),
            'last_error': self.recent_errors[-1] if self.recent_errors else None
        }

class DataQualityMonitor:
    """Monitor data quality across the system"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.quality_thresholds = {
            'technical_indicators': 0.8,  # 80% coverage required
            'historical_data': 0.9,       # 90% coverage required
            'price_data': 0.95,           # 95% coverage required
            'fundamental_data': 0.7       # 70% coverage required
        }
    
    def check_technical_indicator_quality(self) -> Dict:
        """Check technical indicator data quality"""
        try:
            # Get overall technical indicator coverage
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN rsi_14 IS NOT NULL AND rsi_14 != 0 THEN 1 END) as rsi_count,
                COUNT(CASE WHEN ema_20 IS NOT NULL AND ema_20 != 0 THEN 1 END) as ema20_count,
                COUNT(CASE WHEN macd_line IS NOT NULL AND macd_line != 0 THEN 1 END) as macd_count
            FROM daily_charts
            WHERE close IS NOT NULL AND close != 0
            """
            
            result = self.db.fetch_one(query)
            if not result:
                return {'status': 'error', 'message': 'No data found'}
            
            total, rsi_count, ema20_count, macd_count = result
            
            # Calculate coverage percentages
            rsi_coverage = rsi_count / total if total > 0 else 0
            ema20_coverage = ema20_count / total if total > 0 else 0
            macd_coverage = macd_count / total if total > 0 else 0
            
            # Overall technical indicator quality
            overall_quality = (rsi_coverage + ema20_coverage + macd_coverage) / 3
            
            quality_report = {
                'status': 'success',
                'total_records': total,
                'rsi_coverage': rsi_coverage,
                'ema20_coverage': ema20_coverage,
                'macd_coverage': macd_coverage,
                'overall_quality': overall_quality,
                'meets_threshold': overall_quality >= self.quality_thresholds['technical_indicators'],
                'threshold': self.quality_thresholds['technical_indicators']
            }
            
            return quality_report
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_historical_data_quality(self) -> Dict:
        """Check historical data quality"""
        try:
            # Get tickers with insufficient historical data
            query = """
            SELECT 
                COUNT(DISTINCT s.ticker) as total_tickers,
                COUNT(DISTINCT CASE WHEN dc.day_count >= 100 THEN s.ticker END) as sufficient_data,
                COUNT(DISTINCT CASE WHEN dc.day_count < 100 THEN s.ticker END) as insufficient_data
            FROM stocks s
            LEFT JOIN (
                SELECT ticker, COUNT(*) as day_count
                FROM daily_charts
                GROUP BY ticker
            ) dc ON s.ticker = dc.ticker
            WHERE s.ticker IS NOT NULL
            """
            
            result = self.db.fetch_one(query)
            if not result:
                return {'status': 'error', 'message': 'No data found'}
            
            total_tickers, sufficient_data, insufficient_data = result
            
            # Calculate coverage
            coverage = sufficient_data / total_tickers if total_tickers > 0 else 0
            
            quality_report = {
                'status': 'success',
                'total_tickers': total_tickers,
                'sufficient_data': sufficient_data,
                'insufficient_data': insufficient_data,
                'coverage': coverage,
                'meets_threshold': coverage >= self.quality_thresholds['historical_data'],
                'threshold': self.quality_thresholds['historical_data']
            }
            
            return quality_report
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_price_data_quality(self) -> Dict:
        """Check price data quality"""
        try:
            # Get recent price data coverage (fixed SQL query)
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN close IS NOT NULL AND close != 0 THEN 1 END) as valid_prices,
                COUNT(CASE WHEN volume IS NOT NULL AND volume != 0 THEN 1 END) as valid_volumes
            FROM daily_charts
            WHERE date::date >= CURRENT_DATE - INTERVAL '7 days'
            """
            
            result = self.db.fetch_one(query)
            if not result:
                return {'status': 'error', 'message': 'No recent data found'}
            
            total, valid_prices, valid_volumes = result
            
            # Calculate coverage
            price_coverage = valid_prices / total if total > 0 else 0
            volume_coverage = valid_volumes / total if total > 0 else 0
            overall_coverage = (price_coverage + volume_coverage) / 2
            
            quality_report = {
                'status': 'success',
                'total_records': total,
                'price_coverage': price_coverage,
                'volume_coverage': volume_coverage,
                'overall_coverage': overall_coverage,
                'meets_threshold': overall_coverage >= self.quality_thresholds['price_data'],
                'threshold': self.quality_thresholds['price_data']
            }
            
            return quality_report
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def generate_quality_report(self) -> Dict:
        """Generate comprehensive data quality report"""
        technical_quality = self.check_technical_indicator_quality()
        historical_quality = self.check_historical_data_quality()
        price_quality = self.check_price_data_quality()
        
        # Calculate overall system health
        quality_scores = []
        if technical_quality['status'] == 'success':
            quality_scores.append(technical_quality['overall_quality'])
        if historical_quality['status'] == 'success':
            quality_scores.append(historical_quality['coverage'])
        if price_quality['status'] == 'success':
            quality_scores.append(price_quality['overall_coverage'])
        
        overall_health = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': overall_health,
            'technical_indicators': technical_quality,
            'historical_data': historical_quality,
            'price_data': price_quality,
            'recommendations': self.generate_recommendations(technical_quality, historical_quality, price_quality)
        }
        
        return report
    
    def generate_recommendations(self, technical_quality: Dict, historical_quality: Dict, price_quality: Dict) -> List[str]:
        """Generate recommendations based on quality issues"""
        recommendations = []
        
        if technical_quality['status'] == 'success' and not technical_quality['meets_threshold']:
            recommendations.append("Run technical indicator backfill to improve coverage")
        
        if historical_quality['status'] == 'success' and not historical_quality['meets_threshold']:
            recommendations.append("Run historical data backfill to ensure sufficient data for all tickers")
        
        if price_quality['status'] == 'success' and not price_quality['meets_threshold']:
            recommendations.append("Check price data fetching services for recent data issues")
        
        if not recommendations:
            recommendations.append("Data quality is within acceptable thresholds")
        
        return recommendations

class SystemMonitor:
    """Monitor overall system health and performance"""
    
    def __init__(self, error_handler: ImprovedErrorHandler, quality_monitor: DataQualityMonitor):
        self.error_handler = error_handler
        self.quality_monitor = quality_monitor
        self.monitoring_file = Path("logs/system_monitoring.json")
        self.monitoring_file.parent.mkdir(exist_ok=True)
    
    def run_system_health_check(self) -> Dict:
        """Run comprehensive system health check"""
        start_time = time.time()
        
        try:
            # Get error summary
            error_summary = self.error_handler.get_error_summary()
            
            # Get data quality report
            quality_report = self.quality_monitor.generate_quality_report()
            
            # Calculate system health score
            health_score = self.calculate_health_score(error_summary, quality_report)
            
            # Generate monitoring report
            monitoring_report = {
                'timestamp': datetime.now().isoformat(),
                'health_score': health_score,
                'error_summary': error_summary,
                'quality_report': quality_report,
                'check_duration': time.time() - start_time,
                'status': 'healthy' if health_score >= 0.8 else 'warning' if health_score >= 0.6 else 'critical'
            }
            
            # Save monitoring report
            self.save_monitoring_report(monitoring_report)
            
            return monitoring_report
            
        except Exception as e:
            self.error_handler.handle_error(
                "System health check failed",
                e,
                ErrorSeverity.HIGH,
                ErrorCategory.SYSTEM
            )
            return {
                'status': 'error',
                'error': str(e),
                'check_duration': time.time() - start_time
            }
    
    def calculate_health_score(self, error_summary: Dict, quality_report: Dict) -> float:
        """Calculate overall system health score (0-1)"""
        try:
            # Error score (lower is better)
            total_errors = error_summary['total_errors']
            error_score = max(0, 1 - (total_errors / 100))  # Penalize for errors
            
            # Quality score
            quality_score = quality_report.get('overall_health', 0)
            
            # Weighted average (quality more important than errors)
            health_score = (quality_score * 0.7) + (error_score * 0.3)
            
            return max(0, min(1, health_score))  # Ensure 0-1 range
            
        except Exception:
            return 0.5  # Default score if calculation fails
    
    def save_monitoring_report(self, report: Dict):
        """Save monitoring report to file"""
        with open(self.monitoring_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    def print_health_summary(self, report: Dict):
        """Print human-readable health summary"""
        print("\n" + "="*60)
        print("SYSTEM HEALTH MONITORING REPORT")
        print("="*60)
        print(f"Status: {report['status'].upper()}")
        print(f"Health Score: {report['health_score']:.2f}/1.00")
        print(f"Check Duration: {report['check_duration']:.2f} seconds")
        
        # Error summary
        error_summary = report['error_summary']
        print(f"\n📊 ERROR SUMMARY:")
        print(f"  Total Errors: {error_summary['total_errors']}")
        for severity, count in error_summary['error_counts'].items():
            if count > 0:
                print(f"  {severity.title()}: {count}")
        
        # Quality summary
        quality_report = report['quality_report']
        print(f"\n📈 DATA QUALITY:")
        print(f"  Technical Indicators: {quality_report['technical_indicators'].get('overall_quality', 0):.1%}")
        print(f"  Historical Data: {quality_report['historical_data'].get('coverage', 0):.1%}")
        print(f"  Price Data: {quality_report['price_data'].get('overall_coverage', 0):.1%}")
        
        # Recommendations
        recommendations = quality_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("="*60)

def main():
    """Main function to run system monitoring"""
    try:
        # Initialize components
        from database import DatabaseManager
        db = DatabaseManager()
        
        error_handler = ImprovedErrorHandler()
        quality_monitor = DataQualityMonitor(db)
        system_monitor = SystemMonitor(error_handler, quality_monitor)
        
        # Run system health check
        report = system_monitor.run_system_health_check()
        
        # Print summary
        system_monitor.print_health_summary(report)
        
        return report
        
    except Exception as e:
        print(f"❌ System monitoring failed: {e}")
        return {'status': 'error', 'error': str(e)}

if __name__ == "__main__":
    main() 