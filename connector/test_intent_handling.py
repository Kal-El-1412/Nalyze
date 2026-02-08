"""
Test that clarification option clicks (intent/value) are handled properly.

Acceptance:
- When intent="set_analysis_type" value="Row count" arrives, backend updates state and returns run_queries
- When intent="set_time_period" value="last_30_days" arrives, backend updates state appropriately
- No "Please provide a message" error for intent-based requests
"""
import asyncio
import pytest
from app.chat_orchestrator import ChatOrchestrator
from app.models import ChatOrchestratorRequest
from app.state import state_manager
from app.storage import storage


@pytest.mark.asyncio
async def test_intent_set_analysis_type_row_count():
    """
    Test that clicking 'Row count' option updates state and returns run_queries.
    """
    orchestrator = ChatOrchestrator()

    # Clear any existing state
    conv_id = "test_intent_row_count"
    state_manager.clear_state(conv_id)

    # Mock dataset
    dataset_id = "test_dataset_1"
    await storage.store_dataset({
        "id": dataset_id,
        "name": "test_data",
        "sourceType": "local_file",
        "filePath": "/tmp/test.csv"
    })

    # Create a request with intent (simulating clarification option click)
    request = ChatOrchestratorRequest(
        datasetId=dataset_id,
        conversationId=conv_id,
        message=None,  # No message, just intent/value
        intent="set_analysis_type",
        value="Row count"
    )

    response = await orchestrator.process(request)

    # Should NOT return "Please provide a message"
    assert response.type != "needs_clarification", f"Got needs_clarification: {response}"

    # Should return run_queries or intent_acknowledgment
    assert response.type in ["run_queries", "intent_acknowledgment"], f"Got unexpected type: {response.type}"

    # State should be updated
    state = state_manager.get_state(conv_id)
    context = state.get("context", {})
    assert context.get("analysis_type") == "row_count", f"analysis_type not set: {context}"
    assert context.get("time_period") == "all_time", f"time_period should be all_time for row_count: {context}"

    print(f"✅ Intent handler correctly processed Row count: {response.type}")


@pytest.mark.asyncio
async def test_intent_set_analysis_type_trends():
    """
    Test that clicking 'Trends over time' option updates state correctly.
    """
    orchestrator = ChatOrchestrator()

    conv_id = "test_intent_trends"
    state_manager.clear_state(conv_id)

    dataset_id = "test_dataset_2"
    await storage.store_dataset({
        "id": dataset_id,
        "name": "test_data",
        "sourceType": "local_file",
        "filePath": "/tmp/test.csv"
    })

    request = ChatOrchestratorRequest(
        datasetId=dataset_id,
        conversationId=conv_id,
        message=None,
        intent="set_analysis_type",
        value="Trends over time"
    )

    response = await orchestrator.process(request)

    assert response.type != "needs_clarification" or response.question != "Please provide a message"

    # State should be updated
    state = state_manager.get_state(conv_id)
    context = state.get("context", {})
    assert context.get("analysis_type") == "trend", f"analysis_type should be 'trend': {context}"

    print(f"✅ Intent handler correctly processed Trends over time: {response.type}")


@pytest.mark.asyncio
async def test_intent_set_time_period():
    """
    Test that set_time_period intent updates state correctly.
    """
    orchestrator = ChatOrchestrator()

    conv_id = "test_intent_time_period"
    state_manager.clear_state(conv_id)

    # Pre-populate with analysis_type so time_period is needed
    state_manager.update_context(conv_id, {"analysis_type": "trend"})

    dataset_id = "test_dataset_3"
    await storage.store_dataset({
        "id": dataset_id,
        "name": "test_data",
        "sourceType": "local_file",
        "filePath": "/tmp/test.csv"
    })

    request = ChatOrchestratorRequest(
        datasetId=dataset_id,
        conversationId=conv_id,
        message=None,
        intent="set_time_period",
        value="last_30_days"
    )

    response = await orchestrator.process(request)

    assert response.type != "needs_clarification" or response.question != "Please provide a message"

    # State should be updated
    state = state_manager.get_state(conv_id)
    context = state.get("context", {})
    assert context.get("time_period") == "last_30_days", f"time_period not set: {context}"

    print(f"✅ Intent handler correctly processed time_period: {response.type}")


if __name__ == "__main__":
    asyncio.run(test_intent_set_analysis_type_row_count())
    asyncio.run(test_intent_set_analysis_type_trends())
    asyncio.run(test_intent_set_time_period())
    print("\n✅ All intent handling tests passed!")
