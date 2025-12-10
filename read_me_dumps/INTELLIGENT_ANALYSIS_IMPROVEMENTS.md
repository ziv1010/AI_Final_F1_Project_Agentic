# Intelligent Analysis System Improvements

## Overview

The F1 Weekend Strategy Analyst has been significantly enhanced to be **smarter and more autonomous** in analyzing race data. The system now intelligently thinks about what factors matter and automatically fetches relevant data sources to provide comprehensive, multi-dimensional analysis.

## Key Improvements

### 1. **Intelligent Factor Analysis Node** 🧠

**Location**: [src/nodes/factor_analyzer.py](src/nodes/factor_analyzer.py)

The new Factor Analyzer node analyzes each query to understand:

- **What the user is really asking** - Goes beyond surface-level interpretation
- **What performance factors matter** - Identifies tire strategy, weather, pace, reliability, etc.
- **What data sources are needed** - Intelligently determines which API endpoints to call
- **What comparisons should be made** - Plans driver vs driver, team vs team, stint vs stint analyses
- **What hypotheses to test** - Formulates testable hypotheses about race outcomes

**Benefits**:
- The system now **thinks** about each query before starting analysis
- Automatically identifies what factors could have affected race outcomes
- No longer relies on simple keyword matching - uses LLM reasoning

**Example**:
```
Query: "Why did Mercedes struggle at Monaco 2023?"

Factor Analysis Output:
{
  "primary_question": "What caused Mercedes' poor performance at Monaco?",
  "key_factors": ["tire_strategy", "track_characteristics", "car_setup", "pace_evolution"],
  "data_sources_needed": {
    "lap_times": true,
    "tire_stints": true,
    "weather": true,
    "telemetry": true,
    "pit_stops": true,
    "race_control": true,
    "radio": true
  },
  "comparisons": [
    {"type": "team", "entities": ["Mercedes", "Red Bull", "Ferrari"], "metric": "lap_pace"},
    {"type": "stint", "entities": ["Stint 1", "Stint 2"], "metric": "tire_degradation"}
  ],
  "hypotheses": [
    "Mercedes had higher tire degradation than competitors",
    "Track characteristics didn't suit Mercedes' car setup",
    "Strategy decisions were sub-optimal"
  ]
}
```

### 2. **Enhanced Analysis Planner** 📊

**Location**: [src/nodes/analysis_planner.py](src/nodes/analysis_planner.py)

The Analysis Planner now receives factor analysis context and creates **comprehensive, intelligent plans** that:

- Think about **WHY** results differ, not just **WHAT** they are
- Plan multiple angles of analysis (pace, strategy, conditions)
- Consider time-based patterns (evolution during the race)
- Plan for comparative analysis across multiple dimensions
- Include tire degradation, pit timing, and strategy differences

**New Plan Sections**:
1. Factors & Hypotheses - What might explain the results?
2. Files to Load - All relevant data sources
3. Cleaning Steps - Data preparation
4. Joins & Data Integration - Building complete datasets
5. **Time-Based Analysis** - Lap-by-lap pace evolution, stint performance
6. **Comparative Metrics** - Multi-dimensional comparisons
7. **Visualizations** - Comprehensive visual analysis
8. **Insights to Extract** - What patterns to look for

### 3. **Expanded OpenF1 API Tools** 📡

**Location**: [src/tools/openf1_tools.py](src/tools/openf1_tools.py)

**New API Endpoints**:

#### Team Radio Communications
```python
@tool
def get_openf1_team_radio(session_key: int, driver_number: Optional[int] = None)
```

Provides access to team radio communications during sessions, offering insights into:
- Strategy discussions between driver and team
- Driver feedback on car behavior
- Real-time decision making during the race
- Team instructions and responses

#### GPS Location Data
```python
@tool
def get_openf1_location(session_key: int, driver_number: int, limit: int = 100)
```

Provides car location data (GPS coordinates) useful for:
- Analyzing racing lines
- Identifying where overtakes happened
- Understanding track position during incidents

**Enhanced Data Fetching**:
```python
fetch_comprehensive_session_data(
    year, country, session_type,
    driver_numbers=None,
    include_radio=True,      # NEW
    include_location=False   # NEW
)
```

### 4. **Smart Deep Analysis Fetcher** 🎯

**Location**: [src/nodes/deep_analysis_fetcher.py](src/nodes/deep_analysis_fetcher.py)

The Deep Analysis Fetcher now uses factor analysis to **intelligently determine what data to fetch**:

```python
# Get factor analysis to intelligently determine what data to fetch
factor_analysis = state.get("analysis_outputs", {}).get("factor_analysis", {})
data_sources_needed = factor_analysis.get("data_sources_needed", {})

# Intelligent data source selection
include_radio = data_sources_needed.get("radio", True)
include_location = data_sources_needed.get("positions", False)
```

**Benefits**:
- Only fetches data that's relevant to the query
- Reduces API calls and token usage for irrelevant data
- Automatically adapts to query requirements

### 5. **Advanced Code Generation** 💻

**Location**: [src/nodes/code_writer.py](src/nodes/code_writer.py)

The Code Writer now generates **more intelligent, comprehensive analysis code**:

**New Capabilities**:

1. **Comparative Analysis**:
   - Stint-by-stint lap time comparison (not just overall averages)
   - Tire degradation analysis within stints
   - Pit strategy comparison with timing and compound analysis
   - Pace deltas between drivers/teams over time
   - Performance gap evolution tracking

2. **Time-Based Patterns**:
   - Lap-by-lap pace evolution
   - Fastest lap identification and timing
   - Performance in different race phases (start, middle, end)
   - Position changes over time

3. **Multi-Dimensional Visualizations**:
   - Lap time evolution plots (colored by stint/tire)
   - Strategy timelines (horizontal bars showing tire compounds)
   - Pace delta heatmaps (driver vs driver by lap/stint)
   - Box plots for stint performance comparison
   - Scatter plots for pit timing vs final position

4. **Statistical Analysis**:
   - Mean, median, standard deviation for key metrics
   - Trend analysis within stints
   - Comparative statistics across entities

### 6. **Updated Workflow** 🔄

**Location**: [src/graph.py](src/graph.py)

All graph workflows now include the Factor Analyzer:

```
Old Flow:
query_interpreter → data_loader → analysis_planner → ...

New Flow:
query_interpreter → factor_analyzer → data_loader → analysis_planner → ...
```

This ensures every query goes through intelligent factor analysis before proceeding.

## Usage Examples

### Basic Query with Intelligent Analysis
```bash
python main.py "Compare Verstappen and Hamilton at the 2023 Bahrain GP"
```

The system will:
1. Analyze what factors matter (tire strategy, pace, pit timing)
2. Determine what data sources are needed
3. Fetch relevant data (laps, pits, stints)
4. Generate comprehensive comparative analysis
5. Create multi-dimensional visualizations

### Deep Analysis with API Data
```bash
python main.py "Why did Mercedes struggle at Monaco 2023?" --deep
```

The system will:
1. Perform intelligent factor analysis
2. Identify that weather, tire strategy, and pace evolution are key
3. Fetch OpenF1 API data (weather, telemetry, stints, radio)
4. Compare Mercedes vs competitors across multiple dimensions
5. Analyze time-based patterns (pace evolution during race)
6. Generate hypothesis-driven insights

### Story Mode with Full Context
```bash
python main.py "Tell me the story of the 2023 Las Vegas GP" --story
```

The system will:
1. Identify key narrative elements through factor analysis
2. Fetch comprehensive data (Kaggle + OpenF1)
3. Analyze multiple dimensions (strategy, pace, incidents, radio)
4. Generate a cohesive narrative explaining the race
5. Include team radio context and decision-making insights

## Technical Architecture

### Data Flow

```
User Query
    ↓
Query Interpreter (identify race, drivers, teams)
    ↓
Factor Analyzer (intelligent analysis of what matters)
    ↓
Data Loader (load Kaggle dataset)
    ↓
Analysis Planner (comprehensive plan with factor context)
    ↓
Plan Reviewer (validate and refine)
    ↓
Code Writer (generate smart, comparative analysis code)
    ↓
Report Generator (basic report)
    ↓
Deep Analysis Fetcher (intelligent API data fetching) [if --deep or --story]
    ↓
Storyteller (narrative synthesis) [if --story]
```

### State Extensions

The `WeekendState` now includes:
```python
{
    "analysis_outputs": {
        "factor_analysis": {
            "primary_question": str,
            "key_factors": List[str],
            "data_sources_needed": Dict[str, bool],
            "comparisons": List[Dict],
            "hypotheses": List[str],
            "analysis_approach": str
        }
    }
}
```

## Benefits Summary

### 🎯 **Autonomous Intelligence**
- System thinks about what factors matter before analyzing
- No longer relies on simple keyword matching
- Adapts analysis approach based on query context

### 📊 **Comprehensive Analysis**
- Multi-dimensional comparisons (driver, team, stint, time)
- Time-based pattern recognition
- Hypothesis-driven insights

### 🔧 **Smart Data Fetching**
- Only fetches relevant data sources
- Reduces API calls and costs
- Includes team radio for strategy insights

### 📈 **Better Visualizations**
- Stint-by-stint analysis
- Strategy timelines
- Pace evolution plots
- Comparative heatmaps

### 💡 **Deeper Insights**
- Explains WHY results occurred (not just WHAT happened)
- Tests hypotheses about performance
- Identifies causal factors

## Future Enhancements

Potential areas for further improvement:

1. **Machine Learning Integration**: Use historical patterns to predict strategy outcomes
2. **Weather Impact Analysis**: Quantify how weather affected different teams/drivers
3. **Tire Model Refinement**: More sophisticated tire degradation modeling
4. **Radio Sentiment Analysis**: Analyze team radio tone and sentiment
5. **Predictive Analytics**: Forecast race outcomes based on practice/qualifying data
6. **Multi-Race Comparisons**: Compare performance across multiple races to identify trends

## Configuration

The system behavior can be tuned via [config.yaml](config.yaml):

```yaml
llm:
  model: "openai/gpt-oss-120b"  # Or other models
  temperature: 0.1

tokens:
  limit: 50000  # Adjust based on your API tier

analysis:
  default_depth: "basic"  # "basic", "deep", or "story"
  enable_api: true
  api_rate_limit: 2
```

## Performance Considerations

- **Token Usage**: Factor Analyzer uses ~2000-3000 tokens per query
- **API Calls**: Intelligent selection reduces unnecessary OpenF1 API calls
- **Execution Time**: Factor analysis adds ~2-3 seconds to workflow
- **Benefits**: More comprehensive results with similar or lower token usage overall

## Conclusion

The enhanced F1 Weekend Strategy Analyst is now a **truly intelligent analysis system** that:
- ✅ Thinks autonomously about what factors matter
- ✅ Fetches data intelligently based on query context
- ✅ Generates comprehensive, multi-dimensional analysis
- ✅ Creates hypothesis-driven insights
- ✅ Explains WHY results occurred, not just WHAT happened

This makes it a powerful tool for F1 strategy analysis, race engineering review, and fan engagement.
