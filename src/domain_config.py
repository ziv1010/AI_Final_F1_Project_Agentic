"""
Domain Configuration System for Universal Racing Analytics.

Auto-detects the racing domain from dataset structure and provides
domain-agnostic configuration for the pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd
import json


@dataclass
class DomainConfig:
    """Configuration for a specific racing domain."""
    domain_name: str  # "f1", "motogp", "indycar", "nascar", "generic"
    primary_entity: str  # "driver", "rider", "competitor"
    primary_entity_plural: str  # "drivers", "riders", "competitors"
    secondary_entity: str  # "constructor", "team", "manufacturer"
    secondary_entity_plural: str  # "constructors", "teams", "manufacturers"
    event_name: str  # "race", "grand_prix", "round"
    venue_name: str  # "circuit", "track"
    
    # Auto-detected entities from data
    detected_entities: Dict[str, List[str]] = field(default_factory=dict)
    
    # Column mappings discovered from schema
    column_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Available data files
    data_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "domain_name": self.domain_name,
            "primary_entity": self.primary_entity,
            "primary_entity_plural": self.primary_entity_plural,
            "secondary_entity": self.secondary_entity,
            "secondary_entity_plural": self.secondary_entity_plural,
            "event_name": self.event_name,
            "venue_name": self.venue_name,
            "detected_entities": self.detected_entities,
            "column_mappings": self.column_mappings,
            "data_files": self.data_files
        }


# Predefined domain templates
DOMAIN_TEMPLATES = {
    "f1": DomainConfig(
        domain_name="f1",
        primary_entity="driver",
        primary_entity_plural="drivers",
        secondary_entity="constructor",
        secondary_entity_plural="constructors",
        event_name="grand prix",
        venue_name="circuit"
    ),
    "motogp": DomainConfig(
        domain_name="motogp",
        primary_entity="rider",
        primary_entity_plural="riders",
        secondary_entity="team",
        secondary_entity_plural="teams",
        event_name="race",
        venue_name="circuit"
    ),
    "indycar": DomainConfig(
        domain_name="indycar",
        primary_entity="driver",
        primary_entity_plural="drivers",
        secondary_entity="team",
        secondary_entity_plural="teams",
        event_name="race",
        venue_name="track"
    ),
    "nascar": DomainConfig(
        domain_name="nascar",
        primary_entity="driver",
        primary_entity_plural="drivers",
        secondary_entity="team",
        secondary_entity_plural="teams",
        event_name="race",
        venue_name="track"
    ),
    "generic": DomainConfig(
        domain_name="generic",
        primary_entity="competitor",
        primary_entity_plural="competitors",
        secondary_entity="team",
        secondary_entity_plural="teams",
        event_name="event",
        venue_name="venue"
    )
}


def detect_domain_from_columns(columns: List[str]) -> str:
    """
    Detect the racing domain based on column names.
    
    Args:
        columns: List of column names from the dataset
        
    Returns:
        Domain name string
    """
    columns_lower = [c.lower() for c in columns]
    columns_str = " ".join(columns_lower)
    
    # F1 indicators
    f1_indicators = ["constructorid", "driverid", "raceid", "qualifyid", "fastestlap", "constructors"]
    f1_score = sum(1 for ind in f1_indicators if ind in columns_str)
    
    # MotoGP indicators
    motogp_indicators = ["rider", "bike", "category", "rider_name", "bike_name", "motogp"]
    motogp_score = sum(1 for ind in motogp_indicators if ind in columns_str)
    
    # IndyCar indicators
    indycar_indicators = ["indycar", "indy", "chassis", "engine"]
    indycar_score = sum(1 for ind in indycar_indicators if ind in columns_str)
    
    # NASCAR indicators
    nascar_indicators = ["nascar", "manufacturer", "sponsor"]
    nascar_score = sum(1 for ind in nascar_indicators if ind in columns_str)
    
    scores = {
        "f1": f1_score,
        "motogp": motogp_score,
        "indycar": indycar_score,
        "nascar": nascar_score
    }
    
    max_score = max(scores.values())
    if max_score == 0:
        return "generic"
    
    return max(scores, key=scores.get)


def detect_domain(data_path: Path) -> DomainConfig:
    """
    Auto-detect the racing domain from the dataset.
    
    Args:
        data_path: Path to the data directory
        
    Returns:
        DomainConfig with detected settings
    """
    data_path = Path(data_path)
    
    # Collect all columns from all CSV files
    all_columns = set()
    data_files = []
    
    for csv_file in data_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file, nrows=5)
            all_columns.update(df.columns.tolist())
            data_files.append(csv_file.name)
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")
    
    # Detect domain
    domain_name = detect_domain_from_columns(list(all_columns))
    
    # Get template and customize
    config = DomainConfig(
        domain_name=DOMAIN_TEMPLATES[domain_name].domain_name,
        primary_entity=DOMAIN_TEMPLATES[domain_name].primary_entity,
        primary_entity_plural=DOMAIN_TEMPLATES[domain_name].primary_entity_plural,
        secondary_entity=DOMAIN_TEMPLATES[domain_name].secondary_entity,
        secondary_entity_plural=DOMAIN_TEMPLATES[domain_name].secondary_entity_plural,
        event_name=DOMAIN_TEMPLATES[domain_name].event_name,
        venue_name=DOMAIN_TEMPLATES[domain_name].venue_name,
        data_files=data_files
    )
    
    # Detect column mappings
    columns_lower = {c.lower(): c for c in all_columns}
    
    # Primary entity column
    primary_cols = ["driver", "rider", "competitor", "driverid", "rider_name", "driver_name"]
    for col in primary_cols:
        if col in columns_lower:
            config.column_mappings["primary_entity"] = columns_lower[col]
            break
    
    # Secondary entity column
    secondary_cols = ["constructor", "team", "constructorid", "team_name", "team_id"]
    for col in secondary_cols:
        if col in columns_lower:
            config.column_mappings["secondary_entity"] = columns_lower[col]
            break
    
    # Event/race column
    event_cols = ["race", "raceid", "event", "race_name", "circuit_name", "shortname"]
    for col in event_cols:
        if col in columns_lower:
            config.column_mappings["event"] = columns_lower[col]
            break
    
    # Position/result column
    result_cols = ["position", "positionorder", "position_order", "finish", "result"]
    for col in result_cols:
        if col in columns_lower:
            config.column_mappings["result"] = columns_lower[col]
            break
    
    # Points column
    points_cols = ["points", "score", "pts"]
    for col in points_cols:
        if col in columns_lower:
            config.column_mappings["points"] = columns_lower[col]
            break
    
    # Time column
    time_cols = ["time", "race_time", "lap_time", "milliseconds"]
    for col in time_cols:
        if col in columns_lower:
            config.column_mappings["time"] = columns_lower[col]
            break
    
    # Year column
    year_cols = ["year", "season", "date"]
    for col in year_cols:
        if col in columns_lower:
            config.column_mappings["year"] = columns_lower[col]
            break
    
    print(f"[Domain Config] Detected domain: {config.domain_name}")
    print(f"[Domain Config] Found {len(data_files)} data files")
    print(f"[Domain Config] Column mappings: {config.column_mappings}")
    
    return config


# Global domain config cache
_domain_config_cache: Optional[DomainConfig] = None
_cache_file_path = Path("outputs/.cache/domain_config.json")


def get_domain_config(data_path: Optional[Path] = None, force_refresh: bool = False) -> DomainConfig:
    """
    Get the domain configuration, using cache if available.
    
    Args:
        data_path: Path to data directory (uses default if None)
        force_refresh: Force re-detection even if cached
        
    Returns:
        DomainConfig instance
    """
    global _domain_config_cache
    
    # Try memory cache first
    if _domain_config_cache is not None and not force_refresh:
        return _domain_config_cache
    
    # Try file cache
    if not force_refresh and _cache_file_path.exists():
        try:
            import json
            with open(_cache_file_path) as f:
                data = json.load(f)
            _domain_config_cache = DomainConfig(
                domain_name=data["domain_name"],
                primary_entity=data["primary_entity"],
                primary_entity_plural=data["primary_entity_plural"],
                secondary_entity=data["secondary_entity"],
                secondary_entity_plural=data["secondary_entity_plural"],
                event_name=data["event_name"],
                venue_name=data["venue_name"],
                detected_entities=data.get("detected_entities", {}),
                column_mappings=data.get("column_mappings", {}),
                data_files=data.get("data_files", [])
            )
            print(f"[Domain Config] Loaded from cache: {_domain_config_cache.domain_name}")
            return _domain_config_cache
        except Exception as e:
            print(f"[Domain Config] Cache load failed: {e}")
    
    if data_path is None:
        from src.config import get_raw_data_path
        data_path = get_raw_data_path()
    
    _domain_config_cache = detect_domain(data_path)
    
    # Save to file cache
    try:
        _cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(_cache_file_path, "w") as f:
            json.dump(_domain_config_cache.to_dict(), f, indent=2)
        print(f"[Domain Config] Saved to cache: {_cache_file_path}")
    except Exception as e:
        print(f"[Domain Config] Cache save failed: {e}")
    
    return _domain_config_cache


def clear_domain_cache():
    """Clear the cached domain configuration."""
    global _domain_config_cache
    _domain_config_cache = None
    if _cache_file_path.exists():
        _cache_file_path.unlink()
        print("[Domain Config] Cache cleared")

