#!/bin/bash
# Test script to verify intent handler processes clarification option clicks correctly

echo "🧪 Testing Intent Handler - Clarification Option Clicks"
echo "========================================================"
echo ""

# Test 1: set_analysis_type with "Row count"
echo "Test 1: Sending intent='set_analysis_type', value='Row count'"
echo "Expected: Should return type='run_queries' with SELECT COUNT(*) query"
echo ""

response=$(curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "test_dataset",
    "conversationId": "test_conv_1",
    "intent": "set_analysis_type",
    "value": "Row count"
  }')

echo "Response:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Check if response contains "run_queries" or "intent_acknowledgment" (not "Please provide a message")
if echo "$response" | grep -q '"type".*:.*"run_queries"'; then
    echo "✅ Test 1 PASSED: Got run_queries response"
elif echo "$response" | grep -q '"type".*:.*"intent_acknowledgment"'; then
    echo "✅ Test 1 PASSED: Got intent_acknowledgment response"
elif echo "$response" | grep -q "Please provide a message"; then
    echo "❌ Test 1 FAILED: Still returning 'Please provide a message' error"
else
    echo "⚠️  Test 1: Unexpected response type"
fi
echo ""
echo "========================================================"
echo ""

# Test 2: set_analysis_type with "Trends over time"
echo "Test 2: Sending intent='set_analysis_type', value='Trends over time'"
echo ""

response=$(curl -s http://localhost:7337/chat \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "test_dataset",
    "conversationId": "test_conv_2",
    "intent": "set_analysis_type",
    "value": "Trends over time"
  }')

echo "Response type:"
echo "$response" | grep -o '"type"[^,]*'
echo ""

if echo "$response" | grep -q '"type".*:.*"run_queries"'; then
    echo "✅ Test 2 PASSED: Got run_queries response"
elif echo "$response" | grep -q '"type".*:.*"intent_acknowledgment"'; then
    echo "✅ Test 2 PASSED: Got intent_acknowledgment response"
elif echo "$response" | grep -q '"type".*:.*"needs_clarification"'; then
    echo "⚠️  Test 2: Got needs_clarification (may need time_period)"
else
    echo "❌ Test 2 FAILED: Unexpected response"
fi
echo ""
echo "========================================================"

echo ""
echo "Note: Make sure the connector is running on http://localhost:7337"
echo "Run with: cd connector && ./run.sh"
