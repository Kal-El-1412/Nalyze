"""
Test OFF-REAL-2: Deterministic Intent Mapping

Verifies that the deterministic router correctly maps user messages to analysis types
using improved keyword rules.

Run with: python3 test_deterministic_keywords.py
"""

import sys
from app.router import deterministic_router


def test_row_count_keywords():
    """Test that all row count keywords map correctly"""
    print("\n" + "=" * 60)
    print("Test 1: Row Count Keywords")
    print("=" * 60)

    test_cases = [
        "row count",
        "count rows",
        "how many rows",
        "how many rows?",
        "count the rows",
        "total rows",
    ]

    all_passed = True
    for message in test_cases:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type == "row_count" and confidence >= 0.8:
            print(f"✅ '{message}' → row_count (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f})")
            print(f"   Expected: row_count with confidence >= 0.8")
            all_passed = False

    return all_passed


def test_trend_keywords():
    """Test that all trend keywords map correctly"""
    print("\n" + "=" * 60)
    print("Test 2: Trend Keywords")
    print("=" * 60)

    test_cases = [
        "trend",
        "trends",
        "over time",
        "monthly",
        "weekly",
        "week-over-week",
        "week over week",
        "month-over-month",
        "month over month",
        "show me trends",
        "data over time",
    ]

    all_passed = True
    for message in test_cases:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type == "trend" and confidence >= 0.8:
            print(f"✅ '{message}' → trend (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f})")
            print(f"   Expected: trend with confidence >= 0.8")
            all_passed = False

    return all_passed


def test_outliers_keywords():
    """Test that all outliers keywords map correctly"""
    print("\n" + "=" * 60)
    print("Test 3: Outliers Keywords")
    print("=" * 60)

    test_cases = [
        "outliers",
        "anomalies",
        "2 standard deviations",
        "z-score",
        "zscore",
        "z score",
        "2 std dev",
        "find outliers",
        "show anomalies",
    ]

    all_passed = True
    for message in test_cases:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type == "outliers" and confidence >= 0.8:
            print(f"✅ '{message}' → outliers (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f})")
            print(f"   Expected: outliers with confidence >= 0.8")
            all_passed = False

    return all_passed


def test_no_match_returns_none():
    """Test that unclear messages return None (triggers needs_clarification)"""
    print("\n" + "=" * 60)
    print("Test 4: No Match Returns None")
    print("=" * 60)

    test_cases = [
        "show me something",
        "analyze the data",
        "what can you do",
        "help me understand",
        "tell me about this",
        "random gibberish xyz",
    ]

    all_passed = True
    for message in test_cases:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type is None:
            print(f"✅ '{message}' → None (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f})")
            print(f"   Expected: None (no confident match)")
            all_passed = False

    return all_passed


def test_critical_row_count():
    """Test critical acceptance criteria: 'row count' never returns clarification"""
    print("\n" + "=" * 60)
    print("Test 5: Critical - 'row count' Never Returns Clarification")
    print("=" * 60)

    message = "row count"
    result = deterministic_router.route_intent(message)
    analysis_type = result.get("analysis_type")
    confidence = result.get("confidence", 0.0)

    print(f"Message: '{message}'")
    print(f"Result: analysis_type={analysis_type}, confidence={confidence:.2f}")

    if analysis_type == "row_count" and confidence >= 0.8:
        print(f"✅ CRITICAL TEST PASSED")
        print(f"   'row count' maps to row_count with high confidence")
        print(f"   Will NOT trigger needs_clarification")
        print(f"   Will proceed directly to run_queries")
        return True
    else:
        print(f"❌ CRITICAL TEST FAILED")
        print(f"   Expected: analysis_type=row_count, confidence >= 0.8")
        print(f"   This would trigger needs_clarification (WRONG!)")
        return False


def test_top_categories_keywords():
    """Test that top categories keywords map correctly"""
    print("\n" + "=" * 60)
    print("Test 6: Top Categories Keywords")
    print("=" * 60)

    test_cases = [
        "top categories",
        "top 10",
        "breakdown by category",
        "grouped by",
    ]

    all_passed = True
    for message in test_cases:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type == "top_categories" and confidence >= 0.8:
            print(f"✅ '{message}' → top_categories (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f})")
            print(f"   Expected: top_categories with confidence >= 0.8")
            all_passed = False

    return all_passed


def test_data_quality_keywords():
    """Test that data quality keywords map correctly"""
    print("\n" + "=" * 60)
    print("Test 7: Data Quality Keywords")
    print("=" * 60)

    test_cases = [
        "missing values",
        "nulls",
        "duplicates",
        "data quality",
        "check data",
    ]

    all_passed = True
    for message in test_cases:
        result = deterministic_router.route_intent(message)
        analysis_type = result.get("analysis_type")
        confidence = result.get("confidence", 0.0)

        if analysis_type == "data_quality" and confidence >= 0.8:
            print(f"✅ '{message}' → data_quality (confidence: {confidence:.2f})")
        else:
            print(f"❌ '{message}' → {analysis_type} (confidence: {confidence:.2f})")
            print(f"   Expected: data_quality with confidence >= 0.8")
            all_passed = False

    return all_passed


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OFF-REAL-2: Deterministic Intent Mapping - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Row count keywords
    results.append(("Row count keywords", test_row_count_keywords()))

    # Test 2: Trend keywords
    results.append(("Trend keywords", test_trend_keywords()))

    # Test 3: Outliers keywords
    results.append(("Outliers keywords", test_outliers_keywords()))

    # Test 4: No match returns None
    results.append(("No match returns None", test_no_match_returns_none()))

    # Test 5: Critical - row count never returns clarification
    results.append(("CRITICAL: 'row count' maps directly", test_critical_row_count()))

    # Test 6: Top categories keywords
    results.append(("Top categories keywords", test_top_categories_keywords()))

    # Test 7: Data quality keywords
    results.append(("Data quality keywords", test_data_quality_keywords()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nAcceptance Criteria Met:")
        print("✅ 'row count' maps to row_count with confidence >= 0.8")
        print("✅ 'row count' never triggers needs_clarification")
        print("✅ 'row count' never returns generic template")
        print("✅ All trend keywords map correctly")
        print("✅ All outliers keywords map correctly")
        print("✅ Unclear messages return None (triggers clarification)")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
