from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import WeekendState
from src.tools.data_tools import inspect_dataset
from src.config import CONFIG


def plan_reviewer(state: WeekendState):
    """
    Acts as a second-pass thinking agent to stress-test and improve the analysis plan.
    It checks the current plan against the available data paths and schemas, then returns
    a refined plan plus any gaps or risks the coder should keep in mind.
    """
    llm = ChatGroq(model=CONFIG["llm"]["model"], temperature=0.1)

    schemas = inspect_dataset.invoke({"schema_only": True})
    data_paths = state["analysis_outputs"].get("data_paths", {})

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the thinking/QA agent that reviews the analysis plan before coding.
Sanity-check the scope, required columns, joins, and feasibility against the actual schemas and data paths.
If the user asks for seasons/years beyond what the cached data contains, call that out and propose a fallback.
Avoid prescribing exact column names; instead, point to the relevant tables/fields conceptually using the schemas.

Return two sections in Markdown:
Refined Plan:
1) ...
2) ...
Gaps or Risks:
- ... (focus on data coverage, missing columns, time conversions, joins)
"""),
        ("user", """User Query: {query}
Weekend: {weekend}
Focus: Drivers {drivers_focus}, Teams {teams_focus}
Data paths: {data_paths}
Schemas: {schemas}

Current Plan:
{plan}
""")
    ])

    response = (prompt | llm).invoke({
        "query": state["user_query"],
        "weekend": str(state.get("weekend_spec")),
        "drivers_focus": str(state.get("drivers_focus")),
        "teams_focus": str(state.get("teams_focus")),
        "data_paths": str(data_paths),
        "schemas": str(schemas),
        "plan": state.get("plan", "")
    })

    refined = response.content

    return {
        "plan_review": refined
    }
