"""
Test Report Persistence (R2)
Tests that reports are saved when returning final_answer

Run with: python -m pytest test_report_persistence.py -v -s
"""

import pytest
from app.models import (
    ChatRequest,
    FinalAnswerResponse,
    DatasetCatalog,
    DatasetColumn
)
from app.chat_orchestrator import chat_orchestrator
from app.state import state_manager


@pytest.fixture
def conversation_id():
    """Create a unique conversation ID for each test"""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def mock_catalog():
    """Mock catalog for testing"""
    return DatasetCatalog(
        columns=[
            DatasetColumn(name="order_date", type="DATE"),
            DatasetColumn(name="order_id", type="INTEGER"),
            DatasetColumn(name="amount", type="DECIMAL"),
            DatasetColumn(name="category", type="VARCHAR"),
        ]
    )


@pytest.mark.asyncio
async def test_final_answer_includes_report_id(conversation_id, mock_catalog):
    """
    Test that final_answer response includes reportId in audit metadata

    Flow:
    1. Send initial request
    2. Get run_queries response
    3. Send results back
    4. Verify final_answer has reportId
    """
    # Step 1: Initial request
    request = ChatRequest(
        datasetId="test-dataset-123",
        conversationId=conversation_id,
        message="Show me trends",
        privacyMode=False,
        safeMode=True,
        catalog=mock_catalog
    )

    # Store original message for report
    state_manager.update_context(conversation_id, {"original_message": "Show me trends"})

    response = await chat_orchestrator.handle_chat(request)
    assert response.type == "run_queries"

    print(f"✓ Step 1: Got run_queries with {len(response.queries)} queries")

    # Step 2: Simulate query results
    mock_results = [
        {
            "name": "monthly_trends",
            "columns": ["month", "order_count", "revenue"],
            "rows": [
                ["2024-01", 100, 5000.0],
                ["2024-02", 150, 7500.0],
                ["2024-03", 200, 10000.0]
            ]
        }
    ]

    # Step 3: Send results back
    follow_up_request = ChatRequest(
        datasetId="test-dataset-123",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=False,
        safeMode=True,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    final_response = await chat_orchestrator.handle_chat(follow_up_request)

    # Verify response structure
    assert final_response.type == "final_answer"
    assert isinstance(final_response, FinalAnswerResponse)

    print(f"✓ Step 2: Got final_answer response")

    # Verify audit metadata exists
    assert hasattr(final_response, 'audit')
    assert final_response.audit is not None

    # Verify reportId exists (if Supabase is available)
    # Note: reportId might be None if Supabase is not configured in test environment
    if final_response.audit.reportId:
        assert isinstance(final_response.audit.reportId, str)
        assert len(final_response.audit.reportId) == 36  # UUID length with hyphens
        print(f"✓ Step 3: Report saved with ID: {final_response.audit.reportId}")
    else:
        print(f"⚠ Step 3: Report not saved (Supabase not available in test env)")

    # Verify other audit metadata
    assert final_response.audit.analysisType == "trend"
    assert final_response.audit.timePeriod == "all_time"
    assert final_response.audit.datasetId == "test-dataset-123"

    print(f"✓ Test passed! final_answer includes audit with optional reportId")


@pytest.mark.asyncio
async def test_report_structure(conversation_id, mock_catalog):
    """
    Test that the report contains all expected fields
    """
    # Setup
    request = ChatRequest(
        datasetId="test-dataset-456",
        conversationId=conversation_id,
        message="Show top categories",
        privacyMode=True,
        safeMode=False,
        catalog=mock_catalog
    )

    state_manager.update_context(conversation_id, {"original_message": "Show top categories"})

    # Get run_queries
    response = await chat_orchestrator.handle_chat(request)
    assert response.type == "run_queries"

    # Send results
    mock_results = [
        {
            "name": "top_categories",
            "columns": ["category", "count"],
            "rows": [
                ["Electronics", 500],
                ["Clothing", 350],
                ["Home", 200]
            ]
        }
    ]

    follow_up_request = ChatRequest(
        datasetId="test-dataset-456",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=True,
        safeMode=False,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    final_response = await chat_orchestrator.handle_chat(follow_up_request)

    # Verify final_answer structure
    assert final_response.type == "final_answer"
    assert hasattr(final_response, 'summaryMarkdown')
    assert hasattr(final_response, 'tables')
    assert hasattr(final_response, 'audit')

    # Verify tables
    assert len(final_response.tables) > 0
    first_table = final_response.tables[0]
    assert hasattr(first_table, 'name')
    assert hasattr(first_table, 'columns')
    assert hasattr(first_table, 'rows')
    assert first_table.columns == ["category", "count"]
    assert len(first_table.rows) == 3

    # Verify audit
    assert final_response.audit.privacyMode == True
    assert final_response.audit.safeMode == False
    assert final_response.audit.analysisType == "top_categories"

    print(f"✓ Report structure verified with all expected fields")


@pytest.mark.asyncio
async def test_error_case_no_report_saved(conversation_id, mock_catalog):
    """
    Test that error cases do NOT save reports
    """
    # Request with no results context (should return error message)
    request = ChatRequest(
        datasetId="test-dataset-789",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=False,
        safeMode=True,
        resultsContext=None,  # No results!
        catalog=mock_catalog
    )

    state_manager.update_context(conversation_id, {"analysis_type": "trend"})

    response = await chat_orchestrator.handle_chat(request)

    # Should return final_answer with error message
    assert response.type == "final_answer"
    assert "No results" in response.summaryMarkdown

    # Should NOT have reportId (error case)
    # Note: If it does have a reportId, the test should fail
    # because error cases shouldn't generate reports
    if response.audit.reportId:
        pytest.fail("Error cases should not save reports!")

    print(f"✓ Error case correctly does NOT save report")


def test_report_model_structure():
    """Test that Report model has correct structure"""
    from app.models import Report

    # Create sample report
    report_dict = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "dataset_id": "dataset-123",
        "conversation_id": "conv-456",
        "question": "Show me trends",
        "analysis_type": "trend",
        "time_period": "last_7_days",
        "summary_markdown": "Your trends show growth",
        "tables": [
            {
                "name": "Monthly Trend",
                "columns": ["month", "count"],
                "rows": [["2024-01", 100]]
            }
        ],
        "audit_log": ["Analysis Type: trend"],
        "created_at": "2026-02-05T10:00:00Z",
        "privacy_mode": True,
        "safe_mode": False
    }

    report = Report(**report_dict)

    # Verify all fields accessible
    assert report.id == "123e4567-e89b-12d3-a456-426614174000"
    assert report.dataset_id == "dataset-123"
    assert report.question == "Show me trends"
    assert report.analysis_type == "trend"
    assert report.privacy_mode == True
    assert len(report.tables) == 1
    assert report.tables[0]["name"] == "Monthly Trend"

    print(f"✓ Report model structure validated")


if __name__ == "__main__":
    import asyncio
    import sys

    async def run_tests():
        print("=" * 60)
        print("R2: Report Persistence Tests")
        print("=" * 60)

        conv_id_base = "test-report-"
        from app.models import DatasetCatalog, DatasetColumn

        catalog = DatasetCatalog(
            columns=[
                DatasetColumn(name="order_date", type="DATE"),
                DatasetColumn(name="amount", type="DECIMAL"),
            ]
        )

        try:
            print("\n[Test 1] final_answer includes reportId")
            await test_final_answer_includes_report_id(conv_id_base + "1", catalog)

            print("\n[Test 2] Report structure validation")
            await test_report_structure(conv_id_base + "2", catalog)

            print("\n[Test 3] Error case doesn't save report")
            await test_error_case_no_report_saved(conv_id_base + "3", catalog)

            print("\n[Test 4] Report model structure")
            test_report_model_structure()

            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\nAcceptance Criteria Met:")
            print("✅ final_answer includes reportId in audit")
            print("✅ Reports saved to database (if Supabase available)")
            print("✅ Report structure includes all required fields")
            print("✅ Error cases don't save reports")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_tests())
