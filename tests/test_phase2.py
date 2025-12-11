"""
Tests for Phase 2 modules.

Run with: python -m pytest tests/test_phase2.py -v
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_closed_state_allows_calls(self):
        from src.utils.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        result = breaker.call(lambda: "success")
        assert result == "success"
    
    def test_opens_after_threshold_failures(self):
        from src.utils.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
        
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        def failing_func():
            raise ValueError("error")
        
        # Fail 3 times
        for _ in range(3):
            try:
                breaker.call(failing_func)
            except ValueError:
                pass
        
        # Should be open now
        assert breaker.state == CircuitState.OPEN
        
        # Next call should raise CircuitOpenError
        with pytest.raises(CircuitOpenError):
            breaker.call(lambda: "success")
    
    def test_reset_closes_circuit(self):
        from src.utils.circuit_breaker import CircuitBreaker, CircuitState
        
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        
        try:
            breaker.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        
        assert breaker.state == CircuitState.OPEN
        
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED


class TestGracefulDegradation:
    """Test graceful degradation functionality."""
    
    def test_fallback_chain_uses_first_success(self):
        from src.utils.graceful_degradation import FallbackChain
        
        chain = FallbackChain("test")
        chain.add(lambda: "primary", "primary")
        chain.add(lambda: "fallback", "fallback")
        
        result = chain.execute()
        
        assert result.value == "primary"
        assert result.source == "primary"
        assert result.was_fallback == False
    
    def test_fallback_chain_uses_fallback_on_failure(self):
        from src.utils.graceful_degradation import FallbackChain
        
        def failing():
            raise ValueError("fail")
        
        chain = FallbackChain("test")
        chain.add(failing, "primary")
        chain.add(lambda: "fallback", "fallback")
        
        result = chain.execute()
        
        assert result.value == "fallback"
        assert result.source == "fallback"
        assert result.was_fallback == True
    
    def test_with_fallback_decorator(self):
        from src.utils.graceful_degradation import with_fallback
        
        @with_fallback(fallback_value=[])
        def failing_func():
            raise ValueError("error")
        
        result = failing_func()
        assert result == []


class TestErrorMessages:
    """Test error message functionality."""
    
    def test_get_error_info_returns_known_error(self):
        from src.utils.error_messages import get_error_info
        
        info = get_error_info("GROQ_RATE_LIMIT")
        assert info is not None
        assert "rate limit" in info.message.lower()
        assert len(info.recovery) > 0
    
    def test_identify_error_detects_rate_limit(self):
        from src.utils.error_messages import identify_error
        
        error_code = identify_error(Exception("Rate limit exceeded"))
        assert error_code == "GROQ_RATE_LIMIT"
    
    def test_format_error_includes_recovery(self):
        from src.utils.error_messages import format_error
        
        formatted = format_error("GROQ_AUTH")
        assert "recovery" in formatted.lower() or "fix" in formatted.lower()


class TestMetrics:
    """Test evaluation metrics functionality."""
    
    def test_session_lifecycle(self):
        from src.evaluation.metrics import start_session, end_session, get_current_session
        
        session = start_session("test query", "basic")
        assert session is not None
        assert session.query == "test query"
        
        current = get_current_session()
        assert current == session
        
        ended = end_session()
        assert ended == session
        
        assert get_current_session() is None
    
    def test_node_tracking(self):
        from src.evaluation.metrics import (
            start_session, end_session, 
            track_node_start, track_node_end
        )
        
        session = start_session("test", "basic")
        
        metric = track_node_start("test_node")
        track_node_end(metric, success=True, tokens=100)
        
        assert len(session.node_metrics) == 1
        assert session.node_metrics[0].node_name == "test_node"
        assert session.total_tokens == 100
        
        end_session()
    
    def test_precision_recall_calculation(self):
        from src.evaluation.metrics import calculate_precision_recall
        
        result = calculate_precision_recall(
            predicted_factors=["a", "b", "c"],
            actual_important=["a", "b", "d"]
        )
        
        assert result["precision"] == 2/3
        assert result["recall"] == 2/3


class TestDecisionLogger:
    """Test decision logger functionality."""
    
    def test_log_decision(self):
        from src.evaluation.decision_logger import DecisionLogger
        
        logger = DecisionLogger("test_session")
        
        decision = logger.log_decision(
            node="test_node",
            decision_type="tool_call",
            context="test context",
            choice="run_code",
            rationale="needed to analyze data"
        )
        
        assert len(logger.decisions) == 1
        assert decision.node == "test_node"
        assert decision.choice == "run_code"
    
    def test_summary(self):
        from src.evaluation.decision_logger import DecisionLogger
        
        logger = DecisionLogger("test")
        logger.log_decision("n1", "tool_call", "", "c1", "r1")
        logger.log_decision("n2", "routing", "", "c2", "r2")
        
        summary = logger.get_summary()
        
        assert summary["total_decisions"] == 2
        assert summary["by_type"]["tool_call"] == 1
        assert summary["by_type"]["routing"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
