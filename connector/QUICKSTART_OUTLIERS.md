# Quick Start: Outlier Detection (2σ)

## What It Does

Detects statistical outliers beyond 2 standard deviations from the mean across all numeric columns.

## Usage

### Free Text Query
```
User: "find outliers beyond 2 std dev"
System: *analyzes all numeric columns*
System: *returns table with outliers*
```

### Button Selection
```
User: Selects "outliers" analysis type
User: Selects time period
System: *executes outlier detection*
```

## Two Modes

### Regular Mode (Safe Mode OFF)
Returns individual outlier rows:
```
column_name | value | mean_value | stddev_value | z_score | row_index
revenue     | 15000 | 5000       | 2000         | 5.0     | 42
quantity    | 500   | 100        | 80           | 5.0     | 87
```

### Safe Mode (Safe Mode ON)
Returns aggregated counts only (no raw data):
```
column_name | outlier_count | mean_value | stddev_value
revenue     | 12            | 5000       | 2000
quantity    | 8             | 100        | 80
```

## Key Features

1. **Automatic** - Detects all numeric columns
2. **Smart** - Excludes ID columns
3. **Statistical** - Uses 2σ threshold (95% confidence)
4. **Safe** - Respects Safe Mode setting
5. **Limited** - 50 rows per column (prevents overload)

## Acceptance

✅ Returns concrete table (not stub)
✅ Shows column_name, value, z_score, row_index
✅ Safe Mode shows counts only

## Implementation

See `OUTLIERS_2STDDEV.md` for full details.

**Files:**
- `connector/app/chat_orchestrator.py` - SQL generation & formatting
- `connector/test_outliers_2stddev.py` - Test scenarios
