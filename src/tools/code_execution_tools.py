"""
Code Execution Tools for ReAct Agents.

Provides tools for:
1. Safe Python code execution
2. Code debugging and error analysis
3. Visualization saving
"""

from langchain_core.tools import tool
from typing import Optional, Dict, Any
from pathlib import Path
import sys
import io
import traceback
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


@tool
def run_python_code(code: str, timeout_seconds: int = 60) -> str:
    """
    Execute Python code and return the output.
    
    Use this tool to run data analysis code. The code can:
    - Load and process data with pandas
    - Perform statistical analysis with scipy/sklearn
    - Generate visualizations with matplotlib/seaborn
    - Calculate metrics and aggregations
    
    IMPORTANT:
    - Always use print() to output results you want to see
    - Save figures to files, don't try to display them
    - Handle potential errors in your code
    
    Args:
        code: Python code to execute
        timeout_seconds: Maximum execution time (default 60s)
    
    Returns:
        stdout output, any errors, and paths to saved files
    
    Examples:
        run_python_code("import pandas as pd; print(pd.read_csv('data.csv').head())")
        -> Returns the first 5 rows of the dataframe
    """
    # Capture stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = captured_stdout = io.StringIO()
    sys.stderr = captured_stderr = io.StringIO()
    
    saved_files = []
    error_info = None
    
    try:
        # Create a restricted globals environment
        exec_globals = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
        }
        
        # Add common imports
        import_code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')
"""
        exec(import_code, exec_globals)
        
        # Add data path helpers
        setup_code = """
from src.config import get_raw_data_path, get_cache_path
DATA_PATH = get_raw_data_path()
CACHE_PATH = get_cache_path()
OUTPUT_PATH = Path('outputs')
OUTPUT_PATH.mkdir(exist_ok=True)
"""
        try:
            exec(setup_code, exec_globals)
        except:
            # Fallback if src.config not available
            exec_globals['DATA_PATH'] = Path('data/raw')
            exec_globals['CACHE_PATH'] = Path('data/cache')
            exec_globals['OUTPUT_PATH'] = Path('outputs')
        
        # Execute user code
        exec(code, exec_globals)
        
        # Check for saved figures
        import matplotlib.pyplot as plt
        if plt.get_fignums():
            # Save any open figures
            for i, fig_num in enumerate(plt.get_fignums()):
                fig = plt.figure(fig_num)
                fig_path = f"outputs/figure_{fig_num}.png"
                fig.savefig(fig_path, dpi=150, bbox_inches='tight')
                saved_files.append(fig_path)
            plt.close('all')
        
    except Exception as e:
        error_info = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    # Build output
    stdout_content = captured_stdout.getvalue()
    stderr_content = captured_stderr.getvalue()
    
    output_parts = []
    
    if stdout_content:
        output_parts.append(f"**Output:**\n```\n{stdout_content[:5000]}\n```")
        if len(stdout_content) > 5000:
            output_parts.append("... (output truncated)")
    
    if stderr_content:
        output_parts.append(f"**Warnings:**\n```\n{stderr_content[:1000]}\n```")
    
    if saved_files:
        output_parts.append(f"**Saved files:** {saved_files}")
    
    if error_info:
        output_parts.append(
            f"**ERROR ({error_info['type']}):**\n"
            f"{error_info['message']}\n\n"
            f"**Traceback:**\n```\n{error_info['traceback'][-2000:]}\n```"
        )
    
    if not output_parts:
        output_parts.append("Code executed successfully (no output)")
    
    return "\n\n".join(output_parts)


@tool
def debug_code(code: str, error_message: str) -> str:
    """
    Analyze code that produced an error and suggest fixes.
    
    Use this tool when run_python_code fails. It will analyze the
    error and provide corrected code.
    
    Args:
        code: The Python code that failed
        error_message: The error message/traceback from the failure
    
    Returns:
        Analysis of the issue and corrected code
    
    Examples:
        debug_code("df = pd.read_csv('file.csv')", "FileNotFoundError: ...")
        -> Returns analysis and fixed code with correct path
    """
    # Common error patterns and fixes
    fixes = []
    
    error_lower = error_message.lower()
    
    # File not found
    if "filenotfound" in error_lower or "no such file" in error_lower:
        fixes.append({
            "issue": "File path issue",
            "suggestion": "Use DATA_PATH / 'filename.csv' instead of hardcoded paths",
            "example": "df = pd.read_csv(DATA_PATH / 'results.csv')"
        })
    
    # KeyError (column not found)
    if "keyerror" in error_lower:
        fixes.append({
            "issue": "Column name not found",
            "suggestion": "Check available columns with df.columns first",
            "example": "print(df.columns.tolist())  # Check available columns"
        })
    
    # ModuleNotFoundError
    if "modulenotfound" in error_lower or "no module named" in error_lower:
        fixes.append({
            "issue": "Missing import",
            "suggestion": "Add the missing import at the top of your code",
            "example": "import pandas as pd  # Make sure to import required modules"
        })
    
    # ValueError
    if "valueerror" in error_lower:
        fixes.append({
            "issue": "Invalid value or type conversion",
            "suggestion": "Check data types and handle NaN values",
            "example": "df = df.dropna() or df['col'] = pd.to_numeric(df['col'], errors='coerce')"
        })
    
    # TypeError
    if "typeerror" in error_lower:
        fixes.append({
            "issue": "Type mismatch",
            "suggestion": "Check variable types and convert as needed",
            "example": "df['col'] = df['col'].astype(str) or df['col'].astype(float)"
        })
    
    # Memory error
    if "memory" in error_lower:
        fixes.append({
            "issue": "Memory overflow",
            "suggestion": "Process data in chunks or filter to smaller subset",
            "example": "df = pd.read_csv(file, nrows=10000)  # Limit rows"
        })
    
    # Syntax error
    if "syntaxerror" in error_lower or "indentation" in error_lower:
        fixes.append({
            "issue": "Syntax or indentation error",
            "suggestion": "Check code formatting, parentheses, and indentation",
            "example": "Ensure consistent indentation (4 spaces) and matching brackets"
        })
    
    # Build response
    response_parts = [
        "**Error Analysis:**",
        f"```\n{error_message[:500]}\n```\n"
    ]
    
    if fixes:
        response_parts.append("**Identified Issues:**")
        for fix in fixes:
            response_parts.append(f"\n• **{fix['issue']}**")
            response_parts.append(f"  Suggestion: {fix['suggestion']}")
            response_parts.append(f"  Example: `{fix['example']}`")
    
    # Provide debugging template
    response_parts.append("\n**Debugging Template:**")
    response_parts.append("```python")
    response_parts.append("# First, check what data is available")
    response_parts.append("import os")
    response_parts.append("print('Available files:', os.listdir(DATA_PATH))")
    response_parts.append("")
    response_parts.append("# Then load and inspect")
    response_parts.append("df = pd.read_csv(DATA_PATH / 'your_file.csv')")
    response_parts.append("print('Shape:', df.shape)")
    response_parts.append("print('Columns:', df.columns.tolist())")
    response_parts.append("print('Sample:', df.head())")
    response_parts.append("```")
    
    return "\n".join(response_parts)


@tool
def save_visualization(
    code: str,
    filename: str,
    title: str = ""
) -> str:
    """
    Generate and save a matplotlib/seaborn visualization.
    
    Use this tool specifically for creating and saving charts.
    The figure will be saved to the outputs directory.
    
    Args:
        code: Python code that creates a matplotlib figure
              (should NOT include plt.show() or plt.savefig())
        filename: Name for the saved file (without extension)
        title: Optional title to add to the figure
    
    Returns:
        Path to the saved visualization
    
    Examples:
        save_visualization(
            "plt.figure(figsize=(10,6)); plt.bar(df['x'], df['y'])",
            "bar_chart",
            "Results by Category"
        )
    """
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    try:
        # Set up environment
        exec_globals = {
            "__builtins__": __builtins__,
        }
        
        # Import common libraries
        exec("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
plt.style.use('seaborn-v0_8-whitegrid')
""", exec_globals)
        
        # Add data paths
        try:
            exec("""
from src.config import get_raw_data_path
DATA_PATH = get_raw_data_path()
""", exec_globals)
        except:
            exec_globals['DATA_PATH'] = Path('data/raw')
        
        # Execute visualization code
        exec(code, exec_globals)
        
        # Add title if provided
        if title:
            plt.title(title, fontsize=14, fontweight='bold')
        
        # Save figure
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / f"{filename}.png"
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close('all')
        
        return f"**Visualization saved:** {filepath}"
        
    except Exception as e:
        return f"Error creating visualization: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
