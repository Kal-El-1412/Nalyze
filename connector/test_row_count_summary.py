"""
Test that row count summaries show the actual count dynamically.

Acceptance:
- When analysis_type="row_count", summary shows "This dataset has X rows."
- The count must be extracted from actual query results
- No generic "analysis complete" text
"""
from app.summarizer import results_summarizer


def test_row_count_summary_with_row_count_column():
    """Test row count summary when result has 'row_count' column"""
    tables = [
        {
            "name": "row_count_result",
            "columns": ["row_count"],
            "rows": [[1748]],
            "rowCount": 1
        }
    ]

    audit = {
        "datasetId": "test",
        "analysisType": "row_count",
        "executedQueries": []
    }

    flags = {
        "aiAssist": False,
        "safeMode": False,
        "privacyMode": True
    }

    summary = results_summarizer.summarize_results("row_count", tables, audit, flags)

    print(f"Summary:\n{summary}\n")

    # Must contain the actual count
    assert "1,748" in summary, f"Expected '1,748' in summary, got: {summary}"
    assert "This dataset has" in summary, f"Expected 'This dataset has' in summary, got: {summary}"

    # Must NOT contain generic text
    assert "analysis complete" not in summary.lower(), f"Summary should not have generic text: {summary}"

    print("✅ Row count summary shows actual count (1,748 rows)")


def test_row_count_summary_with_count_column():
    """Test row count summary when result has 'count' or 'COUNT(*)' column"""
    tables = [
        {
            "name": "row_count_result",
            "columns": ["COUNT(*)"],
            "rows": [[523]],
            "rowCount": 1
        }
    ]

    audit = {
        "datasetId": "test",
        "analysisType": "row_count",
        "executedQueries": []
    }

    flags = {
        "aiAssist": False,
        "safeMode": False,
        "privacyMode": True
    }

    summary = results_summarizer.summarize_results("row_count", tables, audit, flags)

    print(f"Summary:\n{summary}\n")

    # Must contain the actual count (first column fallback)
    assert "523" in summary, f"Expected '523' in summary, got: {summary}"
    assert "This dataset has" in summary, f"Expected 'This dataset has' in summary, got: {summary}"

    print("✅ Row count summary shows actual count from first column (523 rows)")


def test_row_count_summary_large_number():
    """Test row count summary formats large numbers with thousands separator"""
    tables = [
        {
            "name": "row_count_result",
            "columns": ["row_count"],
            "rows": [[1234567]],
            "rowCount": 1
        }
    ]

    audit = {
        "datasetId": "test",
        "analysisType": "row_count",
        "executedQueries": []
    }

    flags = {
        "aiAssist": False,
        "safeMode": False,
        "privacyMode": True
    }

    summary = results_summarizer.summarize_results("row_count", tables, audit, flags)

    print(f"Summary:\n{summary}\n")

    # Must format with thousands separator
    assert "1,234,567" in summary, f"Expected formatted number '1,234,567' in summary, got: {summary}"

    print("✅ Row count summary formats large numbers correctly (1,234,567 rows)")


def test_row_count_summary_zero_rows():
    """Test row count summary when dataset is empty"""
    tables = [
        {
            "name": "row_count_result",
            "columns": ["row_count"],
            "rows": [[0]],
            "rowCount": 1
        }
    ]

    audit = {
        "datasetId": "test",
        "analysisType": "row_count",
        "executedQueries": []
    }

    flags = {
        "aiAssist": False,
        "safeMode": False,
        "privacyMode": True
    }

    summary = results_summarizer.summarize_results("row_count", tables, audit, flags)

    print(f"Summary:\n{summary}\n")

    # Must mention empty dataset
    assert "empty" in summary.lower() or "0 rows" in summary.lower(), f"Expected empty/0 rows message, got: {summary}"

    print("✅ Row count summary handles empty dataset (0 rows)")


if __name__ == "__main__":
    test_row_count_summary_with_row_count_column()
    test_row_count_summary_with_count_column()
    test_row_count_summary_large_number()
    test_row_count_summary_zero_rows()
    print("\n✅ All row count summary tests passed!")
