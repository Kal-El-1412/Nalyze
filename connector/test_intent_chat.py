#!/usr/bin/env python3
"""
Test script for intent-based chat requests.
Run: python test_intent_chat.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.models import ChatOrchestratorRequest, IntentAcknowledgmentResponse
from app.state import state_manager


def test_intent_validation():
    print("Testing Intent-Based Chat Request Validation\n")
    print("=" * 60)

    conv_id = "test-intent-conv-123"
    dataset_id = "test-dataset-456"

    print("\n1. Test message-based request (backward compatible)")
    try:
        request = ChatOrchestratorRequest(
            datasetId=dataset_id,
            conversationId=conv_id,
            message="Show me sales trends"
        )
        print(f"   ✓ Message request created: '{request.message}'")
        assert request.message == "Show me sales trends"
        assert request.intent is None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        sys.exit(1)

    print("\n2. Test intent-based request")
    try:
        request = ChatOrchestratorRequest(
            datasetId=dataset_id,
            conversationId=conv_id,
            intent="set_analysis_type",
            value="trend"
        )
        print(f"   ✓ Intent request created: {request.intent} = {request.value}")
        assert request.intent == "set_analysis_type"
        assert request.value == "trend"
        assert request.message is None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        sys.exit(1)

    print("\n3. Test validation: Cannot provide both message and intent")
    try:
        request = ChatOrchestratorRequest(
            datasetId=dataset_id,
            conversationId=conv_id,
            message="Show trends",
            intent="set_analysis_type",
            value="trend"
        )
        print(f"   ✗ Should have raised validation error!")
        sys.exit(1)
    except ValueError as e:
        print(f"   ✓ Correctly rejected: {e}")

    print("\n4. Test validation: Must provide either message or intent")
    try:
        request = ChatOrchestratorRequest(
            datasetId=dataset_id,
            conversationId=conv_id
        )
        print(f"   ✗ Should have raised validation error!")
        sys.exit(1)
    except ValueError as e:
        print(f"   ✓ Correctly rejected: {e}")

    print("\n5. Test validation: Intent requires value")
    try:
        request = ChatOrchestratorRequest(
            datasetId=dataset_id,
            conversationId=conv_id,
            intent="set_analysis_type"
        )
        print(f"   ✗ Should have raised validation error!")
        sys.exit(1)
    except ValueError as e:
        print(f"   ✓ Correctly rejected: {e}")

    print("\n6. Test various intent types")
    intents_to_test = [
        ("set_analysis_type", "trend"),
        ("set_time_period", "last_30_days"),
        ("set_metric", "revenue"),
        ("set_dimension", "region"),
        ("set_filter", {"status": "active"}),
        ("set_visualization", "line_chart")
    ]

    for intent, value in intents_to_test:
        try:
            request = ChatOrchestratorRequest(
                datasetId=dataset_id,
                conversationId=conv_id,
                intent=intent,
                value=value
            )
            print(f"   ✓ {intent} = {value}")
        except Exception as e:
            print(f"   ✗ Failed for {intent}: {e}")
            sys.exit(1)

    print("\n7. Test IntentAcknowledgmentResponse creation")
    try:
        response = IntentAcknowledgmentResponse(
            intent="set_analysis_type",
            value="trend",
            state={"conversation_id": conv_id, "ready": True},
            message="Updated analysis type to 'trend'"
        )
        print(f"   ✓ Response created: {response.type}")
        assert response.type == "intent_acknowledged"
        assert response.intent == "set_analysis_type"
        assert response.value == "trend"
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        sys.exit(1)

    print("\n8. Test state updates with intents")
    conv_id_2 = "test-intent-conv-456"
    state = state_manager.get_state(conv_id_2)
    print(f"   Initial context: {state.get('context', {})}")

    state_manager.update_state(
        conv_id_2,
        context={
            "analysis_type": "trend",
            "time_period": "last_30_days",
            "metric": "revenue"
        }
    )

    updated_state = state_manager.get_state(conv_id_2)
    print(f"   Updated context: {updated_state['context']}")
    assert updated_state["context"]["analysis_type"] == "trend"
    assert updated_state["context"]["time_period"] == "last_30_days"
    assert updated_state["context"]["metric"] == "revenue"
    print("   ✓ State context updated correctly")

    state_manager.clear_state(conv_id_2)

    print("\n" + "=" * 60)
    print("✓ All intent-based chat tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_intent_validation()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
