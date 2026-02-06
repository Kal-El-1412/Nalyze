"""
Test AE-2: Deterministic Router Analysis Type Mapping

Verifies that the deterministic router correctly maps keywords to analysis types
with appropriate confidence levels.

Run with: python3 test_ae2_deterministic_router.py
"""

import sys
from app.router import deterministic_router


def test_row_count_keywords():
    """Test row_count keyword mapping"""
    print("\n" + "=" * 60)
    print("Test 1: Row Count Keywords")
    print("=" * 60)

    test_cases = [
        ("row count", "row_count", 0.9),
        ("count rows", "row_count", 0.9),
        ("how many rows", "row_count", 0.9),
        ("what's the row count", "row_count", 0.9),
        ("give me the count rows", "row_count", 0.9),
        ("how many rows are there", "row_count", 0.9),
    ]

    all_passed = True
    for message, expected_type, min_confidence in test_cases:
        result = deterministic_router.route_intent(message)

        if result["analysis_type"] == expected_type and result["confidence"] >= min_confidence:
            print(f"✅ '{message}' → {expected_type} (confidence: {result['confidence']:.2f})")
        else:
            print(f"❌ '{message}' → {result['analysis_type']} (confidence: {result['confidence']:.2f})")
            print(f"   Expected: {expected_type} with confidence >= {min_confidence}")
            all_passed = False

    return all_passed


def test_trend_keywords():
    """Test trend keyword mapping"""
    print("\n" + "=" * 60)
    print("Test 2: Trend Keywords")
    print("=" * 60)

    test_cases = [
        ("trend", "trend", 0.9),
        ("trends", "trend", 0.9),
        ("monthly", "trend", 0.9),
        ("weekly", "trend", 0.9),
        ("over time", "trend", 0.9),
        ("mom", "trend", 0.9),
        ("wow", "trend", 0.9),
        ("show me the trend", "trend", 0.9),
        ("what's the trend over time", "trend", 0.9),
        ("monthly breakdown", "trend", 0.9),  # Could match both, but trend should win
    ]

    all_passed = True
    for message, expected_type, min_confidence in test_cases:
        result = deterministic_router.route_intent(message)

        if result["analysis_type"] == expected_type and result["confidence"] >= min_confidence:
            print(f"✅ '{message}' → {expected_type} (confidence: {result['confidence']:.2f})")
        else:
            print(f"❌ '{message}' → {result['analysis_type']} (confidence: {result['confidence']:.2f})")
            print(f"   Expected: {expected_type} with confidence >= {min_confidence}")
            all_passed = False

    return all_passed


def test_outliers_keywords():
    """Test outliers keyword mapping"""
    print("\n" + "=" * 60)
    print("Test 3: Outliers Keywords")
    print("=" * 60)

    test_cases = [
        ("outliers", "outliers", 0.9),
        ("outlier", "outliers", 0.9),
        ("anomaly", "outliers", 0.9),
        ("anomalies", "outliers", 0.9),
        ("std dev", "outliers", 0.9),
        ("z-score", "outliers", 0.9),
        ("z score", "outliers", 0.9),
        ("show me outliers", "outliers", 0.9),
        ("find anomalies", "outliers", 0.9),
        ("2 std dev", "outliers", 0.9),
    ]

    all_passed = True
    for message, expected_type, min_confidence in test_cases:
        result = deterministic_router.route_intent(message)

        if result["analysis_type"] == expected_type and result["confidence"] >= min_confidence:
            print(f"✅ '{message}' → {expected_type} (confidence: {result['confidence']:.2f})")
        else:
            print(f"❌ '{message}' → {result['analysis_type']} (confidence: {result['confidence']:.2f})")
            print(f"   Expected: {expected_type} with confidence >= {min_confidence}")
            all_passed = False

    return all_passed


def test_top_categories_keywords():
    """Test top_categories keyword mapping"""
    print("\n" + "=" * 60)
    print("Test 4: Top Categories Keywords")
    print("=" * 60)

    test_cases = [
        ("top categories", "top_categories", 0.9),
        ("breakdown", "top_categories", 0.9),
        ("group by", "top_categories", 0.9),
        ("grouped by", "top_categories", 0.9),
        ("show me top categories", "top_categories", 0.9),
        ("give me a breakdown", "top_categories", 0.9),
        ("group by category", "top_categories", 0.9),
        ("top 10", "top_categories", 0.9),
    ]

    all_passed = True
    for message, expected_type, min_confidence in test_cases:
        result = deterministic_router.route_intent(message)

        if result["analysis_type"] == expected_type and result["confidence"] >= min_confidence:
            print(f"✅ '{message}' → {expected_type} (confidence: {result['confidence']:.2f})")
        else:
            print(f"❌ '{message}' → {result['analysis_type']} (confidence: {result['confidence']:.2f})")
            print(f"   Expected: {expected_type} with confidence >= {min_confidence}")
            all_passed = False

    return all_passed


def test_exact_match_confidence():
    """Test that exact matches get confidence >= 0.9"""
    print("\n" + "=" * 60)
    print("Test 5: Exact Match Confidence Levels")
    print("=" * 60)

    test_cases = [
        ("row count", 0.9),
        ("trend", 0.9),
        ("outliers", 0.9),
        ("top categories", 0.9),
    ]

    all_passed = True
    for message, min_confidence in test_cases:
        result = deterministic_router.route_intent(message)

        if result["confidence"] >= min_confidence:
            print(f"✅ '{message}' → confidence: {result['confidence']:.2f} (>= {min_confidence})")
        else:
            print(f"❌ '{message}' → confidence: {result['confidence']:.2f} (< {min_confidence})")
            all_passed = False

    return all_passed


def test_never_fallback_to_generic():
    """Test that 'row count' never falls into generic/default plan"""
    print("\n" + "=" * 60)
    print("Test 6: No Generic/Default Fallback")
    print("=" * 60)

    critical_phrases = [
        "row count",
        "count rows",
        "trend",
        "outliers",
        "top categories",
    ]

    all_passed = True
    for phrase in critical_phrases:
        result = deterministic_router.route_intent(phrase)

        # These should ALWAYS return a valid analysis_type, never None
        if result["analysis_type"] is not None and result["confidence"] >= 0.9:
            print(f"✅ '{phrase}' → {result['analysis_type']} (NOT generic/default)")
        else:
            print(f"❌ '{phrase}' → {result['analysis_type']} with confidence {result['confidence']:.2f}")
            print(f"   This would fallback to generic/default plan!")
            all_passed = False

    return all_passed


def test_case_insensitive():
    """Test that matching is case-insensitive"""
    print("\n" + "=" * 60)
    print("Test 7: Case Insensitive Matching")
    print("=" * 60)

    test_cases = [
        ("ROW COUNT", "row_count"),
        ("Row Count", "row_count"),
        ("TREND", "trend"),
        ("Trend", "trend"),
        ("OUTLIERS", "outliers"),
        ("Outliers", "outliers"),
        ("TOP CATEGORIES", "top_categories"),
        ("Top Categories", "top_categories"),
    ]

    all_passed = True
    for message, expected_type in test_cases:
        result = deterministic_router.route_intent(message)

        if result["analysis_type"] == expected_type and result["confidence"] >= 0.9:
            print(f"✅ '{message}' → {expected_type} (confidence: {result['confidence']:.2f})")
        else:
            print(f"❌ '{message}' → {result['analysis_type']} (confidence: {result['confidence']:.2f})")
            print(f"   Expected: {expected_type}")
            all_passed = False

    return all_passed


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AE-2: Deterministic Router - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Row count keywords
    results.append(("row_count keywords", test_row_count_keywords()))

    # Test 2: Trend keywords
    results.append(("trend keywords", test_trend_keywords()))

    # Test 3: Outliers keywords
    results.append(("outliers keywords", test_outliers_keywords()))

    # Test 4: Top categories keywords
    results.append(("top_categories keywords", test_top_categories_keywords()))

    # Test 5: Exact match confidence
    results.append(("exact match confidence >= 0.9", test_exact_match_confidence()))

    # Test 6: Never fallback to generic
    results.append(("no generic/default fallback", test_never_fallback_to_generic()))

    # Test 7: Case insensitive
    results.append(("case insensitive matching", test_case_insensitive()))

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
        print("✅ 'row count' → analysis_type='row_count' with confidence >= 0.9")
        print("✅ 'trend', 'monthly', 'weekly', 'over time', 'mom', 'wow' → analysis_type='trend'")
        print("✅ 'outlier', 'anomaly', 'std dev', 'z-score' → analysis_type='outliers'")
        print("✅ 'top categories', 'breakdown', 'group by' → analysis_type='top_categories'")
        print("✅ Exact matches get confidence >= 0.9")
        print("✅ 'row count' never falls into generic/default plan")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
