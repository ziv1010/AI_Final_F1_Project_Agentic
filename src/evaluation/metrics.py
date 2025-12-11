"""
Evaluation Metrics for Universal Racing Analytics.

Tracks agent performance, execution times, and decision quality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class NodeMetric:
    """Metrics for a single node execution."""
    node_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = True
    error: Optional[str] = None
    tokens_used: int = 0
    
    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds() * 1000


@dataclass  
class FactorMetric:
    """Metrics for factor analysis accuracy."""
    factor_name: str
    predicted_importance: float
    actual_correlation: Optional[float] = None
    was_validated: bool = False
    validation_method: str = ""


@dataclass
class SessionMetrics:
    """Aggregate metrics for a session."""
    session_id: str
    start_time: datetime
    query: str
    depth: str
    node_metrics: List[NodeMetric] = field(default_factory=list)
    factor_metrics: List[FactorMetric] = field(default_factory=list)
    total_tokens: int = 0
    total_errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "query": self.query,
            "depth": self.depth,
            "node_count": len(self.node_metrics),
            "success_rate": self.get_success_rate(),
            "total_duration_ms": self.get_total_duration(),
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "factor_validation_rate": self.get_factor_validation_rate()
        }
    
    def get_success_rate(self) -> float:
        if not self.node_metrics:
            return 1.0
        successful = sum(1 for m in self.node_metrics if m.success)
        return successful / len(self.node_metrics)
    
    def get_total_duration(self) -> float:
        return sum(m.duration_ms for m in self.node_metrics)
    
    def get_factor_validation_rate(self) -> float:
        if not self.factor_metrics:
            return 0.0
        validated = sum(1 for f in self.factor_metrics if f.was_validated)
        return validated / len(self.factor_metrics)


# Global session tracker
_current_session: Optional[SessionMetrics] = None
_session_history: List[SessionMetrics] = []


def start_session(query: str, depth: str = "basic") -> SessionMetrics:
    """Start a new evaluation session."""
    global _current_session
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    _current_session = SessionMetrics(
        session_id=session_id,
        start_time=datetime.now(),
        query=query,
        depth=depth
    )
    print(f"[Evaluation] Started session {session_id}")
    return _current_session


def get_current_session() -> Optional[SessionMetrics]:
    """Get the current session."""
    return _current_session


def track_node_start(node_name: str) -> NodeMetric:
    """Track the start of a node execution."""
    metric = NodeMetric(
        node_name=node_name,
        start_time=datetime.now()
    )
    
    if _current_session:
        _current_session.node_metrics.append(metric)
    
    return metric


def track_node_end(metric: NodeMetric, success: bool = True, error: Optional[str] = None, tokens: int = 0):
    """Track the end of a node execution."""
    metric.end_time = datetime.now()
    metric.success = success
    metric.error = error
    metric.tokens_used = tokens
    
    if _current_session:
        _current_session.total_tokens += tokens
        if not success:
            _current_session.total_errors += 1
    
    status = "✓" if success else "✗"
    print(f"[Evaluation] {status} {metric.node_name}: {metric.duration_ms:.0f}ms")


def track_factor(factor_name: str, importance: float, validated: bool = False, method: str = "") -> FactorMetric:
    """Track a factor analysis result."""
    metric = FactorMetric(
        factor_name=factor_name,
        predicted_importance=importance,
        was_validated=validated,
        validation_method=method
    )
    
    if _current_session:
        _current_session.factor_metrics.append(metric)
    
    return metric


def end_session() -> Optional[SessionMetrics]:
    """End the current session and save metrics."""
    global _current_session
    
    if _current_session is None:
        return None
    
    session = _current_session
    _session_history.append(session)
    
    # Save to file
    _save_session(session)
    
    print(f"[Evaluation] Session {session.session_id} complete:")
    print(f"  - Nodes: {len(session.node_metrics)}")
    print(f"  - Success rate: {session.get_success_rate():.1%}")
    print(f"  - Duration: {session.get_total_duration():.0f}ms")
    print(f"  - Tokens: {session.total_tokens:,}")
    
    _current_session = None
    return session


def _save_session(session: SessionMetrics):
    """Save session metrics to file."""
    output_dir = Path("outputs/evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / f"session_{session.session_id}.json"
    
    # Convert to serializable format
    data = session.to_dict()
    data["nodes"] = [
        {
            "name": m.node_name,
            "duration_ms": m.duration_ms,
            "success": m.success,
            "error": m.error,
            "tokens": m.tokens_used
        }
        for m in session.node_metrics
    ]
    data["factors"] = [
        {
            "name": f.factor_name,
            "importance": f.predicted_importance,
            "validated": f.was_validated,
            "method": f.validation_method
        }
        for f in session.factor_metrics
    ]
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"[Evaluation] Saved metrics to {filepath}")


def get_session_summary() -> str:
    """Get a summary of all sessions."""
    if not _session_history:
        return "No sessions recorded."
    
    lines = [f"Total sessions: {len(_session_history)}", ""]
    
    for session in _session_history[-5:]:  # Last 5 sessions
        lines.append(f"Session {session.session_id}:")
        lines.append(f"  Query: {session.query[:50]}...")
        lines.append(f"  Success: {session.get_success_rate():.1%}")
        lines.append(f"  Duration: {session.get_total_duration():.0f}ms")
        lines.append("")
    
    return "\n".join(lines)


def calculate_precision_recall(predicted_factors: List[str], actual_important: List[str]) -> Dict[str, float]:
    """
    Calculate precision and recall for factor selection.
    
    Args:
        predicted_factors: Factors selected by the agent
        actual_important: Ground truth important factors
        
    Returns:
        Dict with precision, recall, and f1 score
    """
    if not predicted_factors or not actual_important:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    predicted_set = set(f.lower() for f in predicted_factors)
    actual_set = set(f.lower() for f in actual_important)
    
    true_positives = len(predicted_set & actual_set)
    
    precision = true_positives / len(predicted_set) if predicted_set else 0.0
    recall = true_positives / len(actual_set) if actual_set else 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": true_positives,
        "predicted_count": len(predicted_set),
        "actual_count": len(actual_set)
    }
