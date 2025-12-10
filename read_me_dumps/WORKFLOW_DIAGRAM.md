# F1 Agent Self-Debugging Workflow

## New Workflow with Intelligent Error Recovery

```
┌─────────────────────────────────────────────────────────────────┐
│                    F1 Analysis Agent Workflow                    │
└─────────────────────────────────────────────────────────────────┘

    User Query
        ↓
┌───────────────────┐
│ Query Interpreter │  Extracts race info, teams, drivers
└────────┬──────────┘
         ↓
┌───────────────────┐
│   Data Loader     │  Loads parquet files from cache
└────────┬──────────┘
         ↓
┌───────────────────┐
│ Analysis Planner  │  Creates analysis plan
└────────┬──────────┘
         ↓
┌───────────────────┐
│  Plan Reviewer    │  Validates and refines plan
└────────┬──────────┘
         ↓
┌───────────────────────────────────────────────────────────────┐
│                     CODE EXECUTION LOOP                        │
│                   (Up to 5 attempts with                       │
│                   intelligent debugging)                       │
└───────────────────────────────────────────────────────────────┘
         ↓
┌───────────────────┐
│   Code Writer     │◄──────────────────┐
└────────┬──────────┘                   │
         ↓                               │
    [Execute Code]                       │
         ↓                               │
    ┌────────┐                          │
    │Success?│                          │
    └───┬─┬──┘                          │
        │ │                             │
    Yes │ │ No                          │
        │ │                             │
        │ └──────► Attempt 1? ──────────┘
        │              │                  (Retry with error context)
        │              No
        │              ↓
        │         Attempt 2-4?
        │              │
        │              Yes
        │              ↓
        │    ┌──────────────────┐
        │    │  Code Debugger   │  ← NEW! Intelligent Fix
        │    │                  │
        │    │  • Analyze error │
        │    │  • Identify root │
        │    │    cause         │
        │    │  • Generate fix  │
        │    └────────┬─────────┘
        │             │
        │             └─────────────────► Code Writer
        │                                    │
        │                                    ↓
        │                               [Re-execute]
        │                                    │
        │                                    │
        │◄───────────────────────────────────┘
        │                            (Loop until success
        │                             or 5 attempts)
        ↓
┌───────────────────┐
│ Report Generator  │  Synthesizes results
└────────┬──────────┘
         ↓
┌───────────────────┐
│   Final Report    │  Markdown output
└───────────────────┘


═══════════════════════════════════════════════════════════════
                    ERROR PATTERN DETECTION
═══════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────┐
│                    Code Debugger Logic                        │
└──────────────────────────────────────────────────────────────┘

Error Traceback
     ↓
┌─────────────────────────────────────────────────────────────┐
│              Pattern Recognition                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Pattern 1: REGEX_ESCAPE_ERROR                              │
│    Detect: "missing {", "PatternError"                      │
│    Fix: Use direct string replacement                       │
│                                                              │
│  Pattern 2: COLUMN_NOT_FOUND                                │
│    Detect: "KeyError", "not in index"                       │
│    Fix: Check df.columns, verify joins                      │
│                                                              │
│  Pattern 3: TYPE_CONVERSION_ERROR                           │
│    Detect: "TypeError", "cannot convert"                    │
│    Fix: Use pd.to_numeric(..., errors='coerce')            │
│                                                              │
│  Pattern 4: JOIN_ERROR                                      │
│    Detect: "can only merge", "MergeError"                   │
│    Fix: Verify keys exist, check dtypes                     │
│                                                              │
│  Pattern 5: DATETIME_PARSE_ERROR                            │
│    Detect: "to_datetime", "DateParseError"                  │
│    Fix: Use time_to_seconds() helper                        │
│                                                              │
│  Pattern 6: EMPTY_DATAFRAME                                 │
│    Detect: "empty", "no objects"                            │
│    Fix: Add if not df.empty: checks                         │
│                                                              │
│  Pattern 7: INDEX_ERROR                                     │
│    Detect: "IndexError", "out of bounds"                    │
│    Fix: Check length before indexing                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
     ↓
Generate Corrected Code
     ↓
Return to Code Writer


═══════════════════════════════════════════════════════════════
                      RETRY STRATEGY
═══════════════════════════════════════════════════════════════

Attempt #    Action              Node Used         Strategy
─────────────────────────────────────────────────────────────────
   1         Initial execution   Code Writer       Fresh generation

   2         First retry         Code Debugger     Pattern analysis
                                                   + intelligent fix

   3         Second retry        Code Debugger     Deeper analysis
                                                   with more context

   4         Third retry         Code Debugger     Alternative
                                                   approach

   5         Final attempt       Code Writer       Last chance with
                                                   all error history

   -         Failure             Report Generator  Document errors
                                                   in failure report


═══════════════════════════════════════════════════════════════
                    KEY IMPROVEMENTS
═══════════════════════════════════════════════════════════════

Before:
  • 3 simple retries with same approach
  • No error pattern recognition
  • Generic error messages
  • Manual intervention needed
  • Hardcoded values (teams, patterns)

After:
  • 5 intelligent retries with adaptive strategy
  • 7+ error patterns recognized automatically
  • Specific fixes for each error type
  • Fully autonomous error recovery
  • Dynamic value discovery (no hardcoding)
  • Detailed error analysis in logs
  • Pattern-based code corrections


═══════════════════════════════════════════════════════════════
                    EXAMPLE EXECUTION
═══════════════════════════════════════════════════════════════

User Query: "Analyze the 2024 Abu Dhabi GP for Ferrari and McLaren"

1. Query Interpreter → race_id=1141, teams=[Ferrari, McLaren]
2. Data Loader → Loads parquet files
3. Analysis Planner → Plans lap times, positions, pit stops
4. Plan Reviewer → Validates plan feasibility
5. Code Writer → Generates Python analysis code
   └─► Execute → ERROR: "missing { at position 2"
6. Code Debugger → Detects REGEX_ESCAPE_ERROR
   └─► Fix: Replace regex=True with direct replacement
7. Code Writer → Re-executes with corrected code
   └─► Execute → SUCCESS!
8. Report Generator → Creates markdown report
9. Output: "outputs/race_report.md"

Total time: ~15 seconds (including 1 auto-fix)
Human intervention: ZERO ✓
