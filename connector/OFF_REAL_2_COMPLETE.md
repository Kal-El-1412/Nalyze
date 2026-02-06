# OFF-REAL-2: Deterministic Intent Mapping

## Status: ✅ COMPLETE

## Summary

The deterministic router now has comprehensive keyword mapping rules that correctly identify user intent without needing AI assistance. All specified keywords map to their respective analysis types with high confidence (≥ 0.8).

## Changes Made

### Enhanced Keyword Patterns (router.py:21-121)

#### 1. Row Count Keywords (Moved to First Priority)

**Before:**
```python
"row_count": {
    "strong": [
        r"\bhow many\s+\w+\s+rows?\b",
        r"\bhow many rows?\b",
        r"\bcount(?:ing)? rows?\b",
        r"\brow count\b",
        # ...
    ],
    # ...
}
```

**After:**
```python
"row_count": {
    "strong": [
        r"\brow count\b",
        r"\bcount\s+(?:the\s+)?rows?\b",  # Catches "count rows" and "count the rows"
        r"\bhow many rows?\b",
        r"\btotal rows?\b",
        r"\bnumber of rows?\b",
        r"\brecord count\b",
        r"\bhow many records?\b",
        r"\btotal records?\b",
        r"\bcount(?:ing)?\s+of\s+rows?\b",
    ],
    "weak": [
        r"\bhow many\b",
        r"\bcount\b",
        r"\btotal\b",
        r"\bsize\b",
    ]
}
```

**Rationale:**
- Moved row_count to first position for clarity and priority
- Simplified patterns to match required keywords: "row count", "count rows", "how many rows"
- Added pattern to catch "count the rows" variations
- All patterns map with confidence ≥ 0.90

#### 2. Trend Keywords (Enhanced with Week/Month-over-Week/Month)

**Before:**
```python
"trend": {
    "strong": [
        r"\btrend(?:s|ing)?\b",
        r"\bover time\b",
        r"\bmonthly\b",
        r"\bweekly\b",
        # ...
    ],
}
```

**After:**
```python
"trend": {
    "strong": [
        r"\btrend(?:s|ing)?\b",
        r"\bover time\b",
        r"\bmonthly\b",
        r"\bweekly\b",
        r"\bweek[- ]over[- ]week\b",  # NEW: week-over-week, week over week
        r"\bmonth[- ]over[- ]month\b",  # NEW: month-over-month, month over month
        r"\bw[o0][w]?\b",  # NEW: wow abbreviation
        r"\bm[o0]m\b",  # NEW: mom abbreviation
        r"\bdaily\b",
        r"\bquarterly\b",
        r"\byearly\b",
        r"\btime series\b",
        r"\bchanges? over\b",
        r"\bgrow(?:th|ing)\b",
    ],
    "weak": [
        r"\bhistor(?:y|ical)\b",
        r"\bprogress\b",
        r"\bevolution\b",
        r"\bpattern\b",
    ]
}
```

**Rationale:**
- Added patterns for "week-over-week" and "month-over-month" (with hyphen or space)
- Added support for "wow" and "mom" abbreviations
- All required keywords now map with confidence ≥ 0.90

#### 3. Outliers Keywords (Added 2 Standard Deviations)

**Before:**
```python
"outliers": {
    "strong": [
        r"\boutlier(?:s)?\b",
        r"\banomal(?:y|ies)\b",
        r"\bstd dev\b",
        r"\bstandard deviation\b",
        r"\bz-?score\b",
        # ...
    ],
}
```

**After:**
```python
"outliers": {
    "strong": [
        r"\boutlier(?:s)?\b",
        r"\banomal(?:y|ies)\b",
        r"\b2\s+std(?:\.?|ev)?\b",  # NEW: 2 std, 2 stddev, 2 std.
        r"\b2\s+standard deviations?\b",  # NEW: 2 standard deviation(s)
        r"\bstd dev\b",
        r"\bstandard deviation\b",
        r"\bz[- ]?score\b",  # Enhanced: z-score, zscore, z score
        r"\bunusual\b",
        r"\babnorm?al\b",
    ],
    "weak": [
        r"\bextreme\b",
        r"\bodd\b",
        r"\bweird\b",
        r"\bspike(?:s)?\b",
    ]
}
```

**Rationale:**
- Added patterns for "2 standard deviations" and "2 std dev"
- Enhanced z-score pattern to catch "z-score", "zscore", and "z score"
- All required keywords now map with confidence ≥ 0.90

### Existing Behavior Confirmed

The router already correctly:
- Returns `analysis_type=None` when no pattern matches (confidence < 0.5)
- Returns `analysis_type=None` when confidence is between 0.5-0.8 (medium confidence)
- Only returns an analysis_type when confidence ≥ 0.8 (high confidence via strong keyword match)

The chat orchestrator (chat_orchestrator.py:328-421) already correctly:
- Uses deterministic path when confidence ≥ 0.8 → generates SQL immediately
- Returns `needs_clarification` when confidence < 0.8 and AI Assist is OFF
- Never returns a generic `final_answer` without query results (from OFF-REAL-1)

## Behavior Changes

### AI Assist OFF Mode - Keyword Mapping

| User Message | Before | After |
|--------------|--------|-------|
| "row count" | ✅ row_count (0.95) | ✅ row_count (0.95) |
| "count rows" | ✅ row_count (0.95) | ✅ row_count (0.95) |
| "how many rows" | ✅ row_count (0.95) | ✅ row_count (0.95) |
| "count the rows" | ⚠️ row_count (0.60) → clarification | ✅ row_count (0.95) → direct |
| "trend" | ✅ trend (0.90) | ✅ trend (0.90) |
| "over time" | ✅ trend (0.90) | ✅ trend (0.90) |
| "monthly" | ✅ trend (0.90) | ✅ trend (0.90) |
| "weekly" | ✅ trend (0.90) | ✅ trend (0.90) |
| "week-over-week" | ❌ None → clarification | ✅ trend (0.90) → direct |
| "month-over-month" | ❌ None → clarification | ✅ trend (0.90) → direct |
| "outliers" | ✅ outliers (0.90) | ✅ outliers (0.90) |
| "anomalies" | ✅ outliers (0.90) | ✅ outliers (0.90) |
| "2 standard deviations" | ❌ None → clarification | ✅ outliers (0.90) → direct |
| "z-score" | ✅ outliers (0.90) | ✅ outliers (0.90) |
| "show me something" | ✅ None (0.00) → clarification | ✅ None (0.00) → clarification |

## Acceptance Criteria

✅ **Typing "row count" never returns clarification**
- "row count" maps to row_count with confidence 0.95
- Triggers deterministic path (confidence ≥ 0.8)
- Proceeds directly to run_queries
- Never returns needs_clarification

✅ **Typing "row count" never returns generic template**
- Combined with OFF-REAL-1 changes
- No canned summaries without query results
- Only real data-based summaries returned

✅ **All required keywords map correctly**
- Row count: "row count", "count rows", "how many rows" → confidence ≥ 0.90
- Trend: "trend", "over time", "monthly", "weekly", "week-over-week", "month-over-month" → confidence ≥ 0.90
- Outliers: "outliers", "anomalies", "2 standard deviations", "z-score" → confidence ≥ 0.90

✅ **No match returns needs_clarification**
- Unclear messages return analysis_type=None
- Triggers needs_clarification in chat orchestrator (AI Assist OFF)
- Never returns final_answer without results

## Testing

Run test suite:
```bash
cd connector
python3 test_deterministic_keywords.py
```

Expected output:
```
✅ PASS: Row count keywords
✅ PASS: Trend keywords
✅ PASS: Outliers keywords
✅ PASS: No match returns None
✅ PASS: CRITICAL: 'row count' maps directly
✅ PASS: Top categories keywords
✅ PASS: Data quality keywords
```

## Flow Diagram

### AI Assist OFF - "row count" Message

```
User: "row count"
   ↓
Deterministic Router
   ↓
Match: row_count (confidence 0.95)
   ↓
confidence >= 0.8 ✅
   ↓
Set analysis_type="row_count", time_period="all_time"
   ↓
Generate SQL: "SELECT COUNT(*) as row_count FROM data"
   ↓
Return run_queries (NOT needs_clarification)
   ↓
Frontend executes via /queries/execute
   ↓
Frontend sends resultsContext back
   ↓
Backend generates final_answer with actual count
```

### AI Assist OFF - "show me something" Message

```
User: "show me something"
   ↓
Deterministic Router
   ↓
No match found (confidence 0.00)
   ↓
analysis_type = None
   ↓
confidence < 0.8 ❌
   ↓
AI Assist is OFF
   ↓
Return needs_clarification with choices:
  - Trends over time
  - Top categories
  - Find outliers
  - Count rows
  - Check data quality
```

## Files Modified

- `connector/app/router.py`
  - Lines 21-121: Enhanced keyword patterns for all analysis types
  - Reordered patterns (row_count first for clarity)
  - Added week-over-week, month-over-month patterns
  - Added 2 standard deviations patterns
  - Enhanced z-score pattern

## Files Added

- `connector/test_deterministic_keywords.py` - Comprehensive test suite
- `connector/OFF_REAL_2_COMPLETE.md` - This document

## Related Requirements

- OFF-REAL-1 (No canned summaries) - Compatible and complementary
- Prompt 4 (row_count never asks for time period) - Already implemented
- HR6 (JSON-only responses) - Compatible
- HR7 (No repeated clarifications) - Compatible
- Safe Mode - Compatible (works with aggregates)
- Privacy Mode - Compatible (works with redacted schemas)

## Keyword Mapping Reference

### Row Count
- ✅ "row count"
- ✅ "count rows"
- ✅ "count the rows"
- ✅ "how many rows"
- ✅ "total rows"
- ✅ "number of rows"
- ✅ "record count"
- ✅ "how many records"
- ✅ "total records"

### Trend
- ✅ "trend" / "trends" / "trending"
- ✅ "over time"
- ✅ "monthly"
- ✅ "weekly"
- ✅ "week-over-week" / "week over week"
- ✅ "month-over-month" / "month over month"
- ✅ "daily"
- ✅ "quarterly"
- ✅ "yearly"
- ✅ "time series"
- ✅ "changes over"
- ✅ "growth" / "growing"

### Outliers
- ✅ "outliers" / "outlier"
- ✅ "anomalies" / "anomaly"
- ✅ "2 standard deviations" / "2 standard deviation"
- ✅ "2 std dev" / "2 std" / "2 stddev"
- ✅ "z-score" / "zscore" / "z score"
- ✅ "standard deviation"
- ✅ "std dev"
- ✅ "unusual"
- ✅ "abnormal"

### Top Categories
- ✅ "top categories"
- ✅ "top 10" / "top 5" (any number)
- ✅ "breakdown by category"
- ✅ "grouped by"
- ✅ "highest"
- ✅ "ranked"

### Data Quality
- ✅ "missing values"
- ✅ "nulls"
- ✅ "duplicates"
- ✅ "data quality"
- ✅ "check data"
- ✅ "validate"
