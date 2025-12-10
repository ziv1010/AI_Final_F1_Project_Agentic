"""
Query Validator Node

Validates and cross-checks the extracted query parameters against the actual database:
1. Verifies drivers exist in the database
2. Verifies the race exists
3. Validates that drivers participated in the specific race
4. Provides corrected/validated parameters back to the pipeline
"""

import pandas as pd
from src.state import WeekendState
from src.config import CONFIG
from pathlib import Path


def query_validator(state: WeekendState) -> dict:
    """
    Validates the extracted query parameters against the actual data.

    This node:
    1. Loads the drivers and results data
    2. Validates that specified drivers exist
    3. Validates that drivers participated in the specified race
    4. Returns validated and corrected driver/team lists
    """
    print("\n=== [Query Validator] Validating extracted parameters ===")

    weekend_spec = state.get("weekend_spec", {})
    drivers_focus = state.get("drivers_focus", [])
    teams_focus = state.get("teams_focus", [])
    race_id = weekend_spec.get("race_id") if weekend_spec else None

    if not race_id:
        print("[Query Validator] No race_id found, skipping validation")
        return {}

    # Load data
    data_dir = Path(CONFIG.get("data_paths", {}).get("raw", "data/raw"))

    try:
        drivers_df = pd.read_csv(data_dir / "drivers.csv")
        results_df = pd.read_csv(data_dir / "results.csv")
        constructors_df = pd.read_csv(data_dir / "constructors.csv")
    except FileNotFoundError as e:
        print(f"[Query Validator] Could not load data files: {e}")
        return {}

    # Get drivers who participated in this race
    race_results = results_df[results_df['raceId'] == race_id]
    race_driver_ids = set(race_results['driverId'].unique())

    # Validate drivers
    validated_drivers = []
    validation_messages = []

    for driver_name in drivers_focus:
        # Try to match by surname (case-insensitive)
        driver_name_lower = driver_name.lower().strip()

        # Match by surname (exact)
        matches = drivers_df[drivers_df['surname'].str.lower() == driver_name_lower]

        if matches.empty:
            # Try partial match on surname
            matches = drivers_df[drivers_df['surname'].str.lower().str.contains(driver_name_lower, na=False)]

        if matches.empty:
            # Try by driver code (3-letter codes like VER, HAM)
            matches = drivers_df[drivers_df['code'].str.lower() == driver_name_lower]

        if matches.empty:
            # Try by forename
            matches = drivers_df[drivers_df['forename'].str.lower() == driver_name_lower]

        if matches.empty:
            # Try partial match on forename
            matches = drivers_df[drivers_df['forename'].str.lower().str.contains(driver_name_lower, na=False)]

        found_in_race = False
        if not matches.empty:
            # Check if driver participated in this race
            for _, driver_row in matches.iterrows():
                driver_id = driver_row['driverId']
                surname = driver_row['surname']

                if driver_id in race_driver_ids:
                    if surname not in validated_drivers:
                        validated_drivers.append(surname)
                        validation_messages.append(f"✓ {driver_name} -> {surname} (driverId={driver_id}) participated in race {race_id}")
                    found_in_race = True
                    break

            if not found_in_race:
                # Driver exists but didn't participate in this race - still add to list
                surname = matches.iloc[0]['surname']
                if surname not in validated_drivers:
                    validated_drivers.append(surname)
                validation_messages.append(f"⚠ {driver_name} -> {surname} exists (may have different driverId in this season)")
        else:
            validation_messages.append(f"✗ {driver_name} not found in drivers database")

    # Validate teams
    validated_teams = []
    for team_name in teams_focus:
        team_name_lower = team_name.lower().strip()

        # Get constructor IDs in this race
        race_constructor_ids = set(race_results['constructorId'].unique())

        # Match constructor
        matches = constructors_df[constructors_df['name'].str.lower().str.contains(team_name_lower, na=False)]

        if not matches.empty:
            for _, constructor_row in matches.iterrows():
                constructor_id = constructor_row['constructorId']
                name = constructor_row['name']

                if constructor_id in race_constructor_ids:
                    validated_teams.append(name)
                    validation_messages.append(f"✓ {team_name} -> {name} participated in race {race_id}")
                    break

    # Print validation results
    print("[Query Validator] Validation Results:")
    for msg in validation_messages:
        print(f"  {msg}")

    print(f"[Query Validator] Original drivers: {drivers_focus}")
    print(f"[Query Validator] Validated drivers: {validated_drivers}")
    print(f"[Query Validator] Original teams: {teams_focus}")
    print(f"[Query Validator] Validated teams: {validated_teams}")

    # Get schema info for the code writer
    schema_info = {
        "results_columns": results_df.columns.tolist(),
        "drivers_columns": drivers_df.columns.tolist(),
        "constructors_columns": constructors_df.columns.tolist(),
        "race_id": race_id,
        "validated_driver_ids": list(race_driver_ids),
    }

    # If no drivers could be validated, keep original (let code handle gracefully)
    if not validated_drivers and drivers_focus:
        print(f"[Query Validator] WARNING: No drivers could be validated. Keeping original: {drivers_focus}")
        validated_drivers = drivers_focus

    return {
        "drivers_focus": validated_drivers,
        "teams_focus": validated_teams,
        "analysis_outputs": {
            **state.get("analysis_outputs", {}),
            "validation_info": {
                "messages": validation_messages,
                "schema_info": schema_info,
                "original_drivers": drivers_focus,
                "validated_drivers": validated_drivers,
            }
        }
    }
