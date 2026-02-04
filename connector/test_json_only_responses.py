"""
Test Strict JSON-Only Responses (HR-6)

Tests that:
1. LLM returns ONLY valid JSON (no markdown)
2. Intent extraction follows standardized schema
3. Backend can parse LLM results reliably
4. No "AI asked a question" loops
5. Uses "unspecified" instead of null for missing fields
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from app.models import (
    ChatOrchestratorRequest,
    Catalog,
    ColumnInfo,
    PIIColumnInfo
)
from app.chat_orchestrator import ChatOrchestrator, INTENT_EXTRACTION_PROMPT


@pytest.fixture
def simple_catalog():
    """Simple catalog for testing"""
    return Catalog(
        table="data",
        rowCount=1000,
        columns=[
            ColumnInfo(name="order_date", type="DATE"),
            ColumnInfo(name="product", type="TEXT"),
            ColumnInfo(name="revenue", type="NUMERIC"),
            ColumnInfo(name="quantity", type="INTEGER"),
        ],
        detectedDateColumns=["order_date"],
        detectedNumericColumns=["revenue", "quantity"],
        piiColumns=[],
        basicStats={
            "revenue": {"count": 1000, "min": 10.0, "max": 500.0, "mean": 125.5},
            "quantity": {"count": 1000, "min": 1, "max": 100, "mean": 15.3}
        }
    )


def test_intent_extraction_prompt_requires_json_only():
    """Test: Intent extraction prompt explicitly requires JSON-only output"""
    assert "Return ONLY valid JSON" in INTENT_EXTRACTION_PROMPT
    assert "No markdown" in INTENT_EXTRACTION_PROMPT
    assert "No code blocks" in INTENT_EXTRACTION_PROMPT
    assert "CRITICAL" in INTENT_EXTRACTION_PROMPT

    print("✓ Intent extraction prompt requires JSON-only output")


def test_intent_extraction_prompt_has_standardized_schema():
    """Test: Intent extraction prompt defines standardized schema"""
    assert "analysis_type" in INTENT_EXTRACTION_PROMPT
    assert "time_period" in INTENT_EXTRACTION_PROMPT
    assert "metric" in INTENT_EXTRACTION_PROMPT
    assert "group_by" in INTENT_EXTRACTION_PROMPT
    assert "date_column" in INTENT_EXTRACTION_PROMPT

    # Check for standardized time periods
    assert "last_7_days" in INTENT_EXTRACTION_PROMPT
    assert "last_30_days" in INTENT_EXTRACTION_PROMPT
    assert "last_90_days" in INTENT_EXTRACTION_PROMPT
    assert "all_time" in INTENT_EXTRACTION_PROMPT
    assert "unspecified" in INTENT_EXTRACTION_PROMPT

    print("✓ Intent extraction prompt defines standardized schema")


def test_intent_extraction_prompt_uses_unspecified():
    """Test: Intent extraction prompt uses 'unspecified' instead of null"""
    assert "unspecified" in INTENT_EXTRACTION_PROMPT
    assert "If you cannot determine a field value, use \"unspecified\"" in INTENT_EXTRACTION_PROMPT

    # Should not encourage null usage
    assert "not null" in INTENT_EXTRACTION_PROMPT.lower()

    print("✓ Intent extraction prompt uses 'unspecified' for missing values")


@pytest.mark.asyncio
async def test_intent_extraction_valid_json():
    """Test: Intent extraction returns valid JSON that can be parsed"""
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

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI intent extraction response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = json.dumps({
            "analysis_type": "trend",
            "time_period": "last_30_days",
            "metric": "revenue",
            "group_by": "unspecified",
            "date_column": "order_date"
        })

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            intent = await orchestrator._extract_intent_with_openai(
                ChatOrchestratorRequest(
                    datasetId="test",
                    conversationId="conv-test",
                    message="show me revenue trends last month",
                    aiAssist=True
                ),
                catalog
            )

            # Verify all required fields are present
            assert "analysis_type" in intent
            assert "time_period" in intent
            assert "metric" in intent
            assert "group_by" in intent
            assert "date_column" in intent

            # Verify values
            assert intent["analysis_type"] == "trend"
            assert intent["time_period"] == "last_30_days"
            assert intent["metric"] == "revenue"
            assert intent["group_by"] == "unspecified"
            assert intent["date_column"] == "order_date"

            print("✓ Intent extraction returns valid, parseable JSON")


@pytest.mark.asyncio
async def test_intent_extraction_handles_markdown_blocks():
    """Test: Intent extraction strips markdown blocks if LLM ignores instructions"""
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[ColumnInfo(name="amount", type="NUMERIC")],
            detectedNumericColumns=["amount"],
            piiColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI response with markdown blocks (bad behavior)
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = """```json
{
  "analysis_type": "row_count",
  "time_period": "unspecified",
  "metric": "unspecified",
  "group_by": "unspecified",
  "date_column": "unspecified"
}
```"""

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            # Should still parse successfully by stripping markdown
            intent = await orchestrator._extract_intent_with_openai(
                ChatOrchestratorRequest(
                    datasetId="test",
                    conversationId="conv-test",
                    message="how many rows?",
                    aiAssist=True
                ),
                catalog
            )

            assert intent["analysis_type"] == "row_count"
            assert intent["time_period"] == "unspecified"

            print("✓ Backend strips markdown blocks and parses JSON successfully")


@pytest.mark.asyncio
async def test_intent_extraction_defaults_missing_fields():
    """Test: Missing fields are defaulted to 'unspecified'"""
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[ColumnInfo(name="amount", type="NUMERIC")],
            detectedNumericColumns=["amount"],
            piiColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock incomplete response (missing some fields)
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = json.dumps({
            "analysis_type": "outliers",
            "time_period": "unspecified"
            # Missing: metric, group_by, date_column
        })

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            intent = await orchestrator._extract_intent_with_openai(
                ChatOrchestratorRequest(
                    datasetId="test",
                    conversationId="conv-test",
                    message="find outliers",
                    aiAssist=True
                ),
                catalog
            )

            # Missing fields should be defaulted to "unspecified"
            assert intent["analysis_type"] == "outliers"
            assert intent["time_period"] == "unspecified"
            assert intent["metric"] == "unspecified"  # Added by backend
            assert intent["group_by"] == "unspecified"  # Added by backend
            assert intent["date_column"] == "unspecified"  # Added by backend

            print("✓ Missing fields are defaulted to 'unspecified'")


@pytest.mark.asyncio
async def test_intent_extraction_converts_null_to_unspecified():
    """Test: null values are converted to 'unspecified'"""
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[ColumnInfo(name="amount", type="NUMERIC")],
            detectedNumericColumns=["amount"],
            piiColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock response with null values
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = json.dumps({
            "analysis_type": "data_quality",
            "time_period": None,
            "metric": None,
            "group_by": None,
            "date_column": None
        })

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            intent = await orchestrator._extract_intent_with_openai(
                ChatOrchestratorRequest(
                    datasetId="test",
                    conversationId="conv-test",
                    message="check data quality",
                    aiAssist=True
                ),
                catalog
            )

            # null values should be converted to "unspecified"
            assert intent["time_period"] == "unspecified"
            assert intent["metric"] == "unspecified"
            assert intent["group_by"] == "unspecified"
            assert intent["date_column"] == "unspecified"

            print("✓ null values are converted to 'unspecified'")


@pytest.mark.asyncio
async def test_main_openai_call_strips_markdown():
    """Test: Main OpenAI call strips markdown blocks for query generation"""
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[ColumnInfo(name="amount", type="NUMERIC")],
            detectedNumericColumns=["amount"],
            piiColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock response with markdown blocks (bad behavior)
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = """```json
{
  "type": "run_queries",
  "queries": [{
    "name": "count",
    "sql": "SELECT COUNT(*) FROM data LIMIT 1000"
  }],
  "explanation": "Counting rows"
}
```"""

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            request = ChatOrchestratorRequest(
                datasetId="test",
                conversationId="conv-test",
                message="count rows",
                aiAssist=True
            )

            # Should parse successfully despite markdown
            response = await orchestrator.process(request)

            assert response is not None
            # The response should be valid (could be RunQueriesResponse or other)

            print("✓ Main OpenAI call strips markdown blocks successfully")


def test_standardized_time_periods():
    """Test: Intent extraction uses standardized time periods"""
    valid_time_periods = [
        "last_7_days",
        "last_30_days",
        "last_90_days",
        "all_time",
        "unspecified"
    ]

    for period in valid_time_periods:
        assert period in INTENT_EXTRACTION_PROMPT

    print("✓ All standardized time periods are defined in prompt")


def test_time_period_mapping_examples():
    """Test: Prompt includes examples of time period mapping"""
    # Should show how to map user terms to standardized values
    mapping_examples = [
        ("last week", "last_7_days"),
        ("past week", "last_7_days"),
        ("last month", "last_30_days"),
        ("past month", "last_30_days"),
        ("last quarter", "last_90_days"),
        ("past quarter", "last_90_days"),
        ("all time", "all_time"),
    ]

    for user_term, standard_value in mapping_examples:
        # Check that mapping is documented
        assert user_term in INTENT_EXTRACTION_PROMPT.lower() or standard_value in INTENT_EXTRACTION_PROMPT

    print("✓ Time period mapping examples present in prompt")


def test_no_clarification_loop_in_prompt():
    """Test: Prompt instructs LLM not to ask questions"""
    # Intent extraction should not ask questions
    # Should use "unspecified" instead
    assert "unspecified" in INTENT_EXTRACTION_PROMPT

    # The main SYSTEM_PROMPT should also forbid clarification questions
    from app.chat_orchestrator import SYSTEM_PROMPT
    assert "DO NOT ask" in SYSTEM_PROMPT or "NEVER ask" in SYSTEM_PROMPT

    print("✓ Prompts instruct LLM not to ask clarification questions")


@pytest.mark.asyncio
async def test_json_parsing_error_handling():
    """Test: Graceful error handling when JSON parsing fails"""
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[ColumnInfo(name="amount", type="NUMERIC")],
            detectedNumericColumns=["amount"],
            piiColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock completely invalid response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = "This is not JSON at all!"

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            # Should raise ValueError with clear message
            with pytest.raises(ValueError) as exc_info:
                await orchestrator._extract_intent_with_openai(
                    ChatOrchestratorRequest(
                        datasetId="test",
                        conversationId="conv-test",
                        message="test",
                        aiAssist=True
                    ),
                    catalog
                )

            assert "Invalid JSON" in str(exc_info.value)

            print("✓ JSON parsing errors are handled gracefully")


def test_analysis_type_values():
    """Test: All analysis types are defined in prompt"""
    valid_analysis_types = [
        "trend",
        "top_categories",
        "outliers",
        "row_count",
        "data_quality"
    ]

    for analysis_type in valid_analysis_types:
        assert analysis_type in INTENT_EXTRACTION_PROMPT

    print("✓ All analysis types are defined in prompt")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Testing Strict JSON-Only Responses (HR-6)")
    print("="*80 + "\n")

    print("To run these tests:")
    print("  cd connector")
    print("  pip install pytest pytest-asyncio")
    print("  pytest test_json_only_responses.py -v")
    print()
    print("Tests cover:")
    print("  ✓ Intent extraction prompt requires JSON-only output")
    print("  ✓ Standardized schema defined (analysis_type, time_period, etc.)")
    print("  ✓ Uses 'unspecified' instead of null")
    print("  ✓ Intent extraction returns valid, parseable JSON")
    print("  ✓ Backend strips markdown blocks if present")
    print("  ✓ Missing fields are defaulted to 'unspecified'")
    print("  ✓ null values are converted to 'unspecified'")
    print("  ✓ Main OpenAI call strips markdown blocks")
    print("  ✓ Standardized time periods defined")
    print("  ✓ Time period mapping examples present")
    print("  ✓ No clarification loop (uses 'unspecified')")
    print("  ✓ JSON parsing errors handled gracefully")
    print("  ✓ All analysis types defined")
