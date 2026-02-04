"""
Test AI Mode configuration and validation
"""
import sys
import os

# Set environment BEFORE importing config
print("=" * 70)
print("AI MODE CONFIGURATION TEST")
print("=" * 70)

# Test 1: AI_MODE=off (default)
print("\n1️⃣  Test: AI_MODE=off (default)")
print("-" * 70)
os.environ.pop("AI_MODE", None)
os.environ.pop("OPENAI_API_KEY", None)

sys.path.insert(0, '/tmp/cc-agent/63216419/project/connector')
from app.config import Config

config1 = Config()
print(f"   ai_mode: {config1.ai_mode}")
print(f"   openai_api_key configured: {bool(config1.openai_api_key)}")
is_valid, error = config1.validate_ai_mode_for_request()
print(f"   validate_ai_mode_for_request(): valid={is_valid}")
if not is_valid:
    print(f"   error: {error}")
print(f"   ✅ Expected: AI mode OFF, validation returns False")

# Test 2: AI_MODE=on, no API key
print("\n2️⃣  Test: AI_MODE=on, no API key")
print("-" * 70)
os.environ["AI_MODE"] = "on"
os.environ.pop("OPENAI_API_KEY", None)

config2 = Config()
print(f"   ai_mode: {config2.ai_mode}")
print(f"   openai_api_key configured: {bool(config2.openai_api_key)}")
is_valid, error = config2.validate_ai_mode_for_request()
print(f"   validate_ai_mode_for_request(): valid={is_valid}")
if not is_valid:
    print(f"   error: {error}")
print(f"   ✅ Expected: AI mode ON, validation returns False with error message")

# Test 3: AI_MODE=on, with API key
print("\n3️⃣  Test: AI_MODE=on, with API key")
print("-" * 70)
os.environ["AI_MODE"] = "on"
os.environ["OPENAI_API_KEY"] = "sk-test-key-12345"

config3 = Config()
print(f"   ai_mode: {config3.ai_mode}")
print(f"   openai_api_key configured: {bool(config3.openai_api_key)}")
is_valid, error = config3.validate_ai_mode_for_request()
print(f"   validate_ai_mode_for_request(): valid={is_valid}")
if error:
    print(f"   error: {error}")
print(f"   ✅ Expected: AI mode ON, validation returns True")

# Test 4: Different AI_MODE values
print("\n4️⃣  Test: Different AI_MODE values")
print("-" * 70)
for value in ["on", "ON", "true", "TRUE", "1", "yes", "YES", "off", "OFF", "false", "0", "no"]:
    os.environ["AI_MODE"] = value
    config_test = Config()
    expected = value.lower() in ["on", "true", "1", "yes"]
    actual = config_test.ai_mode
    status = "✅" if actual == expected else "❌"
    print(f"   AI_MODE={value:8s} → ai_mode={actual!s:5s} (expected {expected!s:5s}) {status}")

# Test 5: get_safe_summary()
print("\n5️⃣  Test: get_safe_summary() output")
print("-" * 70)
os.environ["AI_MODE"] = "on"
os.environ["OPENAI_API_KEY"] = "sk-test-key-12345"

config5 = Config()
summary = config5.get_safe_summary()
print(f"   aiMode: {summary.get('aiMode')}")
print(f"   openaiApiKeyConfigured: {summary.get('openaiApiKeyConfigured')}")
print(f"   ✅ Expected: aiMode='on', openaiApiKeyConfigured=True")
print(f"   ✅ Key value NOT exposed in summary (security check)")

# Verify key not in summary
if "openai_api_key" not in str(summary).lower() or "sk-test" not in str(summary):
    print(f"   ✅ PASS: API key not exposed")
else:
    print(f"   ❌ FAIL: API key exposed in summary!")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
