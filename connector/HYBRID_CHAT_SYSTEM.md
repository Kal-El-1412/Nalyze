# Hybrid Chat System: Intent-Based + Free-Text

## Overview

The chat system supports two interaction modes that coexist seamlessly:

1. **Free-Text Mode** - Exploratory, flexible, LLM-powered
2. **Intent Mode** - Deterministic, fast, state-based

## Visual Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                              │
├─────────────────────────────┬───────────────────────────────────┤
│                             │                                   │
│   📝 TEXT INPUT BOX         │   🔘 CLARIFICATION BUTTONS        │
│   "Show me top customers"   │   [Trend] [Summary] [Comparison]  │
│                             │                                   │
└──────────────┬──────────────┴───────────────┬───────────────────┘
               │                              │
               │                              │
               ▼                              ▼
        FREE-TEXT MODE                  INTENT MODE
               │                              │
               ▼                              ▼
    ┌──────────────────────┐      ┌──────────────────────┐
    │  POST /chat          │      │  POST /chat          │
    │  {                   │      │  {                   │
    │    message: "..."    │      │    intent: "...",    │
    │  }                   │      │    value: "..."      │
    │                      │      │  }                   │
    └──────────┬───────────┘      └──────────┬───────────┘
               │                              │
               ▼                              ▼
    ┌──────────────────────┐      ┌──────────────────────┐
    │  LLM PROCESSING      │      │  STATE UPDATE        │
    │  - Interprets text   │      │  - Direct update     │
    │  - Full NLU          │      │  - No LLM call       │
    │  - Flexible          │      │  - Instant           │
    │  - ~2-3 sec          │      │  - ~50ms             │
    │  - $0.001-0.01       │      │  - Free              │
    └──────────┬───────────┘      └──────────┬───────────┘
               │                              │
               ▼                              ▼
    ┌──────────────────────┐      ┌──────────────────────┐
    │  queries OR           │      │  intent_acknowledged │
    │  needs_clarification  │      │                      │
    └──────────────────────┘      └──────────┬───────────┘
                                              │
                                              ▼
                                   ┌──────────────────────┐
                                   │  Frontend sends:     │
                                   │  { message: "cont." }│
                                   └──────────┬───────────┘
                                              │
                                              ▼
                                   ┌──────────────────────┐
                                   │  Backend checks      │
                                   │  state → next step   │
                                   └──────────────────────┘
```

## Request Flow Comparison

### Free-Text Flow

```
User types: "What are my top customers by revenue?"

Frontend:
  handleSendMessage("What are my top customers by revenue?")

Request:
  POST /chat
  {
    "datasetId": "sales-2024",
    "conversationId": "conv-123",
    "message": "What are my top customers by revenue?"
  }

Backend:
  1. Load state (context from previous intents)
  2. Call LLM with message + context
  3. LLM processes natural language
  4. LLM generates SQL queries OR asks clarification

Response:
  {
    "type": "run_queries",
    "queries": [
      {
        "name": "top_customers",
        "sql": "SELECT customer_name, SUM(revenue) as total FROM sales GROUP BY customer_name ORDER BY total DESC LIMIT 10"
      }
    ]
  }

Result: Queries executed, results returned
```

**Characteristics:**
- ✅ Flexible natural language
- ✅ Exploratory analysis
- ✅ LLM understands intent
- ⏱️ 2-3 seconds
- 💰 $0.001-0.01 per request

---

### Intent Flow

```
User clicks: [Trend] button

Frontend:
  handleClarificationResponse("Trend", "set_analysis_type")

Request:
  POST /chat
  {
    "datasetId": "sales-2024",
    "conversationId": "conv-123",
    "intent": "set_analysis_type",
    "value": "Trend"
  }

Backend:
  1. Update state: { analysis_type: "Trend" }
  2. Return acknowledgment (NO LLM call)

Response:
  {
    "type": "intent_acknowledged",
    "intent": "set_analysis_type",
    "value": "Trend",
    "state": {
      "conversation_id": "conv-123",
      "context": {
        "analysis_type": "Trend"
      }
    }
  }

Frontend:
  POST /chat
  {
    "datasetId": "sales-2024",
    "conversationId": "conv-123",
    "message": "continue"
  }

Backend:
  1. Check state: { analysis_type: "Trend" }
  2. Still missing time_period
  3. Return next clarification

Response:
  {
    "type": "needs_clarification",
    "question": "What time period?",
    "choices": ["Last 7 days", "Last 30 days", "Last 90 days"]
  }

Result: Next clarification shown
```

**Characteristics:**
- ✅ Deterministic state update
- ✅ No LLM interpretation
- ✅ Instant response
- ⏱️ ~50ms
- 💰 Free

---

## Mixed Mode Example

### Complete User Journey

```
1. User types: "Show me trends"
   → POST /chat { message: "Show me trends" }
   → LLM processes, identifies need for clarification
   → Response: needs_clarification (analysis_type)

2. User clicks: [Trend]
   → POST /chat { intent: "set_analysis_type", value: "Trend" }
   → State updated (no LLM)
   → Response: intent_acknowledged
   → Frontend: POST /chat { message: "continue" }
   → Response: needs_clarification (time_period)

3. User clicks: [Last 30 days]
   → POST /chat { intent: "set_time_period", value: "Last 30 days" }
   → State updated (no LLM)
   → Response: intent_acknowledged
   → Frontend: POST /chat { message: "continue" }
   → Backend: All fields present, call LLM
   → Response: run_queries

4. Queries executed, results shown

5. User types: "Can you also show year-over-year?"
   → POST /chat { message: "Can you also show year-over-year?" }
   → LLM processes with existing state context
   → Response: run_queries (additional analysis)
```

**Key Points:**
- Started with free-text
- Used intents for clarifications (fast)
- Returned to free-text for follow-up (flexible)
- State preserved throughout
- Best of both worlds

---

## Routing Decision Tree

```
┌─────────────────────────┐
│   User Interaction      │
└───────────┬─────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌────────┐      ┌────────┐
│ Types  │      │ Clicks │
│ Text   │      │ Button │
└────┬───┘      └────┬───┘
     │               │
     │          ┌────┴────┐
     │          │         │
     │          ▼         ▼
     │    ┌─────────┐ ┌─────────┐
     │    │ Intent  │ │   No    │
     │    │ Detected│ │ Intent  │
     │    └────┬────┘ └────┬────┘
     │         │           │
     ▼         ▼           ▼
┌────────────────────────────┐
│   handleSendMessage()      │
│   → { message: "..." }     │
│   → LLM processes          │
└────────────────────────────┘
            │
            ▼
┌────────────────────────────┐
│   handleClarificationResp  │
│   → { intent: "...", ... } │
│   → State updated          │
└────────────────────────────┘
```

---

## Code Structure

### Text Input Handler

```typescript
// src/pages/AppLayout.tsx

const handleSendMessage = async (content: string) => {
  // Create user message for display
  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content,
    timestamp: new Date().toLocaleTimeString(),
  };
  setMessages([...messages, userMessage]);

  // Send to backend with message field
  const result = await connectorApi.sendChatMessage({
    datasetId: activeDataset,
    conversationId,
    message: content,  // ← Free-text message
    defaultsContext: defaults,
  });

  // Process response
  await handleChatResponse(result.data);
};
```

---

### Button Click Handler

```typescript
// src/pages/AppLayout.tsx

const handleClarificationResponse = async (
  choice: string,
  intent?: string
) => {
  // Create user message for display
  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content: choice,
    timestamp: new Date().toLocaleTimeString(),
  };
  setMessages(prev => [...prev, userMessage]);

  if (intent) {
    // Send intent request
    const result = await connectorApi.sendChatMessage({
      datasetId: activeDataset,
      conversationId,
      intent,        // ← Intent name
      value: choice, // ← Intent value
    });

    await handleChatResponse(result.data);

    // Explicit follow-up
    const followUp = await connectorApi.sendChatMessage({
      datasetId: activeDataset,
      conversationId,
      message: 'continue',
    });

    await handleChatResponse(followUp.data);
  } else {
    // No intent, fall back to text
    handleSendMessage(choice);
  }
};
```

---

## Backend Handling

```python
# app/chat_orchestrator.py

@router.post("/chat")
async def chat(request: ChatOrchestratorRequest):
    # Validation
    if request.message and request.intent:
        raise HTTPException(400, "Cannot provide both")
    if not request.message and not request.intent:
        raise HTTPException(400, "Must provide either")

    # Intent-based (deterministic)
    if request.intent:
        # Update state directly
        state_manager.update_state(
            conversation_id=request.conversationId,
            context={
                request.intent.replace("set_", ""): request.value
            }
        )

        # Return acknowledgment (no LLM)
        return IntentAcknowledgmentResponse(
            type="intent_acknowledged",
            intent=request.intent,
            value=request.value,
            state=state_manager.get_state(request.conversationId)
        )

    # Message-based (LLM processing)
    if request.message:
        # Load state
        context = state_manager.get_state(request.conversationId)

        # Check if clarifications needed
        missing = check_required_fields(context)
        if missing:
            return NeedsClarificationResponse(
                type="needs_clarification",
                question=get_clarification_question(missing[0]),
                choices=get_choices(missing[0])
            )

        # All fields present, call LLM
        llm_response = await llm.process(
            message=request.message,
            context=context,
            catalog=catalog
        )

        return llm_response
```

---

## Performance Comparison

| Metric | Free-Text Mode | Intent Mode |
|--------|----------------|-------------|
| **Latency** | 2-3 seconds | ~50ms |
| **Cost** | $0.001-0.01 | Free |
| **LLM Calls** | 1 per message | 0 |
| **Determinism** | Variable | 100% |
| **Flexibility** | High | Fixed options |
| **Use Case** | Exploration | Clarifications |

---

## Benefits

### For Users

✅ **Type when exploring** - Natural language questions
✅ **Click when clarifying** - Fast, clear options
✅ **Switch freely** - No mode switching needed
✅ **No repeated questions** - State remembered
✅ **Instant feedback** - Button clicks instant

### For Developers

✅ **Separation of concerns** - Backend handles clarifications, LLM handles analysis
✅ **Cost optimization** - Intents bypass LLM
✅ **Predictable behavior** - Intents deterministic
✅ **Flexible extension** - Add new intents easily
✅ **Backward compatible** - Old code works

### For Product

✅ **Better UX** - Right tool for each interaction
✅ **Lower cost** - Fewer LLM calls
✅ **Faster response** - Instant state updates
✅ **Reliable** - Deterministic clarifications
✅ **Scalable** - State-based, not LLM-based

---

## Fallback Behavior

If a clarification question doesn't match known intent patterns:

```typescript
// Frontend detects no intent
const intent = detectIntentFromQuestion(
  "Which specific column should I use?"
);
// Returns: undefined

// Falls back to text-based
if (intent) {
  // Send intent
} else {
  // Send as regular message
  handleSendMessage(choice);
}
```

**Result:** ✅ Graceful degradation, backward compatible

---

## Summary

The hybrid system provides:

**Free-Text Mode:**
- User types questions
- LLM interprets natural language
- Flexible, exploratory
- ~2-3 seconds response time

**Intent Mode:**
- User clicks buttons
- State updated directly
- Deterministic, fast
- ~50ms response time

**Both Together:**
- Seamless coexistence
- No mode switching
- State shared across both
- Best tool for each interaction

**Result:** Fast, cheap, flexible chat experience with perfect separation between exploration (LLM) and clarification (state).
