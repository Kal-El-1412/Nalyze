"""
Test AE-3: Results-Driven Summarizer

Verifies that summaries are generated from actual query results,
not from hardcoded templates. Tests all analysis types plus generic fallback.

Run with: python3 test_ae3_results_summarizer.py
"""

import sys
from app.summarizer import results_summarizer


def test_row_count_summary():
    """Test row_count summary includes numeric count"""
    print("\n" + "=" * 60)
    print("Test 1: Row Count Summary")
    print("=" * 60)

    tables = [
        {
            "name": "row_count",
            "columns": ["row_count"],
            "rows": [[12345]],
            "rowCount": 1
        }
    ]

    audit = {"executedQueries": [{"name": "row_count", "sql": "SELECT COUNT(*) FROM data", "rowCount": 1}]}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary = results_summarizer.summarize_results("row_count", tables, audit, flags)

    # Verify it contains the actual number
    if "12,345" in summary or "12345" in summary:
        print(f"✅ Summary contains actual row count")
        print(f"   Summary: {summary}")
        return True
    else:
        print(f"❌ Summary does not contain actual row count")
        print(f"   Summary: {summary}")
        return False


def test_row_count_different_values():
    """Test that different row counts produce different summaries"""
    print("\n" + "=" * 60)
    print("Test 2: Different Row Counts Produce Different Summaries")
    print("=" * 60)

    tables1 = [{"name": "row_count", "columns": ["row_count"], "rows": [[100]], "rowCount": 1}]
    tables2 = [{"name": "row_count", "columns": ["row_count"], "rows": [[5000]], "rowCount": 1}]

    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary1 = results_summarizer.summarize_results("row_count", tables1, audit, flags)
    summary2 = results_summarizer.summarize_results("row_count", tables2, audit, flags)

    if summary1 != summary2 and ("100" in summary1 or "100 rows" in summary1) and ("5,000" in summary2 or "5000" in summary2):
        print(f"✅ Different values produce different summaries")
        print(f"   Summary 1 (100 rows): {summary1}")
        print(f"   Summary 2 (5000 rows): {summary2}")
        return True
    else:
        print(f"❌ Summaries are not different based on data")
        print(f"   Summary 1: {summary1}")
        print(f"   Summary 2: {summary2}")
        return False


def test_trend_summary():
    """Test trend summary references periods and totals"""
    print("\n" + "=" * 60)
    print("Test 3: Trend Summary with Real Data")
    print("=" * 60)

    tables = [
        {
            "name": "monthly_trend",
            "columns": ["month", "count", "total_revenue", "avg_revenue"],
            "rows": [
                ["2024-01-01", 100, 50000.00, 500.00],
                ["2024-02-01", 120, 60000.00, 500.00],
                ["2024-03-01", 150, 75000.00, 500.00]
            ],
            "rowCount": 3
        }
    ]

    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary = results_summarizer.summarize_results("trend", tables, audit, flags)

    # Should mention period count and latest period data
    checks = [
        ("3" in summary or "three" in summary.lower(), "period count"),
        ("2024-03" in summary or "150" in summary, "latest period data"),
        ("25" in summary and ("%" in summary or "increase" in summary.lower() or "decrease" in summary.lower()), "period-over-period change")
    ]

    all_passed = True
    for check, description in checks:
        if check:
            print(f"✅ Contains {description}")
        else:
            print(f"❌ Missing {description}")
            all_passed = False

    print(f"   Summary: {summary}")
    return all_passed


def test_top_categories_summary():
    """Test top categories summary shows real counts and percentages"""
    print("\n" + "=" * 60)
    print("Test 4: Top Categories Summary")
    print("=" * 60)

    tables = [
        {
            "name": "top_categories",
            "columns": ["category", "count"],
            "rows": [
                ["Electronics", 500],
                ["Clothing", 300],
                ["Books", 200],
                ["Home", 100]
            ],
            "rowCount": 4
        }
    ]

    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary = results_summarizer.summarize_results("top_categories", tables, audit, flags)

    # Should mention top categories with counts
    checks = [
        ("Electronics" in summary, "top category name"),
        ("500" in summary, "top category count"),
        ("%" in summary, "percentage calculation"),
        ("4" in summary or "four" in summary.lower(), "category count")
    ]

    all_passed = True
    for check, description in checks:
        if check:
            print(f"✅ Contains {description}")
        else:
            print(f"❌ Missing {description}")
            all_passed = False

    print(f"   Summary: {summary}")
    return all_passed


def test_outliers_summary():
    """Test outliers summary shows detection counts"""
    print("\n" + "=" * 60)
    print("Test 5: Outliers Summary")
    print("=" * 60)

    # Test safe mode (aggregated)
    tables_safe = [
        {
            "name": "outlier_summary",
            "columns": ["column_name", "outlier_count", "mean_value", "stddev_value"],
            "rows": [
                ["revenue", 15, 1000.0, 200.0],
                ["age", 8, 35.0, 10.0],
                ["score", 0, 75.0, 5.0]
            ],
            "rowCount": 3
        }
    ]

    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": True, "privacyMode": True}

    summary_safe = results_summarizer.summarize_results("outliers", tables_safe, audit, flags)

    # Should mention total outliers and columns
    checks_safe = [
        ("23" in summary_safe, "total outlier count (15+8)"),
        ("2" in summary_safe, "columns with outliers"),
        ("standard deviation" in summary_safe.lower(), "detection method")
    ]

    all_passed = True
    for check, description in checks_safe:
        if check:
            print(f"✅ Safe mode contains {description}")
        else:
            print(f"❌ Safe mode missing {description}")
            all_passed = False

    print(f"   Safe Mode Summary: {summary_safe}")

    # Test regular mode (individual rows)
    tables_regular = [
        {
            "name": "outliers_detected",
            "columns": ["column_name", "value", "mean_value", "stddev_value", "z_score"],
            "rows": [
                ["revenue", 5000, 1000, 200, 20.0],
                ["revenue", 4800, 1000, 200, 19.0],
                ["age", 90, 35, 10, 5.5]
            ],
            "rowCount": 3
        }
    ]

    flags_regular = {"aiAssist": False, "safeMode": False, "privacyMode": True}
    summary_regular = results_summarizer.summarize_results("outliers", tables_regular, audit, flags_regular)

    checks_regular = [
        ("3" in summary_regular, "outlier value count"),
        ("2" in summary_regular, "unique columns"),
        ("z-score" in summary_regular.lower() or "20" in summary_regular, "z-score info")
    ]

    for check, description in checks_regular:
        if check:
            print(f"✅ Regular mode contains {description}")
        else:
            print(f"❌ Regular mode missing {description}")
            all_passed = False

    print(f"   Regular Mode Summary: {summary_regular}")
    return all_passed


def test_data_quality_summary():
    """Test data quality summary shows real counts"""
    print("\n" + "=" * 60)
    print("Test 6: Data Quality Summary")
    print("=" * 60)

    tables = [
        {
            "name": "null_counts",
            "columns": ["total_rows", "name_nulls", "email_nulls", "age_nulls"],
            "rows": [[1000, 5, 0, 12]],
            "rowCount": 1
        },
        {
            "name": "duplicate_check",
            "columns": ["total_rows", "unique_rows"],
            "rows": [[1000, 995]],
            "rowCount": 1
        }
    ]

    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary = results_summarizer.summarize_results("data_quality", tables, audit, flags)

    # Should mention null counts and duplicates
    checks = [
        ("1,000" in summary or "1000" in summary, "total rows"),
        ("2" in summary or "17" in summary, "null columns or total nulls"),
        ("5" in summary or "duplicate" in summary.lower(), "duplicates")
    ]

    all_passed = True
    for check, description in checks:
        if check:
            print(f"✅ Contains {description}")
        else:
            print(f"❌ Missing {description}")
            all_passed = False

    print(f"   Summary: {summary}")
    return all_passed


def test_generic_fallback():
    """Test generic fallback for unknown analysis types"""
    print("\n" + "=" * 60)
    print("Test 7: Generic Fallback for Unknown Types")
    print("=" * 60)

    tables = [
        {
            "name": "custom_query_result",
            "columns": ["product", "sales", "profit"],
            "rows": [
                ["Widget A", 1000, 250.50],
                ["Widget B", 800, 200.00]
            ],
            "rowCount": 2
        }
    ]

    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary = results_summarizer.summarize_results("unknown_type", tables, audit, flags)

    # Should describe table structure without interpretation
    checks = [
        ("custom_query_result" in summary or "Analysis Results" in summary, "table name"),
        ("2" in summary or "two" in summary.lower(), "row count"),
        ("product" in summary or "sales" in summary or "profit" in summary, "column names"),
        ("Dataset contains" not in summary, "no canned phrases"),
        ("Statistical analysis" not in summary, "no canned phrases"),
        ("normal distribution" not in summary, "no canned phrases")
    ]

    all_passed = True
    for check, description in checks:
        if check:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_passed = False

    print(f"   Summary: {summary}")
    return all_passed


def test_no_canned_phrases():
    """Test that no canned phrases appear in summaries"""
    print("\n" + "=" * 60)
    print("Test 8: No Canned Phrases")
    print("=" * 60)

    # Test all analysis types for canned phrases
    canned_phrases = [
        "Dataset contains diverse data patterns",
        "Statistical analysis shows normal distribution",
        "No significant anomalies",
        "Analysis Complete",
        "diverse data patterns",
        "normal distribution"
    ]

    tables = [
        {"name": "test", "columns": ["col1"], "rows": [[100]], "rowCount": 1}
    ]

    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    analysis_types = ["row_count", "trend", "top_categories", "outliers", "data_quality", "unknown"]

    all_passed = True
    for analysis_type in analysis_types:
        summary = results_summarizer.summarize_results(analysis_type, tables, audit, flags)

        for phrase in canned_phrases:
            if phrase.lower() in summary.lower():
                print(f"❌ Found canned phrase '{phrase}' in {analysis_type} summary")
                all_passed = False

    if all_passed:
        print(f"✅ No canned phrases found in any summaries")

    return all_passed


def test_empty_results_error():
    """Test guardrail against empty results"""
    print("\n" + "=" * 60)
    print("Test 9: Empty Results Guardrail")
    print("=" * 60)

    # Empty tables
    tables = []
    audit = {"executedQueries": []}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary = results_summarizer.summarize_results("row_count", tables, audit, flags)

    # Should return error message, not success
    if "Error" in summary or "No results" in summary:
        print(f"✅ Returns error for empty results")
        print(f"   Error message: {summary}")
        return True
    else:
        print(f"❌ Does not return error for empty results")
        print(f"   Summary: {summary}")
        return False


def test_ai_assist_off_no_fake_complete():
    """Test that AI Assist OFF doesn't return fake 'Analysis Complete'"""
    print("\n" + "=" * 60)
    print("Test 10: AI Assist OFF - No Fake Complete")
    print("=" * 60)

    # Simulate unknown prompt with AI Assist OFF
    tables = [
        {"name": "result", "columns": ["value"], "rows": [[42]], "rowCount": 1}
    ]

    audit = {"executedQueries": [{"name": "query", "sql": "SELECT 42", "rowCount": 1}]}
    flags = {"aiAssist": False, "safeMode": False, "privacyMode": True}

    summary = results_summarizer.summarize_results("unknown_type", tables, audit, flags)

    # Should describe actual results, not say "Analysis Complete"
    if "Analysis Complete" not in summary and ("42" in summary or "value" in summary or "result" in summary):
        print(f"✅ No fake 'Analysis Complete' message")
        print(f"   Summary describes actual data: {summary}")
        return True
    else:
        print(f"❌ Contains fake completion or doesn't describe data")
        print(f"   Summary: {summary}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AE-3: Results-Driven Summarizer - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Row count summary
    results.append(("row_count includes numeric count", test_row_count_summary()))

    # Test 2: Different values produce different summaries
    results.append(("different values produce different summaries", test_row_count_different_values()))

    # Test 3: Trend summary
    results.append(("trend references periods and totals", test_trend_summary()))

    # Test 4: Top categories summary
    results.append(("top_categories shows counts and percentages", test_top_categories_summary()))

    # Test 5: Outliers summary
    results.append(("outliers shows detection counts", test_outliers_summary()))

    # Test 6: Data quality summary
    results.append(("data_quality shows real counts", test_data_quality_summary()))

    # Test 7: Generic fallback
    results.append(("generic fallback for unknown types", test_generic_fallback()))

    # Test 8: No canned phrases
    results.append(("no canned phrases", test_no_canned_phrases()))

    # Test 9: Empty results error
    results.append(("empty results return error", test_empty_results_error()))

    # Test 10: AI Assist OFF no fake complete
    results.append(("AI Assist OFF no fake complete", test_ai_assist_off_no_fake_complete()))

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
        print("✅ No canned summary templates")
        print("✅ summarize_results() implemented with analysis-type plugins")
        print("✅ row_count summary includes numeric count")
        print("✅ trend summary references periods and latest totals")
        print("✅ Different prompts produce different summaries when tables differ")
        print("✅ Unknown prompt with AI Assist OFF returns results-based summary")
        print("✅ Guardrails prevent fake 'Analysis Complete' without results")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
