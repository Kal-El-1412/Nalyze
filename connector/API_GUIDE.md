# Complete API Guide

## Overview

This connector provides a stateful, intent-based chat API for data analysis with three key features:

1. **Conversation State Management** - Persistent state per conversation
2. **Intent-Based Requests** - Direct state updates without LLM overhead
3. **Deterministic Clarifications** - Required fields enforced before analysis

## Request Formats

### Message Request (Free Text)
```json
POST /chat
{
  "datasetId": "abc-123",
  "conversationId": "conv-456",
  "message": "Show me trends"
}
```

### Intent Request (Structured)
```json
POST /chat
{
  "datasetId": "abc-123",
  "conversationId": "conv-456",
  "intent": "set_analysis_type",
  "value": "trend"
}
```

## Response Types

### 1. needs_clarification
```json
{
  "type": "needs_clarification",
  "question": "What type of analysis would you like to perform?",
  "choices": ["trend", "comparison", "distribution", "correlation", "summary"]
}
```

### 2. intent_acknowledged
```json
{
  "type": "intent_acknowledged",
  "intent": "set_analysis_type",
  "value": "trend",
  "state": { "conversation_id": "...", "context": {...} },
  "message": "Updated analysis type to 'trend'"
}
```

### 3. run_queries
```json
{
  "type": "run_queries",
  "queries": [{"name": "...", "sql": "...", "reasoning": "..."}]
}
```

### 4. final_answer
```json
{
  "type": "final_answer",
  "message": "Based on the data...",
  "tables": [...],
  "audit": {...}
}
```

## Required Fields

Before LLM processing, these fields must be in conversation state:

1. **analysis_type** - Type of analysis (`trend`, `comparison`, `distribution`, `correlation`, `summary`)
2. **time_period** - Time range (`last_7_days`, `last_30_days`, `last_90_days`, `last_year`, `year_to_date`, `all_time`)

## Conversation Flow Example

```
1. User: "Show me trends"
   → Response: needs_clarification (analysis_type)

2. User: [Selects "trend"]
   → Response: intent_acknowledged

3. User: "Show me trends"
   → Response: needs_clarification (time_period)

4. User: [Selects "last_30_days"]
   → Response: intent_acknowledged

5. User: "Show me trends"
   → Response: run_queries or final_answer (LLM called)
```

## Documentation

- **API_GUIDE.md** (this file) - Complete API overview
- **STATE_MANAGER.md** - State management details
- **INTENT_API.md** - Intent-based API reference
- **CLARIFICATION_FLOW.md** - Clarification logic
- **CHANGES.md** - Implementation changelog

## Key Benefits

✅ Deterministic clarifications (no LLM for required fields)
✅ No repeated questions
✅ State persistence across conversation
✅ Backward compatible
✅ Faster responses
✅ Lower costs
