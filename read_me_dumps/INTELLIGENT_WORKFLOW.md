# Intelligent F1 Analysis Workflow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER QUERY                                     │
│  "Why did Mercedes struggle at Monaco 2023?"                            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      QUERY INTERPRETER                                   │
│  • Identifies race: Monaco 2023                                         │
│  • Extracts focus: Mercedes team                                        │
│  • Maps to weekend_spec                                                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   🧠 FACTOR ANALYZER (NEW!)                              │
│                                                                          │
│  Intelligent Analysis:                                                  │
│  ✓ Primary Question: "What caused poor Mercedes performance?"           │
│  ✓ Key Factors:                                                         │
│    - Tire strategy                                                      │
│    - Track characteristics (low speed, high downforce)                  │
│    - Car setup suitability                                              │
│    - Pace evolution during race                                         │
│                                                                          │
│  ✓ Data Sources Needed:                                                 │
│    lap_times: ✓  tire_stints: ✓  weather: ✓  telemetry: ✓             │
│    pit_stops: ✓  race_control: ✓  radio: ✓  positions: ✓              │
│                                                                          │
│  ✓ Comparisons:                                                         │
│    - Mercedes vs Red Bull (lap pace, tire deg)                          │
│    - Mercedes vs Ferrari (strategy, pit timing)                         │
│    - Stint 1 vs Stint 2 (performance evolution)                         │
│                                                                          │
│  ✓ Hypotheses:                                                          │
│    - Mercedes had higher tire degradation                               │
│    - Car setup didn't suit track characteristics                        │
│    - Pit strategy was sub-optimal                                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LOADER                                       │
│  • Loads Kaggle datasets for Monaco 2023                               │
│  • Extracts: results, laps, drivers, constructors, pits                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   📊 ANALYSIS PLANNER (ENHANCED!)                        │
│                                                                          │
│  Uses Factor Analysis to create SMART plan:                             │
│                                                                          │
│  1. FACTORS & HYPOTHESES                                                │
│     - Test tire degradation hypothesis                                  │
│     - Compare setup/balance indicators                                  │
│                                                                          │
│  2. FILES TO LOAD                                                       │
│     - results, laps, drivers, constructors, pits                        │
│                                                                          │
│  3. TIME-BASED ANALYSIS                                                 │
│     - Lap-by-lap pace evolution                                         │
│     - Stint performance degradation                                     │
│     - Pit window timing                                                 │
│                                                                          │
│  4. COMPARATIVE METRICS                                                 │
│     - Mercedes vs competitors (pace delta by lap)                       │
│     - Tire degradation rates (slope within stints)                      │
│     - Strategy effectiveness (pit timing impact)                        │
│                                                                          │
│  5. VISUALIZATIONS                                                      │
│     - Lap time evolution (colored by tire compound)                     │
│     - Strategy timeline (who pitted when)                               │
│     - Pace delta heatmap (Mercedes vs others)                           │
│     - Tire degradation comparison (stint analysis)                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       PLAN REVIEWER                                      │
│  • Validates plan completeness                                          │
│  • Ensures factor analysis context is incorporated                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   💻 CODE WRITER (SMARTER!)                              │
│                                                                          │
│  Generates comprehensive Python code with:                              │
│                                                                          │
│  • Data loading & cleaning                                              │
│  • Stint-by-stint lap time comparison                                   │
│  • Tire degradation analysis (linear regression within stints)          │
│  • Pace delta calculation over time                                     │
│  • Multiple visualizations:                                             │
│    - Lap time evolution by driver (colored by compound)                 │
│    - Strategy timeline (horizontal bars)                                │
│    - Pace delta heatmap                                                 │
│    - Box plots for stint comparison                                     │
│  • Statistical analysis (mean, std, trends)                             │
│  • Hypothesis testing results                                           │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CODE EXECUTION                                      │
│  • Runs generated analysis code                                         │
│  • Produces metrics, visualizations, insights                           │
│  • Code Debugger available if errors occur                              │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    REPORT GENERATOR                                      │
│  • Creates markdown report with findings                                │
│  • Includes visualizations                                              │
│  • Basic analysis complete!                                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    (if --deep or --story)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              🎯 DEEP ANALYSIS FETCHER (INTELLIGENT!)                     │
│                                                                          │
│  Uses Factor Analysis to determine what API data to fetch:              │
│                                                                          │
│  ✓ Weather data (track temp, air temp, conditions)                     │
│  ✓ Telemetry (speed, throttle, brake, DRS usage)                       │
│  ✓ Tire stints (compound, age, lap range)                              │
│  ✓ Pit stops (timing, duration)                                        │
│  ✓ Race control (flags, incidents, safety car)                         │
│  ✓ Team radio (strategy discussions, driver feedback) 📡 NEW!          │
│  ✓ GPS location (racing lines, overtake locations) 📍 NEW!             │
│                                                                          │
│  Intelligent Selection:                                                 │
│  • Only fetches data marked as needed by factor analysis                │
│  • Focuses on drivers/teams of interest                                 │
│  • Reduces API calls and costs                                          │
│                                                                          │
│  Example Mercedes Monaco data:                                          │
│  • Weather: Hot conditions (air 28°C, track 45°C)                       │
│  • Tire stints: Mercedes on Soft→Medium→Hard                            │
│  •              Red Bull on Soft→Medium→Medium                          │
│  • Team radio: "Tires are gone" (lap 35)                               │
│  • Pit timing: Mercedes pit lap 18, 42 | Red Bull pit lap 20, 40       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    (if --story)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       📖 STORYTELLER                                     │
│                                                                          │
│  Synthesizes narrative using:                                           │
│  • Dataset analysis results                                             │
│  • OpenF1 API data (weather, radio, telemetry)                         │
│  • Factor analysis hypotheses                                           │
│                                                                          │
│  Creates cohesive story explaining:                                     │
│  • What happened during the race                                        │
│  • WHY it happened (factor-driven insights)                             │
│  • Key moments and turning points                                       │
│  • Team strategy decisions (with radio context)                         │
│  • Driver performance and behavior                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FINAL OUTPUT                                     │
│                                                                          │
│  📄 Reports:                                                            │
│     • outputs/race_report.md (basic analysis)                           │
│     • outputs/narrative_report.md (story mode)                          │
│                                                                          │
│  📊 Visualizations:                                                     │
│     • Lap time evolution plots                                          │
│     • Strategy timelines                                                │
│     • Pace delta heatmaps                                               │
│     • Stint performance comparisons                                     │
│     • Position change plots                                             │
│                                                                          │
│  📈 Metrics:                                                            │
│     • outputs/analysis_metrics.parquet                                  │
│                                                                          │
│  💡 Insights:                                                           │
│     • WHY Mercedes struggled (hypothesis validated)                     │
│     • Specific factors that made the difference                         │
│     • Comparative analysis vs competitors                               │
│     • Time-based patterns and evolution                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Innovation: Factor-Driven Intelligence

### Before (Simple Keyword Matching)
```
Query: "Why did Mercedes struggle?"
→ Load data
→ Generate code to compare Mercedes
→ Basic analysis
```

### After (Intelligent Factor Analysis)
```
Query: "Why did Mercedes struggle?"
→ Factor Analyzer thinks:
   "What factors affect performance at Monaco?"
   - Tire strategy (high deg track)
   - Car setup (low speed corners)
   - Driver skill (precision needed)
   - Team strategy (pit timing critical)

→ Plans comprehensive analysis:
   - Compare tire degradation rates
   - Analyze stint-by-stint performance
   - Check pit timing vs competitors
   - Look at team radio for strategy clues
   - Fetch weather data (temp affects tires)

→ Fetches only relevant API data
→ Generates smart comparative code
→ Produces multi-dimensional insights
```

## Analysis Dimensions

The system now analyzes across multiple dimensions:

```
        TIME
         ↑
         │  ┌─────────────┐
         │  │ Lap-by-lap  │
         │  │   analysis  │
         │  └─────────────┘
         │
    ─────┼─────────────────────→ DRIVER
         │     Compare:
         │     • Verstappen
         │     • Hamilton
         │     • Russell
         │
         ↓
       TIRE
    Compound
    ┌─────────┐
    │ Soft    │──→ Degradation
    │ Medium  │──→ Pace delta
    │ Hard    │──→ Stint length
    └─────────┘
         ↓
      STRATEGY
    ┌──────────────┐
    │ Pit timing   │
    │ Compound     │
    │ choice       │
    │ Window       │
    └──────────────┘
```

## Data Sources Integration

```
┌─────────────────┐     ┌──────────────────┐
│  Kaggle Dataset │     │  OpenF1 API      │
│                 │     │                  │
│  • Results      │     │  • Weather       │
│  • Laps         │     │  • Telemetry     │
│  • Drivers      │     │  • Stints        │
│  • Constructors │     │  • Pit stops     │
│  • Pit stops    │     │  • Race control  │
│                 │     │  • Team radio    │🆕
│                 │     │  • GPS location  │🆕
└────────┬────────┘     └────────┬─────────┘
         │                       │
         │    ┌─────────────────┐│
         └────►  FACTOR         ├┘
              │  ANALYZER       │
              │  decides what   │
              │  to fetch       │
              └────────┬────────┘
                       │
                       ▼
              ┌────────────────┐
              │  COMPREHENSIVE │
              │   ANALYSIS     │
              └────────────────┘
```

## Example: Factor-Driven Data Fetching

```python
# Factor Analyzer determines what matters for the query
factor_analysis = {
    "data_sources_needed": {
        "lap_times": True,      # Always useful
        "tire_stints": True,    # Query mentions strategy
        "weather": True,        # Hot track affects tires
        "telemetry": True,      # Need pace data
        "pit_stops": True,      # Strategy comparison
        "race_control": True,   # Check for incidents
        "radio": True,          # Strategy discussions
        "positions": False      # Not needed for this query
    }
}

# Deep Analysis Fetcher uses this to fetch intelligently
api_data = fetch_comprehensive_session_data(
    year=2023,
    country="Monaco",
    session_type="Race",
    include_radio=True,      # ✓ Fetch
    include_location=False   # ✗ Skip (saves time & tokens)
)
```

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Intelligence** | Keyword-based | LLM reasoning |
| **Data Fetching** | Fetch everything | Fetch what's needed |
| **Analysis Depth** | Single dimension | Multi-dimensional |
| **Comparisons** | Basic averages | Stint-by-stint, time-based |
| **Insights** | WHAT happened | WHY it happened |
| **Visualizations** | Simple plots | Comprehensive, layered |
| **API Calls** | All endpoints | Intelligent selection |
| **Token Usage** | Higher | Optimized |
| **Understanding** | Surface level | Deep, causal |

---

**The system is now truly intelligent and autonomous!** 🚀
