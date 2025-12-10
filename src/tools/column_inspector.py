"""
Column Inspector Tool - Helps the agent discover available columns in datasets
This tool is used by the code_debugger to fix column-related errors
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
import json

def inspect_columns(data_paths: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Inspect all available columns in the provided dataset files.

    Args:
        data_paths: Dictionary mapping dataset names to file paths

    Returns:
        Dictionary mapping dataset names to their column lists
    """
    column_info = {}

    for dataset_name, file_path in data_paths.items():
        if not file_path:
            continue

        try:
            # Read the parquet file
            df = pd.read_parquet(file_path)

            # Get column names and their data types
            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                # Get sample non-null value if available
                sample_val = None
                non_null_vals = df[col].dropna()
                if len(non_null_vals) > 0:
                    sample_val = str(non_null_vals.iloc[0])
                    if len(sample_val) > 50:
                        sample_val = sample_val[:47] + "..."

                columns.append({
                    'name': col,
                    'dtype': dtype,
                    'null_count': int(df[col].isnull().sum()),
                    'sample': sample_val
                })

            column_info[dataset_name] = {
                'columns': columns,
                'row_count': len(df),
                'file_path': file_path
            }

        except Exception as e:
            column_info[dataset_name] = {
                'error': str(e),
                'file_path': file_path
            }

    return column_info


def search_column(column_name: str, data_paths: Dict[str, str]) -> Dict[str, any]:
    """
    Search for a specific column across all datasets.

    Args:
        column_name: The column name to search for (case-insensitive)
        data_paths: Dictionary mapping dataset names to file paths

    Returns:
        Dictionary with search results
    """
    results = {
        'query': column_name,
        'found_in': [],
        'similar': []
    }

    column_name_lower = column_name.lower()

    for dataset_name, file_path in data_paths.items():
        if not file_path:
            continue

        try:
            df = pd.read_parquet(file_path)

            # Check for exact match (case-insensitive)
            for col in df.columns:
                if col.lower() == column_name_lower:
                    results['found_in'].append({
                        'dataset': dataset_name,
                        'column': col,
                        'dtype': str(df[col].dtype),
                        'null_count': int(df[col].isnull().sum()),
                        'total_rows': len(df)
                    })

                # Check for similar names (substring match or edit distance)
                elif column_name_lower in col.lower() or col.lower() in column_name_lower:
                    results['similar'].append({
                        'dataset': dataset_name,
                        'column': col,
                        'dtype': str(df[col].dtype),
                        'null_count': int(df[col].isnull().sum()),
                        'total_rows': len(df)
                    })

        except Exception as e:
            pass

    return results


def get_join_keys(data_paths: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Identify common columns that can be used for joining datasets.

    Args:
        data_paths: Dictionary mapping dataset names to file paths

    Returns:
        Dictionary showing potential join keys between datasets
    """
    all_columns = {}

    # First, collect all columns from each dataset
    for dataset_name, file_path in data_paths.items():
        if not file_path:
            continue

        try:
            df = pd.read_parquet(file_path)
            all_columns[dataset_name] = set(df.columns)
        except:
            continue

    # Find common columns
    join_keys = {}
    dataset_names = list(all_columns.keys())

    for i, dataset1 in enumerate(dataset_names):
        for dataset2 in dataset_names[i+1:]:
            common = all_columns[dataset1] & all_columns[dataset2]
            if common:
                key = f"{dataset1} <-> {dataset2}"
                join_keys[key] = sorted(list(common))

    return join_keys


def format_column_info_for_llm(data_paths: Dict[str, str]) -> str:
    """
    Format column information in a way that's easy for the LLM to understand.

    Args:
        data_paths: Dictionary mapping dataset names to file paths

    Returns:
        Formatted string with column information
    """
    info = inspect_columns(data_paths)
    join_keys = get_join_keys(data_paths)

    output = ["=" * 80, "AVAILABLE COLUMNS IN DATASETS", "=" * 80, ""]

    for dataset_name, dataset_info in info.items():
        if 'error' in dataset_info:
            output.append(f"\n{dataset_name}: ERROR - {dataset_info['error']}")
            continue

        output.append(f"\n{dataset_name} ({dataset_info['row_count']} rows):")
        output.append("-" * 60)

        for col in dataset_info['columns']:
            null_pct = (col['null_count'] / dataset_info['row_count'] * 100) if dataset_info['row_count'] > 0 else 0
            sample_info = f" [sample: {col['sample']}]" if col['sample'] else ""
            output.append(f"  • {col['name']:<30} {col['dtype']:<15} ({null_pct:.1f}% null){sample_info}")

    # Add join key information
    output.append("\n" + "=" * 80)
    output.append("POTENTIAL JOIN KEYS BETWEEN DATASETS")
    output.append("=" * 80 + "\n")

    for join_pair, keys in join_keys.items():
        output.append(f"{join_pair}:")
        for key in keys:
            output.append(f"  • {key}")

    return "\n".join(output)


if __name__ == "__main__":
    # Test the tool
    from src.config import CONFIG

    test_paths = {
        'results_path': 'data/cache/r1121_results.parquet',
        'drivers_path': 'data/cache/r1121_drivers.parquet',
        'constructors_path': 'data/cache/r1121_constructors.parquet',
        'laps_path': 'data/cache/r1121_laps.parquet',
        'pits_path': 'data/cache/r1121_pits.parquet',
    }

    print(format_column_info_for_llm(test_paths))
    print("\n\nSearching for 'driver':")
    print(json.dumps(search_column('driver', test_paths), indent=2))
    print("\n\nSearching for 'stop':")
    print(json.dumps(search_column('stop', test_paths), indent=2))
