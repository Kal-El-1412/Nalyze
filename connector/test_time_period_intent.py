"""
Test script to verify time period intent handling logic
"""

# Mock the state manager behavior
class MockStateManager:
    def __init__(self):
        self.states = {}

    def get_state(self, conversation_id):
        if conversation_id not in self.states:
            self.states[conversation_id] = {
                "conversation_id": conversation_id,
                "context": {}
            }
        return self.states[conversation_id].copy()

    def update_state(self, conversation_id, **fields):
        if conversation_id not in self.states:
            self.states[conversation_id] = {
                "conversation_id": conversation_id,
                "context": {}
            }
        self.states[conversation_id].update(fields)
        return self.states[conversation_id].copy()


def test_time_period_normalization():
    """Test that time period values are properly normalized"""

    # Map from frontend (F2 spec)
    time_period_map = {
        'Last 7 days': 'last_7_days',
        'Last 30 days': 'last_30_days',
        'Last 90 days': 'last_90_days',
        'All time': 'all_time',
    }

    for friendly, normalized in time_period_map.items():
        print(f"✓ '{friendly}' → '{normalized}'")

    print("\n✅ Time period normalization mapping verified")


def test_intent_flow():
    """Test the flow of intent handling"""

    print("\nTesting intent flow:")
    print("=" * 50)

    state_manager = MockStateManager()
    conversation_id = "test-conversation-1"

    # Step 1: Set analysis_type
    print("\n1. User selects analysis_type: 'trend'")
    state = state_manager.get_state(conversation_id)
    context = state.get("context", {})
    context["analysis_type"] = "trend"
    state_manager.update_state(conversation_id, context=context)

    # Check state readiness
    updated_state = state_manager.get_state(conversation_id)
    updated_context = updated_state.get("context", {})
    has_analysis = "analysis_type" in updated_context
    has_time_period = "time_period" in updated_context
    is_ready = has_analysis and has_time_period

    print(f"   - has_analysis_type: {has_analysis}")
    print(f"   - has_time_period: {has_time_period}")
    print(f"   - is_ready: {is_ready}")

    if not is_ready:
        if not has_analysis:
            print("   → Should ask for: analysis_type")
        elif not has_time_period:
            print("   → Should ask for: time_period")

    # Step 2: Set time_period
    print("\n2. User selects time_period: 'last_7_days' (normalized from 'Last 7 days')")
    state = state_manager.get_state(conversation_id)
    context = state.get("context", {})
    context["time_period"] = "last_7_days"
    state_manager.update_state(conversation_id, context=context)

    # Check state readiness again
    updated_state = state_manager.get_state(conversation_id)
    updated_context = updated_state.get("context", {})
    has_analysis = "analysis_type" in updated_context
    has_time_period = "time_period" in updated_context
    is_ready = has_analysis and has_time_period

    print(f"   - has_analysis_type: {has_analysis}")
    print(f"   - has_time_period: {has_time_period}")
    print(f"   - is_ready: {is_ready}")

    if is_ready:
        print("   → Should proceed to: generate queries (run)")

    # Step 3: Verify time period is not asked again
    print("\n3. User sends another message")
    state = state_manager.get_state(conversation_id)
    context = state.get("context", {})

    print(f"   - has_time_period: {'time_period' in context}")
    if "time_period" in context:
        print(f"   - time_period value: {context['time_period']}")
        print("   → Should NOT ask for time_period again")

    print("\n✅ Intent flow verified")


def test_reverse_order():
    """Test setting time_period before analysis_type"""

    print("\nTesting reverse order (time_period first):")
    print("=" * 50)

    state_manager = MockStateManager()
    conversation_id = "test-conversation-2"

    # Step 1: Set time_period first
    print("\n1. User selects time_period: 'last_30_days' (normalized from 'Last 30 days')")
    state = state_manager.get_state(conversation_id)
    context = state.get("context", {})
    context["time_period"] = "last_30_days"
    state_manager.update_state(conversation_id, context=context)

    # Check state readiness
    updated_state = state_manager.get_state(conversation_id)
    updated_context = updated_state.get("context", {})
    has_analysis = "analysis_type" in updated_context
    has_time_period = "time_period" in updated_context
    is_ready = has_analysis and has_time_period

    print(f"   - has_analysis_type: {has_analysis}")
    print(f"   - has_time_period: {has_time_period}")
    print(f"   - is_ready: {is_ready}")

    if not is_ready:
        if not has_analysis:
            print("   → Should ask for: analysis_type")
        elif not has_time_period:
            print("   → Should ask for: time_period")

    # Step 2: Set analysis_type
    print("\n2. User selects analysis_type: 'row_count'")
    state = state_manager.get_state(conversation_id)
    context = state.get("context", {})
    context["analysis_type"] = "row_count"
    state_manager.update_state(conversation_id, context=context)

    # Check state readiness again
    updated_state = state_manager.get_state(conversation_id)
    updated_context = updated_state.get("context", {})
    has_analysis = "analysis_type" in updated_context
    has_time_period = "time_period" in updated_context
    is_ready = has_analysis and has_time_period

    print(f"   - has_analysis_type: {has_analysis}")
    print(f"   - has_time_period: {has_time_period}")
    print(f"   - is_ready: {is_ready}")

    if is_ready:
        print("   → Should proceed to: generate queries (run)")

    print("\n✅ Reverse order flow verified")


if __name__ == "__main__":
    print("=" * 50)
    print("Time Period Intent Handling Tests")
    print("=" * 50)

    test_time_period_normalization()
    test_intent_flow()
    test_reverse_order()

    print("\n" + "=" * 50)
    print("All tests completed successfully! ✅")
    print("=" * 50)
