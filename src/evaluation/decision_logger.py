"""
Decision Logger for Universal Racing Analytics.

Logs agent decisions for quality review and debugging.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json


@dataclass
class Decision:
    """A single agent decision."""
    timestamp: datetime
    node: str
    decision_type: str  # "tool_call", "factor_selection", "error_recovery", "routing"
    context: str
    choice: str
    rationale: str
    alternatives: List[str] = field(default_factory=list)
    outcome: Optional[str] = None


class DecisionLogger:
    """Logs and tracks agent decisions."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.decisions: List[Decision] = []
        
    def log_decision(
        self,
        node: str,
        decision_type: str,
        context: str,
        choice: str,
        rationale: str,
        alternatives: List[str] = None,
        outcome: str = None
    ) -> Decision:
        """Log a decision."""
        decision = Decision(
            timestamp=datetime.now(),
            node=node,
            decision_type=decision_type,
            context=context[:500],  # Limit context size
            choice=choice,
            rationale=rationale,
            alternatives=alternatives or [],
            outcome=outcome
        )
        self.decisions.append(decision)
        return decision
    
    def log_tool_call(self, node: str, tool_name: str, inputs: Dict, output: Any):
        """Log a tool call decision."""
        self.log_decision(
            node=node,
            decision_type="tool_call",
            context=f"Tool inputs: {str(inputs)[:200]}",
            choice=tool_name,
            rationale="Agent selected this tool based on current state",
            outcome=f"Output: {str(output)[:200]}"
        )
    
    def log_factor_selection(self, node: str, factors: List[str], reasons: Dict[str, str]):
        """Log factor selection decisions."""
        for factor in factors:
            self.log_decision(
                node=node,
                decision_type="factor_selection",
                context="Analyzing query for relevant factors",
                choice=factor,
                rationale=reasons.get(factor, "No rationale provided")
            )
    
    def log_error_recovery(self, node: str, error: str, recovery_action: str, alternatives: List[str] = None):
        """Log error recovery decision."""
        self.log_decision(
            node=node,
            decision_type="error_recovery",
            context=f"Error occurred: {error[:200]}",
            choice=recovery_action,
            rationale="Attempting recovery from error",
            alternatives=alternatives or []
        )
    
    def log_routing(self, node: str, destination: str, condition: str):
        """Log routing decision."""
        self.log_decision(
            node=node,
            decision_type="routing",
            context=condition,
            choice=destination,
            rationale=f"Routing based on: {condition}"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all decisions."""
        by_type = {}
        by_node = {}
        
        for d in self.decisions:
            by_type[d.decision_type] = by_type.get(d.decision_type, 0) + 1
            by_node[d.node] = by_node.get(d.node, 0) + 1
        
        return {
            "session_id": self.session_id,
            "total_decisions": len(self.decisions),
            "by_type": by_type,
            "by_node": by_node,
            "error_recoveries": sum(1 for d in self.decisions if d.decision_type == "error_recovery")
        }
    
    def save(self, output_dir: Path = None):
        """Save decisions to file."""
        output_dir = output_dir or Path("outputs/decisions")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / f"decisions_{self.session_id}.json"
        
        data = {
            "session_id": self.session_id,
            "summary": self.get_summary(),
            "decisions": [
                {
                    "timestamp": d.timestamp.isoformat(),
                    "node": d.node,
                    "type": d.decision_type,
                    "context": d.context,
                    "choice": d.choice,
                    "rationale": d.rationale,
                    "alternatives": d.alternatives,
                    "outcome": d.outcome
                }
                for d in self.decisions
            ]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[DecisionLogger] Saved {len(self.decisions)} decisions to {filepath}")
        return filepath
    
    def export_csv(self, output_dir: Path = None) -> Path:
        """Export decisions to CSV for analysis."""
        import csv
        
        output_dir = output_dir or Path("outputs/decisions")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / f"decisions_{self.session_id}.csv"
        
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "node", "type", "choice", "rationale", "outcome"])
            
            for d in self.decisions:
                writer.writerow([
                    d.timestamp.isoformat(),
                    d.node,
                    d.decision_type,
                    d.choice,
                    d.rationale,
                    d.outcome or ""
                ])
        
        print(f"[DecisionLogger] Exported to {filepath}")
        return filepath


# Global logger instance
_logger: Optional[DecisionLogger] = None


def get_logger() -> DecisionLogger:
    """Get or create the global decision logger."""
    global _logger
    if _logger is None:
        _logger = DecisionLogger()
    return _logger


def reset_logger(session_id: str = None):
    """Reset the global logger with a new session."""
    global _logger
    _logger = DecisionLogger(session_id)
    return _logger
