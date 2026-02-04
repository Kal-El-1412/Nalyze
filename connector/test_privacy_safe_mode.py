"""
Test Privacy Mode and Safe Mode Enforcement (HR-5)

Tests that:
1. Privacy Mode prevents PII exposure to LLM
2. Safe Mode enforces aggregated queries only
3. SQL validation blocks non-aggregate queries in Safe Mode
4. Audit trail accurately reflects what was shared
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.models import (
    ChatOrchestratorRequest,
    RunQueriesResponse,
    NeedsClarificationResponse,
    Catalog,
    ColumnInfo,
    PIIColumnInfo
)
from app.chat_orchestrator import ChatOrchestrator
from app.pii_redactor import pii_redactor
from app.sql_validator import sql_validator


@pytest.fixture
def catalog_with_pii():
    """Catalog with PII columns"""
    return Catalog(
        table="data",
        rowCount=1000,
        columns=[
            ColumnInfo(name="customer_id", type="INTEGER"),
            ColumnInfo(name="customer_email", type="TEXT"),
            ColumnInfo(name="customer_phone", type="TEXT"),
            ColumnInfo(name="purchase_amount", type="NUMERIC"),
            ColumnInfo(name="purchase_date", type="DATE"),
        ],
        detectedDateColumns=["purchase_date"],
        detectedNumericColumns=["customer_id", "purchase_amount"],
        piiColumns=[
            PIIColumnInfo(name="customer_email", type="EMAIL"),
            PIIColumnInfo(name="customer_phone", type="PHONE")
        ],
        basicStats={
            "customer_id": {"count": 1000, "min": 1, "max": 1000},
            "customer_email": {"count": 1000, "unique": 987},
            "customer_phone": {"count": 950, "unique": 950},
            "purchase_amount": {"count": 1000, "min": 10.0, "max": 500.0, "mean": 125.5}
        }
    )


def test_privacy_mode_redacts_pii_columns(catalog_with_pii):
    """Test: Privacy Mode redacts PII column names to placeholders"""
    redacted_catalog, pii_map = pii_redactor.redact_catalog(catalog_with_pii, privacy_mode=True)

    # Check that PII columns are redacted in column list
    column_names = [col.name for col in redacted_catalog.columns]
    assert "customer_email" not in column_names
    assert "customer_phone" not in column_names
    assert "PII_EMAIL_1" in column_names
    assert "PII_PHONE_1" in column_names

    # Non-PII columns should remain unchanged
    assert "customer_id" in column_names
    assert "purchase_amount" in column_names
    assert "purchase_date" in column_names

    # Check reverse mapping
    assert pii_map["PII_EMAIL_1"] == "customer_email"
    assert pii_map["PII_PHONE_1"] == "customer_phone"

    print("✓ Privacy Mode redacts PII column names")


def test_privacy_mode_removes_pii_statistics(catalog_with_pii):
    """Test: Privacy Mode removes PII statistics from basicStats"""
    redacted_catalog, _ = pii_redactor.redact_catalog(catalog_with_pii, privacy_mode=True)

    # PII column stats should be removed entirely
    assert "customer_email" not in redacted_catalog.basicStats
    assert "customer_phone" not in redacted_catalog.basicStats
    assert "PII_EMAIL_1" not in redacted_catalog.basicStats
    assert "PII_PHONE_1" not in redacted_catalog.basicStats

    # Non-PII stats should remain
    assert "customer_id" in redacted_catalog.basicStats
    assert "purchase_amount" in redacted_catalog.basicStats

    print("✓ Privacy Mode removes PII statistics")


def test_privacy_mode_excludes_pii_from_detected_columns(catalog_with_pii):
    """Test: Privacy Mode excludes PII from detectedNumericColumns, etc."""
    # Add PII column to detectedNumericColumns
    catalog_with_pii.detectedNumericColumns.append("customer_email")

    redacted_catalog, _ = pii_redactor.redact_catalog(catalog_with_pii, privacy_mode=True)

    # PII columns should be excluded from detected columns
    assert "customer_email" not in redacted_catalog.detectedNumericColumns
    assert "customer_phone" not in redacted_catalog.detectedNumericColumns

    # Non-PII columns should remain
    assert "customer_id" in redacted_catalog.detectedNumericColumns
    assert "purchase_amount" in redacted_catalog.detectedNumericColumns

    print("✓ Privacy Mode excludes PII from detected columns lists")


def test_privacy_mode_off_preserves_columns(catalog_with_pii):
    """Test: Privacy Mode OFF keeps original column names"""
    original_catalog, pii_map = pii_redactor.redact_catalog(catalog_with_pii, privacy_mode=False)

    # All columns should be unchanged
    column_names = [col.name for col in original_catalog.columns]
    assert "customer_email" in column_names
    assert "customer_phone" in column_names
    assert "PII_EMAIL_1" not in column_names

    # No mapping should be created
    assert len(pii_map) == 0

    print("✓ Privacy Mode OFF preserves original column names")


def test_safe_mode_validates_aggregate_queries():
    """Test: Safe Mode allows aggregated queries"""
    aggregate_queries = [
        {
            "name": "count_rows",
            "sql": "SELECT COUNT(*) FROM data LIMIT 1000"
        },
        {
            "name": "sum_amount",
            "sql": "SELECT SUM(amount) as total FROM data LIMIT 1000"
        },
        {
            "name": "group_by",
            "sql": "SELECT category, COUNT(*) FROM data GROUP BY category LIMIT 1000"
        }
    ]

    for query in aggregate_queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=True)
        assert valid, f"Query '{query['name']}' should be valid in Safe Mode: {error}"

    print("✓ Safe Mode allows aggregated queries")


def test_safe_mode_blocks_non_aggregate_queries():
    """Test: Safe Mode blocks non-aggregated queries"""
    non_aggregate_queries = [
        {
            "name": "select_all",
            "sql": "SELECT * FROM data LIMIT 10"
        },
        {
            "name": "select_columns",
            "sql": "SELECT id, name, email FROM data LIMIT 100"
        },
        {
            "name": "select_with_where",
            "sql": "SELECT * FROM data WHERE amount > 100 LIMIT 50"
        }
    ]

    for query in non_aggregate_queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=True)
        assert not valid, f"Query '{query['name']}' should be blocked in Safe Mode"
        assert "Safe Mode is ON" in error
        assert "aggregated" in error.lower()

    print("✓ Safe Mode blocks non-aggregated queries")


def test_safe_mode_off_allows_all_queries():
    """Test: Safe Mode OFF allows both aggregate and non-aggregate queries"""
    queries = [
        {"name": "aggregate", "sql": "SELECT COUNT(*) FROM data LIMIT 1000"},
        {"name": "non_aggregate", "sql": "SELECT * FROM data LIMIT 10"}
    ]

    for query in queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=False)
        assert valid, f"Query '{query['name']}' should be valid when Safe Mode is OFF: {error}"

    print("✓ Safe Mode OFF allows both aggregate and non-aggregate queries")


def test_sql_validator_blocks_non_select():
    """Test: SQL validator always blocks non-SELECT statements"""
    dangerous_queries = [
        {"name": "drop", "sql": "DROP TABLE data"},
        {"name": "delete", "sql": "DELETE FROM data WHERE id = 1"},
        {"name": "insert", "sql": "INSERT INTO data VALUES (1, 2, 3)"},
        {"name": "update", "sql": "UPDATE data SET amount = 0"}
    ]

    for query in dangerous_queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=False)
        assert not valid, f"Dangerous query '{query['name']}' should always be blocked"

    print("✓ SQL validator blocks all non-SELECT statements")


def test_sql_validator_requires_limit():
    """Test: SQL validator requires LIMIT clause"""
    query_without_limit = {
        "name": "no_limit",
        "sql": "SELECT COUNT(*) FROM data"
    }

    valid, error = sql_validator.validate_queries([query_without_limit], safe_mode=False)
    assert not valid
    assert "LIMIT" in error

    print("✓ SQL validator requires LIMIT clause")


def test_sql_validator_enforces_max_limit():
    """Test: SQL validator enforces maximum LIMIT value"""
    query_with_high_limit = {
        "name": "high_limit",
        "sql": "SELECT * FROM data LIMIT 100000"  # > MAX_LIMIT (10000)
    }

    valid, error = sql_validator.validate_queries([query_with_high_limit], safe_mode=False)
    assert not valid
    assert "exceeds maximum" in error

    print("✓ SQL validator enforces maximum LIMIT value")


@pytest.mark.asyncio
async def test_openai_call_with_privacy_mode_on():
    """Test: OpenAI receives redacted catalog when Privacy Mode is ON"""
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
                ColumnInfo(name="email", type="TEXT"),
                ColumnInfo(name="amount", type="NUMERIC")
            ],
            piiColumns=[PIIColumnInfo(name="email", type="EMAIL")],
            detectedNumericColumns=["amount"],
            basicStats={"email": {"unique": 100}, "amount": {"mean": 50}}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '''{
            "type": "run_queries",
            "queries": [{
                "name": "count",
                "sql": "SELECT COUNT(*) FROM data LIMIT 1000"
            }],
            "explanation": "Counting rows"
        }'''

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            request = ChatOrchestratorRequest(
                datasetId="test",
                conversationId="conv-privacy",
                message="count rows",
                aiAssist=True,
                privacyMode=True,  # Privacy Mode ON
                safeMode=False
            )

            response = await orchestrator.process(request)

            # Check that OpenAI was called
            assert mock_client.chat.completions.create.called

            # Get the messages sent to OpenAI
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs['messages']

            # Check that Privacy Mode notification was sent
            privacy_messages = [m for m in messages if "PRIVACY MODE IS ON" in m.get('content', '')]
            assert len(privacy_messages) > 0

            # Check that schema mentions PII redaction
            schema_messages = [m for m in messages if "Dataset Schema" in m.get('content', '')]
            assert len(schema_messages) > 0

            # Schema should NOT contain "email" (it should be redacted)
            schema_content = schema_messages[0]['content']
            assert "email" not in schema_content.lower() or "pii_email" in schema_content.lower()

            # Check audit trail
            assert isinstance(response, RunQueriesResponse)
            assert "PII_redacted" in response.audit.sharedWithAI

            print("✓ OpenAI receives redacted catalog with Privacy Mode ON")


@pytest.mark.asyncio
async def test_openai_call_with_safe_mode_on():
    """Test: OpenAI receives Safe Mode instructions"""
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
            piiColumns=[],
            detectedNumericColumns=["amount"],
            basicStats={"amount": {"mean": 50}}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI response with aggregated query
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '''{
            "type": "run_queries",
            "queries": [{
                "name": "stats",
                "sql": "SELECT AVG(amount) as avg_amount FROM data LIMIT 1000"
            }],
            "explanation": "Average amount"
        }'''

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            request = ChatOrchestratorRequest(
                datasetId="test",
                conversationId="conv-safe",
                message="average amount",
                aiAssist=True,
                privacyMode=False,
                safeMode=True  # Safe Mode ON
            )

            response = await orchestrator.process(request)

            # Check that OpenAI was called
            assert mock_client.chat.completions.create.called

            # Get the messages sent to OpenAI
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs['messages']

            # Check that Safe Mode notification was sent
            safe_mode_messages = [m for m in messages if "SAFE MODE IS ON" in m.get('content', '')]
            assert len(safe_mode_messages) > 0

            # Check that system prompt mentions Safe Mode rules
            system_messages = [m for m in messages if m.get('role') == 'system']
            assert len(system_messages) > 0
            assert any("Safe Mode" in m.get('content', '') for m in system_messages)

            # Check audit trail
            assert isinstance(response, RunQueriesResponse)
            assert "safe_mode_no_raw_rows" in response.audit.sharedWithAI

            print("✓ OpenAI receives Safe Mode instructions")


@pytest.mark.asyncio
async def test_safe_mode_rejects_non_aggregate_from_llm():
    """Test: Safe Mode rejects non-aggregate queries generated by LLM"""
    with patch('app.chat_orchestrator.storage') as mock_storage, \
         patch('app.chat_orchestrator.ingestion_pipeline') as mock_ingestion, \
         patch('app.chat_orchestrator.config') as mock_config:

        mock_storage.get_dataset = AsyncMock(return_value={
            "datasetId": "test", "status": "ingested"
        })

        catalog = Catalog(
            table="data",
            rowCount=100,
            columns=[ColumnInfo(name="name", type="TEXT")],
            piiColumns=[],
            detectedNumericColumns=[],
            basicStats={}
        )
        mock_ingestion.load_catalog = AsyncMock(return_value=catalog)

        mock_config.ai_mode = True
        mock_config.openai_api_key = "sk-test"
        mock_config.validate_ai_mode_for_request = Mock(return_value=(True, None))

        # Mock OpenAI response with NON-aggregated query (violates Safe Mode)
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = '''{
            "type": "run_queries",
            "queries": [{
                "name": "raw_rows",
                "sql": "SELECT * FROM data LIMIT 10"
            }],
            "explanation": "Showing raw data"
        }'''

        with patch('app.chat_orchestrator.OpenAI') as MockOpenAI:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(return_value=mock_openai_response)
            MockOpenAI.return_value = mock_client

            orchestrator = ChatOrchestrator()

            request = ChatOrchestratorRequest(
                datasetId="test",
                conversationId="conv-safe-reject",
                message="show me data",
                aiAssist=True,
                privacyMode=False,
                safeMode=True  # Safe Mode ON
            )

            response = await orchestrator.process(request)

            # Should return clarification because query was rejected
            assert isinstance(response, NeedsClarificationResponse)
            assert "Safe Mode is ON" in response.question
            assert "aggregated" in response.question.lower()

            print("✓ Safe Mode rejects non-aggregate queries from LLM")


def test_audit_trail_reflects_actual_modes():
    """Test: Audit trail accurately reflects privacy_mode and safe_mode"""
    from app.chat_orchestrator import chat_orchestrator

    # Mock response data
    response_data = {
        "type": "run_queries",
        "queries": [{
            "name": "test",
            "sql": "SELECT COUNT(*) FROM data LIMIT 1000"
        }],
        "explanation": "Test"
    }

    # Test all combinations
    test_cases = [
        (False, False, ["schema", "aggregates_only"]),
        (True, False, ["schema", "aggregates_only", "PII_redacted"]),
        (False, True, ["schema", "aggregates_only", "safe_mode_no_raw_rows"]),
        (True, True, ["schema", "aggregates_only", "PII_redacted", "safe_mode_no_raw_rows"])
    ]

    for privacy_mode, safe_mode, expected_audit in test_cases:
        response = chat_orchestrator._parse_response(response_data, safe_mode, privacy_mode)

        assert isinstance(response, RunQueriesResponse)
        for item in expected_audit:
            assert item in response.audit.sharedWithAI, \
                f"Expected '{item}' in audit with privacy={privacy_mode}, safe={safe_mode}"

        print(f"✓ Audit correct for privacy={privacy_mode}, safe={safe_mode}: {response.audit.sharedWithAI}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Testing Privacy Mode and Safe Mode Enforcement (HR-5)")
    print("="*80 + "\n")

    print("To run these tests:")
    print("  cd connector")
    print("  pip install pytest pytest-asyncio")
    print("  pytest test_privacy_safe_mode.py -v")
    print()
    print("Tests cover:")
    print("  ✓ Privacy Mode redacts PII column names")
    print("  ✓ Privacy Mode removes PII statistics")
    print("  ✓ Privacy Mode excludes PII from detected columns")
    print("  ✓ Safe Mode allows aggregated queries")
    print("  ✓ Safe Mode blocks non-aggregated queries")
    print("  ✓ SQL validator blocks non-SELECT statements")
    print("  ✓ SQL validator requires LIMIT clause")
    print("  ✓ SQL validator enforces max LIMIT")
    print("  ✓ OpenAI receives redacted catalog with Privacy Mode")
    print("  ✓ OpenAI receives Safe Mode instructions")
    print("  ✓ Safe Mode rejects non-aggregate queries from LLM")
    print("  ✓ Audit trail accurately reflects modes")
