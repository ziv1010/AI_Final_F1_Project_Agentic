import yaml
import os
from pathlib import Path
from datetime import datetime

def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

CONFIG = load_config()

# Global run ID management
_current_run_id: str = None

def start_new_run(query: str = None) -> str:
    """
    Start a new run with a unique ID.
    Returns the run ID (timestamp-based).
    """
    global _current_run_id
    _current_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create run directory
    run_dir = get_run_output_path()
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Write run metadata
    metadata_path = run_dir / "run_metadata.txt"
    with open(metadata_path, "w") as f:
        f.write(f"Run ID: {_current_run_id}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        if query:
            f.write(f"Query: {query}\n")
    
    print(f"[Run Manager] Started run: {_current_run_id}")
    return _current_run_id

def get_current_run_id() -> str:
    """Get the current run ID, or create one if not set."""
    global _current_run_id
    if _current_run_id is None:
        start_new_run()
    return _current_run_id

def set_run_id(run_id: str):
    """Manually set the run ID (for testing or resuming)."""
    global _current_run_id
    _current_run_id = run_id

def get_raw_data_path():
    return Path(os.getcwd()) / CONFIG["data"]["raw_path"]

def get_cache_path():
    return Path(os.getcwd()) / CONFIG["data"]["cache_path"]

def get_outputs_path():
    return Path(os.getcwd()) / CONFIG["data"]["outputs_path"]

def get_run_output_path() -> Path:
    """
    Get the output path for the current run.
    Creates a run-specific subdirectory: outputs/runs/YYYYMMDD_HHMMSS/
    """
    run_id = get_current_run_id()
    run_dir = get_outputs_path() / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

def get_run_vis_path() -> Path:
    """Get the visualization path for the current run."""
    vis_dir = get_run_output_path() / "visualizations"
    vis_dir.mkdir(parents=True, exist_ok=True)
    return vis_dir

