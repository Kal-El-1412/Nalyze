"""
Test Router Integration (HR-3)

Tests that the deterministic router is properly integrated
into the chat orchestrator and works end-to-end.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.models import (
    ChatOrchestratorRequest,
    FinalAnswerResponse,
    NeedsClarificationResponse,
    RunQueriesResponse
)
from app.chat_orchestrator import ChatOrchestrator


@pytest.fixture
def mock_storage():
    """Mock storage with test dataset"""
    with patch('app.chat_orchestrator.storage') as mock:
        mock.get_dataset = AsyncMock(return_value={
            "datasetId": "test-dataset",
            "status": "ingested",
            "name": "Test Dataset"
        })
        yield mock


@pytest.fixture
def mock_ingestion():
    """Mock ingestion pipeline with test catalog"""
    with patch('app.chat_orchestrator.ingestion_pipeline') as mock:
        mock.load_catalog = AsyncMock(return_value={
            "table": "data",
            "rowCount": 1000,
            "columns": [
                {"name": "date", "type": "DATE"},
                {"name": "amount", "type": "NUMERIC"},
                {"name": "category", "type": "TEXT"}
            ],
            "detectedDateColumns": ["date"],
            "detectedNumericColumns": ["amount"]
        })
        yield mock


@pytest.fixture
def mock_state_manager():
    """Mock state manager"""
    with patch('app.chat_orchestrator.state_manager') as mock:
        state_storage = {}

        def get_state(conv_id):
            return state_storage.get(conv_id, {"context": {}})

        def update_context(conv_id, updates):
            if conv_id not in state_storage:
                state_storage[conv_id] = {"context": {}}
            state_storage[conv_id]["context"].update(updates)

        mock.get_state = get_state
        mock.update_context = update_context
        yield mock


@pytest.mark.asyncio
async def test_high_confidence_with_time_period_generates_sql(
    mock_storage, mock_ingestion, mock_state_manager
):
    """Test: High confidence query with time period generates SQL directly"""

    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = None  # No API key needed!

        orchestrator = ChatOrchestrator()

        # Request with high confidence and time period
        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-123",
            message="show me trends last month",
            aiAssist=True
        )

        response = await orchestrator.process(request)

        # Should generate SQL without OpenAI call
        assert isinstance(response, RunQueriesResponse)
        assert len(response.queries) > 0
        assert "trend" in response.explanation.lower() or "month" in response.explanation.lower()

        # Check state was updated
        state = mock_state_manager.get_state("conv-123")
        assert state["context"]["analysis_type"] == "trend"
        assert state["context"]["time_period"] == "last_month"

        print("✓ High confidence with time period → SQL generated (no OpenAI)")


@pytest.mark.asyncio
async def test_high_confidence_without_time_period_asks_clarification(
    mock_storage, mock_ingestion, mock_state_manager
):
    """Test: High confidence query without time period asks for it"""

    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = None  # No API key needed!

        orchestrator = ChatOrchestrator()

        # Request with high confidence but no time period
        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-456",
            message="show me the trends",
            aiAssist=True
        )

        response = await orchestrator.process(request)

        # Should ask for time period
        assert isinstance(response, NeedsClarificationResponse)
        assert "time period" in response.question.lower()
        assert response.intent == "set_time_period"

        # Check state was updated with analysis_type
        state = mock_state_manager.get_state("conv-456")
        assert state["context"]["analysis_type"] == "trend"

        print("✓ High confidence without time period → clarification asked (no OpenAI)")


@pytest.mark.asyncio
async def test_row_count_no_time_period_needed(
    mock_storage, mock_ingestion, mock_state_manager
):
    """Test: Row count query doesn't need time period"""

    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = None  # No API key needed!

        orchestrator = ChatOrchestrator()

        # Row count query
        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-789",
            message="how many rows",
            aiAssist=True
        )

        response = await orchestrator.process(request)

        # Should generate SQL immediately (row_count doesn't need time_period)
        assert isinstance(response, RunQueriesResponse)
        assert len(response.queries) > 0
        assert "count" in response.queries[0].sql.lower()

        print("✓ Row count query → SQL generated immediately (no time period needed)")


@pytest.mark.asyncio
async def test_low_confidence_requires_openai(
    mock_storage, mock_ingestion, mock_state_manager
):
    """Test: Low confidence query requires OpenAI"""

    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = None  # No API key

        orchestrator = ChatOrchestrator()

        # Low confidence query
        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-abc",
            message="what's interesting about this data?",
            aiAssist=True
        )

        response = await orchestrator.process(request)

        # Should return error about missing API key
        assert isinstance(response, FinalAnswerResponse)
        assert "no API key" in response.message.lower()

        print("✓ Low confidence query → requires OpenAI (friendly error)")


@pytest.mark.asyncio
async def test_deterministic_router_bypasses_openai(
    mock_storage, mock_ingestion, mock_state_manager
):
    """Test: Deterministic router never calls OpenAI for high confidence"""

    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test-key"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            # High confidence queries
            high_confidence_queries = [
                "show me trends last month",
                "find outliers last week",
                "how many rows",
                "top 10 categories last quarter",
            ]

            for query in high_confidence_queries:
                conv_id = f"conv-{hash(query)}"
                request = ChatOrchestratorRequest(
                    datasetId="test-dataset",
                    conversationId=conv_id,
                    message=query,
                    aiAssist=True
                )

                response = await orchestrator.process(request)

                # Should NOT call OpenAI
                assert not mock_client.chat.completions.create.called, \
                    f"OpenAI was called for high confidence query: {query}"

                # Should return RunQueriesResponse or NeedsClarificationResponse
                assert isinstance(response, (RunQueriesResponse, NeedsClarificationResponse))

                print(f"✓ '{query}' → no OpenAI call")


@pytest.mark.asyncio
async def test_confidence_threshold_behavior(
    mock_storage, mock_ingestion, mock_state_manager
):
    """Test: Confidence threshold of 0.8 works correctly"""

    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test-key"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI for low confidence queries
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '''{
            "type": "needs_clarification",
            "question": "What would you like to analyze?",
            "choices": ["Trends", "Categories"]
        }'''

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            # Test queries at different confidence levels
            test_cases = [
                ("show trends over time", True, "high confidence - no OpenAI"),
                ("show me the top", False, "medium confidence - uses OpenAI"),
                ("what is this", False, "low confidence - uses OpenAI"),
            ]

            for query, should_skip_openai, description in test_cases:
                mock_client.chat.completions.create.reset_mock()

                conv_id = f"conv-{hash(query)}"
                request = ChatOrchestratorRequest(
                    datasetId="test-dataset",
                    conversationId=conv_id,
                    message=query,
                    aiAssist=True
                )

                response = await orchestrator.process(request)

                if should_skip_openai:
                    assert not mock_client.chat.completions.create.called, \
                        f"OpenAI was called for: {query}"
                    print(f"✓ '{query}' → {description}")
                else:
                    assert mock_client.chat.completions.create.called, \
                        f"OpenAI was NOT called for: {query}"
                    print(f"✓ '{query}' → {description}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Testing Router Integration (HR-3)")
    print("="*80 + "\n")

    import asyncio

    # Note: These tests require pytest-asyncio to run properly
    # Run with: pytest test_router_integration.py -v

    print("To run these tests:")
    print("  cd connector")
    print("  pip install pytest pytest-asyncio")
    print("  pytest test_router_integration.py -v")
    print()
    print("Tests cover:")
    print("  ✓ High confidence + time period → SQL generated")
    print("  ✓ High confidence - time period → clarification asked")
    print("  ✓ Row count → no time period needed")
    print("  ✓ Low confidence → requires OpenAI")
    print("  ✓ Deterministic router bypasses OpenAI")
    print("  ✓ Confidence threshold (0.8) behavior")
