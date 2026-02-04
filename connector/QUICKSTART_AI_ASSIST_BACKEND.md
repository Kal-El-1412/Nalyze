# Quick Start: AI Assist Backend (HR-2)

## What It Does

Gates OpenAI usage based on the `aiAssist` flag from the frontend:
- **OFF:** Never calls OpenAI, returns friendly message
- **ON + No API Key:** Returns friendly error (not 500)
- **ON + API Key:** Uses OpenAI normally

## Request Format

**Body:**
```json
{
  "datasetId": "ds-123",
  "conversationId": "conv-456",
  "message": "show trends",
  "aiAssist": true
}
```

**Header:**
```
X-AI-Assist: on
```

**Default:** `false` (OFF)

## Responses

### AI Assist OFF
```json
{
  "type": "final_answer",
  "message": "AI Assist is currently OFF. To ask questions in natural language, please enable AI Assist using the toggle next to the chat input.",
  "tables": null
}
```

### AI Assist ON + No API Key
```json
{
  "type": "final_answer",
  "message": "AI Assist is ON but no API key is configured. Set OPENAI_API_KEY in .env or turn AI Assist off.",
  "tables": null
}
```

### AI Assist ON + API Key Available
```json
{
  "type": "needs_clarification",
  "question": "What time period?",
  "choices": ["Last week", "Last month"],
  "intent": "set_time_period"
}
```

## Files Modified

1. **app/models.py** - Added `aiAssist` field
2. **app/main.py** - Read `aiAssist` from body/header
3. **app/chat_orchestrator.py** - Gate OpenAI calls

## Testing

```bash
cd connector
python test_ai_assist_gating.py
```

Expected output:
```
✓ Test passed: aiAssist=false returns friendly message
✓ Test passed: aiAssist=true + no API key returns error
✓ Test passed: aiAssist=true + API key calls OpenAI
✓ Test passed: Deterministic path works regardless
✓ Test passed: Request model accepts aiAssist field
```

## Quick Test with curl

**AI Assist OFF:**
```bash
curl -X POST http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -H "X-AI-Assist: off" \
  -d '{
    "datasetId": "test",
    "conversationId": "test-conv",
    "message": "show trends",
    "aiAssist": false
  }'
```

**AI Assist ON (no key):**
```bash
# Unset OPENAI_API_KEY first
curl -X POST http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -H "X-AI-Assist: on" \
  -d '{
    "datasetId": "test",
    "conversationId": "test-conv",
    "message": "show trends",
    "aiAssist": true
  }'
```

## Environment Setup

**Required for AI Assist:**
```bash
# .env
OPENAI_API_KEY=sk-...
AI_MODE=on
```

**Without API key:**
- `aiAssist=false` works (no AI needed)
- `aiAssist=true` returns friendly error

## Acceptance

✅ AI Assist OFF returns friendly message
✅ AI Assist ON without key returns friendly error (not 500)
✅ No OpenAI calls when OFF
✅ OpenAI called when ON with key

---

**Status:** ✅ Ready
