"""
Deep Analysis Fetcher Node

This node is triggered when the user requests "further analysis" or "deep dive".
It fetches historical data and enriches the analysis with additional context.

NOTE: OpenF1 API integration has been disabled due to stability issues.
The node now relies on FastF1 and local data sources only.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_outputs_path
from src.tools.token_tracker import (
    track_llm_response,
    is_limit_exceeded,
    get_usage_summary,
    check_token_budget,
    estimate_tokens
)
import json


# Map common country name variations to expected names
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


def deep_analysis_fetcher(state: WeekendState) -> dict:
    """
    Fetch detailed data for deep analysis.

    This node:
    1. Checks if we have token budget for API processing
    2. Maps the weekend spec to analysis parameters
    3. Fetches FastF1 telemetry data if available
    4. Uses LLM to summarize and contextualize the data
    5. Returns enriched state for the storyteller node
    
    NOTE: OpenF1 API has been disabled due to stability issues.
    """
    print("\n=== [Deep Analysis Fetcher] Starting Data Retrieval ===")

    # Check token budget first
    if is_limit_exceeded():
        print("[Deep Analysis Fetcher] Token limit exceeded, skipping deep analysis")
        return {
            "api_data": {"error": "Token limit exceeded"},
            "api_data_summary": "Analysis limited due to token budget constraints.",
            "token_limit_exceeded": True
        }

    weekend_spec = state.get("weekend_spec")
    if not weekend_spec:
        return {
            "api_data": {"error": "No weekend specified"},
            "api_data_summary": "Could not fetch data - no race weekend identified.",
            "errors": state.get("errors", []) + ["No weekend_spec available for deep analysis"]
        }

    # Extract year and country
    year = weekend_spec.get("year")
    country = _normalize_country(weekend_spec)

    print(f"[Deep Analysis Fetcher] Looking up: {year} {country}")

    # Initialize data containers
    api_data = {}
    api_summary = ""
    fastf1_data = None
    fastf1_summary = ""

    # Fetch FastF1 data if available (2018+)
    if year and year >= 2018:
        print(f"[Deep Analysis Fetcher] Fetching FastF1 telemetry data...")
        try:
            from src.tools.fastf1_tools import get_comprehensive_analysis, summarize_fastf1_data

            # Get driver focus
            drivers_focus = state.get("drivers_focus", [])

            # Map driver names to FastF1 abbreviations
            driver_abbrevs = None
            if drivers_focus:
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
            api_summary = fastf1_summary

            print(f"[Deep Analysis Fetcher] FastF1 data fetched successfully")

        except Exception as f1_error:
            print(f"[Deep Analysis Fetcher] FastF1 fetch failed: {f1_error}")
            fastf1_summary = f"FastF1 data unavailable: {str(f1_error)}"
            api_summary = fastf1_summary

    else:
        fastf1_summary = f"FastF1 data not available for {year} (requires 2018+)"
        api_summary = fastf1_summary

    # Use LLM to create insights if we have data
    enriched_summary = api_summary
    if api_summary and check_token_budget(2000):
        try:
            llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.2)

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an F1 technical analyst. Analyze the data below and extract key insights.

**CRITICAL RULES:**
1. ONLY report information that appears in the Data Summary below.
2. DO NOT make up or assume any data not present in the summary.
3. If certain data is not available, say "data not available".
4. Quote specific values exactly as they appear.

Focus on (if data is available):
1. Lap time analysis and pace comparisons
2. Tire strategy patterns (compounds used)
3. Sector performance comparisons
4. Speed trap data

User Query: {query}

Data Summary (ONLY USE THIS DATA):
{api_summary}

Previous Analysis (from dataset):
{previous_analysis}

Provide insights based ONLY on the data above. Do not add information not present in the data."""),
                ("user", "What insights can you extract from this data? Only use information present in the data above.")
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
        except Exception as llm_error:
            print(f"[Deep Analysis Fetcher] LLM enrichment failed: {llm_error}")
            enriched_summary = api_summary
    else:
        print("[Deep Analysis Fetcher] Skipping LLM enrichment due to token budget or no data")

    print(get_usage_summary())

    # Persist deep analysis outputs
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
