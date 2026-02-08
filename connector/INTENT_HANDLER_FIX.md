# Intent Handler Fix - Clarification Option Clicks Now Work

## Problem
When users clicked clarification options (e.g., "Row count", "Trends over time"), the backend would return "Please provide a message" because it only checked `request.message` and ignored `request.intent` and `request.value`.

## Solution
Added an intent handler in `chat_orchestrator.py` that processes structured intent/value requests before the message check:

1. **set_analysis_type intent**: Maps UI labels to analysis types and updates conversation state
   - "Row count" → `analysis_type: "row_count"` + `time_period: "all_time"`
   - "Trends over time" → `analysis_type: "trend"`
   - "Top categories" → `analysis_type: "top_categories"`
   - "Find outliers" → `analysis_type: "outliers"`
   - "Check data quality" → `analysis_type: "data_quality"`

2. **set_time_period intent**: Updates time_period in state

3. **Immediate SQL generation**: If state is ready after updating, returns `run_queries` immediately (no extra round-trip)

## Code Location
File: `connector/app/chat_orchestrator.py`
Lines: 302-360 (inserted right after state/context retrieval)

## Acceptance Tests

### UI Flow Test
1. Start chat, type "Monthly trend"
2. If backend asks for clarification, click "Row count" option
3. ✅ Backend returns `run_queries` with `SELECT COUNT(*) as row_count FROM data`
4. ✅ UI executes query and shows results

### Direct API Test
```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "test_id",
    "conversationId": "conv1",
    "intent": "set_analysis_type",
    "value": "Row count"
  }'
```

Expected response type: `"run_queries"` (NOT `"needs_clarification"`)

### Automated Test
Run: `python3 connector/test_intent_handling.py`
- ✅ Tests row count intent
- ✅ Tests trends intent
- ✅ Tests time period intent
- ✅ Verifies state updates correctly
- ✅ Confirms no "Please provide a message" errors

## Benefits
- Clarification options are now fully functional
- Users get immediate SQL execution after selecting options
- No more dead-end "Please provide a message" errors
- State management works correctly for UI-driven flows
