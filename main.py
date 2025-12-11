#!/usr/bin/env python3
"""
Universal Racing Strategy Analyst - Main Entry Point

An AI-powered racing analytics system that works with any motorsport dataset:
- Formula 1
- MotoGP
- IndyCar
- NASCAR
- And more...

Supports three analysis modes:
1. BASIC: Dataset analysis only (fast, uses local data)
2. DEEP: Dataset + external API data (adds weather, telemetry, etc.)
3. STORY: Full narrative synthesis (comprehensive analysis with storytelling)

Features:
- EDA Agent for data exploration
- Web Search for external context
- Propensity Guardrail for factor validation
- ReAct-based code execution

Usage:
    python main.py "Your query here"                    # Basic analysis
    python main.py "Your query here" --deep             # Deep analysis
    python main.py "Your query here" --story            # Full narrative mode
    python main.py "Your query here" --interactive      # Interactive mode
    python main.py "Your query here" --token-limit 30000  # Custom token limit
"""

import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

from src.graph import build_react_graph, get_graph_for_depth
from src.config import CONFIG
from src.tools.token_tracker import (
    set_token_limit,
    get_usage_summary,
    reset_usage,
    is_limit_exceeded,
    get_remaining_tokens
)

# Phase 2: Evaluation and visualization
try:
    from src.evaluation import start_session, end_session, track_node_start, track_node_end
    from src.visualization import create_session_dashboard, create_factor_importance_plot
    from src.utils import handle_exception, format_error
    PHASE2_ENABLED = True
except ImportError:
    PHASE2_ENABLED = False
    print("[Warning] Phase 2 modules not fully available")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Universal Racing Strategy Analyst - AI-powered motorsport analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # F1 Analysis
  python main.py "Compare Verstappen and Hamilton at the 2023 Bahrain GP"
  python main.py "Why did Mercedes struggle at Monaco 2023?" --deep
  
  # MotoGP Analysis
  python main.py "Analyze Marc Marquez performance in 2019 MotoGP"
  
  # Data Exploration
  python main.py "Show me what data is available"
  python main.py "List all drivers in 2023"
  
  # Deep Analysis
  python main.py "Tell me the story of the 2023 Las Vegas GP" --story
        """
    )

    parser.add_argument("query", nargs="?", help="Your motorsport analysis question")

    parser.add_argument(
        "--deep", "-d",
        action="store_true",
        help="Enable deep analysis with external API data (weather, telemetry, etc.)"
    )

    parser.add_argument(
        "--story", "-s",
        action="store_true",
        help="Enable story mode with full narrative synthesis"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode: prompts for deep analysis after basic results"
    )

    parser.add_argument(
        "--token-limit", "-t",
        type=int,
        default=None,
        help=f"Maximum tokens for this session (default: {CONFIG.get('tokens', {}).get('limit', 50000)})"
    )

    parser.add_argument(
        "--no-streaming",
        action="store_true",
        help="Disable streaming output (use .invoke() instead of .stream())"
    )
    
    parser.add_argument(
        "--domain",
        type=str,
        default="auto",
        choices=["auto", "f1", "motogp", "indycar", "nascar", "generic"],
        help="Force a specific racing domain (default: auto-detect)"
    )

    return parser.parse_args()


def get_analysis_depth(args) -> str:
    """Determine analysis depth from arguments."""
    if args.story:
        return "story"
    elif args.deep:
        return "deep"
    else:
        return "basic"


def create_initial_state(query: str, depth: str, token_limit: int) -> dict:
    """Create the initial state for the graph."""
    return {
        "user_query": query,
        "messages": [],
        "errors": [],
        "analysis_outputs": {},
        "code_snippets": [],
        "figures": [],
        "plan": "",
        "plan_review": "",
        
        # Universal event/entity fields
        "domain": "auto",
        "schema_info": {},
        "event_spec": None,
        "competitors_focus": [],
        "teams_focus": [],
        
        # Backwards compatibility
        "weekend_spec": None,
        "drivers_focus": [],
        
        # EDA Agent
        "eda_results": "",
        "visualizations": [],
        
        # Web Search
        "web_context": "",
        "search_queries": [],
        
        # Propensity Guardrail
        "validated_factors": [],
        "propensity_report": "",
        
        # Code execution
        "code_output": "",
        
        # Deep analysis
        "analysis_depth": depth,
        "deep_analysis_requested": depth in ("deep", "story"),
        "api_data": {},
        "api_data_summary": "",
        "narrative_report": "",
        
        # Token tracking
        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total": 0},
        "token_limit": token_limit,
        "token_limit_exceeded": False,
    }


def run_analysis(query: str, depth: str, token_limit: int, streaming: bool = True):
    """Run the analysis pipeline."""
    print(f"\n{'='*60}")
    print(f"🏎️  Universal Racing Strategy Analyst")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"Analysis Depth: {depth.upper()}")
    print(f"Token Limit: {token_limit:,}")
    print(f"{'='*60}\n")

    # Set up token tracking
    reset_usage()
    set_token_limit(token_limit)
    
    # Phase 2: Start evaluation session
    if PHASE2_ENABLED:
        start_session(query, depth)

    # Get appropriate graph (always uses ReAct graph now)
    graph = get_graph_for_depth(depth)

    # Create initial state
    initial_state = create_initial_state(query, depth, token_limit)

    # Track state for debugging
    current_state = dict(initial_state)

    if streaming:
        # Stream events
        for event in graph.stream(initial_state):
            for key, value in event.items():
                # Update local state view
                if isinstance(value, dict):
                    for field, val in value.items():
                        current_state[field] = val

                print(f"\n--- Finished Node: {key} ---")

                # Show relevant state updates
                if "errors" in value and value["errors"]:
                    print(f"  ⚠️  Errors: {value['errors']}")

                # EDA Agent output
                if key == "eda_agent" and value.get("eda_results"):
                    print(f"  📊 EDA: {value['eda_results'][:200]}...")
                
                # Web Search output
                if key == "web_search_agent" and value.get("web_context"):
                    print(f"  🌐 Web context: {len(value['web_context'])} chars")
                
                # Propensity Guardrail output
                if key == "propensity_guardrail":
                    validated = value.get("validated_factors", [])
                    print(f"  ✅ Validated factors: {len(validated)}")

                if current_state.get("event_spec") or current_state.get("weekend_spec"):
                    es = current_state.get("event_spec") or current_state.get("weekend_spec")
                    if es:
                        print(f"  🏁 Event: {es.get('name', 'Unknown')} ({es.get('year', '')})")

                if current_state.get("competitors_focus") or current_state.get("drivers_focus"):
                    competitors = current_state.get("competitors_focus") or current_state.get("drivers_focus")
                    teams = current_state.get("teams_focus", [])
                    print(f"  👤 Focus - Competitors: {competitors}, Teams: {teams}")

                if key == "data_loader" and current_state.get("analysis_outputs", {}).get("data_paths"):
                    print(f"  📁 Data loaded: {len(current_state['analysis_outputs']['data_paths'])} files")

                if key == "analysis_planner" and "plan" in value:
                    print(f"  📋 Plan generated ({len(value['plan'])} chars)")

                if key == "plan_reviewer" and value.get("plan_review"):
                    print(f"  ✔️  Plan reviewed ({len(value['plan_review'])} chars)")

                if key == "code_writer":
                    stdout = value.get("analysis_outputs", {}).get("stdout", "")
                    if stdout:
                        print(f"  💻 Code output: {stdout[:300]}..." if len(stdout) > 300 else f"  💻 Code output: {stdout}")

                if key == "report_generator":
                    report_path = value.get("analysis_outputs", {}).get("report_path")
                    if report_path:
                        print(f"  📄 Report saved to: {report_path}")

                if key == "deep_analysis_fetcher":
                    api_summary = value.get("api_data_summary", "")
                    if api_summary:
                        print(f"  🔍 API data summary ({len(api_summary)} chars)")
                    if value.get("api_data", {}).get("error"):
                        print(f"  ⚠️  API Error: {value['api_data']['error']}")

                if key == "storyteller":
                    narrative_path = value.get("analysis_outputs", {}).get("narrative_path")
                    if narrative_path:
                        print(f"  📖 Narrative saved to: {narrative_path}")

                # Check token limit
                if is_limit_exceeded():
                    print(f"\n  ⚠️  WARNING: Token limit exceeded!")
                    print(get_usage_summary())

    else:
        # Use invoke instead of stream
        final_state = graph.invoke(initial_state)
        current_state = final_state
    
    # Phase 2: End session and generate dashboard
    if PHASE2_ENABLED:
        try:
            session = end_session()
            if session:
                # Generate dashboard
                session_data = session.to_dict()
                session_data["nodes"] = [
                    {"name": m.node_name, "duration_ms": m.duration_ms, 
                     "success": m.success, "tokens": m.tokens_used}
                    for m in session.node_metrics
                ]
                session_data["factors"] = [
                    {"name": f.factor_name, "importance": f.predicted_importance,
                     "validated": f.was_validated, "method": f.validation_method}
                    for f in session.factor_metrics
                ]
                dashboard_path = create_session_dashboard(session_data)
                print(f"📊 Dashboard: {dashboard_path}")
        except Exception as e:
            print(f"[Warning] Could not generate dashboard: {e}")

    return current_state


def prompt_for_deep_analysis() -> str:
    """Prompt user to decide on deep analysis."""
    print("\n" + "="*60)
    print("✅ Basic analysis complete!")
    print("="*60)
    print("\nWould you like a deeper analysis?")
    print("  [d] Deep analysis - Add web search, external data")
    print("  [s] Story mode   - Full narrative synthesis")
    print("  [n] No thanks    - Keep basic analysis")
    print()

    while True:
        try:
            choice = input("Your choice [d/s/n]: ").strip().lower()
            if choice in ("d", "deep"):
                return "deep"
            elif choice in ("s", "story"):
                return "story"
            elif choice in ("n", "no", ""):
                return "basic"
            else:
                print("Please enter 'd', 's', or 'n'")
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return "basic"


def run_interactive(query: str, token_limit: int):
    """Run in interactive mode with prompts for deep analysis."""
    # First, run basic analysis
    print("\n🚀 Starting with basic analysis...")
    state = run_analysis(query, "basic", token_limit)

    # Check if we have budget for more
    remaining = get_remaining_tokens()
    if remaining < 5000:
        print(f"\n[Token budget low: {remaining:,} remaining]")
        print("Deep analysis would exceed token limit. Ending here.")
        return state

    # Prompt for deep analysis
    next_depth = prompt_for_deep_analysis()

    if next_depth == "basic":
        print("\n✅ Keeping basic analysis. Done!")
        return state

    # Continue with deeper analysis
    print(f"\n🔍 Continuing with {next_depth} analysis...")

    # Create new state with existing data
    deep_state = create_initial_state(query, next_depth, token_limit)

    # Carry over relevant fields from basic analysis
    deep_state["weekend_spec"] = state.get("weekend_spec")
    deep_state["event_spec"] = state.get("event_spec")
    deep_state["drivers_focus"] = state.get("drivers_focus", [])
    deep_state["competitors_focus"] = state.get("competitors_focus", [])
    deep_state["teams_focus"] = state.get("teams_focus", [])
    deep_state["analysis_outputs"] = state.get("analysis_outputs", {})
    deep_state["figures"] = state.get("figures", [])
    deep_state["code_snippets"] = state.get("code_snippets", [])
    deep_state["validated_factors"] = state.get("validated_factors", [])

    # Run deep analysis nodes only
    from src.nodes.deep_analysis_fetcher import deep_analysis_fetcher
    from src.nodes.storyteller import storyteller

    print("\n--- Running Deep Analysis Fetcher ---")
    deep_result = deep_analysis_fetcher(deep_state)
    deep_state.update(deep_result)

    if next_depth == "story" and not deep_state.get("token_limit_exceeded"):
        print("\n--- Running Storyteller ---")
        story_result = storyteller(deep_state)
        deep_state.update(story_result)

    return deep_state


def main():
    """Main entry point."""
    args = parse_args()

    # Check for query
    if not args.query:
        print("Error: Please provide a query.")
        print("Usage: python main.py \"Your query here\"")
        print("Run 'python main.py --help' for more options.")
        sys.exit(1)

    # Ensure API key is set
    if "GROQ_API_KEY" not in os.environ:
        print("Error: GROQ_API_KEY environment variable not set.")
        print("Please add your Groq API key to .env file:")
        print("  GROQ_API_KEY=your_key_here")
        sys.exit(1)

    # Get token limit
    token_limit = args.token_limit or CONFIG.get("tokens", {}).get("limit", 50000)

    # Get analysis depth
    depth = get_analysis_depth(args)

    # Run analysis
    if args.interactive:
        final_state = run_interactive(args.query, token_limit)
    else:
        final_state = run_analysis(
            args.query,
            depth,
            token_limit,
            streaming=not args.no_streaming
        )

    # Print final summary
    print("\n" + "="*60)
    print("🏁 Analysis Complete!")
    print("="*60)

    outputs = final_state.get("analysis_outputs", {})
    if outputs.get("report_path"):
        print(f"\n📄 Report: {outputs['report_path']}")
    if outputs.get("narrative_path"):
        print(f"📖 Narrative: {outputs['narrative_path']}")

    # Show validated factors
    validated = final_state.get("validated_factors", [])
    if validated:
        print(f"\n✅ Validated Factors ({len(validated)}):")
        for f in validated[:5]:
            factor_name = f.get("factor", "Unknown")
            print(f"  - {factor_name}")

    figures = final_state.get("figures", [])
    if figures:
        print(f"\n📊 Visualizations ({len(figures)}):")
        for fig in figures[:5]:
            print(f"  - {fig}")
        if len(figures) > 5:
            print(f"  ... and {len(figures) - 5} more")

    print(f"\n{get_usage_summary()}")

    if final_state.get("errors"):
        print(f"\n⚠️  Errors encountered: {len(final_state['errors'])}")
        for err in final_state["errors"][:3]:
            print(f"  - {err[:100]}...")


if __name__ == "__main__":
    main()
