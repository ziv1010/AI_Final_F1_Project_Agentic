# F1 Weekend Strategy Analyst

A fully agentic AI system that analyzes F1 race weekends using LangGraph, LangChain, and Groq.

## 🚀 **NEW: Intelligent Factor Analysis**

The system now **thinks autonomously** about what factors matter for each query and adapts its analysis accordingly!

**[Read the full improvements documentation →](IMPROVEMENTS_SUMMARY.md)**

## Features

- **🧠 Intelligent Factor Analysis**: Automatically identifies what performance factors matter (tires, weather, strategy, pace)
- **Natural Language Queries**: Ask questions like "Why did Mercedes struggle at Monaco 2023?"
- **Autonomous Analysis**: The agent plans its own comprehensive, multi-dimensional analysis
- **Smart Data Fetching**: Only fetches relevant data sources based on query context
- **Data Integration**: Combines Kaggle F1 datasets with OpenF1 API (weather, telemetry, team radio)
- **Advanced Visualizations**: Stint-by-stint analysis, strategy timelines, pace evolution, heatmaps
- **Evidence-Based Reporting**: Generates reports explaining WHY results occurred, not just WHAT happened

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Data Setup**:
   - Download the [Formula 1 World Championship (1950-2024)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) dataset from Kaggle.
   - Place the CSV files (races.csv, results.csv, lap_times.csv, pit_stops.csv, drivers.csv, constructors.csv, circuits.csv) in `data/raw/`.

3. **Environment Variables**:
   - Set your Groq API key:
     ```bash
     export GROQ_API_KEY="your_api_key_here"
     ```

## Usage

### Basic Analysis (Fast, intelligent dataset analysis)
```bash
python main.py "Compare Ferrari and McLaren at Qatar 2023"
```

### Deep Analysis (Includes OpenF1 API data: weather, telemetry, team radio)
```bash
python main.py "Why did Mercedes struggle at Monaco 2023?" --deep
```

### Story Mode (Full narrative with comprehensive insights)
```bash
python main.py "Tell me the story of the 2023 Las Vegas GP" --story
```

### Interactive Mode (Prompts for deeper analysis after basic results)
```bash
python main.py "Compare Verstappen and Hamilton at Bahrain 2023" --interactive
```

## Architecture

The system uses an intelligent graph of agents:

1. **Query Interpreter**: Identifies the race, drivers, and teams
2. **🧠 Factor Analyzer** (NEW!): Intelligently determines what factors matter and what data to fetch
3. **Data Loader**: Prepares relevant dataset files
4. **Analysis Planner**: Creates comprehensive, multi-dimensional analysis plan
5. **Code Writer**: Generates smart Python code with stint-by-stint analysis
6. **Code Debugger**: Fixes errors automatically if code fails
7. **Report Generator**: Creates basic analysis report
8. **Deep Analysis Fetcher**: Intelligently fetches OpenF1 API data (weather, telemetry, radio)
9. **Storyteller**: Synthesizes comprehensive narrative (story mode)

**[See the full workflow diagram →](INTELLIGENT_WORKFLOW.md)**

## What Makes It Intelligent?

### Factor-Driven Analysis
Instead of simple keyword matching, the system uses LLM reasoning to:
- Identify key performance factors (tire strategy, weather, car setup, etc.)
- Determine what data sources are actually needed
- Plan multi-dimensional comparisons
- Formulate hypotheses to test
- Explain WHY results occurred, not just WHAT happened

### Smart Data Fetching
The system only fetches API data that's relevant to your query:
- Team radio communications (strategy discussions, driver feedback)
- GPS location data (racing lines, overtake analysis)
- Weather conditions (temperature, rain impact)
- Telemetry data (speed, throttle, brake, DRS)
- Race control messages (incidents, flags, safety car)

### Advanced Analysis
- **Stint-by-stint comparison**: Not just overall averages
- **Tire degradation tracking**: Pace evolution within each stint
- **Strategy timeline visualization**: Who pitted when, on what compounds
- **Pace delta heatmaps**: Driver vs driver, lap by lap
- **Time-based patterns**: How performance evolved during the race

### Example Comparison

**Before**: "Verstappen won by 25 seconds"

**After**: "Verstappen won due to better tire management (0.05s/lap degradation vs Hamilton's 0.08s/lap), optimal pit timing (lap 18 vs lap 16), and superior pace in the final stint (+0.3s/lap). Team radio on lap 35 shows Hamilton reporting tire issues. Weather data shows track temperature increased 5°C in final stint, affecting tire performance."

## Outputs

Check the `outputs/` directory for:
- `race_report.md`: Basic analysis report with findings
- `narrative_report.md`: Story mode comprehensive narrative (if --story)
- `analysis_metrics.parquet`: Detailed metrics data
- `visualizations/`: Multiple plots showing:
  - Lap time evolution (colored by tire compound)
  - Strategy timelines
  - Pace delta heatmaps
  - Stint performance comparisons
  - Position changes over time

## Documentation

- **[Improvements Summary](IMPROVEMENTS_SUMMARY.md)**: Quick overview of new features
- **[Intelligent Workflow](INTELLIGENT_WORKFLOW.md)**: Visual workflow diagram
- **[Full Documentation](INTELLIGENT_ANALYSIS_IMPROVEMENTS.md)**: Complete technical details
