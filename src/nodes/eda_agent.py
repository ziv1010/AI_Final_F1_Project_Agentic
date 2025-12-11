"""
EDA Agent for Universal Racing Analytics.

A ReAct agent that can:
1. Explore and search datasets
2. Generate visualizations
3. Provide data summaries
4. Answer data-related questions

Works with any racing dataset (F1, MotoGP, etc.) without hardcoded logic.
"""

from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG
from src.tools.token_tracker import track_llm_response, check_token_budget
from src.tools.search_tools import search_dataset, get_schema_info, explore_dataset_columns
from src.tools.code_execution_tools import run_python_code, save_visualization

# Phase 2: Evaluation and error handling
try:
    from src.evaluation import track_node_start, track_node_end
    from src.utils import get_breaker, handle_exception
    PHASE2_ENABLED = True
except ImportError:
    PHASE2_ENABLED = False

# EDA Agent prompt
EDA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert data analyst specializing in motorsport data.
Your job is to explore and understand racing datasets.

You have access to these tools:
1. **get_schema_info**: Get information about available tables and columns
2. **search_dataset**: Search for specific data using natural language
3. **explore_dataset_columns**: Find columns matching a pattern
4. **run_python_code**: Execute Python code for analysis
5. **save_visualization**: Create and save charts

**IMPORTANT RULES:**
- ALWAYS start by understanding what data is available using get_schema_info
- Use search_dataset for quick lookups
- Use run_python_code for complex analysis or aggregations
- Generate visualizations when they would help understanding
- Be concise but thorough in your analysis

**Dataset Context:**
{schema_summary}

**Analysis Depth:** {analysis_depth}

When you have gathered enough information, provide a clear summary of your findings."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])


def eda_agent(state: WeekendState) -> dict:
    """
    EDA Agent using ReAct framework.
    
    Explores the dataset to understand:
    - What data is available
    - Key statistics and summaries
    - Relevant visualizations
    
    This runs before analysis to ensure the model understands the data.
    """
    print("\n=== [EDA Agent] Exploring Dataset ===")
    
    # Phase 2: Start metrics tracking
    metric = None
    if PHASE2_ENABLED:
        metric = track_node_start("eda_agent")
    
    # Check token budget
    if not check_token_budget(5000):
        print("[EDA Agent] Insufficient token budget, using basic exploration")
        if PHASE2_ENABLED and metric:
            track_node_end(metric, success=True, tokens=0)
        return _basic_eda(state)
    
    # Get schema summary
    try:
        from src.tools.schema_detector import get_schema
        from src.config import get_raw_data_path
        schema = get_schema(get_raw_data_path())
        schema_summary = schema.get_summary()
    except Exception as e:
        print(f"[EDA Agent] Could not get schema: {e}")
        schema_summary = "Schema not available. Use get_schema_info tool to explore."
    
    # Define tools
    tools = [
        get_schema_info,
        search_dataset,
        explore_dataset_columns,
        run_python_code,
        save_visualization
    ]
    
    # Create LLM
    llm = ChatGroq(
        model=CONFIG["llm"]["model"],
        temperature=0.1
    )
    
    try:
        # Create ReAct agent
        agent = create_react_agent(llm, tools, EDA_PROMPT)
        
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        # Formulate EDA query based on user query
        user_query = state.get("user_query", "")
        eda_query = _formulate_eda_query(user_query)
        
        # Run agent
        result = executor.invoke({
            "input": eda_query,
            "schema_summary": schema_summary[:2000],  # Limit context size
            "analysis_depth": state.get("analysis_depth", "basic")
        })
        
        # Track tokens (approximate)
        track_llm_response(None, manual_count=2000)
        
        # Extract results
        eda_results = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])
        
        # Extract any visualizations created
        visualizations = []
        for step in intermediate_steps:
            if hasattr(step, '__iter__') and len(step) > 1:
                action_output = str(step[1]) if len(step) > 1 else ""
                if "saved:" in action_output.lower() or ".png" in action_output:
                    visualizations.append(action_output)
        
        print(f"[EDA Agent] Exploration complete. Generated {len(visualizations)} visualizations.")
        
        return {
            "eda_results": eda_results,
            "visualizations": visualizations,
            "analysis_outputs": {
                **state.get("analysis_outputs", {}),
                "eda_summary": eda_results,
                "schema_summary": schema_summary
            }
        }
        
    except Exception as e:
        print(f"[EDA Agent] Error: {e}")
        return _basic_eda(state)


def _formulate_eda_query(user_query: str) -> str:
    """
    Transform user query into an EDA exploration query.
    """
    query_lower = user_query.lower()
    
    # Check if this is an explicit EDA request
    eda_keywords = ["show data", "what data", "describe", "explore", "list all", 
                    "what columns", "schema", "available data"]
    
    if any(kw in query_lower for kw in eda_keywords):
        return user_query
    
    # Otherwise, create an exploration query
    return f"""Before analyzing the user's question: "{user_query}"

Please explore the dataset to understand:
1. What tables and columns are available
2. What entities (competitors, teams, events) exist in the data
3. Any relevant statistics for the query

Focus on data that would be needed to answer the user's question."""


def _basic_eda(state: WeekendState) -> dict:
    """
    Fallback basic EDA when token budget is low.
    """
    try:
        from src.tools.schema_detector import get_schema
        from src.config import get_raw_data_path
        
        schema = get_schema(get_raw_data_path())
        summary = schema.get_summary()
        
        return {
            "eda_results": summary,
            "visualizations": [],
            "analysis_outputs": {
                **state.get("analysis_outputs", {}),
                "eda_summary": summary,
                "schema_summary": summary
            }
        }
    except Exception as e:
        return {
            "eda_results": f"Error in basic EDA: {str(e)}",
            "visualizations": [],
            "analysis_outputs": state.get("analysis_outputs", {})
        }


def should_run_full_eda(state: WeekendState) -> bool:
    """
    Determine if full EDA should run based on query.
    """
    query_lower = state.get("user_query", "").lower()
    
    # Explicit EDA requests
    eda_keywords = ["show data", "what data", "describe", "explore", "list all",
                    "what columns", "schema", "what's available"]
    
    if any(kw in query_lower for kw in eda_keywords):
        return True
    
    # First-time analysis should explore
    if not state.get("analysis_outputs", {}).get("schema_summary"):
        return True
    
    return False
