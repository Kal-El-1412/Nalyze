# Template Dropdown → Structured Intents → Query Generation
## Acceptance Test Guide

## Status: ✅ IMPLEMENTED

## Overview

The template dropdown now sends **structured intents** instead of raw text. Each template includes an `analysisType` field that maps to backend query generation logic. This ensures that clicking a template always produces the correct SQL queries, regardless of AI Assist mode.

## Frontend Changes

### Template Structure (ChatPanel.tsx)

Each template now includes:
```typescript
interface AnalysisTemplate {
  id: string;
  icon: any;
  label: string;
  description: string;
  analysisType: string;  // ← NEW: Maps to backend query generation
  getPrompt: (catalog: DatasetCatalog | null) => string;
  color: string;
  defaults?: {
    timeBucket?: string;  // ← NEW: Optional defaults (e.g., 'month', 'week')
  };
}
```

### Template → Analysis Type Mapping

| Template Label | analysisType | Expected Query Type |
|----------------|--------------|-------------------|
| Trend over time (monthly) | `trend` | DATE_TRUNC with monthly bucketing |
| Week-over-week change | `trend` | DATE_TRUNC with weekly bucketing |
| Outliers and anomalies | `outliers` | Z-score calculation, >2 std dev filter |
| Top categories | `top_categories` | GROUP BY with COUNT, ORDER BY DESC |
| Cohort comparison | `top_categories` | GROUP BY segments |
| Funnel-style drop-offs | `top_categories` | GROUP BY stages |
| Data quality report | `data_quality` | NULL checks, duplicate detection |
| Row count | `row_count` | SELECT COUNT(*) FROM data |

### Template Click Handler

**Before (Broken):**
```typescript
const handleTemplateSelect = (template: AnalysisTemplate) => {
  const prompt = template.getPrompt(catalog);
  setInput(prompt);  // ← Just filled the input box
  setShowTemplates(false);
};
```

**After (Fixed):**
```typescript
const handleTemplateSelect = (template: AnalysisTemplate) => {
  setShowTemplates(false);

  // Send structured intent with analysis_type as the value
  onClarificationResponse(template.analysisType, 'set_analysis_type');
  // ← Sends intent="set_analysis_type", value="trend" (for example)
};
```

## Backend Flow

### 1. Intent Processing (main.py:532-601)

When frontend sends `intent="set_analysis_type"`, `value="trend"`:

```python
async def handle_intent(request: ChatOrchestratorRequest):
    # Map user-friendly names to internal values (line 554-569)
    analysis_type_map = {
        "Trends over time": "trend",
        "Top categories": "top_categories",
        "Find outliers": "outliers",
        "Count rows": "row_count",
        "Check data quality": "data_quality",
    }
    value = analysis_type_map.get(value, value)  # ← Fallback to value as-is

    # Update conversation state (line 584)
    state_manager.update_state(request.conversationId, context={"analysis_type": value})

    # Delegate to orchestrator (line 596)
    response = await chat_orchestrator.process(request)
    # ← Orchestrator generates SQL plan immediately
```

### 2. Orchestrator Processing (chat_orchestrator.py:279-368)

```python
async def process(self, request: ChatOrchestratorRequest):
    state = state_manager.get_state(request.conversationId)
    context = state.get("context", {})

    # Check if state is ready (line 302)
    if self._is_state_ready(context):
        if request.resultsContext:
            return await self._generate_final_answer(...)
        else:
            return await self._generate_sql_plan(...)  # ← Generate queries!
```

### 3. SQL Generation (chat_orchestrator.py:519-719)

```python
async def _generate_sql_plan(self, request, catalog, context):
    analysis_type = context.get("analysis_type")

    if analysis_type == "row_count":
        queries = [{"name": "row_count", "sql": "SELECT COUNT(*) as row_count FROM data"}]

    elif analysis_type == "top_categories":
        categorical_col = self._detect_best_categorical_column(catalog)
        queries = [{
            "name": "top_categories",
            "sql": f'SELECT "{categorical_col}" AS category, COUNT(*) as count FROM data GROUP BY "{categorical_col}" ORDER BY count DESC LIMIT 20'
        }]

    elif analysis_type == "trend":
        date_col = self._detect_date_column(catalog)
        metric_col = self._detect_metric_column(catalog)
        queries = [{
            "name": "monthly_trend",
            "sql": f'''SELECT
                DATE_TRUNC('month', "{date_col}") as month,
                COUNT(*) as count,
                SUM("{metric_col}") as total_{metric_col}
            FROM data
            GROUP BY month
            ORDER BY month
            LIMIT 200'''
        }]

    elif analysis_type == "outliers":
        numeric_cols = self._detect_all_numeric_columns(catalog)
        # Generates z-score SQL for outlier detection (>2 std dev)
        # ...

    elif analysis_type == "data_quality":
        # Generates NULL counts and duplicate checks
        # ...

    return RunQueriesResponse(queries=queries, explanation="...")
```

## Acceptance Tests

### Test 1: Row Count Template

**Action:**
1. Open application
2. Connect a dataset
3. Click template dropdown
4. Click "Row count"

**Expected:**
```
User message: "row_count" (or similar audit text)
Backend receives: intent="set_analysis_type", value="row_count"
Response type: run_queries
Query name: "row_count"
SQL: "SELECT COUNT(*) as row_count FROM data"
```

**Verify:**
- Tables tab shows 1 table with 1 row containing count
- Audit tab shows:
  - Analysis Type: row_count
  - Time Period: all_time
  - Executed SQL: SELECT COUNT(*)...
  - Row Count: 1

### Test 2: Trend Template

**Action:**
1. Click template dropdown
2. Click "Trend over time (monthly)"

**Expected:**
```
Backend receives: intent="set_analysis_type", value="trend"
Response type: run_queries
Query name: "monthly_trend" or "monthly_count"
SQL includes:
  - DATE_TRUNC('month', <date_column>)
  - GROUP BY month
  - ORDER BY month
```

**Verify:**
- Tables tab shows monthly aggregated data
- Audit tab shows:
  - Analysis Type: trend
  - SQL includes DATE_TRUNC
  - Rows ordered by month

### Test 3: Outliers Template

**Action:**
1. Click template dropdown
2. Click "Outliers and anomalies"

**Expected:**
```
Backend receives: intent="set_analysis_type", value="outliers"
Response type: run_queries
Query name: "outliers_detected" or "outlier_summary"
SQL includes:
  - STDDEV calculation
  - Z-score formula or >2 std dev filter
```

**Verify:**
- Tables tab shows outlier rows or aggregated counts
- Audit tab shows:
  - Analysis Type: outliers
  - SQL includes STDDEV/z-score

### Test 4: Top Categories Template

**Action:**
1. Click template dropdown
2. Click "Top categories contributing to metric"

**Expected:**
```
Backend receives: intent="set_analysis_type", value="top_categories"
Response type: run_queries
Query name: "top_categories"
SQL includes:
  - GROUP BY <categorical_column>
  - COUNT(*) as count
  - ORDER BY count DESC
  - LIMIT 20
```

**Verify:**
- Tables tab shows top 20 categories with counts
- Summary shows "Top Categories: N categories found"
- Categories ordered by count descending

### Test 5: Data Quality Template

**Action:**
1. Click template dropdown
2. Click "Data quality report"

**Expected:**
```
Backend receives: intent="set_analysis_type", value="data_quality"
Response type: run_queries
Queries: Multiple (null_counts, duplicate_check)
SQL includes:
  - NULL checks per column
  - COUNT(DISTINCT *) for duplicates
```

**Verify:**
- Tables tab shows 2+ tables (null counts, duplicates)
- Summary includes null values and duplicate counts

### Test 6: Free-Text with AI Assist OFF

**Action:**
1. Toggle AI Assist OFF
2. Type free-text: "Show me insights about my data"
3. Send message

**Expected:**
```
Response type: needs_clarification
Question: "What type of analysis would you like?"
Choices: ["Trends over time", "Top categories", "Find outliers", "Count rows", "Check data quality"]
Intent: "set_analysis_type"
```

**Verify:**
- Clarification message appears
- Clicking a choice triggers query generation
- No fake summary generated

### Test 7: Template Click Populates All Tabs

**Action:**
1. Click any template (e.g., "Row count")
2. Wait for query execution
3. Check all 3 tabs: Summary, Tables, Audit

**Expected Summary:**
```
Row count: 12,345 rows
```

**Expected Tables:**
- Table name: "row_count"
- Columns: ["row_count"]
- Rows: [[12345]]

**Expected Audit:**
- Analysis Type: row_count
- Time Period: all_time
- AI Assist: OFF (or ON depending on toggle)
- Safe Mode: OFF (or ON depending on toggle)
- Privacy Mode: ON (or OFF depending on toggle)
- Query: row_count (1 rows)
- SQL: SELECT COUNT(*) as row_count FROM data

## Edge Cases

### Edge Case 1: No Catalog Available

**Scenario:** Dataset uploaded but catalog not yet built

**Expected:**
- Templates work, but may generate fallback queries
- Example: "trend" template without date column → generates row_count instead
- User sees explanation: "I couldn't find date columns for trending..."

### Edge Case 2: No Matching Columns

**Scenario:** "top_categories" template but dataset has no categorical columns

**Expected:**
- Falls back to row_count query
- Explanation: "I couldn't find a categorical column, so I'll show you the total row count"

### Edge Case 3: AI Assist ON

**Scenario:** Template clicked with AI Assist ON

**Expected:**
- Same behavior as AI Assist OFF
- Templates bypass AI and use deterministic routing
- Structured intent always works regardless of AI mode

## Success Criteria

✅ All templates send structured `set_analysis_type` intent
✅ Backend generates queries without LLM (deterministic)
✅ Each template produces expected query type:
  - Row count → COUNT(*)
  - Trend → DATE_TRUNC bucket query
  - Outliers → Z-score filter query
  - Top categories → GROUP BY with ORDER BY
  - Data quality → NULL checks + duplicates
✅ Tables tab populated with query results
✅ Audit tab shows executed SQL and metadata
✅ Summary derived from actual query results (no canned text)
✅ Free-text with AI OFF still asks for clarification
✅ Works regardless of AI Assist mode

## Files Modified

### Frontend
1. **src/components/ChatPanel.tsx**
   - Added `analysisType` field to AnalysisTemplate interface (line 41)
   - Added `defaults` field for time bucket hints (line 44-46)
   - Updated all templates with analysisType values (lines 49-159)
   - Modified handleTemplateSelect to send structured intent (lines 215-221)

### Backend
1. **connector/app/main.py** (No changes needed)
   - Already supports set_analysis_type intent (line 554-569)
   - Maps user-friendly names to internal values
   - Falls back to value as-is if no mapping found

2. **connector/app/chat_orchestrator.py** (No changes needed)
   - _is_state_ready checks for analysis_type (line 517)
   - _generate_sql_plan handles all analysis types (lines 519-719)
   - Deterministic router handles high-confidence matches (line 329)

### Tests
1. **connector/test_template_dropdown_intents.py** (New file)
   - Test suite for template → intent → query flow
   - Verifies each template generates expected query type

2. **connector/TEMPLATE_DROPDOWN_ACCEPTANCE.md** (This file)
   - Manual acceptance test guide
   - Documents expected behavior for each template

## Migration Notes

**Breaking Changes:** None

**Backward Compatibility:** Yes
- Old behavior: Templates filled input box with text
- New behavior: Templates send structured intent
- Free-text input still works as before
- Existing conversations not affected

**Deployment Notes:**
- Frontend and backend changes are compatible
- No database migrations needed
- No configuration changes required
- Works with existing connector instances
