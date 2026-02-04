# Conversation State Manager

## Overview

The `state_manager` provides persistent conversation state across chat messages. State is stored in-memory per `conversationId` and persists throughout the conversation lifecycle.

## Location

`app/state.py`

## API Reference

### `get_state(conversation_id: str) -> Dict[str, Any]`

Get the current state for a conversation. Creates default state if it doesn't exist.

**Returns:**
```python
{
    "conversation_id": "uuid",
    "dataset_id": None,           # UUID of active dataset
    "dataset_name": None,         # Name of active dataset
    "ready": False,               # Whether conversation is ready for queries
    "message_count": 0,           # Number of messages exchanged
    "created_at": "ISO timestamp",
    "last_updated": "ISO timestamp",
    "context": {},                # Custom context data
    "metadata": {}                # Custom metadata
}
```

### `update_state(conversation_id: str, **fields) -> Dict[str, Any]`

Update specific fields in the conversation state. Automatically updates `last_updated` timestamp.

**Example:**
```python
state_manager.update_state(
    conv_id,
    dataset_id="abc-123",
    dataset_name="sales.xlsx",
    ready=True,
    message_count=5
)
```

### `is_ready(conversation_id: str) -> bool`

Check if a conversation is ready for querying. Returns `True` only if:
- `dataset_id` is set (not None)
- `ready` flag is `True`

### `clear_state(conversation_id: str) -> bool`

Remove state for a conversation. Returns `True` if state was removed, `False` if it didn't exist.

### `list_conversations() -> List[str]`

Get list of all active conversation IDs.

### `get_stats() -> Dict[str, Any]`

Get statistics about active conversations.

## Integration Example

### In `/chat` endpoint (app/main.py)

```python
from app.state import state_manager

@app.post("/chat")
async def chat(request: ChatOrchestratorRequest):
    # Get or create conversation state
    state = state_manager.get_state(request.conversationId)

    # Update state with current message
    state_manager.update_state(
        request.conversationId,
        dataset_id=request.datasetId,
        message_count=state["message_count"] + 1
    )

    # Check if ready
    if not state_manager.is_ready(request.conversationId):
        # Mark as ready after first successful query
        state_manager.update_state(
            request.conversationId,
            ready=True
        )

    # Process chat...
    response = await chat_orchestrator.process(request)
    return response
```

### In chat_orchestrator.py

```python
from app.state import state_manager

class ChatOrchestrator:
    async def process(self, request: ChatOrchestratorRequest):
        # Get conversation context
        state = state_manager.get_state(request.conversationId)

        # Use state to maintain context across messages
        if state.get("context"):
            # Restore previous context
            previous_queries = state["context"].get("queries", [])

        # After processing, update context
        state_manager.update_state(
            request.conversationId,
            context={
                "last_query": query_sql,
                "last_result_count": result_count
            }
        )
```

## Testing

Run the test suite:

```bash
cd connector
python3 test_state.py
```

## Thread Safety

The state manager uses threading locks to ensure thread-safe operations when multiple requests access the same conversation simultaneously.

## Persistence

**Current Implementation (MVP):** In-memory storage using module-level dictionary.

**Future Enhancement:** Replace with SQLite or Supabase for persistent storage across restarts.

## State Lifecycle

1. **Creation:** First call to `get_state()` or `update_state()` creates default state
2. **Updates:** Each chat message can update relevant state fields
3. **Cleanup:** Call `clear_state()` when conversation ends or expires
4. **Reset:** Restarting the connector clears all in-memory state

## Best Practices

1. **Always update message_count** when processing new messages
2. **Set ready=True** only after successful dataset ingestion
3. **Store minimal context** - avoid storing large data structures
4. **Clear old conversations** to prevent memory growth
5. **Use context dict** for conversation-specific temporary data
6. **Use metadata dict** for conversation-level permanent data

## Example: Multi-Turn Conversation

```python
# Turn 1: User asks about sales
state_manager.update_state(
    conv_id,
    dataset_id="sales-123",
    ready=True,
    message_count=1,
    context={"topic": "sales_analysis"}
)

# Turn 2: User asks follow-up question
state = state_manager.get_state(conv_id)
# state["message_count"] = 1
# state["context"]["topic"] = "sales_analysis"

state_manager.update_state(
    conv_id,
    message_count=2,
    context={
        **state["context"],
        "last_query": "SELECT SUM(amount) FROM data"
    }
)

# Turn 3: Check conversation status
is_ready = state_manager.is_ready(conv_id)  # True
stats = state_manager.get_stats()
# {"total_conversations": 1, "conversations": ["conv_id"]}
```
