import os
from src.graph import build_graph

def run_demo():
    # Example query
    query = "Compare Verstappen and Hamilton at the 2021 Bahrain GP"
    
    print(f"Running Demo Query: {query}")
    
    if "GROQ_API_KEY" not in os.environ:
        print("Please set GROQ_API_KEY")
        return

    graph = build_graph()
    
    initial_state = {
        "user_query": query,
        "messages": [],
        "errors": [],
        "analysis_outputs": {},
        "code_snippets": [],
        "figures": [],
        "plan": "",
        "weekend_spec": None,
        "drivers_focus": []
    }
    
    print("Graph initialized. Streaming events...")
    
    try:
        final_state = graph.invoke(initial_state)
        
        print("\n=== Analysis Complete ===")
        if final_state.get("weekend_spec"):
            print(f"Weekend: {final_state['weekend_spec']['name']} {final_state['weekend_spec']['year']}")
        
        print("\nGenerated Figures:")
        for fig in final_state.get("figures", []):
            print(f"- {fig}")
            
        print("\nReport:")
        report_path = final_state.get("analysis_outputs", {}).get("report_path")
        if report_path:
            print(f"Saved to: {report_path}")
            
    except Exception as e:
        print(f"Demo failed: {e}")

if __name__ == "__main__":
    run_demo()
