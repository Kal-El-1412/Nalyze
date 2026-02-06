"""
Test TP2: Row Count Router Only
Tests that deterministic router matches row count patterns

Run with: python3 test_row_count_router_only.py
"""

import sys
sys.path.insert(0, '/tmp/cc-agent/63216419/project/connector')

from app.router import deterministic_router


def test_deterministic_router():
    """Test that deterministic router matches row count patterns"""
    print("\n" + "=" * 60)
    print("Test: Deterministic Router - Row Count Patterns")
    print("=" * 60)

    test_messages = [
        "row count",
        "count rows",
        "how many rows",
        "how many rows are there",
        "total rows",
        "number of rows",
        "record count",
        "how many records",
        "how many records do we have",
        "what is the row count",
    ]

    all_passed = True
    for message in test_messages:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type == "row_count" and confidence >= 0.8:
            print(f"✅ '{message}' → row_count (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f}) - EXPECTED row_count with >=0.8")
            all_passed = False

    # Also test some negative cases (should NOT match row_count)
    print("\n--- Negative cases (should NOT match row_count) ---")
    negative_messages = [
        "show trends",
        "top categories",
        "find outliers",
    ]

    for message in negative_messages:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type != "row_count":
            print(f"✅ '{message}' → {analysis_type} (confidence: {confidence:.2f}) [correct, not row_count]")
        else:
            print(f"❌ '{message}' → row_count (confidence: {confidence:.2f}) - Should NOT be row_count")
            all_passed = False

    if all_passed:
        print("\n" + "=" * 60)
        print("✅ ALL ROUTER TESTS PASSED!")
        print("=" * 60)
        print("\nAcceptance Criteria Met:")
        print("✅ 'row count' patterns matched with high confidence (>=0.8)")
        print("✅ Deterministic router correctly identifies row_count queries")
        print("=" * 60)
    else:
        print("\n❌ Some router tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    test_deterministic_router()
