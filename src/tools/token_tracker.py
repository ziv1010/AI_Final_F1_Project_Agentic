"""
Token Usage Tracker for monitoring LLM API costs.

Tracks prompt and completion tokens across all LLM calls to prevent
exceeding free tier limits on APIs like Groq.
"""

from typing import Dict, Optional, Callable
from functools import wraps
import threading

# Thread-safe singleton tracker
_lock = threading.Lock()
_usage = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "call_count": 0
}
_limit = 100000  # Default token limit (adjustable via config)
_callbacks = []  # Callbacks to invoke when limit is exceeded


def set_token_limit(limit: int):
    """Set the maximum token limit for the session."""
    global _limit
    with _lock:
        _limit = limit
    print(f"[TokenTracker] Token limit set to {limit:,}")


def get_token_limit() -> int:
    """Get the current token limit."""
    return _limit


def reset_usage():
    """Reset token usage counters."""
    global _usage
    with _lock:
        _usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "call_count": 0
        }
    print("[TokenTracker] Usage counters reset")


def add_usage(prompt_tokens: int = 0, completion_tokens: int = 0):
    """Add token usage from an LLM call."""
    global _usage
    with _lock:
        _usage["prompt_tokens"] += prompt_tokens
        _usage["completion_tokens"] += completion_tokens
        _usage["total_tokens"] += (prompt_tokens + completion_tokens)
        _usage["call_count"] += 1

        # Check if limit exceeded
        if _usage["total_tokens"] >= _limit:
            print(f"[TokenTracker] WARNING: Token limit exceeded! {_usage['total_tokens']:,} >= {_limit:,}")
            for callback in _callbacks:
                callback(_usage)


def get_usage() -> Dict[str, int]:
    """Get current token usage."""
    with _lock:
        return dict(_usage)


def get_remaining_tokens() -> int:
    """Get remaining tokens before limit."""
    with _lock:
        return max(0, _limit - _usage["total_tokens"])


def is_limit_exceeded() -> bool:
    """Check if token limit has been exceeded."""
    with _lock:
        return _usage["total_tokens"] >= _limit


def register_limit_callback(callback: Callable):
    """Register a callback to be invoked when limit is exceeded."""
    _callbacks.append(callback)


def get_usage_summary() -> str:
    """Get a human-readable usage summary."""
    usage = get_usage()
    remaining = get_remaining_tokens()
    pct_used = (usage["total_tokens"] / _limit * 100) if _limit > 0 else 0

    return f"""Token Usage Summary:
- Prompt tokens:     {usage['prompt_tokens']:,}
- Completion tokens: {usage['completion_tokens']:,}
- Total tokens:      {usage['total_tokens']:,}
- Limit:             {_limit:,}
- Remaining:         {remaining:,} ({100-pct_used:.1f}%)
- LLM calls:         {usage['call_count']}"""


def estimate_tokens(text: str) -> int:
    """
    Rough estimate of tokens in a text string.
    Uses ~4 characters per token as a rough heuristic.
    """
    return len(text) // 4


class TokenLimitExceeded(Exception):
    """Exception raised when token limit is exceeded."""
    pass


def check_token_budget(required_estimate: int = 0) -> bool:
    """
    Check if we have enough token budget for an operation.

    Args:
        required_estimate: Estimated tokens needed for the operation

    Returns:
        True if we have budget, False otherwise
    """
    remaining = get_remaining_tokens()
    if required_estimate > 0 and remaining < required_estimate:
        print(f"[TokenTracker] Insufficient budget: need ~{required_estimate:,}, have {remaining:,}")
        return False
    return remaining > 0


def track_llm_response(response) -> Dict[str, int]:
    """
    Extract and track token usage from an LLM response.

    Works with LangChain response objects that have usage_metadata.

    Args:
        response: LLM response object

    Returns:
        Dict with token usage from this call
    """
    usage = {"prompt_tokens": 0, "completion_tokens": 0}

    # Try different response formats
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        meta = response.usage_metadata
        usage["prompt_tokens"] = meta.get("input_tokens", 0) or meta.get("prompt_tokens", 0)
        usage["completion_tokens"] = meta.get("output_tokens", 0) or meta.get("completion_tokens", 0)

    elif hasattr(response, "response_metadata") and response.response_metadata:
        meta = response.response_metadata
        if "token_usage" in meta:
            tu = meta["token_usage"]
            usage["prompt_tokens"] = tu.get("prompt_tokens", 0)
            usage["completion_tokens"] = tu.get("completion_tokens", 0)

    # Groq specific
    if hasattr(response, "llm_output") and response.llm_output:
        if "token_usage" in response.llm_output:
            tu = response.llm_output["token_usage"]
            usage["prompt_tokens"] = tu.get("prompt_tokens", 0)
            usage["completion_tokens"] = tu.get("completion_tokens", 0)

    # Add to tracker
    if usage["prompt_tokens"] > 0 or usage["completion_tokens"] > 0:
        add_usage(usage["prompt_tokens"], usage["completion_tokens"])

    return usage


def with_token_tracking(func):
    """
    Decorator to add token tracking to functions that make LLM calls.

    The decorated function should return a response object with usage metadata.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if is_limit_exceeded():
            raise TokenLimitExceeded(f"Token limit ({_limit:,}) exceeded before call")

        result = func(*args, **kwargs)

        # Try to track usage from result
        if result is not None:
            track_llm_response(result)

        return result

    return wrapper
