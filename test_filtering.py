import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load data
results = pd.read_parquet('data/cache/r1141_results.parquet')
drivers = pd.read_parquet('data/cache/r1141_drivers.parquet')
constructors = pd.read_parquet('data/cache/r1141_constructors.parquet')

# Clean data
for df in [results, drivers, constructors]:
    df.replace(r'\N', np.nan, inplace=True)

# Convert numeric columns
results['points'] = pd.to_numeric(results['points'], errors='coerce')
results['position'] = pd.to_numeric(results['position'], errors='coerce')
results['grid'] = pd.to_numeric(results['grid'], errors='coerce')

# Join results with constructors
merged = pd.merge(results, constructors, on='constructorId')

# Filter for race 1141
race_1141 = merged[merged['raceId'] == 1141]

# Filter for teams
teams_of_interest = ['Ferrari', 'McLaren', 'Red Bull']
focus_df = race_1141[race_1141['name'].isin(teams_of_interest)]

print(f"Found {len(focus_df)} rows for teams {teams_of_interest}")
print(focus_df[['name', 'points', 'position', 'grid']])

# Calculate metrics
team_points = focus_df.groupby('name')['points'].sum().reset_index()
print("\nTeam Points:")
print(team_points)

# Save
OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)
team_points.to_parquet(OUTPUT_DIR / 'analysis_metrics.parquet')
print(f"\nSaved to {OUTPUT_DIR / 'analysis_metrics.parquet'}")
