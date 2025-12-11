"""
Schema Auto-Detector for Universal Racing Analytics.

Automatically analyzes CSV files to understand:
- Column names and types
- Relationships between tables
- Entity columns (competitors, teams, events)
- Outcome columns (position, points, time)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
import json


@dataclass
class ColumnInfo:
    """Information about a single column."""
    name: str
    dtype: str
    sample_values: List[Any]
    null_count: int
    unique_count: int
    is_numeric: bool
    is_categorical: bool
    is_temporal: bool
    is_id: bool
    semantic_type: Optional[str] = None  # "competitor", "team", "event", "result", etc.


@dataclass
class TableSchema:
    """Schema for a single table/CSV file."""
    name: str
    path: str
    row_count: int
    columns: Dict[str, ColumnInfo]
    potential_keys: List[str]
    potential_foreign_keys: List[str]


@dataclass
class DatasetSchema:
    """Complete schema for the racing dataset."""
    domain: str
    tables: Dict[str, TableSchema]
    relationships: List[Tuple[str, str, str, str]]  # (table1, col1, table2, col2)
    entity_columns: Dict[str, str]  # semantic_type -> table.column
    outcome_columns: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "domain": self.domain,
            "tables": {
                name: {
                    "name": t.name,
                    "path": t.path,
                    "row_count": t.row_count,
                    "columns": {
                        col_name: {
                            "name": col.name,
                            "dtype": col.dtype,
                            "sample_values": col.sample_values[:5],
                            "null_count": col.null_count,
                            "unique_count": col.unique_count,
                            "semantic_type": col.semantic_type
                        }
                        for col_name, col in t.columns.items()
                    },
                    "potential_keys": t.potential_keys
                }
                for name, t in self.tables.items()
            },
            "entity_columns": self.entity_columns,
            "outcome_columns": self.outcome_columns
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the schema."""
        lines = [
            f"=== Dataset Schema ({self.domain.upper()}) ===",
            f"Tables: {len(self.tables)}",
            ""
        ]
        
        for name, table in self.tables.items():
            lines.append(f"📁 {name} ({table.row_count:,} rows)")
            for col_name, col in list(table.columns.items())[:10]:
                semantic = f" [{col.semantic_type}]" if col.semantic_type else ""
                lines.append(f"   • {col_name}: {col.dtype}{semantic}")
            if len(table.columns) > 10:
                lines.append(f"   ... and {len(table.columns) - 10} more columns")
            lines.append("")
        
        if self.entity_columns:
            lines.append("Entity Columns:")
            for sem_type, location in self.entity_columns.items():
                lines.append(f"   • {sem_type}: {location}")
        
        return "\n".join(lines)


def _infer_semantic_type(col_name: str, sample_values: List[Any], dtype: str) -> Optional[str]:
    """
    Infer the semantic type of a column based on name and values.
    """
    col_lower = col_name.lower()
    
    # Competitor-related
    if any(kw in col_lower for kw in ["driver", "rider", "competitor", "racer", "pilot"]):
        return "competitor"
    
    # Team-related
    if any(kw in col_lower for kw in ["team", "constructor", "manufacturer", "squad"]):
        return "team"
    
    # Event-related
    if any(kw in col_lower for kw in ["race", "event", "grand_prix", "gp", "round"]):
        return "event"
    
    # Venue-related
    if any(kw in col_lower for kw in ["circuit", "track", "venue", "location"]):
        return "venue"
    
    # Result-related
    if any(kw in col_lower for kw in ["position", "finish", "rank", "place"]):
        return "result"
    
    # Points-related
    if any(kw in col_lower for kw in ["point", "score", "pts"]):
        return "points"
    
    # Time-related
    if any(kw in col_lower for kw in ["time", "duration", "lap_time", "millisecond"]):
        return "time"
    
    # Speed-related
    if any(kw in col_lower for kw in ["speed", "velocity", "pace"]):
        return "speed"
    
    # Year/season
    if any(kw in col_lower for kw in ["year", "season"]):
        return "year"
    
    # ID columns
    if col_lower.endswith("id") or col_lower.endswith("_id"):
        return "id"
    
    return None


def _analyze_column(df: pd.DataFrame, col_name: str) -> ColumnInfo:
    """
    Analyze a single column and extract metadata.
    """
    series = df[col_name]
    dtype_str = str(series.dtype)
    
    # Get sample values (non-null)
    non_null = series.dropna()
    sample_values = non_null.head(10).tolist() if len(non_null) > 0 else []
    
    # Determine column characteristics
    is_numeric = pd.api.types.is_numeric_dtype(series)
    is_temporal = pd.api.types.is_datetime64_any_dtype(series)
    
    # Check if categorical (string with limited unique values)
    is_categorical = (
        series.dtype == "object" and 
        series.nunique() < min(100, len(df) * 0.5)
    )
    
    # Check if it's an ID column
    is_id = (
        col_name.lower().endswith("id") or
        col_name.lower().endswith("_id") or
        (is_numeric and series.nunique() == len(series.dropna()))
    )
    
    # Infer semantic type
    semantic_type = _infer_semantic_type(col_name, sample_values, dtype_str)
    
    return ColumnInfo(
        name=col_name,
        dtype=dtype_str,
        sample_values=sample_values,
        null_count=int(series.isnull().sum()),
        unique_count=int(series.nunique()),
        is_numeric=is_numeric,
        is_categorical=is_categorical,
        is_temporal=is_temporal,
        is_id=is_id,
        semantic_type=semantic_type
    )


def _analyze_table(file_path: Path, max_rows: int = 10000) -> TableSchema:
    """
    Analyze a single CSV file and extract its schema.
    """
    df = pd.read_csv(file_path, nrows=max_rows)
    
    columns = {}
    for col_name in df.columns:
        columns[col_name] = _analyze_column(df, col_name)
    
    # Identify potential primary keys
    potential_keys = [
        col_name for col_name, col_info in columns.items()
        if col_info.is_id or (col_info.unique_count == len(df) and col_info.null_count == 0)
    ]
    
    # Identify potential foreign keys (ID columns that aren't primary keys)
    potential_foreign_keys = [
        col_name for col_name, col_info in columns.items()
        if col_info.is_id and col_name not in potential_keys
    ]
    
    return TableSchema(
        name=file_path.stem,
        path=str(file_path),
        row_count=len(df),
        columns=columns,
        potential_keys=potential_keys,
        potential_foreign_keys=potential_foreign_keys
    )


def detect_schema(data_path: Path, max_rows: int = 10000) -> DatasetSchema:
    """
    Analyze all CSV files in a directory and build a complete schema.
    
    Args:
        data_path: Path to the data directory
        max_rows: Maximum rows to read per file for analysis
        
    Returns:
        DatasetSchema with complete metadata
    """
    data_path = Path(data_path)
    
    tables = {}
    all_columns = set()
    
    # Analyze each CSV file
    for csv_file in sorted(data_path.glob("*.csv")):
        try:
            table_schema = _analyze_table(csv_file, max_rows)
            tables[table_schema.name] = table_schema
            all_columns.update(table_schema.columns.keys())
        except Exception as e:
            print(f"Warning: Could not analyze {csv_file}: {e}")
    
    # Detect domain from all columns
    from src.domain_config import detect_domain_from_columns
    domain = detect_domain_from_columns(list(all_columns))
    
    # Collect entity columns across all tables
    entity_columns = {}
    outcome_columns = []
    
    for table_name, table in tables.items():
        for col_name, col_info in table.columns.items():
            if col_info.semantic_type:
                key = col_info.semantic_type
                if key not in entity_columns:
                    entity_columns[key] = f"{table_name}.{col_name}"
                
                if col_info.semantic_type in ["result", "points"]:
                    outcome_columns.append(f"{table_name}.{col_name}")
    
    # Detect relationships (matching column names across tables)
    relationships = []
    table_names = list(tables.keys())
    for i, t1_name in enumerate(table_names):
        t1 = tables[t1_name]
        for t2_name in table_names[i+1:]:
            t2 = tables[t2_name]
            
            # Check for matching foreign key columns
            for fk in t1.potential_foreign_keys:
                if fk in t2.potential_keys:
                    relationships.append((t1_name, fk, t2_name, fk))
            
            for fk in t2.potential_foreign_keys:
                if fk in t1.potential_keys:
                    relationships.append((t2_name, fk, t1_name, fk))
    
    schema = DatasetSchema(
        domain=domain,
        tables=tables,
        relationships=relationships,
        entity_columns=entity_columns,
        outcome_columns=outcome_columns
    )
    
    print(f"[Schema Detector] Analyzed {len(tables)} tables")
    print(f"[Schema Detector] Domain: {domain}")
    print(f"[Schema Detector] Found {len(relationships)} relationships")
    
    return schema


# Cache for schema
_schema_cache: Optional[DatasetSchema] = None


def get_schema(data_path: Optional[Path] = None, force_refresh: bool = False) -> DatasetSchema:
    """
    Get the dataset schema, using cache if available.
    """
    global _schema_cache
    
    if _schema_cache is not None and not force_refresh:
        return _schema_cache
    
    if data_path is None:
        from src.config import get_raw_data_path
        data_path = get_raw_data_path()
    
    _schema_cache = detect_schema(data_path)
    return _schema_cache


def clear_schema_cache():
    """Clear the cached schema."""
    global _schema_cache
    _schema_cache = None
