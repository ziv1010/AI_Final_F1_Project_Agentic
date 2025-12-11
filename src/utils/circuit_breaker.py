"""
Circuit Breaker Pattern for Universal Racing Analytics.

Prevents cascading failures by failing fast when a service is unhealthy.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import functools


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast, not calling
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for protecting against failing services.
    
    States:
    - CLOSED: Normal operation, calls go through
    - OPEN: Service is unhealthy, calls fail immediately  
    - HALF_OPEN: Testing if service recovered
    
    Usage:
        breaker = CircuitBreaker(name="groq_api")
        
        try:
            result = breaker.call(api_function, arg1, arg2)
        except CircuitOpenError:
            # Handle gracefully
            pass
    """
    name: str
    failure_threshold: int = 5
    reset_timeout_seconds: int = 60
    half_open_max_calls: int = 3
    
    def __post_init__(self):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
    
    @property
    def state(self) -> CircuitState:
        """Get current state, checking for timeout transition."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                elapsed = datetime.now() - self._last_failure_time
                if elapsed > timedelta(seconds=self.reset_timeout_seconds):
                    print(f"[CircuitBreaker:{self.name}] Transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
        return self._state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function through the circuit breaker.
        
        Raises:
            CircuitOpenError: If circuit is open
        """
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit '{self.name}' is OPEN. "
                f"Will retry after {self.reset_timeout_seconds}s."
            )
        
        if current_state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self):
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_calls:
                print(f"[CircuitBreaker:{self.name}] Transitioning to CLOSED")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        else:
            # In CLOSED state, reset failure count on success
            self._failure_count = 0
    
    def _on_failure(self, error: Exception):
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        print(f"[CircuitBreaker:{self.name}] Failure {self._failure_count}/{self.failure_threshold}: {error}")
        
        if self._state == CircuitState.HALF_OPEN:
            print(f"[CircuitBreaker:{self.name}] Transitioning to OPEN (failed during half-open)")
            self._state = CircuitState.OPEN
            self._success_count = 0
        elif self._failure_count >= self.failure_threshold:
            print(f"[CircuitBreaker:{self.name}] Transitioning to OPEN")
            self._state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset the circuit breaker."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        print(f"[CircuitBreaker:{self.name}] Manually reset to CLOSED")
    
    def force_open(self):
        """Manually open the circuit."""
        self._state = CircuitState.OPEN
        self._last_failure_time = datetime.now()
        print(f"[CircuitBreaker:{self.name}] Manually forced OPEN")
    
    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None
        }


class CircuitOpenError(Exception):
    """Raised when a call is attempted on an open circuit."""
    pass


# Global circuit breakers
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name, **kwargs)
    return _breakers[name]


def with_circuit_breaker(breaker_name: str, **breaker_kwargs):
    """
    Decorator to wrap a function with a circuit breaker.
    
    Usage:
        @with_circuit_breaker("groq_api")
        def call_groq_api(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            breaker = get_breaker(breaker_name, **breaker_kwargs)
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def get_all_breaker_status() -> list[dict]:
    """Get status of all circuit breakers."""
    return [b.get_status() for b in _breakers.values()]


def reset_all_breakers():
    """Reset all circuit breakers."""
    for breaker in _breakers.values():
        breaker.reset()
    print(f"[CircuitBreaker] Reset all {len(_breakers)} breakers")
