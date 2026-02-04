# Prompt 4 Summary: Disable LLM-Driven Clarifications

## Objective

Prevent the LLM from asking clarification questions. All clarifications must originate from backend state checks (implemented in Prompt 3).

## Changes Made

### 1. Updated System Prompt

**File:** `app/chat_orchestrator.py`

**Added critical section:**
```
## CRITICAL: No Clarification Questions
- DO NOT ask the user for clarification
- DO NOT use the "needs_clarification" response type
- All required context (analysis type, time period, etc.) is provided by the backend
- You have all the information needed to generate queries
- If something seems ambiguous, make reasonable assumptions based on schema
```

**Removed:**
- "Ask clarifying questions when needed" from responsibilities
- Entire "needs_clarification" response type documentation
- Examples showing LLM asking questions
- Instructions to ask about ambiguous dates/metrics

**Added:**
- "NEVER ask clarifying questions" to responsibilities
- "Handling Ambiguity" section with assumption guidelines
- Examples showing assumption-based responses
- SQL generation rules for handling multiple columns

### 2. Reject LLM Clarification Attempts

**Updated `_parse_response()` method:**

```python
if response_type == "needs_clarification":
    # LLM should NEVER ask for clarification - this is a prompt violation
    logger.error(f"LLM attempted to ask clarification question: {response_data.get('question')}")
    raise ValueError(
        "LLM attempted to ask a clarification question. "
        "All clarifications should be handled by backend state checks. "
        "This indicates the LLM prompt needs updating or the LLM is not following instructions."
    )
```

If the LLM attempts to return a clarification question, it will now raise an error instead of passing it through.

### 3. Pass Conversation State to LLM

**Added import:**
```python
from app.state import state_manager
```

**Updated `_build_messages()` method:**
```python
# Add conversation state context
state = state_manager.get_state(request.conversationId)
context = state.get("context", {})
if context:
    context_info = self._build_context_info(context)
    messages.append({
        "role": "system",
        "content": f"User Preferences:\n{context_info}"
    })
```

**Created `_build_context_info()` method:**
```python
def _build_context_info(self, context: Dict[str, Any]) -> str:
    """Build a summary of user preferences from conversation state"""
    lines = []

    if "analysis_type" in context:
        lines.append(f"Analysis Type: {context['analysis_type']}")

    if "time_period" in context:
        lines.append(f"Time Period: {context['time_period']}")

    # ... other context fields

    return "\n".join(lines) if lines else "No specific preferences set"
```

The LLM now receives all conversation state as "User Preferences" in the system messages.

## How It Works

### Before (Problems):
1. User: "Show me trends"
2. Backend checks state → missing analysis_type → returns clarification
3. User selects "trend"
4. User: "Show me trends"
5. Backend checks state → missing time_period → returns clarification
6. User selects "last_30_days"
7. User: "Show me trends"
8. **LLM called** → might ask "Which metric?" → **LLM clarification!** ❌

### After (Solution):
1. User: "Show me trends"
2. Backend checks state → missing analysis_type → returns clarification
3. User selects "trend"
4. User: "Show me trends"
5. Backend checks state → missing time_period → returns clarification
6. User selects "last_30_days"
7. User: "Show me trends"
8. **LLM called with full state:**
   - User Preferences: analysis_type=trend, time_period=last_30_days
   - Dataset Schema: ...
9. **LLM generates queries** (no clarifications) ✓

## Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Message                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Check state.context                                │
├─────────────────────────────────────────────────────────────┤
│ Missing analysis_type? → Clarification (backend)            │
│ Missing time_period?   → Clarification (backend)            │
│ All present?           → Continue to LLM                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ LLM: Receives messages                                      │
├─────────────────────────────────────────────────────────────┤
│ 1. System Prompt (NEVER ask clarifications)                 │
│ 2. User Preferences (analysis_type, time_period, etc.)      │
│ 3. Dataset Schema                                            │
│ 4. User Message                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ LLM: Generates response                                     │
├─────────────────────────────────────────────────────────────┤
│ - Makes assumptions based on schema                         │
│ - Uses first date column if multiple exist                  │
│ - Analyzes all relevant metrics                             │
│ - Returns run_queries or final_answer ONLY                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Parse response                                     │
├─────────────────────────────────────────────────────────────┤
│ run_queries?       → Execute queries                         │
│ final_answer?      → Return to user                          │
│ needs_clarification? → ERROR (prompt violation)             │
└─────────────────────────────────────────────────────────────┘
```

## Testing

**Test File:** `test_llm_no_clarification.py`

**Tests (6/6 passing):**
1. ✓ System prompt forbids LLM clarifications
2. ✓ No clarification examples in prompt
3. ✓ Ambiguity handled via assumptions
4. ✓ Parse response rejects LLM clarifications
5. ✓ Conversation state passed to LLM
6. ✓ State manager properly imported

**Run test:**
```bash
cd connector
python test_llm_no_clarification.py
```

## Acceptance Criteria

✅ **LLM responses never contain questions**
- System prompt explicitly forbids clarifications
- Examples removed from prompt
- Parse response rejects attempts

✅ **All questions originate from backend logic**
- Backend checks state before calling LLM (Prompt 3)
- Backend returns clarifications deterministically
- LLM never reached until context complete

✅ **LLM has full context from conversation state**
- State manager integrated into orchestrator
- User preferences passed in system messages
- LLM receives analysis_type, time_period, etc.

✅ **LLM makes reasonable assumptions**
- Prompt instructs to use first date column
- Prompt instructs to analyze all metrics
- Prompt instructs to make schema-based decisions

## Benefits

### Separation of Concerns
- **Backend:** Handles clarifications (deterministic, state-based)
- **LLM:** Handles analysis (generative, context-aware)
- Clear boundary between roles

### Consistency
- Same state always produces same clarifications
- No variability from LLM temperature/creativity
- Predictable user experience

### Cost Savings
- No LLM tokens wasted on clarification questions
- Fewer back-and-forth cycles
- Clarifications handled instantly by backend

### Better Context
- LLM receives complete user preferences
- No need to infer user intent
- More accurate query generation

## Files Modified

1. **`app/chat_orchestrator.py`**
   - Updated SYSTEM_PROMPT (removed clarification instructions)
   - Added state_manager import
   - Updated _build_messages() to include state
   - Created _build_context_info() method
   - Updated _parse_response() to reject clarifications

## Documentation Updated

1. **`CHANGES.md`** - Added Prompt 4 section
2. **`IMPLEMENTATION_SUMMARY.md`** - Added Prompt 4 details
3. **`PROMPT_4_SUMMARY.md`** - This file

## Integration with Previous Prompts

**Prompt 1 (State Manager):**
- Prompt 4 uses state_manager to get conversation state
- State includes analysis_type, time_period, etc.

**Prompt 2 (Intent-Based Chat):**
- Intents update state fields
- Prompt 4 reads those fields and passes to LLM

**Prompt 3 (Deterministic Clarifications):**
- Prompt 3 asks clarifications when fields missing
- Prompt 4 ensures LLM never asks (backend only)
- Perfect separation: backend clarifies, LLM analyzes

**Result:** Complete, coherent system with clear responsibilities at each layer.

## Example Scenarios

### Scenario 1: Happy Path

```
1. User: "Show me trends"
   Backend: Missing analysis_type → Clarification

2. User: [Selects "trend"]
   Backend: State updated → Acknowledged

3. User: "Show me trends"
   Backend: Missing time_period → Clarification

4. User: [Selects "last_30_days"]
   Backend: State updated → Acknowledged

5. User: "Show me trends"
   Backend: All fields present → Call LLM
   LLM receives:
     - User Preferences: analysis_type=trend, time_period=last_30_days
     - Dataset Schema: [columns...]
     - Message: "Show me trends"
   LLM returns:
     - type: run_queries
     - queries: [SELECT DATE_TRUNC('month', date_col)...]
```

### Scenario 2: Multiple Date Columns

```
Dataset has: order_date, created_at, updated_at

User: "Show me trends"
Backend: Ensures analysis_type and time_period set
LLM receives:
  - User Preferences: analysis_type=trend, time_period=last_30_days
  - Date Columns: order_date, created_at, updated_at

OLD behavior (wrong):
  LLM: {type: "needs_clarification", question: "Which date column?"}

NEW behavior (correct):
  LLM: Uses first date column (order_date)
  LLM: {type: "run_queries", queries: [SELECT DATE_TRUNC('month', order_date)...]}
```

### Scenario 3: Vague Request

```
User: "Show me the data"
Backend: Ensures analysis_type and time_period set
LLM receives full context

OLD behavior (wrong):
  LLM: {type: "needs_clarification", question: "What would you like to see?"}

NEW behavior (correct):
  LLM: Makes informed decision
  LLM: {type: "run_queries", queries: [SELECT COUNT(*), SUM(amount)...]}
```

## Key Takeaways

1. **LLM cannot ask questions** - System prompt forbids it
2. **Backend handles all clarifications** - Deterministic, state-based
3. **LLM receives full context** - No ambiguity
4. **Separation of concerns** - Clear responsibilities
5. **Better UX** - Consistent, predictable behavior
6. **Cost efficient** - No wasted tokens on clarifications

## Next Steps

1. ✅ LLM clarifications disabled
2. 🔲 Frontend integration (handle clarification responses)
3. 🔲 Add more context fields (metric, dimension, filter)
4. 🔲 Test with real LLM to ensure compliance
5. 🔲 Monitor logs for any prompt violations
