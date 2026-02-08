"""Test the hardened ChatOrchestratorRequest contract"""
import sys
sys.path.insert(0, '.')

from app.models import ChatOrchestratorRequest

def test_message_only_no_conversationId():
    """✓ Message only, no conversationId - should auto-generate"""
    req = ChatOrchestratorRequest(datasetId="ds-123", message="row count")
    assert req.conversationId is not None
    assert req.conversationId.startswith("conv-")
    print("✓ Message only (no conversationId): auto-generated", req.conversationId)

def test_message_only_with_conversationId():
    """✓ Message with conversationId - should use provided"""
    req = ChatOrchestratorRequest(
        datasetId="ds-123",
        conversationId="conv-existing",
        message="row count"
    )
    assert req.conversationId == "conv-existing"
    print("✓ Message with conversationId: preserved")

def test_intent_with_value():
    """✓ Intent with value - should work"""
    req = ChatOrchestratorRequest(
        datasetId="ds-123",
        intent="set_analysis_type",
        value="outliers"
    )
    assert req.conversationId.startswith("conv-")
    print("✓ Intent with value: valid")

def test_intent_without_value():
    """✗ Intent without value - should fail"""
    try:
        req = ChatOrchestratorRequest(
            datasetId="ds-123",
            intent="set_analysis_type"
        )
        print("✗ Intent without value: SHOULD HAVE FAILED")
        sys.exit(1)
    except ValueError as e:
        assert "'value' is required when 'intent' is provided" in str(e)
        print("✓ Intent without value: correctly rejected")

def test_both_message_and_intent():
    """✗ Both message and intent - should fail"""
    try:
        req = ChatOrchestratorRequest(
            datasetId="ds-123",
            message="row count",
            intent="set_analysis_type",
            value="outliers"
        )
        print("✗ Both message and intent: SHOULD HAVE FAILED")
        sys.exit(1)
    except ValueError as e:
        assert "Cannot provide both 'message' and 'intent'" in str(e)
        print("✓ Both message and intent: correctly rejected")

def test_neither_message_nor_intent():
    """✗ Neither message nor intent - should fail"""
    try:
        req = ChatOrchestratorRequest(datasetId="ds-123")
        print("✗ Neither message nor intent: SHOULD HAVE FAILED")
        sys.exit(1)
    except ValueError as e:
        assert "Either 'message' or 'intent' must be provided" in str(e)
        print("✓ Neither message nor intent: correctly rejected")

def test_empty_strings():
    """✗ Empty/whitespace strings - should fail"""
    try:
        req = ChatOrchestratorRequest(datasetId="ds-123", message="   ")
        print("✗ Empty message string: SHOULD HAVE FAILED")
        sys.exit(1)
    except ValueError as e:
        assert "Either 'message' or 'intent' must be provided" in str(e)
        print("✓ Empty message string: correctly rejected")

if __name__ == "__main__":
    print("\n=== Testing ChatOrchestratorRequest Contract ===\n")

    test_message_only_no_conversationId()
    test_message_only_with_conversationId()
    test_intent_with_value()
    test_intent_without_value()
    test_both_message_and_intent()
    test_neither_message_nor_intent()
    test_empty_strings()

    print("\n✅ All contract validation tests passed!\n")
