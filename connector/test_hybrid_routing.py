"""
Test Hybrid Routing Logic (HR-4)

Tests the complete hybrid routing flow:
1. Deterministic router first (confidence >= 0.8)
2. If confidence < 0.8 AND aiAssist=false: ask clarification
3. If confidence < 0.8 AND aiAssist=true: use OpenAI intent extractor
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.models import (
    ChatOrchestratorRequest,
    NeedsClarificationResponse,
    RunQueriesResponse,
    FinalAnswerResponse
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
async def test_high_confidence_bypasses_all_ai(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: High confidence (>=0.8) uses deterministic path
    regardless of aiAssist setting
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True

        orchestrator = ChatOrchestrator()

        # Test with aiAssist=True
        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-high-1",
            message="show me trends last month",
            aiAssist=True
        )

        response = await orchestrator.process(request)

        # Should generate SQL without any AI calls
        assert isinstance(response, RunQueriesResponse)
        assert len(response.queries) > 0

        # Test with aiAssist=False (should also work!)
        request2 = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-high-2",
            message="how many rows",
            aiAssist=False
        )

        response2 = await orchestrator.process(request2)

        # Should still work with aiAssist=False because high confidence
        assert isinstance(response2, RunQueriesResponse)

        print("✓ High confidence bypasses AI (works with aiAssist ON or OFF)")


@pytest.mark.asyncio
async def test_low_confidence_ai_assist_off_asks_clarification(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: Low confidence + aiAssist=false asks for analysis type choices
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True

        orchestrator = ChatOrchestrator()

        # Ambiguous query with AI Assist OFF
        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-low-off",
            message="what's interesting about this data?",
            aiAssist=False
        )

        response = await orchestrator.process(request)

        # Should ask for analysis type
        assert isinstance(response, NeedsClarificationResponse)
        assert "What would you like to analyze?" in response.question
        assert "Trends over time" in response.choices
        assert "Top categories" in response.choices
        assert "Find outliers" in response.choices
        assert "Count rows" in response.choices
        assert "Check data quality" in response.choices
        assert response.intent == "set_analysis_type"

        print("✓ Low confidence + aiAssist OFF → asks for analysis type")


@pytest.mark.asyncio
async def test_low_confidence_ai_assist_off_second_attempt_gives_help(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: After asking once, subsequent unclear messages return helpful message
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True

        orchestrator = ChatOrchestrator()

        conv_id = "conv-low-off-2"

        # First ambiguous query
        request1 = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId=conv_id,
            message="help me",
            aiAssist=False
        )

        response1 = await orchestrator.process(request1)
        assert isinstance(response1, NeedsClarificationResponse)

        # Mark that we asked for clarification
        mock_state_manager.update_context(conv_id, {"clarification_asked": True})

        # Second unclear query
        request2 = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId=conv_id,
            message="something else unclear",
            aiAssist=False
        )

        response2 = await orchestrator.process(request2)

        # Should return helpful message instead of asking again
        assert isinstance(response2, FinalAnswerResponse)
        assert "not sure" in response2.message.lower()
        assert "AI Assist" in response2.message

        print("✓ Low confidence + aiAssist OFF (2nd time) → helpful message")


@pytest.mark.asyncio
async def test_low_confidence_ai_assist_on_extracts_intent(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: Low confidence + aiAssist=true uses OpenAI intent extractor
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test-key"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '''{
            "analysis_type": "trend",
            "time_period": "last_month",
            "metric": "revenue",
            "group_by": null,
            "notes": "User wants revenue trends"
        }'''

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            # Ambiguous query with AI Assist ON
            request = ChatOrchestratorRequest(
                datasetId="test-dataset",
                conversationId="conv-low-on",
                message="I want to see how revenue changed recently",
                aiAssist=True
            )

            response = await orchestrator.process(request)

            # Should call OpenAI intent extractor
            assert mock_client.chat.completions.create.called

            # Should generate SQL after extracting intent
            assert isinstance(response, RunQueriesResponse)

            # Check that state was updated with extracted fields
            state = mock_state_manager.get_state("conv-low-on")
            assert state["context"]["analysis_type"] == "trend"
            assert state["context"]["time_period"] == "last_month"
            assert state["context"]["metric"] == "revenue"

            print("✓ Low confidence + aiAssist ON → uses OpenAI intent extractor")


@pytest.mark.asyncio
async def test_medium_confidence_ai_assist_on_extracts_intent(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: Medium confidence (0.5-0.79) + aiAssist=true uses OpenAI
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test-key"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '''{
            "analysis_type": "top_categories",
            "time_period": "last_quarter",
            "metric": null,
            "group_by": "region",
            "notes": "User wants top regions"
        }'''

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            # Medium confidence query (weak keyword "top")
            request = ChatOrchestratorRequest(
                datasetId="test-dataset",
                conversationId="conv-med-on",
                message="show me the top",
                aiAssist=True
            )

            response = await orchestrator.process(request)

            # Should call OpenAI (confidence ~0.6, below 0.8 threshold)
            assert mock_client.chat.completions.create.called

            print("✓ Medium confidence + aiAssist ON → uses OpenAI")


@pytest.mark.asyncio
async def test_intent_extractor_saves_all_fields(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: Intent extractor saves analysis_type, time_period, metric, group_by, notes
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test-key"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI response with all fields
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '''{
            "analysis_type": "outliers",
            "time_period": "this_week",
            "metric": "price",
            "group_by": "product",
            "notes": "Find unusual prices by product"
        }'''

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            request = ChatOrchestratorRequest(
                datasetId="test-dataset",
                conversationId="conv-all-fields",
                message="find unusual prices",
                aiAssist=True
            )

            response = await orchestrator.process(request)

            # Check all fields were saved to state
            state = mock_state_manager.get_state("conv-all-fields")
            context = state["context"]

            assert context["analysis_type"] == "outliers"
            assert context["time_period"] == "this_week"
            assert context["metric"] == "price"
            assert context["grouping"] == "product"  # Note: group_by → grouping
            assert context["notes"] == "Find unusual prices by product"

            print("✓ Intent extractor saves all fields to state")


@pytest.mark.asyncio
async def test_low_confidence_ai_assist_on_no_api_key_error(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: Low confidence + aiAssist=true + no API key returns error
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = None  # No API key

        orchestrator = ChatOrchestrator()

        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId="conv-no-key",
            message="something unclear",
            aiAssist=True
        )

        response = await orchestrator.process(request)

        # Should return error about missing API key
        assert isinstance(response, FinalAnswerResponse)
        assert "no API key" in response.message.lower()

        print("✓ Low confidence + aiAssist ON + no API key → error message")


@pytest.mark.asyncio
async def test_deterministic_first_priority(
    mock_storage, mock_ingestion, mock_state_manager
):
    """
    Test: Deterministic router always runs first, before checking aiAssist
    """
    with patch('app.chat_orchestrator.config') as mock_config:
        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test-key"

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            # High confidence queries should NEVER call OpenAI
            high_confidence_queries = [
                "show me trends last month",
                "find outliers last week",
                "how many rows",
                "top 10 categories",
            ]

            for query in high_confidence_queries:
                mock_client.chat.completions.create.reset_mock()

                request = ChatOrchestratorRequest(
                    datasetId="test-dataset",
                    conversationId=f"conv-{hash(query)}",
                    message=query,
                    aiAssist=True  # Even with AI Assist ON
                )

                response = await orchestrator.process(request)

                # Should NOT call OpenAI
                assert not mock_client.chat.completions.create.called, \
                    f"OpenAI was called for high confidence query: {query}"

                print(f"✓ '{query}' → deterministic (no OpenAI)")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Testing Hybrid Routing Logic (HR-4)")
    print("="*80 + "\n")

    print("To run these tests:")
    print("  cd connector")
    print("  pip install pytest pytest-asyncio")
    print("  pytest test_hybrid_routing.py -v")
    print()
    print("Tests cover:")
    print("  ✓ High confidence bypasses all AI (works with aiAssist ON/OFF)")
    print("  ✓ Low confidence + aiAssist OFF → asks for analysis type")
    print("  ✓ Low confidence + aiAssist OFF (2nd time) → helpful message")
    print("  ✓ Low confidence + aiAssist ON → uses OpenAI intent extractor")
    print("  ✓ Medium confidence + aiAssist ON → uses OpenAI")
    print("  ✓ Intent extractor saves all fields to state")
    print("  ✓ Low confidence + no API key → error message")
    print("  ✓ Deterministic router always runs first")
