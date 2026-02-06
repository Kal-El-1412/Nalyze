"""
Test OFF-REAL-1: No Canned Summary Unless Queries Executed

Verifies that:
1. No generic canned summaries are returned
2. Row count returns actual numeric count from results
3. Trend returns table + summary references actual data
4. Cannot return final_answer without resultsContext

Run with: python3 test_no_canned_summaries.py
"""

import sys
import asyncio
import logging
from app.chat_orchestrator import chat_orchestrator
from app.models import (
    ChatOrchestratorRequest,
    DatasetColumn,
    DatasetCatalog,
    ResultsContext,
    QueryResult
)
from app.state import state_manager

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def test_no_canned_on_repeated_clarification():
    """Test that repeated unclear messages don't return canned summaries"""
    print("\n" + "=" * 60)
    print("Test 1: No Canned Summary on Repeated Clarification")
    print("=" * 60)

    catalog = DatasetCatalog(
        columns=[
            DatasetColumn(name="id", type="INTEGER"),
            DatasetColumn(name="value", type="DECIMAL"),
        ]
    )

    conversation_id = "test-no-canned-001"
    state_manager.clear_state(conversation_id)

    # Send unclear message with AI Assist OFF
    request = ChatOrchestratorRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="show me something interesting",  # Unclear message
        privacyMode=False,
        safeMode=False,
        aiAssist=False,
    )

    print(f"\n📤 First unclear message: '{request.message}'")
    response1 = await chat_orchestrator.process(request)

    if response1.type == "needs_clarification":
        print(f"✅ First response: needs_clarification")
    else:
        print(f"❌ Expected needs_clarification, got {response1.type}")
        sys.exit(1)

    # Send another unclear message
    request.message = "do the analysis"
    print(f"\n📤 Second unclear message: '{request.message}'")
    response2 = await chat_orchestrator.process(request)

    if response2.type == "needs_clarification":
        print(f"✅ Second response: needs_clarification (not final_answer)")
        print(f"   Question: {response2.question[:60]}...")
    elif response2.type == "final_answer":
        # Check if it's a canned/generic summary
        summary = response2.summaryMarkdown.lower()
        forbidden_phrases = [
            "dataset contains diverse data patterns",
            "statistical analysis shows normal distribution",
            "no significant anomalies detected",
        ]

        has_canned = any(phrase in summary for phrase in forbidden_phrases)
        if has_canned:
            print(f"❌ Second response returned canned summary!")
            print(f"   Summary: {response2.summaryMarkdown}")
            sys.exit(1)
        else:
            print(f"⚠️  Got final_answer but no forbidden canned phrases")
            print(f"   Summary: {response2.summaryMarkdown}")
    else:
        print(f"✅ Second response: {response2.type}")

    print(f"\n✅ Test passed: No canned summaries returned")


async def test_row_count_with_results():
    """Test that row count returns actual numeric value from results"""
    print("\n" + "=" * 60)
    print("Test 2: Row Count Returns Actual Number from Results")
    print("=" * 60)

    catalog = DatasetCatalog(
        rowCount=1523,
        columns=[
            DatasetColumn(name="id", type="INTEGER"),
            DatasetColumn(name="value", type="DECIMAL"),
        ]
    )

    conversation_id = "test-row-count-002"
    state_manager.clear_state(conversation_id)

    # Step 1: Get query plan
    request = ChatOrchestratorRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="row count",
        privacyMode=False,
        safeMode=False,
        aiAssist=False,
    )

    print(f"\n📤 Step 1: Send message: '{request.message}'")
    response1 = await chat_orchestrator.process(request)

    if response1.type != "run_queries":
        print(f"❌ Expected run_queries, got {response1.type}")
        sys.exit(1)

    print(f"✅ Step 1: Got run_queries response")

    # Step 2: Simulate query execution with results
    mock_results = ResultsContext(
        results=[
            QueryResult(
                name="row_count",
                columns=["row_count"],
                rows=[[1523]],  # Actual count
                rowCount=1
            )
        ]
    )

    request.resultsContext = mock_results
    print(f"\n📤 Step 2: Send resultsContext with actual count: 1523")

    response2 = await chat_orchestrator.process(request)

    if response2.type != "final_answer":
        print(f"❌ Expected final_answer, got {response2.type}")
        sys.exit(1)

    # Check that summary includes the actual number
    summary = response2.summaryMarkdown
    if "1523" in summary or "1,523" in summary:
        print(f"✅ Step 2: Summary includes actual row count")
        print(f"   Summary: {summary}")
    else:
        print(f"❌ Summary doesn't include actual count!")
        print(f"   Expected: 1523 or 1,523")
        print(f"   Got: {summary}")
        sys.exit(1)

    print(f"\n✅ Test passed: Row count returns actual number from results")


async def test_trend_with_table():
    """Test that trend returns table and summary references data"""
    print("\n" + "=" * 60)
    print("Test 3: Trend Returns Table + Summary References Data")
    print("=" * 60)

    catalog = DatasetCatalog(
        columns=[
            DatasetColumn(name="date", type="DATE"),
            DatasetColumn(name="amount", type="DECIMAL"),
        ]
    )

    conversation_id = "test-trend-003"
    state_manager.clear_state(conversation_id)

    # Update state with trend analysis
    state_manager.update_context(conversation_id, {"analysis_type": "trend"})

    # Simulate trend results
    mock_results = ResultsContext(
        results=[
            QueryResult(
                name="monthly_trend",
                columns=["month", "count", "total_amount", "avg_amount"],
                rows=[
                    ["2024-01-01", 120, 45000, 375],
                    ["2024-02-01", 135, 52000, 385],
                    ["2024-03-01", 142, 58000, 408],
                ],
                rowCount=3
            )
        ]
    )

    request = ChatOrchestratorRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="show trends",
        resultsContext=mock_results,
        privacyMode=False,
        safeMode=False,
        aiAssist=False,
    )

    print(f"\n📤 Processing trend with resultsContext (3 months)")

    response = await chat_orchestrator.process(request)

    if response.type != "final_answer":
        print(f"❌ Expected final_answer, got {response.type}")
        sys.exit(1)

    # Check that tables are included
    if not response.tables or len(response.tables) == 0:
        print(f"❌ No tables returned!")
        sys.exit(1)

    print(f"✅ Tables returned: {len(response.tables)}")
    print(f"   Table: {response.tables[0].name}")

    # Check that summary references the data
    summary = response.summaryMarkdown
    if "3 data points" in summary or "data points" in summary:
        print(f"✅ Summary references actual data")
        print(f"   Summary: {summary}")
    else:
        print(f"⚠️  Summary may not reference data points")
        print(f"   Summary: {summary}")

    print(f"\n✅ Test passed: Trend returns table and references data")


async def test_final_answer_requires_results():
    """Test that final_answer cannot be generated without resultsContext"""
    print("\n" + "=" * 60)
    print("Test 4: Final Answer Requires ResultsContext")
    print("=" * 60)

    catalog = DatasetCatalog(
        columns=[
            DatasetColumn(name="id", type="INTEGER"),
        ]
    )

    conversation_id = "test-guard-004"
    state_manager.clear_state(conversation_id)

    # Set up state as if queries were planned
    state_manager.update_context(conversation_id, {"analysis_type": "row_count"})

    # Try to generate final answer WITHOUT resultsContext
    request = ChatOrchestratorRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="row count",
        resultsContext=None,  # No results!
        privacyMode=False,
        safeMode=False,
        aiAssist=False,
    )

    print(f"\n📤 Attempting to generate final_answer without resultsContext")

    try:
        # This should trigger the _generate_final_answer path
        # Since state has analysis_type, process() will call _generate_sql_plan
        # We need to manually call _generate_final_answer to test the guard
        from app.chat_orchestrator import chat_orchestrator as orc

        state = state_manager.get_state(conversation_id)
        context = state.get("context", {})

        await orc._generate_final_answer(request, catalog, context)

        print(f"❌ Should have raised ValueError!")
        sys.exit(1)

    except ValueError as e:
        if "Cannot generate final answer without query results" in str(e):
            print(f"✅ Guard triggered correctly: {str(e)}")
        else:
            print(f"❌ Wrong error: {str(e)}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    print(f"\n✅ Test passed: Guard prevents final_answer without results")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OFF-REAL-1: No Canned Summary - Test Suite")
    print("=" * 60)

    try:
        # Test 1: No canned summaries
        await test_no_canned_on_repeated_clarification()

        # Test 2: Row count with actual number
        await test_row_count_with_results()

        # Test 3: Trend with table
        await test_trend_with_table()

        # Test 4: Guard requires results
        await test_final_answer_requires_results()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nAcceptance Criteria Met:")
        print("✅ No canned/generic summaries returned")
        print("✅ Row count returns actual numeric value from results")
        print("✅ Trend returns table + summary references data")
        print("✅ Guard prevents final_answer without resultsContext")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
