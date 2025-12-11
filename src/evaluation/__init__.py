"""
Evaluation package for Universal Racing Analytics.

Provides metrics, accuracy tracking, and decision logging.
"""

from src.evaluation.metrics import (
    start_session,
    end_session,
    get_current_session,
    track_node_start,
    track_node_end,
    track_factor,
    get_session_summary,
    calculate_precision_recall
)

__all__ = [
    "start_session",
    "end_session", 
    "get_current_session",
    "track_node_start",
    "track_node_end",
    "track_factor",
    "get_session_summary",
    "calculate_precision_recall"
]
