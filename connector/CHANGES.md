# /chat Endpoint Refactor - Intent-Based Support

## Summary

The `/chat` endpoint has been refactored to support both free-text messages (existing) and structured intent-based requests (new). Backward compatibility is fully maintained.

## Changes Made

### 1. `app/models.py`

**Updated `ChatOrchestratorRequest`:**
- Made `message` optional
- Added `intent` (optional string)
- Added `value` (optional any type)
- Added validation in `__init__`:
  - Either `message` OR `intent` must be provided
  - Cannot provide both
  - If `intent` is provided, `value` is required

**Added `IntentAcknowledgmentResponse`:**
```python
class IntentAcknowledgmentResponse(BaseModel):
    type: Literal["intent_acknowledged"] = "intent_acknowledged"
    intent: str
    value: Any
    state: Dict[str, Any]
    message: str
```

**Updated `ChatOrchestratorResponse`:**
- Added `IntentAcknowledgmentResponse` to union type

### 2. `app/main.py`

**Added imports:**
- `IntentAcknowledgmentResponse`
- `state_manager` from `app.state`

**Updated `/chat` endpoint:**
- Routes to `handle_intent()` for intent-based requests
- Routes to `handle_message()` for message-based requests

**Added `handle_intent()` function:**
- Processes structured intent requests
- Updates conversation state directly
- Returns acknowledgment response
- **No LLM call made**

**Added `handle_message()` function:**
- Processes free-text message requests
- Updates message count in state
- Calls chat orchestrator (LLM processing)
- Returns LLM response

### 3. `app/chat_orchestrator.py`

**Updated `process()` method:**
- Added validation to ensure `message` is present
- Returns error if message is None

### 4. `app/state.py` (From Prompt 1)

Created conversation state manager:
- `get_state(conversation_id)` - Get/create state
- `update_state(conversation_id, **fields)` - Update fields
- `is_ready(conversation_id)` - Check readiness
- Thread-safe operations
- In-memory storage

## API Contract

### Request Format

**Option 1: Message-based (existing, unchanged):**
```json
{
  "datasetId": "string",
  "conversationId": "string",
  "message": "string"
}
```

**Option 2: Intent-based (new):**
```json
{
  "datasetId": "string",
  "conversationId": "string",
  "intent": "string",
  "value": any
}
```

### Response Formats

**For message requests:**
- `NeedsClarificationResponse`
- `RunQueriesResponse`
- `FinalAnswerResponse`

**For intent requests (new):**
- `IntentAcknowledgmentResponse`

## Processing Flow

### Intent Request Flow
1. Client sends intent + value
2. `handle_intent()` validates request
3. State manager updates conversation context
4. Immediate acknowledgment returned
5. **No LLM call made**

### Message Request Flow (unchanged)
1. Client sends message
2. `handle_message()` updates message count
3. Chat orchestrator processes with LLM
4. LLM response returned

## State Storage

Intent values are stored in conversation state's `context` object:

```python
{
  "conversation_id": "conv-123",
  "context": {
    "analysis_type": "trend",
    "time_period": "last_30_days",
    "metric": "revenue"
  }
}
```

## Supported Intents

| Intent | Stored As | Example Value |
|--------|-----------|---------------|
| `set_analysis_type` | `analysis_type` | `"trend"` |
| `set_time_period` | `time_period` | `"last_30_days"` |
| `set_metric` | `metric` | `"revenue"` |
| `set_dimension` | `dimension` | `"region"` |
| `set_filter` | `filter` | `{"status": "active"}` |
| `set_grouping` | `grouping` | `"monthly"` |
| `set_visualization` | `visualization_type` | `"line_chart"` |

Custom intents are also supported.

## Backward Compatibility

✅ **100% Backward Compatible**
- All existing message-based requests work unchanged
- No breaking changes to request/response format
- Existing clients continue to work without modifications

## Benefits

1. **Performance** - Intent updates skip LLM processing
2. **Predictability** - Direct state updates without parsing
3. **Cost** - No API calls for parameter changes
4. **Type Safety** - Structured data vs free text
5. **Flexibility** - Mix message and intent requests in conversation

## Testing

Created test files:
- `test_state.py` - State manager tests (✓ 10/10 passed)
- `test_contract.py` - Contract structure demonstration
- `test_intent_chat.py` - Intent validation tests

## Documentation

Created documentation files:
- `STATE_MANAGER.md` - State manager API reference
- `INTENT_API.md` - Complete intent-based API guide
- `CHANGES.md` - This file

## Files Modified

1. `/connector/app/models.py` - Updated models
2. `/connector/app/main.py` - Updated endpoint + added handlers
3. `/connector/app/chat_orchestrator.py` - Added message validation
4. `/connector/app/state.py` - New state manager (Prompt 1)

## Acceptance Criteria

✅ Backend updates state directly when intent is present
✅ No LLM call happens when setting fields
✅ Backward compatibility maintained
✅ State persists per conversationId
✅ Fields persist across messages
