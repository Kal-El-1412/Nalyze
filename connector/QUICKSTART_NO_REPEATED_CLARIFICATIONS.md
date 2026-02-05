# Quick Start: No Repeated Clarifications (HR-7)

## What It Does

Prevents asking the same clarification question twice in a conversation by:
1. Tracking which clarifications have been asked
2. Checking before asking
3. Providing helpful messages instead of repeating
4. Sending structured intents from UI buttons

## Key Concepts

### Clarification Types

| Type | When Asked | Example |
|------|-----------|---------|
| set_analysis_type | User request is vague, AI Assist OFF | "What would you like to analyze?" |
| set_time_period | Analysis type needs time filtering | "What time period would you like to analyze?" |

### State Tracking

**Per conversation, track which clarifications have been asked:**
```python
{
  "context": {
    "clarifications_asked": ["set_analysis_type", "set_time_period"]
  }
}
```

## Backend Usage

### Check if Clarification Was Asked

```python
from app.state import state_manager

# Check before asking
if state_manager.has_asked_clarification(conversation_id, "set_time_period"):
    # Already asked - return helpful message instead
    return FinalAnswerResponse(
        message="I need a time period. Please specify like 'last week' or 'last month'."
    )
```

### Mark Clarification as Asked

```python
# Mark before returning clarification
state_manager.mark_clarification_asked(conversation_id, "set_time_period")

return NeedsClarificationResponse(
    question="What time period would you like to analyze?",
    choices=["Last week", "Last month", "Last quarter", "Last year"],
    intent="set_time_period"
)
```

### Pattern for Asking Clarifications

```python
# 1. Check if already asked
if state_manager.has_asked_clarification(conv_id, "set_analysis_type"):
    logger.warning("Already asked for analysis_type - not asking again")
    return FinalAnswerResponse(
        message="Try asking about trends, categories, outliers, row counts, or data quality."
    )

# 2. Mark as asked
state_manager.mark_clarification_asked(conv_id, "set_analysis_type")

# 3. Return clarification
return NeedsClarificationResponse(
    question="What would you like to analyze?",
    choices=["Trends over time", "Top categories", "Find outliers", "Count rows", "Check data quality"],
    intent="set_analysis_type"
)
```

## UI Behavior

### ConversationId is Constant

```typescript
// Set once on component mount, never changes
const [conversationId] = useState(() => `conv-${Date.now()}`);
```

**Result:** State persists across all messages in session

### Clarification Buttons Send Intents

```typescript
// User clicks "Last month" button
// UI sends structured intent:
await connectorApi.sendChatMessage({
  datasetId: activeDataset,
  conversationId,
  intent: "set_time_period",
  value: "Last month",
  privacyMode,
  safeMode,
});
```

**Backend receives:**
```python
request.intent == "set_time_period"
request.value == "Last month"
```

### Answered Clarifications are Disabled

**UI automatically:**
- Marks clarification as answered after clicking
- Disables buttons (grayed out)
- Shows "Answered" badge
- Prevents re-clicking

**Code:**
```typescript
// Find and mark the clarification as answered
setMessages(prev => {
  const lastClarificationIndex = [...prev].reverse().findIndex(
    m => m.type === 'clarification' &&
         m.clarificationData?.intent === intent &&
         !m.answered
  );

  if (lastClarificationIndex === -1) return prev;

  const actualIndex = prev.length - 1 - lastClarificationIndex;

  return prev.map((msg, idx) =>
    idx === actualIndex ? { ...msg, answered: true } : msg
  );
});
```

## Example Flow

### First Request (Vague)

```
User: "Show me data"
  ↓
Backend: has_asked_clarification("set_analysis_type") → False
  ↓
Backend: mark_clarification_asked("set_analysis_type")
  ↓
Backend: Returns NeedsClarificationResponse with intent="set_analysis_type"
  ↓
UI: Shows buttons: "Trends over time", "Top categories", etc.
```

### Second Request (Still Vague)

```
User: "Show me something" (still vague)
  ↓
Backend: has_asked_clarification("set_analysis_type") → True ✅
  ↓
Backend: Returns FinalAnswerResponse with helpful message
  ↓
UI: Shows: "I'm not sure how to help. Try asking about trends, categories..."
```

**Result:** ✅ No repeated clarification

### User Answers Clarification

```
User: [Clicks "Trends over time"]
  ↓
UI: Sends {intent: "set_analysis_type", value: "Trends over time"}
UI: Marks clarification as answered (disables buttons)
  ↓
Backend: Updates context: {"analysis_type": "trend"}
Backend: Returns IntentAcknowledgmentResponse
  ↓
Backend: Continues with query generation
```

## State Manager API

### Methods

```python
# Check if clarification was asked
has_asked_clarification(conversation_id: str, clarification_type: str) -> bool

# Mark clarification as asked
mark_clarification_asked(conversation_id: str, clarification_type: str)

# Get full state (includes clarifications_asked list)
get_state(conversation_id: str) -> Dict[str, Any]

# Clear conversation state
clear_state(conversation_id: str) -> bool
```

### State Structure

```python
{
  "conversation_id": "conv-123",
  "dataset_id": "dataset-1",
  "ready": False,
  "message_count": 3,
  "context": {
    "clarifications_asked": ["set_analysis_type", "set_time_period"],
    "analysis_type": "trend",
    "time_period": "last_30_days"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T10:35:00Z"
}
```

## Model Updates

### NeedsClarificationResponse

```python
class NeedsClarificationResponse(BaseModel):
    type: Literal["needs_clarification"] = "needs_clarification"
    question: str
    choices: List[str]
    intent: Optional[str] = None  # ✅ Intent type (e.g., "set_time_period")
    allowFreeText: bool = False   # ✅ Can user type custom response?
    audit: AuditInfo = Field(default_factory=AuditInfo)
```

**Usage:**
```python
return NeedsClarificationResponse(
    question="What time period would you like to analyze?",
    choices=["Last week", "Last month", "Last quarter", "Last year"],
    intent="set_time_period",  # ✅ Required for tracking
    allowFreeText=False
)
```

## Common Patterns

### Pattern 1: Prevent Repeated Clarification

```python
# Check → Mark → Ask
if state_manager.has_asked_clarification(conv_id, clarification_type):
    return FinalAnswerResponse(message="Helpful message here")

state_manager.mark_clarification_asked(conv_id, clarification_type)

return NeedsClarificationResponse(
    question="Your question here",
    choices=[...],
    intent=clarification_type
)
```

### Pattern 2: Process Structured Intent

```python
# User clicked clarification button
if request.intent == "set_time_period":
    # Update context
    state_manager.update_state(
        request.conversationId,
        context={"time_period": normalize_time_period(request.value)}
    )

    # Return acknowledgment
    return IntentAcknowledgmentResponse(
        intent=request.intent,
        value=request.value,
        state=state_manager.get_state(request.conversationId),
        message="Time period set"
    )
```

### Pattern 3: Check State Readiness

```python
def _is_state_ready(self, context: Dict[str, Any]) -> bool:
    analysis_type = context.get("analysis_type")
    time_period = context.get("time_period")

    # Some analysis types don't need time_period
    if analysis_type in ["row_count", "data_quality", "outliers"]:
        return analysis_type is not None

    # Trend analysis needs time_period
    if analysis_type == "trend":
        return analysis_type is not None and time_period is not None

    return False
```

## Testing

**Quick test:**
```bash
cd connector
pytest test_clarification_no_repeat.py -v
```

**What's tested:**
- ✅ State manager tracks clarifications
- ✅ Prevents duplicates
- ✅ Orchestrator checks before asking
- ✅ Model includes intent field
- ✅ Conversation state persists

## Debugging

**Check clarification tracking:**
```python
from app.state import state_manager

# Get state
state = state_manager.get_state("conv-123")

# Check clarifications asked
clarifications = state["context"]["clarifications_asked"]
print(f"Clarifications asked: {clarifications}")

# Check specific clarification
has_asked = state_manager.has_asked_clarification("conv-123", "set_time_period")
print(f"Asked for time_period: {has_asked}")
```

**Logs to watch:**
```
INFO: Marked clarification 'set_analysis_type' as asked for conv-123
WARNING: Already asked for time_period - not asking again
```

## Edge Cases

### User Never Answers

**First time:**
- Ask clarification

**Second time:**
- Return helpful message
- User can type response in message

### User Provides Conflicting Info

**Behavior:**
- Context updated with latest value
- Clarification still marked as asked
- Won't ask again even if user changes mind

### New Clarification Type

**To add:**
1. Define clarification type string (e.g., "set_metric")
2. Add check and mark logic in orchestrator
3. Return NeedsClarificationResponse with intent
4. No schema changes needed!

## Best Practices

**Do:**
- ✅ Always check before asking clarification
- ✅ Always mark after checking
- ✅ Always include intent in NeedsClarificationResponse
- ✅ Return helpful messages when already asked

**Don't:**
- ❌ Ask clarification without checking
- ❌ Forget to mark after asking
- ❌ Return clarification without intent
- ❌ Return same clarification twice

---

**Status:** ✅ Production ready

**Complexity:** Low (simple state tracking)

**Performance:** Fast (in-memory state checks)

**User Experience:** Excellent (no repeated questions, clear feedback)
