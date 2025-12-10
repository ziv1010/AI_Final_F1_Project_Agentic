"""
F1 Analysis Agent - Backend API Server
Provides REST API and WebSocket support for real-time agent execution
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
from pathlib import Path
import matplotlib
import json
import threading
import time
from datetime import datetime

# Force headless backend for matplotlib to avoid GUI creation in worker threads
matplotlib.use("Agg")

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph import get_graph_for_depth
from src.state import WeekendState
from src.config import CONFIG

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store active analysis sessions
active_sessions = {}
# Cache completed results by query/depth
completed_cache = {}

@app.route('/')
def serve_frontend():
    """Serve the React frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'llm_model': CONFIG['llm']['model'],
        'token_limit': CONFIG['tokens']['limit'],
        'default_analysis_depth': CONFIG['analysis']['default_depth'],
        'api_enabled': CONFIG['analysis']['enable_api']
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Start a new analysis
    Accepts JSON with:
    - query: str (the natural language query)
    - depth: str (optional, 'basic'/'deep'/'story', defaults to config setting)
    """
    data = request.json
    query = data.get('query')
    depth = data.get('depth', CONFIG['analysis']['default_depth'])
    cache_key = f"{(query or '').strip().lower()}::{depth}"

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    if depth not in ['basic', 'deep', 'story']:
        return jsonify({'error': 'Invalid depth. Must be basic, deep, or story'}), 400

    # If we already ran this exact query/depth and files are still present, return cached result
    if cache_key in completed_cache:
        cached = completed_cache[cache_key]
        if files_exist(cached.get('result')):
            session_id = cached['session_id']
            active_sessions[session_id] = {
                'status': 'completed',
                'query': query,
                'depth': depth,
                'start_time': cached.get('start_time'),
                'end_time': cached.get('end_time'),
                'progress': cached.get('progress', []),
                'result': cached['result'],
                'error': None,
            }
            return jsonify({
                'session_id': session_id,
                'status': 'completed',
                'message': 'Returned cached analysis results',
                'cached': True,
            })
        else:
            # Cached metadata exists but files are missing; drop cache and rerun
            completed_cache.pop(cache_key, None)

    # Generate session ID
    session_id = f"session_{int(time.time())}_{len(active_sessions)}"

    # Initialize session
    active_sessions[session_id] = {
        'status': 'running',
        'query': query,
        'depth': depth,
        'start_time': datetime.now().isoformat(),
        'progress': [],
        'result': None,
        'error': None
    }

    # Run analysis in background thread
    thread = threading.Thread(
        target=run_analysis_async,
        args=(session_id, query, depth)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'session_id': session_id,
        'status': 'started',
        'message': 'Analysis started successfully'
    })

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """Get status of an analysis session"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = active_sessions[session_id]
    return jsonify(session)

@app.route('/api/outputs', methods=['GET'])
def list_outputs():
    """List all available analysis outputs"""
    base_dir = Path(__file__).parent.parent.resolve()
    outputs_dir = (base_dir / CONFIG['data']['outputs_path']).resolve()
    alt_vis_dir = (base_dir / "analysis_vis").resolve()

    outputs = {
        'reports': [],
        'visualizations': [],
        'data': []
    }

    if outputs_dir.exists():
        # List markdown reports
        for md_file in outputs_dir.glob('*.md'):
            outputs['reports'].append({
                'name': md_file.name,
                'path': str(md_file.relative_to(base_dir)),
                'modified': datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
            })

        # List visualizations
        vis_dir = outputs_dir / 'visualizations'
        if vis_dir.exists():
            for img_file in vis_dir.glob('*.png'):
                outputs['visualizations'].append({
                    'name': img_file.name,
                    'path': str(img_file.relative_to(base_dir)),
                    'modified': datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                })

        # List deep analysis visualizations
        deep_vis_dir = outputs_dir / 'deep_analysis_visualizations'
        if deep_vis_dir.exists():
            for img_file in deep_vis_dir.glob('*.png'):
                outputs['visualizations'].append({
                    'name': img_file.name,
                    'path': str(img_file.relative_to(base_dir)),
                    'modified': datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                })

        # Visualizations stored in analysis_vis
        if alt_vis_dir.exists():
            for img_file in alt_vis_dir.glob('*.png'):
                outputs['visualizations'].append({
                    'name': img_file.name,
                    'path': str(img_file.relative_to(base_dir)),
                    'modified': datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                })

        # List data files
        for data_file in outputs_dir.glob('*.parquet'):
            outputs['data'].append({
                'name': data_file.name,
                'path': str(data_file.relative_to(base_dir)),
                'modified': datetime.fromtimestamp(data_file.stat().st_mtime).isoformat()
            })

    # Deduplicate visualizations by path
    if outputs['visualizations']:
        unique_vis = {}
        for viz in outputs['visualizations']:
            unique_vis[viz['path']] = viz
        outputs['visualizations'] = list(unique_vis.values())

    return jsonify(outputs)

@app.route('/api/file/<path:filepath>', methods=['GET'])
def get_file(filepath):
    """Get a specific output file"""
    base_dir = Path(__file__).parent.parent.resolve()
    file_path = Path(filepath)
    if not file_path.is_absolute():
        file_path = (base_dir / file_path).resolve()

    # Security: prevent directory traversal
    try:
        file_path.relative_to(base_dir)
    except ValueError:
        return jsonify({'error': 'Invalid file path'}), 400

    if file_path.suffix == '.md':
        # Return markdown as text
        if file_path.exists():
            return jsonify({
                'content': file_path.read_text(),
                'type': 'markdown'
            })
    elif file_path.suffix == '.png':
        # Return image file directly
        if file_path.exists():
            return send_from_directory(str(file_path.parent), file_path.name)
        return jsonify({'error': 'File not found'}), 404
    elif file_path.suffix == '.parquet':
        # Return parquet metadata
        import pandas as pd
        try:
            df = pd.read_parquet(file_path)
            return jsonify({
                'shape': df.shape,
                'columns': list(df.columns),
                'head': df.head(10).to_dict(orient='records'),
                'type': 'data'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File not found'}), 404


def files_exist(result):
    """Check that referenced report files are present on disk."""
    if not result:
        return False
    report_ok = Path(result.get('report_path', '')).exists()
    deep_ok = True
    if result.get('deep_report_path'):
        deep_ok = Path(result['deep_report_path']).exists()
    return report_ok and deep_ok

def run_analysis_async(session_id, query, depth):
    """Run analysis in background thread with progress updates"""
    print(f"[Analysis Thread] Starting analysis for session {session_id}")
    print(f"[Analysis Thread] Query: {query}")
    print(f"[Analysis Thread] Depth: {depth}")
    cache_key = f"{(query or '').strip().lower()}::{depth}"

    try:
        # Create graph
        print(f"[Analysis Thread] Creating graph for depth: {depth}")
        graph = get_graph_for_depth(depth)

        # Initial state
        initial_state = {
            "user_query": query,  # Changed from "query" to "user_query" to match graph expectations
            "analysis_depth": depth,
            "weekend_spec": None,
            "errors": [],
            "code_snippets": [],
            "figures": [],
            "analysis_outputs": {}
        }

        # Update progress
        print(f"[Analysis Thread] Initialized, starting execution...")
        emit_progress(session_id, 'initialized', 'Analysis initialized')

        # Stream graph execution
        for step_output in graph.stream(initial_state):
            node_name = list(step_output.keys())[0]
            state = step_output[node_name]

            # Emit progress update
            progress_msg = f"Executing: {node_name}"
            print(f"[Analysis Thread] {progress_msg}")
            emit_progress(session_id, 'running', progress_msg, node_name)

            # Check for errors
            if state.get('errors'):
                latest_error = state['errors'][-1]
                print(f"[Analysis Thread] Error in {node_name}: {latest_error}")
                emit_progress(session_id, 'error', f"Error in {node_name}: {latest_error}", node_name)

        # Get final state
        final_state = state

        # Check if successful
        if final_state.get('errors'):
            print(f"[Analysis Thread] Analysis failed with errors: {final_state['errors'][-1]}")
            active_sessions[session_id].update({
                'status': 'failed',
                'error': final_state['errors'][-1],
                'end_time': datetime.now().isoformat()
            })
            emit_progress(session_id, 'failed', 'Analysis failed')
        else:
            # Extract results
            print(f"[Analysis Thread] Analysis completed successfully!")
            outputs_dir = Path(CONFIG['data']['outputs_path'])
            result = {
                'report_path': str(outputs_dir / 'race_report.md'),
                'deep_report_path': str(outputs_dir / 'deep_analysis_summary.md') if depth in ['deep', 'story'] else None,
                'visualizations': [],
                'token_usage': final_state.get('analysis_outputs', {}).get('token_usage', {})
            }

            active_sessions[session_id].update({
                'status': 'completed',
                'result': result,
                'end_time': datetime.now().isoformat()
            })
            emit_progress(session_id, 'completed', 'Analysis completed successfully')
            print(f"[Analysis Thread] Session {session_id} marked as completed")

            # Save to cache for future identical queries
            completed_cache[cache_key] = {
                'session_id': session_id,
                'result': result,
                'start_time': active_sessions[session_id].get('start_time'),
                'end_time': active_sessions[session_id].get('end_time'),
                'progress': active_sessions[session_id].get('progress', []),
            }

    except Exception as e:
        print(f"[Analysis Thread] Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        active_sessions[session_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.now().isoformat()
        })
        emit_progress(session_id, 'failed', f'Analysis failed: {str(e)}')

def emit_progress(session_id, status, message, node=None):
    """Emit progress update via WebSocket"""
    progress_item = {
        'timestamp': datetime.now().isoformat(),
        'status': status,
        'message': message,
        'node': node
    }

    # Add to session progress
    if session_id in active_sessions:
        active_sessions[session_id]['progress'].append(progress_item)

    # Emit via WebSocket
    socketio.emit('progress', {
        'session_id': session_id,
        **progress_item
    }, namespace='/')

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to F1 Analysis Agent'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f'Client disconnected: {request.sid}')

@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to a session's progress updates"""
    session_id = data.get('session_id')
    if session_id and session_id in active_sessions:
        emit('subscribed', {'session_id': session_id})
    else:
        emit('error', {'message': 'Invalid session ID'})

if __name__ == '__main__':
    print("Starting F1 Analysis Agent Backend...")
    print(f"Backend API: http://localhost:5010")
    print(f"WebSocket: ws://localhost:5010")
    socketio.run(app, debug=True, host='0.0.0.0', port=5010)
