import sys
import os
import pandas as pd
from src.tools.data_tools import list_weekends, load_kaggle_weekend
from src.tools.analysis_tools import run_python

def debug_pipeline():
    print("=== Debugging Pipeline ===")
    
    # 1. Check Environment
    print("\n1. Checking Environment...")
    try:
        import pyarrow
        print("pyarrow is installed.")
    except ImportError:
        print("ERROR: pyarrow is NOT installed.")
        
    try:
        import fastparquet
        print("fastparquet is installed.")
    except ImportError:
        print("fastparquet is NOT installed (optional if pyarrow works).")
        
    # 2. Check Data Tools
    print("\n2. Testing list_weekends...")
    weekends = list_weekends.invoke({"filter_str": "Bahrain 2023"})
    print(f"Found: {weekends}")
    
    if not weekends or "error" in weekends[0]:
        print("Skipping load test due to list failure.")
        return

    race_id = weekends[0]["race_id"]
    print(f"\n3. Testing load_kaggle_weekend for race_id {race_id}...")
    paths = load_kaggle_weekend.invoke({"race_id": race_id})
    print(f"Paths: {paths}")
    
    if "error" in paths:
        print("ERROR in loading data.")
        # Try to debug why
        # Maybe print the error from the tool
    else:
        print("Data loaded successfully.")
        
    # 4. Check Analysis Tools
    print("\n4. Testing run_python...")
    code = """
import pandas as pd
print("Hello from sandbox")
df = pd.DataFrame({"a": [1, 2, 3]})
print(df)
"""
    result = run_python.invoke({"code": code})
    print(f"Result: {result}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    debug_pipeline()
