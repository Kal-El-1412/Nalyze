"""
Test HR-7: No Repeated Clarifications

Tests that:
1. Clarifications are marked as asked
2. Same clarification is not asked twice
3. Intent is properly sent with clarification responses
4. ConversationId remains constant
"""
import pytest
from app.state import state_manager
from app.models import NeedsClarificationResponse, FinalAnswerResponse


def test_state_manager_tracks_clarifications():
    """Test: State manager tracks which clarifications have been asked"""
    conv_id = "test-conv-1"

    # Initially, no clarifications asked
    assert not state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert not state_manager.has_asked_clarification(conv_id, "set_time_period")

    # Mark analysis_type as asked
    state_manager.mark_clarification_asked(conv_id, "set_analysis_type")

    # Verify it's tracked
    assert state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert not state_manager.has_asked_clarification(conv_id, "set_time_period")

    # Mark time_period as asked
    state_manager.mark_clarification_asked(conv_id, "set_time_period")

    # Verify both are tracked
    assert state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert state_manager.has_asked_clarification(conv_id, "set_time_period")

    # Clean up
    state_manager.clear_state(conv_id)

    print("✓ State manager tracks clarifications asked")


def test_state_manager_initializes_with_empty_clarifications():
    """Test: New conversations start with empty clarifications_asked list"""
    conv_id = "test-conv-2"

    # Get state (creates default if not exists)
    state = state_manager.get_state(conv_id)

    # Verify clarifications_asked is initialized as empty list
    assert "context" in state
    assert "clarifications_asked" in state["context"]
    assert state["context"]["clarifications_asked"] == []

    # Clean up
    state_manager.clear_state(conv_id)

    print("✓ New conversations have empty clarifications_asked list")


def test_mark_clarification_idempotent():
    """Test: Marking same clarification twice doesn't duplicate"""
    conv_id = "test-conv-3"

    # Mark once
    state_manager.mark_clarification_asked(conv_id, "set_analysis_type")

    # Get clarifications asked
    state = state_manager.get_state(conv_id)
    clarifications = state["context"]["clarifications_asked"]
    assert clarifications == ["set_analysis_type"]

    # Mark again
    state_manager.mark_clarification_asked(conv_id, "set_analysis_type")

    # Verify not duplicated
    state = state_manager.get_state(conv_id)
    clarifications = state["context"]["clarifications_asked"]
    assert clarifications == ["set_analysis_type"]

    # Clean up
    state_manager.clear_state(conv_id)

    print("✓ Marking same clarification twice doesn't duplicate")


def test_multiple_clarifications_tracked():
    """Test: Multiple different clarifications are all tracked"""
    conv_id = "test-conv-4"

    # Mark multiple clarifications
    state_manager.mark_clarification_asked(conv_id, "set_analysis_type")
    state_manager.mark_clarification_asked(conv_id, "set_time_period")
    state_manager.mark_clarification_asked(conv_id, "set_metric")

    # Verify all are tracked
    assert state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert state_manager.has_asked_clarification(conv_id, "set_time_period")
    assert state_manager.has_asked_clarification(conv_id, "set_metric")

    # Verify list contains all three
    state = state_manager.get_state(conv_id)
    clarifications = state["context"]["clarifications_asked"]
    assert len(clarifications) == 3
    assert "set_analysis_type" in clarifications
    assert "set_time_period" in clarifications
    assert "set_metric" in clarifications

    # Clean up
    state_manager.clear_state(conv_id)

    print("✓ Multiple clarifications are tracked correctly")


def test_clarification_response_has_intent():
    """Test: NeedsClarificationResponse includes intent field"""
    response = NeedsClarificationResponse(
        question="What time period would you like to analyze?",
        choices=["Last week", "Last month", "Last quarter", "Last year"],
        intent="set_time_period"
    )

    assert response.type == "needs_clarification"
    assert response.question == "What time period would you like to analyze?"
    assert response.intent == "set_time_period"
    assert len(response.choices) == 4

    print("✓ NeedsClarificationResponse includes intent field")


def test_clarification_response_has_allow_free_text():
    """Test: NeedsClarificationResponse includes allowFreeText field"""
    response = NeedsClarificationResponse(
        question="What time period would you like to analyze?",
        choices=["Last week", "Last month"],
        intent="set_time_period",
        allowFreeText=True
    )

    assert response.allowFreeText is True

    # Default is False
    response2 = NeedsClarificationResponse(
        question="What would you like to analyze?",
        choices=["Trends", "Categories"],
        intent="set_analysis_type"
    )

    assert response2.allowFreeText is False

    print("✓ NeedsClarificationResponse includes allowFreeText field")


@pytest.mark.asyncio
async def test_orchestrator_prevents_repeated_clarifications():
    """Test: Chat orchestrator prevents asking same clarification twice"""
    from unittest.mock import Mock, AsyncMock, patch
    from app.models import ChatOrchestratorRequest, Catalog, ColumnInfo
    from app.chat_orchestrator import ChatOrchestrator

    conv_id = "test-conv-5"

    # Mock storage and ingestion
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[
                ColumnInfo(name="order_date", type="DATE"),
                ColumnInfo(name="revenue", type="NUMERIC")
            ],
            detectedDateColumns=["order_date"],
            detectedNumericColumns=["revenue"],
            piiColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = False
        mock_config.openai_api_key = None
        mock_config.validate_ai_mode_for_request = Mock(return_value=(False, None))

        orchestrator = ChatOrchestrator()

        # First request - should ask for analysis type
        request1 = ChatOrchestratorRequest(
            datasetId="test",
            conversationId=conv_id,
            message="show me data",
            aiAssist=False
        )

        response1 = await orchestrator.process(request1)

        # Should ask for clarification
        assert isinstance(response1, NeedsClarificationResponse)
        assert response1.intent == "set_analysis_type"
        assert "What would you like to analyze?" in response1.question

        # Verify it was marked as asked
        assert state_manager.has_asked_clarification(conv_id, "set_analysis_type")

        # Second request with same vague message - should NOT ask again
        request2 = ChatOrchestratorRequest(
            datasetId="test",
            conversationId=conv_id,
            message="show me something",
            aiAssist=False
        )

        response2 = await orchestrator.process(request2)

        # Should return helpful message, NOT another clarification
        assert isinstance(response2, FinalAnswerResponse)
        assert "not sure" in response2.message.lower() or "try asking" in response2.message.lower()

    # Clean up
    state_manager.clear_state(conv_id)

    print("✓ Orchestrator prevents repeated clarifications")


@pytest.mark.asyncio
async def test_time_period_clarification_not_repeated():
    """Test: Time period clarification is not asked twice"""
    from unittest.mock import Mock, AsyncMock, patch
    from app.models import ChatOrchestratorRequest, Catalog, ColumnInfo, IntentAcknowledgmentResponse
    from app.chat_orchestrator import ChatOrchestrator

    conv_id = "test-conv-6"

    # Mock storage and ingestion
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[
                ColumnInfo(name="order_date", type="DATE"),
                ColumnInfo(name="revenue", type="NUMERIC")
            ],
            detectedDateColumns=["order_date"],
            detectedNumericColumns=["revenue"],
            piiColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = False
        mock_config.validate_ai_mode_for_request = Mock(return_value=(False, None))

        orchestrator = ChatOrchestrator()

        # Set analysis_type via intent (so we know time_period is needed)
        request1 = ChatOrchestratorRequest(
            datasetId="test",
            conversationId=conv_id,
            intent="set_analysis_type",
            value="trend",
            aiAssist=False
        )

        response1 = await orchestrator.process(request1)

        # Should acknowledge intent
        assert isinstance(response1, IntentAcknowledgmentResponse)
        assert response1.intent == "set_analysis_type"

        # Now send message that needs time_period
        request2 = ChatOrchestratorRequest(
            datasetId="test",
            conversationId=conv_id,
            message="show me trends",
            aiAssist=False
        )

        response2 = await orchestrator.process(request2)

        # Should ask for time_period
        assert isinstance(response2, NeedsClarificationResponse)
        assert response2.intent == "set_time_period"

        # Verify it was marked as asked
        assert state_manager.has_asked_clarification(conv_id, "set_time_period")

        # Try again without providing time_period - should NOT ask again
        request3 = ChatOrchestratorRequest(
            datasetId="test",
            conversationId=conv_id,
            message="show me trends again",
            aiAssist=False
        )

        response3 = await orchestrator.process(request3)

        # Should return helpful message, NOT another clarification
        assert isinstance(response3, FinalAnswerResponse)
        assert "time period" in response3.message.lower()
        assert "need" in response3.message.lower() or "specify" in response3.message.lower()

    # Clean up
    state_manager.clear_state(conv_id)

    print("✓ Time period clarification is not asked twice")


def test_conversation_state_persists():
    """Test: Conversation state persists across multiple operations"""
    conv_id = "test-conv-7"

    # Set initial state
    state_manager.update_state(conv_id, dataset_id="dataset-1")

    # Mark clarifications
    state_manager.mark_clarification_asked(conv_id, "set_analysis_type")

    # Update context with analysis_type
    state_manager.update_state(conv_id, context={"analysis_type": "trend"})

    # Retrieve state
    state = state_manager.get_state(conv_id)

    # Verify all data persists
    assert state["dataset_id"] == "dataset-1"
    assert state["context"]["analysis_type"] == "trend"
    assert "set_analysis_type" in state["context"]["clarifications_asked"]

    # Add more clarifications
    state_manager.mark_clarification_asked(conv_id, "set_time_period")

    # Verify both clarifications tracked
    state = state_manager.get_state(conv_id)
    assert len(state["context"]["clarifications_asked"]) == 2
    assert "set_analysis_type" in state["context"]["clarifications_asked"]
    assert "set_time_period" in state["context"]["clarifications_asked"]

    # Clean up
    state_manager.clear_state(conv_id)

    print("✓ Conversation state persists correctly")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Testing HR-7: No Repeated Clarifications")
    print("="*80 + "\n")

    print("To run these tests:")
    print("  cd connector")
    print("  pytest test_clarification_no_repeat.py -v")
    print()
    print("Tests cover:")
    print("  ✓ State manager tracks clarifications asked")
    print("  ✓ New conversations start with empty list")
    print("  ✓ Marking same clarification twice doesn't duplicate")
    print("  ✓ Multiple clarifications tracked correctly")
    print("  ✓ NeedsClarificationResponse includes intent")
    print("  ✓ NeedsClarificationResponse includes allowFreeText")
    print("  ✓ Orchestrator prevents repeated analysis_type clarifications")
    print("  ✓ Orchestrator prevents repeated time_period clarifications")
    print("  ✓ Conversation state persists correctly")
