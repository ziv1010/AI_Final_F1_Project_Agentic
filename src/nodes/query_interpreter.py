from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.tools.data_tools import list_weekends
from src.config import CONFIG
import json
import re
import unicodedata
from typing import List, Dict

# Map driver codes/names to surnames (for database matching)
DRIVER_NAME_MAP = {
    # Common codes to surnames
    "max": "Verstappen", "ver": "Verstappen", "verstappen": "Verstappen",
    "lewis": "Hamilton", "ham": "Hamilton", "hamilton": "Hamilton",
    "lando": "Norris", "nor": "Norris", "lan": "Norris", "norris": "Norris",
    "charles": "Leclerc", "lec": "Leclerc", "leclerc": "Leclerc",
    "carlos": "Sainz", "sai": "Sainz", "sainz": "Sainz",
    "george": "Russell", "rus": "Russell", "russell": "Russell",
    "sergio": "Perez", "per": "Perez", "perez": "Perez", "checo": "Perez",
    "fernando": "Alonso", "alo": "Alonso", "alonso": "Alonso",
    "lance": "Stroll", "str": "Stroll", "stroll": "Stroll",
    "pierre": "Gasly", "gas": "Gasly", "gasly": "Gasly",
    "esteban": "Ocon", "oco": "Ocon", "ocon": "Ocon",
    "yuki": "Tsunoda", "tsu": "Tsunoda", "tsunoda": "Tsunoda",
    "daniel": "Ricciardo", "ric": "Ricciardo", "ricciardo": "Ricciardo",
    "kevin": "Magnussen", "mag": "Magnussen", "magnussen": "Magnussen",
    "nico": "Hulkenberg", "hul": "Hulkenberg", "hulkenberg": "Hulkenberg",
    "valtteri": "Bottas", "bot": "Bottas", "bottas": "Bottas",
    "guanyu": "Zhou", "zho": "Zhou", "zhou": "Zhou",
    "alexander": "Albon", "alb": "Albon", "albon": "Albon",
    "logan": "Sargeant", "sar": "Sargeant", "sargeant": "Sargeant",
    "oscar": "Piastri", "pia": "Piastri", "piastri": "Piastri",
    "liam": "Lawson", "law": "Lawson", "lawson": "Lawson",
    "franco": "Colapinto", "col": "Colapinto", "colapinto": "Colapinto",
    "oliver": "Bearman", "bea": "Bearman", "bearman": "Bearman",
    "jack": "Doohan", "doo": "Doohan", "doohan": "Doohan",
}

# Map common team name variations to their official database names
TEAM_NAME_MAP = {
    # Red Bull variations
    "redbull": "Red Bull",
    "redbulls": "Red Bull",
    "red bull": "Red Bull",
    "red bulls": "Red Bull",
    "rb": "Red Bull",
    "red bull racing": "Red Bull",
    # McLaren variations
    "mclaren": "McLaren",
    "mclarens": "McLaren",
    "mc laren": "McLaren",
    # Ferrari variations
    "ferrari": "Ferrari",
    "ferrar": "Ferrari",
    "ferarri": "Ferrari",
    "scuderia ferrari": "Ferrari",
    # Mercedes variations
    "mercedes": "Mercedes",
    "merc": "Mercedes",
    "mercs": "Mercedes",
    "mercedes-amg": "Mercedes",
    # Alpine variations
    "alpine": "Alpine F1 Team",
    "alpine f1": "Alpine F1 Team",
    # Aston Martin variations
    "aston martin": "Aston Martin",
    "astonmartin": "Aston Martin",
    "aston": "Aston Martin",
    # Williams
    "williams": "Williams",
    # Haas variations
    "haas": "Haas F1 Team",
    "haas f1": "Haas F1 Team",
    # Sauber/Kick Sauber/Alfa Romeo
    "sauber": "Sauber",
    "kick sauber": "Sauber",
    "alfa romeo": "Alfa Romeo",
    # AlphaTauri / RB
    "alphatauri": "AlphaTauri",
    "alpha tauri": "AlphaTauri",
    "rb f1": "RB F1 Team",
    "visa rb": "RB F1 Team",
    # Racing Point
    "racing point": "Racing Point",
    "racingpoint": "Racing Point",
    # Toro Rosso
    "toro rosso": "Toro Rosso",
}


def _normalize(text: str) -> str:
    text = str(text).lower()
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _normalize_team_name(team: str) -> str:
    """Normalize a team name to match the database format."""
    normalized = team.strip().lower()
    return TEAM_NAME_MAP.get(normalized, team)


def _normalize_driver_name(driver: str) -> str:
    """Normalize a driver name/code to surname for database matching."""
    normalized = driver.strip().lower()
    return DRIVER_NAME_MAP.get(normalized, driver.title())


def _pick_best_candidate(candidates: List[Dict], query: str):
    if not candidates:
        return None
    normalized_query = _normalize(query)
    year_matches = re.findall(r"(19|20)\d{2}", query)
    year_matches = [int(y) for y in year_matches]
    query_tokens = normalized_query.split()

    best = None
    best_score = -1
    for cand in candidates:
        score = 0
        cand_name = _normalize(cand.get("name", ""))
        cand_circuit = _normalize(cand.get("circuit", ""))
        cand_location = _normalize(cand.get("location", ""))
        cand_year = cand.get("year")

        for kw in query_tokens:
            if kw and (kw in cand_name or kw in cand_circuit or kw in cand_location):
                score += 2
        if cand_year in year_matches:
            score += 5
        # Strong boost if the query explicitly contains the country or location name
        cand_country = _normalize(cand.get("country", ""))
        if cand_country and cand_country in normalized_query:
            score += 4
        if cand_location and cand_location in normalized_query:
            score += 4
        # prefer more recent dates when scores tie
        if score > best_score or (
            score == best_score and cand_year and best and cand_year > best.get("year", 0)
        ):
            best = cand
            best_score = score
    return best or candidates[0]


def query_interpreter(state: WeekendState):
    """
    Interprets the user query to identify the race weekend and any specific drivers or teams mentioned in the user's query.
    Weekend selection is deterministic; the LLM is only used to pull driver/team mentions.
    """
    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0)

    # Step 1: get weekend candidates deterministically
    weekend_candidates = list_weekends.invoke({"filter_str": state["user_query"]})
    best = _pick_best_candidate(weekend_candidates, state["user_query"])

    print(f"DEBUG [Query Interpreter] Candidates (top 5): {weekend_candidates[:5]}")
    print(f"DEBUG [Query Interpreter] Chosen weekend: {best}")

    if not best:
        return {"errors": ["Could not identify race weekend from query."]}

    # Step 2: extract driver/team focus only (avoid hallucinating weekend)
    focus_prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract the driver SURNAMES and team names explicitly mentioned in the query.

IMPORTANT: Return driver SURNAMES (last names), not first names or codes.
Examples:
- "Verstappen" not "Max" or "VER"
- "Hamilton" not "Lewis" or "HAM"
- "Norris" not "Lando" or "NOR"

Return ONLY valid JSON (no thinking, no explanation):
{{
  "drivers_focus": ["Surname1", "Surname2", ...],
  "teams_focus": ["Team1", ...]
}}

Do NOT invent entries. Only extract names explicitly mentioned.
"""),
        ("user", "{query}")
    ])
    focus_chain = focus_prompt | llm
    focus_raw = focus_chain.invoke({"query": state["user_query"]}).content

    print(f"DEBUG [Query Interpreter] Focus Output: {focus_raw}")

    try:
        content = focus_raw

        # Handle <think> tags that some models output
        if "<think>" in content:
            # Extract content after </think> tag
            if "</think>" in content:
                content = content.split("</think>")[-1]
            else:
                # No closing tag, try to find JSON after think block
                content = content.split("<think>")[-1]

        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        # Try to find JSON object in the content
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        focus_data = json.loads(content.strip())
        drivers_focus = focus_data.get("drivers_focus", [])
        teams_focus = focus_data.get("teams_focus", [])

        # Normalize driver names to surnames for database matching
        drivers_focus = [_normalize_driver_name(driver) for driver in drivers_focus]

        # Normalize team names to match database format
        teams_focus = [_normalize_team_name(team) for team in teams_focus]

        print(f"DEBUG [Query Interpreter] Normalized drivers: {drivers_focus}")

    except Exception as e:
        print(f"DEBUG [Query Interpreter] JSON parsing error: {e}")
        # Fallback: try to extract driver names directly from query
        drivers_focus = []
        query_lower = state["user_query"].lower()
        for key, surname in DRIVER_NAME_MAP.items():
            if key in query_lower and surname not in drivers_focus:
                drivers_focus.append(surname)
        teams_focus = []
        print(f"DEBUG [Query Interpreter] Fallback extraction: {drivers_focus}")

    return {
        "weekend_spec": best,
        "drivers_focus": drivers_focus,
        "teams_focus": teams_focus
    }

