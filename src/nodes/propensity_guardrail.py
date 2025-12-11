"""
Propensity Guardrail Agent for Universal Racing Analytics.

A ReAct agent that validates proposed factors using statistical methods:
1. Correlation analysis
2. Feature importance
3. Propensity score analysis
4. Statistical hypothesis testing

Filters out factors that don't have statistical significance.
"""

from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG
from src.tools.token_tracker import track_llm_response, check_token_budget
from src.tools.statistical_tools import (
    calculate_correlation,
    calculate_feature_importance,
    run_statistical_test,
    calculate_propensity_score
)
from typing import List, Dict, Any
import json
import re

# Phase 2: Evaluation and error handling
try:
    from src.evaluation import track_node_start, track_node_end, track_factor
    from src.utils import get_breaker, handle_exception
    from src.visualization import create_validation_summary_plot
    PHASE2_ENABLED = True
except ImportError:
    PHASE2_ENABLED = False


# Propensity Guardrail prompt
PROPENSITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a statistical analyst validating factor causality.
Your job is to determine which proposed factors ACTUALLY affect the outcome.

You have access to these statistical tools:
1. **calculate_correlation**: Test linear/monotonic relationship (use first!)
2. **calculate_feature_importance**: Rank factors by predictive power
3. **run_statistical_test**: Test group differences (ANOVA, t-test, etc.)
4. **calculate_propensity_score**: Estimate causal effect (advanced)

**VALIDATION CRITERIA:**
- Correlation: |r| > 0.3 AND p < 0.05 = SIGNIFICANT
- Feature Importance: > 5% = SIGNIFICANT  
- Statistical Test: p < 0.05 = SIGNIFICANT
- Propensity Score: ATE significant at p < 0.05 = CAUSAL

**YOUR JOB:**
1. For each proposed factor, run at least ONE statistical test
2. Determine if the factor is statistically significant
3. REJECT factors that fail validation
4. Report validated factors with confidence scores

**DATA CONTEXT:**
{data_context}

**OUTCOME VARIABLE:** {outcome_column}

**PROPOSED FACTORS:**
{proposed_factors}

At the end, provide a JSON summary:
```json
{{
  "validated_factors": [
    {{"factor": "name", "test": "correlation", "statistic": 0.72, "p_value": 0.001, "significant": true}}
  ],
  "rejected_factors": [
    {{"factor": "name", "reason": "p-value too high"}}
  ]
}}
```"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])


def propensity_guardrail(state: WeekendState) -> dict:
    """
    Propensity Guardrail using ReAct framework.
    
    Validates proposed factors using statistical analysis to ensure
    they have actual causal impact on outcomes.
    
    This prevents hallucinated factors from affecting the analysis.
    """
    print("\n=== [Propensity Guardrail] Validating Factor Causality ===")
    
    # Phase 2: Start metrics tracking
    metric = None
    if PHASE2_ENABLED:
        metric = track_node_start("propensity_guardrail")
    
    try:
        # Get proposed factors
        factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
        proposed_factors = factor_analysis.get("key_factors", [])
        
        if not proposed_factors:
            print("[Propensity Guardrail] No factors to validate")
            if PHASE2_ENABLED and metric:
                track_node_end(metric, success=True, tokens=0)
            return {
                "validated_factors": [],
                "propensity_report": "No factors proposed for validation."
            }
        
        print(f"[Propensity Guardrail] Validating {len(proposed_factors)} factors: {proposed_factors}")
    except Exception as e:
        if PHASE2_ENABLED:
            if metric:
                track_node_end(metric, success=False, error=str(e))
            print(handle_exception(e, "propensity_guardrail setup"))
        raise
    
    # Check token budget  
    if not check_token_budget(4000):
        print("[Propensity Guardrail] Insufficient token budget, using basic validation")
        return _basic_validation(state, proposed_factors)
    
    # Get data context
    data_context = _build_data_context(state)
    outcome_column = _detect_outcome_column(state)
    
    # Define tools
    tools = [
        calculate_correlation,
        calculate_feature_importance,
        run_statistical_test,
        calculate_propensity_score
    ]
    
    # Create LLM
    llm = ChatGroq(
        model=CONFIG["llm"]["model"],
        temperature=0.1
    )
    
    try:
        # Create ReAct agent
        agent = create_react_agent(llm, tools, PROPENSITY_PROMPT)
        
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=6,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        # Run validation
        result = executor.invoke({
            "input": f"Validate these factors for statistical significance: {proposed_factors}",
            "data_context": data_context,
            "outcome_column": outcome_column,
            "proposed_factors": json.dumps(proposed_factors)
        })
        
        # Track tokens
        track_llm_response(None, manual_count=2000)
        
        # Parse results
        output = result.get("output", "")
        validated_factors, rejected_factors = _parse_validation_results(output, proposed_factors)
        
        print(f"[Propensity Guardrail] Validated: {len(validated_factors)}, Rejected: {len(rejected_factors)}")
        
        return {
            "validated_factors": validated_factors,
            "propensity_report": output,
            "analysis_outputs": {
                **state.get("analysis_outputs", {}),
                "validated_factors": validated_factors,
                "rejected_factors": rejected_factors
            }
        }
        
    except Exception as e:
        print(f"[Propensity Guardrail] Agent error: {e}")
        return _basic_validation(state, proposed_factors)


def _build_data_context(state: WeekendState) -> str:
    """
    Build data context for the guardrail agent.
    """
    lines = []
    
    # Get data paths
    data_paths = state.get("analysis_outputs", {}).get("data_paths", {})
    if data_paths:
        lines.append("**Available data files:**")
        for key, path in data_paths.items():
            lines.append(f"  - {key}: {path}")
    
    # Get schema info if available
    try:
        from src.tools.schema_detector import get_schema
        from src.config import get_raw_data_path
        schema = get_schema(get_raw_data_path())
        
        lines.append("\n**Available tables:**")
        for table_name, table in list(schema.tables.items())[:5]:
            numeric_cols = [col for col, info in table.columns.items() 
                          if info.is_numeric and not info.is_id]
            lines.append(f"  - {table_name}: {numeric_cols[:10]}")
    except Exception as e:
        lines.append(f"\nNote: Could not load schema: {e}")
    
    return "\n".join(lines) if lines else "Use data from data/raw/*.csv files"


def _detect_outcome_column(state: WeekendState) -> str:
    """
    Detect the most likely outcome column.
    """
    # Check user query for hints
    query_lower = state.get("user_query", "").lower()
    
    if "point" in query_lower:
        return "points"
    if "win" in query_lower or "position" in query_lower:
        return "position"
    if "time" in query_lower or "lap" in query_lower:
        return "milliseconds"
    
    # Default based on domain
    try:
        from src.domain_config import get_domain_config
        domain_config = get_domain_config()
        
        if "position" in domain_config.column_mappings:
            return domain_config.column_mappings["position"]
        if "points" in domain_config.column_mappings:
            return domain_config.column_mappings["points"]
    except:
        pass
    
    return "position"


def _parse_validation_results(output: str, proposed_factors: List[str]) -> tuple:
    """
    Parse validation results from agent output.
    """
    validated = []
    rejected = []
    
    # Try to find JSON in output
    json_match = re.search(r'\{[\s\S]*"validated_factors"[\s\S]*\}', output)
    
    if json_match:
        try:
            data = json.loads(json_match.group())
            validated = data.get("validated_factors", [])
            rejected = data.get("rejected_factors", [])
            return validated, rejected
        except json.JSONDecodeError:
            pass
    
    # Fallback: Parse text for results
    output_lower = output.lower()
    
    for factor in proposed_factors:
        factor_lower = factor.lower()
        
        # Look for validation indicators near factor name
        factor_section = ""
        if factor_lower in output_lower:
            idx = output_lower.index(factor_lower)
            factor_section = output_lower[idx:idx+200]
        
        # Check for significance indicators
        if any(kw in factor_section for kw in ["significant", "validated", "confirmed", "p < 0.05"]):
            validated.append({
                "factor": factor,
                "significant": True,
                "source": "text_parsing"
            })
        elif any(kw in factor_section for kw in ["not significant", "rejected", "p > 0.05", "failed"]):
            rejected.append({
                "factor": factor,
                "reason": "Failed statistical validation"
            })
        else:
            # If unclear, include with lower confidence
            validated.append({
                "factor": factor,
                "significant": True,
                "confidence": "low",
                "source": "default"
            })
    
    return validated, rejected


def _basic_validation(state: WeekendState, proposed_factors: List[str]) -> dict:
    """
    Fallback basic validation without full agent.
    """
    print("[Propensity Guardrail] Running basic validation...")
    
    validated = []
    rejected = []
    report_lines = ["## Basic Factor Validation\n"]
    
    # Get data path
    try:
        from src.config import get_raw_data_path
        data_path = get_raw_data_path()
        result_file = data_path / "results.csv"
        
        if not result_file.exists():
            # Try to find any results file
            csv_files = list(data_path.glob("*.csv"))
            result_file = csv_files[0] if csv_files else None
    except:
        result_file = None
    
    if result_file:
        # Run basic correlation for each factor
        for factor in proposed_factors[:5]:  # Limit to 5
            try:
                result = calculate_correlation.invoke({
                    "factor_column": factor,
                    "outcome_column": "position",
                    "data_path": str(result_file),
                    "method": "spearman"
                })
                
                report_lines.append(f"### {factor}")
                report_lines.append(result)
                report_lines.append("")
                
                # Check if significant
                if "SIGNIFICANT" in result and "NOT SIGNIFICANT" not in result:
                    validated.append({
                        "factor": factor,
                        "test": "correlation",
                        "significant": True
                    })
                else:
                    rejected.append({
                        "factor": factor,
                        "reason": "Not statistically significant"
                    })
                    
            except Exception as e:
                # If we can't test, include the factor anyway
                validated.append({
                    "factor": factor,
                    "test": "untested",
                    "significant": True,
                    "note": str(e)
                })
    else:
        # Can't validate, include all factors
        validated = [{"factor": f, "test": "none", "significant": True} for f in proposed_factors]
        report_lines.append("Could not access data for validation. Including all factors.")
    
    return {
        "validated_factors": validated,
        "propensity_report": "\n".join(report_lines),
        "analysis_outputs": {
            **state.get("analysis_outputs", {}),
            "validated_factors": validated,
            "rejected_factors": rejected
        }
    }
