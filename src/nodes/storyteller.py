"""
Storyteller Node

This node creates a compelling narrative by synthesizing:
1. The original dataset analysis
2. Real-time API data (weather, telemetry, race control)
3. Historical context and patterns

The goal is to tell the "story" of the race, explaining not just WHAT happened
but WHY it happened, connecting multiple data points into a coherent narrative.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_outputs_path
from src.tools.token_tracker import (
    track_llm_response,
    is_limit_exceeded,
    get_usage_summary,
    check_token_budget
)


def storyteller(state: WeekendState) -> dict:
    """
    Create a narrative synthesis of all analysis data.

    This is the final "deep" analysis node that weaves together:
    - Original dataset findings
    - OpenF1 API data (weather, telemetry, incidents)
    - Context about drivers, teams, and the season

    The output is a rich, story-driven report that explains the race.
    """
    print("\n=== [Storyteller] Creating Narrative Synthesis ===")

    # Check token budget
    if is_limit_exceeded():
        print("[Storyteller] Token limit exceeded, generating minimal report")
        return _generate_budget_exceeded_report(state)

    if not check_token_budget(3000):
        print("[Storyteller] Insufficient token budget for full storytelling")
        return _generate_budget_exceeded_report(state)

    # Gather all inputs
    user_query = state.get("user_query", "")
    weekend_spec = state.get("weekend_spec", {})
    drivers_focus = state.get("drivers_focus", [])
    teams_focus = state.get("teams_focus", [])

    # Original analysis
    analysis_outputs = state.get("analysis_outputs", {})
    original_stdout = analysis_outputs.get("stdout", "")
    original_report = analysis_outputs.get("report", "")
    figures = state.get("figures", [])

    # API data
    api_data_summary = state.get("api_data_summary", "")
    api_data = state.get("api_data", {})

    # Build context for LLM
    race_name = weekend_spec.get("name", "Unknown Race")
    race_year = weekend_spec.get("year", "")
    circuit = weekend_spec.get("circuit", "")

    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.3)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an elite Formula 1 journalist and analyst. Your task is to create a narrative that explains the STORY of this race weekend using ONLY the data provided below.

## CRITICAL RULES - YOU MUST FOLLOW THESE:
1. ONLY use information from the "Dataset Analysis Results" and "Real-Time API Data Insights" sections below.
2. If the analysis says "RACE WINNER: X from Y", then X won the race. DO NOT contradict this.
3. DO NOT make up, guess, or assume any race results, winners, lap times, or statistics.
4. DO NOT use your training knowledge about F1 races - ONLY use the data provided.
5. If data is missing, say "data not available" rather than guessing.
6. Quote specific numbers exactly as they appear in the data.

## Race Context
Race: {race_name} ({race_year})
Circuit: {circuit}
Focus Drivers: {drivers}
Focus Teams: {teams}

## Original Question
{query}

## Dataset Analysis Results (USE THESE EXACT VALUES)
{original_analysis}

## Real-Time API Data Insights
{api_insights}

## Generated Visualizations
{figures}

## Your Task
Create a narrative report that:
1. Opens with a hook about this race (based on the data provided)
2. Reports the race winner EXACTLY as stated in the analysis
3. Uses ONLY specific data points from the analysis provided
4. If weather/strategy data is available in API insights, include it
5. Stay factual - only include claims supported by the data above

Write in markdown format. Use headers to organize sections.
Keep it engaging but 100% faithful to the data provided.
Target length: 400-600 words."""),
        ("user", "Tell the story of this race using ONLY the data provided above. Do not add any information that isn't in the data.")
    ])

    chain = prompt | llm

    # Truncate inputs if too long
    original_analysis = original_stdout if original_stdout else original_report
    if len(original_analysis) > 3000:
        original_analysis = original_analysis[:3000] + "\n...[truncated]..."

    if len(api_data_summary) > 2000:
        api_data_summary = api_data_summary[:2000] + "\n...[truncated]..."

    try:
        response = chain.invoke({
            "race_name": race_name,
            "race_year": race_year,
            "circuit": circuit,
            "drivers": ", ".join(drivers_focus) if drivers_focus else "All drivers",
            "teams": ", ".join(teams_focus) if teams_focus else "All teams",
            "query": user_query,
            "original_analysis": original_analysis,
            "api_insights": api_data_summary if api_data_summary else "No real-time API data available for this session.",
            "figures": ", ".join(figures) if figures else "No visualizations generated"
        })

        # Track usage
        usage = track_llm_response(response)
        print(f"[Storyteller] LLM tokens used: {usage}")

        narrative = response.content

        # Save the narrative report
        outputs_path = get_outputs_path()
        narrative_path = outputs_path / "narrative_report.md"

        # Combine with original report
        full_report = f"""# Race Analysis: {race_name} {race_year}

## Executive Summary
{original_report if original_report else "See detailed analysis below."}

---

# The Full Story

{narrative}

---

## Technical Appendix

### Data Sources
- **Historical Dataset**: Kaggle F1 World Championship (1950-2024)
- **Real-Time API**: OpenF1 (2023+ sessions)

### Visualizations Generated
{chr(10).join([f"- {f}" for f in figures]) if figures else "No visualizations"}

### API Data Retrieved
{api_data_summary if api_data_summary else "No API data available"}

---
*Analysis generated by F1 Weekend Strategy Analyst*
"""

        with open(narrative_path, "w") as f:
            f.write(full_report)

        # Also update the main report
        main_report_path = outputs_path / "race_report.md"
        with open(main_report_path, "w") as f:
            f.write(full_report)

        print(f"[Storyteller] Narrative saved to {narrative_path}")
        print(get_usage_summary())

        return {
            "narrative_report": narrative,
            "analysis_outputs": {
                **analysis_outputs,
                "narrative_path": str(narrative_path),
                "report_path": str(main_report_path),
                "report": full_report
            },
            "analysis_depth": "story"
        }

    except Exception as e:
        print(f"[Storyteller] Error generating narrative: {e}")
        return {
            "narrative_report": f"Error generating narrative: {str(e)}",
            "errors": state.get("errors", []) + [f"Storyteller error: {str(e)}"]
        }


def _generate_budget_exceeded_report(state: WeekendState) -> dict:
    """Generate a minimal report when token budget is exceeded."""
    outputs_path = get_outputs_path()

    # Use existing analysis without LLM enhancement
    analysis_outputs = state.get("analysis_outputs", {})
    original_report = analysis_outputs.get("report", "")
    api_summary = state.get("api_data_summary", "")

    budget_report = f"""# Race Analysis Report

## Analysis Summary
{original_report if original_report else "Analysis data available in output files."}

## API Data Summary
{api_summary if api_summary else "No API data retrieved."}

---
*Note: Full narrative analysis was limited due to token budget constraints.*
*{get_usage_summary()}*
"""

    report_path = outputs_path / "race_report.md"
    with open(report_path, "w") as f:
        f.write(budget_report)

    return {
        "narrative_report": budget_report,
        "analysis_outputs": {
            **analysis_outputs,
            "report_path": str(report_path),
            "report": budget_report
        },
        "token_limit_exceeded": True
    }
