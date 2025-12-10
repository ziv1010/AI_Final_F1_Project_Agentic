from src.state import WeekendState
from src.tools.data_tools import load_kaggle_weekend

def data_loader(state: WeekendState):
    """
    Loads the data for the identified weekend.
    """
    if not state.get("weekend_spec"):
        return {"errors": ["No weekend specified."]}
        
    race_id = state["weekend_spec"]["race_id"]
    
    paths = load_kaggle_weekend.invoke({"race_id": race_id})
    
    if "error" in paths:
        return {"errors": [paths["error"]]}
        
    return {"analysis_outputs": {"data_paths": paths}}
