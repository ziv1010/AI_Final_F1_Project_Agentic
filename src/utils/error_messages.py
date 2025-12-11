"""
Error Messages for Universal Racing Analytics.

Provides user-friendly error messages with recovery suggestions.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class ErrorCategory(Enum):
    """Categories of errors."""
    API = "api"
    DATA = "data"
    EXECUTION = "execution"
    CONFIG = "config"
    NETWORK = "network"
    AUTH = "auth"


@dataclass
class ErrorInfo:
    """Structured error information."""
    code: str
    category: ErrorCategory
    message: str
    detail: str
    recovery: List[str]
    docs_link: Optional[str] = None


# Error catalog
ERROR_CATALOG: Dict[str, ErrorInfo] = {
    "GROQ_RATE_LIMIT": ErrorInfo(
        code="GROQ_RATE_LIMIT",
        category=ErrorCategory.API,
        message="Groq API rate limit exceeded",
        detail="You have exceeded the allowed number of API requests per minute.",
        recovery=[
            "Wait 60 seconds before retrying",
            "Use --token-limit flag to reduce token usage",
            "Try --depth basic for lighter analysis",
            "Consider using a paid API plan for higher limits"
        ]
    ),
    
    "GROQ_AUTH": ErrorInfo(
        code="GROQ_AUTH",
        category=ErrorCategory.AUTH,
        message="Invalid Groq API key",
        detail="The GROQ_API_KEY environment variable is missing or invalid.",
        recovery=[
            "Check that GROQ_API_KEY is set in your .env file",
            "Verify the API key is correct at console.groq.com",
            "Ensure the .env file is in the project root directory"
        ]
    ),
    
    "DATA_NOT_FOUND": ErrorInfo(
        code="DATA_NOT_FOUND",
        category=ErrorCategory.DATA,
        message="Required data file not found",
        detail="The analysis requires data files that could not be located.",
        recovery=[
            "Check that data files exist in data/raw/",
            "Run the data download script if available",
            "Verify the data path in config.yaml"
        ]
    ),
    
    "INVALID_QUERY": ErrorInfo(
        code="INVALID_QUERY",
        category=ErrorCategory.EXECUTION,
        message="Could not understand the query",
        detail="The query could not be parsed into a valid analysis request.",
        recovery=[
            "Be more specific about the event (e.g., '2023 Bahrain GP')",
            "Specify drivers or teams explicitly",
            "Use simpler language (e.g., 'Compare X and Y')",
            "Try 'Show me what data is available' first"
        ]
    ),
    
    "CODE_EXECUTION_ERROR": ErrorInfo(
        code="CODE_EXECUTION_ERROR",
        category=ErrorCategory.EXECUTION,
        message="Generated code failed to execute",
        detail="The analysis code encountered an error during execution.",
        recovery=[
            "The system will automatically retry with debugging",
            "Try a simpler query if errors persist",
            "Check that all required columns exist in the data"
        ]
    ),
    
    "TOKEN_LIMIT": ErrorInfo(
        code="TOKEN_LIMIT",
        category=ErrorCategory.API,
        message="Token limit exceeded",
        detail="The analysis exceeded the maximum allowed tokens for this session.",
        recovery=[
            "Use --token-limit flag to increase the limit",
            "Try --depth basic for a shorter analysis",
            "Break complex queries into smaller parts"
        ]
    ),
    
    "NETWORK_ERROR": ErrorInfo(
        code="NETWORK_ERROR",
        category=ErrorCategory.NETWORK,
        message="Network connection error",
        detail="Could not connect to external services.",
        recovery=[
            "Check your internet connection",
            "Try again in a few moments",
            "Use cached data if available (--use-cache)"
        ]
    ),
    
    "SCHEMA_DETECTION_FAILED": ErrorInfo(
        code="SCHEMA_DETECTION_FAILED",
        category=ErrorCategory.DATA,
        message="Could not detect data schema",
        detail="The system could not automatically detect the structure of your data.",
        recovery=[
            "Ensure CSV files have headers",
            "Check that files are valid CSV format",
            "Specify domain manually with --domain flag"
        ]
    ),
    
    "NO_FACTORS_VALIDATED": ErrorInfo(
        code="NO_FACTORS_VALIDATED",
        category=ErrorCategory.EXECUTION,
        message="No factors passed statistical validation",
        detail="All proposed factors were rejected by the propensity guardrail.",
        recovery=[
            "This may indicate the query is too vague",
            "Try specifying different factors to analyze",
            "Check if the outcome variable exists in the data"
        ]
    ),
    
    "CIRCUIT_OPEN": ErrorInfo(
        code="CIRCUIT_OPEN",
        category=ErrorCategory.API,
        message="Service temporarily unavailable",
        detail="The API service has been experiencing failures and is temporarily bypassed.",
        recovery=[
            "Wait 60 seconds for the circuit to reset",
            "The system will automatically retry",
            "Check service status if issues persist"
        ]
    )
}


def get_error_info(code: str) -> Optional[ErrorInfo]:
    """Get error info by code."""
    return ERROR_CATALOG.get(code)


def format_error(code: str, additional_detail: str = None) -> str:
    """
    Format an error for display.
    
    Returns a user-friendly error message with recovery suggestions.
    """
    info = get_error_info(code)
    
    if info is None:
        return f"Unknown error: {code}\n{additional_detail or ''}"
    
    lines = [
        f"❌ Error: {info.message}",
        f"",
        f"   {info.detail}"
    ]
    
    if additional_detail:
        lines.append(f"   Details: {additional_detail}")
    
    lines.append("")
    lines.append("💡 Suggested fixes:")
    
    for i, recovery in enumerate(info.recovery, 1):
        lines.append(f"   {i}. {recovery}")
    
    if info.docs_link:
        lines.append("")
        lines.append(f"📚 More info: {info.docs_link}")
    
    return "\n".join(lines)


def identify_error(exception: Exception) -> str:
    """
    Identify the error code from an exception.
    
    Returns the error code or "UNKNOWN".
    """
    error_str = str(exception).lower()
    
    # API errors
    if "rate limit" in error_str or "429" in error_str:
        return "GROQ_RATE_LIMIT"
    if "authentication" in error_str or "401" in error_str or "invalid api" in error_str:
        return "GROQ_AUTH"
    if "token" in error_str and "limit" in error_str:
        return "TOKEN_LIMIT"
    
    # Network errors
    if "connection" in error_str or "network" in error_str or "timeout" in error_str:
        return "NETWORK_ERROR"
    
    # Data errors
    if "not found" in error_str or "no such file" in error_str:
        return "DATA_NOT_FOUND"
    
    # Circuit breaker
    if "circuit" in error_str and "open" in error_str:
        return "CIRCUIT_OPEN"
    
    return "UNKNOWN"


def handle_exception(exception: Exception, context: str = "") -> str:
    """
    Handle an exception and return a formatted error message.
    
    Args:
        exception: The exception that occurred
        context: Optional context about where the error occurred
        
    Returns:
        Formatted error message string
    """
    error_code = identify_error(exception)
    
    additional_detail = None
    if context:
        additional_detail = f"Context: {context}"
    
    if error_code == "UNKNOWN":
        # For unknown errors, include the full exception
        lines = [
            f"❌ An unexpected error occurred",
            f"",
            f"   {type(exception).__name__}: {str(exception)[:200]}"
        ]
        if context:
            lines.append(f"   Context: {context}")
        lines.extend([
            "",
            "💡 Suggested fixes:",
            "   1. Check the error message above for clues",
            "   2. Try a simpler query",
            "   3. Check logs for more details"
        ])
        return "\n".join(lines)
    
    return format_error(error_code, additional_detail)
