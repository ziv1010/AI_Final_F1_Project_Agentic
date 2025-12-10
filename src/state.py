from typing import List, Dict, Any, Optional, TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage
import operator

class WeekendState(TypedDict):
    # Core fields
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str
    weekend_spec: Optional[Dict[str, Any]]
    drivers_focus: List[str]
    teams_focus: List[str]
    plan: str
    plan_review: str
    code_snippets: Annotated[List[str], operator.add]
    analysis_outputs: Dict[str, Any]
    figures: List[str]
    errors: List[str]

    # Deep analysis fields (for F1 API integration)
    analysis_depth: Literal["basic", "deep", "story"]  # Controls analysis flow
    deep_analysis_requested: bool  # User requested further analysis
    api_data: Dict[str, Any]  # Data fetched from OpenF1 API
    api_data_summary: str  # LLM-generated summary of API data
    narrative_report: str  # Storyteller's narrative synthesis

    # Token tracking
    token_usage: Dict[str, int]  # {"prompt_tokens": X, "completion_tokens": Y, "total": Z}
    token_limit: int  # Max tokens allowed for the session
    token_limit_exceeded: bool  # Flag to stop execution if limit exceeded
