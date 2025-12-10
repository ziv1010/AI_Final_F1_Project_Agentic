"""
FastF1 Tools for detailed telemetry and session data.

FastF1 provides access to:
- Real telemetry data (speed, throttle, brake, gear, DRS, RPM)
- Tire compound information per stint
- Weather data throughout session
- Track status (yellow flags, safety car, etc.)
- Detailed lap data with sector times
- Car position data on track
"""

import fastf1
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import warnings

# Suppress FastF1 warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Enable FastF1 cache for faster subsequent loads
CACHE_DIR = Path("data/cache/fastf1")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))


def get_session_data(year: int, race_name: str, session_type: str = "R") -> Optional[fastf1.core.Session]:
    """
    Load a FastF1 session.

    Args:
        year: Race year (2018+)
        race_name: Race name or location (e.g., "Bahrain", "Monaco", "Monza")
        session_type: "R" (Race), "Q" (Qualifying), "FP1", "FP2", "FP3", "S" (Sprint)

    Returns:
        FastF1 Session object or None if not found
    """
    try:
        print(f"[FastF1] Loading {year} {race_name} {session_type}...")
        session = fastf1.get_session(year, race_name, session_type)
        session.load()
        print(f"[FastF1] Session loaded successfully")
        return session
    except Exception as e:
        print(f"[FastF1] Error loading session: {e}")
        return None


def get_driver_telemetry(session: fastf1.core.Session, driver: str, lap_number: Optional[int] = None) -> Optional[pd.DataFrame]:
    """
    Get telemetry data for a driver.

    Args:
        session: FastF1 session object
        driver: Driver code (e.g., "VER", "HAM") or number
        lap_number: Specific lap number (None = all laps)

    Returns:
        DataFrame with telemetry (Time, Speed, Throttle, Brake, nGear, DRS, RPM)
    """
    try:
        if lap_number:
            lap = session.laps.pick_driver(driver).pick_lap(lap_number)
            if lap is None or lap.empty:
                return None
            telemetry = lap.get_telemetry()
        else:
            laps = session.laps.pick_driver(driver)
            if laps is None or laps.empty:
                return None
            # Get telemetry for fastest lap
            fastest_lap = laps.pick_fastest()
            if fastest_lap is None or fastest_lap.empty:
                return None
            telemetry = fastest_lap.get_telemetry()

        return telemetry
    except Exception as e:
        print(f"[FastF1] Error getting telemetry for {driver}: {e}")
        return None


def get_driver_laps(session: fastf1.core.Session, driver: str) -> Optional[pd.DataFrame]:
    """
    Get all laps for a driver with detailed information.

    Returns:
        DataFrame with columns: LapNumber, LapTime, Sector1Time, Sector2Time, Sector3Time,
        Compound, TyreLife, TrackStatus, IsPersonalBest, Position, etc.
    """
    try:
        laps = session.laps.pick_driver(driver)
        if laps is None or laps.empty:
            return None
        return laps
    except Exception as e:
        print(f"[FastF1] Error getting laps for {driver}: {e}")
        return None


def get_tire_strategy(session: fastf1.core.Session, drivers: List[str] = None) -> Dict[str, List[Dict]]:
    """
    Extract tire strategy for drivers.

    Returns:
        Dict mapping driver -> list of stints with {compound, start_lap, end_lap, laps}
    """
    try:
        if drivers is None:
            drivers = session.drivers

        strategies = {}
        for driver in drivers:
            laps = session.laps.pick_driver(driver)
            if laps is None or laps.empty:
                continue

            stints = []
            current_compound = None
            stint_start = None

            for idx, lap in laps.iterrows():
                compound = lap['Compound']
                lap_num = lap['LapNumber']

                if compound != current_compound:
                    if current_compound is not None:
                        stints.append({
                            'compound': current_compound,
                            'start_lap': stint_start,
                            'end_lap': lap_num - 1,
                            'laps': lap_num - stint_start
                        })
                    current_compound = compound
                    stint_start = lap_num

            # Add final stint
            if current_compound is not None:
                stints.append({
                    'compound': current_compound,
                    'start_lap': stint_start,
                    'end_lap': laps['LapNumber'].max(),
                    'laps': laps['LapNumber'].max() - stint_start + 1
                })

            strategies[driver] = stints

        return strategies
    except Exception as e:
        print(f"[FastF1] Error extracting tire strategies: {e}")
        return {}


def get_weather_data(session: fastf1.core.Session) -> Optional[pd.DataFrame]:
    """
    Get weather data for the session.

    Returns:
        DataFrame with AirTemp, TrackTemp, Humidity, Pressure, WindSpeed, Rainfall
    """
    try:
        weather = session.weather_data
        if weather is None or weather.empty:
            return None
        return weather
    except Exception as e:
        print(f"[FastF1] Error getting weather data: {e}")
        return None


def compare_telemetry(session: fastf1.core.Session, driver1: str, driver2: str,
                     lap1: Optional[int] = None, lap2: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get telemetry for two drivers to compare.

    Args:
        session: FastF1 session
        driver1, driver2: Driver codes
        lap1, lap2: Specific lap numbers (None = fastest lap)

    Returns:
        Tuple of (telemetry1, telemetry2)
    """
    tel1 = get_driver_telemetry(session, driver1, lap1)
    tel2 = get_driver_telemetry(session, driver2, lap2)
    return tel1, tel2


def get_stint_analysis(session: fastf1.core.Session, driver: str) -> pd.DataFrame:
    """
    Analyze tire degradation per stint for a driver.

    Returns:
        DataFrame with stint stats: compound, avg_laptime, deg_rate, fastest_lap, etc.
    """
    try:
        laps = get_driver_laps(session, driver)
        if laps is None or laps.empty:
            return pd.DataFrame()

        # Group by compound to identify stints
        laps['StintNumber'] = (laps['Compound'] != laps['Compound'].shift()).cumsum()

        stint_stats = []
        for stint_num, stint_laps in laps.groupby('StintNumber'):
            # Filter out in/out laps and invalid laps
            valid_laps = stint_laps[
                (stint_laps['LapTime'].notna()) &
                (~stint_laps['PitOutTime'].notna()) &
                (~stint_laps['PitInTime'].notna())
            ]

            if len(valid_laps) < 2:
                continue

            # Convert lap times to seconds
            lap_times = valid_laps['LapTime'].dt.total_seconds()
            lap_numbers = valid_laps['LapNumber'].values

            # Calculate degradation rate (linear fit)
            if len(lap_times) > 1:
                deg_rate = np.polyfit(range(len(lap_times)), lap_times, 1)[0]
            else:
                deg_rate = 0

            stint_stats.append({
                'Driver': driver,
                'StintNumber': stint_num,
                'Compound': valid_laps['Compound'].iloc[0],
                'StartLap': valid_laps['LapNumber'].min(),
                'EndLap': valid_laps['LapNumber'].max(),
                'NumLaps': len(valid_laps),
                'AvgLapTime': lap_times.mean(),
                'FastestLap': lap_times.min(),
                'SlowestLap': lap_times.max(),
                'DegradationRate': deg_rate,  # seconds per lap
                'TotalDegradation': deg_rate * len(valid_laps) if deg_rate > 0 else 0
            })

        return pd.DataFrame(stint_stats)
    except Exception as e:
        print(f"[FastF1] Error in stint analysis for {driver}: {e}")
        return pd.DataFrame()


def get_comprehensive_analysis(year: int, race_name: str, drivers: List[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive FastF1 analysis data for a race.

    Args:
        year: Race year
        race_name: Race name/location
        drivers: List of driver codes to focus on (None = all)

    Returns:
        Dict with all FastF1 data: session, laps, weather, telemetry, strategies, etc.
    """
    data = {
        'session': None,
        'laps': {},
        'weather': None,
        'strategies': {},
        'stint_analysis': {},
        'telemetry_samples': {},
        'session_info': {},
        'errors': []
    }

    try:
        # Load session
        session = get_session_data(year, race_name, 'R')
        if session is None:
            data['errors'].append(f"Could not load session for {year} {race_name}")
            return data

        data['session'] = session
        data['session_info'] = {
            'event_name': session.event['EventName'],
            'location': session.event['Location'],
            'date': str(session.event['EventDate']),
            'track_length': session.event.get('CircuitLength', 'Unknown'),
            'total_laps': session.total_laps
        }

        # Get weather
        data['weather'] = get_weather_data(session)

        # If no specific drivers, get all
        if drivers is None:
            drivers = [session.get_driver(d)['Abbreviation'] for d in session.drivers]

        # Get tire strategies
        data['strategies'] = get_tire_strategy(session, drivers)

        # Get detailed data for each driver
        for driver in drivers:
            # Laps
            laps = get_driver_laps(session, driver)
            if laps is not None and not laps.empty:
                data['laps'][driver] = laps

            # Stint analysis
            stint_df = get_stint_analysis(session, driver)
            if not stint_df.empty:
                data['stint_analysis'][driver] = stint_df

            # Sample telemetry (fastest lap)
            telemetry = get_driver_telemetry(session, driver)
            if telemetry is not None and not telemetry.empty:
                # Downsample for storage
                sample_rate = max(1, len(telemetry) // 500)
                data['telemetry_samples'][driver] = telemetry.iloc[::sample_rate]

        print(f"[FastF1] Comprehensive analysis complete for {len(drivers)} drivers")

    except Exception as e:
        print(f"[FastF1] Error in comprehensive analysis: {e}")
        data['errors'].append(str(e))

    return data


def summarize_fastf1_data(data: Dict[str, Any]) -> str:
    """
    Create a human-readable summary of FastF1 data.
    """
    lines = []

    if data.get('session_info'):
        info = data['session_info']
        lines.append(f"# FastF1 Analysis: {info.get('event_name', 'Unknown')}")
        lines.append(f"Location: {info.get('location', 'Unknown')}")
        lines.append(f"Date: {info.get('date', 'Unknown')}")
        lines.append(f"Total Laps: {info.get('total_laps', 'Unknown')}")
        lines.append("")

    # Weather summary
    if data.get('weather') is not None:
        weather = data['weather']
        if not weather.empty:
            lines.append("## Weather Conditions")
            lines.append(f"- Air Temperature: {weather['AirTemp'].min():.1f}°C - {weather['AirTemp'].max():.1f}°C")
            lines.append(f"- Track Temperature: {weather['TrackTemp'].min():.1f}°C - {weather['TrackTemp'].max():.1f}°C")
            lines.append(f"- Humidity: {weather['Humidity'].min():.0f}% - {weather['Humidity'].max():.0f}%")
            if 'Rainfall' in weather.columns:
                rainfall = weather['Rainfall'].any()
                lines.append(f"- Rainfall: {'Yes' if rainfall else 'No'}")
            lines.append("")

    # Strategy summary
    if data.get('strategies'):
        lines.append("## Tire Strategies")
        for driver, stints in data['strategies'].items():
            compounds = ' → '.join([f"{s['compound']}({s['laps']}L)" for s in stints])
            lines.append(f"- **{driver}**: {compounds}")
        lines.append("")

    # Stint degradation summary
    if data.get('stint_analysis'):
        lines.append("## Tire Degradation Analysis")
        for driver, stint_df in data['stint_analysis'].items():
            if not stint_df.empty:
                lines.append(f"### {driver}")
                for _, stint in stint_df.iterrows():
                    lines.append(f"- Stint {int(stint['StintNumber'])}: {stint['Compound']} "
                               f"({int(stint['NumLaps'])} laps, "
                               f"deg: {stint['DegradationRate']:.3f}s/lap)")
        lines.append("")

    # Telemetry availability
    if data.get('telemetry_samples'):
        lines.append("## Telemetry Data Available")
        lines.append(f"Detailed telemetry captured for: {', '.join(data['telemetry_samples'].keys())}")
        lines.append("")

    # Errors
    if data.get('errors'):
        lines.append("## Data Fetch Errors")
        for err in data['errors']:
            lines.append(f"- {err}")

    return "\n".join(lines)
