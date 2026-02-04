"""
Test Safe Mode SQL validation.

This test verifies that Safe Mode SQL enforcement works correctly:
1. Blocks raw row queries (SELECT * FROM data)
2. Allows aggregate queries (COUNT, SUM, AVG, MIN, MAX)
3. Allows GROUP BY queries
4. Safe Mode OFF allows all valid queries
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.sql_validator import sql_validator


def test_safe_mode_blocks_raw_queries():
    """Test that Safe Mode blocks queries that select raw rows without aggregation"""
    print("\n=== Test 1: Safe Mode BLOCKS raw row queries ===")

    blocked_queries = [
        {
            "name": "select_all",
            "sql": "SELECT * FROM data LIMIT 10"
        },
        {
            "name": "select_columns",
            "sql": "SELECT name, email, age FROM data LIMIT 100"
        },
        {
            "name": "select_with_where",
            "sql": "SELECT order_id, customer_name, amount FROM data WHERE status = 'active' LIMIT 50"
        }
    ]

    for query in blocked_queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=True)
        print(f"\nQuery: {query['sql']}")
        print(f"  Valid: {valid}")
        print(f"  Error: {error}")

        assert not valid, f"FAIL: Query should be blocked in Safe Mode: {query['sql']}"
        assert "Safe Mode is ON" in error, f"FAIL: Error message should mention Safe Mode"
        print(f"  ✓ Correctly blocked")

    print("\n✓ PASS: All raw row queries correctly blocked in Safe Mode")


def test_safe_mode_allows_aggregate_queries():
    """Test that Safe Mode allows queries with aggregate functions"""
    print("\n=== Test 2: Safe Mode ALLOWS aggregate queries ===")

    allowed_queries = [
        {
            "name": "count_all",
            "sql": "SELECT COUNT(*) FROM data LIMIT 1"
        },
        {
            "name": "sum_revenue",
            "sql": "SELECT SUM(revenue) FROM data LIMIT 1"
        },
        {
            "name": "avg_age",
            "sql": "SELECT AVG(age) FROM data LIMIT 1"
        },
        {
            "name": "min_max",
            "sql": "SELECT MIN(price), MAX(price) FROM data LIMIT 1"
        },
        {
            "name": "multiple_aggregates",
            "sql": "SELECT COUNT(*), SUM(revenue), AVG(age) FROM data LIMIT 1"
        }
    ]

    for query in allowed_queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=True)
        print(f"\nQuery: {query['sql']}")
        print(f"  Valid: {valid}")
        if error:
            print(f"  Error: {error}")

        assert valid, f"FAIL: Aggregate query should be allowed in Safe Mode: {query['sql']} - Error: {error}"
        print(f"  ✓ Correctly allowed")

    print("\n✓ PASS: All aggregate queries correctly allowed in Safe Mode")


def test_safe_mode_allows_group_by_queries():
    """Test that Safe Mode allows queries with GROUP BY"""
    print("\n=== Test 3: Safe Mode ALLOWS GROUP BY queries ===")

    allowed_queries = [
        {
            "name": "group_by_status",
            "sql": "SELECT status, COUNT(*) FROM data GROUP BY status LIMIT 100"
        },
        {
            "name": "group_by_category",
            "sql": "SELECT category, SUM(revenue) FROM data GROUP BY category LIMIT 50"
        },
        {
            "name": "group_by_multiple",
            "sql": "SELECT region, product, COUNT(*), AVG(price) FROM data GROUP BY region, product LIMIT 200"
        },
        {
            "name": "group_by_having",
            "sql": "SELECT status, COUNT(*) as cnt FROM data GROUP BY status HAVING COUNT(*) > 10 LIMIT 100"
        }
    ]

    for query in allowed_queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=True)
        print(f"\nQuery: {query['sql']}")
        print(f"  Valid: {valid}")
        if error:
            print(f"  Error: {error}")

        assert valid, f"FAIL: GROUP BY query should be allowed in Safe Mode: {query['sql']} - Error: {error}"
        print(f"  ✓ Correctly allowed")

    print("\n✓ PASS: All GROUP BY queries correctly allowed in Safe Mode")


def test_safe_mode_off_allows_all():
    """Test that Safe Mode OFF allows all valid queries"""
    print("\n=== Test 4: Safe Mode OFF allows all valid queries ===")

    queries = [
        {
            "name": "select_all",
            "sql": "SELECT * FROM data LIMIT 10"
        },
        {
            "name": "aggregate",
            "sql": "SELECT COUNT(*) FROM data LIMIT 1"
        },
        {
            "name": "group_by",
            "sql": "SELECT status, COUNT(*) FROM data GROUP BY status LIMIT 100"
        }
    ]

    for query in queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=False)
        print(f"\nQuery: {query['sql']}")
        print(f"  Valid: {valid}")
        if error:
            print(f"  Error: {error}")

        assert valid, f"FAIL: Query should be allowed when Safe Mode is OFF: {query['sql']} - Error: {error}"
        print(f"  ✓ Correctly allowed")

    print("\n✓ PASS: All queries correctly allowed when Safe Mode is OFF")


def test_safe_mode_still_blocks_dangerous_queries():
    """Test that Safe Mode still blocks dangerous operations"""
    print("\n=== Test 5: Safe Mode still blocks dangerous operations ===")

    dangerous_queries = [
        {
            "name": "delete",
            "sql": "DELETE FROM data WHERE id = 1"
        },
        {
            "name": "drop",
            "sql": "DROP TABLE data"
        },
        {
            "name": "update",
            "sql": "UPDATE data SET status = 'active' LIMIT 100"
        }
    ]

    for query in dangerous_queries:
        # Test with Safe Mode ON
        valid, error = sql_validator.validate_queries([query], safe_mode=True)
        print(f"\nQuery: {query['sql']}")
        print(f"  Safe Mode ON - Valid: {valid}, Error: {error}")
        assert not valid, f"FAIL: Dangerous query should be blocked in Safe Mode"

        # Test with Safe Mode OFF
        valid, error = sql_validator.validate_queries([query], safe_mode=False)
        print(f"  Safe Mode OFF - Valid: {valid}, Error: {error}")
        assert not valid, f"FAIL: Dangerous query should be blocked even when Safe Mode is OFF"

        print(f"  ✓ Correctly blocked in both modes")

    print("\n✓ PASS: Dangerous operations blocked in both Safe Mode ON and OFF")


def test_case_insensitive_aggregate_detection():
    """Test that aggregate detection is case-insensitive"""
    print("\n=== Test 6: Case-insensitive aggregate detection ===")

    queries = [
        {
            "name": "lowercase",
            "sql": "select count(*) from data limit 1"
        },
        {
            "name": "uppercase",
            "sql": "SELECT COUNT(*) FROM DATA LIMIT 1"
        },
        {
            "name": "mixed",
            "sql": "SeLeCt CoUnT(*) FrOm DaTa LiMiT 1"
        }
    ]

    for query in queries:
        valid, error = sql_validator.validate_queries([query], safe_mode=True)
        print(f"\nQuery: {query['sql']}")
        print(f"  Valid: {valid}")

        assert valid, f"FAIL: Aggregate query should be detected regardless of case: {query['sql']}"
        print(f"  ✓ Correctly allowed")

    print("\n✓ PASS: Aggregate detection is case-insensitive")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SAFE MODE SQL VALIDATION TEST SUITE")
    print("="*70)

    try:
        test_safe_mode_blocks_raw_queries()
        test_safe_mode_allows_aggregate_queries()
        test_safe_mode_allows_group_by_queries()
        test_safe_mode_off_allows_all()
        test_safe_mode_still_blocks_dangerous_queries()
        test_case_insensitive_aggregate_detection()

        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("\nSafe Mode SQL validation is working correctly:")
        print("  • Raw row queries blocked when Safe Mode ON")
        print("  • Aggregate queries (COUNT, SUM, AVG, MIN, MAX) allowed")
        print("  • GROUP BY queries allowed")
        print("  • All queries allowed when Safe Mode OFF")
        print("  • Dangerous operations blocked in both modes")
        print("  • Case-insensitive aggregate detection")
        print()

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
