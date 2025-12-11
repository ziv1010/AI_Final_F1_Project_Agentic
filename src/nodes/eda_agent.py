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
from langchain_core.prompts import PromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_run_output_path
from src.tools.token_tracker import track_llm_response, check_token_budget
from src.tools.search_tools import search_dataset, get_schema_info, explore_dataset_columns
from src.tools.code_execution_tools import run_python_code, save_visualization
from datetime import datetime

# Phase 2: Evaluation and error handling
try:
    from src.evaluation import track_node_start, track_node_end
    from src.utils import get_breaker, handle_exception
    PHASE2_ENABLED = True
except ImportError:
    PHASE2_ENABLED = False

# EDA Agent prompt - using standard ReAct PromptTemplate format for langchain_classic
EDA_PROMPT = PromptTemplate.from_template("""You are an expert data analyst specializing in motorsport data.
Your job is to explore and understand racing datasets.

You have access to these tools:
{tools}

**IMPORTANT RULES:**
- ALWAYS start by understanding what data is available using get_schema_info
- Use search_dataset for quick lookups
- Use run_python_code for complex analysis or aggregations
- Generate visualizations when they would help understanding
- Be concise but thorough in your analysis

**Dataset Context:**
{schema_summary}

**Analysis Depth:** {analysis_depth}

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
    
    # Initialize log content
    log_lines = []
    log_lines.append("=" * 60)
    log_lines.append("EDA AGENT LOG")
    log_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    log_lines.append("=" * 60)
    log_lines.append("")
    log_lines.append("## User Query")
    log_lines.append(state.get("user_query", ""))
    log_lines.append("")
    log_lines.append("## Schema Summary (truncated)")
    log_lines.append(schema_summary[:1500])
    log_lines.append("")
    
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
        
        log_lines.append("## EDA Query")
        log_lines.append(eda_query)
        log_lines.append("")
        
        # Run agent
        result = executor.invoke({
            "input": eda_query,
            "schema_summary": schema_summary[:2000],  # Limit context size
            "analysis_depth": state.get("analysis_depth", "basic")
        })
        
        # Extract results
        eda_results = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])
        
        # Log intermediate steps (agent actions and observations)
        log_lines.append("## Agent Actions (Intermediate Steps)")
        for step_num, step in enumerate(intermediate_steps, 1):
            log_lines.append(f"### Step {step_num}")
            if hasattr(step, '__iter__') and len(step) > 0:
                action = step[0]
                observation = step[1] if len(step) > 1 else ""
                if hasattr(action, 'tool'):
                    log_lines.append(f"**Tool:** {action.tool}")
                    log_lines.append(f"**Input:** {action.tool_input}")
                else:
                    log_lines.append(f"**Action:** {str(action)[:500]}")
                obs_str = str(observation)
                log_lines.append(f"**Observation:** {obs_str[:1500]}..." if len(obs_str) > 1500 else f"**Observation:** {obs_str}")
            else:
                log_lines.append(f"**Step Data:** {str(step)[:500]}")
            log_lines.append("")
        
        # Log final output
        log_lines.append("## Final Output")
        log_lines.append(eda_results)
        log_lines.append("")
        
        # Extract any visualizations created
        visualizations = []
        for step in intermediate_steps:
            if hasattr(step, '__iter__') and len(step) > 1:
                action_output = str(step[1]) if len(step) > 1 else ""
                if "saved:" in action_output.lower() or ".png" in action_output:
                    visualizations.append(action_output)
        
        # Log summary
        log_lines.append("## Summary")
        log_lines.append(f"- Agent steps: {len(intermediate_steps)}")
        log_lines.append(f"- Visualizations generated: {len(visualizations)}")
        log_lines.append(f"- Output length: {len(eda_results)} chars")
        
        print(f"[EDA Agent] Exploration complete. Generated {len(visualizations)} visualizations.")
        
        # Save log to run output directory
        try:
            run_output_path = get_run_output_path()
            run_output_path.mkdir(parents=True, exist_ok=True)
            log_path = run_output_path / "eda_agent_log.txt"
            with open(log_path, "w") as f:
                f.write("\n".join(log_lines))
            print(f"[EDA Agent] Log saved to: {log_path}")
        except Exception as log_error:
            print(f"[EDA Agent] Could not save log: {log_error}")
        
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
        log_lines.append("## ERROR")
        log_lines.append(f"Agent error: {str(e)}")
        
        # Save log even on error
        try:
            run_output_path = get_run_output_path()
            run_output_path.mkdir(parents=True, exist_ok=True)
            log_path = run_output_path / "eda_agent_log.txt"
            with open(log_path, "w") as f:
                f.write("\n".join(log_lines))
        except:
            pass
        
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
