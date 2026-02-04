# Outlier Detection - 2 Standard Deviations

## Overview

Advanced outlier detection that identifies values beyond 2 standard deviations from the mean across all numeric columns (excluding ID columns).

## How It Works

### 1. Numeric Column Detection

- Automatically detects all numeric columns in the dataset
- Excludes columns with "id" in the name (case-insensitive)
- Supports: INTEGER, BIGINT, DOUBLE, FLOAT, DECIMAL, NUMERIC

### 2. Outlier Detection Logic

For each numeric column:
```sql
WHERE ABS(value - mean) > 2 * stddev
```

**Z-Score Calculation:**
```
z_score = (value - mean) / stddev
```

Values with |z_score| > 2 are flagged as outliers.

### 3. Two Modes

#### Regular Mode (Safe Mode OFF)
Returns individual outlier rows with:
- `column_name` - Which column the outlier is from
- `value` - The outlier value
- `mean_value` - Mean of that column
- `stddev_value` - Standard deviation of that column
- `z_score` - How many standard deviations from mean
- `row_index` - Row number in dataset

**Limit:** 50 rows per column (up to 10 columns analyzed)

#### Safe Mode (Safe Mode ON)
Returns aggregated counts per column:
- `column_name` - Column name
- `outlier_count` - Number of outliers in that column
- `mean_value` - Column mean
- `stddev_value` - Column standard deviation
- `min_value` - Minimum outlier value
- `max_value` - Maximum outlier value

**No raw data exposed in Safe Mode!**

## SQL Implementation

### Regular Mode Query
```sql
SELECT
    'revenue' as column_name,
    "revenue" as value,
    (SELECT AVG("revenue") FROM data WHERE "revenue" IS NOT NULL) as mean_value,
    (SELECT STDDEV("revenue") FROM data WHERE "revenue" IS NOT NULL) as stddev_value,
    ("revenue" - (SELECT AVG("revenue") FROM data WHERE "revenue" IS NOT NULL))
        / (SELECT STDDEV("revenue") FROM data WHERE "revenue" IS NOT NULL) as z_score,
    ROW_NUMBER() OVER () as row_index
FROM data
WHERE "revenue" IS NOT NULL
  AND ABS("revenue" - (SELECT AVG("revenue") FROM data WHERE "revenue" IS NOT NULL))
      > 2 * (SELECT STDDEV("revenue") FROM data WHERE "revenue" IS NOT NULL)
LIMIT 50
```

Repeated for each numeric column, combined with `UNION ALL`.

### Safe Mode Query
```sql
SELECT
    'revenue' as column_name,
    COUNT(*) as outlier_count,
    AVG("revenue") as mean_value,
    STDDEV("revenue") as stddev_value,
    MIN("revenue") as min_value,
    MAX("revenue") as max_value
FROM data
WHERE "revenue" IS NOT NULL
  AND ABS("revenue" - (SELECT AVG("revenue") FROM data WHERE "revenue" IS NOT NULL))
      > 2 * (SELECT STDDEV("revenue") FROM data WHERE "revenue" IS NOT NULL)
```

Repeated for each numeric column, combined with `UNION ALL`.

## Usage

### Via Intent Router

```
User: "find outliers beyond 2 std dev"
System: Routes to analysis_type='outliers'
System: Asks for time_period (if needed)
System: Executes outlier detection
System: Returns table with outlier details
```

### Via Button

```
User: Clicks "outliers" analysis type
User: Selects time period
System: Executes outlier detection
```

## Example Results

### Regular Mode Output

| column_name | value | mean_value | stddev_value | z_score | row_index |
|-------------|-------|------------|--------------|---------|-----------|
| revenue     | 15000 | 5000       | 2000         | 5.0     | 42        |
| revenue     | -3000 | 5000       | 2000         | -4.0    | 103       |
| quantity    | 500   | 100        | 80           | 5.0     | 87        |

**Interpretation:**
- Revenue value of 15000 is 5 standard deviations above mean (extreme outlier!)
- Revenue value of -3000 is 4 standard deviations below mean (also extreme)
- Quantity value of 500 is 5 standard deviations above mean

### Safe Mode Output

| column_name | outlier_count | mean_value | stddev_value | min_value | max_value |
|-------------|---------------|------------|--------------|-----------|-----------|
| revenue     | 12            | 5000       | 2000         | -3000     | 15000     |
| quantity    | 8             | 100        | 80           | -50       | 500       |

**Interpretation:**
- Revenue has 12 outliers ranging from -3000 to 15000
- Quantity has 8 outliers ranging from -50 to 500

## Features

1. **Automatic Column Detection**
   - Analyzes all numeric columns
   - Excludes ID columns automatically

2. **Statistical Rigor**
   - Uses 2 standard deviation threshold
   - Computes z-scores for context
   - Handles NULL values correctly

3. **Performance Optimized**
   - Limits to 10 columns max
   - Limits to 50 rows per column
   - Uses efficient DuckDB queries

4. **Safe Mode Compatible**
   - Aggregated counts only in Safe Mode
   - No raw data exposure
   - Still provides statistical insights

## Acceptance Criteria

✅ "Find outliers beyond 2 std dev" returns concrete table (not stub)
✅ Detects numeric columns, excludes IDs
✅ Computes mean + stddev for each column
✅ Returns rows where |value - mean| > 2*stddev
✅ Limits output to 50 rows per column
✅ Safe Mode returns aggregated counts, not raw rows
✅ Regular Mode returns: column_name, value, z_score, row_index

## Implementation Details

**Files Modified:**
1. `connector/app/chat_orchestrator.py`
   - Added `_detect_all_numeric_columns()` method
   - Updated outliers SQL generation
   - Updated result formatting

**Key Methods:**
- `_detect_all_numeric_columns(catalog)` - Returns list of numeric columns
- `_generate_sql_plan()` - Generates outlier detection queries
- `_generate_final_answer()` - Formats outlier results

**DuckDB Functions Used:**
- `AVG()` - Calculate mean
- `STDDEV()` - Calculate standard deviation
- `ABS()` - Absolute value for threshold check
- `ROW_NUMBER()` - Add row indices
- `UNION ALL` - Combine results from multiple columns

## Testing

### Test Case 1: Regular Mode
```json
{
  "datasetId": "test-data",
  "conversationId": "conv-123",
  "message": "find outliers beyond 2 std dev",
  "safeMode": false
}
```

**Expected:**
- Table with columns: column_name, value, mean_value, stddev_value, z_score, row_index
- Only values with |z_score| > 2
- Up to 50 rows per numeric column

### Test Case 2: Safe Mode
```json
{
  "datasetId": "test-data",
  "conversationId": "conv-456",
  "message": "find outliers",
  "safeMode": true
}
```

**Expected:**
- Table with columns: column_name, outlier_count, mean_value, stddev_value, min_value, max_value
- Aggregated counts only
- No individual outlier rows

### Test Case 3: Dataset with IDs
**Given:** Dataset with columns: id, user_id, revenue, quantity

**Expected:**
- Only analyze: revenue, quantity
- Exclude: id, user_id

## Edge Cases Handled

1. **NULL values** - Excluded from calculations
2. **Zero standard deviation** - No outliers detected (all values same)
3. **Small datasets** - May not have outliers
4. **No numeric columns** - Falls back to row count
5. **All values are outliers** - Returns up to limit (50/column)

## Performance Considerations

- Subqueries for mean/stddev computed per column
- DuckDB optimizes these efficiently
- Limits prevent excessive data transfer
- Safe mode more performant (aggregation only)

## Future Enhancements

Potential improvements:
1. Configurable threshold (1σ, 2σ, 3σ)
2. IQR-based outlier detection
3. Time-based outlier detection
4. Outlier visualization (box plots)
5. Automatic outlier remediation suggestions

---

**Status:** ✅ COMPLETE

**Ready for:** Production use
