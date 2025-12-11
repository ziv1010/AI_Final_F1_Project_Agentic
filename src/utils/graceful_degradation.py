"""
Graceful Degradation for Universal Racing Analytics.

Provides fallback mechanisms when primary services fail.
"""

from typing import Callable, Any, Optional, List, TypeVar, Generic
import functools
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


T = TypeVar('T')


@dataclass
class FallbackResult(Generic[T]):
    """Result from a fallback chain."""
    value: T
    source: str
    was_fallback: bool
    elapsed_ms: float = 0.0


@dataclass
class CachedResult:
    """A cached result with metadata."""
    key: str
    value: Any
    cached_at: datetime
    ttl_seconds: int = 3600
    
    def is_expired(self) -> bool:
        from datetime import timedelta
        return datetime.now() > self.cached_at + timedelta(seconds=self.ttl_seconds)


class FallbackChain:
    """
    Chain of fallback functions to try in order.
    
    Usage:
        chain = FallbackChain("api_data")
        chain.add(primary_api_call, "primary")
        chain.add(backup_api_call, "backup")
        chain.add(lambda: cached_data, "cache")
        
        result = chain.execute(query="test")
    """
    
    def __init__(self, name: str):
        self.name = name
        self._fallbacks: List[tuple[Callable, str]] = []
    
    def add(self, func: Callable, source_name: str) -> 'FallbackChain':
        """Add a fallback function to the chain."""
        self._fallbacks.append((func, source_name))
        return self
    
    def execute(self, *args, **kwargs) -> FallbackResult:
        """
        Execute the fallback chain.
        
        Tries each function in order until one succeeds.
        """
        import time
        
        start = time.time()
        last_error = None
        
        for i, (func, source_name) in enumerate(self._fallbacks):
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start) * 1000
                
                was_fallback = i > 0
                if was_fallback:
                    print(f"[FallbackChain:{self.name}] Using fallback '{source_name}'")
                
                return FallbackResult(
                    value=result,
                    source=source_name,
                    was_fallback=was_fallback,
                    elapsed_ms=elapsed
                )
            except Exception as e:
                print(f"[FallbackChain:{self.name}] {source_name} failed: {e}")
                last_error = e
                continue
        
        # All fallbacks failed
        raise FallbackExhaustedError(
            f"All {len(self._fallbacks)} fallbacks failed for '{self.name}'. "
            f"Last error: {last_error}"
        )


class FallbackExhaustedError(Exception):
    """Raised when all fallbacks have failed."""
    pass


class ResultCache:
    """
    Simple cache for storing fallback results.
    
    Used to provide cached data when all live sources fail.
    """
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path("outputs/.cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, CachedResult] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        # Try memory cache first
        if key in self._memory_cache:
            cached = self._memory_cache[key]
            if not cached.is_expired():
                return cached.value
            else:
                del self._memory_cache[key]
        
        # Try disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                cached_at = datetime.fromisoformat(data["cached_at"])
                ttl = data.get("ttl_seconds", 3600)
                
                cached = CachedResult(
                    key=key,
                    value=data["value"],
                    cached_at=cached_at,
                    ttl_seconds=ttl
                )
                
                if not cached.is_expired():
                    self._memory_cache[key] = cached
                    return cached.value
            except Exception as e:
                print(f"[Cache] Error reading {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set a cached value."""
        cached = CachedResult(
            key=key,
            value=value,
            cached_at=datetime.now(),
            ttl_seconds=ttl_seconds
        )
        
        # Memory cache
        self._memory_cache[key] = cached
        
        # Disk cache
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "value": value,
                    "cached_at": cached.cached_at.isoformat(),
                    "ttl_seconds": ttl_seconds
                }, f)
        except Exception as e:
            print(f"[Cache] Error writing {key}: {e}")
    
    def clear(self):
        """Clear all caches."""
        self._memory_cache.clear()
        for f in self.cache_dir.glob("*.json"):
            f.unlink()


# Global cache instance
_cache = ResultCache()


def get_cache() -> ResultCache:
    """Get the global cache instance."""
    return _cache


def with_fallback(fallback_value: Any = None, fallback_fn: Callable = None):
    """
    Decorator to provide a fallback value or function on error.
    
    Usage:
        @with_fallback(fallback_value=[])
        def get_drivers():
            return api.get_drivers()
        
        @with_fallback(fallback_fn=get_cached_drivers)
        def get_drivers():
            return api.get_drivers()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"[Fallback] {func.__name__} failed: {e}")
                
                if fallback_fn is not None:
                    try:
                        result = fallback_fn(*args, **kwargs)
                        print(f"[Fallback] Using fallback function for {func.__name__}")
                        return result
                    except Exception as fallback_error:
                        print(f"[Fallback] Fallback function also failed: {fallback_error}")
                
                if fallback_value is not None:
                    print(f"[Fallback] Using fallback value for {func.__name__}")
                    return fallback_value
                
                raise
        return wrapper
    return decorator


def with_cache(key_fn: Callable = None, ttl_seconds: int = 3600):
    """
    Decorator to cache function results.
    
    Usage:
        @with_cache(key_fn=lambda query: f"search_{query}", ttl_seconds=1800)
        def search_data(query):
            return expensive_search(query)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_fn:
                cache_key = key_fn(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Check cache
            cached = _cache.get(cache_key)
            if cached is not None:
                print(f"[Cache] Hit for {cache_key}")
                return cached
            
            # Execute and cache
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl_seconds)
            return result
        return wrapper
    return decorator
