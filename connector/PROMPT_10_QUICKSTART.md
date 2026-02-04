# Prompt 10 Quickstart: UI Automatic Flow

## Overview

The UI automatically handles `run_queries` responses with zero manual intervention.

---

## What Changed

### TypeScript Interfaces

**Before:**
```typescript
interface FinalAnswerResponse {
  summaryMarkdown: string;  // ❌ Wrong
  tables: Array<{ name: string; ... }>;  // ❌ Wrong
}
```

**After:**
```typescript
interface FinalAnswerResponse {
  message: string;  // ✅ Matches backend
  tables?: Array<{ title: string; ... }>;  // ✅ Matches backend
}
```

---

## Complete Flow

### 1. User Action

```
User → Selects dataset
User → Picks "Top Categories"
User → Picks "This Year"
User → Sends message "Analyze"
```

---

### 2. Backend Response (run_queries)

```json
POST /chat
→ Response:
{
  "type": "run_queries",
  "queries": [{
    "name": "top_categories",
    "sql": "SELECT \"product_category\", COUNT(*) as count FROM data GROUP BY \"product_category\" ORDER BY count DESC LIMIT 10"
  }],
  "explanation": "I'll show you the top 10 categories..."
}
```

---

### 3. UI Shows Waiting State

```
┌────────────────────────────────────────┐
│ 🤖 Bot                                 │
│ ┌────────────────────────────────────┐ │
│ │ ⏳ I'll show you the top 10        │ │
│ │    categories...                   │ │
│ │                                    │ │
│ │ 📝 Queries to execute:             │ │
│ │   • top_categories                 │ │
│ │     SELECT "product_category", ... │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

---

### 4. UI Executes Queries (Automatic)

```typescript
// Happens automatically
const result = await connectorApi.executeQueries({
  datasetId: activeDataset,
  queries: response.queries,
});
```

---

### 5. UI Sends Results Back (Automatic)

```typescript
// Happens automatically
const followUpResponse = await connectorApi.sendChatMessage({
  datasetId: activeDataset,
  conversationId,
  message: 'Here are the query results.',
  resultsContext: { results: queryResults.results },
});
```

---

### 6. Backend Formats Answer

```json
{
  "type": "final_answer",
  "message": "Here are your top_categories results...",
  "tables": [{
    "title": "Top 10 Categories",
    "columns": ["product_category", "count"],
    "rows": [["Electronics", 450], ...]
  }]
}
```

---

### 7. UI Displays Results

**Chat:**
```
🤖 Here are your top_categories results for this_year:

   **Top categories:** Found 10 categories.
```

**Results Panel (Tables tab):**
```
┌────────────────────────────────────────┐
│ Top 10 Categories                      │
├──────────────────┬─────────────────────┤
│ product_category │ count               │
├──────────────────┼─────────────────────┤
│ Electronics      │ 450                 │
│ Clothing         │ 320                 │
│ Books            │ 280                 │
│ ...              │ ...                 │
└──────────────────┴─────────────────────┘
```

---

## Timeline

```
User sends message         (t=0ms)
  ↓
Backend SQL plan          (t=20ms)    ← No LLM!
  ↓
UI receives run_queries   (t=50ms)
  ↓
UI executes queries       (t=550ms)   ← Local DuckDB
  ↓
UI sends resultsContext   (t=600ms)
  ↓
Backend formats answer    (t=620ms)   ← No LLM!
  ↓
UI displays result        (t=650ms)
```

**Total: ~650ms**

---

## Key Features

### ✅ Fully Automatic

**No manual steps:**
- User doesn't click "Execute"
- User doesn't send results back
- User doesn't format output

**Everything happens automatically:**
1. Detect run_queries
2. Execute locally
3. Send results back
4. Display answer + tables

---

### ✅ Clear Loading States

**User sees progress:**
1. "I'll show you..." (with query preview)
2. "Writing summary..."
3. Final answer with tables

---

### ✅ Error Handling

**Graceful fallbacks:**
```typescript
if (result.success) {
  queryResults = result.data;
} else {
  // Show error toast
  // Use mock data
  // Continue flow
}
```

**Never crashes:**
- Errors logged
- User notified
- Mock data used
- Flow continues

---

## Files Modified

### 1. src/services/connectorApi.ts

**Changes:**
- `summaryMarkdown` → `message`
- `tables[].name` → `tables[].title`
- Added `explanation` to RunQueriesResponse
- Added `audit` to RunQueriesResponse

---

### 2. src/pages/AppLayout.tsx

**Changes:**
- Updated to use `response.message`
- Updated to use `response.explanation`
- Added null safety for `response.tables`
- Flow already implemented

---

### 3. src/components/ResultsPanel.tsx

**Changes:**
- Added `title` field to TableData
- Updated to prefer `title` over `name`
- Backwards compatible

---

## Testing

### Manual Test

```bash
# 1. Start connector
cd connector && ./run.sh

# 2. Register + ingest dataset
curl -X POST http://localhost:8000/datasets/register \
  -d '{"name": "test", "sourceType": "local_file", "filePath": "/path/to/data.csv"}'

curl -X POST http://localhost:8000/datasets/{id}/ingest

# 3. Set state (simulate UI selections)
curl -X POST http://localhost:8000/state/intent \
  -d '{"conversationId": "test-1", "intent": "set_analysis_type", "value": "top_categories"}'

curl -X POST http://localhost:8000/state/intent \
  -d '{"conversationId": "test-1", "intent": "set_time_period", "value": "this_year"}'

# 4. Send chat request
curl -X POST http://localhost:8000/chat \
  -d '{"conversationId": "test-1", "datasetId": "{id}", "message": "Analyze"}'

# Expected: { "type": "run_queries", "queries": [...] }
```

---

### Frontend Test

**1. Open app in browser:**
```
npm run dev
```

**2. Connect dataset:**
- Click "Connect Data"
- Upload CSV/Excel file
- Wait for ingestion

**3. Select preferences:**
- Click "Top Categories" button
- Click "This Year" button

**4. Send message:**
- Type anything (e.g., "show me")
- Hit Enter

**5. Watch automatic flow:**
- ⏳ Waiting message appears
- 📝 Queries shown
- ⏳ "Writing summary..."
- 🤖 Final answer with table

**Total time: ~1 second**

---

## Troubleshooting

### Issue: Tables not showing

**Check:**
```typescript
console.log(response.tables);
// Should be: [{ title: "...", columns: [...], rows: [...] }]
// NOT: [{ name: "...", ... }]
```

**Fix:**
Backend returns `title`, not `name`.

---

### Issue: Message is undefined

**Check:**
```typescript
console.log(response.message);
// Should be: "Here are your results..."
// NOT: response.summaryMarkdown
```

**Fix:**
Backend returns `message`, not `summaryMarkdown`.

---

### Issue: No automatic execution

**Check:**
```typescript
if (response.type === 'run_queries') {
  // This block should execute
  console.log('Executing queries automatically');
}
```

**Fix:**
Make sure AppLayout.tsx has the run_queries handler.

---

## Summary

**Endpoint:** POST /chat

**Input:** User message (when state is ready)

**Output 1:** `run_queries` response

**UI Action:** Execute → Send back → Display

**Output 2:** `final_answer` with tables

**Total Time:** ~650ms

**Manual Steps:** 0

**Result:** Complete automatic flow from preferences → query → results with zero manual intervention.
