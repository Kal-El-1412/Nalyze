# FIX-4: Remove Preview Queries from Analysis Plans - COMPLETE ✅

## Summary

Removed all "SELECT * LIMIT" preview queries from analysis plans. All analysis types now generate proper, intent-specific SQL queries with aggregation. The row_count analysis consistently uses `SELECT COUNT(*) as row_count FROM data`.

## Problem

Previously, when the catalog was not available or certain conditions were met, the system would fall back to "discover_columns" queries using `SELECT * FROM data LIMIT 1`. These preview queries:
- Were not actual analysis queries
- Could appear in the audit tab
- Confused users expecting real analysis SQL
- Were not appropriate as analysis plans

Additionally, the user requirement explicitly stated:
> For row_count, SQL must be SELECT COUNT(*) AS row_count FROM <table>

## Solution

Replaced all "discover_columns" fallback queries with proper aggregation queries:
- **Row count analysis**: Always uses `SELECT COUNT(*) as row_count FROM data`
- **All fallback cases**: Use row count query instead of SELECT * LIMIT
- **No preview queries**: Removed all discover_columns references

## What Changed

### Modified File: connector/app/chat_orchestrator.py

#### 1. Updated Import (Line 12)
Changed from `reports_storage` to `reports_local_storage` (aligning with FIX-3):

```python
# Before
from app.reports_storage import reports_storage

# After
from app.reports_local import reports_local_storage
```

#### 2. Top Categories Fallback (Lines 570-576)
Removed discover_columns query:

```python
# Before
else:
    queries.append({
        "name": "discover_columns",
        "sql": "SELECT * FROM data LIMIT 1"
    })
    explanation = f"I'll first discover the columns in your dataset, then show you the top categories for the {time_period} period."

# After
else:
    # No catalog available - return row count as safe fallback
    queries.append({
        "name": "row_count",
        "sql": "SELECT COUNT(*) as row_count FROM data"
    })
    explanation = f"I'll show you the total row count for the {time_period} period. Please ensure the dataset is ingested for detailed analysis."
```

#### 3. Trend Analysis Fallback (Lines 615-621)
Removed discover_columns query:

```python
# Before
else:
    queries.append({
        "name": "discover_columns",
        "sql": "SELECT * FROM data LIMIT 1"
    })
    explanation = f"I'll first discover the columns in your dataset, then show you the trends for the {time_period} period."

# After
else:
    # No catalog available - return row count as safe fallback
    queries.append({
        "name": "row_count",
        "sql": "SELECT COUNT(*) as row_count FROM data"
    })
    explanation = f"I'll show you the total row count for the {time_period} period. Please ensure the dataset is ingested for trend analysis."
```

#### 4. Outliers Analysis Fallback (Lines 685-691)
Removed discover_columns query:

```python
# Before
else:
    queries.append({
        "name": "discover_columns",
        "sql": "SELECT * FROM data LIMIT 1"
    })
    explanation = f"I'll first discover the columns in your dataset, then check for outliers for the {time_period} period."

# After
else:
    # No catalog available - return row count as safe fallback
    queries.append({
        "name": "row_count",
        "sql": "SELECT COUNT(*) as row_count FROM data"
    })
    explanation = f"I'll show you the total row count for the {time_period} period. Please ensure the dataset is ingested for outlier analysis."
```

#### 5. Data Quality Fallback (Lines 717-723)
Removed discover_columns query:

```python
# Before
else:
    queries.append({
        "name": "discover_columns",
        "sql": "SELECT * FROM data LIMIT 1"
    })
    explanation = f"I'll first discover the columns in your dataset, then check data quality."

# After
else:
    # No catalog available - return row count as safe fallback
    queries.append({
        "name": "row_count",
        "sql": "SELECT COUNT(*) as row_count FROM data"
    })
    explanation = f"I'll show you the total row count for the {time_period} period. Please ensure the dataset is ingested for data quality analysis."
```

#### 6. Updated Report Storage References (Lines 855, 1305)
Changed all `reports_storage.save_report` calls to `reports_local_storage.save_report` for consistency with FIX-3.

## Row Count Analysis

The row_count analysis was already correct but is now verified to be consistent:

```python
if analysis_type == "row_count":
    queries.append({
        "name": "row_count",
        "sql": "SELECT COUNT(*) as row_count FROM data"
    })
    explanation = "I'll count the total rows in your dataset."
```

**Key properties:**
- ✅ Uses `COUNT(*)` aggregation
- ✅ Returns result as `row_count` column
- ✅ No LIMIT clause needed
- ✅ Works regardless of catalog availability
- ✅ Never uses SELECT * LIMIT

## All Analysis Types Now Use Proper Queries

### Row Count
```sql
SELECT COUNT(*) as row_count FROM data
```

### Top Categories
```sql
SELECT "category_column" AS category, COUNT(*) as count
FROM data
GROUP BY "category_column"
ORDER BY count DESC
LIMIT 20
```
Fallback: Uses row count query

### Trend Analysis
```sql
SELECT
    DATE_TRUNC('month', "date_column") as month,
    COUNT(*) as count,
    SUM("metric_column") as total_metric,
    AVG("metric_column") as avg_metric
FROM data
GROUP BY month
ORDER BY month
LIMIT 200
```
Fallback: Uses row count query

### Outliers (Safe Mode)
```sql
SELECT
    'column_name' as column_name,
    COUNT(*) as outlier_count,
    AVG("column") as mean_value,
    STDDEV("column") as stddev_value,
    MIN("column") as min_value,
    MAX("column") as max_value
FROM data
WHERE "column" IS NOT NULL
  AND ABS("column" - (SELECT AVG("column") FROM data WHERE "column" IS NOT NULL))
      > 2 * (SELECT STDDEV("column") FROM data WHERE "column" IS NOT NULL)
```
Fallback: Uses row count query

### Data Quality
```sql
-- Null counts
SELECT COUNT(*) as total_rows,
       SUM(CASE WHEN "col1" IS NULL THEN 1 ELSE 0 END) as "col1_nulls",
       SUM(CASE WHEN "col2" IS NULL THEN 1 ELSE 0 END) as "col2_nulls"
FROM data

-- Duplicate check
SELECT COUNT(*) as total_rows, COUNT(DISTINCT *) as unique_rows
FROM data
```
Fallback: Uses row count query

## Verification

### No discover_columns References

```bash
$ grep -n "discover_columns" connector/app/chat_orchestrator.py
# No results - all removed ✅
```

### No SELECT * LIMIT in Analysis Plans

```bash
$ grep -n "SELECT \* FROM data LIMIT" connector/app/chat_orchestrator.py
121:- **NO RAW ROWS**: You cannot generate queries that return individual rows like "SELECT * FROM data LIMIT 10"
# Only reference is in the system prompt as an example of what NOT to do ✅
```

### Row Count Uses COUNT(*)

```bash
$ grep -A2 "row_count" connector/app/chat_orchestrator.py | grep "sql"
"sql": "SELECT COUNT(*) as row_count FROM data"
# All instances use COUNT(*) ✅
```

## Testing

### Created Test File

**connector/test_fix4_no_preview_in_analysis.py**

Tests cover:
1. **Row count uses COUNT(*)** - Verifies exact SQL
2. **No discover_columns fallback** - Tests all analysis types with no catalog
3. **All queries use aggregation** - Verifies aggregation in all queries
4. **Audit shows correct SQL** - Ensures audit tab will display proper SQL

### Run Tests

```bash
cd connector
python3 test_fix4_no_preview_in_analysis.py
```

**Expected output:**
```
==================================================
FIX-4: No Preview Queries in Analysis Plans
==================================================

Test 1: Row Count Uses COUNT(*)
--------------------------------------------------
Query name: row_count
Query SQL: SELECT COUNT(*) as row_count FROM data
✅ PASS: row_count uses SELECT COUNT(*) as row_count FROM data
   NOT SELECT * LIMIT 100
   NOT SELECT * LIMIT 10

Test 2: No discover_columns Fallback Queries
--------------------------------------------------
✅ top_categories: row_count
   SQL: SELECT COUNT(*) as row_count FROM data...
✅ trend: row_count
   SQL: SELECT COUNT(*) as row_count FROM data...
✅ outliers: row_count
   SQL: SELECT COUNT(*) as row_count FROM data...
✅ data_quality: row_count
   SQL: SELECT COUNT(*) as row_count FROM data...

✅ PASS: All analysis types use proper aggregation queries
   No discover_columns fallbacks
   No SELECT * LIMIT in analysis plans

Test 3: All Queries Use Aggregation
--------------------------------------------------
✅ row_count.row_count uses aggregation
✅ top_categories.top_categories uses aggregation
✅ trend.monthly_trend uses aggregation
✅ outliers.outliers_detected uses aggregation
✅ data_quality.null_counts uses aggregation

✅ PASS: All queries use aggregation

Test 4: Audit Shows Correct SQL for Row Count
--------------------------------------------------
✅ Query name: row_count
✅ Query SQL: SELECT COUNT(*) as row_count FROM data
✅ PASS: Audit will show correct SQL, not preview query

==================================================
TEST SUMMARY
==================================================
✅ PASS: Row Count Uses COUNT(*)
✅ PASS: No discover_columns Fallback
✅ PASS: All Queries Use Aggregation
✅ PASS: Audit Shows Correct SQL

✅ ALL TESTS PASSED

Acceptance Criteria Met:
✅ row_count uses SELECT COUNT(*) as row_count FROM data
✅ No SELECT * LIMIT 100 in any analysis plan
✅ No discover_columns fallback queries
✅ All queries use proper aggregation
✅ Audit tab will show correct SQL, not preview queries
```

## Acceptance Criteria Verification

### ✅ Audit tab never shows SELECT * LIMIT 100 for "row count"

**Before:**
- Possible to see discover_columns with SELECT * LIMIT 1
- Inconsistent SQL in audit trail

**After:**
- Row count always uses `SELECT COUNT(*) as row_count FROM data`
- Audit tab will show the actual analysis SQL
- No preview queries in analysis plans

**Testing:**
```bash
# 1. Start connector
cd connector && python3 -m app.main

# 2. In UI, ask: "How many rows?"
# 3. Check Audit tab
# 4. Verify SQL shows: SELECT COUNT(*) as row_count FROM data
# 5. Verify it does NOT show: SELECT * FROM data LIMIT 100
```

### ✅ For row_count, SQL must be SELECT COUNT(*) AS row_count FROM table

**Current implementation (line 551):**
```python
"sql": "SELECT COUNT(*) as row_count FROM data"
```

**Verification:**
- Uses `COUNT(*)` aggregation ✅
- Returns column named `row_count` ✅
- Queries `FROM data` table ✅
- No LIMIT clause needed ✅
- Consistent across all code paths ✅

### ✅ Do not use preview query as an analysis plan

**Changes made:**
- Removed all `discover_columns` queries
- All fallback cases use row count instead
- No `SELECT * FROM data LIMIT` in any analysis path

**Verification:**
```python
# Search for preview queries
grep -n "SELECT \* FROM data LIMIT" app/chat_orchestrator.py
# Result: Only in system prompt as example of what NOT to do

# Search for discover_columns
grep -n "discover_columns" app/chat_orchestrator.py
# Result: No matches
```

### ✅ Generate intent-appropriate SQL for all analysis types

Each analysis type now generates appropriate SQL:

| Analysis Type | SQL Generated | Aggregation |
|--------------|---------------|-------------|
| row_count | SELECT COUNT(*) | ✅ COUNT |
| top_categories | SELECT category, COUNT(*) GROUP BY | ✅ COUNT + GROUP BY |
| trend | SELECT month, COUNT(*), SUM(), AVG() GROUP BY | ✅ Multiple aggregations |
| outliers | SELECT with STDDEV, AVG, z-score | ✅ Statistical aggregations |
| data_quality | SELECT with null counts, duplicates | ✅ CASE + COUNT |

**All queries:**
- Use proper aggregation
- Are specific to the analysis intent
- Never use generic preview queries
- Include appropriate LIMIT clauses where needed

## Benefits

### 1. Consistent SQL Generation
- Row count always uses COUNT(*)
- No ambiguity about what SQL will be generated
- Predictable audit trail

### 2. Better User Experience
- Audit tab shows actual analysis SQL
- Users can understand what queries ran
- No confusion about preview vs analysis queries

### 3. Proper Fallback Behavior
- When catalog unavailable, returns row count
- Still provides useful information
- Encourages proper dataset ingestion

### 4. Cleaner Code
- Removed unused discover_columns logic
- Simplified fallback cases
- Consistent error messages

## Manual Testing Checklist

### Test 1: Row Count Query
- [ ] Start connector
- [ ] Upload and ingest dataset
- [ ] Ask: "How many rows?"
- [ ] Check response includes count
- [ ] Open Audit tab
- [ ] Verify SQL shows: `SELECT COUNT(*) as row_count FROM data`
- [ ] Verify it does NOT show: `SELECT * FROM data LIMIT`

### Test 2: All Analysis Types
For each analysis type (top_categories, trend, outliers, data_quality):
- [ ] Run analysis
- [ ] Check Audit tab
- [ ] Verify SQL uses aggregation (COUNT, SUM, AVG, etc.)
- [ ] Verify NO `SELECT * FROM data LIMIT` queries

### Test 3: Fallback Without Catalog
- [ ] Upload dataset but don't ingest
- [ ] Try to run analysis
- [ ] System should return row count
- [ ] Verify SQL is `SELECT COUNT(*)`
- [ ] Verify user sees message about ingesting dataset

### Test 4: Safe Mode Compatibility
- [ ] Enable Safe Mode
- [ ] Run row count analysis
- [ ] Verify still uses COUNT(*)
- [ ] Verify no raw rows returned

## Related Changes

This fix is compatible with:
- **FIX-3**: Uses `reports_local_storage` for report persistence
- **Safe Mode**: All queries use aggregation (Safe Mode compatible)
- **Privacy Mode**: Works with PII redaction
- **Deterministic Router**: Routes row_count correctly

## Edge Cases Handled

### 1. No Catalog Available
- **Before**: Would generate discover_columns query
- **After**: Returns row count with message to ingest dataset

### 2. No Suitable Columns Found
- **Before**: Would fallback to discover_columns
- **After**: Returns row count with appropriate explanation

### 3. Empty Dataset
- **Before**: discover_columns would return no results
- **After**: COUNT(*) returns 0 (correct)

### 4. Multiple Analysis Types in Sequence
- **Before**: Could see mix of preview and analysis queries
- **After**: All queries are proper analysis queries

## Build Status

```bash
# Python syntax check
cd connector
python3 -m py_compile app/chat_orchestrator.py
# ✅ No errors

# Frontend build
npm run build
# ✅ Built successfully

# Test suite
python3 test_fix4_no_preview_in_analysis.py
# ✅ All tests pass
```

## Documentation Updates

Created/updated:
- ✅ `FIX-4_COMPLETE.md` - This document
- ✅ `test_fix4_no_preview_in_analysis.py` - Test suite
- ✅ `app/chat_orchestrator.py` - Updated with inline comments

## Summary of SQL Changes

### Removed Queries
```sql
-- ❌ REMOVED: discover_columns fallback
SELECT * FROM data LIMIT 1
```

### Added Fallbacks
```sql
-- ✅ ADDED: Proper row count fallback
SELECT COUNT(*) as row_count FROM data
```

### Unchanged (Already Correct)
```sql
-- ✅ Row count (already correct)
SELECT COUNT(*) as row_count FROM data

-- ✅ Top categories (already correct)
SELECT "category" AS category, COUNT(*) as count
FROM data GROUP BY "category" ORDER BY count DESC LIMIT 20

-- ✅ Trend analysis (already correct)
SELECT DATE_TRUNC('month', "date") as month, COUNT(*) as count
FROM data GROUP BY month ORDER BY month LIMIT 200

-- ✅ Outliers (already correct)
-- Complex aggregation query with STDDEV, AVG, etc.

-- ✅ Data quality (already correct)
SELECT COUNT(*) as total_rows,
       SUM(CASE WHEN col IS NULL THEN 1 ELSE 0 END) as col_nulls
FROM data
```

## Conclusion

✅ **All acceptance criteria met**
✅ **No breaking changes**
✅ **All analysis types generate proper SQL**
✅ **Row count consistently uses COUNT(*)**
✅ **No preview queries in analysis plans**
✅ **Test suite validates behavior**
✅ **Backward compatible with existing features**

The chat orchestrator now generates intent-appropriate, aggregated SQL for all analysis types, with no reliance on preview queries. The audit tab will show users exactly what SQL was executed for their analysis.
