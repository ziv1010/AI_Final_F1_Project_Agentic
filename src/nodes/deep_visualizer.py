"""
Deep Analysis Visualizer Node

Creates comprehensive visualizations using FastF1 telemetry data.
Saves visualizations to outputs/deep_analysis_visualizations/
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_run_vis_path
from src.tools.token_tracker import track_llm_response, check_token_budget
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List


# Mapping from driver surnames to FastF1 abbreviations
SURNAME_TO_ABBREV = {
    "verstappen": "VER", "hamilton": "HAM", "norris": "NOR",
    "leclerc": "LEC", "sainz": "SAI", "russell": "RUS",
    "perez": "PER", "alonso": "ALO", "stroll": "STR",
    "gasly": "GAS", "ocon": "OCO", "tsunoda": "TSU",
    "ricciardo": "RIC", "magnussen": "MAG", "hulkenberg": "HUL",
    "bottas": "BOT", "zhou": "ZHO", "albon": "ALB",
    "sargeant": "SAR", "piastri": "PIA", "lawson": "LAW",
    "colapinto": "COL", "bearman": "BEA", "doohan": "DOO",
    # Also support common first names
    "max": "VER", "lewis": "HAM", "lando": "NOR",
    "charles": "LEC", "carlos": "SAI", "george": "RUS",
    "sergio": "PER", "fernando": "ALO", "lance": "STR",
    "pierre": "GAS", "esteban": "OCO", "yuki": "TSU",
    "daniel": "RIC", "kevin": "MAG", "nico": "HUL",
    "valtteri": "BOT", "guanyu": "ZHO", "alexander": "ALB",
    "logan": "SAR", "oscar": "PIA", "liam": "LAW",
    "franco": "COL", "oliver": "BEA", "jack": "DOO",
}


def _get_driver_abbreviations(drivers_focus: List[str]) -> List[str]:
    """Convert driver surnames/names to FastF1 abbreviations."""
    abbrevs = []
    for driver in drivers_focus:
        driver_lower = driver.lower().strip()
        # Check if it's already an abbreviation (3 letters)
        if len(driver_lower) == 3 and driver_lower.upper() in [v for v in SURNAME_TO_ABBREV.values()]:
            abbrevs.append(driver_lower.upper())
        elif driver_lower in SURNAME_TO_ABBREV:
            abbrevs.append(SURNAME_TO_ABBREV[driver_lower])
        else:
            # Try partial match
            for surname, abbrev in SURNAME_TO_ABBREV.items():
                if surname in driver_lower or driver_lower in surname:
                    abbrevs.append(abbrev)
                    break
    return abbrevs


def deep_visualizer(state: WeekendState) -> dict:
    """
    Generate deep analysis visualizations using FastF1 data.

    Creates:
    - Telemetry comparison plots (speed, throttle, brake traces)
    - Tire degradation curves per stint
    - Strategy visualization timeline
    - Weather impact analysis
    - Sector time comparisons
    - Speed trap comparisons
    """
    print("\n=== [Deep Visualizer] Creating Advanced Visualizations ===")

    # Check for FastF1 data
    fastf1_data = state.get("analysis_outputs", {}).get("fastf1_data")
    if not fastf1_data:
        print("[Deep Visualizer] No FastF1 data available, skipping")
        return {}

    # Create deep analysis visualization directory (run-specific)
    deep_vis_dir = get_run_vis_path()
    deep_vis_dir.mkdir(parents=True, exist_ok=True)
    
    # Also create backwards-compatible directory
    compat_vis_dir = Path("analysis_vis")
    compat_vis_dir.mkdir(parents=True, exist_ok=True)

    visualizations = []
    drivers_focus = state.get("drivers_focus", [])

    # Log which drivers we're focusing on
    print(f"[Deep Visualizer] Drivers focus: {drivers_focus}")

    try:
        # Extract data
        laps_data = fastf1_data.get("laps", {})
        telemetry_data = fastf1_data.get("telemetry_samples", {})
        strategies = fastf1_data.get("strategies", {})
        stint_analysis = fastf1_data.get("stint_analysis", {})
        weather = fastf1_data.get("weather")

        # Filter data to only include focused drivers (if specified)
        def filter_by_drivers(data_dict, focus_list):
            """Filter a dictionary to only include keys matching driver focus.

            Handles both surname->abbreviation conversion and direct abbreviation matching.
            """
            if not focus_list or not data_dict:
                return data_dict

            # Convert focus list (surnames) to abbreviations for matching FastF1 keys
            focus_abbrevs = _get_driver_abbreviations(focus_list)
            focus_abbrevs_upper = [a.upper() for a in focus_abbrevs]

            print(f"[Deep Visualizer] Filtering - Focus surnames: {focus_list}")
            print(f"[Deep Visualizer] Filtering - Mapped abbreviations: {focus_abbrevs_upper}")
            print(f"[Deep Visualizer] Filtering - Available keys: {list(data_dict.keys())}")

            filtered = {}
            for key, value in data_dict.items():
                key_upper = key.upper()
                # Check if key matches any abbreviation
                if key_upper in focus_abbrevs_upper:
                    filtered[key] = value

            if filtered:
                print(f"[Deep Visualizer] Filtering - Kept: {list(filtered.keys())}")
            else:
                print(f"[Deep Visualizer] Filtering - No matches found, keeping all data")

            return filtered if filtered else data_dict

        if drivers_focus:
            print(f"[Deep Visualizer] Filtering data for drivers: {drivers_focus}")
            laps_data = filter_by_drivers(laps_data, drivers_focus)
            telemetry_data = filter_by_drivers(telemetry_data, drivers_focus)
            strategies = filter_by_drivers(strategies, drivers_focus)
            stint_analysis = filter_by_drivers(stint_analysis, drivers_focus)
            print(f"[Deep Visualizer] After filtering - Laps: {list(laps_data.keys())}, Telemetry: {list(telemetry_data.keys())}")

        # 1. Telemetry Comparison (if 2 drivers)
        if len(telemetry_data) >= 2:
            drivers = list(telemetry_data.keys())[:2]
            tel1 = telemetry_data[drivers[0]]
            tel2 = telemetry_data[drivers[1]]

            if tel1 is not None and tel2 is not None and not tel1.empty and not tel2.empty:
                fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

                # Speed comparison
                axes[0].plot(tel1['Distance'], tel1['Speed'], label=drivers[0], linewidth=2)
                axes[0].plot(tel2['Distance'], tel2['Speed'], label=drivers[1], linewidth=2, alpha=0.8)
                axes[0].set_ylabel('Speed (km/h)', fontsize=11)
                axes[0].legend(loc='upper right')
                axes[0].grid(True, alpha=0.3)
                axes[0].set_title('Speed Trace Comparison (Fastest Lap)', fontsize=13, fontweight='bold')

                # Throttle comparison
                axes[1].plot(tel1['Distance'], tel1['Throttle'], label=drivers[0], linewidth=2)
                axes[1].plot(tel2['Distance'], tel2['Throttle'], label=drivers[1], linewidth=2, alpha=0.8)
                axes[1].set_ylabel('Throttle (%)', fontsize=11)
                axes[1].legend(loc='upper right')
                axes[1].grid(True, alpha=0.3)

                # Brake comparison
                axes[2].plot(tel1['Distance'], tel1['Brake'], label=drivers[0], linewidth=2)
                axes[2].plot(tel2['Distance'], tel2['Brake'], label=drivers[1], linewidth=2, alpha=0.8)
                axes[2].set_ylabel('Brake', fontsize=11)
                axes[2].set_xlabel('Distance (m)', fontsize=11)
                axes[2].legend(loc='upper right')
                axes[2].grid(True, alpha=0.3)

                plt.tight_layout()
                telemetry_path = deep_vis_dir / "telemetry_comparison.png"
                plt.savefig(telemetry_path, dpi=300, bbox_inches='tight')
                plt.close()
                visualizations.append(str(telemetry_path))
                print(f"[Deep Visualizer] Saved telemetry comparison to {telemetry_path}")

        # 2. Tire Degradation Curves
        if stint_analysis:
            fig, ax = plt.subplots(figsize=(12, 7))

            for driver, stint_df in stint_analysis.items():
                if not stint_df.empty:
                    for _, stint in stint_df.iterrows():
                        compound = stint['Compound']
                        deg_rate = stint['DegradationRate']
                        num_laps = int(stint['NumLaps'])

                        # Create degradation curve
                        laps_range = np.arange(0, num_laps)
                        times = stint['AvgLapTime'] + (deg_rate * laps_range)

                        label = f"{driver} - {compound} (Stint {int(stint['StintNumber'])})"
                        ax.plot(laps_range, times, marker='o', label=label, linewidth=2)

            ax.set_xlabel('Laps into Stint', fontsize=12)
            ax.set_ylabel('Lap Time (seconds)', fontsize=12)
            ax.set_title('Tire Degradation Curves by Stint', fontsize=14, fontweight='bold')
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            deg_path = deep_vis_dir / "tire_degradation_curves.png"
            plt.savefig(deg_path, dpi=300, bbox_inches='tight')
            plt.close()
            visualizations.append(str(deg_path))
            print(f"[Deep Visualizer] Saved degradation curves to {deg_path}")

        # 3. Strategy Timeline
        if strategies:
            fig, ax = plt.subplots(figsize=(14, 6))

            y_pos = 0
            for driver, stints in strategies.items():
                for stint in stints:
                    compound = stint['compound']
                    start = stint['start_lap']
                    length = stint['laps']

                    # Color by compound
                    colors = {'SOFT': '#FF3333', 'MEDIUM': '#FFF200', 'HARD': '#EEEEEE',
                             'INTERMEDIATE': '#39B54A', 'WET': '#00AEEF'}
                    color = colors.get(compound, '#CCCCCC')

                    ax.barh(y_pos, length, left=start, height=0.7, color=color,
                           edgecolor='black', linewidth=1.5)
                    ax.text(start + length/2, y_pos, compound[:3],
                           ha='center', va='center', fontsize=9, fontweight='bold')

                y_pos += 1

            ax.set_yticks(range(len(strategies)))
            ax.set_yticklabels(list(strategies.keys()), fontsize=11)
            ax.set_xlabel('Lap Number', fontsize=12)
            ax.set_title('Tire Strategy Timeline', fontsize=14, fontweight='bold')
            ax.grid(True, axis='x', alpha=0.3)

            plt.tight_layout()
            strategy_path = deep_vis_dir / "strategy_timeline.png"
            plt.savefig(strategy_path, dpi=300, bbox_inches='tight')
            plt.close()
            visualizations.append(str(strategy_path))
            print(f"[Deep Visualizer] Saved strategy timeline to {strategy_path}")

        # 4. Weather Evolution (if available)
        if weather is not None and not weather.empty:
            fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

            time_index = range(len(weather))

            # Temperature evolution
            axes[0].plot(time_index, weather['AirTemp'], label='Air Temp', linewidth=2, color='orange')
            axes[0].plot(time_index, weather['TrackTemp'], label='Track Temp', linewidth=2, color='red')
            axes[0].set_ylabel('Temperature (°C)', fontsize=11)
            axes[0].legend(loc='upper right')
            axes[0].grid(True, alpha=0.3)
            axes[0].set_title('Weather Evolution During Session', fontsize=13, fontweight='bold')

            # Humidity
            axes[1].plot(time_index, weather['Humidity'], linewidth=2, color='blue')
            axes[1].set_ylabel('Humidity (%)', fontsize=11)
            axes[1].set_xlabel('Time Points', fontsize=11)
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            weather_path = deep_vis_dir / "weather_evolution.png"
            plt.savefig(weather_path, dpi=300, bbox_inches='tight')
            plt.close()
            visualizations.append(str(weather_path))
            print(f"[Deep Visualizer] Saved weather evolution to {weather_path}")

        # 5. Lap Time Distribution per Stint
        if laps_data:
            fig, ax = plt.subplots(figsize=(12, 7))

            all_stint_data = []
            for driver, laps in laps_data.items():
                if laps is not None and not laps.empty:
                    # Add stint number based on compound changes
                    laps = laps.copy()
                    laps['StintNumber'] = (laps['Compound'] != laps['Compound'].shift()).cumsum()

                    # Filter valid laps
                    valid_laps = laps[
                        (laps['LapTime'].notna()) &
                        (~laps['PitOutTime'].notna()) &
                        (~laps['PitInTime'].notna())
                    ].copy()

                    if not valid_laps.empty:
                        valid_laps['LapTimeSeconds'] = valid_laps['LapTime'].dt.total_seconds()
                        valid_laps['Driver'] = driver
                        valid_laps['StintLabel'] = valid_laps.apply(
                            lambda x: f"{driver}-{x['Compound']}-S{int(x['StintNumber'])}", axis=1
                        )
                        all_stint_data.append(valid_laps[['StintLabel', 'LapTimeSeconds']])

            if all_stint_data:
                combined = pd.concat(all_stint_data, ignore_index=True)
                sns.boxplot(data=combined, x='StintLabel', y='LapTimeSeconds', ax=ax)
                ax.set_xlabel('Stint', fontsize=12)
                ax.set_ylabel('Lap Time (seconds)', fontsize=12)
                ax.set_title('Lap Time Distribution by Stint', fontsize=14, fontweight='bold')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3, axis='y')

                plt.tight_layout()
                dist_path = deep_vis_dir / "stint_laptime_distribution.png"
                plt.savefig(dist_path, dpi=300, bbox_inches='tight')
                plt.close()
                visualizations.append(str(dist_path))
                print(f"[Deep Visualizer] Saved stint distribution to {dist_path}")

        print(f"[Deep Visualizer] Created {len(visualizations)} deep analysis visualizations")

        return {
            "analysis_outputs": {
                **state.get("analysis_outputs", {}),
                "deep_visualizations": visualizations
            }
        }

    except Exception as e:
        print(f"[Deep Visualizer] Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return {
            "errors": state.get("errors", []) + [f"Deep visualization error: {str(e)}"]
        }
