"""
Enhanced error handling and logging utilities.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Type
from datetime import datetime, timezone
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorTracker:
    """
    Error tracking and analysis utility.
    """
    
    def __init__(self):
        """Initialize error tracker."""
        self.errors = []
        self.error_counts = {}
        self.logger = logger
    
    def track_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        operation: str = None
    ) -> str:
        """Track an error with context."""
        error_id = f"err_{int(datetime.now(timezone.utc).timestamp())}"
        
        error_data = {
            "id": error_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "operation": operation,
            "context": context or {}
        }
        
        self.errors.append(error_data)
        
        # Update error counts
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log error
        self.logger.error(f"Error tracked [{error_id}]: {error_type} - {str(error)}")
        
        return error_id
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": len(self.errors),
            "error_counts": self.error_counts.copy(),
            "recent_errors": self.errors[-10:] if self.errors else []
        }
    
    def clear_errors(self) -> None:
        """Clear all tracked errors."""
        self.errors.clear()
        self.error_counts.clear()
        self.logger.info("Error tracking data cleared")


class RetryManager:
    """
    Retry logic manager with exponential backoff.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """Initialize retry manager."""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.logger = logger
    
    async def retry_async(
        self,
        func,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ):
        """Retry async function with exponential backoff."""
        import asyncio
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded for {func.__name__}")
                    break
                
                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                self.logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def retry_sync(
        self,
        func,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ):
        """Retry sync function with exponential backoff."""
        import time
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    self.logger.error(f"Max retries ({self.max_retries}) exceeded for {func.__name__}")
                    break
                
                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                self.logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay:.2f}s")
                time.sleep(delay)
        
        raise last_exception


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logger
    
    def call(self, func, *args, **kwargs):
        """Call function through circuit breaker."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return False
        
        return (datetime.now(timezone.utc).timestamp() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc).timestamp()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


# Global instances
error_tracker = ErrorTracker()
retry_manager = RetryManager()


def handle_errors(
    operation: str = None,
    track_errors: bool = True,
    reraise: bool = True
):
    """Decorator for error handling."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if track_errors:
                    error_tracker.track_error(
                        e,
                        context={"args": str(args), "kwargs": str(kwargs)},
                        operation=operation or func.__name__
                    )
                
                if reraise:
                    raise
                
                return None
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if track_errors:
                    error_tracker.track_error(
                        e,
                        context={"args": str(args), "kwargs": str(kwargs)},
                        operation=operation or func.__name__
                    )
                
                if reraise:
                    raise
                
                return None
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    retryable_exceptions: tuple = (Exception,)
):
    """Decorator for retry logic."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_manager.retry_async(
                func, *args,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return retry_manager.retry_sync(
                func, *args,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator


def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60
):
    """Decorator for circuit breaker pattern."""
    breaker = CircuitBreaker(failure_threshold, recovery_timeout)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator