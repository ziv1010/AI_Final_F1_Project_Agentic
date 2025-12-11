"""
Deep Analysis Report Generator

Creates a focused report that:
1. Presents all the deep analysis findings
2. DIRECTLY answers the user's original query
3. Provides evidence-based conclusions
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_run_output_path
from src.tools.token_tracker import track_llm_response, check_token_budget
from pathlib import Path


def deep_report_generator(state: WeekendState) -> dict:
    """
    Generate a comprehensive deep analysis report that focuses on answering the user's query.

    The report includes:
    - Executive summary answering the query directly
    - Deep analysis findings (telemetry, tire deg, weather impact)
    - Evidence from FastF1 data
    - Visual references
    - Conclusion directly addressing the query
    """
    print("\n=== [Deep Report Generator] Creating Focused Deep Analysis Report ===")

    if not check_token_budget(5000):
        print("[Deep Report Generator] Insufficient token budget")
        return {}

    # Get all analysis data
    user_query = state.get("user_query", "")
    basic_stdout = state.get("analysis_outputs", {}).get("stdout", "")
    api_summary = state.get("api_data_summary", "")
    fastf1_summary = state.get("analysis_outputs", {}).get("fastf1_summary", "")
    deep_visualizations = state.get("analysis_outputs", {}).get("deep_visualizations", [])
    basic_report_path = state.get("analysis_outputs", {}).get("report_path", "")
    factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
    validation_info = state.get("analysis_outputs", {}).get("validation_info", {})
    drivers_focus = state.get("drivers_focus", [])
    teams_focus = state.get("teams_focus", [])
    weekend_spec = state.get("weekend_spec", {})

    # Read basic report if available
    basic_report_content = ""
    if basic_report_path and Path(basic_report_path).exists():
        with open(basic_report_path, 'r') as f:
            basic_report_content = f.read()

    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert F1 analyst writing a comprehensive deep analysis report.

**CRITICAL REQUIREMENT**: Your report MUST directly answer the user's original query.

Your task:
1. Synthesize ALL available data (basic analysis, API data, FastF1 telemetry, weather, tire data)
2. Create a focused report that DIRECTLY answers the user's question
3. Provide evidence-based conclusions
4. Reference specific data points and visualizations

**Report Structure**:

# Deep Analysis: [Query]

## Executive Summary
- **Direct answer to the query in 2-3 sentences**
- Key finding that answers the question
- Evidence summary

## Detailed Analysis

### Performance Comparison
[Compare drivers/teams with specific data]
**CRITICAL**: ALWAYS specify the ACTUAL race finishing positions using "P#" notation (e.g., "Verstappen won the race (P1), Hamilton finished P10, Norris finished P6").
NEVER say "finished second" or "finished third" without clarification - readers will assume you mean the actual race position.
If comparing only a subset of drivers, say "Among the compared drivers, Norris performed best (P6 actual), followed by Hamilton (P10 actual)".

### Telemetry Insights
[What telemetry reveals - speed, throttle, brake patterns]

### Tire Strategy & Degradation
[Tire compound choices, degradation rates, strategy effectiveness]

### Weather Impact
[How weather affected performance, if relevant]

### Critical Moments
[Key laps, incidents, strategic decisions that determined the outcome]

## Answer to Query
**Question**: {query}

**Answer**: [Direct, comprehensive answer using all evidence gathered]

### Supporting Evidence
1. [Evidence point 1 with data]
2. [Evidence point 2 with data]
3. [Evidence point 3 with data]

## Visualizations
[List all deep analysis visualizations with descriptions]

## Conclusion
[Final answer to the query, summarizing key factors that explain the outcome]

---

**RULES**:
1. MUST directly answer the user's query in the "Answer to Query" section
2. Use SPECIFIC data points (lap times, degradation rates, speed deltas, etc.)
3. Reference visualizations by name
4. Be evidence-based - no speculation without data
5. If data is missing, state it clearly
6. Connect findings back to the original question

**Available Data**:

User Query: {query}

**CRITICAL - DRIVER/TEAM FOCUS**:
Drivers to analyze: {drivers_focus}
Teams to analyze: {teams_focus}
Race Weekend: {weekend_info}

YOU MUST ONLY ANALYZE AND REPORT ON THE DRIVERS/TEAMS LISTED ABOVE.
DO NOT include analysis of other drivers unless they directly affected the focused drivers.

Factor Analysis:
{factor_analysis}

Validation Info:
{validation_info}

Basic Analysis Output:
{basic_analysis}

Basic Report:
{basic_report}

API Data Summary:
{api_summary}

FastF1 Data Summary:
{fastf1_summary}

Deep Visualizations Available:
{visualizations}

"""),
        ("user", "Generate a comprehensive deep analysis report that directly answers my query: {query}\n\nREMEMBER: Focus ONLY on these drivers: {drivers_focus}")
    ])

    chain = prompt | llm

    try:
        # Build weekend info string
        weekend_info = ""
        if weekend_spec:
            weekend_info = f"{weekend_spec.get('name', 'Unknown')} ({weekend_spec.get('year', 'Unknown')})"

        response = chain.invoke({
            "query": user_query,
            "drivers_focus": ", ".join(drivers_focus) if drivers_focus else "All drivers",
            "teams_focus": ", ".join(teams_focus) if teams_focus else "All teams",
            "weekend_info": weekend_info,
            "factor_analysis": str(factor_analysis),
            "validation_info": str(validation_info),
            "basic_analysis": basic_stdout[:3000] if basic_stdout else "No basic analysis output",
            "basic_report": basic_report_content[:2000] if basic_report_content else "No basic report",
            "api_summary": api_summary[:2000] if api_summary else "No API data",
            "fastf1_summary": fastf1_summary[:2000] if fastf1_summary else "No FastF1 data",
            "visualizations": "\n".join([f"- {Path(v).name}" for v in deep_visualizations]) if deep_visualizations else "No visualizations"
        })

        # Track token usage
        usage = track_llm_response(response)
        print(f"[Deep Report Generator] LLM tokens used: {usage}")

        report_content = response.content

        # Save deep analysis report to run-specific directory
        run_dir = get_run_output_path()
        run_deep_report_path = run_dir / "deep_analysis_summary.md"
        with open(run_deep_report_path, 'w') as f:
            f.write(report_content)

        # Also save to main outputs for backwards compatibility
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        deep_report_path = output_dir / "deep_analysis_summary.md"
        with open(deep_report_path, 'w') as f:
            f.write(report_content)

        print(f"[Deep Report Generator] Deep analysis report saved to run: {run_dir}")

        return {
            "analysis_outputs": {
                **state.get("analysis_outputs", {}),
                "deep_report_path": str(deep_report_path)
            }
        }

    except Exception as e:
        print(f"[Deep Report Generator] Error generating report: {e}")
        return {
            "errors": state.get("errors", []) + [f"Deep report generation error: {str(e)}"]
        }
