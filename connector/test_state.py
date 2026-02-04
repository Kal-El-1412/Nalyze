#!/usr/bin/env python3
"""
Quick test script for conversation state manager.
Run: python test_state.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.state import state_manager


def test_conversation_state():
    print("Testing Conversation State Manager\n")
    print("=" * 50)

    conv_id = "test-conv-123"

    print(f"\n1. Getting state for new conversation: {conv_id}")
    state = state_manager.get_state(conv_id)
    print(f"   Created state: {state}")
    assert state["conversation_id"] == conv_id
    assert state["dataset_id"] is None
    assert state["ready"] is False
    print("   ✓ Default state created correctly")

    print(f"\n2. Updating state with dataset info")
    updated = state_manager.update_state(
        conv_id,
        dataset_id="dataset-456",
        dataset_name="sales_data.xlsx",
        ready=True,
        message_count=1
    )
    print(f"   Updated state: {updated}")
    assert updated["dataset_id"] == "dataset-456"
    assert updated["dataset_name"] == "sales_data.xlsx"
    assert updated["message_count"] == 1
    print("   ✓ State updated correctly")

    print(f"\n3. Checking if conversation is ready")
    is_ready = state_manager.is_ready(conv_id)
    print(f"   Is ready: {is_ready}")
    assert is_ready is True
    print("   ✓ Conversation is ready")

    print(f"\n4. Getting state again (should persist)")
    persisted = state_manager.get_state(conv_id)
    print(f"   Persisted state: {persisted}")
    assert persisted["dataset_id"] == "dataset-456"
    assert persisted["message_count"] == 1
    print("   ✓ State persisted correctly")

    print(f"\n5. Updating message count")
    state_manager.update_state(conv_id, message_count=2)
    state = state_manager.get_state(conv_id)
    assert state["message_count"] == 2
    print(f"   Message count: {state['message_count']}")
    print("   ✓ Message count updated")

    print(f"\n6. Testing second conversation")
    conv_id_2 = "test-conv-456"
    state2 = state_manager.get_state(conv_id_2)
    assert state2["conversation_id"] == conv_id_2
    assert state2["dataset_id"] is None
    print(f"   Second conversation created: {conv_id_2}")
    print("   ✓ Multiple conversations supported")

    print(f"\n7. Listing all conversations")
    conversations = state_manager.list_conversations()
    print(f"   Active conversations: {conversations}")
    assert len(conversations) == 2
    print("   ✓ Both conversations tracked")

    print(f"\n8. Getting stats")
    stats = state_manager.get_stats()
    print(f"   Stats: {stats}")
    assert stats["total_conversations"] == 2
    print("   ✓ Stats correct")

    print(f"\n9. Clearing first conversation")
    cleared = state_manager.clear_state(conv_id)
    assert cleared is True
    conversations = state_manager.list_conversations()
    assert len(conversations) == 1
    print(f"   Remaining conversations: {conversations}")
    print("   ✓ Conversation cleared")

    print(f"\n10. Testing is_ready for conversation without dataset")
    conv_id_3 = "test-conv-789"
    is_ready = state_manager.is_ready(conv_id_3)
    assert is_ready is False
    print(f"   Conversation {conv_id_3} ready: {is_ready}")
    print("   ✓ Correctly returns False for conversation without dataset")

    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_conversation_state()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
