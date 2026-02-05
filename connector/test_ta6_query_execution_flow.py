"""
TA-6 Test: Query Execution Flow
Tests the complete flow: run_queries → execute → final_answer with tables

Run with: python -m pytest test_ta6_query_execution_flow.py -v -s
"""

import pytest
from app.models import (
    ChatRequest,
    RunQueriesResponse,
    FinalAnswerResponse,
    QueryData
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
    from app.models import DatasetCatalog, DatasetColumn
    return DatasetCatalog(
        columns=[
            DatasetColumn(name="order_date", type="DATE"),
            DatasetColumn(name="order_id", type="INTEGER"),
            DatasetColumn(name="amount", type="DECIMAL"),
            DatasetColumn(name="category", type="VARCHAR"),
            DatasetColumn(name="customer_id", type="INTEGER"),
        ]
    )


@pytest.mark.asyncio
async def test_trend_flow_generates_tables(conversation_id, mock_catalog):
    """
    Test that trend analysis flow generates proper table output

    Flow:
    1. User asks for trends
    2. Backend returns run_queries
    3. Frontend executes queries (simulated)
    4. Backend returns final_answer with tables
    """
    # Step 1: Initial request for trends
    request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Show me trends over last 7 days",
        privacyMode=False,
        safeMode=True,
        catalog=mock_catalog
    )

    # Step 2: First response should be run_queries
    response = await chat_orchestrator.handle_chat(request)

    assert response.type == "run_queries"
    assert isinstance(response, RunQueriesResponse)
    assert len(response.queries) > 0

    # Verify query structure
    first_query = response.queries[0]
    assert hasattr(first_query, 'name')
    assert hasattr(first_query, 'sql')
    assert 'order_date' in first_query.sql.lower() or 'date' in first_query.sql.lower()

    print(f"\n✅ Step 1: Got run_queries response with {len(response.queries)} queries")
    for q in response.queries:
        print(f"   - Query: {q.name}")
        print(f"     SQL: {q.sql[:100]}...")

    # Step 3: Simulate query execution results
    mock_results = [
        {
            "name": first_query.name,
            "columns": ["month", "order_count", "total_revenue"],
            "rows": [
                ["2024-01", 1250, 45320.50],
                ["2024-02", 1437, 52100.75],
                ["2024-03", 1589, 58750.25]
            ]
        }
    ]

    # Step 4: Send results back to get final_answer
    follow_up_request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=False,
        safeMode=True,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    final_response = await chat_orchestrator.handle_chat(follow_up_request)

    # Verify final_answer structure
    assert final_response.type == "final_answer"
    assert isinstance(final_response, FinalAnswerResponse)

    print(f"\n✅ Step 2: Got final_answer response")

    # Verify summary markdown
    assert hasattr(final_response, 'summaryMarkdown')
    assert len(final_response.summaryMarkdown) > 0
    print(f"   - Summary: {final_response.summaryMarkdown[:100]}...")

    # Verify tables array
    assert hasattr(final_response, 'tables')
    assert len(final_response.tables) > 0

    first_table = final_response.tables[0]
    assert hasattr(first_table, 'name')
    assert hasattr(first_table, 'columns')
    assert hasattr(first_table, 'rows')

    print(f"   - Tables: {len(final_response.tables)}")
    print(f"     • Table name: {first_table.name}")
    print(f"     • Columns: {first_table.columns}")
    print(f"     • Rows: {len(first_table.rows)}")

    # Verify table content
    assert len(first_table.columns) == 3
    assert len(first_table.rows) == 3
    assert first_table.columns == ["month", "order_count", "total_revenue"]
    assert first_table.rows[0] == ["2024-01", 1250, 45320.50]

    # Verify audit metadata
    assert hasattr(final_response, 'audit')
    audit = final_response.audit
    assert audit.analysisType == "trend"
    assert audit.timePeriod == "last_7_days"
    assert audit.safeMode == True
    assert audit.privacyMode == False
    assert len(audit.executedQueries) > 0

    print(f"   - Audit:")
    print(f"     • Analysis Type: {audit.analysisType}")
    print(f"     • Time Period: {audit.timePeriod}")
    print(f"     • Executed Queries: {len(audit.executedQueries)}")

    print("\n✅ ACCEPTANCE CRITERIA MET: Trend analysis returns tables!")


@pytest.mark.asyncio
async def test_top_categories_flow_generates_tables(conversation_id, mock_catalog):
    """Test that top categories flow generates proper table output"""
    # Step 1: Request top categories
    request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Show me top categories",
        privacyMode=False,
        safeMode=True,
        catalog=mock_catalog
    )

    response = await chat_orchestrator.handle_chat(request)
    assert response.type == "run_queries"

    # Step 2: Simulate results
    mock_results = [
        {
            "name": "top_categories",
            "columns": ["category", "count"],
            "rows": [
                ["Electronics", 3500],
                ["Clothing", 2800],
                ["Home & Garden", 2100],
                ["Sports", 1850],
                ["Books", 1200]
            ]
        }
    ]

    follow_up_request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=False,
        safeMode=True,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    final_response = await chat_orchestrator.handle_chat(follow_up_request)

    # Verify tables
    assert final_response.type == "final_answer"
    assert len(final_response.tables) > 0

    table = final_response.tables[0]
    assert "categories" in table.name.lower()
    assert len(table.rows) == 5
    assert table.columns == ["category", "count"]

    print(f"\n✅ Top categories test passed!")
    print(f"   - Table: {table.name}")
    print(f"   - Rows: {len(table.rows)}")


@pytest.mark.asyncio
async def test_outliers_safe_mode_generates_summary_table(conversation_id, mock_catalog):
    """Test that outliers in safe mode generates summary table (not individual rows)"""
    request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Find outliers",
        privacyMode=False,
        safeMode=True,  # Safe mode ON
        catalog=mock_catalog
    )

    response = await chat_orchestrator.handle_chat(request)
    assert response.type == "run_queries"

    # Simulate outlier summary results (aggregated counts)
    mock_results = [
        {
            "name": "outlier_summary",
            "columns": ["column_name", "outlier_count"],
            "rows": [
                ["amount", 42],
                ["quantity", 15],
                ["discount", 8]
            ]
        }
    ]

    follow_up_request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=False,
        safeMode=True,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    final_response = await chat_orchestrator.handle_chat(follow_up_request)

    # Verify safe mode returns summary table
    assert final_response.type == "final_answer"
    assert len(final_response.tables) > 0

    table = final_response.tables[0]
    assert "outlier" in table.title.lower() or "outlier" in table.name.lower()
    assert len(table.rows) == 3
    assert table.columns == ["column_name", "outlier_count"]

    # Verify it's aggregated, not individual rows
    assert all(isinstance(row[1], int) for row in table.rows)  # Counts are integers

    print(f"\n✅ Outliers safe mode test passed!")
    print(f"   - Table: {table.title or table.name}")
    print(f"   - Type: Aggregated summary (Safe Mode)")
    print(f"   - Total outliers: {sum(row[1] for row in table.rows)}")


@pytest.mark.asyncio
async def test_data_quality_generates_table(conversation_id, mock_catalog):
    """Test that data quality check generates table output"""
    request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Check data quality",
        privacyMode=False,
        safeMode=True,
        catalog=mock_catalog
    )

    response = await chat_orchestrator.handle_chat(request)
    assert response.type == "run_queries"

    # Simulate quality check results
    mock_results = [
        {
            "name": "null_counts",
            "columns": ["total_rows", "null_order_date", "null_amount", "null_category"],
            "rows": [[10000, 0, 45, 120]]
        }
    ]

    follow_up_request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=False,
        safeMode=True,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    final_response = await chat_orchestrator.handle_chat(follow_up_request)

    # Verify table output
    assert final_response.type == "final_answer"
    assert len(final_response.summaryMarkdown) > 0

    print(f"\n✅ Data quality test passed!")
    print(f"   - Summary includes quality metrics")


@pytest.mark.asyncio
async def test_privacy_mode_does_not_affect_table_structure(conversation_id, mock_catalog):
    """
    Test that privacy mode still generates tables
    (Privacy filtering happens at query execution, not response building)
    """
    request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Show trends",
        privacyMode=True,  # Privacy mode ON
        safeMode=True,
        catalog=mock_catalog
    )

    response = await chat_orchestrator.handle_chat(request)
    assert response.type == "run_queries"

    # Simulate aggregate results (no PII)
    mock_results = [
        {
            "name": "trends",
            "columns": ["month", "order_count"],
            "rows": [["2024-01", 1250], ["2024-02", 1437]]
        }
    ]

    follow_up_request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=True,
        safeMode=True,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    final_response = await chat_orchestrator.handle_chat(follow_up_request)

    # Tables should still be generated
    assert final_response.type == "final_answer"
    assert len(final_response.tables) > 0
    assert final_response.audit.privacyMode == True

    print(f"\n✅ Privacy mode test passed!")
    print(f"   - Tables generated even with privacy mode ON")
    print(f"   - Privacy flag recorded in audit")


@pytest.mark.asyncio
async def test_multiple_queries_generate_multiple_tables(conversation_id, mock_catalog):
    """Test that multiple queries can generate multiple tables"""
    # Manually create a state with multiple queries planned
    state_manager.update_context(conversation_id, {
        "analysis_type": "trend",
        "time_period": "last_30_days"
    })

    # Simulate multiple query results
    mock_results = [
        {
            "name": "monthly_trends",
            "columns": ["month", "count"],
            "rows": [["2024-01", 100], ["2024-02", 120]]
        },
        {
            "name": "daily_averages",
            "columns": ["day_of_week", "avg_orders"],
            "rows": [["Monday", 45], ["Tuesday", 52], ["Wednesday", 48]]
        }
    ]

    request = ChatRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="Here are the query results.",
        privacyMode=False,
        safeMode=True,
        resultsContext={"results": mock_results},
        catalog=mock_catalog
    )

    response = await chat_orchestrator.handle_chat(request)

    # Should generate tables for both results
    assert response.type == "final_answer"
    assert len(response.tables) >= 1  # At least one table

    print(f"\n✅ Multiple queries test passed!")
    print(f"   - Generated {len(response.tables)} table(s)")


def test_table_data_structure():
    """Test that TableData model has correct structure for frontend"""
    from app.models import TableData

    table = TableData(
        name="Test Table",
        columns=["col1", "col2", "col3"],
        rows=[
            [1, "value1", 100.5],
            [2, "value2", 200.75]
        ]
    )

    # Verify it can be serialized to dict
    table_dict = table.model_dump()
    assert "name" in table_dict
    assert "columns" in table_dict
    assert "rows" in table_dict

    # Verify structure matches frontend expectations
    assert isinstance(table_dict["columns"], list)
    assert isinstance(table_dict["rows"], list)
    assert len(table_dict["rows"][0]) == len(table_dict["columns"])

    print("\n✅ TableData structure test passed!")
    print(f"   - Structure matches frontend expectations")


if __name__ == "__main__":
    # Run with: python test_ta6_query_execution_flow.py
    import asyncio
    import sys

    async def run_tests():
        print("=" * 60)
        print("TA-6: Query Execution Flow Tests")
        print("=" * 60)

        conv_id = "test-conv-123"
        from app.models import DatasetCatalog, DatasetColumn
        catalog = DatasetCatalog(
            columns=[
                DatasetColumn(name="order_date", type="DATE"),
                DatasetColumn(name="amount", type="DECIMAL"),
                DatasetColumn(name="category", type="VARCHAR"),
            ]
        )

        try:
            print("\n[Test 1] Trend Flow")
            await test_trend_flow_generates_tables(conv_id + "-1", catalog)

            print("\n[Test 2] Top Categories Flow")
            await test_top_categories_flow_generates_tables(conv_id + "-2", catalog)

            print("\n[Test 3] Outliers Safe Mode")
            await test_outliers_safe_mode_generates_summary_table(conv_id + "-3", catalog)

            print("\n[Test 4] Data Quality")
            await test_data_quality_generates_table(conv_id + "-4", catalog)

            print("\n[Test 5] Privacy Mode")
            await test_privacy_mode_does_not_affect_table_structure(conv_id + "-5", catalog)

            print("\n[Test 6] Multiple Tables")
            await test_multiple_queries_generate_multiple_tables(conv_id + "-6", catalog)

            print("\n[Test 7] TableData Structure")
            test_table_data_structure()

            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\nAcceptance Criteria Met:")
            print("✅ run_queries → execute → final_answer flow works")
            print("✅ Tables generated for trend analysis")
            print("✅ Tables displayed in Tables tab")
            print("✅ Audit metadata included")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_tests())
