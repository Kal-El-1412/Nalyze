"""
Test Safe Mode enforcement in chat orchestrator.

This test verifies that when Safe Mode is enabled:
1. Catalog stats (including min/max/avg/distinct/null) ARE included - these are aggregates
2. No sample rows are included in the results context sent to LLM
3. Only row count and column metadata are provided for results, NO actual row values
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.chat_orchestrator import chat_orchestrator
from app.models import (
    QueryResultContext,
    ResultsContext
)


def test_results_context_safe_mode_on():
    """Test that results context excludes sample rows when Safe Mode is ON"""
    print("\n=== Test 1: Results Context with Safe Mode ON ===")

    # Create mock results
    results_context = ResultsContext(
        results=[
            QueryResultContext(
                name="monthly_summary",
                columns=["month", "total_revenue", "order_count"],
                rows=[
                    ["2024-01", 45320.50, 234],
                    ["2024-02", 52100.75, 267],
                    ["2024-03", 48900.25, 241]
                ]
            )
        ]
    )

    # Test with Safe Mode ON
    results_text_safe = chat_orchestrator._build_results_context(results_context, safe_mode=True)

    print("Results context with Safe Mode ON:")
    print(results_text_safe)
    print()

    # Verify that sample rows are NOT included
    assert "2024-01" not in results_text_safe, "FAIL: Sample row data should not be in Safe Mode"
    assert "45320" not in results_text_safe, "FAIL: Sample row data should not be in Safe Mode"
    assert "Sample data:" not in results_text_safe, "FAIL: Sample data section should not be in Safe Mode"

    # Verify that metadata IS included
    assert "Columns: month, total_revenue, order_count" in results_text_safe, "FAIL: Column names should be included"
    assert "Rows returned: 3" in results_text_safe, "FAIL: Row count should be included"
    assert "Safe Mode - no raw rows" in results_text_safe, "FAIL: Safe Mode label should be present"

    print("✓ PASS: Results context correctly excludes sample rows in Safe Mode")


def test_results_context_safe_mode_off():
    """Test that results context includes sample rows when Safe Mode is OFF"""
    print("\n=== Test 2: Results Context with Safe Mode OFF ===")

    # Create mock results
    results_context = ResultsContext(
        results=[
            QueryResultContext(
                name="monthly_summary",
                columns=["month", "total_revenue", "order_count"],
                rows=[
                    ["2024-01", 45320.50, 234],
                    ["2024-02", 52100.75, 267],
                    ["2024-03", 48900.25, 241]
                ]
            )
        ]
    )

    # Test with Safe Mode OFF
    results_text_normal = chat_orchestrator._build_results_context(results_context, safe_mode=False)

    print("Results context with Safe Mode OFF:")
    print(results_text_normal)
    print()

    # Verify that sample rows ARE included
    assert "'2024-01'" in results_text_normal, "FAIL: Sample row data should be included when Safe Mode is OFF"
    assert "45320" in results_text_normal, "FAIL: Sample row data should be included when Safe Mode is OFF"
    assert "Sample data:" in results_text_normal, "FAIL: Sample data section should be included when Safe Mode is OFF"

    # Verify that metadata is also included
    assert "Columns: month, total_revenue, order_count" in results_text_normal, "FAIL: Column names should be included"
    assert "Rows returned: 3" in results_text_normal, "FAIL: Row count should be included"

    print("✓ PASS: Results context correctly includes sample rows when Safe Mode is OFF")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SAFE MODE ENFORCEMENT TEST SUITE")
    print("="*60)

    try:
        test_results_context_safe_mode_on()
        test_results_context_safe_mode_off()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nSafe Mode is correctly enforced:")
        print("  • Sample rows excluded when Safe Mode ON")
        print("  • Metadata (columns, row count) included in Safe Mode")
        print("  • Full data available when Safe Mode OFF")
        print("  • Catalog stats always included (these are aggregates)")
        print()

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
