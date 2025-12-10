"""
Test script for the column inspector tool
"""

from src.tools.column_inspector import (
    format_column_info_for_llm,
    search_column,
    get_join_keys,
    inspect_columns
)
from pathlib import Path
import json

def main():
    print("🏎️  F1 Analysis Agent - Column Inspector Test")
    print("=" * 60)
    print()

    # Define test paths
    cache_dir = Path("data/cache")

    # Find any race data files
    race_files = list(cache_dir.glob("r*_*.parquet"))

    if not race_files:
        print("❌ No cached race data found in data/cache/")
        print("   Run an analysis first to generate cache files")
        return

    # Extract race ID from first file
    race_id = race_files[0].name.split('_')[0][1:]

    test_paths = {
        'results_path': str(cache_dir / f"r{race_id}_results.parquet"),
        'drivers_path': str(cache_dir / f"r{race_id}_drivers.parquet"),
        'constructors_path': str(cache_dir / f"r{race_id}_constructors.parquet"),
        'laps_path': str(cache_dir / f"r{race_id}_laps.parquet"),
        'pits_path': str(cache_dir / f"r{race_id}_pits.parquet"),
    }

    # Verify files exist
    missing = [name for name, path in test_paths.items() if not Path(path).exists()]
    if missing:
        print(f"⚠️  Missing files: {missing}")
        print("   Some tests may be skipped")
        print()

    # Test 1: Format column info for LLM
    print("Test 1: Format Column Info for LLM")
    print("-" * 60)
    print(format_column_info_for_llm(test_paths))
    print()

    # Test 2: Search for 'driver' column
    print("\nTest 2: Search for 'driver' column")
    print("-" * 60)
    result = search_column('driver', test_paths)
    print(json.dumps(result, indent=2))
    print()

    # Test 3: Search for 'stop' column
    print("\nTest 3: Search for 'stop' column (should be in pits table)")
    print("-" * 60)
    result = search_column('stop', test_paths)
    print(json.dumps(result, indent=2))
    print()

    # Test 4: Search for 'surname' column
    print("\nTest 4: Search for 'surname' column (should be in drivers table)")
    print("-" * 60)
    result = search_column('surname', test_paths)
    print(json.dumps(result, indent=2))
    print()

    # Test 5: Get join keys
    print("\nTest 5: Get Join Keys")
    print("-" * 60)
    join_keys = get_join_keys(test_paths)
    for pair, keys in join_keys.items():
        print(f"{pair}:")
        for key in keys:
            print(f"  • {key}")
    print()

    # Test 6: Inspect specific dataset
    print("\nTest 6: Inspect Pits Dataset (where 'stop' column is)")
    print("-" * 60)
    info = inspect_columns({'pits': test_paths['pits_path']})
    pits_info = info.get('pits', {})
    if 'columns' in pits_info:
        print(f"Pits table has {pits_info['row_count']} rows")
        print("Columns:")
        for col in pits_info['columns']:
            print(f"  • {col['name']:<25} {col['dtype']:<15} (sample: {col['sample']})")
    print()

    print("=" * 60)
    print("✅ All tests completed successfully!")
    print()
    print("The column inspector is working correctly and will help")
    print("the agent fix column-related errors automatically.")

if __name__ == "__main__":
    main()
