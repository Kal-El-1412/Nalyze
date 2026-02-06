# AE-1: Analysis-Specific SQL Plans (Backend)

## Status: ✅ COMPLETE

## Summary

The `_generate_sql_plan()` method in `chat_orchestrator.py` now generates analysis-specific SQL queries for each intent type, replacing any generic "SELECT * LIMIT 100" preview plans with proper analytical queries.

## Changes Made

### 1. Top Categories - Updated LIMIT and Column Alias (chat_orchestrator.py:554-562)

**Before:**
```python
queries.append({
    "name": "top_categories",
    "sql": f'SELECT "{categorical_col}", COUNT(*) as count FROM data GROUP BY "{categorical_col}" ORDER BY count DESC LIMIT 10'
})
explanation = f"I'll show you the top 10 categories in the {categorical_col} column for the {time_period} period."
```

**After:**
```python
queries.append({
    "name": "top_categories",
    "sql": f'SELECT "{categorical_col}" AS category, COUNT(*) as count FROM data GROUP BY "{categorical_col}" ORDER BY count DESC LIMIT 20'
})
explanation = f"I'll show you the top 20 categories in the {categorical_col} column for the {time_period} period."
```

**Changes:**
- Increased LIMIT from 10 to 20 as per requirement
- Added `AS category` alias for consistency
- Updated explanation text

### 2. Outliers - Added 200 Row Cap (chat_orchestrator.py:649-675)

**Before:**
```python
union_sql = " UNION ALL ".join(outlier_selects)
queries.append({
    "name": "outliers_detected",
    "sql": union_sql
})
```

**After:**
```python
union_sql = " UNION ALL ".join(outlier_selects)
# Wrap in subquery and cap at 200 rows
final_sql = f"SELECT * FROM ({union_sql}) AS outliers LIMIT 200"
queries.append({
    "name": "outliers_detected",
    "sql": final_sql
})
```

**Changes:**
- Wrapped UNION ALL in subquery with LIMIT 200
- Removed individual row_index calculation (no longer needed)
- Updated explanation to mention "capped at 200 rows"

### 3. Removed Legacy parse_natural_language_to_sql (utils.py:76-101)

**Before:**
```python
def parse_natural_language_to_sql(
    user_message: str,
    columns: List[str],
    sample_data: Optional[List[Dict[str, Any]]] = None
) -> str:
    user_message_lower = user_message.lower()

    if "count" in user_message_lower or "how many" in user_message_lower:
        return "SELECT COUNT(*) as count FROM data"

    if "show" in user_message_lower or "display" in user_message_lower or "all" in user_message_lower:
        if "first" in user_message_lower or "top" in user_message_lower:
            return "SELECT * FROM data LIMIT 10"
        return "SELECT * FROM data LIMIT 100"  # ❌ Generic preview

    if "average" in user_message_lower or "mean" in user_message_lower:
        numeric_cols = [col for col in columns if "price" in col.lower() or "amount" in col.lower() or "value" in col.lower()]
        if numeric_cols:
            return f'SELECT AVG("{numeric_cols[0]}") as average FROM data'

    if "sum" in user_message_lower or "total" in user_message_lower:
        numeric_cols = [col for col in columns if "price" in col.lower() or "amount" in col.lower() or "value" in col.lower()]
        if numeric_cols:
            return f'SELECT SUM("{numeric_cols[0]}") as total FROM data'

    return "SELECT * FROM data LIMIT 10"  # ❌ Generic fallback
```

**After:**
```python
# Function completely removed (unused legacy code)
```

**Rationale:**
- This function was never called anywhere in the codebase
- Contained the problematic `SELECT * FROM data LIMIT 100` and `LIMIT 10` patterns
- All SQL generation now goes through `_generate_sql_plan()` in chat orchestrator

## Existing Implementations (Already Correct)

### Row Count (chat_orchestrator.py:547-552)
```python
if analysis_type == "row_count":
    queries.append({
        "name": "row_count",
        "sql": "SELECT COUNT(*) as row_count FROM data"
    })
    explanation = "I'll count the total rows in your dataset."
```
✅ Already generates `COUNT(*)` query, not `SELECT * LIMIT 100`

### Trend (chat_orchestrator.py:576-618)
```python
elif analysis_type == "trend":
    if working_catalog:
        date_col = self._detect_date_column(working_catalog)
        metric_col = self._detect_metric_column(working_catalog)

        if date_col and metric_col:
            queries.append({
                "name": "monthly_trend",
                "sql": f'''SELECT
                    DATE_TRUNC('month', "{date_col}") as month,
                    COUNT(*) as count,
                    SUM("{metric_col}") as total_{metric_col},
                    AVG("{metric_col}") as avg_{metric_col}
                FROM data
                GROUP BY month
                ORDER BY month
                LIMIT 200'''
            })
```
✅ Already uses `DATE_TRUNC('month')` with GROUP BY and ORDER BY

### Outliers (chat_orchestrator.py:620-687)
```python
elif analysis_type == "outliers":
    # ... calculates z-score and filters by > 2 std dev ...
    WHERE "{col}" IS NOT NULL
      AND ABS("{col}" - (SELECT AVG("{col}") FROM data WHERE "{col}" IS NOT NULL))
          > 2 * (SELECT STDDEV("{col}") FROM data WHERE "{col}" IS NOT NULL)
```
✅ Already computes z-score and filters by > 2 standard deviations

## SQL Plan Examples

### Row Count
```sql
SELECT COUNT(*) as row_count FROM data
```

### Top Categories
```sql
SELECT "category" AS category, COUNT(*) as count
FROM data
GROUP BY "category"
ORDER BY count DESC
LIMIT 20
```

### Trend (Monthly)
```sql
SELECT
    DATE_TRUNC('month', "created_at") as month,
    COUNT(*) as count,
    SUM("value") as total_value,
    AVG("value") as avg_value
FROM data
GROUP BY month
ORDER BY month
LIMIT 200
```

### Outliers (Z-Score > 2, Capped at 200 Rows)
```sql
SELECT * FROM (
    SELECT
        'value' as column_name,
        "value" as value,
        (SELECT AVG("value") FROM data WHERE "value" IS NOT NULL) as mean_value,
        (SELECT STDDEV("value") FROM data WHERE "value" IS NOT NULL) as stddev_value,
        ("value" - (SELECT AVG("value") FROM data WHERE "value" IS NOT NULL))
            / (SELECT STDDEV("value") FROM data WHERE "value" IS NOT NULL) as z_score
    FROM data
    WHERE "value" IS NOT NULL
      AND ABS("value" - (SELECT AVG("value") FROM data WHERE "value" IS NOT NULL))
          > 2 * (SELECT STDDEV("value") FROM data WHERE "value" IS NOT NULL)

    UNION ALL

    -- ... (repeats for other numeric columns) ...
) AS outliers
LIMIT 200
```

## Behavior Changes

| Analysis Type | Before | After |
|---------------|--------|-------|
| row_count | ✅ `COUNT(*)` | ✅ `COUNT(*)` (no change) |
| top_categories | LIMIT 10, no alias | LIMIT 20, `AS category` |
| trend | ✅ `DATE_TRUNC('month')` with GROUP BY | ✅ No change |
| outliers | z-score, no explicit cap | z-score, explicit LIMIT 200 |
| unknown/fallback | row_count | row_count (no change) |

## Acceptance Criteria

✅ **Asking "row count" yields a COUNT(*) query, not SELECT * LIMIT 100**
- Confirmed: row_count returns `SELECT COUNT(*) as row_count FROM data`
- No SELECT * LIMIT 100 queries in row_count path

✅ **Audit shows the correct SQL for each intent**
- row_count: `SELECT COUNT(*) as row_count FROM data`
- top_categories: `SELECT <cat_col> AS category, COUNT(*) as count FROM data GROUP BY 1 ORDER BY count DESC LIMIT 20`
- trend: `SELECT DATE_TRUNC('month', <date_col>) AS month, SUM(<metric_col>) AS total FROM data GROUP BY 1 ORDER BY 1`
- outliers: Query that computes z-score and filters abs(z) > 2 (capped at 200 rows)

✅ **No default/preview plan with SELECT * LIMIT 100**
- Removed `parse_natural_language_to_sql` function from utils.py
- All "SELECT * FROM data LIMIT 100" and "LIMIT 10" patterns removed
- Only remaining SELECT * queries are for technical column discovery (SELECT * LIMIT 1)

## Testing

Run test suite:
```bash
cd connector
python3 test_ae1_simple.py
```

Expected output:
```
✅ PASS: row_count implementation
✅ PASS: top_categories implementation
✅ PASS: trend implementation
✅ PASS: outliers implementation
✅ PASS: No SELECT * LIMIT 100
```

## Files Modified

1. **connector/app/chat_orchestrator.py**
   - Line 560: Changed top_categories LIMIT from 10 to 20
   - Line 560: Added `AS category` alias
   - Line 562: Updated explanation text
   - Lines 654-675: Added LIMIT 200 cap for outliers
   - Line 675: Updated explanation to mention cap

2. **connector/app/utils.py**
   - Lines 76-101: Removed `parse_natural_language_to_sql` function

## Files Added

1. **connector/test_analysis_specific_plans.py** - Full async test suite (requires dependencies)
2. **connector/test_ae1_simple.py** - Simplified test suite (no dependencies)
3. **connector/AE1_COMPLETE.md** - This document

## Related Requirements

- OFF-REAL-1 (No canned summaries) - Compatible
- OFF-REAL-2 (Deterministic keyword mapping) - Compatible
- Prompt 4 (row_count never asks for time period) - Compatible
- HR6 (JSON-only responses) - Compatible
- Safe Mode - Compatible (already uses aggregates)
- Privacy Mode - Compatible (works with redacted schemas)

## Column Detection Methods

The implementation uses helper methods to detect appropriate columns:

### _detect_best_categorical_column(catalog)
- Returns first text/string column suitable for categorization
- Used by top_categories

### _detect_date_column(catalog)
- Returns first date/timestamp column
- Used by trend

### _detect_metric_column(catalog)
- Returns first numeric column suitable for aggregation
- Used by trend

### _detect_all_numeric_columns(catalog)
- Returns all numeric columns
- Used by outliers (checks up to 10 columns)

## Fallback Behavior

When catalog is missing or columns can't be detected:

1. **top_categories without categorical column**: Falls back to row_count
2. **trend without date column**: Falls back to row_count
3. **outliers without numeric columns**: Falls back to row_count
4. **Unknown analysis_type**: Falls back to row_count

All fallbacks use `SELECT COUNT(*) as row_count FROM data`, never `SELECT * LIMIT 100`.

## Discovery Queries

Technical note: There are still `SELECT * FROM data LIMIT 1` queries used for column discovery when catalog is missing. These are:
- Named "discover_columns"
- Used only to infer schema, not as data preview
- Not part of the "default preview plan" problem
- Necessary for technical functionality

## Next Steps

This implementation is production-ready. The SQL plans are now:
- Analysis-specific for each intent type
- Free of generic SELECT * LIMIT 100 fallbacks
- Properly scoped (row counts, aggregates, z-scores)
- Capped at reasonable limits (20 categories, 200 outliers, 200 trend points)
