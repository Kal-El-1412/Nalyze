# Implementation: AI Assist Backend Gating (HR-2)

## Summary

Updated the backend `/chat` endpoint to accept `aiAssist` boolean flag and gate OpenAI usage based on it. When AI Assist is OFF, the system never calls OpenAI. When ON without an API key, it returns a friendly error message instead of a 500 error.

## Requirements Met

✅ Accept `aiAssist` boolean in request body and `X-AI-Assist` header
✅ If `aiAssist=false`: NEVER call OpenAI
✅ If `aiAssist=true`: Only call OpenAI when deterministic router confidence is low (state not ready)
✅ If `aiAssist=true` but no `OPENAI_API_KEY`: Return friendly final_answer (not 500)

## Changes Made

### 1. Request Model (models.py)

**Added fields to `ChatOrchestratorRequest`:**
```python
class ChatOrchestratorRequest(BaseModel):
    datasetId: str
    conversationId: str
    message: Optional[str] = None
    intent: Optional[str] = None
    value: Optional[Any] = None
    privacyMode: Optional[bool] = True
    safeMode: Optional[bool] = False
    aiAssist: Optional[bool] = False  # NEW: AI Assist flag
    resultsContext: Optional[ResultsContext] = None
```

**Default:** `aiAssist=False` (OFF)

### 2. Chat Endpoint (main.py)

**Updated `/chat` endpoint to read `aiAssist` from body and header:**

```python
@app.post("/chat")
async def chat(request_data: Request):
    body = await request_data.json()

    # Read privacyMode
    privacy_mode = body.get("privacyMode")
    if privacy_mode is None:
        privacy_header = request_data.headers.get("X-Privacy-Mode", "on")
        privacy_mode = privacy_header.lower() == "on"

    # Read safeMode
    safe_mode = body.get("safeMode")
    if safe_mode is None:
        safe_header = request_data.headers.get("X-Safe-Mode", "off")
        safe_mode = safe_header.lower() == "on"

    # Read aiAssist (NEW)
    ai_assist = body.get("aiAssist")
    if ai_assist is None:
        ai_header = request_data.headers.get("X-AI-Assist", "off")
        ai_assist = ai_header.lower() == "on"

    body["privacyMode"] = privacy_mode
    body["safeMode"] = safe_mode
    body["aiAssist"] = ai_assist
    request = ChatOrchestratorRequest(**body)

    logger.info(f"   aiAssist: {request.aiAssist}")
    # ... rest of handler
```

**Priority:** Body value takes precedence over header value

### 3. Chat Orchestrator (chat_orchestrator.py)

**Added gating logic in `process()` method:**

```python
async def process(self, request: ChatOrchestratorRequest):
    # ... dataset and catalog loading ...

    state = state_manager.get_state(request.conversationId)
    context = state.get("context", {})

    # If state is ready (has analysis_type and time_period), use deterministic path
    if self._is_state_ready(context):
        if request.resultsContext:
            return await self._generate_final_answer(request, catalog, context)
        else:
            return await self._generate_sql_plan(request, catalog, context)

    # NEW: Check if AI Assist is enabled
    ai_assist = request.aiAssist if request.aiAssist is not None else False

    if not ai_assist:
        # AI Assist is OFF - cannot process free-text queries
        logger.info("AI Assist is OFF - cannot process free-text queries")
        return FinalAnswerResponse(
            message="AI Assist is currently OFF. To ask questions in natural language, please enable AI Assist using the toggle next to the chat input.",
            tables=None
        )

    # AI Assist is ON - check if OpenAI API key is configured
    if not self.openai_api_key:
        logger.warning("AI Assist is ON but OPENAI_API_KEY is not configured")
        return FinalAnswerResponse(
            message="AI Assist is ON but no API key is configured. Set OPENAI_API_KEY in .env or turn AI Assist off.",
            tables=None
        )

    # Proceed with OpenAI call
    # ... rest of validation and _call_openai ...
```

## How It Works

### Flow Diagram

```
User sends chat request
    ↓
Parse aiAssist from body/header
    ↓
Is state ready? (has analysis_type + time_period)
    ↓                           ↓
   YES                         NO
    ↓                           ↓
Use deterministic         Check aiAssist
SQL generation                  ↓
(no OpenAI needed)         aiAssist=false?
    ↓                           ↓
Return RunQueriesResponse   YES: Return friendly message
                                 "AI Assist is OFF"
                                ↓
                               NO: aiAssist=true
                                ↓
                           Has API key?
                                ↓
                            YES: Call OpenAI
                                ↓
                            NO: Return friendly error
                                "no API key configured"
```

### Three Scenarios

#### Scenario 1: AI Assist OFF

**Request:**
```json
POST /chat
X-AI-Assist: off

{
  "datasetId": "ds-123",
  "conversationId": "conv-456",
  "message": "show me trends",
  "aiAssist": false
}
```

**Response:**
```json
{
  "type": "final_answer",
  "message": "AI Assist is currently OFF. To ask questions in natural language, please enable AI Assist using the toggle next to the chat input.",
  "tables": null
}
```

**Note:** This only happens when state is NOT ready. If the state already has `analysis_type` and `time_period` set (from previous clarifications), the deterministic path is used regardless of `aiAssist` setting.

#### Scenario 2: AI Assist ON + No API Key

**Request:**
```json
POST /chat
X-AI-Assist: on

{
  "datasetId": "ds-123",
  "conversationId": "conv-456",
  "message": "show me trends",
  "aiAssist": true
}
```

**Environment:** `OPENAI_API_KEY` not set

**Response:**
```json
{
  "type": "final_answer",
  "message": "AI Assist is ON but no API key is configured. Set OPENAI_API_KEY in .env or turn AI Assist off.",
  "tables": null
}
```

**Status Code:** 200 (not 500!)

#### Scenario 3: AI Assist ON + API Key Available

**Request:**
```json
POST /chat
X-AI-Assist: on

{
  "datasetId": "ds-123",
  "conversationId": "conv-456",
  "message": "show me trends",
  "aiAssist": true
}
```

**Environment:** `OPENAI_API_KEY=sk-...`

**Response:**
```json
{
  "type": "needs_clarification",
  "question": "What time period would you like to analyze?",
  "choices": ["Last week", "Last month", "Last quarter", "Last year"],
  "intent": "set_time_period"
}
```

**Behavior:** Calls OpenAI to parse user intent

## Deterministic vs AI-Assisted Paths

### Deterministic Path (No OpenAI)

**When:** State is ready (has `analysis_type` and `time_period`)

**Method:** `_generate_sql_plan()`

**Behavior:**
- Uses predefined SQL templates
- No OpenAI call needed
- Works even with `aiAssist=false`
- Fast and predictable

**Example state:**
```python
{
  "context": {
    "analysis_type": "trend",
    "time_period": "last_month"
  }
}
```

### AI-Assisted Path (Uses OpenAI)

**When:** State is NOT ready (missing `analysis_type` or `time_period`)

**Method:** `_call_openai()`

**Behavior:**
- Requires `aiAssist=true`
- Requires `OPENAI_API_KEY` set
- Parses free-text user queries
- Returns clarification questions if needed

**Example state:**
```python
{
  "context": {}  # Empty - needs AI to parse user intent
}
```

## Files Modified

1. **connector/app/models.py**
   - Added `aiAssist: Optional[bool] = False` to `ChatOrchestratorRequest`
   - Added `safeMode: Optional[bool] = False` to `ChatOrchestratorRequest`

2. **connector/app/main.py**
   - Updated `/chat` endpoint to read `aiAssist` from body and header
   - Added logging for `aiAssist` value
   - Read `safeMode` from body and header (was missing)

3. **connector/app/chat_orchestrator.py**
   - Added gating logic in `process()` method
   - Check `aiAssist` flag before calling OpenAI
   - Return friendly messages for OFF and missing API key cases

## Testing

Created `test_ai_assist_gating.py` with tests for:

1. ✅ `aiAssist=false` returns friendly message
2. ✅ `aiAssist=true` + no API key returns friendly error
3. ✅ `aiAssist=true` + API key calls OpenAI
4. ✅ Deterministic path works regardless of `aiAssist`
5. ✅ Request model accepts `aiAssist` field

Run tests:
```bash
cd connector
python test_ai_assist_gating.py
```

## Acceptance Criteria

✅ **Turning AI Assist ON without key returns a clear message**
- Returns `FinalAnswerResponse` with friendly message
- HTTP 200 status (not 500)
- Message includes actionable guidance

✅ **No OpenAI calls occur when OFF**
- When `aiAssist=false`, OpenAI is never called
- Returns friendly message explaining how to enable
- Only applies when state is not ready (otherwise deterministic path is used)

✅ **Accepts aiAssist in request**
- Request body field: `aiAssist: true|false`
- Request header: `X-AI-Assist: on|off`
- Default: `false` (OFF)

## Environment Variables

**Required for AI Assist to work:**
```bash
# .env file
OPENAI_API_KEY=sk-...
AI_MODE=on
```

**If `OPENAI_API_KEY` is missing:**
- With `aiAssist=false`: Works normally (no OpenAI needed)
- With `aiAssist=true`: Returns friendly error message

## Backwards Compatibility

**Default behavior:** `aiAssist=false`
- Existing clients without the flag will have AI Assist OFF by default
- This is safe because the deterministic path still works for structured queries
- Users must explicitly enable AI Assist to use OpenAI features

**Upgrade path:**
1. Users see "AI Assist is OFF" message
2. They enable the toggle in the UI
3. Frontend sends `aiAssist=true`
4. Backend uses OpenAI if API key is configured

## Error Messages

### AI Assist OFF
```
AI Assist is currently OFF. To ask questions in natural language,
please enable AI Assist using the toggle next to the chat input.
```

### AI Assist ON but No API Key
```
AI Assist is ON but no API key is configured.
Set OPENAI_API_KEY in .env or turn AI Assist off.
```

Both messages:
- Are user-friendly (no technical jargon)
- Provide clear next steps
- Return as `final_answer` (not error)
- Use HTTP 200 status code

## Logging

**Log messages added:**

```python
logger.info("AI Assist is OFF - cannot process free-text queries")
logger.warning("AI Assist is ON but OPENAI_API_KEY is not configured")
logger.info(f"   aiAssist: {request.aiAssist}")
```

**Helps with:**
- Debugging user issues
- Monitoring AI Assist usage
- Identifying API key configuration problems

---

**Status:** ✅ COMPLETE

**Ready for:** Production deployment

**Risk Level:** Low (safe default, friendly errors, backwards compatible)
