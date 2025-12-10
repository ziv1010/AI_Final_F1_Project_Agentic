"""
OpenF1 API Tools for real-time and historical F1 data.

API Documentation: https://openf1.org
Endpoints used:
- /v1/sessions - Get session info (race, quali, practice)
- /v1/weather - Weather conditions during sessions
- /v1/car_data - Telemetry (throttle, brake, DRS, speed, RPM)
- /v1/laps - Lap times with sector splits
- /v1/stints - Tire compound and stint info
- /v1/race_control - Flags, safety car, incidents
- /v1/intervals - Gap to leader (race only)
- /v1/pit - Pit stop data
- /v1/drivers - Driver info per session
- /v1/position - Position changes
- /v1/team_radio - Team radio communications (NEW)
- /v1/location - Car position on track (NEW)
"""

import requests
from typing import Dict, List, Optional, Any
from langchain_core.tools import tool
import pandas as pd
from datetime import datetime
import time

OPENF1_BASE_URL = "https://api.openf1.org/v1"

# Rate limiting helper
_last_request_time = 0
MIN_REQUEST_INTERVAL = 1.5  # seconds between requests (increased for API stability)
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds to wait before retry


def _rate_limit():
    """Ensure we don't exceed rate limits."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _make_request(endpoint: str, params: Dict = None) -> Optional[List[Dict]]:
    """Make a request to OpenF1 API with error handling and retry logic."""
    url = f"{OPENF1_BASE_URL}/{endpoint}"

    for attempt in range(MAX_RETRIES):
        _rate_limit()

        try:
            response = requests.get(url, params=params, timeout=30)

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    print(f"OpenF1 API Rate Limited (429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"OpenF1 API Error: 429 Too Many Requests (max retries exceeded) for {endpoint}")
                    return None

            # Handle client errors (400-499)
            if 400 <= response.status_code < 500:
                # Don't retry client errors (except 429 which is handled above)
                print(f"OpenF1 API Error: {response.status_code} Client Error for {endpoint} with params {params}")
                print(f"  -> This endpoint may not have data for this session/driver")
                return None

            # Raise for other HTTP errors (500+)
            response.raise_for_status()

            # Success
            return response.json()

        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                print(f"OpenF1 API Timeout. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"OpenF1 API Error: Timeout after {MAX_RETRIES} attempts for {endpoint}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"OpenF1 API Error: {e}")
            return None

    return None


@tool
def get_openf1_session(year: int, country: str, session_type: str = "Race") -> Optional[Dict]:
    """
    Get session information from OpenF1 API.

    Args:
        year: Race year (2023 onwards for most data)
        country: Country name (e.g., "Bahrain", "Monaco", "United States")
        session_type: Type of session - "Race", "Qualifying", "Practice 1", "Practice 2", "Practice 3", "Sprint"

    Returns:
        Session info dict with session_key, meeting_key, dates, etc.
    """
    params = {
        "year": year,
        "country_name": country,
        "session_name": session_type
    }
    result = _make_request("sessions", params)
    if result and len(result) > 0:
        return result[0]
    return None


@tool
def get_openf1_weather(session_key: int, limit: int = 50) -> List[Dict]:
    """
    Get weather data for a session.

    Args:
        session_key: The session key from get_openf1_session
        limit: Max number of weather readings to return

    Returns:
        List of weather readings with air_temp, track_temp, humidity, pressure, wind_speed, rainfall
    """
    params = {"session_key": session_key}
    result = _make_request("weather", params)
    if result:
        # Return evenly spaced samples if too many
        if len(result) > limit:
            step = len(result) // limit
            return result[::step][:limit]
        return result
    return []


@tool
def get_openf1_car_telemetry(session_key: int, driver_number: int, limit: int = 100) -> List[Dict]:
    """
    Get car telemetry data (sampled at ~3.7Hz).

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Driver's car number (e.g., 1 for Verstappen, 44 for Hamilton)
        limit: Max number of telemetry points to return

    Returns:
        List of telemetry readings with speed, throttle, brake, n_gear, drs, rpm
    """
    params = {
        "session_key": session_key,
        "driver_number": driver_number
    }
    result = _make_request("car_data", params)
    if result:
        # Sample to reduce data volume
        if len(result) > limit:
            step = len(result) // limit
            return result[::step][:limit]
        return result
    return []


@tool
def get_openf1_laps(session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
    """
    Get lap data including sector times and speed traps.

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Optional - filter by specific driver

    Returns:
        List of lap data with lap_number, lap_duration, sector times, speed traps
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    return _make_request("laps", params) or []


@tool
def get_openf1_stints(session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
    """
    Get stint data (tire compound, age, lap range).

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Optional - filter by specific driver

    Returns:
        List of stints with compound, tyre_age_at_start, lap_start, lap_end
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    return _make_request("stints", params) or []


@tool
def get_openf1_race_control(session_key: int) -> List[Dict]:
    """
    Get race control messages (flags, safety car, incidents).

    Args:
        session_key: The session key from get_openf1_session

    Returns:
        List of race control messages with flag, message, category, scope
    """
    return _make_request("race_control", {"session_key": session_key}) or []


@tool
def get_openf1_intervals(session_key: int, driver_number: Optional[int] = None, limit: int = 100) -> List[Dict]:
    """
    Get interval data (gap to leader, gap to car ahead) - Race sessions only.

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Optional - filter by specific driver
        limit: Max number of interval readings

    Returns:
        List of intervals with gap_to_leader, interval (to car ahead)
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    result = _make_request("intervals", params)
    if result:
        if len(result) > limit:
            step = len(result) // limit
            return result[::step][:limit]
        return result
    return []


@tool
def get_openf1_pit_stops(session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
    """
    Get pit stop data.

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Optional - filter by specific driver

    Returns:
        List of pit stops with lap_number, pit_duration, date
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    return _make_request("pit", params) or []


@tool
def get_openf1_drivers(session_key: int) -> List[Dict]:
    """
    Get driver information for a session.

    Args:
        session_key: The session key from get_openf1_session

    Returns:
        List of drivers with driver_number, full_name, team_name, team_colour
    """
    return _make_request("drivers", {"session_key": session_key}) or []


@tool
def get_openf1_positions(session_key: int, driver_number: Optional[int] = None, limit: int = 100) -> List[Dict]:
    """
    Get position changes throughout a session.

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Optional - filter by specific driver
        limit: Max number of position updates

    Returns:
        List of position updates with date, driver_number, position
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    result = _make_request("position", params)
    if result:
        if len(result) > limit:
            step = len(result) // limit
            return result[::step][:limit]
        return result
    return []


@tool
def get_openf1_team_radio(session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
    """
    Get team radio communications during a session.

    This provides valuable insight into:
    - Strategy discussions between driver and team
    - Driver feedback on car behavior
    - Real-time decision making during the race
    - Team instructions and responses

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Optional - filter by specific driver

    Returns:
        List of team radio messages with date, driver_number, recording_url
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    return _make_request("team_radio", params) or []


@tool
def get_openf1_location(session_key: int, driver_number: int, limit: int = 100) -> List[Dict]:
    """
    Get car location data (GPS coordinates on track).

    Useful for:
    - Analyzing racing lines
    - Identifying where overtakes happened
    - Understanding track position during incidents

    Args:
        session_key: The session key from get_openf1_session
        driver_number: Driver's car number
        limit: Max number of location points to return

    Returns:
        List of location data with x, y, z coordinates, date
    """
    params = {
        "session_key": session_key,
        "driver_number": driver_number
    }
    result = _make_request("location", params)
    if result:
        # Sample to reduce data volume
        if len(result) > limit:
            step = len(result) // limit
            return result[::step][:limit]
        return result
    return []


def fetch_comprehensive_session_data(year: int, country: str, session_type: str = "Race",
                                      driver_numbers: List[int] = None,
                                      include_radio: bool = True,
                                      include_location: bool = False) -> Dict[str, Any]:
    """
    Fetch comprehensive data for a session (not a tool - used internally by nodes).

    Args:
        year: Race year
        country: Country name
        session_type: Session type
        driver_numbers: List of driver numbers to focus on
        include_radio: Whether to fetch team radio communications
        include_location: Whether to fetch location data (GPS, very large dataset)

    Returns:
        Dict with all available data for the session
    """
    data = {
        "session": None,
        "weather": [],
        "drivers": [],
        "race_control": [],
        "stints": [],
        "pit_stops": [],
        "laps": [],
        "intervals": [],
        "telemetry": {},
        "team_radio": [],
        "location": {},
        "errors": []
    }

    # Get session info first
    session = get_openf1_session.invoke({"year": year, "country": country, "session_type": session_type})
    if not session:
        data["errors"].append(f"Could not find session for {year} {country} {session_type}")
        return data

    data["session"] = session
    session_key = session.get("session_key")

    if not session_key:
        data["errors"].append("No session_key in session response")
        return data

    print(f"[OpenF1] Fetching data for session_key={session_key}")

    # Fetch all data types
    data["weather"] = get_openf1_weather.invoke({"session_key": session_key, "limit": 30})
    data["drivers"] = get_openf1_drivers.invoke({"session_key": session_key})
    data["race_control"] = get_openf1_race_control.invoke({"session_key": session_key})
    data["stints"] = get_openf1_stints.invoke({"session_key": session_key})
    data["pit_stops"] = get_openf1_pit_stops.invoke({"session_key": session_key})

    # Get laps for all drivers or focused ones
    if driver_numbers:
        for dn in driver_numbers:
            laps = get_openf1_laps.invoke({"session_key": session_key, "driver_number": dn})
            data["laps"].extend(laps)
    else:
        data["laps"] = get_openf1_laps.invoke({"session_key": session_key})

    # Get intervals (race only)
    if session_type == "Race":
        data["intervals"] = get_openf1_intervals.invoke({"session_key": session_key, "limit": 50})

    # Get telemetry for focused drivers only (too much data otherwise)
    # NOTE: This endpoint often fails with 422 for certain sessions/drivers
    if driver_numbers:
        for dn in driver_numbers:
            try:
                telemetry = get_openf1_car_telemetry.invoke({
                    "session_key": session_key,
                    "driver_number": dn,
                    "limit": 50
                })
                if telemetry:
                    data["telemetry"][dn] = telemetry
                else:
                    print(f"[OpenF1] No telemetry data available for driver {dn}")
            except Exception as e:
                print(f"[OpenF1] Failed to fetch telemetry for driver {dn}: {e}")
                data["errors"].append(f"Telemetry fetch failed for driver {dn}")

    # Get team radio communications
    if include_radio:
        try:
            if driver_numbers:
                # Get radio for focused drivers
                for dn in driver_numbers:
                    radio = get_openf1_team_radio.invoke({
                        "session_key": session_key,
                        "driver_number": dn
                    })
                    if radio:
                        data["team_radio"].extend(radio)
            else:
                # Get all radio communications
                radio = get_openf1_team_radio.invoke({"session_key": session_key})
                if radio:
                    data["team_radio"] = radio
        except Exception as e:
            print(f"[OpenF1] Failed to fetch team radio: {e}")
            data["errors"].append(f"Team radio fetch failed: {str(e)}")

    # Get location data (GPS) if requested - WARNING: very large dataset
    if include_location and driver_numbers:
        for dn in driver_numbers:
            try:
                location = get_openf1_location.invoke({
                    "session_key": session_key,
                    "driver_number": dn,
                    "limit": 100
                })
                if location:
                    data["location"][dn] = location
                else:
                    print(f"[OpenF1] No location data available for driver {dn}")
            except Exception as e:
                print(f"[OpenF1] Failed to fetch location for driver {dn}: {e}")
                data["errors"].append(f"Location fetch failed for driver {dn}")

    return data


def summarize_api_data(data: Dict[str, Any]) -> str:
    """
    Create a human-readable summary of API data (not a tool - used by nodes).
    """
    lines = []

    # Session info
    if data.get("session"):
        s = data["session"]
        lines.append(f"## Session: {s.get('session_name', 'Unknown')} - {s.get('country_name', 'Unknown')} {s.get('year', '')}")
        lines.append(f"Circuit: {s.get('circuit_short_name', 'Unknown')}")
        lines.append(f"Date: {s.get('date_start', 'Unknown')}")
        lines.append("")

    # Weather summary
    if data.get("weather"):
        w = data["weather"]
        if len(w) > 0:
            temps = [x.get("air_temperature", 0) for x in w if x.get("air_temperature")]
            track_temps = [x.get("track_temperature", 0) for x in w if x.get("track_temperature")]
            humidity = [x.get("humidity", 0) for x in w if x.get("humidity")]
            rainfall = any(x.get("rainfall", 0) for x in w)

            lines.append("## Weather Conditions")
            if temps:
                lines.append(f"- Air Temperature: {min(temps):.1f}C - {max(temps):.1f}C")
            if track_temps:
                lines.append(f"- Track Temperature: {min(track_temps):.1f}C - {max(track_temps):.1f}C")
            if humidity:
                lines.append(f"- Humidity: {min(humidity):.0f}% - {max(humidity):.0f}%")
            lines.append(f"- Rainfall: {'Yes' if rainfall else 'No'}")
            lines.append("")

    # Race control events
    if data.get("race_control"):
        rc = data["race_control"]
        flags = [x for x in rc if x.get("flag")]
        if flags:
            lines.append("## Race Control Events")
            for event in flags[:10]:  # Limit to 10
                lines.append(f"- {event.get('flag', 'UNKNOWN')}: {event.get('message', '')}")
            lines.append("")

    # Stint summary
    if data.get("stints"):
        lines.append("## Tire Strategy Summary")
        driver_stints = {}
        for stint in data["stints"]:
            dn = stint.get("driver_number")
            if dn not in driver_stints:
                driver_stints[dn] = []
            driver_stints[dn].append(stint)

        for dn, stints in list(driver_stints.items())[:5]:  # Top 5 drivers
            compounds = [s.get("compound", "?") for s in stints]
            lines.append(f"- Driver {dn}: {' -> '.join(compounds)}")
        lines.append("")

    # Pit stop summary
    if data.get("pit_stops"):
        lines.append("## Pit Stop Summary")
        pits = data["pit_stops"]
        driver_pits = {}
        for pit in pits:
            dn = pit.get("driver_number")
            if dn not in driver_pits:
                driver_pits[dn] = []
            driver_pits[dn].append(pit.get("pit_duration", 0))

        for dn, durations in list(driver_pits.items())[:5]:
            avg_dur = sum(durations) / len(durations) if durations else 0
            lines.append(f"- Driver {dn}: {len(durations)} stops, avg {avg_dur:.1f}s")
        lines.append("")

    # Driver info
    if data.get("drivers"):
        lines.append("## Drivers in Session")
        for d in data["drivers"][:10]:
            lines.append(f"- #{d.get('driver_number', '?')} {d.get('full_name', 'Unknown')} ({d.get('team_name', 'Unknown')})")
        lines.append("")

    # Team radio summary
    if data.get("team_radio"):
        radio = data["team_radio"]
        lines.append("## Team Radio Communications")
        lines.append(f"- Total radio messages captured: {len(radio)}")

        # Group by driver
        driver_radio = {}
        for msg in radio:
            dn = msg.get("driver_number")
            if dn not in driver_radio:
                driver_radio[dn] = []
            driver_radio[dn].append(msg)

        lines.append(f"- Drivers with radio: {list(driver_radio.keys())}")
        lines.append("- Radio data available for strategy and decision analysis")
        lines.append("")

    # Location data summary
    if data.get("location"):
        loc_data = data["location"]
        if loc_data:
            lines.append("## GPS Location Data")
            lines.append(f"- Drivers with location tracking: {list(loc_data.keys())}")
            total_points = sum(len(v) for v in loc_data.values())
            lines.append(f"- Total GPS points: {total_points}")
            lines.append("")

    # Errors
    if data.get("errors"):
        lines.append("## Data Fetch Errors")
        for err in data["errors"]:
            lines.append(f"- {err}")

    return "\n".join(lines)
