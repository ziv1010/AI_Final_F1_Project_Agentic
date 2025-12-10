#!/usr/bin/env python3
"""
F1 Weekend Strategy Analyst - Main Entry Point

Supports three analysis modes:
1. BASIC: Dataset analysis only (fast, uses Kaggle data)
2. DEEP: Dataset + OpenF1 API data (adds weather, telemetry, race control)
3. STORY: Full narrative synthesis (comprehensive analysis with storytelling)

Usage:
    python main.py "Your query here"                    # Basic analysis
    python main.py "Your query here" --deep             # Deep analysis with API
    python main.py "Your query here" --story            # Full narrative mode
    python main.py "Your query here" --interactive      # Interactive mode
    python main.py "Your query here" --token-limit 30000  # Custom token limit
"""

import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

from src.graph import build_graph, build_flexible_graph, get_graph_for_depth
from src.config import CONFIG
from src.tools.token_tracker import (
    set_token_limit,
    get_usage_summary,
    reset_usage,
    is_limit_exceeded,
    get_remaining_tokens
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="F1 Weekend Strategy Analyst - AI-powered race analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Compare Verstappen and Hamilton at the 2023 Bahrain GP"
  python main.py "Why did Mercedes struggle at Monaco 2023?" --deep
  python main.py "Tell me the story of the 2023 Las Vegas GP" --story
  python main.py "Analyze Red Bull's strategy at Silverstone 2023" --interactive
        """
    )

    parser.add_argument("query", nargs="?", help="Your F1 analysis question")

    parser.add_argument(
        "--deep", "-d",
        action="store_true",
        help="Enable deep analysis with OpenF1 API data (weather, telemetry, etc.)"
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
        "weekend_spec": None,
        "drivers_focus": [],
        "teams_focus": [],
        # New fields for deep analysis
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
    print(f"F1 Weekend Strategy Analyst")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"Analysis Depth: {depth.upper()}")
    print(f"Token Limit: {token_limit:,}")
    print(f"{'='*60}\n")

    # Set up token tracking
    reset_usage()
    set_token_limit(token_limit)

    # Get appropriate graph
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
                for field, val in value.items():
                    current_state[field] = val

                print(f"\n--- Finished Node: {key} ---")

                # Show relevant state updates
                if "errors" in value and value["errors"]:
                    print(f"  Errors: {value['errors']}")

                if current_state.get("weekend_spec"):
                    ws = current_state["weekend_spec"]
                    print(f"  Weekend: {ws.get('name', 'Unknown')} ({ws.get('year', '')})")

                if current_state.get("drivers_focus") or current_state.get("teams_focus"):
                    print(f"  Focus - Drivers: {current_state.get('drivers_focus')}, Teams: {current_state.get('teams_focus')}")

                if key == "data_loader" and current_state.get("analysis_outputs", {}).get("data_paths"):
                    print(f"  Data loaded: {len(current_state['analysis_outputs']['data_paths'])} files")

                if key == "analysis_planner" and "plan" in value:
                    print(f"  Plan generated ({len(value['plan'])} chars)")

                if key == "plan_reviewer" and value.get("plan_review"):
                    print(f"  Plan reviewed ({len(value['plan_review'])} chars)")

                if key == "code_writer":
                    stdout = value.get("analysis_outputs", {}).get("stdout", "")
                    if stdout:
                        print(f"  Code output: {stdout[:300]}..." if len(stdout) > 300 else f"  Code output: {stdout}")

                if key == "report_generator":
                    report_path = value.get("analysis_outputs", {}).get("report_path")
                    if report_path:
                        print(f"  Basic report saved to: {report_path}")

                if key == "deep_analysis_fetcher":
                    api_summary = value.get("api_data_summary", "")
                    if api_summary:
                        print(f"  API data summary ({len(api_summary)} chars)")
                    if value.get("api_data", {}).get("error"):
                        print(f"  API Error: {value['api_data']['error']}")

                if key == "storyteller":
                    narrative_path = value.get("analysis_outputs", {}).get("narrative_path")
                    if narrative_path:
                        print(f"  Narrative report saved to: {narrative_path}")

                # Check token limit
                if is_limit_exceeded():
                    print(f"\n  WARNING: Token limit exceeded!")
                    print(get_usage_summary())

    else:
        # Use invoke instead of stream
        final_state = graph.invoke(initial_state)
        current_state = final_state

    return current_state


def prompt_for_deep_analysis() -> str:
    """Prompt user to decide on deep analysis."""
    print("\n" + "="*60)
    print("Basic analysis complete!")
    print("="*60)
    print("\nWould you like a deeper analysis?")
    print("  [d] Deep analysis - Add weather, telemetry, race control data")
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
    print("\nStarting with basic analysis...")
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
        print("\nKeeping basic analysis. Done!")
        return state

    # Continue with deeper analysis
    print(f"\nContinuing with {next_depth} analysis...")

    # Create new state with existing data
    deep_state = create_initial_state(query, next_depth, token_limit)

    # Carry over relevant fields from basic analysis
    deep_state["weekend_spec"] = state.get("weekend_spec")
    deep_state["drivers_focus"] = state.get("drivers_focus", [])
    deep_state["teams_focus"] = state.get("teams_focus", [])
    deep_state["analysis_outputs"] = state.get("analysis_outputs", {})
    deep_state["figures"] = state.get("figures", [])
    deep_state["code_snippets"] = state.get("code_snippets", [])

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
    print("Analysis Complete!")
    print("="*60)

    outputs = final_state.get("analysis_outputs", {})
    if outputs.get("report_path"):
        print(f"\nReport: {outputs['report_path']}")
    if outputs.get("narrative_path"):
        print(f"Narrative: {outputs['narrative_path']}")

    figures = final_state.get("figures", [])
    if figures:
        print(f"\nVisualizations ({len(figures)}):")
        for fig in figures[:5]:
            print(f"  - {fig}")
        if len(figures) > 5:
            print(f"  ... and {len(figures) - 5} more")

    print(f"\n{get_usage_summary()}")

    if final_state.get("errors"):
        print(f"\nErrors encountered: {len(final_state['errors'])}")
        for err in final_state["errors"][:3]:
            print(f"  - {err[:100]}...")


if __name__ == "__main__":
    main()
