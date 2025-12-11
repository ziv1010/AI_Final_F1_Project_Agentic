"""
Web Search Agent for Universal Racing Analytics.

A ReAct agent that can:
1. Search the web for real-time information
2. Look up Wikipedia articles
3. Find racing news and context
4. Enrich analysis with external data

Uses DuckDuckGo and Wikipedia for searches.
"""

from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG
from src.tools.token_tracker import track_llm_response, check_token_budget
from src.tools.search_tools import search_web
from typing import List


# Web Search Agent prompt
WEB_SEARCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert motorsport researcher.
Your job is to find relevant external information to support data analysis.

You have access to:
1. **search_web**: Search the web using DuckDuckGo or Wikipedia

**IMPORTANT RULES:**
- Search for factual, relevant information only
- Focus on context that would help explain data patterns
- Look for historical events, rule changes, incidents, or news
- Limit searches to 3 queries maximum
- Be concise in your summaries

**What to search for:**
{search_context}

When you have enough information, summarize the key findings that would be relevant for the analysis."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])


def web_search_agent(state: WeekendState) -> dict:
    """
    Web Search Agent using ReAct framework.
    
    Searches the web for:
    - Background context on events/competitors
    - Recent news that might affect analysis
    - Historical information for comparison
    
    This enriches the analysis with real-time external data.
    """
    print("\n=== [Web Search Agent] Gathering External Context ===")
    
    # Check if web search should run
    analysis_depth = state.get("analysis_depth", "basic")
    if analysis_depth == "basic":
        print("[Web Search Agent] Skipping web search for basic analysis")
        return {"web_context": "", "search_queries": []}
    
    # Check token budget
    if not check_token_budget(3000):
        print("[Web Search Agent] Insufficient token budget, skipping")
        return {"web_context": "", "search_queries": []}
    
    # Generate search queries based on state
    search_queries = _generate_search_queries(state)
    
    if not search_queries:
        print("[Web Search Agent] No search queries generated")
        return {"web_context": "", "search_queries": []}
    
    # Define tools
    tools = [search_web]
    
    # Create LLM
    llm = ChatGroq(
        model=CONFIG["llm"]["model"],
        temperature=0.1
    )
    
    try:
        # Create ReAct agent
        agent = create_react_agent(llm, tools, WEB_SEARCH_PROMPT)
        
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=4,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        # Build search context
        search_context = _build_search_context(state, search_queries)
        
        # Run agent
        result = executor.invoke({
            "input": f"Search for relevant information using these queries: {search_queries[:3]}",
            "search_context": search_context
        })
        
        # Track tokens
        track_llm_response(None, manual_count=1500)
        
        web_context = result.get("output", "")
        
        print(f"[Web Search Agent] Found context ({len(web_context)} chars)")
        
        return {
            "web_context": web_context,
            "search_queries": search_queries[:3]
        }
        
    except Exception as e:
        print(f"[Web Search Agent] Error: {e}")
        # Try direct search as fallback
        return _fallback_search(search_queries)


def _generate_search_queries(state: WeekendState) -> List[str]:
    """
    Generate relevant search queries based on the analysis context.
    """
    queries = []
    
    user_query = state.get("user_query", "")
    event_spec = state.get("weekend_spec") or state.get("event_spec", {})
    competitors = state.get("drivers_focus", []) or state.get("competitors_focus", [])
    teams = state.get("teams_focus", [])
    
    # Get domain info
    try:
        from src.domain_config import get_domain_config
        domain_config = get_domain_config()
        domain_name = domain_config.domain_name.upper()
    except:
        domain_name = "racing"
    
    # Build queries based on available info
    if event_spec:
        event_name = event_spec.get("name", "")
        year = event_spec.get("year", "")
        if event_name and year:
            queries.append(f"{domain_name} {event_name} {year} race summary")
    
    # Competitor queries
    for competitor in competitors[:2]:
        queries.append(f"{competitor} {domain_name} performance career")
    
    # Team queries  
    for team in teams[:1]:
        queries.append(f"{team} {domain_name} team history")
    
    # Factor-based queries
    factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
    if factor_analysis:
        hypotheses = factor_analysis.get("hypotheses", [])
        for hypothesis in hypotheses[:1]:
            queries.append(f"{domain_name} {hypothesis}")
    
    # If no specific queries, use user query
    if not queries and user_query:
        # Clean up user query for search
        queries.append(f"{domain_name} {user_query[:50]}")
    
    return queries[:5]


def _build_search_context(state: WeekendState, queries: List[str]) -> str:
    """
    Build context string for the search agent.
    """
    lines = ["**Analysis Context:**"]
    
    user_query = state.get("user_query", "")
    lines.append(f"User Question: {user_query}")
    
    event_spec = state.get("weekend_spec") or state.get("event_spec", {})
    if event_spec:
        lines.append(f"Event: {event_spec.get('name', 'Unknown')} ({event_spec.get('year', '')})")
    
    competitors = state.get("drivers_focus", []) or state.get("competitors_focus", [])
    if competitors:
        lines.append(f"Competitors of interest: {competitors}")
    
    teams = state.get("teams_focus", [])
    if teams:
        lines.append(f"Teams of interest: {teams}")
    
    lines.append(f"\n**Suggested search queries:** {queries}")
    
    return "\n".join(lines)


def _fallback_search(queries: List[str]) -> dict:
    """
    Fallback direct search without agent.
    """
    from src.tools.search_tools import search_web
    
    results = []
    executed_queries = []
    
    for query in queries[:2]:
        try:
            result = search_web.invoke({"query": query, "search_type": "general"})
            if result and "error" not in result.lower():
                results.append(result)
                executed_queries.append(query)
        except Exception as e:
            print(f"[Web Search Fallback] Error for '{query}': {e}")
    
    return {
        "web_context": "\n\n---\n\n".join(results),
        "search_queries": executed_queries
    }
