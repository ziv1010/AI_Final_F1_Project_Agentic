import pandas as pd
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional
from langchain_core.tools import tool
from src.config import get_raw_data_path, get_cache_path


def _normalize(text: str) -> str:
    """
    Lowercase and strip accents so keyword matching works with names like 'São Paulo'.
    """
    text = str(text).lower()
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )

@tool
def list_weekends(filter_str: Optional[str] = None) -> List[Dict]:
    """
    List F1 race weekends from the database.
    Args:
        filter_str: Optional string to filter by year or race name (e.g. "2023" or "Bahrain").
    Returns:
        List of dictionaries containing race details.
    """
    raw_path = get_raw_data_path()
    races_path = raw_path / "races.csv"
    circuits_path = raw_path / "circuits.csv"
    
    if not races_path.exists():
        return [{"error": f"races.csv not found in {raw_path}"}]
        
    races = pd.read_csv(races_path)
    circuits = pd.read_csv(circuits_path)
    
    # Merge to get circuit name, country and location
    races = races.merge(circuits, on="circuitId", how="left")

    # Build a normalized search string that includes race name, circuit, country and location
    search_text = (
        races["year"].astype(str)
        + " "
        + races["name_x"].apply(_normalize)
        + " "
        + races["name_y"].apply(_normalize)
        + " "
        + races["location"].fillna("").apply(_normalize)
        + " "
        + races["country"].fillna("").apply(_normalize)
    )

    if filter_str:
        keywords = [_normalize(kw) for kw in str(filter_str).split() if kw.strip()]
        # Score rows by keyword hits (no strict AND to avoid empty results)
        scores = []
        for text in search_text:
            score = sum(1 for kw in keywords if kw in text)
            scores.append(score)
        races["score"] = scores
        # If no keywords matched, fall back to zero scores but keep recent races first
        races = races.sort_values(["score", "date"], ascending=[False, False])
    else:
        races["score"] = 0
        races = races.sort_values("date", ascending=False)

    results = []
    for _, row in races.head(20).iterrows():  # Limit to 20 to avoid context overflow
        results.append({
            "race_id": int(row["raceId"]),
            "year": int(row["year"]),
            "round": int(row["round"]),
            "name": row["name_x"],
            "circuit": row["name_y"],
            "country": row.get("country"),
            "location": row.get("location"),
            "date": row["date"],
            "score": int(row.get("score", 0)),
        })
    return results

@tool
def load_kaggle_weekend(race_id: int) -> Dict:
    """
    Load and cache data for a specific race weekend.
    Args:
        race_id: The unique ID of the race.
    Returns:
        Dictionary of paths to the cached parquet files.
    """
    raw_path = get_raw_data_path()
    cache_path = get_cache_path()
    cache_path.mkdir(parents=True, exist_ok=True)
    
    files_map = {
        "results": "results.csv",
        "laps": "lap_times.csv",
        "pits": "pit_stops.csv",
        "drivers": "drivers.csv",
        "constructors": "constructors.csv",
        "races": "races.csv"
    }
    
    output_paths = {}
    
    try:
        # Load races first to get context if needed, but mainly we filter other tables by raceId
        # Note: drivers and constructors are metadata, so we might want the full set or filtered.
        # Let's filter results/laps/pits by raceId. Drivers/Constructors we keep full or filter to those present.
        
        for key, filename in files_map.items():
            src = raw_path / filename
            if not src.exists():
                print(f"Warning: {filename} not found.")
                continue
                
            df = pd.read_csv(src)
            
            # Historically we filtered by raceId, but that prevents season-wide questions.
            # Keep the full table so analyses can span multiple races/seasons.
            dest = cache_path / f"r{race_id}_{key}.parquet"
            df.to_parquet(dest, index=False)
            output_paths[f"{key}_path"] = str(dest.absolute())
            
        return output_paths
    except Exception as e:
        return {"error": str(e)}

@tool
def inspect_dataset(schema_only: bool = True) -> Dict:
    """
    Inspect the cached dataset files to understand available columns.
    Args:
        schema_only: If True, returns only column names and types.
    Returns:
        Dictionary of schemas for available files.
    """
    cache_path = get_cache_path()
    files = list(cache_path.glob("*.parquet"))
    
    schemas = {}
    for f in files:
        try:
            df = pd.read_parquet(f)
            schemas[f.name] = df.dtypes.astype(str).to_dict()
        except Exception as e:
            schemas[f.name] = f"Error reading: {str(e)}"
            
    return schemas
