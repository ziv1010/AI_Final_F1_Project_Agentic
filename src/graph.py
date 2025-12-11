"""
LangGraph Workflow Definition for Universal Racing Analytics.

This graph supports:
1. Universal domain detection (F1, MotoGP, IndyCar, etc.)
2. EDA Agent for data exploration
3. Web Search Agent for external context
4. Propensity Guardrail for factor validation
5. ReAct-based code execution

All agents use tool calling - no hardcoded logic.
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

# Import new agents
from src.nodes.eda_agent import eda_agent
from src.nodes.web_search_agent import web_search_agent
from src.nodes.propensity_guardrail import propensity_guardrail


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


def build_react_graph():
    """
    Build the full ReAct-based analysis graph with new agents.

    This is the recommended graph featuring:
    - EDA Agent for data exploration
    - Web Search Agent for external context
    - Propensity Guardrail for factor validation
    - All agents use tool calling
    
    Flow:
    query_interpreter -> query_validator -> eda_agent -> factor_analyzer 
    -> web_search_agent -> data_loader -> propensity_guardrail 
    -> analysis_planner -> plan_reviewer -> code_writer -> report_generator
    """
    workflow = StateGraph(WeekendState)

    # Add all nodes including new agents
    workflow.add_node("query_interpreter", query_interpreter)
    workflow.add_node("query_validator", query_validator)
    workflow.add_node("eda_agent", eda_agent)  # NEW
    workflow.add_node("factor_analyzer", factor_analyzer)
    workflow.add_node("web_search_agent", web_search_agent)  # NEW
    workflow.add_node("data_loader", data_loader)
    workflow.add_node("propensity_guardrail", propensity_guardrail)  # NEW
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

    # Query understanding
    workflow.add_edge("query_interpreter", "query_validator")
    workflow.add_edge("query_validator", "eda_agent")
    
    # EDA agent can branch for pure EDA queries
    def route_after_eda(state):
        query = state.get("user_query", "").lower()
        
        # If purely EDA request, end here
        eda_only_keywords = ["show data", "what columns", "describe dataset", "list tables"]
        if any(kw in query for kw in eda_only_keywords):
            print("[Graph] Pure EDA query - ending after EDA agent")
            return END
        
        return "factor_analyzer"

    workflow.add_conditional_edges("eda_agent", route_after_eda, {
        "factor_analyzer": "factor_analyzer",
        END: END
    })

    # Factor analysis -> Web search -> Data loading
    workflow.add_edge("factor_analyzer", "web_search_agent")
    workflow.add_edge("web_search_agent", "data_loader")
    
    # Data loading -> Propensity validation
    workflow.add_edge("data_loader", "propensity_guardrail")
    workflow.add_edge("propensity_guardrail", "analysis_planner")
    
    # Planning and execution
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


def build_flexible_graph():
    """
    Build a flexible graph that adapts based on analysis needs.
    
    This is an alias for build_react_graph() for backwards compatibility.
    """
    return build_react_graph()


def build_deep_analysis_graph():
    """
    Build the deep analysis graph with all features.
    
    This is an alias for build_react_graph() for backwards compatibility.
    """
    return build_react_graph()


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
    # Always use the ReAct graph for better analysis
    # The graph internally handles depth-based routing
    return build_react_graph()
