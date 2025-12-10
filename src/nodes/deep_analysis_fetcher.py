"""
Deep Analysis Fetcher Node

This node is triggered when the user requests "further analysis" or "deep dive".
It fetches real-time/historical data from the OpenF1 API to enrich the analysis
with telemetry, weather, race control events, and other live data.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_outputs_path
from src.tools.openf1_tools import (
    fetch_comprehensive_session_data,
    summarize_api_data,
    get_openf1_session
)
from src.tools.token_tracker import (
    track_llm_response,
    is_limit_exceeded,
    get_usage_summary,
    check_token_budget,
    estimate_tokens
)
import json


# Map common country name variations to OpenF1 expected names
COUNTRY_NAME_MAP = {
    "bahrain": "Bahrain",
    "saudi arabia": "Saudi Arabia",
    "jeddah": "Saudi Arabia",
    "australia": "Australia",
    "melbourne": "Australia",
    "japan": "Japan",
    "suzuka": "Japan",
    "china": "China",
    "shanghai": "China",
    "miami": "United States",
    "imola": "Italy",
    "monaco": "Monaco",
    "canada": "Canada",
    "montreal": "Canada",
    "spain": "Spain",
    "barcelona": "Spain",
    "austria": "Austria",
    "spielberg": "Austria",
    "britain": "Great Britain",
    "silverstone": "Great Britain",
    "uk": "Great Britain",
    "hungary": "Hungary",
    "budapest": "Hungary",
    "belgium": "Belgium",
    "spa": "Belgium",
    "netherlands": "Netherlands",
    "zandvoort": "Netherlands",
    "italy": "Italy",
    "monza": "Italy",
    "singapore": "Singapore",
    "azerbaijan": "Azerbaijan",
    "baku": "Azerbaijan",
    "usa": "United States",
    "austin": "United States",
    "cota": "United States",
    "mexico": "Mexico",
    "brazil": "Brazil",
    "interlagos": "Brazil",
    "sao paulo": "Brazil",
    "las vegas": "United States",
    "qatar": "Qatar",
    "abu dhabi": "Abu Dhabi",
    "yas marina": "Abu Dhabi",
}


def _normalize_country(weekend_spec: dict) -> str:
    """Extract and normalize country name from weekend spec."""
    # Try multiple fields
    for field in ["country", "location", "circuit", "name"]:
        value = weekend_spec.get(field, "")
        if value:
            normalized = value.lower().strip()
            if normalized in COUNTRY_NAME_MAP:
                return COUNTRY_NAME_MAP[normalized]
            # Try partial match
            for key, mapped in COUNTRY_NAME_MAP.items():
                if key in normalized or normalized in key:
                    return mapped
    return weekend_spec.get("country", "Unknown")


def _get_driver_numbers(drivers_focus: list, drivers_data: list) -> list:
    """Map driver names/refs to driver numbers."""
    if not drivers_focus or not drivers_data:
        return []

    numbers = []
    focus_lower = [d.lower() for d in drivers_focus]

    for driver in drivers_data:
        full_name = driver.get("full_name", "").lower()
        name_acronym = driver.get("name_acronym", "").lower()
        driver_number = driver.get("driver_number")

        for focus in focus_lower:
            if focus in full_name or focus == name_acronym or focus in name_acronym:
                if driver_number and driver_number not in numbers:
                    numbers.append(driver_number)
                break

    return numbers


def deep_analysis_fetcher(state: WeekendState) -> dict:
    """
    Fetch detailed data from OpenF1 API for deep analysis.

    This node:
    1. Checks if we have token budget for API processing
    2. Maps the weekend spec to OpenF1 API parameters
    3. Fetches weather, telemetry, race control, stints, etc.
    4. Uses LLM to summarize and contextualize the API data
    5. Returns enriched state for the storyteller node
    """
    print("\n=== [Deep Analysis Fetcher] Starting API Data Retrieval ===")

    # Check token budget first
    if is_limit_exceeded():
        print("[Deep Analysis Fetcher] Token limit exceeded, skipping API analysis")
        return {
            "api_data": {"error": "Token limit exceeded"},
            "api_data_summary": "Analysis limited due to token budget constraints.",
            "token_limit_exceeded": True
        }

    weekend_spec = state.get("weekend_spec")
    if not weekend_spec:
        return {
            "api_data": {"error": "No weekend specified"},
            "api_data_summary": "Could not fetch API data - no race weekend identified.",
            "errors": state.get("errors", []) + ["No weekend_spec available for deep analysis"]
        }

    # Extract year and country
    year = weekend_spec.get("year")
    country = _normalize_country(weekend_spec)

    print(f"[Deep Analysis Fetcher] Looking up: {year} {country}")

    # OpenF1 data is mainly available from 2023 onwards
    if year and year < 2023:
        print(f"[Deep Analysis Fetcher] Year {year} predates OpenF1 data (2023+)")
        return {
            "api_data": {"error": f"OpenF1 data not available for {year} (requires 2023+)"},
            "api_data_summary": f"Real-time API data is only available for 2023 onwards. The {year} season predates the OpenF1 API coverage. Analysis will continue with historical Kaggle data only.",
            "errors": []
        }

    # Fetch comprehensive session data
    try:
        # Get session first to get driver list
        session = get_openf1_session.invoke({
            "year": year,
            "country": country,
            "session_type": "Race"
        })

        if not session:
            # Try qualifying if race not found
            session = get_openf1_session.invoke({
                "year": year,
                "country": country,
                "session_type": "Qualifying"
            })

        if not session:
            return {
                "api_data": {"error": f"Session not found for {year} {country}"},
                "api_data_summary": f"Could not find OpenF1 session data for {year} {country}. The race may not be in the API database yet.",
                "errors": []
            }

        # Get driver numbers for focused drivers
        drivers_focus = state.get("drivers_focus", [])
        driver_numbers = None

        if drivers_focus:
            from src.tools.openf1_tools import get_openf1_drivers
            drivers_data = get_openf1_drivers.invoke({"session_key": session["session_key"]})
            driver_numbers = _get_driver_numbers(drivers_focus, drivers_data)
            print(f"[Deep Analysis Fetcher] Focused drivers mapped to numbers: {driver_numbers}")

        # Get factor analysis to intelligently determine what data to fetch
        factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
        data_sources_needed = factor_analysis.get("data_sources_needed", {})

        # Determine what data to fetch based on intelligent factor analysis
        include_radio = data_sources_needed.get("radio", True)  # Default to True
        include_location = data_sources_needed.get("positions", False)  # Default to False (large dataset)

        print(f"[Deep Analysis Fetcher] Intelligent data source selection:")
        print(f"  - Radio communications: {include_radio}")
        print(f"  - GPS location data: {include_location}")

        # Fetch all data with intelligent selection
        api_data = fetch_comprehensive_session_data(
            year=year,
            country=country,
            session_type="Race",
            driver_numbers=driver_numbers,
            include_radio=include_radio,
            include_location=include_location
        )

        # Generate summary
        api_summary = summarize_api_data(api_data)

        # Use LLM to create insights from API data
        if check_token_budget(2000):  # Estimate ~2000 tokens for this call
            llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.2)

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an F1 technical analyst. Analyze the real-time API data below and extract key insights.

**CRITICAL RULES:**
1. ONLY report information that appears in the API Data Summary below.
2. DO NOT make up or assume any data not present in the summary.
3. If certain data is not available, say "data not available".
4. Quote specific values exactly as they appear.

Focus on (if data is available):
1. Weather conditions (temperatures, rainfall)
2. Tire strategy patterns (compounds used)
3. Race incidents and flags
4. Pit stop information

User Query: {query}

API Data Summary (ONLY USE THIS DATA):
{api_summary}

Previous Analysis (from dataset):
{previous_analysis}

Provide insights based ONLY on the data above. Do not add information not present in the API data."""),
                ("user", "What insights can you extract from this API data? Only use information present in the data above.")
            ])

            chain = prompt | llm

            # Get previous analysis summary
            previous_analysis = state.get("analysis_outputs", {}).get("stdout", "No previous analysis available")
            if len(previous_analysis) > 2000:
                previous_analysis = previous_analysis[:2000] + "..."

            response = chain.invoke({
                "query": state.get("user_query", ""),
                "api_summary": api_summary,
                "previous_analysis": previous_analysis
            })

            # Track token usage
            usage = track_llm_response(response)
            print(f"[Deep Analysis Fetcher] LLM tokens used: {usage}")

            enriched_summary = f"{api_summary}\n\n## Additional Insights\n{response.content}"
        else:
            enriched_summary = api_summary
            print("[Deep Analysis Fetcher] Skipping LLM enrichment due to token budget")

        print(f"[Deep Analysis Fetcher] Successfully fetched OpenF1 API data for {year} {country}")

        # Fetch FastF1 data if available (2018+)
        fastf1_data = None
        fastf1_summary = ""

        if year >= 2018:
            print(f"[Deep Analysis Fetcher] Fetching FastF1 telemetry data...")
            try:
                from src.tools.fastf1_tools import get_comprehensive_analysis, summarize_fastf1_data

                # Map driver names to FastF1 abbreviations
                driver_abbrevs = None
                drivers_focus = state.get("drivers_focus", [])

                if driver_numbers:
                    # Try to map from OpenF1 drivers data
                    drivers_list = api_data.get("drivers", [])
                    driver_abbrevs = []
                    for dn in driver_numbers:
                        for d in drivers_list:
                            if d.get("driver_number") == dn:
                                # Use name_acronym if available
                                abbrev = d.get("name_acronym")
                                if abbrev:
                                    driver_abbrevs.append(abbrev)
                                break

                # Fallback: Try to map driver names directly to common abbreviations
                # Note: driver_abbrevs could be [] (empty list) if OpenF1 mapping failed
                if (not driver_abbrevs or len(driver_abbrevs) == 0) and drivers_focus:
                    print(f"[Deep Analysis Fetcher] Driver number mapping failed, trying direct name mapping for: {drivers_focus}")
                    # Common driver name to abbreviation mapping
                    name_to_abbrev = {
                        "verstappen": "VER", "hamilton": "HAM", "norris": "NOR",
                        "leclerc": "LEC", "sainz": "SAI", "russell": "RUS",
                        "perez": "PER", "alonso": "ALO", "stroll": "STR",
                        "gasly": "GAS", "ocon": "OCO", "tsunoda": "TSU",
                        "ricciardo": "RIC", "magnussen": "MAG", "hulkenberg": "HUL",
                        "bottas": "BOT", "zhou": "ZHO", "albon": "ALB",
                        "sargeant": "SAR", "piastri": "PIA", "lawson": "LAW",
                        "colapinto": "COL", "bearman": "BEA", "doohan": "DOO",
                        "max": "VER", "lewis": "HAM", "lando": "NOR",
                        "charles": "LEC", "carlos": "SAI", "george": "RUS",
                        "sergio": "PER", "fernando": "ALO", "lance": "STR",
                        "pierre": "GAS", "esteban": "OCO", "yuki": "TSU",
                        "daniel": "RIC", "kevin": "MAG", "nico": "HUL",
                        "valtteri": "BOT", "guanyu": "ZHO", "alexander": "ALB",
                        "logan": "SAR", "oscar": "PIA", "liam": "LAW",
                        "franco": "COL", "oliver": "BEA", "jack": "DOO"
                    }
                    driver_abbrevs = []
                    for name in drivers_focus:
                        name_lower = name.lower().strip()
                        if name_lower in name_to_abbrev:
                            driver_abbrevs.append(name_to_abbrev[name_lower])
                        elif len(name) == 3:
                            # Already an abbreviation
                            driver_abbrevs.append(name.upper())

                print(f"[Deep Analysis Fetcher] FastF1 driver abbreviations: {driver_abbrevs}")

                # Fetch FastF1 data
                fastf1_data = get_comprehensive_analysis(
                    year=year,
                    race_name=country,
                    drivers=driver_abbrevs if driver_abbrevs else None
                )

                # Summarize FastF1 data
                fastf1_summary = summarize_fastf1_data(fastf1_data)

                print(f"[Deep Analysis Fetcher] FastF1 data fetched successfully")

            except Exception as f1_error:
                print(f"[Deep Analysis Fetcher] FastF1 fetch failed (continuing without it): {f1_error}")
                fastf1_summary = f"FastF1 data unavailable: {str(f1_error)}"

        else:
            fastf1_summary = f"FastF1 data not available for {year} (requires 2018+)"

        print(get_usage_summary())

        # Persist deep analysis outputs so users can compare basic vs deep
        outputs_path = get_outputs_path()
        outputs_path.mkdir(parents=True, exist_ok=True)

        base_report_path = outputs_path / "race_report.md"
        deep_report_path = outputs_path / "race_report_deep.md"
        deep_summary_path = outputs_path / "deep_analysis_summary.md"

        try:
            base_report = base_report_path.read_text()
        except Exception:
            base_report = ""

        deep_report = f"{base_report}\n\n---\n\n## Deep Analysis Addendum\n\n{enriched_summary}"
        with open(deep_report_path, "w") as f:
            f.write(deep_report)

        with open(deep_summary_path, "w") as f:
            f.write("## Deep Analysis Summary\n\n" + enriched_summary)

        return {
            "api_data": api_data,
            "api_data_summary": enriched_summary,
            "analysis_outputs": {
                **state.get("analysis_outputs", {}),
                "deep_report_path": str(deep_report_path),
                "deep_summary_path": str(deep_summary_path),
                "fastf1_data": fastf1_data,
                "fastf1_summary": fastf1_summary
            },
            "token_usage": state.get("token_usage", {}),
            "errors": []
        }

    except Exception as e:
        print(f"[Deep Analysis Fetcher] Error fetching API data: {e}")
        return {
            "api_data": {"error": str(e)},
            "api_data_summary": f"Error fetching real-time data: {str(e)}",
            "errors": state.get("errors", []) + [f"API fetch error: {str(e)}"]
        }
