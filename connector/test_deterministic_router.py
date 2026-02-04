"""
Test Deterministic Router (HR-3)

Tests the keyword-based intent router that determines analysis types
with confidence scores before any OpenAI calls.
"""
from app.router import DeterministicRouter


def test_trend_high_confidence():
    """Test trend detection with strong keywords"""
    router = DeterministicRouter()

    # Strong trend keywords
    test_cases = [
        "show me trends over time",
        "what are the monthly trends",
        "display weekly trends",
        "analyze trends",
        "show me the trend",
        "what's trending over time",
    ]

    for message in test_cases:
        result = router.route_intent(message)
        assert result["analysis_type"] == "trend", f"Failed for: {message}"
        assert result["confidence"] >= 0.8, f"Low confidence for: {message} ({result['confidence']})"
        print(f"✓ '{message}' → trend (confidence: {result['confidence']:.2f})")


def test_top_categories_high_confidence():
    """Test top categories detection with strong keywords"""
    router = DeterministicRouter()

    test_cases = [
        "show me the top 10 categories",
        "what are the top categories",
        "breakdown by category",
        "group by category",
        "show me the highest by region",
        "top 5 products",
    ]

    for message in test_cases:
        result = router.route_intent(message)
        assert result["analysis_type"] == "top_categories", f"Failed for: {message}"
        assert result["confidence"] >= 0.8, f"Low confidence for: {message} ({result['confidence']})"
        print(f"✓ '{message}' → top_categories (confidence: {result['confidence']:.2f})")


def test_outliers_high_confidence():
    """Test outliers detection with strong keywords"""
    router = DeterministicRouter()

    test_cases = [
        "find outliers",
        "detect anomalies",
        "show me outliers",
        "check for anomalies",
        "find unusual values",
        "detect abnormal data",
    ]

    for message in test_cases:
        result = router.route_intent(message)
        assert result["analysis_type"] == "outliers", f"Failed for: {message}"
        assert result["confidence"] >= 0.8, f"Low confidence for: {message} ({result['confidence']})"
        print(f"✓ '{message}' → outliers (confidence: {result['confidence']:.2f})")


def test_row_count_high_confidence():
    """Test row count detection with strong keywords"""
    router = DeterministicRouter()

    test_cases = [
        "how many rows",
        "count rows",
        "row count",
        "total rows",
        "how many records",
        "number of rows",
    ]

    for message in test_cases:
        result = router.route_intent(message)
        assert result["analysis_type"] == "row_count", f"Failed for: {message}"
        assert result["confidence"] >= 0.8, f"Low confidence for: {message} ({result['confidence']})"
        print(f"✓ '{message}' → row_count (confidence: {result['confidence']:.2f})")


def test_data_quality_high_confidence():
    """Test data quality detection with strong keywords"""
    router = DeterministicRouter()

    test_cases = [
        "check data quality",
        "find missing values",
        "check for nulls",
        "find duplicates",
        "validate data",
        "check for data issues",
    ]

    for message in test_cases:
        result = router.route_intent(message)
        assert result["analysis_type"] == "data_quality", f"Failed for: {message}"
        assert result["confidence"] >= 0.8, f"Low confidence for: {message} ({result['confidence']})"
        print(f"✓ '{message}' → data_quality (confidence: {result['confidence']:.2f})")


def test_medium_confidence():
    """Test medium confidence with weak keywords"""
    router = DeterministicRouter()

    test_cases = [
        ("show me the history", "trend"),
        ("show me the top", "top_categories"),
        ("find extreme values", "outliers"),
        ("how many", "row_count"),
        ("check for missing", "data_quality"),
    ]

    for message, expected_type in test_cases:
        result = router.route_intent(message)
        # Medium confidence should be between 0.5 and 0.8
        assert 0.5 <= result["confidence"] < 0.8, f"Wrong confidence for: {message} ({result['confidence']})"
        assert result["analysis_type"] == expected_type, f"Failed for: {message}"
        print(f"✓ '{message}' → {expected_type} (confidence: {result['confidence']:.2f})")


def test_low_confidence():
    """Test low confidence returns None"""
    router = DeterministicRouter()

    test_cases = [
        "hello",
        "what is this",
        "help me",
        "I need assistance",
        "show me something",
        "what can you do",
    ]

    for message in test_cases:
        result = router.route_intent(message)
        assert result["confidence"] < 0.5, f"High confidence for ambiguous: {message}"
        assert result["analysis_type"] is None, f"Should return None for: {message}"
        print(f"✓ '{message}' → None (confidence: {result['confidence']:.2f})")


def test_time_period_extraction():
    """Test extraction of time periods from messages"""
    router = DeterministicRouter()

    test_cases = [
        ("show trends last month", "last_month"),
        ("what are the trends last week", "last_week"),
        ("analyze last quarter", "last_quarter"),
        ("show me this year's trends", "this_year"),
    ]

    for message, expected_period in test_cases:
        result = router.route_intent(message)
        assert "time_period" in result["params"], f"No time_period extracted from: {message}"
        assert result["params"]["time_period"] == expected_period, f"Wrong period for: {message}"
        print(f"✓ '{message}' → extracted time_period: {expected_period}")


def test_top_n_extraction():
    """Test extraction of top N limit"""
    router = DeterministicRouter()

    test_cases = [
        ("show me top 5", 5),
        ("top 10 categories", 10),
        ("show the top 3", 3),
    ]

    for message, expected_limit in test_cases:
        result = router.route_intent(message)
        assert "limit" in result["params"], f"No limit extracted from: {message}"
        assert result["params"]["limit"] == expected_limit, f"Wrong limit for: {message}"
        print(f"✓ '{message}' → extracted limit: {expected_limit}")


def test_confidence_levels():
    """Test that confidence levels are in correct ranges"""
    router = DeterministicRouter()

    # High confidence: >= 0.8
    high_conf_messages = [
        "show trends over time",
        "find outliers",
        "how many rows",
    ]

    # Medium confidence: 0.5 - 0.8
    medium_conf_messages = [
        "show me the top",
        "check for missing",
        "show history",
    ]

    # Low confidence: < 0.5
    low_conf_messages = [
        "hello",
        "help",
        "what",
    ]

    for message in high_conf_messages:
        result = router.route_intent(message)
        assert result["confidence"] >= 0.8, f"Should be high confidence: {message}"
        assert result["analysis_type"] is not None
        print(f"✓ HIGH: '{message}' → {result['confidence']:.2f}")

    for message in medium_conf_messages:
        result = router.route_intent(message)
        assert 0.5 <= result["confidence"] < 0.8, f"Should be medium confidence: {message}"
        assert result["analysis_type"] is not None
        print(f"✓ MEDIUM: '{message}' → {result['confidence']:.2f}")

    for message in low_conf_messages:
        result = router.route_intent(message)
        assert result["confidence"] < 0.5, f"Should be low confidence: {message}"
        assert result["analysis_type"] is None
        print(f"✓ LOW: '{message}' → {result['confidence']:.2f}")


def test_case_insensitive():
    """Test that matching is case insensitive"""
    router = DeterministicRouter()

    test_cases = [
        "SHOW TRENDS",
        "Show Trends",
        "show trends",
        "ShOw TrEnDs",
    ]

    for message in test_cases:
        result = router.route_intent(message)
        assert result["analysis_type"] == "trend"
        assert result["confidence"] >= 0.8
        print(f"✓ '{message}' → trend (case insensitive)")


def test_empty_message():
    """Test handling of empty messages"""
    router = DeterministicRouter()

    result = router.route_intent("")
    assert result["analysis_type"] is None
    assert result["confidence"] == 0.0
    print("✓ Empty message → None (confidence: 0.0)")

    result = router.route_intent(None)
    assert result["analysis_type"] is None
    assert result["confidence"] == 0.0
    print("✓ None message → None (confidence: 0.0)")


def test_realistic_user_queries():
    """Test realistic user queries"""
    router = DeterministicRouter()

    test_cases = [
        ("What are the sales trends this month?", "trend", 0.8),
        ("Show me the top 10 selling products", "top_categories", 0.8),
        ("Are there any outliers in the revenue data?", "outliers", 0.8),
        ("How many total records do we have?", "row_count", 0.8),
        ("Check if there are any missing values", "data_quality", 0.8),
        ("I want to see monthly trends", "trend", 0.8),
        ("What's the breakdown by region?", "top_categories", 0.8),
        ("Find unusual transactions", "outliers", 0.8),
    ]

    for message, expected_type, min_confidence in test_cases:
        result = router.route_intent(message)
        assert result["analysis_type"] == expected_type, f"Failed for: {message}"
        assert result["confidence"] >= min_confidence, f"Low confidence for: {message}"
        print(f"✓ '{message}' → {expected_type} (confidence: {result['confidence']:.2f})")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Testing Deterministic Router (HR-3)")
    print("="*80 + "\n")

    print("Testing TREND detection...")
    test_trend_high_confidence()
    print()

    print("Testing TOP_CATEGORIES detection...")
    test_top_categories_high_confidence()
    print()

    print("Testing OUTLIERS detection...")
    test_outliers_high_confidence()
    print()

    print("Testing ROW_COUNT detection...")
    test_row_count_high_confidence()
    print()

    print("Testing DATA_QUALITY detection...")
    test_data_quality_high_confidence()
    print()

    print("Testing MEDIUM confidence...")
    test_medium_confidence()
    print()

    print("Testing LOW confidence...")
    test_low_confidence()
    print()

    print("Testing TIME_PERIOD extraction...")
    test_time_period_extraction()
    print()

    print("Testing TOP_N extraction...")
    test_top_n_extraction()
    print()

    print("Testing CONFIDENCE levels...")
    test_confidence_levels()
    print()

    print("Testing CASE insensitivity...")
    test_case_insensitive()
    print()

    print("Testing EMPTY messages...")
    test_empty_message()
    print()

    print("Testing REALISTIC queries...")
    test_realistic_user_queries()
    print()

    print("="*80)
    print("All tests passed! ✓")
    print("="*80)
    print("\nSummary:")
    print("  ✓ Trend detection with high confidence")
    print("  ✓ Top categories detection with high confidence")
    print("  ✓ Outliers detection with high confidence")
    print("  ✓ Row count detection with high confidence")
    print("  ✓ Data quality detection with high confidence")
    print("  ✓ Medium confidence for weak keywords")
    print("  ✓ Low confidence returns None")
    print("  ✓ Time period extraction")
    print("  ✓ Top N extraction")
    print("  ✓ Confidence levels in correct ranges")
    print("  ✓ Case insensitive matching")
    print("  ✓ Empty message handling")
    print("  ✓ Realistic user queries")
