"""
API Flow Manager

Intelligent API flow management to ensure smooth operation across all services
without hitting API limits. Manages service priority, fallbacks, and usage tracking.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json

from database import DatabaseManager
from error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status levels"""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    DISABLED = "disabled"


class DataType(Enum):
    """Types of data requests"""
    PRICING = "pricing"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    BATCH = "batch"


@dataclass
class ServiceMetrics:
    """Track service performance metrics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limited_calls: int = 0
    avg_response_time: float = 0.0
    last_call_time: Optional[datetime] = None
    last_error: Optional[str] = None
    status: ServiceStatus = ServiceStatus.ACTIVE


@dataclass
class APIFlowRule:
    """Rules for API flow management"""
    service_id: str
    data_type: DataType
    priority: int
    max_calls_per_minute: int
    max_calls_per_day: Optional[int]
    cost_per_call: float
    batch_size: int = 1
    fallback_delay: float = 1.0


class APIFlowManager:
    """
    Intelligent API flow manager that routes requests optimally
    across all available services based on:
    - API rate limits
    - Service reliability
    - Cost optimization
    - Data type requirements
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.error_handler = ErrorHandler("api_flow_manager")
        self.logger = logging.getLogger("api_flow_manager")
        
        # Service metrics tracking
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        
        # Flow rules configuration
        self.flow_rules = self._initialize_flow_rules()
        
        # Circuit breaker patterns
        self.circuit_breakers: Dict[str, Dict] = {}
        
        self.logger.info("✅ API Flow Manager initialized")
    
    def _initialize_flow_rules(self) -> Dict[DataType, List[APIFlowRule]]:
        """Initialize API flow rules for optimal service routing"""
        return {
            DataType.PRICING: [
                APIFlowRule(
                    service_id='yahoo',
                    data_type=DataType.PRICING,
                    priority=1,
                    max_calls_per_minute=60,
                    max_calls_per_day=None,
                    cost_per_call=0.0,
                    batch_size=100,
                    fallback_delay=0.5
                ),
                APIFlowRule(
                    service_id='fmp',
                    data_type=DataType.PRICING,
                    priority=2,
                    max_calls_per_minute=10,
                    max_calls_per_day=1000,
                    cost_per_call=0.001,
                    batch_size=50,
                    fallback_delay=6.0
                ),
                APIFlowRule(
                    service_id='polygon',
                    data_type=DataType.PRICING,
                    priority=3,
                    max_calls_per_minute=300,
                    max_calls_per_day=None,
                    cost_per_call=0.002,
                    batch_size=100,
                    fallback_delay=0.2
                ),
                APIFlowRule(
                    service_id='finnhub',
                    data_type=DataType.PRICING,
                    priority=4,
                    max_calls_per_minute=60,
                    max_calls_per_day=None,
                    cost_per_call=0.0,
                    batch_size=1,
                    fallback_delay=1.0
                ),
                APIFlowRule(
                    service_id='alpha_vantage',
                    data_type=DataType.PRICING,
                    priority=5,
                    max_calls_per_minute=5,
                    max_calls_per_day=100,
                    cost_per_call=0.0,
                    batch_size=1,
                    fallback_delay=12.0
                )
            ],
            
            DataType.FUNDAMENTALS: [
                APIFlowRule(
                    service_id='yahoo',
                    data_type=DataType.FUNDAMENTALS,
                    priority=1,
                    max_calls_per_minute=60,
                    max_calls_per_day=None,
                    cost_per_call=0.0,
                    batch_size=1,
                    fallback_delay=0.5
                ),
                APIFlowRule(
                    service_id='fmp',
                    data_type=DataType.FUNDAMENTALS,
                    priority=2,
                    max_calls_per_minute=10,
                    max_calls_per_day=1000,
                    cost_per_call=0.001,
                    batch_size=1,
                    fallback_delay=6.0
                ),
                APIFlowRule(
                    service_id='alpha_vantage',
                    data_type=DataType.FUNDAMENTALS,
                    priority=3,
                    max_calls_per_minute=5,
                    max_calls_per_day=100,
                    cost_per_call=0.0,
                    batch_size=1,
                    fallback_delay=12.0
                ),
                APIFlowRule(
                    service_id='polygon',
                    data_type=DataType.FUNDAMENTALS,
                    priority=4,
                    max_calls_per_minute=300,
                    max_calls_per_day=None,
                    cost_per_call=0.002,
                    batch_size=1,
                    fallback_delay=0.2
                ),
                APIFlowRule(
                    service_id='finnhub',
                    data_type=DataType.FUNDAMENTALS,
                    priority=5,
                    max_calls_per_minute=60,
                    max_calls_per_day=None,
                    cost_per_call=0.0,
                    batch_size=1,
                    fallback_delay=1.0
                )
            ],
            
            DataType.BATCH: [
                APIFlowRule(
                    service_id='yahoo',
                    data_type=DataType.BATCH,
                    priority=1,
                    max_calls_per_minute=60,
                    max_calls_per_day=None,
                    cost_per_call=0.0,
                    batch_size=100,
                    fallback_delay=0.5
                ),
                APIFlowRule(
                    service_id='fmp',
                    data_type=DataType.BATCH,
                    priority=2,
                    max_calls_per_minute=10,
                    max_calls_per_day=1000,
                    cost_per_call=0.001,
                    batch_size=50,
                    fallback_delay=6.0
                ),
                APIFlowRule(
                    service_id='polygon',
                    data_type=DataType.BATCH,
                    priority=3,
                    max_calls_per_minute=300,
                    max_calls_per_day=None,
                    cost_per_call=0.002,
                    batch_size=100,
                    fallback_delay=0.2
                )
            ]
        }
    
    def get_optimal_service(self, data_type: DataType, tickers_count: int = 1) -> Tuple[str, APIFlowRule]:
        """
        Get the optimal service for a request based on current conditions
        
        Args:
            data_type: Type of data requested
            tickers_count: Number of tickers to process
            
        Returns:
            Tuple of (service_id, flow_rule) or (None, None) if no service available
        """
        rules = self.flow_rules.get(data_type, [])
        
        for rule in sorted(rules, key=lambda r: r.priority):
            service_id = rule.service_id
            
            # Check if service is available
            if not self._is_service_available(service_id):
                continue
            
            # Check rate limits
            if not self._check_rate_limits(service_id, rule):
                continue
            
            # Check batch capabilities
            if tickers_count > 1 and rule.batch_size < tickers_count:
                # Service doesn't support required batch size
                continue
            
            # Check circuit breaker
            if self._is_circuit_breaker_open(service_id):
                continue
            
            self.logger.debug(f"Selected service '{service_id}' for {data_type.value} request")
            return service_id, rule
        
        self.logger.warning(f"No available service for {data_type.value} request")
        return None, None
    
    def record_api_call(self, service_id: str, success: bool, response_time: float = 0.0, error: str = None):
        """Record an API call for metrics and rate limiting"""
        if service_id not in self.service_metrics:
            self.service_metrics[service_id] = ServiceMetrics()
        
        metrics = self.service_metrics[service_id]
        metrics.total_calls += 1
        metrics.last_call_time = datetime.now()
        
        if success:
            metrics.successful_calls += 1
            metrics.status = ServiceStatus.ACTIVE
        else:
            metrics.failed_calls += 1
            if error and 'rate limit' in error.lower():
                metrics.rate_limited_calls += 1
                metrics.status = ServiceStatus.RATE_LIMITED
                self._activate_circuit_breaker(service_id, "rate_limit")
            else:
                metrics.last_error = error
                metrics.status = ServiceStatus.ERROR
        
        # Update average response time
        if response_time > 0:
            total_response_time = metrics.avg_response_time * (metrics.total_calls - 1) + response_time
            metrics.avg_response_time = total_response_time / metrics.total_calls
    
    def _is_service_available(self, service_id: str) -> bool:
        """Check if a service is available for use"""
        # Check if service is in the enhanced multi-service manager
        try:
            from enhanced_multi_service_manager import get_multi_service_manager
            manager = get_multi_service_manager()
            return service_id in manager.service_instances and manager.service_instances[service_id] is not None
        except Exception:
            return False
    
    def _check_rate_limits(self, service_id: str, rule: APIFlowRule) -> bool:
        """Check if service is within rate limits"""
        if service_id not in self.service_metrics:
            return True
        
        metrics = self.service_metrics[service_id]
        now = datetime.now()
        
        # Check minute limit
        if metrics.last_call_time:
            minute_ago = now - timedelta(minutes=1)
            if metrics.last_call_time > minute_ago:
                # Estimate calls in last minute (simplified)
                estimated_calls = min(metrics.total_calls, rule.max_calls_per_minute)
                if estimated_calls >= rule.max_calls_per_minute:
                    return False
        
        # Check daily limit
        if rule.max_calls_per_day:
            if metrics.last_call_time and metrics.last_call_time.date() == now.date():
                if metrics.total_calls >= rule.max_calls_per_day:
                    return False
        
        return True
    
    def _is_circuit_breaker_open(self, service_id: str) -> bool:
        """Check if circuit breaker is open for a service"""
        if service_id not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[service_id]
        
        # Check if cooldown period has passed
        if breaker['open_until'] and datetime.now() > breaker['open_until']:
            self.circuit_breakers[service_id]['open'] = False
            self.circuit_breakers[service_id]['open_until'] = None
            self.logger.info(f"Circuit breaker closed for {service_id}")
            return False
        
        return breaker.get('open', False)
    
    def _activate_circuit_breaker(self, service_id: str, reason: str):
        """Activate circuit breaker for a service"""
        cooldown_minutes = 5  # 5 minute cooldown
        
        self.circuit_breakers[service_id] = {
            'open': True,
            'reason': reason,
            'open_until': datetime.now() + timedelta(minutes=cooldown_minutes),
            'activated_at': datetime.now()
        }
        
        self.logger.warning(f"Circuit breaker activated for {service_id}: {reason}")
    
    def get_service_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report of all services"""
        report = {
            'timestamp': datetime.now(),
            'services': {},
            'flow_rules': {},
            'circuit_breakers': self.circuit_breakers
        }
        
        # Service metrics
        for service_id, metrics in self.service_metrics.items():
            success_rate = (metrics.successful_calls / metrics.total_calls * 100) if metrics.total_calls > 0 else 0
            
            report['services'][service_id] = {
                'status': metrics.status.value,
                'total_calls': metrics.total_calls,
                'success_rate': round(success_rate, 2),
                'failed_calls': metrics.failed_calls,
                'rate_limited_calls': metrics.rate_limited_calls,
                'avg_response_time': round(metrics.avg_response_time, 3),
                'last_call_time': metrics.last_call_time,
                'last_error': metrics.last_error,
                'available': self._is_service_available(service_id)
            }
        
        # Flow rules summary
        for data_type, rules in self.flow_rules.items():
            report['flow_rules'][data_type.value] = [
                {
                    'service_id': rule.service_id,
                    'priority': rule.priority,
                    'max_calls_per_minute': rule.max_calls_per_minute,
                    'batch_size': rule.batch_size,
                    'cost_per_call': rule.cost_per_call
                }
                for rule in rules
            ]
        
        return report
    
    def optimize_flow_rules(self):
        """Dynamically optimize flow rules based on performance metrics"""
        self.logger.info("Optimizing API flow rules based on performance metrics...")
        
        for data_type, rules in self.flow_rules.items():
            # Sort rules by actual performance (success rate + speed - cost)
            optimized_rules = []
            
            for rule in rules:
                service_id = rule.service_id
                if service_id in self.service_metrics:
                    metrics = self.service_metrics[service_id]
                    success_rate = (metrics.successful_calls / metrics.total_calls) if metrics.total_calls > 0 else 0
                    
                    # Calculate performance score
                    performance_score = (
                        success_rate * 0.5 +  # 50% weight on success rate
                        (1 / max(metrics.avg_response_time, 0.1)) * 0.3 +  # 30% weight on speed
                        (1 - rule.cost_per_call * 1000) * 0.2  # 20% weight on cost
                    )
                    
                    optimized_rules.append((performance_score, rule))
            
            # Re-prioritize rules based on performance
            optimized_rules.sort(key=lambda x: x[0], reverse=True)
            
            for i, (score, rule) in enumerate(optimized_rules, 1):
                rule.priority = i
                self.logger.debug(f"Updated {rule.service_id} priority to {i} for {data_type.value} (score: {score:.3f})")
    
    def get_flow_recommendations(self) -> List[str]:
        """Get recommendations for optimizing API flow"""
        recommendations = []
        
        for service_id, metrics in self.service_metrics.items():
            if metrics.total_calls > 10:  # Only analyze services with sufficient data
                success_rate = (metrics.successful_calls / metrics.total_calls) * 100
                
                if success_rate < 50:
                    recommendations.append(f"⚠️ {service_id} has low success rate ({success_rate:.1f}%) - consider investigating")
                
                if metrics.rate_limited_calls > metrics.successful_calls:
                    recommendations.append(f"🚦 {service_id} is frequently rate limited - consider increasing delays")
                
                if metrics.avg_response_time > 5.0:
                    recommendations.append(f"🐌 {service_id} has slow response times ({metrics.avg_response_time:.1f}s) - consider lower priority")
        
        # Check for inactive services
        available_services = [sid for sid in ['yahoo', 'alpha_vantage', 'finnhub', 'polygon', 'fmp'] 
                            if self._is_service_available(sid)]
        
        if len(available_services) < 3:
            recommendations.append("⚠️ Less than 3 services available - consider adding more API keys for redundancy")
        
        return recommendations 