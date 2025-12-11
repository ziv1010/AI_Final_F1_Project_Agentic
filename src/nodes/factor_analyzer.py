"""
Intelligent Factor Analyzer Node - Universal Version

This node analyzes the user query to determine what factors are relevant to the analysis.
Works with any racing domain (F1, MotoGP, IndyCar, etc.) without hardcoded logic.

It thinks critically about:
- What performance factors matter based on available data
- What comparisons should be made
- What data sources would be valuable
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


def _get_domain_context() -> str:
    """Get domain-specific context for factor analysis."""
    try:
        from src.domain_config import get_domain_config
        from src.tools.schema_detector import get_schema
        from src.config import get_raw_data_path
        
        domain_config = get_domain_config()
        schema = get_schema(get_raw_data_path())
        
        # Build context
        lines = [
            f"Domain: {domain_config.domain_name.upper()}",
            f"Primary entity: {domain_config.primary_entity}",
            f"Secondary entity: {domain_config.secondary_entity}",
            "",
            "Available data columns:"
        ]
        
        # List relevant columns from schema
        for table_name, table in list(schema.tables.items())[:5]:
            numeric_cols = [col for col, info in table.columns.items() 
                          if info.is_numeric and not info.is_id]
            if numeric_cols:
                lines.append(f"  {table_name}: {numeric_cols[:8]}")
        
        # Add potential factors based on detected columns
        all_cols = []
        for table in schema.tables.values():
            all_cols.extend(table.columns.keys())
        
        potential_factors = [c for c in all_cols if any(
            kw in c.lower() for kw in 
            ["position", "time", "speed", "lap", "point", "grid", "pit", "stint"]
        )]
        
        if potential_factors:
            lines.append("")
            lines.append(f"Potential performance factors: {list(set(potential_factors))[:15]}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"Domain detection unavailable: {e}"


def factor_analyzer(state: WeekendState) -> dict:
    """
    Analyzes the query to determine what factors and data sources are relevant.

    This node makes the system intelligent by:
    1. Understanding what the user is really asking
    2. Identifying performance factors that could affect the outcome
    3. Determining what data sources to fetch
    4. Planning comparisons and contrasts
    
    Works with any racing domain using detected schema.
    """
    print("\n=== [Factor Analyzer] Analyzing Query for Relevant Factors ===")

    if not check_token_budget(3000):
        print("[Factor Analyzer] Insufficient token budget, using basic factor analysis")
        return _basic_factor_analysis(state)

    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.3)
    
    # Get domain context
    domain_context = _get_domain_context()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert motorsport strategist and data analyst. 
Analyze the user's query to determine what factors are relevant for a comprehensive analysis.

**DOMAIN CONTEXT:**
{domain_context}

Think critically about:

1. **Performance Factors** - What could have affected performance?
   - Race position and grid position
   - Lap times and pace
   - Strategy decisions (pit stops, tire/compound choices)
   - Weather and track conditions
   - Reliability issues
   - Competitor form and skill
   - Team/manufacturer factors

2. **Data Sources Needed** - What data would help answer this?
   - Results data (positions, points, times)
   - Lap-by-lap data (if available)
   - Qualifying data
   - Pit stop data (if available)
   - Weather data (if available)

3. **Comparisons to Make** - What should be compared?
   - Competitor vs competitor
   - Team vs team
   - Event vs event
   - Season trends

4. **Time-based Analysis** - What patterns to look for?
   - Performance over race/event
   - Season progression
   - Historical comparison

User Query: {query}

Event Context: {event}
Competitors Focus: {competitors_focus}
Teams Focus: {teams_focus}
Analysis Depth: {analysis_depth}

Return a JSON object with your analysis:
{{
  "primary_question": "What is the user really asking?",
  "key_factors": ["list", "of", "important", "factors"],
  "data_sources_needed": {{
    "results": true/false,
    "lap_times": true/false,
    "qualifying": true/false,
    "pit_stops": true/false,
    "weather": true/false,
    "standings": true/false
  }},
  "comparisons": [
    {{"type": "competitor|team|event", "entities": ["A", "B"], "metric": "what to compare"}}
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
        "domain_context": domain_context,
        "event": str(state.get("event_spec") or state.get("weekend_spec", {})),
        "competitors_focus": state.get("competitors_focus", []) or state.get("drivers_focus", []),
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
    Works with any racing domain.
    """
    query_lower = state.get("user_query", "").lower()

    # Simple keyword-based analysis
    factor_analysis = {
        "primary_question": state.get("user_query", ""),
        "key_factors": [],
        "data_sources_needed": {
            "results": True,  # Always useful
            "lap_times": "lap" in query_lower or "pace" in query_lower or "fast" in query_lower,
            "qualifying": "qualifying" in query_lower or "quali" in query_lower or "grid" in query_lower,
            "pit_stops": "pit" in query_lower or "stop" in query_lower or "strategy" in query_lower,
            "weather": "weather" in query_lower or "rain" in query_lower or "wet" in query_lower,
            "standings": "championship" in query_lower or "standing" in query_lower or "point" in query_lower,
        },
        "comparisons": [],
        "time_windows": ["entire event"],
        "hypotheses": ["Performance differences may be explained by strategy, pace, or conditions"],
        "analysis_approach": "Compare key metrics across entities"
    }

    # Add key factors based on keywords
    if any(kw in query_lower for kw in ["tire", "tyre", "compound"]):
        factor_analysis["key_factors"].append("tire_strategy")
    if any(kw in query_lower for kw in ["weather", "rain", "wet", "dry"]):
        factor_analysis["key_factors"].append("weather_conditions")
    if any(kw in query_lower for kw in ["pace", "fast", "speed", "quick"]):
        factor_analysis["key_factors"].append("lap_pace")
    if any(kw in query_lower for kw in ["pit", "stop", "strategy"]):
        factor_analysis["key_factors"].append("pit_strategy")
    if any(kw in query_lower for kw in ["crash", "incident", "accident"]):
        factor_analysis["key_factors"].append("incidents")
    if any(kw in query_lower for kw in ["start", "grid", "position"]):
        factor_analysis["key_factors"].append("grid_position")
        
    if not factor_analysis["key_factors"]:
        factor_analysis["key_factors"] = ["overall_performance", "strategy", "pace"]

    return {
        "analysis_outputs": {
            **state.get("analysis_outputs", {}),
            "factor_analysis": factor_analysis
        }
    }
