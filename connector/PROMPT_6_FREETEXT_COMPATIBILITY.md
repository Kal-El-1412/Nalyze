# Prompt 6: Free-Text Chat Compatibility

## Objective

Ensure free-text chat still works for exploratory queries alongside the new intent-based system.

## Rules

1. **If user types in text box** → send `{ "message": "..." }`
2. **If user clicks button** → send `{ "intent": "...", "value": "..." }`
3. **Backend decides** how to handle each type

## Current Implementation Analysis

### ✅ Already Implemented Correctly

The system already supports both modes! Here's how:

### 1. Typed Messages (Text Box)

**User Action:** Types "Show me sales trends" and presses Enter

**Frontend Flow:**
```typescript
// src/pages/AppLayout.tsx

// Input handler in ChatPanel
const handleSend = () => {
  if (input.trim()) {
    onSendMessage(input.trim());  // Calls AppLayout's handleSendMessage
    setInput('');
  }
};

// AppLayout's message handler
const handleSendMessage = async (content: string) => {
  // Creates user message
  const userMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content,
    timestamp: new Date().toLocaleTimeString(),
  };
  setMessages([...messages, userMessage]);

  // Sends regular message request
  const result = await connectorApi.sendChatMessage({
    datasetId: activeDataset,
    conversationId,
    message: content,  // ✅ Message field populated
    defaultsContext: defaults,
  });

  await handleChatResponse(result.data);
};
```

**Request Sent:**
```json
POST /chat
{
  "datasetId": "sales-2024",
  "conversationId": "conv-123",
  "message": "Show me sales trends",
  "defaultsContext": { ... }
}
```

**Key Point:** ✅ Regular messages include `message` field, reach LLM

---

### 2. Button Clicks (Intent-Based)

**User Action:** Clicks [Trend] button

**Frontend Flow:**
```typescript
// src/components/ChatPanel.tsx

// Button click handler
const handleClarificationChoice = (message: Message, choice: string) => {
  // Save defaults if enabled
  if (datasetName && saveAsDefaultMap[message.id]) {
    const defaultKey = inferDefaultKeyFromQuestion(message.content);
    if (defaultKey) {
      saveDatasetDefault(datasetName, defaultKey, choice);
    }
  }

  // Pass intent to parent
  onClarificationResponse(choice, message.clarificationData?.intent);
};

// src/pages/AppLayout.tsx

// Clarification response handler
const handleClarificationResponse = async (choice: string, intent?: string) => {
  // Creates user message for display
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
      intent,        // ✅ Intent field populated
      value: choice, // ✅ Value field populated
    });

    await handleChatResponse(result.data);

    // Follow-up to continue
    const followUpResult = await connectorApi.sendChatMessage({
      datasetId: activeDataset,
      conversationId,
      message: 'continue',
    });

    await handleChatResponse(followUpResult.data);
  } else {
    // No intent, send as regular message
    handleSendMessage(choice);  // ✅ Falls back to text-based
  }
};
```

**Request Sent:**
```json
POST /chat
{
  "datasetId": "sales-2024",
  "conversationId": "conv-123",
  "intent": "set_analysis_type",
  "value": "Trend"
}
```

**Key Point:** ✅ Intent requests skip LLM, update state directly

---

### 3. Backward Compatibility (Button Without Intent)

**Scenario:** Clarification question doesn't match intent patterns

**Frontend Flow:**
```typescript
// Intent detection returns undefined
const intent = detectIntentFromQuestion("Please specify the column");
// Returns: undefined (no known intent pattern)

// Clarification response handler
const handleClarificationResponse = async (choice: string, intent?: string) => {
  if (intent) {
    // Send intent request
  } else {
    // ✅ Falls back to regular message
    handleSendMessage(choice);
  }
};
```

**Request Sent:**
```json
POST /chat
{
  "datasetId": "sales-2024",
  "conversationId": "conv-123",
  "message": "sales_amount"
}
```

**Key Point:** ✅ Unknown clarifications fall back to text-based flow

---

## Flow Comparison

### Typed Message Flow

```
User types: "Show me top customers by revenue"
↓
handleSendMessage()
↓
POST /chat { message: "Show me top customers by revenue" }
↓
Backend calls LLM
↓
LLM processes request
↓
Response: run_queries or needs_clarification
```

**Characteristics:**
- ✅ LLM processes the request
- ✅ Full natural language understanding
- ✅ Flexible, exploratory
- ✅ May return clarifications or queries

### Button Click Flow (With Intent)

```
User clicks: [Trend]
↓
handleClarificationResponse() with intent="set_analysis_type"
↓
POST /chat { intent: "set_analysis_type", value: "Trend" }
↓
Backend updates state (no LLM)
↓
Response: intent_acknowledged
↓
Frontend sends: POST /chat { message: "continue" }
↓
Backend checks state, returns next clarification or queries
```

**Characteristics:**
- ✅ No LLM call for intent
- ✅ Instant state update
- ✅ Deterministic
- ✅ Never causes loops (single acknowledgment)

### Button Click Flow (Without Intent)

```
User clicks: [Option that doesn't map to intent]
↓
handleClarificationResponse() with intent=undefined
↓
Falls back to handleSendMessage()
↓
POST /chat { message: "Option that doesn't map to intent" }
↓
Backend calls LLM
↓
LLM processes response
↓
Response: run_queries or needs_clarification
```

**Characteristics:**
- ✅ Falls back to text-based
- ✅ Backward compatible
- ✅ Flexible handling

---

## Loop Prevention

### Why Buttons Never Cause Loops

**Intent Acknowledgment Response:**
```json
{
  "type": "intent_acknowledged",
  "intent": "set_analysis_type",
  "value": "Trend",
  "state": { ... }
}
```

**Frontend Handling:**
```typescript
const handleChatResponse = async (response: ChatResponse) => {
  if (response.type === 'intent_acknowledged') {
    // ✅ Only logs, doesn't create message
    console.log(`Intent ${response.intent} acknowledged with value:`, response.value);
    // ✅ Doesn't trigger another request
    return;
  }
  // ... other response types
};
```

**Key Points:**
1. ✅ `intent_acknowledged` doesn't add a message to chat
2. ✅ Frontend explicitly sends "continue" (not automatic loop)
3. ✅ Backend state prevents repeated clarifications
4. ✅ One intent → one acknowledgment → one follow-up

**Flow Trace:**
```
1. POST /chat { intent: "set_analysis_type", value: "Trend" }
   ← Response: intent_acknowledged (no loop)

2. POST /chat { message: "continue" }
   ← Response: needs_clarification OR run_queries (controlled by backend)
```

---

## Test Scenarios

### Scenario 1: Pure Free-Text Exploration

**User:** "What's in this dataset?"

**Expected:**
```
POST /chat
{
  "datasetId": "sales-2024",
  "conversationId": "conv-123",
  "message": "What's in this dataset?"
}
```

**Result:** ✅ LLM processes, provides overview

---

### Scenario 2: Mixed Text and Intents

**User:** "Show me trends"

**Backend:** Returns clarification about analysis type

**User:** Clicks [Trend]

**Expected:**
```
1. POST /chat
   {
     "datasetId": "sales-2024",
     "conversationId": "conv-123",
     "message": "Show me trends"
   }

2. POST /chat
   {
     "datasetId": "sales-2024",
     "conversationId": "conv-123",
     "intent": "set_analysis_type",
     "value": "Trend"
   }
```

**Result:** ✅ First request uses LLM, second uses intent

---

### Scenario 3: Follow-Up Questions

**Initial:** User clicks [Trend], then [Last 30 days]

**Follow-Up:** User types "Can you also show year-over-year?"

**Expected:**
```
POST /chat
{
  "datasetId": "sales-2024",
  "conversationId": "conv-123",
  "message": "Can you also show year-over-year?"
}
```

**Result:** ✅ LLM processes with existing state context

---

### Scenario 4: Clarification Without Intent

**Backend:** Returns clarification that doesn't map to intent
```json
{
  "type": "needs_clarification",
  "question": "Which specific column should I use for the metric?",
  "choices": ["sales_amount", "profit", "quantity"]
}
```

**Frontend:** `detectIntentFromQuestion()` returns `undefined`

**User:** Clicks [sales_amount]

**Expected:**
```
POST /chat
{
  "datasetId": "sales-2024",
  "conversationId": "conv-123",
  "message": "sales_amount"
}
```

**Result:** ✅ Falls back to text-based, LLM interprets

---

## Code Verification

### Entry Points

**1. Text Input:**
```typescript
// ChatPanel.tsx
<input
  type="text"
  value={input}
  onChange={(e) => setInput(e.target.value)}
  onKeyPress={handleKeyPress}  // Calls handleSend on Enter
/>

const handleSend = () => {
  if (input.trim()) {
    onSendMessage(input.trim());  // → AppLayout.handleSendMessage
  }
};
```

**2. Button Click:**
```typescript
// ChatPanel.tsx
<button
  onClick={() => handleClarificationChoice(message, choice)}
>
  {choice}
</button>

const handleClarificationChoice = (message: Message, choice: string) => {
  onClarificationResponse(choice, message.clarificationData?.intent);
  // → AppLayout.handleClarificationResponse
};
```

### Request Routing

```typescript
// AppLayout.tsx

// Route 1: Typed messages
const handleSendMessage = async (content: string) => {
  const result = await connectorApi.sendChatMessage({
    datasetId: activeDataset,
    conversationId,
    message: content,  // ✅ Message field
  });
};

// Route 2: Button clicks
const handleClarificationResponse = async (choice: string, intent?: string) => {
  if (intent) {
    // Intent-based
    const result = await connectorApi.sendChatMessage({
      datasetId: activeDataset,
      conversationId,
      intent,      // ✅ Intent field
      value: choice,
    });
  } else {
    // Text-based fallback
    handleSendMessage(choice);  // ✅ Uses message field
  }
};
```

---

## Backend Handling

### Message Request (LLM Processing)

```python
# app/chat_orchestrator.py

@router.post("/chat")
async def chat(request: ChatOrchestratorRequest):
    if request.message:
        # Free-text message processing
        context = state_manager.get_state(request.conversationId)

        # Call LLM with context
        llm_response = await llm.process(
            message=request.message,
            context=context,
            catalog=catalog
        )

        # LLM returns queries, answer, or clarification
        return llm_response
```

### Intent Request (Direct State Update)

```python
# app/chat_orchestrator.py

@router.post("/chat")
async def chat(request: ChatOrchestratorRequest):
    if request.intent:
        # Intent-based state update
        state_manager.update_state(
            conversation_id=request.conversationId,
            context={request.intent.replace("set_", ""): request.value}
        )

        # Return acknowledgment (no LLM call)
        return {
            "type": "intent_acknowledged",
            "intent": request.intent,
            "value": request.value,
            "state": state_manager.get_state(request.conversationId)
        }
```

---

## Acceptance Criteria

### ✅ Typed messages still reach LLM

**Verification:**
- User types "Show me top customers"
- Request includes `message` field
- Backend calls LLM
- LLM processes natural language
- Returns appropriate response

**Status:** ✅ Working (verified in code)

### ✅ Buttons never cause loops

**Verification:**
- User clicks [Trend] button
- Request includes `intent` field
- Backend returns `intent_acknowledged`
- Frontend logs acknowledgment (doesn't create message)
- Frontend sends explicit "continue" (controlled)
- No automatic re-triggering

**Status:** ✅ Working (verified in code)

### ✅ Both modes coexist

**Verification:**
- User can type exploratory questions
- User can click clarification buttons
- System handles both appropriately
- No conflicts or confusion

**Status:** ✅ Working (verified in code)

---

## Edge Cases

### 1. Empty Message

**Scenario:** User submits empty text

**Handling:**
```typescript
const handleSend = () => {
  if (input.trim()) {  // ✅ Validation
    onSendMessage(input.trim());
  }
};
```

**Result:** ✅ Prevented

### 2. Both Message and Intent

**Scenario:** Client mistakenly sends both

**Handling:** Backend validation (see INTENT_API.md)
```python
if request.message and request.intent:
    raise HTTPException(400, "Cannot provide both message and intent")
```

**Result:** ✅ Error returned

### 3. Neither Message nor Intent

**Scenario:** Empty request

**Handling:** Backend validation
```python
if not request.message and not request.intent:
    raise HTTPException(400, "Must provide either message or intent")
```

**Result:** ✅ Error returned

### 4. Intent Without Value

**Scenario:** Intent but no value

**Handling:** Backend validation
```python
if request.intent and not request.value:
    raise HTTPException(400, "Intent requires value")
```

**Result:** ✅ Error returned

---

## Manual Testing

### Test 1: Pure Text Chat

1. Upload dataset
2. Type: "What columns are in this dataset?"
3. **Verify:** Request has `message` field
4. **Verify:** LLM processes and responds
5. Type: "Show me the top 10 rows"
6. **Verify:** Works as expected

**Expected:** ✅ All text messages work

### Test 2: Intent-Based Clarifications

1. Type: "Show me trends"
2. **Verify:** Clarification appears with buttons
3. Click: [Trend]
4. **Verify:** Request has `intent` and `value` fields
5. **Verify:** Next clarification appears automatically
6. Click: [Last 30 days]
7. **Verify:** Queries generated

**Expected:** ✅ All buttons work

### Test 3: Mixed Mode

1. Type: "Show me trends"
2. Click: [Trend]
3. Click: [Last 30 days]
4. Wait for results
5. Type: "Can you also show week-over-week?"
6. **Verify:** New text message processed

**Expected:** ✅ Can switch between modes

### Test 4: Fallback Behavior

1. Create clarification without known intent
2. Click button
3. **Verify:** Falls back to text-based flow
4. **Verify:** LLM processes button text

**Expected:** ✅ Graceful fallback

---

## Documentation Updates

Added to `INTENT_API.md`:

```markdown
## Free-Text Compatibility

The intent-based system is fully compatible with free-text messages:

### Text Input (Exploratory)
```json
POST /chat
{
  "datasetId": "...",
  "conversationId": "...",
  "message": "Show me sales trends"
}
```
→ LLM processes message

### Button Click (Deterministic)
```json
POST /chat
{
  "datasetId": "...",
  "conversationId": "...",
  "intent": "set_analysis_type",
  "value": "Trend"
}
```
→ Direct state update

### Both coexist seamlessly
- User can type at any time
- User can click buttons when offered
- Backend handles each appropriately
```

---

## Summary

✅ **Free-text chat fully functional**
- Typed messages send `message` field
- LLM processes natural language
- Exploratory queries work as expected

✅ **Intent-based clarifications fully functional**
- Button clicks send `intent` and `value` fields
- State updated directly
- No LLM call for intents

✅ **No loops**
- `intent_acknowledged` only logs
- Follow-up is explicit
- State prevents repetition

✅ **Backward compatible**
- Unknown intents fall back to text
- Old clarifications still work
- Graceful degradation

✅ **Both modes coexist**
- User can switch freely
- No conflicts
- Seamless experience

**Result:** Complete hybrid system supporting both exploratory (text) and deterministic (intent) interactions.
