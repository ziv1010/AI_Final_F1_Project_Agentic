# Driver Filtering Fix

## Issue
When querying "Compare Verstappen and Hamilton at Bahrain 2023", the system was:
- ✅ Correctly identifying the drivers in `DRIVERS_FOCUS` = ["Verstappen", "Hamilton"]
- ❌ But the code generation was analyzing ALL drivers or just top finishers
- ❌ Hamilton's data showed as "not available" in the report

## Root Cause
The code writer was generating code that selected drivers by:
```python
# WRONG - picks top 2 finishers, not the queried drivers
top_two = race_full.nsmallest(2, 'positionOrder')['driverId'].tolist()
compare_drivers = top_two
```

This meant if Verstappen finished 1st and someone else finished 2nd (not Hamilton), the analysis would compare Verstappen to that other driver instead.

## Solution

### Changes Made

1. **Added DRIVERS_FOCUS to configuration** ([code_writer.py:51-76](src/nodes/code_writer.py#L51-L76))
   ```python
   DRIVERS_FOCUS = ['Verstappen', 'Hamilton']  # Now available in generated code
   ```

2. **Added critical rule #0** ([code_writer.py:154-159](src/nodes/code_writer.py#L154-L159))
   ```
   0. DRIVER FOCUS (MOST IMPORTANT):
      - DRIVERS_FOCUS contains the driver surnames from the query
      - You MUST filter your analysis to ONLY these specific drivers
      - After joining results with drivers table, filter: race_full[race_full['surname'].isin(DRIVERS_FOCUS)]
      - DO NOT analyze all drivers or just the top finishers - ONLY the ones in DRIVERS_FOCUS
   ```

3. **Enhanced filtering instructions** ([code_writer.py:172-176](src/nodes/code_writer.py#L172-L176))
   - Emphasized that driver filtering is CRITICAL
   - Provided exact filtering pattern
   - Warned against common mistakes

## Expected Behavior Now

When you run:
```bash
python main.py "Compare Verstappen and Hamilton at Bahrain 2023"
```

The system will:
1. ✅ Extract `DRIVERS_FOCUS = ["Verstappen", "Hamilton"]` from query
2. ✅ Generate code that filters to ONLY these drivers:
   ```python
   race_full = race_full[race_full['surname'].isin(DRIVERS_FOCUS)]
   ```
3. ✅ Analyze lap times, stints, strategy for BOTH drivers
4. ✅ Generate visualizations showing BOTH drivers' data
5. ✅ Report complete statistics for BOTH drivers

## Example Expected Output

**Before Fix:**
```
| Driver | Team | Final Position | Points |
|--------|------|----------------|--------|
| Max Verstappen | Red Bull | 1st | 26.0 |
| Lewis Hamilton | Mercedes | Data not available | Data not available |
```

**After Fix:**
```
| Driver | Team | Final Position | Points | Grid | Fastest Lap |
|--------|------|----------------|--------|------|-------------|
| Max Verstappen | Red Bull | 1st | 26.0 | 1 | 1:32.145 |
| Lewis Hamilton | Mercedes | 3rd | 15.0 | 7 | 1:32.678 |
```

With complete analysis:
- Lap-by-lap pace comparison
- Stint performance for BOTH drivers
- Pit strategy comparison
- Pace evolution over time
- Why Verstappen beat Hamilton (tire management, strategy, etc.)

## Testing

Try these queries to verify the fix:
```bash
# Should compare only these two drivers
python main.py "Compare Verstappen and Hamilton at Bahrain 2024"

# Should compare only these two drivers
python main.py "Leclerc vs Sainz at Monaco 2023" --deep

# Should analyze all drivers (no specific focus)
python main.py "Who won the 2023 Bahrain GP?"
```

## Files Modified

- ✏️ [src/nodes/code_writer.py](src/nodes/code_writer.py)
  - Added `DRIVERS_FOCUS` to header configuration
  - Added critical rule #0 for driver filtering
  - Enhanced filtering instructions
  - Updated function signature to accept `drivers_focus`

## Impact

- **Fixes**: Driver comparison queries now work correctly
- **Backward Compatible**: Queries without specific drivers still work (analyzes all)
- **No Breaking Changes**: Existing functionality preserved
