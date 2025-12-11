"""
Utilities package for Universal Racing Analytics.

Provides error handling, caching, and resilience patterns.
"""

from src.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    get_breaker,
    with_circuit_breaker,
    get_all_breaker_status,
    reset_all_breakers
)

from src.utils.graceful_degradation import (
    FallbackChain,
    FallbackResult,
    FallbackExhaustedError,
    ResultCache,
    get_cache,
    with_fallback,
    with_cache
)

from src.utils.error_messages import (
    ErrorCategory,
    ErrorInfo,
    get_error_info,
    format_error,
    identify_error,
    handle_exception
)

__all__ = [
    # Circuit breaker
    "CircuitBreaker",
    "CircuitState", 
    "CircuitOpenError",
    "get_breaker",
    "with_circuit_breaker",
    "get_all_breaker_status",
    "reset_all_breakers",
    
    # Graceful degradation
    "FallbackChain",
    "FallbackResult",
    "FallbackExhaustedError",
    "ResultCache",
    "get_cache",
    "with_fallback",
    "with_cache",
    
    # Error messages
    "ErrorCategory",
    "ErrorInfo",
    "get_error_info",
    "format_error",
    "identify_error",
    "handle_exception"
]
