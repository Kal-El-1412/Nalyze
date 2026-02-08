# Row Count Summary Fix - Dynamic Count Display

## Problem
Row count queries were returning generic "analysis complete" text instead of showing the actual number of rows in the Summary tab.

## Solution
Updated `_summarize_row_count()` in `connector/app/summarizer.py` to:

1. **Find the row_count column by name** (case-insensitive lookup)
2. **Extract the actual count value** from query results
3. **Format with thousands separator** for readability (e.g., 1,748 instead of 1748)
4. **Use consistent format**: "This dataset has **X** rows."

## Code Changes

**File**: `connector/app/summarizer.py`
**Method**: `_summarize_row_count()` (lines 60-95)

### Key Improvements

**Before:**
```python
# Extract count from first row, first column
count = rows[0][0] if len(rows[0]) > 0 else 0
return f"**Row count:** {count:,} rows"
```

**After:**
```python
# Try to find row_count column by name (case-insensitive)
count = None
cols_lower = [c.lower() for c in columns] if columns else []

if "row_count" in cols_lower:
    idx = cols_lower.index("row_count")
    count = rows[0][idx] if len(rows[0]) > idx else None
elif cols_lower and len(rows[0]) > 0:
    # Fallback: use first column
    count = rows[0][0]

return f"## Row count\n\nThis dataset has **{count:,}** rows."
```

## Examples

### Dataset with 1,748 rows
```markdown
## Row count

This dataset has **1,748** rows.
```

### Large dataset with 1,234,567 rows
```markdown
## Row count

This dataset has **1,234,567** rows.
```

### Empty dataset
```markdown
## Row count

This dataset is empty (0 rows).
```

## Testing

### Automated Tests
Run: `python3 connector/test_row_count_summary.py`

Tests verify:
- ✅ Extracts count from `row_count` column
- ✅ Falls back to first column if needed
- ✅ Formats large numbers with thousands separators
- ✅ Handles empty datasets gracefully
- ✅ Never shows generic "analysis complete" text

### UI Acceptance Test
1. Open the application
2. Load a dataset
3. Ask: "How many rows?"
4. Click "Row count" option (if prompted)
5. **Expected Results:**
   - Summary tab shows: "This dataset has **X** rows."
   - Tables tab shows the row count table
   - Count must match actual dataset size

### API Test
```bash
# Start connector
cd connector && ./run.sh

# In another terminal, run:
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "test_dataset",
    "conversationId": "test_conv",
    "intent": "set_analysis_type",
    "value": "Row count"
  }'
```

Expected response includes:
```json
{
  "type": "run_queries",
  "queries": [{
    "name": "row_count",
    "sql": "SELECT COUNT(*) as row_count FROM data"
  }]
}
```

After query execution, send results back:
```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "test_dataset",
    "conversationId": "test_conv",
    "resultsContext": {
      "tables": [{
        "name": "row_count",
        "columns": ["row_count"],
        "rows": [[1748]]
      }]
    }
  }'
```

Expected `summaryMarkdown` field:
```markdown
## Row count

This dataset has **1,748** rows.
```

## Benefits
- Users see the actual row count immediately in the Summary tab
- Large numbers are formatted for easy reading
- Consistent, professional presentation
- No more generic placeholder text
- Works with any column name (looks for `row_count` first, falls back to first column)
