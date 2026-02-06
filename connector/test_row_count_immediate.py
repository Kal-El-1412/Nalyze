"""
Test TP2: Row Count Immediate Execution
Tests that "row count" queries run immediately without clarification

Run with: python test_row_count_immediate.py
"""

import sys
import asyncio
import logging
from app.router import deterministic_router
from app.chat_orchestrator import chat_orchestrator
from app.models import ChatOrchestratorRequest, DatasetColumn, DatasetCatalog
from app.state import state_manager

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_deterministic_router():
    """Test that deterministic router matches row count patterns"""
    print("\n" + "=" * 60)
    print("Test 1: Deterministic Router - Row Count Patterns")
    print("=" * 60)

    test_messages = [
        "row count",
        "count rows",
        "how many rows",
        "how many rows are there",
        "total rows",
        "number of rows",
        "record count",
        "how many records",
        "how many records do we have",
    ]

    all_passed = True
    for message in test_messages:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type == "row_count" and confidence >= 0.8:
            print(f"✅ '{message}' → row_count (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f}) - EXPECTED row_count with >=0.8")
            all_passed = False

    if all_passed:
        print("\n✅ All router tests passed!")
    else:
        print("\n❌ Some router tests failed!")
        sys.exit(1)


async def test_orchestrator_immediate_execution():
    """Test that orchestrator runs row count immediately without clarification"""
    print("\n" + "=" * 60)
    print("Test 2: Orchestrator - Immediate Execution")
    print("=" * 60)

    # Create a mock catalog
    catalog = DatasetCatalog(
        columns=[
            DatasetColumn(name="id", type="INTEGER"),
            DatasetColumn(name="name", type="TEXT"),
            DatasetColumn(name="amount", type="DECIMAL"),
            DatasetColumn(name="date", type="DATE"),
        ]
    )

    conversation_id = "test-row-count-001"

    # Clean up any existing state
    state_manager.clear_state(conversation_id)

    # Create request for "row count"
    request = ChatOrchestratorRequest(
        datasetId="test-dataset",
        conversationId=conversation_id,
        message="row count",
        privacyMode=False,
        safeMode=False,
        aiAssist=False,  # Test with AI Assist OFF
    )

    print(f"\n📤 Sending message: '{request.message}'")
    print(f"   AI Assist: {request.aiAssist}")

    # Process request
    try:
        response = await chat_orchestrator.process(request)
    except Exception as e:
        print(f"\n❌ Error processing request: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\n📥 Response type: {response.type}")

    # Check response type
    if response.type == "run_queries":
        print(f"✅ Got run_queries response (immediate execution)")

        # Check queries
        if len(response.queries) == 1:
            query = response.queries[0]
            print(f"✅ Query count: {len(response.queries)}")
            print(f"   Query name: {query.name}")
            print(f"   Query SQL: {query.sql}")

            if query.name == "row_count":
                print(f"✅ Query name is 'row_count'")
            else:
                print(f"❌ Expected query name 'row_count', got '{query.name}'")
                sys.exit(1)

            if "COUNT(*)" in query.sql.upper():
                print(f"✅ Query contains COUNT(*)")
            else:
                print(f"❌ Expected COUNT(*) in SQL: {query.sql}")
                sys.exit(1)
        else:
            print(f"❌ Expected 1 query, got {len(response.queries)}")
            sys.exit(1)

        # Check explanation
        print(f"\n   Explanation: {response.explanation}")

        # Verify time_period was set to all_time
        state = state_manager.get_state(conversation_id)
        context = state.get("context", {})
        time_period = context.get("time_period")

        if time_period == "all_time":
            print(f"✅ time_period set to 'all_time'")
        else:
            print(f"❌ Expected time_period='all_time', got '{time_period}'")
            sys.exit(1)

    elif response.type == "needs_clarification":
        print(f"❌ Got clarification request instead of immediate execution!")
        print(f"   Question: {response.question}")
        print(f"   Choices: {response.choices}")
        sys.exit(1)
    else:
        print(f"❌ Unexpected response type: {response.type}")
        sys.exit(1)

    print("\n✅ Orchestrator test passed!")


async def test_multiple_variations():
    """Test multiple row count variations"""
    print("\n" + "=" * 60)
    print("Test 3: Multiple Row Count Variations")
    print("=" * 60)

    variations = [
        "count rows",
        "how many rows",
        "total rows",
        "record count",
    ]

    catalog = DatasetCatalog(
        columns=[
            DatasetColumn(name="id", type="INTEGER"),
            DatasetColumn(name="value", type="DECIMAL"),
        ]
    )

    all_passed = True
    for i, message in enumerate(variations):
        conversation_id = f"test-row-count-{i+2:03d}"
        state_manager.clear_state(conversation_id)

        request = ChatOrchestratorRequest(
            datasetId="test-dataset",
            conversationId=conversation_id,
            message=message,
            privacyMode=False,
            safeMode=False,
            aiAssist=False,
        )

        try:
            response = await chat_orchestrator.process(request)

            if response.type == "run_queries":
                state = state_manager.get_state(conversation_id)
                context = state.get("context", {})
                time_period = context.get("time_period")

                if time_period == "all_time":
                    print(f"✅ '{message}' → run_queries with time_period='all_time'")
                else:
                    print(f"❌ '{message}' → time_period='{time_period}' (expected 'all_time')")
                    all_passed = False
            else:
                print(f"❌ '{message}' → {response.type} (expected run_queries)")
                all_passed = False

        except Exception as e:
            print(f"❌ '{message}' → Error: {e}")
            all_passed = False

    if all_passed:
        print("\n✅ All variation tests passed!")
    else:
        print("\n❌ Some variation tests failed!")
        sys.exit(1)


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TP2: Row Count Immediate Execution - Test Suite")
    print("=" * 60)

    try:
        # Test 1: Router patterns
        await test_deterministic_router()

        # Test 2: Orchestrator immediate execution
        await test_orchestrator_immediate_execution()

        # Test 3: Multiple variations
        await test_multiple_variations()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nAcceptance Criteria Met:")
        print("✅ Deterministic router matches row count patterns with high confidence")
        print("✅ Orchestrator forces time_period='all_time' for row_count")
        print("✅ No clarification request for row count queries")
        print("✅ Typing 'row count' runs immediately")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
