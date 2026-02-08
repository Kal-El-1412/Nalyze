"""
Test to verify the clarification loop fix.
This ensures that repeated clarification questions don't create an infinite loop.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.state import state_manager
from app.models import ChatOrchestratorRequest
from app.chat_orchestrator import chat_orchestrator
import asyncio


async def test_clarification_tracking():
    """Test that clarification tracking works correctly"""
    print("\n=== Test 1: Clarification Tracking ===")

    conv_id = "test_clarification_tracking"

    # Initially, clarification should not be asked
    has_asked = state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert not has_asked, "Clarification should not be marked as asked initially"
    print("✓ Initial state: clarification not asked")

    # Mark clarification as asked
    state_manager.mark_clarification_asked(conv_id, "set_analysis_type")
    has_asked = state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert has_asked, "Clarification should be marked as asked"
    print("✓ After marking: clarification is asked")

    # Clear clarification tracking
    state_manager.clear_clarification_tracking(conv_id, "set_analysis_type")
    has_asked = state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert not has_asked, "Clarification should be cleared"
    print("✓ After clearing: clarification is not asked")

    # Cleanup
    state_manager.clear_state(conv_id)
    print("✓ Test 1 passed\n")


async def test_update_context_clears_tracking():
    """Test that update_context automatically clears clarification tracking"""
    print("=== Test 2: Update Context Clears Tracking ===")

    conv_id = "test_update_context"

    # Mark clarification as asked
    state_manager.mark_clarification_asked(conv_id, "set_analysis_type")
    has_asked = state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert has_asked, "Clarification should be marked as asked"
    print("✓ Clarification marked as asked")

    # Update context with analysis_type
    state_manager.update_context(conv_id, {"analysis_type": "trend"})

    # Clarification tracking should be automatically cleared
    has_asked = state_manager.has_asked_clarification(conv_id, "set_analysis_type")
    assert not has_asked, "Clarification should be automatically cleared when analysis_type is set"
    print("✓ Clarification automatically cleared when analysis_type set")

    # Verify analysis_type is in context
    state = state_manager.get_state(conv_id)
    assert state["context"]["analysis_type"] == "trend", "analysis_type should be set in context"
    print("✓ analysis_type correctly set in context")

    # Cleanup
    state_manager.clear_state(conv_id)
    print("✓ Test 2 passed\n")


async def test_duplicate_clarification_prevention():
    """Test that duplicate clarification questions are prevented"""
    print("=== Test 3: Duplicate Clarification Prevention ===")

    conv_id = "test_duplicate_prevention"

    # Create a mock dataset first
    from app.storage import storage
    dataset_id = "test_dataset_duplicate"
    await storage.create_dataset({
        "id": dataset_id,
        "name": "Test Dataset",
        "status": "ingested",
        "file_path": "/tmp/test.csv"
    })

    # First request with ambiguous message (AI Assist OFF)
    request1 = ChatOrchestratorRequest(
        datasetId=dataset_id,
        conversationId=conv_id,
        message="show me data",
        aiAssist=False,
        privacyMode=True,
        safeMode=False
    )

    response1 = await chat_orchestrator.process(request1)
    print(f"✓ First request: {response1.type}")

    # Should return needs_clarification
    assert response1.type == "needs_clarification", "First request should ask for clarification"
    print("✓ First request correctly asks for clarification")

    # Second request with same ambiguous message (AI Assist OFF)
    request2 = ChatOrchestratorRequest(
        datasetId=dataset_id,
        conversationId=conv_id,
        message="analyze this",
        aiAssist=False,
        privacyMode=True,
        safeMode=False
    )

    response2 = await chat_orchestrator.process(request2)
    print(f"✓ Second request: {response2.type}")

    # Should return final_answer with helpful message (not needs_clarification)
    assert response2.type == "final_answer", "Second request should return final_answer to prevent loop"
    assert "having trouble" in response2.summaryMarkdown.lower(), "Should provide helpful guidance"
    print("✓ Second request correctly prevents loop with helpful message")

    # Cleanup
    state_manager.clear_state(conv_id)
    await storage.delete_dataset(dataset_id)
    print("✓ Test 3 passed\n")


async def test_continue_message_with_state():
    """Test that 'continue' message uses existing state"""
    print("=== Test 4: Continue Message with State ===")

    conv_id = "test_continue_message"

    # Create a mock dataset first
    from app.storage import storage
    dataset_id = "test_dataset_continue"
    await storage.create_dataset({
        "id": dataset_id,
        "name": "Test Dataset",
        "status": "ingested",
        "file_path": "/tmp/test.csv"
    })

    # Set analysis_type in state
    state_manager.update_context(conv_id, {"analysis_type": "row_count"})
    print("✓ Set analysis_type in state")

    # Send "continue" message
    request = ChatOrchestratorRequest(
        datasetId=dataset_id,
        conversationId=conv_id,
        message="continue",
        aiAssist=False,
        privacyMode=True,
        safeMode=False
    )

    response = await chat_orchestrator.process(request)
    print(f"✓ Continue request: {response.type}")

    # Should return run_queries (not needs_clarification)
    assert response.type == "run_queries", "Continue with state should generate SQL"
    print("✓ Continue message correctly uses existing state")

    # Cleanup
    state_manager.clear_state(conv_id)
    await storage.delete_dataset(dataset_id)
    print("✓ Test 4 passed\n")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing Clarification Loop Fix")
    print("="*60)

    try:
        await test_clarification_tracking()
        await test_update_context_clears_tracking()
        await test_duplicate_clarification_prevention()
        await test_continue_message_with_state()

        print("="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
