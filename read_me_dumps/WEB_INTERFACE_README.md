# F1 Analysis Agent - Web Interface

A modern, full-stack web application for AI-powered Formula 1 race analysis with real-time agent execution monitoring.

## 🏗️ Architecture

### Backend (Flask + SocketIO)
- **REST API** for analysis management
- **WebSocket** for real-time progress updates
- **File serving** for reports and visualizations
- **Session management** for concurrent analyses

### Frontend (React + Material-UI)
- **Query input interface** with example queries
- **Real-time progress monitor** showing agent execution
- **Results viewer** with tabbed interface for reports, visualizations, and data
- **Responsive design** with F1-themed styling

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ with virtual environment `f1env_new`
- Node.js 18+ and npm
- All F1 Analysis Agent dependencies installed

### Setup

1. **Install Backend Dependencies**
```bash
pip install -r requirements-web.txt
```

2. **Setup Frontend**
```bash
chmod +x setup_frontend.sh
./setup_frontend.sh
```

### Development Mode

**Option 1: Separate Servers (Recommended for Development)**

Terminal 1 - Backend:
```bash
source f1env_new/bin/activate
python backend/app.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm start
```

Access at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

**Option 2: Production Mode**

Build frontend and serve from Flask:
```bash
chmod +x start_web.sh
./start_web.sh
```

Access at: http://localhost:5000

## 📚 API Documentation

### REST Endpoints

#### `GET /api/health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-20T10:30:00"
}
```

#### `GET /api/config`
Get current configuration

**Response:**
```json
{
  "llm_model": "qwen/qwen3-32b",
  "token_limit": 50000,
  "default_analysis_depth": "basic",
  "api_enabled": true
}
```

#### `POST /api/analyze`
Start a new analysis

**Request Body:**
```json
{
  "query": "Compare Verstappen and Hamilton in 2024 Bahrain GP",
  "depth": "deep"
}
```

**Response:**
```json
{
  "session_id": "session_1710926400_0",
  "status": "started",
  "message": "Analysis started successfully"
}
```

#### `GET /api/session/<session_id>`
Get session status and results

**Response:**
```json
{
  "status": "completed",
  "query": "Compare Verstappen and Hamilton...",
  "depth": "deep",
  "start_time": "2024-03-20T10:30:00",
  "end_time": "2024-03-20T10:32:00",
  "progress": [...],
  "result": {
    "report_path": "outputs/race_report.md",
    "deep_report_path": "outputs/deep_analysis_summary.md",
    "visualizations": [],
    "token_usage": {...}
  },
  "error": null
}
```

#### `GET /api/outputs`
List all available output files

**Response:**
```json
{
  "reports": [
    {
      "name": "race_report.md",
      "path": "outputs/race_report.md",
      "modified": "2024-03-20T10:32:00"
    }
  ],
  "visualizations": [
    {
      "name": "lap_time_evolution.png",
      "path": "outputs/visualizations/lap_time_evolution.png",
      "modified": "2024-03-20T10:32:00"
    }
  ],
  "data": [...]
}
```

#### `GET /api/file/<filepath>`
Get a specific file (markdown, image, or parquet)

### WebSocket Events

#### Client → Server

**`connect`**
Establish WebSocket connection

**`subscribe`**
Subscribe to session progress updates
```json
{
  "session_id": "session_1710926400_0"
}
```

#### Server → Client

**`connected`**
Connection established
```json
{
  "message": "Connected to F1 Analysis Agent"
}
```

**`progress`**
Real-time progress update
```json
{
  "session_id": "session_1710926400_0",
  "timestamp": "2024-03-20T10:30:15",
  "status": "running",
  "message": "Executing: code_writer",
  "node": "code_writer"
}
```

## 🎨 Frontend Components

### QueryInput
- Text input for natural language queries
- Depth selector (basic/deep/story)
- Example query chips
- Form validation

### ProgressMonitor
- Real-time stepper showing agent execution
- Status indicators with icons
- Detailed logs for each node
- Session ID display

### ResultsViewer
- **Analysis Report Tab**: Rendered markdown report
- **Deep Analysis Tab**: Advanced telemetry analysis (if available)
- **Visualizations Tab**: Grid of charts and plots
- **Data & Metrics Tab**: Token usage and file paths

## 🔧 Configuration

### Backend Configuration
Edit [config.yaml](config.yaml):
```yaml
llm:
  model: "qwen/qwen3-32b"
  temperature: 0.1

tokens:
  limit: 50000

analysis:
  default_depth: "basic"
  enable_api: true
```

### Frontend Configuration
Edit [frontend/package.json](frontend/package.json):
```json
{
  "proxy": "http://localhost:5000"
}
```

## 🐛 Troubleshooting

### Backend Issues

**"Module not found" errors:**
```bash
pip install -r requirements-web.txt
```

**Port 5000 already in use:**
Edit `backend/app.py`:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

**CORS errors:**
Check `flask-cors` is installed and configured in `backend/app.py`

### Frontend Issues

**"Cannot find module" errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Proxy not working:**
Ensure backend is running and `proxy` is set in `package.json`

**Build errors:**
```bash
cd frontend
npm run build
```

## 📁 Project Structure

```
AI_Final_F1_Project_Agentic/
├── backend/
│   └── app.py                 # Flask server with SocketIO
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── QueryInput.js       # Query input form
│   │   │   ├── ProgressMonitor.js  # Real-time progress display
│   │   │   └── ResultsViewer.js    # Results visualization
│   │   ├── App.js              # Main application component
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
├── src/
│   ├── graph.py               # LangGraph workflow
│   ├── nodes/                 # Agent nodes
│   └── tools/
│       └── column_inspector.py # Column lookup tool (NEW!)
├── requirements-web.txt       # Web interface dependencies
├── setup_frontend.sh          # Frontend setup script
├── start_web.sh              # Production startup script
└── WEB_INTERFACE_README.md   # This file
```

## 🆕 New Features

### Column Inspector Tool
Added intelligent column lookup for debugging:
- **Auto-discovers** available columns in all datasets
- **Searches** for missing columns with fuzzy matching
- **Identifies** potential join keys
- **Integrated** into code_debugger for automatic error fixing

Usage in code_debugger:
```python
from src.tools.column_inspector import format_column_info_for_llm, search_column

# Get all column information
column_info = format_column_info_for_llm(data_paths)

# Search for a specific column
results = search_column('driver', data_paths)
```

### Bug Fixes
- ✅ Fixed `num_stops` and `total_pit_time` column merge error
- ✅ Added explicit guidance for pit stop analysis pattern
- ✅ Improved error messages in code_writer

## 🎯 Usage Examples

### Basic Analysis
```
Query: "What was the fastest lap in the 2024 Bahrain GP?"
Depth: Basic
Expected: Race report with fastest lap information
```

### Deep Analysis
```
Query: "Compare Verstappen and Hamilton's performance in 2024 Bahrain"
Depth: Deep
Expected: Full telemetry comparison with visualizations
```

### Story Mode
```
Query: "Analyze the battle between Red Bull and Ferrari in 2024 Bahrain"
Depth: Story
Expected: Narrative analysis with strategic insights
```

## 🔐 Security Considerations

- ✅ Input validation on query and depth parameters
- ✅ Path traversal protection on file access
- ✅ CORS configured for localhost development
- ⚠️ **Production deployment requires**:
  - Authentication/authorization
  - Rate limiting
  - HTTPS/WSS
  - Environment-based configuration

## 📊 Performance

- **Average analysis time**: 30-90 seconds (depth-dependent)
- **Concurrent sessions**: Supported via threading
- **Token efficiency**: Monitored and displayed in results
- **Caching**: Dataset caching in `data/cache/`

## 🤝 Contributing

The web interface is designed to be modular and extensible:

1. **Adding new API endpoints**: Edit `backend/app.py`
2. **Adding new components**: Create in `frontend/src/components/`
3. **Styling changes**: Edit component styles or `App.css`
4. **Backend logic**: Integrate with existing `src/` modules

## 📝 License

Same as the main F1 Analysis Agent project.

## 🆘 Support

For issues specific to the web interface:
1. Check this documentation
2. Review browser console and Flask logs
3. Verify all dependencies are installed
4. Check that both backend and frontend are running

---

**Built with ❤️ for F1 fans and data enthusiasts**
