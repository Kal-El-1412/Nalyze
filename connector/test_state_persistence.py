"""
Test to verify state persistence between requests
"""
import sys
sys.path.insert(0, '/tmp/cc-agent/63216419/project/connector')

from app.state import ConversationStateManager

def test_state_persistence():
    """Test that state persists across get/update calls"""
    print("=" * 70)
    print("STATE PERSISTENCE TEST")
    print("=" * 70)

    manager = ConversationStateManager()
    conv_id = "test-conv-123"

    print("\n1️⃣  Initial state (should be empty context)")
    state1 = manager.get_state(conv_id)
    print(f"   Context: {state1.get('context', {})}")

    print("\n2️⃣  Update: set analysis_type = 'trend'")
    manager.update_state(conv_id, context={"analysis_type": "trend"})
    state2 = manager.get_state(conv_id)
    print(f"   Context: {state2.get('context', {})}")

    print("\n3️⃣  Update: set time_period = 'all_time'")
    # Simulate what handle_intent does:
    state = manager.get_state(conv_id)
    context = state.get("context", {})
    context.update({"time_period": "all_time"})
    manager.update_state(conv_id, context=context)

    state3 = manager.get_state(conv_id)
    print(f"   Context: {state3.get('context', {})}")

    print("\n4️⃣  Verify persistence: get state again")
    state4 = manager.get_state(conv_id)
    print(f"   Context: {state4.get('context', {})}")

    has_analysis = "analysis_type" in state4.get('context', {})
    has_time_period = "time_period" in state4.get('context', {})

    print(f"\n   ✓ has_analysis_type: {has_analysis}")
    print(f"   ✓ has_time_period: {has_time_period}")

    if has_analysis and has_time_period:
        print("\n✅ SUCCESS: State persisted correctly!")
    else:
        print("\n❌ FAILED: State was lost!")
        return False

    # Test with a NEW conversation ID to make sure isolation works
    print("\n5️⃣  New conversation ID should have empty context")
    conv_id_2 = "test-conv-456"
    state5 = manager.get_state(conv_id_2)
    print(f"   Context: {state5.get('context', {})}")

    if len(state5.get('context', {})) == 0:
        print("   ✅ New conversation has empty context (correct)")
    else:
        print("   ❌ New conversation has data (state leak!)")
        return False

    # Verify first conversation still has data
    print("\n6️⃣  Original conversation should still have data")
    state6 = manager.get_state(conv_id)
    print(f"   Context: {state6.get('context', {})}")

    if "analysis_type" in state6.get('context', {}) and "time_period" in state6.get('context', {}):
        print("   ✅ Original conversation data intact")
    else:
        print("   ❌ Original conversation data lost!")
        return False

    return True

if __name__ == "__main__":
    success = test_state_persistence()
    print("\n" + "=" * 70)
    if success:
        print("ALL TESTS PASSED ✅")
    else:
        print("TESTS FAILED ❌")
    print("=" * 70)
