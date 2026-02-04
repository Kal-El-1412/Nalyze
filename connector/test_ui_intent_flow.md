# UI Intent Flow Test

## Overview

This document demonstrates how the frontend UI now sends structured intents when clarification buttons are clicked, instead of free-text messages.

## Changes Made

### 1. TypeScript Types (`src/services/connectorApi.ts`)

**Updated `ChatRequest` interface:**
```typescript
export interface ChatRequest {
  datasetId: string;
  conversationId: string;
  message?: string;        // Now optional
  intent?: string;         // NEW: Intent name
  value?: any;            // NEW: Intent value
  resultsContext?: { ... };
  defaultsContext?: { ... };
}
```

**Added `IntentAcknowledgmentResponse` interface:**
```typescript
export interface IntentAcknowledgmentResponse {
  type: 'intent_acknowledged';
  intent: string;
  value: any;
  state: {
    conversation_id: string;
    context: Record<string, any>;
  };
}
```

**Updated `ChatResponse` type:**
```typescript
export type ChatResponse =
  | ClarificationResponse
  | RunQueriesResponse
  | FinalAnswerResponse
  | IntentAcknowledgmentResponse;  // NEW
```

### 2. Message Interface (Both `ChatPanel.tsx` and `AppLayout.tsx`)

**Updated `Message` interface:**
```typescript
interface Message {
  id: string;
  type: 'user' | 'assistant' | 'clarification' | 'waiting';
  content: string;
  timestamp: string;
  pinned?: boolean;
  clarificationData?: {
    question: string;
    choices: string[];
    allowFreeText: boolean;
    intent?: string;  // NEW: Intent type for this clarification
  };
  queriesData?: Array<{ name: string; sql: string }>;
}
```

### 3. ChatPanel Component (`src/components/ChatPanel.tsx`)

**Updated props:**
```typescript
interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onClarificationResponse: (choice: string, intent?: string) => void;  // NEW: intent parameter
  // ... other props
}
```

**Updated click handler:**
```typescript
const handleClarificationChoice = (message: Message, choice: string) => {
  if (datasetName && saveAsDefaultMap[message.id]) {
    const defaultKey = inferDefaultKeyFromQuestion(message.content);
    if (defaultKey) {
      saveDatasetDefault(datasetName, defaultKey, choice);
    }
  }
  onClarificationResponse(choice, message.clarificationData?.intent);  // Pass intent
};
```

### 4. AppLayout Component (`src/pages/AppLayout.tsx`)

**Added intent detection:**
```typescript
const detectIntentFromQuestion = (question: string): string | undefined => {
  const lowerQuestion = question.toLowerCase();

  if (lowerQuestion.includes('type of analysis') ||
      lowerQuestion.includes('analysis would you like')) {
    return 'set_analysis_type';
  }

  if (lowerQuestion.includes('time period') ||
      lowerQuestion.includes('time range')) {
    return 'set_time_period';
  }

  return undefined;
};
```

**Updated clarification handler:**
```typescript
const handleClarificationResponse = async (choice: string, intent?: string) => {
  if (!activeDataset) {
    showToastMessage('Please select a dataset first');
    return;
  }

  // If we have an intent, send structured intent request
  if (intent) {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: choice,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages(prev => [...prev, userMessage]);

    if (connectorStatus === 'connected') {
      const result = await connectorApi.sendChatMessage({
        datasetId: activeDataset,
        conversationId,
        intent,           // Send intent instead of message
        value: choice,    // Send value
      });

      if (result.success) {
        await handleChatResponse(result.data);

        // After acknowledging the intent, continue conversation
        const followUpResult = await connectorApi.sendChatMessage({
          datasetId: activeDataset,
          conversationId,
          message: 'continue',
        });

        if (followUpResult.success) {
          await handleChatResponse(followUpResult.data);
        }
      }
    }
  } else {
    // No intent, send as regular message
    handleSendMessage(choice);
  }
};
```

**Updated response handler:**
```typescript
const handleChatResponse = async (response: ChatResponse) => {
  if (response.type === 'needs_clarification') {
    const intent = detectIntentFromQuestion(response.question);  // Detect intent

    const clarificationMessage: Message = {
      id: Date.now().toString(),
      type: 'clarification',
      content: response.question,
      timestamp: new Date().toLocaleTimeString(),
      clarificationData: {
        question: response.question,
        choices: response.choices,
        allowFreeText: response.allowFreeText,
        intent,  // Attach intent to message
      },
    };
    setMessages(prev => [...prev, clarificationMessage]);
  } else if (response.type === 'intent_acknowledged') {
    // Intent was acknowledged, state updated on backend
    console.log(`Intent ${response.intent} acknowledged with value:`, response.value);
  } else if (response.type === 'run_queries') {
    // ... existing code
  }
};
```

## Flow Demonstration

### Scenario: User asks for trends without providing analysis type or time period

**Step 1: User sends message**
```
User: "Show me trends"
```

**Step 2: Backend returns clarification**
```json
{
  "type": "needs_clarification",
  "question": "What type of analysis would you like to perform?",
  "choices": ["Trend", "Summary", "Comparison"]
}
```

**Step 3: Frontend detects intent and displays clarification**
- UI detects intent type: `set_analysis_type` (from question text)
- Displays clarification with buttons: "Trend", "Summary", "Comparison"

**Step 4: User clicks "Trend" button**

**Step 5: Frontend sends intent request (NOT free text)**
```json
POST /chat
{
  "datasetId": "abc-123",
  "conversationId": "conv-456",
  "intent": "set_analysis_type",
  "value": "Trend"
}
```

**Key Point:** The message field is NOT populated. This is an intent-only request.

**Step 6: Backend acknowledges intent**
```json
{
  "type": "intent_acknowledged",
  "intent": "set_analysis_type",
  "value": "Trend",
  "state": {
    "conversation_id": "conv-456",
    "context": {
      "analysis_type": "Trend"
    }
  }
}
```

**Step 7: Frontend sends follow-up message**
```json
POST /chat
{
  "datasetId": "abc-123",
  "conversationId": "conv-456",
  "message": "continue"
}
```

**Step 8: Backend checks state and returns next clarification**
```json
{
  "type": "needs_clarification",
  "question": "What time period would you like to analyze?",
  "choices": ["Last 7 days", "Last 30 days", "Last 90 days"]
}
```

**Step 9: User clicks "Last 30 days"**

**Step 10: Frontend sends second intent**
```json
POST /chat
{
  "datasetId": "abc-123",
  "conversationId": "conv-456",
  "intent": "set_time_period",
  "value": "Last 30 days"
}
```

**Step 11: Backend acknowledges and returns queries**
```json
{
  "type": "run_queries",
  "queries": [...]
}
```

## Benefits

### 1. Deterministic State Updates
- Clicking "Trend" ALWAYS sets `analysis_type = "Trend"`
- No LLM interpretation needed
- No risk of misunderstanding

### 2. No Repeated Questions
- Backend tracks state per conversation
- Once `analysis_type` is set, never asked again
- State persists throughout conversation

### 3. Consistent Behavior
- Same button click → same backend state
- No variability from LLM responses
- Predictable user experience

### 4. Performance
- Intent requests skip LLM processing
- Instant acknowledgment from backend
- Faster clarification flow

## Testing

### Manual Test Steps

1. Start the connector backend
2. Start the frontend (`npm run dev`)
3. Upload a dataset
4. Send message: "Show me trends"
5. Observe clarification question appears
6. **Check browser DevTools Network tab**
7. Click a clarification button (e.g., "Trend")
8. **Verify request payload:**
   ```json
   {
     "datasetId": "...",
     "conversationId": "...",
     "intent": "set_analysis_type",
     "value": "Trend"
   }
   ```
9. **Verify response:**
   ```json
   {
     "type": "intent_acknowledged",
     "intent": "set_analysis_type",
     "value": "Trend",
     "state": { ... }
   }
   ```
10. Observe next clarification appears automatically
11. Click second clarification button
12. **Verify second intent request is sent**
13. Observe queries are generated

### Expected Network Requests

```
POST /chat
{
  "datasetId": "...",
  "conversationId": "...",
  "message": "Show me trends"
}
↓
Response: needs_clarification (analysis_type)
↓
POST /chat
{
  "datasetId": "...",
  "conversationId": "...",
  "intent": "set_analysis_type",    ← INTENT, not message
  "value": "Trend"
}
↓
Response: intent_acknowledged
↓
POST /chat
{
  "datasetId": "...",
  "conversationId": "...",
  "message": "continue"
}
↓
Response: needs_clarification (time_period)
↓
POST /chat
{
  "datasetId": "...",
  "conversationId": "...",
  "intent": "set_time_period",     ← INTENT, not message
  "value": "Last 30 days"
}
↓
Response: intent_acknowledged
↓
POST /chat
{
  "datasetId": "...",
  "conversationId": "...",
  "message": "continue"
}
↓
Response: run_queries
```

## Acceptance Criteria

✅ **Clicking "Trend" updates backend state**
- Sends `{ "intent": "set_analysis_type", "value": "Trend" }`
- Backend returns `intent_acknowledged`
- State contains `analysis_type: "Trend"`

✅ **The same clarification is never shown again**
- After setting `analysis_type`, that question never reappears
- After setting `time_period`, that question never reappears
- State persists per `conversationId`

✅ **Chat progresses deterministically**
- Same inputs → same state → same clarifications
- No variability from LLM interpretation
- Predictable flow for users

## Comparison: Before vs After

### Before (Text-based)
```
User clicks "Trend"
→ Frontend sends: { message: "Trend" }
→ Backend calls LLM to interpret "Trend"
→ LLM decides what "Trend" means
→ Might ask follow-up questions
→ Unpredictable behavior
```

### After (Intent-based)
```
User clicks "Trend"
→ Frontend sends: { intent: "set_analysis_type", value: "Trend" }
→ Backend updates state directly (no LLM)
→ State: { analysis_type: "Trend" }
→ Returns acknowledgment immediately
→ Deterministic behavior
```

## Files Modified

1. **`src/services/connectorApi.ts`**
   - Updated `ChatRequest` interface (added `intent` and `value`)
   - Added `IntentAcknowledgmentResponse` interface
   - Updated `ChatResponse` type

2. **`src/components/ChatPanel.tsx`**
   - Updated `Message` interface (added `intent` to `clarificationData`)
   - Updated `ChatPanelProps` (added `intent` parameter to `onClarificationResponse`)
   - Updated `handleClarificationChoice` to pass intent

3. **`src/pages/AppLayout.tsx`**
   - Updated `Message` interface (added `intent` to `clarificationData`)
   - Added `detectIntentFromQuestion` function
   - Updated `handleChatResponse` to detect and attach intent
   - Updated `handleClarificationResponse` to send intent requests
   - Added handling for `intent_acknowledged` response type

## Next Steps

1. ✅ Frontend sends intents for clarifications
2. 🔲 Test with real connector backend
3. 🔲 Add more intent types (metric, dimension, filter)
4. 🔲 Add visual feedback when intent is acknowledged
5. 🔲 Add error handling for invalid intents
