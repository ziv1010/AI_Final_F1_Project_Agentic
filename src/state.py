"""
State Definition for Universal Racing Analytics.

Defines the shared state that flows through the LangGraph pipeline.
All agents read from and write to this state.
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage
import operator


class WeekendState(TypedDict):
    """
    Shared state for the racing analytics pipeline.
    
    This state is domain-agnostic and works with any racing dataset.
    """
    
    # === Core Fields ===
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str
    
    # === Domain Detection (Universal) ===
    domain: str  # Auto-detected: "f1", "motogp", "indycar", "generic"
    schema_info: Dict[str, Any]  # Auto-detected schema from data
    
    # === Event Specification (Universal) ===
    # Note: weekend_spec kept for backwards compatibility
    weekend_spec: Optional[Dict[str, Any]]  # F1-specific (deprecated)
    event_spec: Optional[Dict[str, Any]]  # Universal event specification
    
    # === Entity Focus (Universal) ===
    # Note: drivers_focus kept for backwards compatibility
    drivers_focus: List[str]  # F1-specific (deprecated)
    competitors_focus: List[str]  # Universal: drivers, riders, competitors
    teams_focus: List[str]  # Universal: teams, constructors, manufacturers
    
    # === EDA Agent Results ===
    eda_results: str  # Summary from EDA exploration
    visualizations: List[str]  # Paths to generated visualizations
    
    # === Factor Analysis ===
    plan: str
    plan_review: str
    analysis_outputs: Dict[str, Any]  # Contains factor_analysis, data_paths, etc.
    
    # === Web Search Context ===
    web_context: str  # External information from web search
    search_queries: List[str]  # Queries that were executed
    
    # === Propensity Guardrail Results ===
    validated_factors: List[Dict[str, Any]]  # Factors that passed statistical validation
    propensity_report: str  # Detailed validation report
    
    # === Code Execution ===
    code_snippets: Annotated[List[str], operator.add]
    code_output: str  # Most recent code execution output
    figures: List[str]
    errors: List[str]
    
    # === Deep Analysis (API Integration) ===
    analysis_depth: Literal["basic", "deep", "story"]
    deep_analysis_requested: bool
    api_data: Dict[str, Any]  # Data from external APIs
    api_data_summary: str
    narrative_report: str
    
    # === Token Tracking ===
    token_usage: Dict[str, int]
    token_limit: int
    token_limit_exceeded: bool


def create_initial_state(
    query: str,
    depth: str = "basic",
    token_limit: int = 50000
) -> WeekendState:
    """
    Create an initial state for the pipeline.
    
    Args:
        query: User's analysis query
        depth: Analysis depth - "basic", "deep", or "story"
        token_limit: Maximum tokens for the session
        
    Returns:
        Initialized WeekendState
    """
    return {
        # Core
        "messages": [],
        "user_query": query,
        
        # Domain (will be auto-detected)
        "domain": "auto",
        "schema_info": {},
        
        # Event spec
        "weekend_spec": None,
        "event_spec": None,
        
        # Entity focus
        "drivers_focus": [],
        "competitors_focus": [],
        "teams_focus": [],
        
        # EDA
        "eda_results": "",
        "visualizations": [],
        
        # Analysis
        "plan": "",
        "plan_review": "",
        "analysis_outputs": {},
        
        # Web search
        "web_context": "",
        "search_queries": [],
        
        # Propensity
        "validated_factors": [],
        "propensity_report": "",
        
        # Code
        "code_snippets": [],
        "code_output": "",
        "figures": [],
        "errors": [],
        
        # Deep analysis
        "analysis_depth": depth,
        "deep_analysis_requested": depth in ("deep", "story"),
        "api_data": {},
        "api_data_summary": "",
        "narrative_report": "",
        
        # Tokens
        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total": 0},
        "token_limit": token_limit,
        "token_limit_exceeded": False,
    }
