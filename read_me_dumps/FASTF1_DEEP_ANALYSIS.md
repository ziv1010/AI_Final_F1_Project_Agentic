# FastF1 Deep Analysis Integration

## Overview

The system now includes **FastF1 integration** for comprehensive telemetry-based deep analysis. When you use `--deep` or `--story` mode, the system fetches detailed telemetry, tire, and strategy data using the FastF1 library.

## What FastF1 Provides

FastF1 gives access to real F1 session data including:

### 📊 Telemetry Data
- **Speed traces** - Exact speed at every point on track
- **Throttle application** - 0-100% throttle input
- **Brake pressure** - Braking points and intensity
- **Gear selection** - Which gear used where
- **DRS activation** - When DRS was open/closed
- **RPM** - Engine RPM throughout lap

### 🏎️ Tire Information
- **Compound used per stint** - Soft, Medium, Hard, Intermediate, Wet
- **Tire age** - How old tires were at stint start
- **Lap-by-lap degradation** - How performance degraded over stint
- **Strategy timeline** - Visual representation of compound choices

### 🌤️ Weather Data
- **Air temperature** evolution
- **Track temperature** changes
- **Humidity** levels
- **Rainfall** detection
- **Wind speed** (when available)

### ⏱️ Detailed Lap Data
- **Sector times** - S1, S2, S3 splits
- **Speed traps** - Top speed measurements
- **Personal bests** - Fastest laps flagged
- **Track status** - Yellow flags, safety car periods

## New Workflow

When you run with `--deep`:

```
Basic Analysis
    ↓
OpenF1 API Fetch (weather, race control, radio)
    ↓
FastF1 Data Fetch (telemetry, tires, detailed laps)  ← NEW!
    ↓
Deep Visualizations ← NEW!
    ↓
Deep Analysis Report (Answers Your Query) ← NEW!
```

## Deep Analysis Outputs

###  1. Deep Analysis Visualizations

**Location**: `outputs/deep_analysis_visualizations/`

Generated plots include:

#### `telemetry_comparison.png`
- Speed, throttle, and brake traces for compared drivers
- Shows exact driving differences
- Identifies where time is gained/lost

#### `tire_degradation_curves.png`
- Lap time evolution within each stint
- Degradation rate per compound
- Visual comparison of tire management

#### `strategy_timeline.png`
- Horizontal timeline showing tire choices
- Color-coded by compound
- Shows pit stop timing

#### `weather_evolution.png`
- Temperature and humidity changes during session
- Helps explain pace variations
- Identifies weather impact windows

#### `stint_laptime_distribution.png`
- Box plots showing pace consistency per stint
- Identifies performance windows
- Shows stint-to-stint variation

### 2. Deep Analysis Report

**Location**: `outputs/deep_analysis_summary.md`

This report:
- ✅ **Directly answers your original query**
- ✅ Synthesizes ALL data (basic + API + FastF1)
- ✅ Provides evidence-based conclusions
- ✅ References specific telemetry data
- ✅ Explains WHY results occurred

**Structure**:
```markdown
# Deep Analysis: [Your Query]

## Executive Summary
[Direct 2-3 sentence answer to your question]

## Detailed Analysis
- Performance Comparison (with telemetry evidence)
- Telemetry Insights (speed/throttle/brake differences)
- Tire Strategy & Degradation (compound choices, deg rates)
- Weather Impact (if relevant)
- Critical Moments (key laps, strategic decisions)

## Answer to Query
**Direct, comprehensive answer with supporting evidence**

## Visualizations
[List of all deep analysis visualizations]

## Conclusion
[Final answer connecting all evidence]
```

## Data Availability

### FastF1 Data Coverage
- **Years**: 2018 onwards
- **Sessions**: Race, Qualifying, Practice, Sprint
- **Granularity**: ~3.7Hz telemetry sampling

### Automatic Fallback
- If FastF1 data unavailable → continues with OpenF1 API only
- If OpenF1 unavailable → continues with Kaggle dataset only
- System gracefully degrades, never fails completely

## Example Queries

### 1. Telemetry-Focused
```bash
python main.py "Where did Verstappen gain time on Hamilton at Bahrain 2024?" --deep
```

**Deep Analysis Will Show**:
- Exact speed differences at each corner
- Throttle application comparison
- Braking point differences
- Specific track sections where time was gained
- Telemetry plots highlighting differences

### 2. Strategy-Focused
```bash
python main.py "Compare tire strategies at Monaco 2023" --deep
```

**Deep Analysis Will Show**:
- Compound choices per driver/team
- Degradation rates per compound
- Stint length effectiveness
- Strategy timeline visualization
- Which strategy was optimal and why

### 3. Performance Investigation
```bash
python main.py "Why did Ferrari struggle in the final stint at Singapore 2023?" --deep
```

**Deep Analysis Will Show**:
- Lap-by-lap degradation curves
- Weather impact on final stint
- Telemetry showing pace loss
- Comparison with competitors' final stints
- Evidence-based explanation

## Technical Details

### Caching
FastF1 automatically caches data in `data/cache/fastf1/` for faster subsequent loads.

### Memory Usage
- Telemetry data is downsampled (500 points per lap) to reduce memory
- Only focused drivers' telemetry is fetched
- Session data is loaded once and reused

### Error Handling
- FastF1 errors don't crash the pipeline
- System continues with available data
- Errors reported in deep analysis summary

## Configuration

In [config.yaml](config.yaml):

```yaml
analysis:
  enable_api: true  # Enable OpenF1 + FastF1
  api_rate_limit: 2  # Requests per second
```

## Files Created

### New Modules
1. **[src/tools/fastf1_tools.py](src/tools/fastf1_tools.py)** - FastF1 data fetching
2. **[src/nodes/deep_visualizer.py](src/nodes/deep_visualizer.py)** - Deep visualizations
3. **[src/nodes/deep_report_generator.py](src/nodes/deep_report_generator.py)** - Focused report generation

### Enhanced Modules
- **[src/nodes/deep_analysis_fetcher.py](src/nodes/deep_analysis_fetcher.py)** - Now fetches FastF1 data
- **[src/graph.py](src/graph.py)** - Updated workflow to include deep viz + report

## Comparison: Basic vs Deep

| Aspect | Basic Analysis | Deep Analysis |
|--------|---------------|---------------|
| **Data Source** | Kaggle CSV | Kaggle + OpenF1 + FastF1 |
| **Telemetry** | ❌ No | ✅ Speed/Throttle/Brake traces |
| **Tire Info** | Limited (pit stops) | ✅ Compounds, degradation curves |
| **Weather** | ❌ No | ✅ Temperature/Humidity evolution |
| **Visualizations** | Basic plots | Advanced telemetry plots |
| **Report** | General findings | **Direct answer to query** |
| **Evidence** | Statistical | Telemetry-based |
| **Years Supported** | 1950-2024 | 2018-2024 (FastF1) |

## Benefits

### 1. **Query-Focused Answers**
The deep report directly answers your question with evidence, not just data dumps.

### 2. **Telemetry Evidence**
See exact driving differences - where time was gained/lost on track.

### 3. **Strategy Insights**
Understand tire choices, degradation, and pit timing with real data.

### 4. **Weather Context**
Know how conditions affected performance throughout the session.

### 5. **Professional Quality**
Publication-ready visualizations and comprehensive analysis.

## Usage Tips

### Best Practices
1. **Use `--deep` for modern races** (2018+) to get FastF1 data
2. **Ask specific questions** - "Where did X gain time?" vs "Compare X and Y"
3. **Check deep_analysis_summary.md** for the focused answer to your query
4. **Review visualizations** in `deep_analysis_visualizations/` for evidence

### Common Issues

**"FastF1 data unavailable"**
- Race is before 2018
- Session not yet in FastF1 database
- → System continues with OpenF1 data only

**Slow first run**
- FastF1 downloads session data (cached after first run)
- Subsequent runs much faster

## Example Output

Query: `"Where did Verstappen beat Hamilton at Bahrain 2024?"`

### Basic Analysis
"Verstappen finished 1st, Hamilton 3rd. Gap: 22.4s"

### Deep Analysis
```markdown
# Deep Analysis: Where did Verstappen beat Hamilton at Bahrain 2024?

## Executive Summary
Verstappen gained time primarily in Sector 3 (0.15s/lap average) through superior traction out of Turn 10 and higher minimum speeds through the final complex. His tire degradation rate was 0.048s/lap vs Hamilton's 0.067s/lap on the Medium compound.

## Telemetry Insights
**Speed Trace Analysis**:
- Turn 10 exit: Verstappen carried 8 km/h more (186 vs 178 km/h)
- Final chicane: Earlier throttle application by 15m
- Back straight: 4 km/h higher top speed (312 vs 308 km/h)

## Tire Strategy & Degradation
- Both started on Soft tires
- Verstappen pitted lap 18 (optimal window)
- Hamilton pitted lap 16 (too early, more degradation)
- Verstappen's Medium stint: 0.048s/lap degradation
- Hamilton's Medium stint: 0.067s/lap degradation

[See: telemetry_comparison.png, tire_degradation_curves.png]

## Answer to Query
Verstappen beat Hamilton through a combination of:
1. **Better traction** (8 km/h advantage at Turn 10 exit)
2. **Superior tire management** (19ms/lap less degradation)
3. **Optimal pit timing** (2 laps later = fresher tires)

Total advantage: ~0.3s/lap from driving + 0.02s/lap from strategy = **22.4s over 57 laps**.
```

---

**The system now provides comprehensive, evidence-based answers to your F1 analysis questions using real telemetry data!** 🏎️📊
