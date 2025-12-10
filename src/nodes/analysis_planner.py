from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.tools.data_tools import inspect_dataset
from src.config import CONFIG

def analysis_planner(state: WeekendState):
    """
    Plans the analysis based on the query and available data.
    Now enhanced with intelligent factor analysis to think about what matters.
    """
    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.1)

    # Inspect data to know what we have
    schemas = inspect_dataset.invoke({"schema_only": True})
    data_paths = state["analysis_outputs"].get("data_paths", {})

    # Get factor analysis if available
    factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
    factor_context = ""

    if factor_analysis:
        factor_context = f"""
INTELLIGENT FACTOR ANALYSIS:
The query has been analyzed to identify key factors that matter:

Primary Question: {factor_analysis.get('primary_question', 'Unknown')}

Key Factors to Consider: {factor_analysis.get('key_factors', [])}

Relevant Comparisons to Make:
{chr(10).join([f"  - Compare {c.get('entities', [])} on {c.get('metric', 'unknown')}" for c in factor_analysis.get('comparisons', [])])}

Hypotheses to Test:
{chr(10).join([f"  - {h}" for h in factor_analysis.get('hypotheses', [])])}

Analysis Approach: {factor_analysis.get('analysis_approach', 'Standard comparison')}

Time Windows of Interest: {factor_analysis.get('time_windows', ['entire race'])}

USE THIS CONTEXT to create a more intelligent and comprehensive analysis plan.
Think about these factors when planning your analysis.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an F1 Strategy Expert with deep analytical thinking. Plan a python analysis to answer the user's query.

You are now SMARTER - you understand what factors matter and should plan analysis accordingly.

CRITICAL RULES:
- Use ONLY the parquet files listed in DATA_PATHS. Do NOT invent file names.
- Use ONLY the columns shown in the supplied schemas.
- Assume the race of interest is exactly the WEEKEND_SPEC supplied.
- Handle '\\N' as missing and convert numeric/time columns before calculations.

INTELLIGENT ANALYSIS PLANNING:
- Think about WHY results differ (not just WHAT the results are)
- Plan multiple angles of analysis (pace, strategy, conditions)
- Consider time-based patterns (how did things evolve during the race?)
- Plan for comparative analysis (driver vs driver, team vs team, stint vs stint)
- Think about tire degradation, pit timing, and strategy differences

Available cached files (DATA_PATHS):
{data_paths}

Schemas for cached files:
{schemas}

Weekend context:
{weekend}

Focus:
{focus}

{factor_context}

Provide a comprehensive, numbered plan with the following labeled sections:

1) FACTORS & HYPOTHESES
   - What factors might explain the results?
   - What hypotheses should we test?

2) FILES TO LOAD
   - List ALL relevant data sources (use DATA_PATHS keys exactly)
   - Include: results, drivers, constructors, laps, pits

3) CLEANING STEPS
   - Missing values (\\N handling)
   - Type conversions (numeric, time)

4) JOINS & DATA INTEGRATION
   - Explicitly list join keys that exist in schema
   - Build complete dataset with all needed attributes

5) TIME-BASED ANALYSIS
   - Lap-by-lap pace evolution
   - Stint performance analysis
   - Pit timing strategy

6) COMPARATIVE METRICS
   - Driver comparisons (same team, different teams)
   - Team strategy differences
   - Tire strategy effectiveness
   - Pace deltas over time

7) VISUALIZATIONS
   - Lap time evolution plots (per driver, per stint)
   - Strategy comparison plots (pit timing, tire compounds)
   - Pace delta heatmaps
   - Position changes over time

8) INSIGHTS TO EXTRACT
   - What patterns to look for
   - What conclusions to draw

Think deeply. Be comprehensive. Plan for a multi-dimensional analysis.
"""),
        ("user", "{query}")
    ])
    
    chain = prompt | llm

    print(f"\n=== [Analysis Planner] Generating Intelligent Plan ===")
    print(f"Query: {state['user_query']}")
    if factor_analysis:
        print(f"Factors Identified: {factor_analysis.get('key_factors', [])}")

    response = chain.invoke({
        "schemas": str(schemas),
        "data_paths": str(data_paths),
        "weekend": str(state.get("weekend_spec")),
        "focus": f"Drivers: {state.get('drivers_focus')}, Teams: {state.get('teams_focus')}",
        "query": state["user_query"],
        "factor_context": factor_context
    })
    
    print(f"\n=== [Analysis Planner] Plan ===\n{response.content}\n===============================\n")
    
    return {"plan": response.content}
