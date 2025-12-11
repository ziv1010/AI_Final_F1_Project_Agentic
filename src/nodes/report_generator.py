from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.config import CONFIG, get_outputs_path, get_run_output_path

def report_generator(state: WeekendState):
    """
    Generates a final report based on the analysis results.
    """
    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.2)
    
    stdout = state["analysis_outputs"].get("stdout", "")
    stderr = state["analysis_outputs"].get("stderr", "")
    figures = state.get("figures", [])
    tables = state["analysis_outputs"].get("tables", [])
    errors = state.get("errors", [])

    if errors or (not stdout.strip() and not figures and not tables):
        # Write a short failure report and log the errors for transparency
        failure_report = "## Analysis Incomplete\n\n"
        if errors:
            failure_report += "The analysis failed with the following errors:\n\n"
            for err in errors:
                failure_report += f"- {err}\n"
        else:
            failure_report += "No analysis output was produced. Please check the logs.\n"

        # Save to run-specific directory
        run_path = get_run_output_path()
        run_report_path = run_path / "race_report.md"
        with open(run_report_path, "w") as f:
            f.write(failure_report)

        run_log_path = run_path / "analysis_log.txt"
        with open(run_log_path, "w") as f:
            f.write(stdout)
            if stderr:
                f.write("\n\n[stderr]\n")
                f.write(stderr)
        
        # Also save to main outputs for backwards compatibility
        outputs_path = get_outputs_path()
        report_path = outputs_path / "race_report.md"
        with open(report_path, "w") as f:
            f.write(failure_report)

        log_path = outputs_path / "analysis_log.txt"
        with open(log_path, "w") as f:
            f.write(stdout)
            if stderr:
                f.write("\n\n[stderr]\n")
                f.write(stderr)

        return {
            "analysis_outputs": {
                **state["analysis_outputs"],
                "report": failure_report,
                "report_path": str(report_path),
                "log_path": str(log_path)
            }
        }
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an F1 strategy analyst. Write a concise narrative response to the user query using ONLY the data provided in the Analysis Output below.

User Query: {query}

Analysis Output (THIS IS THE ONLY SOURCE OF TRUTH - use these exact values):
{stdout}

Additional Logs:
{stderr}

Generated Figures:
{figures}

**CRITICAL RULES - YOU MUST FOLLOW THESE:**
1. ONLY use information that appears in the "Analysis Output" above.
2. If the output says "RACE WINNER: X from Y", then X is the winner from team Y. DO NOT contradict this.
3. DO NOT make up, guess, or assume any race results, winners, or statistics.
4. DO NOT use your training knowledge about F1 races - ONLY use the data provided above.
5. If data is missing or unclear, say "Data not available" rather than guessing.
6. Quote specific numbers and names exactly as they appear in the Analysis Output.
7. If the Analysis Output is empty or shows errors, report that the analysis failed.

Guidelines:
- Stay 100% faithful to the data provided; never invent results.
- Reference figures if they exist by name from the figures list.
- Prefer short paragraphs or bullet points as needed.
- Keep it readable Markdown.
"""),
        ("user", "Write the report using ONLY the data from the Analysis Output. Do not add any information that isn't in the output.")
    ])
    
    chain = prompt | llm
    print(f"\n=== [Report Generator] Generating Report ===")
    
    response = chain.invoke({
        "query": state["user_query"],
        "stdout": stdout,
        "stderr": stderr,
        "figures": str(figures)
    })
    
    report = response.content
    print(f"=== [Report Generator] Report Generated ({len(report)} chars) ===\n")
    
    # Save report to run-specific directory
    run_path = get_run_output_path()
    run_report_path = run_path / "race_report.md"
    with open(run_report_path, "w") as f:
        f.write(report)
        
    # Save analysis log to run-specific directory
    run_log_path = run_path / "analysis_log.txt"
    with open(run_log_path, "w") as f:
        f.write(stdout)
        if stderr:
            f.write("\n\n[stderr]\n")
            f.write(stderr)
    
    # Also save to main outputs for backwards compatibility
    outputs_path = get_outputs_path()
    report_path = outputs_path / "race_report.md"
    with open(report_path, "w") as f:
        f.write(report)
        
    log_path = outputs_path / "analysis_log.txt"
    with open(log_path, "w") as f:
        f.write(stdout)
        if stderr:
            f.write("\n\n[stderr]\n")
            f.write(stderr)
    
    print(f"[Report Generator] Reports saved to run: {run_path}")
        
    return {"analysis_outputs": {**state["analysis_outputs"], "report": report, "report_path": str(report_path), "log_path": str(log_path)}}
