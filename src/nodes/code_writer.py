from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.tools.analysis_tools import run_python
from src.tools.data_tools import inspect_dataset
from src.config import CONFIG
from textwrap import dedent
import json

def code_writer(state: WeekendState):
    """
    Generates and executes Python code to perform the analysis.
    """
    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.1)

    data_paths = state["analysis_outputs"].get("data_paths", {})
    teams_focus = state.get("teams_focus", [])
    drivers_focus = state.get("drivers_focus", [])
    weekend = state.get("weekend_spec")
    race_id = weekend.get("race_id") if weekend else None
    if race_id is None:
        raise ValueError("weekend_spec missing race_id for code_writer")
    schemas = inspect_dataset.invoke({"schema_only": True})
    schemas_str = json.dumps(schemas, indent=2, default=str)
    plan_text = state.get("plan_review") or state.get("plan", "")

    # If we have previous errors, we include them in the prompt for correction
    error_context = ""
    if state.get("errors"):
        last_error = state['errors'][-1]
        error_context = f"Previous execution failed with errors:\n{last_error}\n\nPlease fix the code."
        last_stderr = state.get("analysis_outputs", {}).get("stderr", "")
        if last_stderr:
            # Include full traceback for better debugging
            error_context += f"\n\nFull stderr (last 1500 chars):\n{last_stderr[-1500:]}"

        # Analyze error type and provide specific guidance
        if "missing {" in str(last_error) or "PatternError" in last_stderr:
            error_context += dedent("""

            CRITICAL FIX REQUIRED - REGEX ERROR:
            - DO NOT use df.replace(pattern, value, regex=True) for simple string replacement
            - USE: for col in df.select_dtypes(include=['object']).columns: df[col] = df[col].replace('\\N', np.nan)
            - The \\N pattern is causing regex parsing errors
            """)
        elif "KeyError" in str(last_error):
            error_context += dedent("""

            CRITICAL: Column not found. Before selecting columns, check df.columns and add missing ones with defaults.
            Use a helper like ensure_columns(df, {'num_stops': 0, 'total_pit_time': 0}) before merging/selection.
            """)
        elif "to_datetime" in last_stderr:
            error_context += "\n\nCRITICAL: Do not use pd.to_datetime on duration columns. Use time_to_seconds() instead."

    def build_header(paths_str: str, race_id: int, teams_focus: list, drivers_focus: list = None) -> str:
        """
        Provide ONLY imports, utilities, and configuration.
        The LLM will generate ALL data loading and processing code.
        """
        # Get teams and drivers from focus
        teams_list = teams_focus if teams_focus else []
        drivers_list = drivers_focus if drivers_focus else []
        missing_token = "\\N"
        return dedent(
            f"""
            import os
            from pathlib import Path
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            import seaborn as sns

            # ============================================================
            # CONFIGURATION - Use these in your code
            # ============================================================
            DATA_PATHS = {paths_str}
            RACE_ID = {race_id}
            TEAMS_FOCUS = {teams_list}
            DRIVERS_FOCUS = {drivers_list}
            MISSING_TOKEN = {missing_token!r}

            # ============================================================
            # CRITICAL SCHEMA REFERENCE - Use these exact column names!
            # ============================================================
            # results table columns: ['resultId', 'raceId', 'driverId', 'constructorId', 'number', 'grid',
            #                         'position', 'positionText', 'positionOrder', 'points', 'laps', 'time',
            #                         'milliseconds', 'fastestLap', 'rank', 'fastestLapTime', 'fastestLapSpeed', 'statusId']
            #
            # drivers table columns: ['driverId', 'driverRef', 'number', 'code', 'forename', 'surname',
            #                         'dob', 'nationality', 'url']
            #
            # constructors table columns: ['constructorId', 'constructorRef', 'name', 'nationality', 'url']
            #
            # laps table columns: ['raceId', 'driverId', 'lap', 'position', 'time', 'milliseconds']
            #
            # pits table columns: ['raceId', 'driverId', 'stop', 'lap', 'time', 'duration', 'milliseconds']
            #                     NOTE: 'stop' column is ONLY in pits table, NOT in results!
            #
            # IMPORTANT:
            # - ONLY results, laps, and pits have 'raceId'. DO NOT filter drivers/constructors on raceId.
            # - Filter by raceId on results/laps/pits first, THEN merge in driver/constructor info.
            # IMPORTANT: After merging results with constructors, use 'name' for team name, NOT 'name_constructor'
            # IMPORTANT: 'stop' column is ONLY in pits table - don't try to access it from results!

            OUTPUT_DIR = Path("outputs")
            VIS_DIR = Path("analysis_vis")
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            VIS_DIR.mkdir(parents=True, exist_ok=True)

            sns.set_theme(style="whitegrid")

            # Matplotlib scatter helper to auto-broadcast scalars and avoid shape errors
            def _broadcast_xy(x, y):
                x_arr = np.asarray(x)
                y_arr = np.asarray(y)
                x_len, y_len = x_arr.size, y_arr.size
                if x_len != y_len:
                    if x_len == 1 and y_len > 1:
                        x_arr = np.full(y_len, x_arr.flat[0])
                    elif y_len == 1 and x_len > 1:
                        y_arr = np.full(x_len, y_arr.flat[0])
                    else:
                        raise ValueError(f"x and y must be the same size (x={{x_len}}, y={{y_len}})")
                return x_arr, y_arr

            _ORIG_SCATTER = plt.scatter
            def scatter_safe(x, y, *args, **kwargs):
                x_arr, y_arr = _broadcast_xy(x, y)
                return _ORIG_SCATTER(x_arr, y_arr, *args, **kwargs)
            plt.scatter = scatter_safe

            from matplotlib.axes import Axes
            _ORIG_AX_SCATTER = Axes.scatter
            def axes_scatter_safe(self, x, y, *args, **kwargs):
                x_arr, y_arr = _broadcast_xy(x, y)
                return _ORIG_AX_SCATTER(self, x_arr, y_arr, *args, **kwargs)
            Axes.scatter = axes_scatter_safe

            # ============================================================
            # UTILITY FUNCTIONS - Use these helpers
            # ============================================================
            def time_to_seconds(val):
                \"\"\"Convert time strings like '1:24.319' or '1:01:02.345' to total seconds.\"\"\"
                if val is None or pd.isna(val):
                    return np.nan
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    val = val.strip()
                    if val.startswith("+"):
                        val = val[1:]
                    if not val or val == MISSING_TOKEN:
                        return np.nan
                    parts = val.split(":")
                    try:
                        if len(parts) == 3:
                            hours, minutes, seconds = parts
                            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                        if len(parts) == 2:
                            minutes, seconds = parts
                            return int(minutes) * 60 + float(seconds)
                        return float(val)
                    except (ValueError, TypeError):
                        return np.nan
                return np.nan

            def ensure_columns(df, defaults: dict):
                \"\"\"Ensure required columns exist; if missing, add with default values.\"\"\"
                for col, default in defaults.items():
                    if col not in df.columns:
                        df[col] = default
                return df

            # ============================================================
            # YOUR CODE STARTS HERE
            # Generate ALL data loading, cleaning, analysis, and visualization code below
            # ============================================================

            """
        )

    # Get factor analysis for intelligent code generation
    factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
    factor_context = ""

    if factor_analysis:
        factor_context = f"""
INTELLIGENT FACTOR ANALYSIS CONTEXT:
The query has been analyzed to identify what matters most:

Key Factors: {factor_analysis.get('key_factors', [])}
Hypotheses to Test: {factor_analysis.get('hypotheses', [])}
Comparisons Needed: {factor_analysis.get('comparisons', [])}
Analysis Approach: {factor_analysis.get('analysis_approach', '')}

Use this context to generate MORE COMPREHENSIVE and INTELLIGENT code.
Think about WHY results differ, not just WHAT they are.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Python Data Scientist specializing in F1 with ADVANCED ANALYTICAL THINKING.
Generate complete, autonomous Python code to perform COMPREHENSIVE analysis described in the plan.

You are now SMARTER - you understand what factors affect race outcomes and should analyze accordingly.

ENVIRONMENT:
- All imports, helpers, and configuration are already available
- Variables: DATA_PATHS, RACE_ID, TEAMS_FOCUS, DRIVERS_FOCUS, time_to_seconds(), etc.
- Your code will be appended to the header, so just write the analysis logic
- **DO NOT redefine DRIVERS_FOCUS, TEAMS_FOCUS, RACE_ID - use them as-is from the header**

{factor_context}

CRITICAL RULES:

0. DRIVER FOCUS (MOST IMPORTANT):
   - DRIVERS_FOCUS contains the driver surnames from the query (e.g., ["Verstappen", "Hamilton"])
   - You MUST filter your analysis to ONLY these specific drivers
   - After joining results with drivers table, filter: race_full[race_full['surname'].isin(DRIVERS_FOCUS)]
   - DO NOT analyze all drivers or just the top finishers - ONLY the ones in DRIVERS_FOCUS
   - If DRIVERS_FOCUS is empty, analyze all drivers

1. DATA LOADING:
   - Load ALL required tables: results, drivers, constructors, laps, pits
   - Use: `pd.read_parquet(DATA_PATHS['results_path'])` etc.

2. DATA CLEANING (CRITICAL - DO THIS FIRST):
   - Replace '\\N' with NaN in ALL dataframes IMMEDIATELY after loading
   - Use DIRECT STRING REPLACEMENT (not regex):
     ```python
     for col in df.select_dtypes(include=['object']).columns:
         df[col] = df[col].replace(MISSING_TOKEN, np.nan)
     ```
   - Convert numeric columns with errors='coerce'

3. FILTERING & JOINS:
   - Filter by RACE_ID variable (don't hardcode the race number)
   - Always join results → drivers → constructors to get full info
   - Handle column name collisions with suffixes parameter

4. TIME CONVERSIONS:
   - Use time_to_seconds() for duration columns (time, fastestLapTime, etc.)
   - Do NOT use pd.to_datetime on these columns

5. DRIVER FILTERING (CRITICAL):
   - The DRIVERS_FOCUS list contains the drivers mentioned in the query
   - You MUST filter to ONLY those specific drivers by matching surnames
   - Example: if DRIVERS_FOCUS = ["Verstappen", "Hamilton"], filter where surname contains "Verstappen" or "Hamilton"
   - DO NOT just take top N finishers - use the ACTUAL drivers from the query

6. TEAM FILTERING:
   - Use TEAMS_FOCUS variable if provided
   - If empty, analyze all teams: `race_full['name'].unique().tolist()`

7. COMPARATIVE ANALYSIS (CRITICAL - BE SMART):
   - Compare lap times STINT-BY-STINT (not just overall average)
   - Analyze tire degradation: lap times trend within each stint
   - Compare pit strategies: when did they pit? what compounds?
   - Calculate pace deltas between drivers/teams over time
   - Identify when performance gaps changed (pit stops, incidents, etc.)
   - For strategy comparison: visualize compound choice timing

8. TIME-BASED PATTERNS:
   - Track how pace evolved lap-by-lap
   - Identify fastest laps and when they occurred
   - Analyze performance in different race phases (start, middle, end)
   - Show position changes over time

9. MULTI-DIMENSIONAL VISUALIZATIONS:
   - Lap time evolution plots (line plot per driver, colored by stint/tire)
   - Strategy timeline (horizontal bar showing tire compounds used)
   - Pace delta heatmap (driver vs driver by lap/stint)
   - Box plots for stint performance comparison
   - Scatter plots for pit timing vs final position

10. OUTPUTS (MANDATORY):
   - MUST save metrics to: OUTPUT_DIR / "analysis_metrics.parquet"
   - Save all visualizations to: VIS_DIR / "plot_name.png"
   - Print clear step messages and results
   - Include statistical summaries (mean, median, std for key metrics)

11. ERROR HANDLING:
   - Do NOT use try-except blocks
   - Let errors surface so they can be debugged

12. WINNER REPORTING:
   - Find winner using: race_results[race_results['positionOrder'] == 1]
   - Print actual values from data, never hardcode
   - Explain WHY they won based on the analysis

13. SCHEMA AWARENESS (CRITICAL - READ CAREFULLY):
   - 'stop' column is ONLY in pits table, NOT in results!
   - After merging results with constructors, team name is in 'name' column, NOT 'name_constructor'
   - results table has: positionOrder, points, laps, milliseconds, fastestLapTime, fastestLapSpeed
   - drivers table has: surname, forename, code, driverId
   - pits table has: stop, lap, duration, milliseconds (for pit stop count and timing)
   - laps table has: lap, position, time, milliseconds (for lap-by-lap analysis)

   CORRECT PIT STOP ANALYSIS PATTERN:
   ```python
   # Load pit data separately
   pits = pd.read_parquet(DATA_PATHS['pits_path'])
   pits = pits[pits['raceId'] == RACE_ID]

   # Clean pits data
   for col in pits.select_dtypes(include=['object']).columns:
       pits[col] = pits[col].replace(MISSING_TOKEN, np.nan)
   for col in pits.select_dtypes(include=['number']).columns:
       pits[col] = pd.to_numeric(pits[col], errors='coerce')

   # Get pit stop counts per driver
   pit_counts = pits.groupby('driverId').agg(
       num_stops=('stop', 'max'),
       total_pit_time=('milliseconds', 'sum')
   ).reset_index()

   # Merge with results AFTER computing pit metrics
   race_full = race_full.merge(pit_counts, on='driverId', how='left')
   # Fill NaN values for drivers with no pit stops
   race_full['num_stops'] = race_full['num_stops'].fillna(0)
   race_full['total_pit_time'] = race_full['total_pit_time'].fillna(0)
   ```

   WRONG (DO NOT DO THIS):
   ```python
   # WRONG: 'stop' doesn't exist in race_full after merging results+drivers+constructors
   race_full.groupby('surname').agg(pit_stops=('stop', 'max'))  # ERROR!

   # WRONG: Don't try to use num_stops before creating it
   analysis_results.groupby('driverId').agg(num_stops=('num_stops', 'first'))  # ERROR!

   # WRONG: Don't try to aggregate columns from another table
   analysis_results = race_full.merge(lap_counts, on='driverId', how='left').merge(
       pit_counts, on='driverId', how='left'
   )
   # Then trying to aggregate analysis_results where lap_counts/pit_counts don't exist yet
   ```

Available Data:
{data_paths}

Schemas:
{schemas}

Weekend: {weekend}
Teams Focus: {teams_focus}
**Drivers Focus: {drivers_focus}** ← YOU MUST ANALYZE ALL OF THESE DRIVERS

Analysis Plan:
{plan}

{error_context}

IMPORTANT: Generate COMPLETE code from data loading through visualization.
Return ONLY Python code, no markdown backticks.
"""),
        ("user", "Generate the complete analysis code.")
    ])
    
    paths_str = str(data_paths)
    
    chain = prompt | llm
    
    print(f"\n=== [Code Writer] Generating Code (Attempt {len(state.get('code_snippets', [])) + 1}) ===")
    
    try:
        response = chain.invoke({
            "data_paths": paths_str,
            "plan": plan_text,
            "error_context": error_context,
            "weekend": str(weekend),
            "drivers_focus": str(drivers_focus),
            "teams_focus": str(teams_focus),
            "schemas": schemas_str,
            "race_id": race_id,
            "factor_context": factor_context,
        })
    except Exception as e:
        # Surface LLM failures (e.g., rate limits) without crashing the graph
        err_msg = f"LLM code generation failed: {e}"
        return {
            "errors": state.get("errors", []) + [err_msg],
            "analysis_outputs": state.get("analysis_outputs", {})
        }
    
    code = response.content
    print(f"=== [Code Writer] Generated Code ===\n{code}\n(Total {len(code)} chars)\n================================\n")
    
    # Clean code
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0]
    elif "```" in code:
        code = code.split("```")[1].split("```")[0]
    
    # Post-process code to fix common LLM errors
    def fix_code(code_str: str) -> str:
        import re
        # Replace '\N' with r'\N' ONLY if it is NOT already raw.
        # Matches '\N' not preceded by r or R
        # We need to match the quote as well to be safe

        # Single quotes: replace '\N' with r'\N'
        code_str = re.sub(r"(?<![rR])'\\N'", "r'\\\\N'", code_str)
        # Double quotes: replace "\N" with r"\N"
        code_str = re.sub(r'(?<![rR])"\\N"', 'r"\\\\N"', code_str)
        # Raw strings with invalid \N escape -> add an extra backslash
        code_str = re.sub(r"r'\\N'", "r'\\\\N'", code_str)
        code_str = re.sub(r'r\"\\N\"', 'r"\\\\N"', code_str)
        # Fix common LLM typo: df[mask].['col'] or ] . [ -> turn into df[mask]['col']
        code_str = re.sub(r"\]\s*\.\s*\[", "][", code_str)

        return code_str

    code = fix_code(code)

    # Prepend the data paths definition to ensure the code runs
    header = build_header(paths_str, race_id, teams_focus, drivers_focus)
    full_code = header + code
    
    # Execute
    result = run_python.invoke({"code": full_code})
    
    def _filter_non_empty_tables(table_paths):
        non_empty = []
        for path in table_paths:
            try:
                import pandas as pd
                df = pd.read_parquet(path)
                if len(df) > 0:
                    non_empty.append(path)
            except Exception:
                # If a table cannot be read, treat as empty for validation purposes
                continue
        return non_empty

    if result["status"] == "error":
        analysis_outputs = {
            **state["analysis_outputs"],
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", "")
        }
        return {
            "errors": state.get("errors", []) + [result.get("error", "Unknown execution error")],
            "code_snippets": [full_code],
            "analysis_outputs": analysis_outputs
        }

    # Validate that we actually produced data
    tables = _filter_non_empty_tables(result.get("tables", []))
    figures = result.get("figures", [])
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    empty_output = (not tables) or ("Empty DataFrame" in stdout and not tables)

    if empty_output:
        err_msg = "Analysis completed but produced no data rows (empty tables)."
        return {
            "errors": state.get("errors", []) + [err_msg],
            "code_snippets": [full_code],
            "figures": figures,
            "analysis_outputs": {
                **state["analysis_outputs"],
                "tables": tables,
                "stdout": stdout,
                "stderr": stderr
            }
        }

    # Success
    return {
        "code_snippets": [full_code],
        "figures": figures,
        "analysis_outputs": {
            **state["analysis_outputs"],
            "tables": tables,
            "stdout": stdout,
            "stderr": stderr
        },
        "errors": [] # Clear errors
    }
