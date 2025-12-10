"""
Intelligent Factor Analyzer Node

This node analyzes the user query to determine what factors are relevant to the analysis.
It thinks critically about:
- What performance factors matter (tyres, weather, strategy, pace, reliability)
- What comparisons should be made (driver vs driver, team vs team, stint vs stint)
- What API data sources would be valuable
- What time-based analysis is needed

This makes the agent autonomous and smart about data collection.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG
from src.tools.token_tracker import track_llm_response, check_token_budget
import json
from typing import Dict, List, Any


def factor_analyzer(state: WeekendState) -> dict:
    """
    Analyzes the query to determine what factors and data sources are relevant.

    This node makes the system intelligent by:
    1. Understanding what the user is really asking
    2. Identifying performance factors that could affect the outcome
    3. Determining what data sources to fetch
    4. Planning comparisons and contrasts
    """
    print("\n=== [Factor Analyzer] Analyzing Query for Relevant Factors ===")

    if not check_token_budget(3000):
        print("[Factor Analyzer] Insufficient token budget, using basic factor analysis")
        return _basic_factor_analysis(state)

    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.3)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert F1 strategist and data analyst. Analyze the user's query to determine what factors are relevant for a comprehensive analysis.

Think critically about:

1. **Performance Factors** - What could have affected performance?
   - Tire strategy (compounds, degradation, pit timing)
   - Weather conditions (temperature, rain, wind)
   - Track characteristics (overtaking opportunities, tire wear)
   - Car setup and balance
   - Reliability issues
   - Driver form and racecraft
   - Team strategy decisions

2. **Data Sources Needed** - What data would help answer this?
   - Lap times and sector times (pace analysis)
   - Tire stints and compounds (strategy)
   - Weather data (conditions impact)
   - Pit stop timing and duration (strategy execution)
   - Telemetry data (speed, throttle, brake, DRS usage)
   - Race control messages (incidents, flags, safety cars)
   - Radio communications (team strategy, driver feedback)
   - Position changes over time (race dynamics)

3. **Comparisons to Make** - What should be compared?
   - Driver vs driver (same team or different)
   - Team vs team (strategy differences)
   - Stint vs stint (tire degradation)
   - Qualifying vs race pace
   - Expected vs actual performance

4. **Time-based Analysis** - When did things happen?
   - Pit window timing
   - Pace evolution during race
   - Weather changes during session
   - Incident timing and impact

User Query: {query}

Weekend Context: {weekend}
Drivers Focus: {drivers_focus}
Teams Focus: {teams_focus}
Analysis Depth: {analysis_depth}

Return a JSON object with your analysis:
{{
  "primary_question": "What is the user really asking?",
  "key_factors": ["list", "of", "important", "factors"],
  "data_sources_needed": {{
    "lap_times": true/false,
    "tire_stints": true/false,
    "weather": true/false,
    "telemetry": true/false,
    "pit_stops": true/false,
    "race_control": true/false,
    "radio": true/false,
    "positions": true/false,
    "intervals": true/false
  }},
  "comparisons": [
    {{"type": "driver|team|stint", "entities": ["A", "B"], "metric": "what to compare"}}
  ],
  "time_windows": ["when to focus analysis"],
  "hypotheses": ["what might explain the results"],
  "analysis_approach": "suggested analytical approach"
}}

Be specific and thoughtful. This will guide the entire analysis."""),
        ("user", "Analyze this query and determine what factors matter.")
    ])

    chain = prompt | llm

    response = chain.invoke({
        "query": state.get("user_query", ""),
        "weekend": str(state.get("weekend_spec", {})),
        "drivers_focus": state.get("drivers_focus", []),
        "teams_focus": state.get("teams_focus", []),
        "analysis_depth": state.get("analysis_depth", "basic")
    })

    # Track token usage
    usage = track_llm_response(response)
    print(f"[Factor Analyzer] LLM tokens used: {usage}")

    # Parse response
    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        factor_analysis = json.loads(content.strip())

        print(f"\n[Factor Analyzer] Primary Question: {factor_analysis.get('primary_question', 'Unknown')}")
        print(f"[Factor Analyzer] Key Factors: {factor_analysis.get('key_factors', [])}")
        print(f"[Factor Analyzer] Data Sources: {factor_analysis.get('data_sources_needed', {})}")
        print(f"[Factor Analyzer] Comparisons: {len(factor_analysis.get('comparisons', []))} planned")
        print(f"[Factor Analyzer] Hypotheses: {factor_analysis.get('hypotheses', [])}")

        return {
            "analysis_outputs": {
                **state.get("analysis_outputs", {}),
                "factor_analysis": factor_analysis
            }
        }

    except Exception as e:
        print(f"[Factor Analyzer] Error parsing response: {e}")
        print(f"[Factor Analyzer] Raw response: {response.content[:500]}...")
        return _basic_factor_analysis(state)


def _basic_factor_analysis(state: WeekendState) -> dict:
    """
    Fallback basic factor analysis when token budget is low or parsing fails.
    """
    query_lower = state.get("user_query", "").lower()

    # Simple keyword-based analysis
    factor_analysis = {
        "primary_question": state.get("user_query", ""),
        "key_factors": [],
        "data_sources_needed": {
            "lap_times": True,  # Always useful
            "tire_stints": "tire" in query_lower or "strategy" in query_lower or "pit" in query_lower,
            "weather": "weather" in query_lower or "rain" in query_lower or "wet" in query_lower,
            "telemetry": "speed" in query_lower or "pace" in query_lower or "fast" in query_lower,
            "pit_stops": "pit" in query_lower or "stop" in query_lower or "strategy" in query_lower,
            "race_control": "incident" in query_lower or "crash" in query_lower or "flag" in query_lower,
            "radio": "radio" in query_lower or "communication" in query_lower or "team" in query_lower,
            "positions": "position" in query_lower or "overtake" in query_lower,
            "intervals": "gap" in query_lower or "interval" in query_lower or "behind" in query_lower
        },
        "comparisons": [],
        "time_windows": ["entire race"],
        "hypotheses": ["Performance differences may be explained by strategy, pace, or conditions"],
        "analysis_approach": "Compare key metrics across entities"
    }

    # Add key factors based on keywords
    if "tire" in query_lower or "tyre" in query_lower:
        factor_analysis["key_factors"].append("tire_strategy")
    if "weather" in query_lower or "rain" in query_lower:
        factor_analysis["key_factors"].append("weather_conditions")
    if "pace" in query_lower or "fast" in query_lower:
        factor_analysis["key_factors"].append("lap_pace")
    if "pit" in query_lower or "stop" in query_lower:
        factor_analysis["key_factors"].append("pit_strategy")
    if not factor_analysis["key_factors"]:
        factor_analysis["key_factors"] = ["overall_performance", "strategy", "pace"]

    return {
        "analysis_outputs": {
            **state.get("analysis_outputs", {}),
            "factor_analysis": factor_analysis
        }
    }
