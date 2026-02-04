# Time Period Recursion Fix

## Problem

After implementing prompts F2 and F3, the chat kept asking for time period recursively, creating an infinite loop.

## Root Cause

The issue was a **mismatch between backend behavior and frontend expectations**:

### Before the Fix

1. **Backend** (`handle_intent()`):
   - Accepted intent (e.g., `set_time_period`)
   - Updated state
   - When state became ready, **immediately returned `run_queries`**

2. **Frontend** (`handleClarificationResponse()`):
   - Sent intent request
   - Received response (could be `run_queries`)
   - **ALWAYS sent a follow-up "continue" message**

3. **Result**:
   - Backend returned `run_queries` → Frontend processed it ✅
   - Frontend sent "continue" → Backend received as new message
   - Backend's `handle_message()` asked for missing fields again ❌
   - **Infinite loop**: Time period kept being asked recursively

### Why This Happened

The frontend's follow-up "continue" message was designed for a different flow:
- Originally, `handle_intent()` returned `IntentAcknowledgmentResponse`
- Frontend would then send "continue" to trigger progression
- But after F3 changes, `handle_intent()` progressed automatically
- Frontend still sent "continue", causing duplicate progression

## The Fix

### 1. Backend Changes (connector/app/main.py)

**Updated `handle_intent()` to progress automatically:**

```python
async def handle_intent(request: ChatOrchestratorRequest):
    # ... update state ...

    # Check if state is ready after update
    if "analysis_type" in context and "time_period" in context:
        # State is ready, generate queries immediately
        response = await chat_orchestrator.process(request)
        return response
    else:
        # State not ready, ask for next missing field
        if "analysis_type" not in context:
            return NeedsClarificationResponse(
                question="What type of analysis would you like to perform?",
                choices=["row_count", "top_categories", "trend"],
                intent="set_analysis_type"
            )
        elif "time_period" not in context:
            return NeedsClarificationResponse(
                question="What time period would you like to analyze?",
                choices=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                intent="set_time_period"
            )
```

**Key behavior:**
- If state is ready → Return `run_queries` directly
- If state not ready → Return `needs_clarification` for next field
- Never returns `intent_acknowledged` anymore

**Added intent field to clarifications:**

```python
class NeedsClarificationResponse(BaseModel):
    type: Literal["needs_clarification"] = "needs_clarification"
    question: str
    choices: List[str]
    intent: Optional[str] = None  # NEW FIELD
    audit: AuditInfo = Field(default_factory=AuditInfo)
```

### 2. Frontend Changes (src/pages/AppLayout.tsx)

**Only send "continue" when backend returns `intent_acknowledged`:**

```typescript
if (result.success) {
  await handleChatResponse(result.data);

  // Only send follow-up if backend returned intent_acknowledged
  // If backend already progressed (run_queries, needs_clarification), don't send continue
  if (result.data.type === 'intent_acknowledged') {
    const followUpResult = await connectorApi.sendChatMessage({
      datasetId: activeDataset,
      conversationId,
      message: 'continue',
      privacyMode,
      safeMode,
    });

    if (followUpResult.success) {
      await handleChatResponse(followUpResult.data);
    }
  }
}
```

**Use intent field from backend:**

```typescript
const handleChatResponse = async (response: ChatResponse) => {
  if (response.type === 'needs_clarification') {
    // Use intent from backend if provided, otherwise detect from question
    const intent = response.intent || detectIntentFromQuestion(response.question);
    // ...
  }
}
```

### 3. Type Definitions (src/services/connectorApi.ts)

**Added intent field to ClarificationResponse:**

```typescript
export interface ClarificationResponse {
  type: 'needs_clarification';
  question: string;
  choices: string[];
  intent?: string;  // NEW FIELD
  allowFreeText: boolean;
}
```

## Flow After Fix

### Happy Path

1. **User starts conversation**
   - Backend: Returns clarification for `analysis_type`

2. **User selects "trend"**
   - Frontend: Sends intent `set_analysis_type` = `trend`
   - Backend: Updates state, checks readiness
   - Backend: Missing `time_period`, returns clarification
   - Frontend: Receives `needs_clarification`, displays choices
   - Frontend: Does NOT send "continue" (response is not `intent_acknowledged`)

3. **User selects "Last 7 days"**
   - Frontend: Sends intent `set_time_period` = `last_7_days`
   - Backend: Updates state, checks readiness
   - Backend: State is ready! Returns `run_queries`
   - Frontend: Receives `run_queries`, executes queries locally
   - Frontend: Does NOT send "continue" (response is not `intent_acknowledged`)

4. **User sends another message later**
   - Backend: State still has `time_period`
   - Backend: Proceeds directly to query generation
   - Never asks for time period again ✅

## Key Improvements

1. **Deterministic progression**: Backend immediately moves to next step after intent
2. **No recursion**: Frontend only sends "continue" when truly needed
3. **Clear intent tracking**: Backend explicitly specifies intent in clarifications
4. **State preservation**: Time period (and other fields) never asked again once set

## Testing

Run the test to verify the fix:

```bash
cd connector
python3 test_no_recursion.py
```

Expected output: Shows the flow without recursion, time period asked exactly once.
