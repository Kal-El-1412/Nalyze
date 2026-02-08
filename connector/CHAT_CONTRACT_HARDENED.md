# Chat Contract Hardening - Complete

## ✅ Implementation Summary

The `/chat` endpoint contract has been hardened with strict validation rules and optional conversationId support.

## Changes Made

### File: `connector/app/models.py`

1. **Added uuid import** for auto-generation of conversation IDs
2. **Made conversationId optional** with `Optional[str] = None`
3. **Enhanced validation logic** in `__init__` to:
   - Strip whitespace from message and intent before validation
   - Enforce: must have either message OR (intent+value), never both, never neither
   - Auto-generate conversationId if not provided
   - Require value when intent is provided

### Contract Rules

```python
class ChatOrchestratorRequest(BaseModel):
    datasetId: str                                    # Required
    conversationId: Optional[str] = None              # Optional - auto-generated if missing

    message: Optional[str] = None                     # Either message
    intent: Optional[str] = None                      # OR intent+value
    value: Optional[Any] = None                       # Required with intent

    privacyMode: Optional[bool] = True
    safeMode: Optional[bool] = False
    aiAssist: Optional[bool] = False

    resultsContext: Optional[ResultsContext] = None
    defaultsContext: Optional[Dict[str, Any]] = None
```

**Validation Rules:**
1. ✓ Must provide either `message` OR `intent`
2. ✗ Cannot provide both `message` AND `intent`
3. ✗ Cannot provide neither `message` NOR `intent`
4. ✗ If `intent` is provided, `value` is required
5. ✓ Empty/whitespace-only strings are treated as missing

**Auto-generation:**
- If `conversationId` is not provided, generates: `conv-{uuid4()}`

## Acceptance Tests

### Test 1: Message only (no conversationId)
✅ **Should succeed** - auto-generates conversationId

```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{"datasetId":"ds-123","message":"row count"}'
```

**Expected:** 200 OK with auto-generated `conversationId` like `conv-550e8400-e29b-41d4-a716-446655440000`

### Test 2: Message with conversationId
✅ **Should succeed** - uses provided conversationId

```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId":"ds-123",
    "conversationId":"conv-existing",
    "message":"row count"
  }'
```

**Expected:** 200 OK with `conversationId: "conv-existing"`

### Test 3: Intent with value
✅ **Should succeed**

```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId":"ds-123",
    "intent":"set_analysis_type",
    "value":"outliers"
  }'
```

**Expected:** 200 OK (or intent_acknowledged response)

### Test 4: Intent without value
❌ **Should fail** - value required

```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId":"ds-123",
    "intent":"set_analysis_type"
  }'
```

**Expected:** 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "'value' is required when 'intent' is provided"
    }
  ]
}
```

### Test 5: Both message and intent
❌ **Should fail** - cannot have both

```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId":"ds-123",
    "message":"row count",
    "intent":"set_analysis_type",
    "value":"outliers"
  }'
```

**Expected:** 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Cannot provide both 'message' and 'intent'"
    }
  ]
}
```

### Test 6: Neither message nor intent
❌ **Should fail** - must have one

```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{"datasetId":"ds-123"}'
```

**Expected:** 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Either 'message' or 'intent' must be provided"
    }
  ]
}
```

### Test 7: Empty/whitespace message
❌ **Should fail** - treated as missing

```bash
curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{"datasetId":"ds-123","message":"   "}'
```

**Expected:** 422 Unprocessable Entity (same as Test 6)

## Benefits

1. **No breaking changes** - existing clients with conversationId continue to work
2. **Simpler client code** - no need to generate conversationId client-side
3. **Stricter validation** - prevents malformed requests early
4. **Better error messages** - clear validation feedback
5. **Whitespace handling** - prevents confusion from empty strings

## Migration Guide

### Before (required conversationId)
```typescript
// Client had to generate conversationId
const conversationId = `conv-${crypto.randomUUID()}`;

await fetch('/chat', {
  body: JSON.stringify({
    datasetId: 'ds-123',
    conversationId,  // Required
    message: 'row count'
  })
});
```

### After (optional conversationId)
```typescript
// Simpler - let backend generate it
await fetch('/chat', {
  body: JSON.stringify({
    datasetId: 'ds-123',
    // conversationId optional - auto-generated
    message: 'row count'
  })
});

// Or provide your own if needed
await fetch('/chat', {
  body: JSON.stringify({
    datasetId: 'ds-123',
    conversationId: 'conv-existing',  // Optional
    message: 'row count'
  })
});
```

## Implementation Details

### Auto-generation Logic
```python
def __init__(self, **data):
    super().__init__(**data)

    # Strip whitespace for validation
    msg = (self.message or "").strip()
    intent = (self.intent or "").strip()

    # Validation rules
    if not msg and not intent:
        raise ValueError("Either 'message' or 'intent' must be provided")
    if msg and intent:
        raise ValueError("Cannot provide both 'message' and 'intent'")
    if intent and self.value is None:
        raise ValueError("'value' is required when 'intent' is provided")

    # Auto-generate conversationId if missing
    if not self.conversationId:
        self.conversationId = f"conv-{uuid.uuid4()}"
```

### Why Strip Whitespace?

Empty or whitespace-only strings are treated as missing values. This prevents confusion where a client might send `message: "   "` thinking it's empty, but the validation would accept it as provided.

```python
# Without strip:
message = "   "  # Would pass: bool(message) == True

# With strip:
message = "   ".strip()  # Correctly fails: bool(message) == False
```

## Testing

Run the included test suite to verify all contract rules:

```bash
cd connector
source venv/bin/activate
python test_chat_contract.py
```

Expected output:
```
=== Testing ChatOrchestratorRequest Contract ===

✓ Message only (no conversationId): auto-generated conv-...
✓ Message with conversationId: preserved
✓ Intent with value: valid
✓ Intent without value: correctly rejected
✓ Both message and intent: correctly rejected
✓ Neither message nor intent: correctly rejected
✓ Empty message string: correctly rejected

✅ All contract validation tests passed!
```

## Status

✅ **COMPLETE** - All validation rules implemented and tested
✅ **BACKWARD COMPATIBLE** - No breaking changes for existing clients
✅ **DOCUMENTED** - Comprehensive test cases and examples provided
