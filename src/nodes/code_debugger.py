"""
Code Debugger Node - Self-healing code execution system.

This node analyzes execution errors and automatically fixes common issues:
- Regex pattern errors
- Column name mismatches
- Data type issues
- Join failures
- Missing imports
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG
from src.tools.column_inspector import format_column_info_for_llm, search_column
from textwrap import dedent
import re


def code_debugger(state: WeekendState):
    """
    Analyzes code execution errors and suggests fixes.

    This node is called when code execution fails. It:
    1. Analyzes the error traceback
    2. Examines the code that failed
    3. Identifies the root cause
    4. Generates a corrected version
    """
    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.1)

    errors = state.get("errors", [])
    if not errors:
        # No errors to debug
        return {}

    last_error = errors[-1]
    code_snippets = state.get("code_snippets", [])

    if not code_snippets:
        return {}

    failed_code = code_snippets[-1]
    stderr = state.get("analysis_outputs", {}).get("stderr", "")
    stdout = state.get("analysis_outputs", {}).get("stdout", "")
    data_paths = state.get("analysis_outputs", {}).get("data_paths", {})

    # Extract specific error patterns and provide targeted fixes
    error_analysis = analyze_error_pattern(last_error, stderr)

    # Get column information if it's a column-related error
    column_info = ""
    if error_analysis['pattern'] == 'COLUMN_NOT_FOUND':
        # Extract the missing column name from error
        missing_col = extract_missing_column(last_error)
        if missing_col and data_paths:
            column_info = f"\n\n=== COLUMN INSPECTOR RESULTS ===\n"
            column_info += format_column_info_for_llm(data_paths)
            column_info += f"\n\nSearching for '{missing_col}':\n"
            search_results = search_column(missing_col, data_paths)
            if search_results['found_in']:
                column_info += f"Found exact matches:\n"
                for match in search_results['found_in']:
                    column_info += f"  - {match['dataset']}.{match['column']} ({match['dtype']})\n"
            if search_results['similar']:
                column_info += f"Similar columns:\n"
                for match in search_results['similar']:
                    column_info += f"  - {match['dataset']}.{match['column']} ({match['dtype']})\n"
            if not search_results['found_in'] and not search_results['similar']:
                column_info += f"No matches found. Check available columns above.\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", dedent("""You are an expert Python debugger specializing in data analysis code.

        Your task is to analyze the failed code and error, then provide a corrected version.

        CRITICAL DEBUGGING RULES:
        1. REGEX ERRORS:
           - NEVER use regex=True with df.replace() for simple string replacement
           - Use direct string replacement: df[col].replace(value, np.nan)
           - Escape special regex characters properly

        2. COLUMN ERRORS:
           - Check if columns exist before accessing: if 'col' in df.columns
           - Use df.columns.tolist() to see available columns
           - Handle missing columns gracefully

        3. JOIN ERRORS:
           - Always check if join keys exist in both dataframes
           - Use suffixes parameter to avoid column name collisions
           - Validate data types match before joining

        4. DATA TYPE ERRORS:
           - Use pd.to_numeric() with errors='coerce' for numeric conversions
           - Check for null values before operations
           - Handle mixed types in columns

        5. COMMON PATTERNS TO AVOID:
           - df.replace(r'\\N', np.nan, regex=True)  # BAD - regex pattern error
           - df[col].replace('\\N', np.nan)           # GOOD - direct replacement

           - df['time'] = pd.to_datetime(df['time']) # BAD - 'time' is duration
           - df['time_sec'] = df['time'].apply(time_to_seconds) # GOOD

        Error Analysis:
        {error_analysis}

        {column_info}

        Failed Code:
        ```python
        {failed_code}
        ```

        Error Message:
        {error}

        Stderr Output:
        {stderr}

        Stdout Output (last 500 chars):
        {stdout}

        INSTRUCTIONS:
        1. Identify the exact line causing the error
        2. Determine the root cause (regex, column, type, etc.)
        3. Provide a minimal fix - only change what's broken
        4. Return ONLY the corrected Python code
        5. Do NOT add try-except blocks - let errors surface
        6. Do NOT add new features - just fix the error

        Return the complete corrected code without markdown backticks.
        """)),
        ("user", "Fix the code to resolve this error. Return only the corrected Python code.")
    ])

    chain = prompt | llm

    print(f"\n=== [Code Debugger] Analyzing Error ===")
    print(f"Error: {last_error[:200]}...")
    print(f"Error Pattern: {error_analysis['pattern']}")
    print(f"Suggested Fix: {error_analysis['fix']}")

    try:
        response = chain.invoke({
            "failed_code": failed_code[-3000:],  # Last 3000 chars to stay within limits
            "error": last_error,
            "stderr": stderr[-1000:] if stderr else "",
            "stdout": stdout[-500:] if stdout else "",
            "error_analysis": error_analysis["description"],
            "column_info": column_info
        })

        corrected_code = response.content

        # Clean markdown if present
        if "```python" in corrected_code:
            corrected_code = corrected_code.split("```python")[1].split("```")[0]
        elif "```" in corrected_code:
            corrected_code = corrected_code.split("```")[1].split("```")[0]

        print(f"=== [Code Debugger] Generated Fix ({len(corrected_code)} chars) ===\n")

        return {
            "code_snippets": [corrected_code],
            "errors": []  # Clear errors to allow retry
        }

    except Exception as e:
        print(f"[Code Debugger] Failed to generate fix: {e}")
        # Don't add to errors, just return empty to let graph handle it
        return {}


def analyze_error_pattern(error_msg: str, stderr: str) -> dict:
    """
    Analyze error patterns and provide targeted fix suggestions.

    Returns:
        dict with keys: pattern, description, fix
    """
    full_error = f"{error_msg}\n{stderr}"

    # Pattern 1: Regex errors with \N
    if "missing {" in full_error or "PatternError" in full_error:
        if "\\N" in full_error or r'\N' in full_error:
            return {
                "pattern": "REGEX_ESCAPE_ERROR",
                "description": "The code uses regex=True with an improperly escaped pattern. The \\N pattern is being interpreted as a regex, causing 'missing {' error.",
                "fix": "Replace df.replace(pattern, value, regex=True) with direct string replacement: for col in df.select_dtypes(include=['object']).columns: df[col] = df[col].replace('\\N', np.nan)"
            }

    # Pattern 2: Column not found
    if "KeyError" in full_error or "not in index" in full_error:
        # Extract column name from error
        match = re.search(r"KeyError: ['\"]([^'\"]+)['\"]", full_error)
        col_name = match.group(1) if match else "unknown"
        return {
            "pattern": "COLUMN_NOT_FOUND",
            "description": f"Column '{col_name}' does not exist in the dataframe.",
            "fix": f"Check available columns with df.columns.tolist() and verify '{col_name}' exists. May need to join with another table first."
        }

    # Pattern 3: Type errors
    if "TypeError" in full_error or "cannot convert" in full_error:
        return {
            "pattern": "TYPE_CONVERSION_ERROR",
            "description": "Data type conversion failed. Column may contain non-numeric values or nulls.",
            "fix": "Use pd.to_numeric(df['col'], errors='coerce') to handle mixed types. Check for null values with df['col'].isna().sum()"
        }

    # Pattern 4: Join/merge errors
    if "can only merge" in full_error or "MergeError" in full_error:
        return {
            "pattern": "JOIN_ERROR",
            "description": "Merge operation failed due to incompatible keys or missing columns.",
            "fix": "Verify both dataframes have the join key. Check dtypes match with df.dtypes. Use how='left' or how='inner' explicitly."
        }

    # Pattern 5: DateTime parsing errors
    if "to_datetime" in full_error or "DateParseError" in full_error:
        return {
            "pattern": "DATETIME_PARSE_ERROR",
            "description": "Attempted to parse duration/gap field as datetime. These are time deltas, not timestamps.",
            "fix": "Use time_to_seconds() helper function instead of pd.to_datetime() for duration columns like 'time', 'fastestLapTime', etc."
        }

    # Pattern 6: Empty DataFrame operations
    if "empty" in full_error.lower() or "no objects to concatenate" in full_error:
        return {
            "pattern": "EMPTY_DATAFRAME",
            "description": "Operation performed on empty DataFrame.",
            "fix": "Add check: if not df.empty: before operations. Verify filters aren't too restrictive."
        }

    # Pattern 7: Index errors
    if "IndexError" in full_error or "out of bounds" in full_error:
        return {
            "pattern": "INDEX_ERROR",
            "description": "Attempted to access index that doesn't exist.",
            "fix": "Check DataFrame length before indexing. Use .iloc[0] with conditional: if len(df) > 0"
        }

    # Generic pattern
    return {
        "pattern": "UNKNOWN_ERROR",
        "description": f"Unrecognized error pattern. Error: {error_msg[:200]}",
        "fix": "Review the full stack trace and identify the failing line. Check data types and column names."
    }


def extract_missing_column(error_msg: str) -> str:
    """Extract the missing column name from a KeyError message."""
    # Try different patterns
    patterns = [
        r"KeyError: ['\"]([^'\"]+)['\"]",  # KeyError: 'column_name'
        r"\['([^'\"]+)'\] not in index",  # ['column_name'] not in index
        r"Column\(s\) \['([^'\"]+)'\]",   # Column(s) ['column_name']
    ]

    for pattern in patterns:
        match = re.search(pattern, error_msg)
        if match:
            return match.group(1)

    return None


def validate_code_syntax(code: str) -> tuple[bool, str]:
    """
    Validate Python code syntax before execution.

    Returns:
        (is_valid, error_message)
    """
    try:
        compile(code, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
