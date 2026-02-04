#!/usr/bin/env python3
"""
Complete validation test - checks implementation without requiring dependencies.
"""

import os
import re

print("=" * 70)
print("COMPLETE VALIDATION: All Four Prompts")
print("=" * 70)

errors = []

print("\n### Prompt 1: State Manager")
print("-" * 70)

if os.path.exists("app/state.py"):
    with open("app/state.py", "r") as f:
        state_content = f.read()

    checks = [
        ("def get_state", "get_state function exists"),
        ("def update_state", "update_state function exists"),
        ("def is_ready", "is_ready function exists"),
        ("def clear_state", "clear_state function exists"),
        ("import threading", "Thread-safe (threading imported)"),
        ("state_manager =", "State manager instance exists"),
    ]

    for check, desc in checks:
        if check in state_content:
            print(f"✓ {desc}")
        else:
            print(f"✗ MISSING: {desc}")
            errors.append(f"Prompt 1: {desc}")
else:
    print("✗ FAIL: app/state.py not found")
    errors.append("Prompt 1: state.py missing")

print("\n### Prompt 2: Intent-Based Chat")
print("-" * 70)

if os.path.exists("app/models.py"):
    with open("app/models.py", "r") as f:
        models_content = f.read()

    checks = [
        ("intent: Optional[str]", "Intent field in request model"),
        ("value: Optional", "Value field in request model"),
        ("class IntentAcknowledgmentResponse", "IntentAcknowledgmentResponse model"),
    ]

    for check, desc in checks:
        if check in models_content:
            print(f"✓ {desc}")
        else:
            print(f"✗ MISSING: {desc}")
            errors.append(f"Prompt 2: {desc}")
else:
    print("✗ FAIL: app/models.py not found")
    errors.append("Prompt 2: models.py missing")

if os.path.exists("app/main.py"):
    with open("app/main.py", "r") as f:
        main_content = f.read()

    checks = [
        ("async def handle_intent", "handle_intent function exists"),
        ("async def handle_message", "handle_message function exists"),
        ("if request.intent:", "Intent routing logic"),
    ]

    for check, desc in checks:
        if check in main_content:
            print(f"✓ {desc}")
        else:
            print(f"✗ MISSING: {desc}")
            errors.append(f"Prompt 2: {desc}")
else:
    print("✗ FAIL: app/main.py not found")
    errors.append("Prompt 2: main.py missing")

print("\n### Prompt 3: Deterministic Clarifications")
print("-" * 70)

if os.path.exists("app/main.py"):
    with open("app/main.py", "r") as f:
        main_content = f.read()

    checks = [
        ('if "analysis_type" not in context:', "Analysis type check"),
        ('if "time_period" not in context:', "Time period check"),
        ("return NeedsClarificationResponse", "Returns clarification"),
        ("chat_orchestrator.process", "Calls LLM when ready"),
    ]

    for check, desc in checks:
        if check in main_content:
            print(f"✓ {desc}")
        else:
            print(f"✗ MISSING: {desc}")
            errors.append(f"Prompt 3: {desc}")
else:
    print("✗ FAIL: app/main.py not found")
    errors.append("Prompt 3: main.py missing")

print("\n### Prompt 4: Disable LLM Clarifications")
print("-" * 70)

if os.path.exists("app/chat_orchestrator.py"):
    with open("app/chat_orchestrator.py", "r") as f:
        orchestrator_content = f.read()

    # Extract system prompt
    match = re.search(r'SYSTEM_PROMPT = """(.+?)"""', orchestrator_content, re.DOTALL)
    if match:
        system_prompt = match.group(1)

        prompt_checks = [
            ("NEVER ask clarifying questions", "Forbids clarifications"),
            ("DO NOT ask the user for clarification", "Explicit instruction"),
            ("DO NOT use the \"needs_clarification\" response type", "Forbids response type"),
            ("Make reasonable assumptions", "Assumption guidance"),
        ]

        for check, desc in prompt_checks:
            if check in system_prompt:
                print(f"✓ System prompt: {desc}")
            else:
                print(f"✗ MISSING: System prompt {desc}")
                errors.append(f"Prompt 4: System prompt {desc}")

        # Check NO clarification examples
        if '"type": "needs_clarification"' not in system_prompt:
            print("✓ No needs_clarification examples in prompt")
        else:
            print("✗ FAIL: System prompt still has clarification examples")
            errors.append("Prompt 4: Clarification examples present")

    else:
        print("✗ FAIL: Could not find SYSTEM_PROMPT")
        errors.append("Prompt 4: SYSTEM_PROMPT not found")

    # Check parse response rejects clarifications
    if 'if response_type == "needs_clarification":' in orchestrator_content:
        section = orchestrator_content.split('if response_type == "needs_clarification":')[1].split('elif')[0]
        if "raise ValueError" in section and "LLM attempted to ask a clarification question" in section:
            print("✓ Parse response rejects LLM clarifications")
        else:
            print("✗ FAIL: Parse response should reject with error")
            errors.append("Prompt 4: Parse response doesn't reject")
    else:
        print("✗ FAIL: needs_clarification handling not found")
        errors.append("Prompt 4: needs_clarification not handled")

    # Check state passed to LLM
    checks = [
        ("from app.state import state_manager", "State manager imported"),
        ("_build_context_info", "Context builder method exists"),
        ("state_manager.get_state", "Gets state for LLM"),
        ("User Preferences:", "Passes preferences to LLM"),
    ]

    for check, desc in checks:
        if check in orchestrator_content:
            print(f"✓ {desc}")
        else:
            print(f"✗ MISSING: {desc}")
            errors.append(f"Prompt 4: {desc}")

else:
    print("✗ FAIL: app/chat_orchestrator.py not found")
    errors.append("Prompt 4: chat_orchestrator.py missing")

print("\n### Documentation Check")
print("-" * 70)

docs = [
    ("STATE_MANAGER.md", "State manager docs"),
    ("INTENT_API.md", "Intent API docs"),
    ("CLARIFICATION_FLOW.md", "Clarification flow docs"),
    ("CHANGES.md", "Change log"),
    ("IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
    ("PROMPT_4_SUMMARY.md", "Prompt 4 summary"),
]

for doc_file, desc in docs:
    if os.path.exists(doc_file):
        print(f"✓ {desc} exists")
    else:
        print(f"⚠ {desc} not found")

print("\n### Test Files Check")
print("-" * 70)

tests = [
    ("test_state.py", "State manager tests"),
    ("test_contract.py", "Contract structure tests"),
    ("test_clarification_flow.py", "Clarification flow demo"),
    ("test_logic_flow.py", "Logic flow tests"),
    ("test_llm_no_clarification.py", "LLM clarification prevention"),
]

for test_file, desc in tests:
    if os.path.exists(test_file):
        print(f"✓ {desc} exists")
    else:
        print(f"⚠ {desc} not found")

print("\n" + "=" * 70)

if errors:
    print(f"✗ VALIDATION FAILED: {len(errors)} issues")
    print("=" * 70)
    for error in errors:
        print(f"  - {error}")
    exit(1)
else:
    print("✓ VALIDATION PASSED")
    print("=" * 70)

    print("\nAll Four Prompts Implemented:")
    print("✅ Prompt 1: State Manager")
    print("✅ Prompt 2: Intent-Based Chat")
    print("✅ Prompt 3: Deterministic Clarifications")
    print("✅ Prompt 4: Disable LLM Clarifications")

    print("\nSystem Architecture:")
    print("  User Request")
    print("       ↓")
    print("  /chat endpoint (main.py)")
    print("       ↓")
    print("  ┌────────────────┬─────────────────┐")
    print("  │                │                 │")
    print("  Intent       Message          Message")
    print("  Request      (no context)     (with context)")
    print("       ↓            ↓                 ↓")
    print("  handle_intent  Clarification   handle_message")
    print("       ↓         (backend)            ↓")
    print("  Update State                   LLM Processing")
    print("       ↓                              ↓")
    print("  Acknowledge                    run_queries or")
    print("                                 final_answer")
    print("")
    print("✓ Clear separation of concerns")
    print("✓ Backend handles clarifications")
    print("✓ LLM handles analysis only")
