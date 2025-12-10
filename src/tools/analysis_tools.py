import sys
import io
import contextlib
import os
from typing import Dict

import pandas as pd
import numpy as np
from langchain_core.tools import tool
from src.config import get_outputs_path

# Ensure matplotlib can write its cache before it initializes
os.environ.setdefault("MPLCONFIGDIR", str(get_outputs_path()))
import matplotlib.pyplot as plt
import seaborn as sns

@tool
def run_python(code: str) -> Dict:
    """
    Execute user-provided Python code in a sandboxed environment.
    The code has access to pandas (pd), numpy (np), matplotlib.pyplot (plt), and seaborn (sns).
    
    Args:
        code: The python code string to execute.
        
    Returns:
        Dictionary containing stdout, stderr, and any generated artifacts.
    """
    # Create outputs directory if it doesn't exist
    outputs_path = get_outputs_path()
    outputs_path.mkdir(parents=True, exist_ok=True)
    # Ensure matplotlib can write its cache in restricted environments
    import os
    os.environ.setdefault("MPLCONFIGDIR", str(outputs_path))
    
    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    # Execution context
    local_vars = {
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
        "DATA_PATHS": {}, # This should be populated by the caller if needed, or we rely on the code to define it
    }
    
    # We need to make sure the code can access the data paths. 
    # Usually the code generator will prepend a DATA_PATHS definition.
    
    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, local_vars)
            
        # Check for generated figures
        # We assume the code saves figures to the outputs directory
        # We can list files in outputs directory that were modified/created recently?
        # Or simply list all files in outputs
        
        figures = [str(p.resolve()) for p in outputs_path.rglob("*.png")]
        tables = [str(p.resolve()) for p in outputs_path.rglob("*.parquet")] # If they save tables
        
        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "figures": figures,
            "tables": tables,
            "status": "success"
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue() + ("\n" + tb),
            "error": str(e),
            "status": "error"
        }
