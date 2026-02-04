# Time Period Re-asking Bug - Diagnosis Instructions

## Problem
The system is repeatedly asking for time period selection even after it has been selected.

## Root Cause Theories

Based on code analysis, the bug could be:

1. **ConversationId changing between requests** - Frontend might be generating new IDs
2. **State not persisting** - Backend state manager might be clearing state
3. **Race condition** - Multiple requests happening simultaneously
4. **Frontend remounting** - React component remounting and resetting state

## How to Diagnose

### Step 1: Check Backend Logs

We've added comprehensive logging. Start the backend with:

```bash
cd connector
python3 app/main.py
```

When you reproduce the bug, look for these log entries:

```
📨 /chat endpoint received request:
   conversationId: conv-1738xxxxxxx
   intent: set_time_period
   value: all_time
```

**Check**: Is the `conversationId` THE SAME across all requests? If it changes, that's the bug!

### Step 2: Check State Persistence

After setting time period, the logs should show:

```
[AFTER RELOAD] Reloaded context: {'analysis_type': 'trend', 'time_period': 'all_time'}
Readiness check: analysis_type=True, time_period=True
```

**Check**: Does it say `time_period=True`? If False, the state didn't persist!

### Step 3: Check Subsequent Requests

When the results are sent back, logs should show:

```
[handle_message] conversationId=conv-1738xxxxxxx, hasResultsContext=True
[handle_message] Retrieved context: {'analysis_type': 'trend', 'time_period': 'all_time'}
[handle_message] time_period present: True
```

**Check**: Does it find `time_period` in context? If not, the state was lost between requests!

## Expected vs Actual Flow

### ✅ Expected Flow

```
1. POST /chat { intent: "set_time_period", value: "all_time", conversationId: "conv-123" }
   → State updated: context = { analysis_type: "trend", time_period: "all_time" }
   → Returns: RunQueriesResponse

2. Frontend executes queries locally

3. POST /chat { message: "Here are results", conversationId: "conv-123", resultsContext: {...} }
   → Retrieves state for "conv-123"
   → Finds time_period in context → proceeds
   → Returns: FinalAnswerResponse
```

### ❌ Actual Flow (Bug)

```
1. POST /chat { intent: "set_time_period", value: "all_time", conversationId: "conv-123" }
   → State updated
   → Returns: RunQueriesResponse

2. Frontend executes queries

3. POST /chat { message: "Here are results", conversationId: "conv-456" } ← DIFFERENT ID!
   → Creates NEW state for "conv-456"
   → time_period not found → asks again!
```

OR:

```
3. POST /chat { message: "Here are results", conversationId: "conv-123" }
   → Retrieves state for "conv-123"
   → context = {} ← STATE WAS LOST!
   → time_period not found → asks again!
```

## Likely Culprits

### 1. Frontend ConversationId Management (src/pages/AppLayout.tsx:55)

```typescript
const [conversationId] = useState(() => `conv-${Date.now()}`);
```

**Possible Issues**:
- Component is remounting
- Dataset change is triggering remount
- Multiple instances of AppLayout

**Fix**: Make conversationId persist across dataset changes or use a stable ID

### 2. Backend State Clearing

**Possible Issues**:
- State manager is being reset
- Multiple backend instances (unlikely with FastAPI)
- Memory issue causing state loss

**Fix**: Add state persistence to database instead of in-memory

## Quick Fix to Test

Add this to frontend AppLayout.tsx right before sending requests:

```typescript
console.log(`🔍 conversationId being used: ${conversationId}`);
```

Then in browser console, check if the ID stays the same. If it changes, that's the bug!

## Recommended Fixes

### Short-term (5 minutes):
1. Make conversationId independent of component lifecycle
2. Store in sessionStorage or similar

### Long-term (30 minutes):
1. Persist conversation state to Supabase database
2. Use dataset_id as part of conversation_id to ensure stability
3. Add conversation state cleanup logic

## Test Command

Run state persistence test:
```bash
cd connector
python3 test_state_persistence.py
```

If this passes, the backend state manager is fine and the issue is in the frontend.
