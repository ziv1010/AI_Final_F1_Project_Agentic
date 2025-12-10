# F1 Analysis Agent - Quick Start Guide

## 🎯 What's New

### 1. Bug Fixes
- ✅ Fixed column merge error in `code_writer.py` (num_stops/total_pit_time issue)
- ✅ Added explicit pit stop analysis pattern to prevent future errors
- ✅ Improved error handling and debugging capabilities

### 2. Column Inspector Tool
NEW intelligent debugging tool that helps the agent when it gets stuck:
- Automatically discovers all available columns in datasets
- Searches for missing columns with fuzzy matching
- Identifies potential join keys between tables
- Integrated into the code debugger for automatic fixes

### 3. Full Web Interface
Brand new full-stack web application:
- **Backend**: Flask REST API + WebSocket for real-time updates
- **Frontend**: React + Material-UI with F1-themed design
- **Features**:
  - Natural language query input
  - Real-time agent execution monitoring
  - Interactive results viewer with tabs
  - Visualization gallery
  - Token usage tracking

## 🚀 Installation & Setup

### Option 1: Command Line (Original)

```bash
# Make sure you're in the project directory
cd /Users/ziv/Desktop/AI_Final_Project_F1/AI_Final_F1_Project_Agentic

# Activate virtual environment
source f1env_new/bin/activate

# Run an analysis
python -m src.main
```

### Option 2: Web Interface (NEW!)

**Step 1: Install Web Dependencies**
```bash
pip install -r requirements-web.txt
```

**Step 2: Setup Frontend**
```bash
./setup_frontend.sh
```

**Step 3: Start the Application**

**Development Mode** (Recommended for testing):
```bash
# Terminal 1 - Backend
source f1env_new/bin/activate
python backend/app.py

# Terminal 2 - Frontend
cd frontend
npm start
```

Then open http://localhost:3000

**Production Mode**:
```bash
./start_web.sh
```

Then open http://localhost:5000

## 📝 How to Use

### Command Line

Run the main script and follow the prompts:
```bash
python -m src.main
```

Example queries:
- "Compare Verstappen and Hamilton in the 2024 Bahrain GP"
- "Analyze tire strategy for Mercedes in 2024 Australian GP"
- "What was the fastest lap in 2024 Saudi Arabian GP?"

### Web Interface

1. **Enter your query** in the text box (or click an example)
2. **Select analysis depth**:
   - `Basic`: Dataset analysis only (fastest)
   - `Deep`: Includes API data and telemetry
   - `Story`: Full narrative with strategic insights
3. **Click "Analyze"** and watch real-time progress
4. **View results** in tabs:
   - Analysis Report
   - Deep Analysis (if depth=deep/story)
   - Visualizations
   - Data & Metrics

## 🔍 Testing the Fixes

### Test the Column Merge Fix

Run this query to verify the pit stop analysis works:
```
"Compare pit strategies for Verstappen and Hamilton in 2024 Bahrain GP"
```

**Expected behavior**:
- ✅ No `KeyError: "Column(s) ['num_stops', 'total_pit_time'] do not exist"`
- ✅ Successful pit stop count and timing analysis
- ✅ Visualizations showing pit stop strategies

### Test the Column Inspector

The column inspector automatically activates when there's a column-related error. To see it in action:

1. The agent encounters a column error
2. Column inspector searches all datasets
3. Finds similar columns and suggests corrections
4. Code debugger uses this info to fix the code

You'll see output like:
```
=== COLUMN INSPECTOR RESULTS ===
AVAILABLE COLUMNS IN DATASETS
================================
pits (57 rows):
  • raceId                        int64           (0.0% null)
  • driverId                      int64           (0.0% null)
  • stop                          int64           (0.0% null) [sample: 1]
  • lap                           int64           (0.0% null)
  ...
```

## 📊 What to Expect

### Successful Analysis

**Command Line**:
- Progress updates for each node
- Race report saved to `outputs/race_report.md`
- Visualizations in `outputs/visualizations/`
- Deep analysis summary (if depth=deep/story)

**Web Interface**:
- Real-time progress stepper
- Interactive report viewer
- Image gallery with download buttons
- Token usage statistics

### If Something Goes Wrong

**Error Handling**:
1. First retry: Code writer tries to fix automatically
2. Retries 2-4: Code debugger analyzes and fixes intelligently
3. After 5 attempts: Returns error details

**Column errors** are now handled automatically:
- Debugger uses column inspector to find correct columns
- Suggests fixes based on actual schema
- Shows available columns and join keys

## 🎨 Web Interface Features

### Query Input
- Large text area for natural language queries
- Example query chips for quick start
- Analysis depth selector with descriptions
- Real-time validation

### Progress Monitor
- Step-by-step visualization of agent execution
- Status icons (✓ completed, ⏳ running, ✗ error)
- Detailed logs with timestamps
- Session ID tracking

### Results Viewer
- **Report Tab**: Beautiful markdown rendering
- **Deep Analysis Tab**: Telemetry insights
- **Visualizations Tab**: Interactive image gallery
- **Metrics Tab**: Token usage and file paths

## 🐛 Troubleshooting

### "Column not found" errors
- ✅ **FIXED!** The column inspector now handles these automatically
- The debugger will search for the correct column and fix the code

### Web interface won't start
```bash
# Backend
pip install -r requirements-web.txt

# Frontend
cd frontend
rm -rf node_modules
npm install
```

### Port conflicts
Edit `backend/app.py` line 310:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)  # Change port
```

### Frontend build errors
```bash
cd frontend
npm run build
```

## 📁 Output Files

All analysis outputs are saved to `outputs/`:
- `race_report.md` - Basic analysis report
- `deep_analysis_summary.md` - Advanced analysis (if depth=deep/story)
- `visualizations/` - Charts and plots
- `deep_analysis_visualizations/` - Telemetry visualizations
- `analysis_metrics.parquet` - Raw data

## 🎯 Example Workflows

### Workflow 1: Quick Race Summary
```
Query: "Summarize the 2024 Bahrain GP"
Depth: Basic
Time: ~30 seconds
Output: Race report with key statistics
```

### Workflow 2: Driver Comparison
```
Query: "Compare Verstappen and Hamilton's lap times in 2024 Bahrain"
Depth: Deep
Time: ~60 seconds
Output: Report + telemetry visualizations
```

### Workflow 3: Strategic Analysis
```
Query: "Analyze tire strategy impact on race outcome in 2024 Bahrain"
Depth: Story
Time: ~90 seconds
Output: Full narrative with strategic insights
```

## 📚 Documentation

- **Main README**: [README.md](README.md)
- **Web Interface**: [WEB_INTERFACE_README.md](WEB_INTERFACE_README.md)
- **Configuration**: [config.yaml](config.yaml)
- **Position Reporting Fix**: [POSITION_REPORTING_FIX.md](POSITION_REPORTING_FIX.md)

## 🆘 Need Help?

1. Check the logs in console/terminal
2. Review [WEB_INTERFACE_README.md](WEB_INTERFACE_README.md) for API docs
3. Look at `outputs/analysis_log.txt` for detailed execution logs
4. Check that all dependencies are installed
5. Verify your API keys are configured (if using OpenF1)

## 🎉 What's Next?

Now that everything is fixed and enhanced:
1. Try the example queries
2. Experiment with different analysis depths
3. Explore the web interface
4. Check out the column inspector in action
5. Review the improved visualizations

Enjoy analyzing F1 races! 🏁
