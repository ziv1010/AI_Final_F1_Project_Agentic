"""
LangGraph Workflow Definition for F1 Weekend Strategy Analyst.

This graph supports three analysis modes:
1. BASIC: Dataset analysis only (original flow)
2. DEEP: Dataset + OpenF1 API data (weather, telemetry, etc.)
3. STORY: Full narrative synthesis with storytelling

The flow is determined by the `analysis_depth` state field.
"""

from langgraph.graph import StateGraph, END
from src.state import WeekendState
from src.nodes.query_interpreter import query_interpreter
from src.nodes.query_validator import query_validator
from src.nodes.factor_analyzer import factor_analyzer
from src.nodes.data_loader import data_loader
from src.nodes.analysis_planner import analysis_planner
from src.nodes.plan_reviewer import plan_reviewer
from src.nodes.code_writer import code_writer
from src.nodes.code_debugger import code_debugger
from src.nodes.report_generator import report_generator
from src.nodes.deep_analysis_fetcher import deep_analysis_fetcher
from src.nodes.deep_visualizer import deep_visualizer
from src.nodes.deep_report_generator import deep_report_generator
from src.nodes.storyteller import storyteller
from src.tools.token_tracker import is_limit_exceeded


def build_graph():
    """Build the basic analysis graph (original flow with intelligent factor analysis)."""
    workflow = StateGraph(WeekendState)

    # Add nodes
    workflow.add_node("query_interpreter", query_interpreter)
    workflow.add_node("query_validator", query_validator)
    workflow.add_node("factor_analyzer", factor_analyzer)
    workflow.add_node("data_loader", data_loader)
    workflow.add_node("analysis_planner", analysis_planner)
    workflow.add_node("plan_reviewer", plan_reviewer)
    workflow.add_node("code_writer", code_writer)
    workflow.add_node("code_debugger", code_debugger)
    workflow.add_node("report_generator", report_generator)

    # Define edges
    workflow.set_entry_point("query_interpreter")

    # Query interpreter -> query validator -> factor analyzer
    workflow.add_edge("query_interpreter", "query_validator")
    workflow.add_edge("query_validator", "factor_analyzer")
    workflow.add_edge("factor_analyzer", "data_loader")
    workflow.add_edge("data_loader", "analysis_planner")
    workflow.add_edge("analysis_planner", "plan_reviewer")
    workflow.add_edge("plan_reviewer", "code_writer")

    # Conditional edge for code writer (retry with debugging on error)
    def check_code_execution(state):
        errors = state.get("errors", [])
        attempts = len(state.get("code_snippets", []))

        if errors and attempts < 5:  # Increased from 3 to 5 with debugger
            print(f"DEBUG [Graph] Code execution failed (Attempt {attempts})")

            # Use debugger for intelligent fixes on attempts 2-4
            if attempts >= 2 and attempts <= 4:
                print(f"DEBUG [Graph] Routing to code_debugger for intelligent fix")
                import time
                time.sleep(1)
                return "code_debugger"
            else:
                # First retry: let code_writer try again with error context
                print(f"DEBUG [Graph] Retrying code_writer with error context")
                import time
                time.sleep(2)
                return "code_writer"

        return "report_generator"

    workflow.add_conditional_edges(
        "code_writer",
        check_code_execution,
        {
            "code_writer": "code_writer",
            "code_debugger": "code_debugger",
            "report_generator": "report_generator"
        }
    )

    # After debugger fixes code, go back to code_writer to execute
    workflow.add_edge("code_debugger", "code_writer")
    workflow.add_edge("report_generator", END)

    return workflow.compile()


def build_deep_analysis_graph():
    """
    Build the deep analysis graph with API integration and intelligent factor analysis.

    Flow:
    query_interpreter -> query_validator -> factor_analyzer -> data_loader -> analysis_planner -> plan_reviewer
    -> code_writer -> report_generator -> deep_analysis_fetcher -> storyteller -> END
    """
    workflow = StateGraph(WeekendState)

    # Add all nodes (basic + deep)
    workflow.add_node("query_interpreter", query_interpreter)
    workflow.add_node("query_validator", query_validator)
    workflow.add_node("factor_analyzer", factor_analyzer)
    workflow.add_node("data_loader", data_loader)
    workflow.add_node("analysis_planner", analysis_planner)
    workflow.add_node("plan_reviewer", plan_reviewer)
    workflow.add_node("code_writer", code_writer)
    workflow.add_node("code_debugger", code_debugger)
    workflow.add_node("report_generator", report_generator)
    workflow.add_node("deep_analysis_fetcher", deep_analysis_fetcher)
    workflow.add_node("storyteller", storyteller)

    # Define edges
    workflow.set_entry_point("query_interpreter")

    workflow.add_edge("query_interpreter", "query_validator")
    workflow.add_edge("query_validator", "factor_analyzer")
    workflow.add_edge("factor_analyzer", "data_loader")
    workflow.add_edge("data_loader", "analysis_planner")
    workflow.add_edge("analysis_planner", "plan_reviewer")
    workflow.add_edge("plan_reviewer", "code_writer")

    # Conditional edge for code writer (retry with debugging on error)
    def check_code_execution(state):
        errors = state.get("errors", [])
        attempts = len(state.get("code_snippets", []))

        if errors and attempts < 5:
            print(f"DEBUG [Graph] Code execution failed (Attempt {attempts})")

            if attempts >= 2 and attempts <= 4:
                print(f"DEBUG [Graph] Routing to code_debugger for intelligent fix")
                import time
                time.sleep(1)
                return "code_debugger"
            else:
                print(f"DEBUG [Graph] Retrying code_writer with error context")
                import time
                time.sleep(2)
                return "code_writer"

        return "report_generator"

    workflow.add_conditional_edges(
        "code_writer",
        check_code_execution,
        {
            "code_writer": "code_writer",
            "code_debugger": "code_debugger",
            "report_generator": "report_generator"
        }
    )

    workflow.add_edge("code_debugger", "code_writer")

    # After basic report, continue to deep analysis
    workflow.add_edge("report_generator", "deep_analysis_fetcher")

    # After fetching API data, check if we should do storytelling
    def check_deep_analysis_result(state):
        # Check token limit
        if state.get("token_limit_exceeded") or is_limit_exceeded():
            print("[Graph] Token limit exceeded, ending without storytelling")
            return END

        # Check if API data was successfully fetched
        api_data = state.get("api_data", {})
        if api_data.get("error"):
            print(f"[Graph] API data fetch failed: {api_data.get('error')}, skipping storyteller")
            return END

        # Check analysis depth
        depth = state.get("analysis_depth", "deep")
        if depth == "story":
            return "storyteller"

        return END

    workflow.add_conditional_edges(
        "deep_analysis_fetcher",
        check_deep_analysis_result,
        {
            "storyteller": "storyteller",
            END: END
        }
    )

    workflow.add_edge("storyteller", END)

    return workflow.compile()


def build_flexible_graph():
    """
    Build a flexible graph where the agent decides the analysis depth.

    The flow adapts based on:
    1. analysis_depth setting (basic/deep/story)
    2. Token budget remaining
    3. API data availability
    4. User's explicit request for deep/story analysis
    5. Intelligent factor analysis to determine what data sources are needed

    This is the recommended graph for production use.
    """
    workflow = StateGraph(WeekendState)

    # Add all nodes
    workflow.add_node("query_interpreter", query_interpreter)
    workflow.add_node("query_validator", query_validator)
    workflow.add_node("factor_analyzer", factor_analyzer)
    workflow.add_node("data_loader", data_loader)
    workflow.add_node("analysis_planner", analysis_planner)
    workflow.add_node("plan_reviewer", plan_reviewer)
    workflow.add_node("code_writer", code_writer)
    workflow.add_node("code_debugger", code_debugger)
    workflow.add_node("report_generator", report_generator)
    workflow.add_node("deep_analysis_fetcher", deep_analysis_fetcher)
    workflow.add_node("deep_visualizer", deep_visualizer)
    workflow.add_node("deep_report_generator", deep_report_generator)
    workflow.add_node("storyteller", storyteller)

    # Entry
    workflow.set_entry_point("query_interpreter")

    # Standard flow with query validation
    workflow.add_edge("query_interpreter", "query_validator")
    workflow.add_edge("query_validator", "factor_analyzer")
    workflow.add_edge("factor_analyzer", "data_loader")
    workflow.add_edge("data_loader", "analysis_planner")
    workflow.add_edge("analysis_planner", "plan_reviewer")
    workflow.add_edge("plan_reviewer", "code_writer")

    # Code writer retry logic with debugger
    def check_code_execution(state):
        errors = state.get("errors", [])
        attempts = len(state.get("code_snippets", []))

        if errors and attempts < 5:
            print(f"DEBUG [Graph] Code execution failed (Attempt {attempts})")

            if attempts >= 2 and attempts <= 4:
                print(f"DEBUG [Graph] Routing to code_debugger for intelligent fix")
                import time
                time.sleep(1)
                return "code_debugger"
            else:
                print(f"DEBUG [Graph] Retrying code_writer with error context")
                import time
                time.sleep(2)
                return "code_writer"

        return "report_generator"

    workflow.add_conditional_edges(
        "code_writer",
        check_code_execution,
        {
            "code_writer": "code_writer",
            "code_debugger": "code_debugger",
            "report_generator": "report_generator"
        }
    )

    workflow.add_edge("code_debugger", "code_writer")

    # After report, decide next step based on analysis depth
    def route_after_report(state):
        # Check token limit
        if state.get("token_limit_exceeded") or is_limit_exceeded():
            print("[Graph] Token limit reached, ending analysis")
            return END

        depth = state.get("analysis_depth", "basic")

        if depth == "basic":
            print("[Graph] Basic analysis complete")
            return END
        elif depth in ("deep", "story"):
            print(f"[Graph] Proceeding to deep analysis (depth={depth})")
            return "deep_analysis_fetcher"
        else:
            return END

    workflow.add_conditional_edges(
        "report_generator",
        route_after_report,
        {
            "deep_analysis_fetcher": "deep_analysis_fetcher",
            END: END
        }
    )

    # After deep analysis fetch, create deep visualizations
    workflow.add_edge("deep_analysis_fetcher", "deep_visualizer")

    # After deep visualizations, generate focused deep report
    workflow.add_edge("deep_visualizer", "deep_report_generator")

    # After deep report, decide if we do storytelling
    def route_after_deep_report(state):
        if state.get("token_limit_exceeded") or is_limit_exceeded():
            print("[Graph] Token limit reached after deep report")
            return END

        depth = state.get("analysis_depth", "deep")
        api_data = state.get("api_data", {})

        # Only storytell if explicitly requested AND we have API data
        if depth == "story" and not api_data.get("error"):
            print("[Graph] Proceeding to storyteller")
            return "storyteller"

        print("[Graph] Deep analysis complete (no storytelling)")
        return END

    workflow.add_conditional_edges(
        "deep_report_generator",
        route_after_deep_report,
        {
            "storyteller": "storyteller",
            END: END
        }
    )

    workflow.add_edge("storyteller", END)

    return workflow.compile()


# Default graph for backwards compatibility
def get_default_graph():
    """Get the default graph (basic analysis)."""
    return build_graph()


def get_graph_for_depth(depth: str = "basic"):
    """
    Get the appropriate graph based on analysis depth.

    Args:
        depth: "basic", "deep", or "story"

    Returns:
        Compiled LangGraph workflow
    """
    if depth == "basic":
        return build_graph()
    elif depth in ("deep", "story"):
        return build_flexible_graph()
    else:
        return build_graph()
