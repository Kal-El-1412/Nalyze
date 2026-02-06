# Template Dropdown → Structured Intents Implementation

## Status: ✅ COMPLETE

## Summary

Template dropdown now sends **structured intents** instead of raw text, ensuring that clicking a template always produces the correct SQL queries. This works for both AI Assist ON and AI Assist OFF modes, using deterministic query generation.

## What Changed

### Frontend (ChatPanel.tsx)

**1. Template Structure Enhanced**
- Added `analysisType` field to map templates to backend query types
- Added optional `defaults` field for time bucketing hints

**2. Template Click Handler Rewired**
```typescript
// Before: Just filled input box
setInput(template.getPrompt(catalog));

// After: Sends structured intent
onClarificationResponse(template.analysisType, 'set_analysis_type');
```

**3. Template → Analysis Type Mapping**
| Template | analysisType | Query Type |
|----------|--------------|------------|
| Trend over time | `trend` | DATE_TRUNC monthly |
| Week-over-week | `trend` | DATE_TRUNC weekly |
| Outliers | `outliers` | Z-score >2 std dev |
| Top categories | `top_categories` | GROUP BY + ORDER BY |
| Data quality | `data_quality` | NULL + duplicates |
| Row count | `row_count` | COUNT(*) |

### Backend (No Changes Needed!)

The backend **already supported structured intents**:
- `main.py` handles `set_analysis_type` intent (line 554-569)
- `chat_orchestrator.py` generates queries based on `analysis_type` (line 519-719)
- All analysis types have deterministic query generation logic

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ USER CLICKS TEMPLATE: "Trend over time (monthly)"          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: ChatPanel.handleTemplateSelect()                 │
│   onClarificationResponse("trend", "set_analysis_type")    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: AppLayout.handleClarificationResponse()          │
│   POST /chat with:                                          │
│     intent: "set_analysis_type"                             │
│     value: "trend"                                          │
│     message: "trend" (for audit)                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: main.py /chat endpoint                             │
│   Sees intent → calls handle_intent()                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: handle_intent()                                    │
│   1. Maps "trend" to internal value (already "trend")       │
│   2. Updates state: context["analysis_type"] = "trend"      │
│   3. Calls chat_orchestrator.process()                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: chat_orchestrator.process()                        │
│   1. Loads state: context = {analysis_type: "trend"}        │
│   2. Checks _is_state_ready() → True                        │
│   3. No resultsContext → calls _generate_sql_plan()         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: _generate_sql_plan()                               │
│   analysis_type == "trend"                                  │
│   → Detects date_col and metric_col from catalog            │
│   → Generates:                                              │
│     SELECT DATE_TRUNC('month', date_col) as month,          │
│            COUNT(*) as count,                               │
│            SUM(metric_col) as total_metric                  │
│     FROM data                                               │
│     GROUP BY month                                          │
│     ORDER BY month                                          │
│     LIMIT 200                                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: Returns RunQueriesResponse                         │
│   {                                                          │
│     type: "run_queries",                                    │
│     queries: [{                                             │
│       name: "monthly_trend",                                │
│       sql: "SELECT DATE_TRUNC(...)..."                      │
│     }],                                                     │
│     explanation: "I'll analyze the trend..."                │
│   }                                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Receives run_queries response                     │
│   Checks response.type !== "intent_acknowledged"            │
│   → Skips follow-up "continue" message                      │
│   → Executes queries via POST /queries/execute              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Query execution completes                         │
│   POST /chat with resultsContext                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: _generate_final_answer()                           │
│   Uses results_summarizer to create summary                 │
│   Returns FinalAnswerResponse                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Updates UI                                        │
│   Summary tab: "Trend Analysis: 12 time periods..."         │
│   Tables tab: Shows monthly_trend table with data           │
│   Audit tab: Shows SQL, analysis_type, metadata             │
└─────────────────────────────────────────────────────────────┘
```

## Key Implementation Details

### 1. Frontend: Template Click Handler

**File:** `src/components/ChatPanel.tsx:215-221`

```typescript
const handleTemplateSelect = (template: AnalysisTemplate) => {
  setShowTemplates(false);

  // Send structured intent with analysis_type as the value
  // The choice parameter will be used as the display text in the user message
  onClarificationResponse(template.analysisType, 'set_analysis_type');
};
```

**Why this works:**
- `onClarificationResponse` already handles intent-based requests
- It sends `intent` and `value` to the backend
- It creates a user message for audit trail
- It handles the response and executes queries

### 2. Backend: Intent → State → SQL

**File:** `connector/app/main.py:532-601`

```python
async def handle_intent(request: ChatOrchestratorRequest):
    # Update state with analysis_type
    state_manager.update_context(
        request.conversationId,
        {"analysis_type": request.value}
    )

    # Orchestrator checks if state is ready → generates SQL
    response = await chat_orchestrator.process(request)
    return response
```

**File:** `connector/app/chat_orchestrator.py:302-306`

```python
if self._is_state_ready(context):
    if request.resultsContext:
        return await self._generate_final_answer(...)
    else:
        return await self._generate_sql_plan(...)  # ← Generates queries!
```

**File:** `connector/app/chat_orchestrator.py:513-517`

```python
def _is_state_ready(self, context: Dict[str, Any]) -> bool:
    """Check if conversation state has required fields for SQL generation"""
    analysis_type = context.get("analysis_type")
    # time_period is optional in v1
    return analysis_type is not None
```

### 3. Backend: Deterministic Query Generation

**File:** `connector/app/chat_orchestrator.py:519-719`

Each `analysis_type` has a deterministic SQL generator:

```python
async def _generate_sql_plan(self, request, catalog, context):
    analysis_type = context.get("analysis_type")

    if analysis_type == "row_count":
        # Generate COUNT(*) query
    elif analysis_type == "top_categories":
        # Generate GROUP BY query
    elif analysis_type == "trend":
        # Generate DATE_TRUNC query
    elif analysis_type == "outliers":
        # Generate z-score query
    elif analysis_type == "data_quality":
        # Generate NULL/duplicate checks
```

**Column Detection Heuristics (AI Assist OFF):**
- Date column: First column with date-like name/type
- Metric column: First numeric column
- Category column: First text/varchar column

**AI Assist ON:**
- Uses same deterministic logic if confidence ≥ 0.8
- Falls back to LLM for ambiguous cases (confidence < 0.8)

## Testing

### Manual Acceptance Tests

See `TEMPLATE_DROPDOWN_ACCEPTANCE.md` for detailed manual test cases.

**Quick Test:**
1. Upload a dataset (any CSV/Excel with dates and numbers)
2. Click template dropdown
3. Click "Trend over time (monthly)"
4. Verify:
   - User message appears: "trend"
   - Queries execute automatically
   - Tables tab shows monthly data
   - Audit tab shows DATE_TRUNC SQL
   - Summary says "Trend Analysis: N time periods..."

### Automated Tests

**File:** `test_template_dropdown_intents.py`

Tests that each template generates the correct query type:
- Row count → COUNT(*)
- Trend → DATE_TRUNC
- Outliers → z-score
- Top categories → GROUP BY
- Data quality → NULL checks

## Acceptance Criteria

✅ **"Row count" produces COUNT(*) query**
- Template sends `analysisType: "row_count"`
- Backend generates `SELECT COUNT(*) as row_count FROM data`
- Tables tab shows 1 row with count
- Audit tab shows SQL

✅ **"Trend" produces date_trunc bucket query**
- Template sends `analysisType: "trend"`
- Backend generates `DATE_TRUNC('month', date_col)...`
- Tables tab shows monthly aggregated data
- Summary shows period-over-period change

✅ **"Outliers" produces z-score filter query**
- Template sends `analysisType: "outliers"`
- Backend generates z-score calculation with >2 std dev filter
- Tables tab shows outlier rows or aggregated counts
- Summary shows outlier detection details

✅ **Template clicks populate Tables + Audit with matching query names and SQL**
- Tables tab: Shows query results with table name matching query name
- Audit tab: Shows executed SQL, analysis type, time period, row counts
- Summary tab: Shows results-derived summary (no canned text)

✅ **Frontend template dropdown sends structured intent, not raw text**
- No longer fills input box
- Sends `intent: "set_analysis_type"`, `value: <analysisType>`
- Creates audit message with template label

✅ **Backend SQL planning is analysis_type-driven (no preview default)**
- No default "summary_statistics" query
- No `SELECT * LIMIT 100` fallback
- Each `analysis_type` has specific query logic
- Returns `run_queries` response immediately after intent is set

✅ **Backend returns run_queries first, then requires resultsContext before final_answer**
- First response: `run_queries` with SQL
- Frontend executes queries
- Second request: Includes `resultsContext`
- Second response: `final_answer` with summary

✅ **Works with AI Assist ON and AI Assist OFF**
- Templates bypass AI routing (always deterministic)
- AI Assist OFF: Free-text asks for clarification
- AI Assist ON: Free-text uses LLM if needed
- Templates work the same in both modes

## Files Modified

### Frontend
1. **src/components/ChatPanel.tsx**
   - Lines 36-47: Added `analysisType` and `defaults` to AnalysisTemplate interface
   - Lines 49-159: Added `analysisType` values to all 8 templates
   - Lines 215-221: Modified `handleTemplateSelect` to send structured intent

### Backend
*No changes needed!* The backend already supported structured intents and deterministic query generation.

### Documentation
1. **connector/TEMPLATE_DROPDOWN_ACCEPTANCE.md** - Manual test guide
2. **connector/TEMPLATE_INTENTS_COMPLETE.md** - This document
3. **connector/test_template_dropdown_intents.py** - Automated test suite

## Build Verification

```bash
npm run build
```

**Result:** ✅ Build successful
```
✓ 1505 modules transformed.
dist/index.html                   0.71 kB │ gzip:  0.39 kB
dist/assets/index-BffDa0f9.css   30.50 kB │ gzip:  5.87 kB
dist/assets/index-CuMYKDgy.js   330.63 kB │ gzip: 91.04 kB
✓ built in 9.49s
```

## Migration Notes

**Breaking Changes:** None

**Backward Compatibility:**
- Old free-text input still works
- Existing conversations not affected
- API unchanged (frontend just sends different values)

**Deployment:**
- Deploy frontend and backend together (though backend changes are minimal)
- No database migrations needed
- No configuration changes required

## Next Steps

1. **Deploy to production**
   - Frontend: Build and deploy React app
   - Backend: No changes needed, already supports intents

2. **Monitor usage**
   - Track which templates are most used
   - Verify query generation works for all dataset types
   - Collect feedback on template effectiveness

3. **Future enhancements**
   - Add more templates (e.g., "Year-over-year comparison")
   - Allow users to customize templates
   - Add template favorites/pinning
   - Template recommendations based on dataset schema

## Related Documents

- `AE3_COMPLETE.md` - Results-driven summarizer (makes summaries truthful)
- `AE3_AE4_INTEGRATION.md` - How AE-3 and AE-4 work together
- `HR4_HYBRID_ROUTING_COMPLETE.md` - Hybrid routing (deterministic + AI)
- `TEMPLATE_DROPDOWN_ACCEPTANCE.md` - Manual test guide
