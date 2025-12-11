"""
Visualization Dashboard for Universal Racing Analytics.

Creates interactive HTML dashboards using Plotly.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json


def create_session_dashboard(
    session_data: Dict[str, Any],
    output_path: Path = None
) -> Path:
    """
    Create an interactive HTML dashboard for a session.
    
    Args:
        session_data: Session metrics and analysis results
        output_path: Where to save the dashboard
        
    Returns:
        Path to the generated dashboard
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("[Dashboard] Plotly not installed. Using simple HTML dashboard.")
        return _create_simple_dashboard(session_data, output_path)
    
    output_path = output_path or Path("outputs/dashboards")
    output_path.mkdir(parents=True, exist_ok=True)
    
    session_id = session_data.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Node Execution Times",
            "Factor Importance",
            "Token Usage by Node",
            "Success Rate"
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "pie"}, {"type": "indicator"}]
        ]
    )
    
    # Node execution times
    nodes = session_data.get("nodes", [])
    if nodes:
        node_names = [n.get("name", "unknown") for n in nodes]
        durations = [n.get("duration_ms", 0) for n in nodes]
        colors = ["#2ecc71" if n.get("success", True) else "#e74c3c" for n in nodes]
        
        fig.add_trace(
            go.Bar(x=node_names, y=durations, marker_color=colors, name="Duration (ms)"),
            row=1, col=1
        )
    
    # Factor importance
    factors = session_data.get("factors", [])
    if factors:
        factor_names = [f.get("name", "unknown") for f in factors]
        importances = [f.get("importance", 0) for f in factors]
        validated_colors = ["#3498db" if f.get("validated", False) else "#95a5a6" for f in factors]
        
        fig.add_trace(
            go.Bar(x=factor_names, y=importances, marker_color=validated_colors, name="Importance"),
            row=1, col=2
        )
    
    # Token usage pie
    if nodes:
        token_data = [(n.get("name", "unknown"), n.get("tokens", 0)) for n in nodes if n.get("tokens", 0) > 0]
        if token_data:
            names, tokens = zip(*token_data)
            fig.add_trace(
                go.Pie(labels=names, values=tokens, name="Tokens"),
                row=2, col=1
            )
    
    # Success rate indicator
    success_rate = session_data.get("success_rate", 1.0)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=success_rate * 100,
            title={"text": "Success Rate"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2ecc71" if success_rate > 0.8 else "#f39c12"},
                "steps": [
                    {"range": [0, 50], "color": "#e74c3c"},
                    {"range": [50, 80], "color": "#f39c12"},
                    {"range": [80, 100], "color": "#2ecc71"}
                ]
            }
        ),
        row=2, col=2
    )
    
    # Layout
    fig.update_layout(
        title=f"Session Dashboard: {session_id}",
        showlegend=False,
        height=700,
        template="plotly_dark"
    )
    
    # Save
    filepath = output_path / f"dashboard_{session_id}.html"
    fig.write_html(str(filepath), include_plotlyjs="cdn")
    
    print(f"[Dashboard] Created dashboard: {filepath}")
    return filepath


def _create_simple_dashboard(session_data: Dict[str, Any], output_path: Path = None) -> Path:
    """Create a simple HTML dashboard without Plotly."""
    output_path = output_path or Path("outputs/dashboards")
    output_path.mkdir(parents=True, exist_ok=True)
    
    session_id = session_data.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Session Dashboard: {session_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #1a1a2e; color: #eee; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #3498db; }}
        .card {{ background: #16213e; border-radius: 8px; padding: 20px; margin: 10px 0; }}
        .metric {{ font-size: 2em; color: #2ecc71; }}
        .label {{ color: #888; font-size: 0.9em; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ color: #3498db; }}
        .success {{ color: #2ecc71; }}
        .error {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏎️ Session Dashboard</h1>
        <p class="label">Session ID: {session_id}</p>
        
        <div class="grid">
            <div class="card">
                <div class="label">Total Duration</div>
                <div class="metric">{session_data.get('total_duration_ms', 0):.0f}ms</div>
            </div>
            <div class="card">
                <div class="label">Success Rate</div>
                <div class="metric">{session_data.get('success_rate', 1.0):.1%}</div>
            </div>
            <div class="card">
                <div class="label">Total Tokens</div>
                <div class="metric">{session_data.get('total_tokens', 0):,}</div>
            </div>
            <div class="card">
                <div class="label">Nodes Executed</div>
                <div class="metric">{session_data.get('node_count', 0)}</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Node Execution</h2>
            <table>
                <tr><th>Node</th><th>Duration</th><th>Status</th><th>Tokens</th></tr>
                {''.join(f'''<tr>
                    <td>{n.get('name', 'unknown')}</td>
                    <td>{n.get('duration_ms', 0):.0f}ms</td>
                    <td class="{'success' if n.get('success', True) else 'error'}">
                        {'✓' if n.get('success', True) else '✗'}
                    </td>
                    <td>{n.get('tokens', 0)}</td>
                </tr>''' for n in session_data.get('nodes', []))}
            </table>
        </div>
        
        <div class="card">
            <h2>Validated Factors</h2>
            <table>
                <tr><th>Factor</th><th>Importance</th><th>Validated</th><th>Method</th></tr>
                {''.join(f'''<tr>
                    <td>{f.get('name', 'unknown')}</td>
                    <td>{f.get('importance', 0):.2f}</td>
                    <td class="{'success' if f.get('validated', False) else 'error'}">
                        {'✓' if f.get('validated', False) else '✗'}
                    </td>
                    <td>{f.get('method', '-')}</td>
                </tr>''' for f in session_data.get('factors', []))}
            </table>
        </div>
        
        <p class="label">Generated: {datetime.now().isoformat()}</p>
    </div>
</body>
</html>"""
    
    filepath = output_path / f"dashboard_{session_id}.html"
    with open(filepath, "w") as f:
        f.write(html)
    
    print(f"[Dashboard] Created simple dashboard: {filepath}")
    return filepath


def create_comparison_dashboard(
    sessions: List[Dict[str, Any]],
    output_path: Path = None
) -> Path:
    """Create a dashboard comparing multiple sessions."""
    output_path = output_path or Path("outputs/dashboards")
    output_path.mkdir(parents=True, exist_ok=True)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Session Comparison</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #1a1a2e; color: #eee; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #3498db; }
        table { width: 100%; border-collapse: collapse; background: #16213e; border-radius: 8px; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #333; }
        th { color: #3498db; background: #0f3460; }
        tr:hover { background: #1f4068; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Session Comparison</h1>
        <table>
            <tr>
                <th>Session ID</th>
                <th>Query</th>
                <th>Depth</th>
                <th>Duration</th>
                <th>Success Rate</th>
                <th>Tokens</th>
                <th>Factors</th>
            </tr>"""
    
    for s in sessions:
        html += f"""
            <tr>
                <td>{s.get('session_id', 'unknown')}</td>
                <td>{s.get('query', 'N/A')[:50]}...</td>
                <td>{s.get('depth', 'basic')}</td>
                <td>{s.get('total_duration_ms', 0):.0f}ms</td>
                <td>{s.get('success_rate', 1.0):.1%}</td>
                <td>{s.get('total_tokens', 0):,}</td>
                <td>{s.get('factor_validation_rate', 0):.1%}</td>
            </tr>"""
    
    html += """
        </table>
    </div>
</body>
</html>"""
    
    filepath = output_path / "session_comparison.html"
    with open(filepath, "w") as f:
        f.write(html)
    
    print(f"[Dashboard] Created comparison dashboard: {filepath}")
    return filepath
