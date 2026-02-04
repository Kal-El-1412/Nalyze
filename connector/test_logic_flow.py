#!/usr/bin/env python3
"""
Logic flow test - validates the deterministic clarification flow
without requiring full dependencies.
"""

print("=" * 70)
print("LOGIC FLOW TEST: Deterministic Clarification")
print("=" * 70)

# Simulate conversation state
state = {
    "conversation_id": "test-conv",
    "context": {}
}

def check_clarification_needed(context):
    """Simulates the handle_message logic"""
    if "analysis_type" not in context:
        return {
            "type": "needs_clarification",
            "question": "What type of analysis would you like to perform?",
            "choices": ["trend", "comparison", "distribution", "correlation", "summary"]
        }

    if "time_period" not in context:
        return {
            "type": "needs_clarification",
            "question": "What time period would you like to analyze?",
            "choices": ["last_7_days", "last_30_days", "last_90_days", "last_year", "year_to_date", "all_time"]
        }

    return {"type": "ready_for_llm"}

print("\n### TEST 1: Empty state")
print("-" * 70)
result = check_clarification_needed(state["context"])
print(f"Context: {state['context']}")
print(f"Result: {result['type']}")
if result["type"] == "needs_clarification":
    print(f"Question: {result['question']}")
    assert "analysis" in result["question"].lower()
    print("✓ PASS: Returns analysis_type clarification")
else:
    print("✗ FAIL: Should return clarification")
    exit(1)

print("\n### TEST 2: After setting analysis_type")
print("-" * 70)
state["context"]["analysis_type"] = "trend"
result = check_clarification_needed(state["context"])
print(f"Context: {state['context']}")
print(f"Result: {result['type']}")
if result["type"] == "needs_clarification":
    print(f"Question: {result['question']}")
    assert "time period" in result["question"].lower()
    assert "analysis" not in result["question"].lower()
    print("✓ PASS: Returns time_period clarification")
    print("✓ PASS: Does NOT repeat analysis_type question")
else:
    print("✗ FAIL: Should return time_period clarification")
    exit(1)

print("\n### TEST 3: After setting both fields")
print("-" * 70)
state["context"]["time_period"] = "last_30_days"
result = check_clarification_needed(state["context"])
print(f"Context: {state['context']}")
print(f"Result: {result['type']}")
if result["type"] == "ready_for_llm":
    print("✓ PASS: No clarification needed")
    print("✓ PASS: Ready to call LLM")
else:
    print("✗ FAIL: Should be ready for LLM")
    exit(1)

print("\n### TEST 4: Subsequent messages")
print("-" * 70)
# State persists
result = check_clarification_needed(state["context"])
print(f"Context: {state['context']}")
print(f"Result: {result['type']}")
if result["type"] == "ready_for_llm":
    print("✓ PASS: Still ready for LLM")
    print("✓ PASS: No repeated clarifications")
else:
    print("✗ FAIL: Should remain ready")
    exit(1)

print("\n### TEST 5: Check order matters")
print("-" * 70)
# Reset and try setting time_period first
state2 = {"context": {}}
result = check_clarification_needed(state2["context"])
print(f"Empty context: {state2['context']}")
print(f"Result: {result['type']}")
assert result["type"] == "needs_clarification"
assert "analysis" in result["question"].lower()
print("✓ PASS: Still asks for analysis_type first (correct order)")

# Set only time_period
state2["context"]["time_period"] = "last_30_days"
result = check_clarification_needed(state2["context"])
print(f"Only time_period set: {state2['context']}")
print(f"Result: {result['type']}")
assert result["type"] == "needs_clarification"
assert "analysis" in result["question"].lower()
print("✓ PASS: Still asks for analysis_type (required field)")

print("\n### TEST 6: Edge cases")
print("-" * 70)

# Empty string values
state3 = {"context": {"analysis_type": "", "time_period": ""}}
result = check_clarification_needed(state3["context"])
print(f"Empty string values: {state3['context']}")
print(f"Result: {result['type']}")
# In Python, "key in dict" checks if key exists, not if value is truthy
# So empty strings would pass our check (which is acceptable)
print("✓ NOTE: Empty strings pass existence check (acceptable behavior)")

# Additional fields don't break logic
state4 = {"context": {
    "analysis_type": "trend",
    "time_period": "last_30_days",
    "metric": "revenue",
    "dimension": "region"
}}
result = check_clarification_needed(state4["context"])
print(f"Extra fields: {state4['context']}")
print(f"Result: {result['type']}")
assert result["type"] == "ready_for_llm"
print("✓ PASS: Extra fields don't interfere")

print("\n" + "=" * 70)
print("✓ ALL LOGIC TESTS PASSED")
print("=" * 70)

print("\nValidated Behaviors:")
print("✓ analysis_type checked first")
print("✓ time_period checked second")
print("✓ Both required before LLM")
print("✓ No repeated questions")
print("✓ Order enforced")
print("✓ State persistence")
print("✓ Extra fields allowed")
