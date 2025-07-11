"""
Circuit Breaker Pattern Implementation

Provides circuit breakers for API services to handle failures gracefully
and prevent cascading failures in the system.
"""

import logging
import time
from typing import Dict, Optional, Callable, Any, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from error_handler import ErrorHandler, ErrorSeverity

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back


class CircuitBreaker:
    """
    Circuit breaker for a single service.
    """
    
    def __init__(self, service_name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 60, expected_exception: Exception = Exception):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        
        self.error_handler = ErrorHandler(f"circuit_breaker_{service_name}")
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
            Original exception: When function fails
        """
        self.total_requests += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker for {self.service_name} moving to HALF_OPEN")
            else:
                raise CircuitBreakerOpenException(f"Circuit breaker OPEN for {self.service_name}")
        
        try:
            # Execute the function
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Success - update state
            self._on_success(execution_time)
            return result
            
        except self.expected_exception as e:
            # Expected failure - update state
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected failure - still count as failure
            self._on_failure(e)
            raise
    
    def _on_success(self, execution_time: float):
        """Handle successful execution"""
        self.total_successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require 3 successes to close
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker for {self.service_name} CLOSED after recovery")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)
        
        logger.debug(f"Circuit breaker success for {self.service_name} "
                    f"(execution_time: {execution_time:.3f}s)")
    
    def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state goes back to open
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker for {self.service_name} back to OPEN after failure")
        elif self.failure_count >= self.failure_threshold:
            # Too many failures - open the circuit
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker for {self.service_name} OPENED after "
                        f"{self.failure_count} failures")
        
        self.error_handler.handle_error(
            f"Circuit breaker recorded failure for {self.service_name}", 
            exception, 
            ErrorSeverity.MEDIUM
        )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'service_name': self.service_name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_requests': self.total_requests,
            'total_failures': self.total_failures,
            'total_successes': self.total_successes,
            'success_rate': self.total_successes / self.total_requests if self.total_requests > 0 else 0,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker for {self.service_name} manually reset")


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different services.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_handler = ErrorHandler("circuit_breaker_manager")
    
    def get_circuit_breaker(self, service_name: str, failure_threshold: int = 5,
                          recovery_timeout: int = 60) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a service.
        
        Args:
            service_name: Name of the service
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting reset
            
        Returns:
            CircuitBreaker instance
        """
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                service_name=service_name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
            logger.info(f"Created circuit breaker for {service_name}")
        
        return self.circuit_breakers[service_name]
    
    def call_with_circuit_breaker(self, service_name: str, func: Callable, 
                                *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            service_name: Name of the service
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        return circuit_breaker.call(func, *args, **kwargs)
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {name: cb.get_state() for name, cb in self.circuit_breakers.items()}
    
    def get_healthy_services(self) -> List[str]:
        """Get list of services with closed circuit breakers"""
        return [name for name, cb in self.circuit_breakers.items() 
                if cb.state == CircuitState.CLOSED]
    
    def get_failed_services(self) -> List[str]:
        """Get list of services with open circuit breakers"""
        return [name for name, cb in self.circuit_breakers.items() 
                if cb.state == CircuitState.OPEN]
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for name, cb in self.circuit_breakers.items():
            cb.reset()
        logger.info("All circuit breakers reset")
    
    def reset_service(self, service_name: str):
        """Reset circuit breaker for a specific service"""
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name].reset()
        else:
            logger.warning(f"No circuit breaker found for service: {service_name}")


class ServiceFallbackManager:
    """
    Manages service fallbacks with circuit breaker integration.
    """
    
    def __init__(self, circuit_manager: CircuitBreakerManager):
        self.circuit_manager = circuit_manager
        self.error_handler = ErrorHandler("service_fallback_manager")
        
        # Define service priorities for different operations
        self.service_priorities = {
            'price_data': ['fmp', 'yahoo_finance', 'alpha_vantage', 'finnhub'],
            'fundamental_data': ['fmp', 'alpha_vantage', 'yahoo_finance'],
            'historical_data': ['yahoo_finance', 'fmp', 'alpha_vantage']
        }
    
    def execute_with_fallback(self, operation_type: str, service_functions: Dict[str, Callable],
                            *args, **kwargs) -> Tuple[Any, str]:
        """
        Execute an operation with automatic fallback to other services.
        
        Args:
            operation_type: Type of operation (price_data, fundamental_data, etc.)
            service_functions: Dict mapping service names to functions
            *args, **kwargs: Arguments for the functions
            
        Returns:
            Tuple of (result, service_name_used)
            
        Raises:
            Exception: If all services fail
        """
        if operation_type not in self.service_priorities:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        services_to_try = self.service_priorities[operation_type]
        
        # Filter to only available services
        available_services = [s for s in services_to_try if s in service_functions]
        
        # Prioritize healthy services
        healthy_services = self.circuit_manager.get_healthy_services()
        failed_services = self.circuit_manager.get_failed_services()
        
        # Reorder: healthy services first, then others
        ordered_services = []
        for service in available_services:
            if service in healthy_services:
                ordered_services.append(service)
        for service in available_services:
            if service not in healthy_services and service not in failed_services:
                ordered_services.append(service)
        for service in available_services:
            if service in failed_services:
                ordered_services.append(service)
        
        last_exception = None
        last_errors = {}
        
        for service_name in ordered_services:
            try:
                logger.debug(f"Trying {service_name} for {operation_type}")
                
                result = self.circuit_manager.call_with_circuit_breaker(
                    service_name, 
                    service_functions[service_name], 
                    *args, **kwargs
                )
                
                logger.info(f"Successfully executed {operation_type} with {service_name}")
                return result, service_name
                
            except CircuitBreakerOpenException:
                logger.warning(f"Circuit breaker open for {service_name}, trying next service")
                last_errors[service_name] = f"Circuit breaker OPEN for {service_name}"
                continue
            except Exception as e:
                logger.warning(f"Service {service_name} failed for {operation_type}: {e}")
                last_exception = e
                last_errors[service_name] = str(e)
                continue
        
        # All services failed
        error_msg = f"All services failed for {operation_type}"
        logger.error(f"{error_msg}. Last error: {last_exception}")
        
        # Fix error handler call - only pass required arguments
        if last_exception:
            self.error_handler.handle_error(error_msg, last_exception)
        else:
            self.error_handler.handle_error(error_msg, Exception("Unknown error"))
            
        # Return None instead of raising exception to prevent process termination
        return None, f"All services failed: {last_exception}"


# Global instances
circuit_manager = CircuitBreakerManager()
fallback_manager = ServiceFallbackManager(circuit_manager)


def circuit_breaker(service_name: str, failure_threshold: int = 5, 
                   recovery_timeout: int = 60):
    """
    Decorator for applying circuit breaker to functions.
    
    Args:
        service_name: Name of the service
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting reset
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return circuit_manager.call_with_circuit_breaker(
                service_name, func, *args, **kwargs
            )
        return wrapper
    return decorator


def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get status of all circuit breakers"""
    return {
        'circuit_breakers': circuit_manager.get_all_states(),
        'healthy_services': circuit_manager.get_healthy_services(),
        'failed_services': circuit_manager.get_failed_services()
    } 