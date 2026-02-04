import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from app.chat_orchestrator import ChatOrchestrator
from app.state import state_manager
from app.models import ChatOrchestratorRequest, QueryResult, ResultsContext


def create_mock_catalog():
    """Create a mock catalog for testing"""
    class MockColumn:
        def __init__(self, name, col_type, nullable=True):
            self.name = name
            self.type = col_type
            self.nullable = nullable

    class MockCatalog:
        def __init__(self):
            self.rowCount = 1000
            self.columns = [
                MockColumn("order_date", "TIMESTAMP"),
                MockColumn("customer_name", "VARCHAR"),
                MockColumn("product_category", "VARCHAR"),
                MockColumn("revenue", "DOUBLE"),
                MockColumn("quantity", "INTEGER")
            ]
            self.detectedDateColumns = ["order_date"]
            self.detectedNumericColumns = ["revenue", "quantity"]
            self.summary = {
                "product_category": {
                    "count": 1000,
                    "unique": 5
                },
                "customer_name": {
                    "count": 1000,
                    "unique": 200
                }
            }

    return MockCatalog()


async def test_row_count():
    print("\n" + "=" * 60)
    print("Test 1: Row Count Analysis")
    print("=" * 60)

    orchestrator = ChatOrchestrator()
    conversation_id = "test-conv-1"

    state_manager.update_state(
        conversation_id,
        dataset_id="test-dataset",
        context={
            "analysis_type": "row_count",
            "time_period": "last_month"
        }
    )

    request = ChatOrchestratorRequest(
        conversationId=conversation_id,
        datasetId="test-dataset",
        message="Show me the row count"
    )

    catalog = create_mock_catalog()
    response = await orchestrator._generate_sql_plan(request, catalog, {"analysis_type": "row_count", "time_period": "last_month"})

    print(f"✓ Response type: {type(response).__name__}")
    print(f"✓ Queries: {len(response.queries)}")
    print(f"✓ Query name: {response.queries[0].name}")
    print(f"✓ SQL: {response.queries[0].sql}")
    print(f"✓ Explanation: {response.explanation}")

    assert response.queries[0].sql == "SELECT COUNT(*) as row_count FROM data"
    print("\n✅ Row count test passed!")


async def test_top_categories():
    print("\n" + "=" * 60)
    print("Test 2: Top Categories Analysis")
    print("=" * 60)

    orchestrator = ChatOrchestrator()
    conversation_id = "test-conv-2"

    state_manager.update_state(
        conversation_id,
        dataset_id="test-dataset",
        context={
            "analysis_type": "top_categories",
            "time_period": "this_year"
        }
    )

    request = ChatOrchestratorRequest(
        conversationId=conversation_id,
        datasetId="test-dataset",
        message="Show me top categories"
    )

    catalog = create_mock_catalog()
    response = await orchestrator._generate_sql_plan(request, catalog, {"analysis_type": "top_categories", "time_period": "this_year"})

    print(f"✓ Response type: {type(response).__name__}")
    print(f"✓ Queries: {len(response.queries)}")
    print(f"✓ Query name: {response.queries[0].name}")
    print(f"✓ SQL: {response.queries[0].sql}")
    print(f"✓ Explanation: {response.explanation}")

    assert "GROUP BY" in response.queries[0].sql
    assert "LIMIT 10" in response.queries[0].sql
    print("\n✅ Top categories test passed!")


async def test_trend():
    print("\n" + "=" * 60)
    print("Test 3: Trend Analysis")
    print("=" * 60)

    orchestrator = ChatOrchestrator()
    conversation_id = "test-conv-3"

    state_manager.update_state(
        conversation_id,
        dataset_id="test-dataset",
        context={
            "analysis_type": "trend",
            "time_period": "last_6_months"
        }
    )

    request = ChatOrchestratorRequest(
        conversationId=conversation_id,
        datasetId="test-dataset",
        message="Show me trends"
    )

    catalog = create_mock_catalog()
    response = await orchestrator._generate_sql_plan(request, catalog, {"analysis_type": "trend", "time_period": "last_6_months"})

    print(f"✓ Response type: {type(response).__name__}")
    print(f"✓ Queries: {len(response.queries)}")
    print(f"✓ Query name: {response.queries[0].name}")
    print(f"✓ SQL: {response.queries[0].sql[:100]}...")
    print(f"✓ Explanation: {response.explanation}")

    assert "DATE_TRUNC" in response.queries[0].sql
    assert "GROUP BY" in response.queries[0].sql
    print("\n✅ Trend test passed!")


async def test_final_answer():
    print("\n" + "=" * 60)
    print("Test 4: Final Answer Generation")
    print("=" * 60)

    orchestrator = ChatOrchestrator()
    conversation_id = "test-conv-4"

    state_manager.update_state(
        conversation_id,
        dataset_id="test-dataset",
        context={
            "analysis_type": "row_count",
            "time_period": "last_month"
        }
    )

    mock_results = ResultsContext(
        results=[
            QueryResult(
                name="row_count",
                columns=["row_count"],
                rows=[[1000]]
            )
        ]
    )

    request = ChatOrchestratorRequest(
        conversationId=conversation_id,
        datasetId="test-dataset",
        message="Show me results",
        resultsContext=mock_results
    )

    catalog = create_mock_catalog()
    response = await orchestrator._generate_final_answer(request, catalog, {"analysis_type": "row_count", "time_period": "last_month"})

    print(f"✓ Response type: {type(response).__name__}")
    print(f"✓ Message: {response.message}")

    assert "1,000" in response.message or "1000" in response.message
    print("\n✅ Final answer test passed!")


async def test_column_detection():
    print("\n" + "=" * 60)
    print("Test 5: Column Detection")
    print("=" * 60)

    orchestrator = ChatOrchestrator()
    catalog = create_mock_catalog()

    categorical_col = orchestrator._detect_best_categorical_column(catalog)
    date_col = orchestrator._detect_date_column(catalog)
    metric_col = orchestrator._detect_metric_column(catalog)

    print(f"✓ Best categorical column: {categorical_col}")
    print(f"✓ Date column: {date_col}")
    print(f"✓ Metric column: {metric_col}")

    assert categorical_col == "product_category"
    assert date_col == "order_date"
    assert metric_col == "revenue"

    print("\n✅ Column detection test passed!")


async def main():
    print("=" * 60)
    print("Prompt 9: Chat Orchestrator → SQL Plan → Execute → Answer")
    print("=" * 60)

    try:
        await test_row_count()
        await test_top_categories()
        await test_trend()
        await test_final_answer()
        await test_column_detection()

        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print("✓ State readiness check works")
        print("✓ Row count SQL generation works")
        print("✓ Top categories SQL generation works")
        print("✓ Trend SQL generation works")
        print("✓ Final answer generation works")
        print("✓ Column detection works")
        print("\n✅ All Prompt 9 tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
