"""
Universal Query Interpreter for Racing Analytics.

Interprets user queries to identify:
- The racing event/weekend of interest
- Competitors (drivers/riders) mentioned
- Teams/constructors mentioned

Uses dynamic entity extraction instead of hardcoded maps.
Works with any racing domain (F1, MotoGP, IndyCar, etc.).
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG
from src.tools.token_tracker import track_llm_response
import json
import re
import unicodedata
from typing import List, Dict, Optional


def _normalize(text: str) -> str:
    """Lowercase and strip accents for matching."""
    text = str(text).lower()
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _get_domain_config():
    """Get domain configuration with entity information."""
    try:
        from src.domain_config import get_domain_config
        return get_domain_config()
    except Exception:
        return None


def _list_events(filter_str: Optional[str] = None) -> List[Dict]:
    """
    List racing events from the dataset.
    Works with any racing domain.
    """
    from src.config import get_raw_data_path
    import pandas as pd
    
    data_path = get_raw_data_path()
    
    # Try to detect domain and find appropriate files
    try:
        from src.domain_config import get_domain_config
        domain_config = get_domain_config()
        domain = domain_config.domain_name
    except:
        domain = "auto"
    
    events = []
    
    # Check for F1 races.csv
    races_file = data_path / "races.csv"
    if races_file.exists():
        try:
            df = pd.read_csv(races_file)
            
            # Try to merge with circuits if available
            circuits_file = data_path / "circuits.csv"
            if circuits_file.exists():
                circuits = pd.read_csv(circuits_file)
                df = df.merge(circuits, on="circuitId", how="left", suffixes=("", "_circuit"))
            
            # Build search string
            search_cols = []
            for col in ["year", "name", "name_circuit", "location", "country"]:
                if col in df.columns:
                    search_cols.append(col)
            
            if search_cols:
                df["_search"] = df[search_cols].fillna("").astype(str).agg(" ".join, axis=1).apply(_normalize)
            else:
                df["_search"] = df.iloc[:, 0].astype(str).apply(_normalize)
            
            # Score and filter
            if filter_str:
                keywords = [_normalize(kw) for kw in str(filter_str).split() if kw.strip()]
                df["_score"] = df["_search"].apply(lambda x: sum(1 for kw in keywords if kw in x))
            else:
                df["_score"] = 0
            
            # Sort by score and date
            if "date" in df.columns:
                df = df.sort_values(["_score", "date"], ascending=[False, False])
            else:
                df = df.sort_values("_score", ascending=False)
            
            # Build event list
            for _, row in df.head(20).iterrows():
                event = {
                    "race_id": int(row.get("raceId", 0)) if "raceId" in row else None,
                    "year": int(row.get("year", 0)) if "year" in row else None,
                    "round": int(row.get("round", 0)) if "round" in row else None,
                    "name": row.get("name", "Unknown"),
                    "circuit": row.get("name_circuit", row.get("circuitId", "")),
                    "country": row.get("country", ""),
                    "location": row.get("location", ""),
                    "date": str(row.get("date", "")),
                    "score": int(row.get("_score", 0))
                }
                events.append(event)
            
            return events
        except Exception as e:
            print(f"[Query Interpreter] Error reading races.csv: {e}")
    
    # Check for MotoGP or other data
    for csv_file in data_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file, nrows=1000)
            
            # Check if this looks like event data
            event_cols = [c for c in df.columns if any(
                kw in c.lower() for kw in ["year", "race", "circuit", "event", "round", "gp"]
            )]
            
            if event_cols:
                # Build events from this file
                group_cols = [c for c in event_cols if "year" in c.lower()]
                if not group_cols:
                    group_cols = event_cols[:1]
                
                name_col = next((c for c in df.columns if "circuit" in c.lower() or "name" in c.lower()), None)
                year_col = next((c for c in df.columns if "year" in c.lower()), None)
                
                if name_col:
                    unique_events = df[[year_col, name_col]].drop_duplicates() if year_col else df[[name_col]].drop_duplicates()
                    
                    for _, row in unique_events.head(20).iterrows():
                        event = {
                            "name": row[name_col] if name_col else "Unknown",
                            "year": int(row[year_col]) if year_col and pd.notna(row[year_col]) else None,
                            "source_file": csv_file.name
                        }
                        
                        # Score against filter
                        if filter_str:
                            event_str = _normalize(str(row.values))
                            event["score"] = sum(1 for kw in _normalize(filter_str).split() if kw in event_str)
                        else:
                            event["score"] = 0
                        
                        events.append(event)
                
                if events:
                    events.sort(key=lambda x: x.get("score", 0), reverse=True)
                    return events[:20]
                    
        except Exception:
            continue
    
    return events


def _pick_best_candidate(candidates: List[Dict], query: str) -> Optional[Dict]:
    """Pick the best matching event from candidates."""
    if not candidates:
        return None
    
    normalized_query = _normalize(query)
    year_matches = re.findall(r"(19|20)\d{2}", query)
    year_matches = [int(y) for y in year_matches]
    query_tokens = normalized_query.split()

    best = None
    best_score = -1
    
    for cand in candidates:
        score = cand.get("score", 0)
        
        cand_name = _normalize(str(cand.get("name", "")))
        cand_circuit = _normalize(str(cand.get("circuit", "")))
        cand_location = _normalize(str(cand.get("location", "")))
        cand_year = cand.get("year")

        for kw in query_tokens:
            if kw and len(kw) > 2:
                if kw in cand_name or kw in cand_circuit or kw in cand_location:
                    score += 2
        
        if cand_year in year_matches:
            score += 5
        
        cand_country = _normalize(str(cand.get("country", "")))
        if cand_country and cand_country in normalized_query:
            score += 4
        
        if score > best_score or (
            score == best_score and cand_year and best and cand_year > best.get("year", 0)
        ):
            best = cand
            best_score = score
    
    return best or candidates[0]


def _extract_entities_with_llm(query: str, domain_config) -> Dict:
    """
    Use LLM to extract competitor and team names from query.
    This is domain-agnostic - works with any racing series.
    """
    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0)
    
    # Build domain-specific prompt
    if domain_config:
        primary_entity = domain_config.primary_entity
        secondary_entity = domain_config.secondary_entity
        domain_name = domain_config.domain_name.upper()
    else:
        primary_entity = "competitor"
        secondary_entity = "team"
        domain_name = "racing"
    
    focus_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are analyzing a {domain_name} query.
Extract the {primary_entity} names and {secondary_entity} names explicitly mentioned.

IMPORTANT:
- For {primary_entity}s, use their surname/family name (e.g., "Verstappen" not "Max")
- For {secondary_entity}s, use official names (e.g., "Red Bull" not "RB")
- Only extract names explicitly mentioned in the query
- Do NOT invent or assume names

Return ONLY valid JSON:
{{{{
  "competitors_focus": ["Name1", "Name2"],
  "teams_focus": ["Team1", "Team2"]
}}}}"""),
        ("user", "{query}")
    ])
    
    try:
        chain = focus_prompt | llm
        response = chain.invoke({"query": query})
        content = response.content
        
        # Track tokens
        track_llm_response(response)
        
        # Handle <think> tags
        if "<think>" in content:
            if "</think>" in content:
                content = content.split("</think>")[-1]
            else:
                content = content.split("<think>")[-1]
        
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        # Find JSON
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content.strip())
        
        return {
            "competitors_focus": data.get("competitors_focus", []),
            "teams_focus": data.get("teams_focus", [])
        }
        
    except Exception as e:
        print(f"[Query Interpreter] Entity extraction error: {e}")
        return {"competitors_focus": [], "teams_focus": []}


def query_interpreter(state: WeekendState) -> dict:
    """
    Interprets the user query to identify:
    - The racing event of interest
    - Competitors (drivers/riders) mentioned
    - Teams/constructors mentioned
    
    This is domain-agnostic and works with any racing dataset.
    """
    print("\n=== [Query Interpreter] Processing Query ===")
    
    user_query = state.get("user_query", "")
    print(f"[Query Interpreter] Query: {user_query}")
    
    # Get domain configuration
    domain_config = _get_domain_config()
    if domain_config:
        print(f"[Query Interpreter] Detected domain: {domain_config.domain_name}")
    
    # Step 1: Find matching events
    event_candidates = _list_events(user_query)
    best_event = _pick_best_candidate(event_candidates, user_query)

    print(f"[Query Interpreter] Candidates (top 5): {event_candidates[:5]}")
    print(f"[Query Interpreter] Chosen event: {best_event}")

    if not best_event:
        return {"errors": ["Could not identify racing event from query."]}

    # Step 2: Extract competitor/team focus using LLM
    entities = _extract_entities_with_llm(user_query, domain_config)
    competitors_focus = entities.get("competitors_focus", [])
    teams_focus = entities.get("teams_focus", [])
    
    print(f"[Query Interpreter] Competitors: {competitors_focus}")
    print(f"[Query Interpreter] Teams: {teams_focus}")

    # Return results
    return {
        # Universal fields
        "event_spec": best_event,
        "competitors_focus": competitors_focus,
        "teams_focus": teams_focus,
        "domain": domain_config.domain_name if domain_config else "auto",
        
        # Backwards compatibility (deprecated)
        "weekend_spec": best_event,
        "drivers_focus": competitors_focus,
    }
