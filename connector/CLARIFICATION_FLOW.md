# Deterministic Clarification Flow

## Overview

The `/chat` endpoint implements deterministic clarification based on conversation state. Required fields are checked **before** LLM processing, ensuring clarification questions appear exactly once and never repeat.

## Required Fields

Two fields must be present in conversation state before analysis can proceed:

1. **analysis_type** - Type of analysis to perform
2. **time_period** - Time range for analysis

## Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│ /chat endpoint receives message                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Check: Is this an intent request?                          │
├─────────────────────────────────────────────────────────────┤
│ YES → handle_intent() → Update state → Return ack          │
│ NO  → Continue to handle_message()                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ handle_message(): Check conversation state                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Is analysis_type in state.context?                         │
├─────────────────────────────────────────────────────────────┤
│ NO  → Return NeedsClarificationResponse for analysis_type  │
│ YES → Continue checking                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Is time_period in state.context?                           │
├─────────────────────────────────────────────────────────────┤
│ NO  → Return NeedsClarificationResponse for time_period    │
│ YES → Continue to LLM                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Both fields present: Call chat_orchestrator.process()      │
│ → LLM processing with full context                         │
│ → Analysis pipeline execution                               │
└─────────────────────────────────────────────────────────────┘
```

## Clarification Questions

### Analysis Type

**When:** `analysis_type` not in conversation state

**Question:** "What type of analysis would you like to perform?"

**Choices:**
- `trend` - Analyze trends over time
- `comparison` - Compare different segments
- `distribution` - View data distribution
- `correlation` - Find correlations between metrics
- `summary` - Get summary statistics

### Time Period

**When:** `time_period` not in conversation state

**Question:** "What time period would you like to analyze?"

**Choices:**
- `last_7_days` - Last 7 days
- `last_30_days` - Last 30 days
- `last_90_days` - Last 90 days
- `last_year` - Last year
- `year_to_date` - Year to date
- `all_time` - All available data

## Example Conversation Flow

### Flow 1: Progressive Clarification

```
User: "Show me trends"
→ State: {}
→ Response: NeedsClarification (analysis_type)

User: [Selects "trend"]
→ Intent: set_analysis_type = "trend"
→ State: {context: {analysis_type: "trend"}}
→ Response: IntentAcknowledged

User: "Show me trends"
→ State: {context: {analysis_type: "trend"}}
→ Response: NeedsClarification (time_period)

User: [Selects "last_30_days"]
→ Intent: set_time_period = "last_30_days"
→ State: {context: {analysis_type: "trend", time_period: "last_30_days"}}
→ Response: IntentAcknowledged

User: "Show me trends"
→ State: {context: {analysis_type: "trend", time_period: "last_30_days"}}
→ Response: RunQueries or FinalAnswer (LLM called)
```

### Flow 2: Pre-configure via Intents

```
User: [Sets analysis_type = "comparison"]
→ Intent: set_analysis_type = "comparison"
→ State: {context: {analysis_type: "comparison"}}
→ Response: IntentAcknowledged

User: [Sets time_period = "last_90_days"]
→ Intent: set_time_period = "last_90_days"
→ State: {context: {analysis_type: "comparison", time_period: "last_90_days"}}
→ Response: IntentAcknowledged

User: "Compare sales by region"
→ State: {context: {analysis_type: "comparison", time_period: "last_90_days"}}
→ Response: RunQueries or FinalAnswer (LLM called)
```

## Implementation Details

### State Check Logic (app/main.py)

```python
async def handle_message(request: ChatOrchestratorRequest):
    state = state_manager.get_state(request.conversationId)
    context = state.get("context", {})

    # Check 1: analysis_type
    if "analysis_type" not in context:
        return NeedsClarificationResponse(
            question="What type of analysis would you like to perform?",
            choices=["trend", "comparison", "distribution", "correlation", "summary"]
        )

    # Check 2: time_period
    if "time_period" not in context:
        return NeedsClarificationResponse(
            question="What time period would you like to analyze?",
            choices=["last_7_days", "last_30_days", "last_90_days", "last_year", "year_to_date", "all_time"]
        )

    # All required fields present: call LLM
    response = await chat_orchestrator.process(request)
    return response
```

### Intent Handling (app/main.py)

```python
async def handle_intent(request: ChatOrchestratorRequest):
    state = state_manager.get_state(request.conversationId)

    # Map intent to field name
    field_name = request.intent.replace("set_", "")

    # Update state context
    if "context" not in state:
        state["context"] = {}

    state["context"][field_name] = request.value
    state_manager.update_state(request.conversationId, context=state["context"])

    # Return acknowledgment
    return IntentAcknowledgmentResponse(
        intent=request.intent,
        value=request.value,
        state=state_manager.get_state(request.conversationId),
        message=f"Updated {field_name} to '{request.value}'"
    )
```

## Benefits

### 1. Deterministic Behavior
- Clarification logic is state-based, not LLM-based
- Same state always produces same clarification
- Predictable user experience

### 2. No Repeated Questions
- Each required field asked exactly once
- State persists across conversation
- User never sees same question twice

### 3. No LLM Overhead for Clarifications
- Clarifications handled by simple state checks
- No API calls until ready to analyze
- Cost savings on clarification flow

### 4. Progressive Enhancement
- Users can answer questions as they appear
- Or pre-configure via intent requests
- Flexible interaction patterns

### 5. Guaranteed Context
- LLM always receives complete required context
- No ambiguous queries reaching analysis pipeline
- Higher quality analysis results

## State Persistence

Clarification responses are based on persistent conversation state:

```python
{
  "conversation_id": "conv-123",
  "dataset_id": "dataset-456",
  "ready": true,
  "message_count": 0,
  "context": {
    "analysis_type": "trend",      # ← Required field 1
    "time_period": "last_30_days", # ← Required field 2
    "metric": "revenue",           # Optional fields
    "dimension": "region"
  },
  "created_at": "2024-01-01T00:00:00",
  "last_updated": "2024-01-01T00:05:00"
}
```

## Frontend Integration

### Handling Clarification Responses

```typescript
const response = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    datasetId: 'abc-123',
    conversationId: 'conv-456',
    message: 'Show me trends'
  })
});

const data = await response.json();

if (data.type === 'needs_clarification') {
  // Display choices to user
  showClarificationUI(data.question, data.choices);
} else if (data.type === 'intent_acknowledged') {
  // Field set successfully
  showConfirmation(data.message);
} else {
  // LLM response (run_queries or final_answer)
  handleAnalysisResponse(data);
}
```

### Responding to Clarification

```typescript
function onUserSelectsChoice(choice: string) {
  // Determine which field this answers
  const intent = determineIntent(currentQuestion);

  // Send intent request
  await fetch('/chat', {
    method: 'POST',
    body: JSON.stringify({
      datasetId: 'abc-123',
      conversationId: 'conv-456',
      intent: intent,
      value: choice
    })
  });

  // Then resend original message to continue flow
  await fetch('/chat', {
    method: 'POST',
    body: JSON.stringify({
      datasetId: 'abc-123',
      conversationId: 'conv-456',
      message: originalMessage
    })
  });
}
```

## Testing

Test scenarios verify:
1. First message without state → analysis_type clarification
2. Set analysis_type → acknowledged
3. Second message → time_period clarification (not analysis_type)
4. Set time_period → acknowledged
5. Third message → LLM processing

See `test_clarification_flow.py` for complete test suite.

## Acceptance Criteria

✅ Clarification questions appear once per required field
✅ Selecting an option never repeats the same question
✅ No LLM calls during clarification flow
✅ LLM only called when all required fields present
✅ State persists across entire conversation
