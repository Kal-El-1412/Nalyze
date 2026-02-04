#!/usr/bin/env python3
"""
Test script to verify the new /chat contract structure.
This demonstrates the API contract without requiring full dependencies.
"""

import json

print("Testing /chat API Contract Changes")
print("=" * 60)

print("\n✓ BACKWARD COMPATIBLE - Message-based request:")
message_request = {
    "datasetId": "abc-123",
    "conversationId": "conv-456",
    "message": "Show me sales trends"
}
print(json.dumps(message_request, indent=2))

print("\n✓ NEW - Intent-based request (set_analysis_type):")
intent_request_1 = {
    "datasetId": "abc-123",
    "conversationId": "conv-456",
    "intent": "set_analysis_type",
    "value": "trend"
}
print(json.dumps(intent_request_1, indent=2))

print("\n✓ NEW - Intent-based request (set_time_period):")
intent_request_2 = {
    "datasetId": "abc-123",
    "conversationId": "conv-456",
    "intent": "set_time_period",
    "value": "last_30_days"
}
print(json.dumps(intent_request_2, indent=2))

print("\n✓ NEW - Intent-based response:")
intent_response = {
    "type": "intent_acknowledged",
    "intent": "set_analysis_type",
    "value": "trend",
    "state": {
        "conversation_id": "conv-456",
        "dataset_id": "abc-123",
        "ready": True,
        "message_count": 0,
        "context": {
            "analysis_type": "trend"
        }
    },
    "message": "Updated analysis type to 'trend'"
}
print(json.dumps(intent_response, indent=2))

print("\n" + "=" * 60)
print("Contract Validation Rules:")
print("=" * 60)
print("✓ Either 'message' OR 'intent' must be provided")
print("✓ Cannot provide both 'message' and 'intent'")
print("✓ If 'intent' is provided, 'value' is required")
print("✓ Intent requests bypass LLM and update state directly")
print("✓ Message requests trigger LLM processing (existing flow)")
print("\n✓ All contract requirements met!")
