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
from langchain_core.prompts import PromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_run_output_path
from src.tools.token_tracker import track_llm_response, check_token_budget
from src.tools.search_tools import search_web
from typing import List
from datetime import datetime


# Web Search Agent prompt - using standard ReAct PromptTemplate format for langchain_classic
WEB_SEARCH_PROMPT = PromptTemplate.from_template("""You are an expert motorsport researcher.
Your job is to find relevant external information to support data analysis.

You have access to these tools:
{tools}

**IMPORTANT RULES:**
- Search for factual, relevant information only
- Focus on context that would help explain data patterns
- Look for historical events, rule changes, incidents, or news
- Limit searches to 3 queries maximum
- Be concise in your summaries
- **PREFER Wikipedia and official F1 sources** - add "site:wikipedia.org" or "wikipedia" to your searches for reliable information

**What to search for:**
{search_context}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}""")


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
    
    # Initialize log content
    log_lines = []
    log_lines.append("=" * 60)
    log_lines.append("WEB SEARCH AGENT LOG")
    log_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    log_lines.append("=" * 60)
    log_lines.append("")
    log_lines.append("## Search Queries Generated")
    for i, query in enumerate(search_queries[:3], 1):
        log_lines.append(f"  {i}. {query}")
    log_lines.append("")
    
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
        log_lines.append("## Search Context")
        log_lines.append(search_context)
        log_lines.append("")
        
        # Run agent
        result = executor.invoke({
            "input": f"Search for relevant information using these queries: {search_queries[:3]}",
            "search_context": search_context
        })
        
        # Token tracking handled by executor automatically
        
        web_context = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])
        
        # Log intermediate steps (agent actions and observations)
        log_lines.append("## Agent Actions (Intermediate Steps)")
        for step_num, (action, observation) in enumerate(intermediate_steps, 1):
            log_lines.append(f"### Step {step_num}")
            log_lines.append(f"**Tool:** {action.tool}")
            log_lines.append(f"**Input:** {action.tool_input}")
            log_lines.append(f"**Observation:** {observation[:1000]}..." if len(str(observation)) > 1000 else f"**Observation:** {observation}")
            log_lines.append("")
        
        # Log final output
        log_lines.append("## Final Output")
        log_lines.append(web_context)
        log_lines.append("")
        log_lines.append(f"## Summary")
        log_lines.append(f"- Total queries: {len(search_queries[:3])}")
        log_lines.append(f"- Agent steps: {len(intermediate_steps)}")
        log_lines.append(f"- Output length: {len(web_context)} chars")
        
        print(f"[Web Search Agent] Found context ({len(web_context)} chars)")
        
        # Save log to run output directory
        try:
            run_output_path = get_run_output_path()
            run_output_path.mkdir(parents=True, exist_ok=True)
            log_path = run_output_path / "web_search_log.txt"
            with open(log_path, "w") as f:
                f.write("\n".join(log_lines))
            print(f"[Web Search Agent] Log saved to: {log_path}")
        except Exception as log_error:
            print(f"[Web Search Agent] Could not save log: {log_error}")
        
        return {
            "web_context": web_context,
            "search_queries": search_queries[:3]
        }
        
    except Exception as e:
        print(f"[Web Search Agent] Error: {e}")
        log_lines.append(f"## ERROR")
        log_lines.append(f"Agent error: {str(e)}")
        
        # Try to save log even on error
        try:
            run_output_path = get_run_output_path()
            run_output_path.mkdir(parents=True, exist_ok=True)
            log_path = run_output_path / "web_search_log.txt"
            with open(log_path, "w") as f:
                f.write("\n".join(log_lines))
        except:
            pass
        
        # Try direct search as fallback
        return _fallback_search(search_queries)


def _generate_search_queries(state: WeekendState) -> List[str]:
    """
    Generate relevant search queries based on the analysis context.
    Focuses on race-specific factors, results, and performance analysis.
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
        domain_name = "F1"
    
    # Build queries based on event and competitors
    event_name = ""
    year = ""
    if event_spec:
        event_name = event_spec.get("name", "")
        year = event_spec.get("year", "")
    
    # 1. Race results from Wikipedia - most reliable source
    if event_name and year:
        queries.append(f"{year} {event_name} wikipedia")
    
    # 2. Specific driver comparison at this race
    if len(competitors) >= 2 and event_name and year:
        queries.append(f"{competitors[0]} vs {competitors[1]} {year} {event_name}")
    
    # 3. Key factors that affected this specific race
    if event_name and year:
        queries.append(f"{year} {event_name} race report results")
    
    # 4. Driver-specific performance at this race (not career)
    for competitor in competitors[:2]:
        if event_name and year:
            queries.append(f"{competitor} {year} {event_name} wikipedia")
    
    # 5. Factor-based queries from factor analysis
    factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
    if factor_analysis:
        key_factors = factor_analysis.get("key_factors", [])
        hypotheses = factor_analysis.get("hypotheses", [])
        
        # Add factor-specific queries
        for factor in key_factors[:2]:
            if event_name and year:
                queries.append(f"{year} {event_name} {factor}")
        
        # Add hypothesis-based queries
        for hypothesis in hypotheses[:1]:
            queries.append(f"{domain_name} {hypothesis} {year}")
    
    # 6. Team performance if teams specified
    for team in teams[:1]:
        if year:
            queries.append(f"{team} {domain_name} {year} season performance issues")
    
    # Fallback: use cleaned user query
    if not queries and user_query:
        queries.append(f"{domain_name} {user_query[:80]} wikipedia")
    
    return queries[:6]  # Return up to 6 focused queries


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
