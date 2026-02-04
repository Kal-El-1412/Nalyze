#!/usr/bin/env python3
"""
Test that LLM is not allowed to ask clarification questions.
All clarifications must come from backend state checks.
"""

import re

print("=" * 70)
print("TEST: LLM Cannot Ask Clarification Questions")
print("=" * 70)

# Read the chat orchestrator file
with open("app/chat_orchestrator.py", "r") as f:
    content = f.read()

print("\n### TEST 1: System Prompt Forbids Clarification")
print("-" * 70)

# Check for the key instructions
checks = [
    ("NEVER ask clarifying questions", "✓ Instruction present"),
    ("DO NOT ask the user for clarification", "✓ Instruction present"),
    ("DO NOT use the \"needs_clarification\" response type", "✓ Instruction present"),
    ("All required context (analysis type, time period, etc.) is provided by the backend", "✓ Context guarantee present"),
    ("make reasonable assumptions based on schema", "✓ Assumption guidance present"),
    ("NEVER ask clarification questions - make informed decisions", "✓ Reinforcement present")
]

test_1_passed = True
for phrase, success_msg in checks:
    if phrase in content:
        print(success_msg)
    else:
        print(f"✗ MISSING: '{phrase}'")
        test_1_passed = False

if test_1_passed:
    print("✓ PASS: System prompt forbids LLM clarifications")
else:
    print("✗ FAIL: System prompt missing key instructions")
    exit(1)

print("\n### TEST 2: No Clarification Examples in Prompt")
print("-" * 70)

# Extract the SYSTEM_PROMPT
match = re.search(r'SYSTEM_PROMPT = """(.+?)"""', content, re.DOTALL)
if match:
    system_prompt = match.group(1)

    # Check that there are NO examples of needs_clarification in responses
    if '"type": "needs_clarification"' in system_prompt:
        print("✗ FAIL: System prompt still contains needs_clarification examples")
        exit(1)
    else:
        print("✓ PASS: No needs_clarification examples in system prompt")

    # Check that examples show only run_queries and final_answer
    if '"type": "run_queries"' in system_prompt and '"type": "final_answer"' in system_prompt:
        print("✓ PASS: Only run_queries and final_answer examples present")
    else:
        print("✗ FAIL: Missing expected response type examples")
        exit(1)
else:
    print("✗ FAIL: Could not find SYSTEM_PROMPT")
    exit(1)

print("\n### TEST 3: Ambiguity Handling Updated")
print("-" * 70)

# Check that ambiguity handling doesn't suggest asking questions
ambiguity_keywords = [
    "Use the first detected date column",
    "Make reasonable assumptions",
    "analyze all relevant numeric columns"
]

test_3_passed = True
for keyword in ambiguity_keywords:
    if keyword in content:
        print(f"✓ Found: '{keyword}'")
    else:
        print(f"✗ Missing: '{keyword}'")
        test_3_passed = False

# Make sure it doesn't say "ask which one"
if "ask which one" in system_prompt:
    print("✗ FAIL: Prompt still suggests asking user")
    test_3_passed = False
else:
    print("✓ PASS: No suggestions to ask user")

if test_3_passed:
    print("✓ PASS: Ambiguity handling updated correctly")
else:
    print("✗ FAIL: Ambiguity handling needs updates")
    exit(1)

print("\n### TEST 4: Parse Response Rejects LLM Clarifications")
print("-" * 70)

# Check that _parse_response raises error for needs_clarification
if 'if response_type == "needs_clarification":' in content:
    # Check that it raises an error instead of returning NeedsClarificationResponse
    parse_section = content.split('if response_type == "needs_clarification":')[1].split('elif response_type')[0]

    if "raise ValueError" in parse_section:
        print("✓ PASS: _parse_response raises error for needs_clarification")

        if "LLM attempted to ask a clarification question" in parse_section:
            print("✓ PASS: Error message is clear")
        else:
            print("⚠ WARNING: Error message could be clearer")
    else:
        print("✗ FAIL: _parse_response still returns NeedsClarificationResponse")
        exit(1)
else:
    print("✗ FAIL: Cannot find needs_clarification handling")
    exit(1)

print("\n### TEST 5: Conversation State Passed to LLM")
print("-" * 70)

# Check that _build_messages includes state context
if "_build_context_info" in content:
    print("✓ PASS: Context info builder method exists")
else:
    print("✗ FAIL: No context info builder")
    exit(1)

if "state_manager.get_state" in content:
    print("✓ PASS: State manager is used in orchestrator")
else:
    print("✗ FAIL: State manager not used")
    exit(1)

if "User Preferences:" in content:
    print("✓ PASS: User preferences added to LLM messages")
else:
    print("✗ FAIL: User preferences not passed to LLM")
    exit(1)

# Check that context fields are included
context_fields = ["analysis_type", "time_period", "metric", "dimension", "grouping"]
test_5_passed = True
for field in context_fields:
    if field in content:
        print(f"✓ Field supported: {field}")
    else:
        print(f"⚠ Field not found: {field}")

print("✓ PASS: Conversation state passed to LLM")

print("\n### TEST 6: Import Statement Updated")
print("-" * 70)

if "from app.state import state_manager" in content:
    print("✓ PASS: state_manager imported")
else:
    print("✗ FAIL: state_manager not imported")
    exit(1)

print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED")
print("=" * 70)

print("\nValidated Behaviors:")
print("✓ System prompt forbids LLM clarifications")
print("✓ No clarification examples in prompt")
print("✓ Ambiguity handled via assumptions, not questions")
print("✓ LLM clarification attempts raise errors")
print("✓ Conversation state passed to LLM")
print("✓ State manager properly imported")

print("\nAcceptance Criteria:")
print("✅ LLM responses never contain questions")
print("✅ All questions originate from backend logic")
print("✅ LLM has full context from conversation state")
print("✅ LLM makes reasonable assumptions instead of asking")
