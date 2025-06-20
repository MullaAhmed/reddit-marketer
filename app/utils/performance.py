"""
Performance monitoring and optimization utilities.
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitoring utility for tracking execution times and resource usage.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}
        self.logger = logger
    
    def track_execution_time(self, operation_name: str):
        """Decorator to track execution time of functions."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self._record_metric(operation_name, execution_time, True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_metric(operation_name, execution_time, False)
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self._record_metric(operation_name, execution_time, True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_metric(operation_name, execution_time, False)
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _record_metric(self, operation_name: str, execution_time: float, success: bool):
        """Record performance metric."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "avg_time": 0.0
            }
        
        metric = self.metrics[operation_name]
        metric["total_calls"] += 1
        metric["total_time"] += execution_time
        metric["min_time"] = min(metric["min_time"], execution_time)
        metric["max_time"] = max(metric["max_time"], execution_time)
        metric["avg_time"] = metric["total_time"] / metric["total_calls"]
        
        if success:
            metric["successful_calls"] += 1
        else:
            metric["failed_calls"] += 1
        
        # Log slow operations
        if execution_time > 5.0:
            self.logger.warning(f"Slow operation '{operation_name}': {execution_time:.2f}s")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all performance metrics."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self.metrics.copy()
        }
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        self.metrics.clear()
        self.logger.info("Performance metrics reset")


class CacheManager:
    """
    Simple in-memory cache manager with TTL support.
    """
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache manager."""
        self.cache = {}
        self.default_ttl = default_ttl
        self.logger = logger
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        active_entries = sum(
            1 for _, expiry in self.cache.values()
            if current_time < expiry
        )
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_entries,
            "expired_entries": len(self.cache) - active_entries
        }


class RateLimiter:
    """
    Rate limiter for API calls and operations.
    """
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
        self.logger = logger
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier."""
        current_time = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(current_time)
            return True
        
        return False
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        current_time = time.time()
        
        if identifier not in self.requests:
            return self.max_requests
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.time_window
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        if identifier in self.requests:
            del self.requests[identifier]


# Global instances
performance_monitor = PerformanceMonitor()
cache_manager = CacheManager()
rate_limiter = RateLimiter()


def track_performance(operation_name: str):
    """Decorator for tracking performance."""
    return performance_monitor.track_execution_time(operation_name)


def cached(ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def rate_limited(identifier_func: Callable, max_requests: int = 100, time_window: int = 60):
    """Decorator for rate limiting."""
    limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            identifier = identifier_func(*args, **kwargs)
            if not limiter.is_allowed(identifier):
                raise Exception(f"Rate limit exceeded for {identifier}")
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            identifier = identifier_func(*args, **kwargs)
            if not limiter.is_allowed(identifier):
                raise Exception(f"Rate limit exceeded for {identifier}")
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator