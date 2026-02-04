# Intent-Based Chat API

## Overview

The `/chat` endpoint now supports both free-text messages and structured intent-based requests. This allows clients to set conversation parameters without triggering LLM calls.

## Backward Compatibility

✅ **The old API format is fully supported:**

```json
POST /chat
{
  "datasetId": "abc-123",
  "conversationId": "conv-456",
  "message": "Show me sales trends"
}
```

## New Intent-Based Format

Set conversation parameters directly without LLM processing:

```json
POST /chat
{
  "datasetId": "abc-123",
  "conversationId": "conv-456",
  "intent": "set_analysis_type",
  "value": "trend"
}
```

## Request Format

### ChatOrchestratorRequest

```typescript
{
  datasetId: string;           // Required: Dataset ID
  conversationId: string;      // Required: Conversation ID
  message?: string;            // Optional: Free-text message for LLM
  intent?: string;             // Optional: Structured intent name
  value?: any;                 // Optional: Intent value (required if intent is set)
  resultsContext?: {           // Optional: Previous query results
    results: Array<{
      name: string;
      columns: string[];
      rows: any[][];
    }>
  }
}
```

### Validation Rules

1. **Either `message` OR `intent` must be provided** (not both, not neither)
2. **If `intent` is provided, `value` is required**
3. **Cannot provide both `message` and `intent` in the same request**

## Response Formats

### For Message Requests (LLM Processing)

Returns one of:
- `NeedsClarificationResponse` - LLM needs more info
- `RunQueriesResponse` - LLM generated SQL queries to run
- `FinalAnswerResponse` - LLM provided final answer

### For Intent Requests (Direct State Update)

Returns `IntentAcknowledgmentResponse`:

```json
{
  "type": "intent_acknowledged",
  "intent": "set_analysis_type",
  "value": "trend",
  "state": {
    "conversation_id": "conv-456",
    "dataset_id": "abc-123",
    "ready": true,
    "message_count": 0,
    "context": {
      "analysis_type": "trend"
    },
    ...
  },
  "message": "Updated analysis type to 'trend'"
}
```

## Supported Intents

### Common Intents

| Intent | Purpose | Example Value |
|--------|---------|---------------|
| `set_analysis_type` | Set analysis mode | `"trend"`, `"comparison"`, `"distribution"` |
| `set_time_period` | Set time range | `"last_30_days"`, `"2024-Q1"`, `"ytd"` |
| `set_metric` | Set primary metric | `"revenue"`, `"sales"`, `"customers"` |
| `set_dimension` | Set grouping dimension | `"region"`, `"product"`, `"category"` |
| `set_filter` | Set data filter | `{"status": "active"}`, `{"region": "US"}` |
| `set_grouping` | Set grouping level | `"daily"`, `"monthly"`, `"yearly"` |
| `set_visualization` | Set chart type | `"line_chart"`, `"bar_chart"`, `"pie_chart"` |

### Custom Intents

You can use any intent name. If it starts with `set_`, the prefix is removed when storing in state:

- `set_foo` → stored as `foo` in context
- `custom_intent` → stored as `custom_intent` in context

## Intent Processing Flow

1. **Client sends intent request** to `/chat`
2. **Backend validates** request format
3. **State manager** updates conversation context
4. **Response returned immediately** (no LLM call)
5. **Subsequent message requests** can access updated context

## State Storage

Intent values are stored in the conversation state's `context` object:

```python
state = {
  "conversation_id": "conv-456",
  "dataset_id": "abc-123",
  "ready": true,
  "message_count": 0,
  "created_at": "2024-01-01T00:00:00",
  "last_updated": "2024-01-01T00:05:00",
  "context": {
    "analysis_type": "trend",      // ← Intent values stored here
    "time_period": "last_30_days",
    "metric": "revenue"
  },
  "metadata": {}
}
```

## Example Usage Flows

### Flow 1: Configure Then Ask

```javascript
// Step 1: Set analysis parameters
await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    datasetId: 'abc-123',
    conversationId: 'conv-456',
    intent: 'set_analysis_type',
    value: 'trend'
  })
});

await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    datasetId: 'abc-123',
    conversationId: 'conv-456',
    intent: 'set_time_period',
    value: 'last_30_days'
  })
});

// Step 2: Ask question (LLM has access to context)
await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    datasetId: 'abc-123',
    conversationId: 'conv-456',
    message: 'Show me the trends'
  })
});
```

### Flow 2: Update Mid-Conversation

```javascript
// User asks question
await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    datasetId: 'abc-123',
    conversationId: 'conv-456',
    message: 'Show sales'
  })
});

// User changes time period via UI control
await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    datasetId: 'abc-123',
    conversationId: 'conv-456',
    intent: 'set_time_period',
    value: 'last_90_days'
  })
});

// Context updated, no LLM call made
```

## Error Handling

### Validation Errors (400)

```json
{
  "detail": "Either 'message' or 'intent' must be provided"
}
```

```json
{
  "detail": "Cannot provide both 'message' and 'intent'"
}
```

```json
{
  "detail": "'value' is required when 'intent' is provided"
}
```

### Processing Errors (500)

```json
{
  "detail": "Chat processing failed: <error message>"
}
```

## Implementation Details

### Backend Files Modified

1. **`app/models.py`**
   - Updated `ChatOrchestratorRequest` to accept `intent` and `value`
   - Added validation in `__init__`
   - Created `IntentAcknowledgmentResponse` model
   - Updated `ChatOrchestratorResponse` union type

2. **`app/main.py`**
   - Added `handle_intent()` function for intent processing
   - Added `handle_message()` function for LLM processing
   - Updated `/chat` endpoint to route based on request type
   - Integrated with state_manager

3. **`app/chat_orchestrator.py`**
   - Added validation to ensure message is present before LLM call

### State Manager Integration

Intent values are persisted in conversation state:

```python
from app.state import state_manager

# Intent handler updates state
state = state_manager.get_state(conversation_id)
state["context"]["analysis_type"] = "trend"
state_manager.update_state(conversation_id, context=state["context"])

# Message handler can access context
state = state_manager.get_state(conversation_id)
analysis_type = state["context"].get("analysis_type")
```

## Testing

### cURL Examples

**Message request (backward compatible):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "abc-123",
    "conversationId": "conv-456",
    "message": "Show me sales trends"
  }'
```

**Intent request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "abc-123",
    "conversationId": "conv-456",
    "intent": "set_analysis_type",
    "value": "trend"
  }'
```

### TypeScript Client Example

```typescript
interface ChatRequest {
  datasetId: string;
  conversationId: string;
  message?: string;
  intent?: string;
  value?: any;
}

async function sendMessage(request: ChatRequest) {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  return response.json();
}

// Usage
await sendMessage({
  datasetId: 'abc-123',
  conversationId: 'conv-456',
  message: 'Show trends'
});

await sendMessage({
  datasetId: 'abc-123',
  conversationId: 'conv-456',
  intent: 'set_time_period',
  value: 'last_30_days'
});
```

## Benefits

1. **No LLM overhead** for UI control changes
2. **Faster response times** for parameter updates
3. **Predictable state management** without parsing natural language
4. **Backward compatible** with existing message-based flow
5. **Type-safe** structured data vs free-text
6. **Cost-effective** - no API calls for simple parameter changes
