"""
Retry utilities with exponential backoff and intelligent error handling.

Features:
- Exponential backoff with jitter
- Different strategies for different error types
- Circuit breaker pattern
- Retry budget tracking
"""

import asyncio
import logging
import random
from typing import Callable, Optional, Type, Tuple
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                logger.info(f"Circuit breaker half-open for {func.__name__}")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker open for {func.__name__}. "
                    f"Retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable):
        """Execute async function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                logger.info(f"Circuit breaker half-open for {func.__name__}")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker open for {func.__name__}. "
                    f"Retry after {self.recovery_timeout}s"
                )
        
        try:
            result = await func()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        if self.state == "half_open":
            self.state = "closed"
            logger.info("Circuit breaker closed")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> float:
    """
    Calculate backoff delay with exponential growth and optional jitter.
    
    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential growth
        jitter: Add random jitter to prevent thundering herd
    
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        # Add jitter: random value between 0 and delay
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay


def should_retry_error(exception: Exception) -> Tuple[bool, float]:
    """
    Determine if error should be retried and with what base delay.
    
    Returns:
        (should_retry, base_delay)
    """
    error_str = str(exception).lower()
    
    # Rate limit errors - wait longer
    if "429" in error_str or "rate limit" in error_str:
        return True, 30.0
    
    # Timeout errors - retry with normal delay
    if "timeout" in error_str or "timed out" in error_str:
        return True, 2.0
    
    # Connection errors - retry quickly
    if "connection" in error_str or "network" in error_str:
        return True, 1.0
    
    # Server errors (5xx) - retry with moderate delay
    if any(code in error_str for code in ["500", "502", "503", "504"]):
        return True, 5.0
    
    # Client errors (4xx except 429) - don't retry
    if any(code in error_str for code in ["400", "401", "403", "404"]):
        return False, 0.0
    
    # Unknown errors - retry with default delay
    return True, 2.0


async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
) -> any:
    """
    Retry async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry
    
    Returns:
        Result of successful function call
    
    Raises:
        RetryExhausted: If all attempts fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            # Check if we should retry this error
            should_retry, error_base_delay = should_retry_error(e)
            if not should_retry:
                logger.warning(f"Non-retryable error: {e}")
                raise
            
            # Use error-specific base delay if available
            delay_base = error_base_delay if error_base_delay > 0 else base_delay
            
            if attempt < max_attempts - 1:
                delay = calculate_backoff(
                    attempt,
                    base_delay=delay_base,
                    max_delay=max_delay,
                    exponential_base=exponential_base,
                )
                
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                if on_retry:
                    await on_retry(attempt, e, delay)
                
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {max_attempts} attempts failed. Last error: {e}"
                )
    
    raise RetryExhausted(
        f"Failed after {max_attempts} attempts. Last error: {last_exception}"
    )


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Usage:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        async def fetch_data():
            # ... API call ...
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def call():
                return await func(*args, **kwargs)
            
            return await retry_async(
                call,
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                exceptions=exceptions,
            )
        
        return wrapper
    return decorator


# Global circuit breakers for common services
_circuit_breakers = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get or create circuit breaker for a service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
        )
    return _circuit_breakers[service_name]


async def call_with_circuit_breaker(
    service_name: str,
    func: Callable,
    *args,
    **kwargs,
):
    """Call function with circuit breaker protection."""
    breaker = get_circuit_breaker(service_name)
    
    async def call():
        return await func(*args, **kwargs)
    
    return await breaker.call_async(call)


# Example usage:
"""
from backend.utils.retry import retry_with_backoff, call_with_circuit_breaker

@retry_with_backoff(max_attempts=3, base_delay=2.0)
async def fetch_stock_quote(symbol: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/quote/{symbol}")
        response.raise_for_status()
        return response.json()

# With circuit breaker
result = await call_with_circuit_breaker(
    "alpha_vantage",
    fetch_stock_quote,
    "AAPL"
)
"""
