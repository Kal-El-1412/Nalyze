"""
Test FIX-4: Verify no "SELECT * LIMIT" queries are used as analysis plans

This test ensures that:
1. row_count analysis uses SELECT COUNT(*) AS row_count FROM data
2. All fallback cases use proper aggregation queries, not SELECT * LIMIT
3. No "discover_columns" queries remain in the analysis plans
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.chat_orchestrator import chat_orchestrator
from app.models import ChatOrchestratorRequest


def test_row_count_query():
    """Test that row_count analysis uses COUNT(*), not SELECT * LIMIT"""
    print("\nTest 1: Row Count Uses COUNT(*)")
    print("-" * 50)

    # Simulate a row count request with state already set
    from app.state import state_manager
    conv_id = "test_conv_row_count"

    # Set the analysis_type in state so it proceeds directly to SQL generation
    state_manager.update_context(conv_id, {
        "analysis_type": "row_count",
        "time_period": "all_time"
    })

    # Mock catalog with some columns
    class MockCatalog:
        def __init__(self):
            self.rowCount = 1000
            self.columns = [
                type('obj', (object,), {'name': 'id', 'type': 'INTEGER'}),
                type('obj', (object,), {'name': 'name', 'type': 'VARCHAR'}),
                type('obj', (object,), {'name': 'value', 'type': 'DOUBLE'}),
            ]
            self.detectedDateColumns = []
            self.detectedNumericColumns = ['value']
            self.basicStats = {}

    catalog = MockCatalog()

    # Create request
    request = ChatOrchestratorRequest(
        datasetId="test_dataset",
        conversationId=conv_id,
        message="How many rows?",
        aiAssist=False,
        privacyMode=True,
        safeMode=False
    )

    # Get SQL plan
    import asyncio
    response = asyncio.run(chat_orchestrator._generate_sql_plan(request, catalog, {
        "analysis_type": "row_count",
        "time_period": "all_time"
    }))

    # Verify
    assert len(response.queries) == 1, f"Expected 1 query, got {len(response.queries)}"
    query = response.queries[0]

    print(f"Query name: {query.name}")
    print(f"Query SQL: {query.sql}")

    # Check SQL
    sql_upper = query.sql.upper()
    assert "COUNT(*)" in sql_upper, "Query must use COUNT(*)"
    assert query.sql.strip() == "SELECT COUNT(*) as row_count FROM data", \
        f"Expected exact COUNT(*) query, got: {query.sql}"
    assert "SELECT *" not in sql_upper or "COUNT(*)" in sql_upper, \
        "Query must not use SELECT * without aggregation"
    assert "LIMIT 100" not in query.sql, "Query must not use LIMIT 100"
    assert "LIMIT 10" not in query.sql, "Query must not use LIMIT 10"

    print("✅ PASS: row_count uses SELECT COUNT(*) as row_count FROM data")
    print(f"   NOT SELECT * LIMIT 100")
    print(f"   NOT SELECT * LIMIT 10")
    return True


def test_no_discover_columns_fallback():
    """Test that all analysis types use proper queries, not discover_columns"""
    print("\nTest 2: No discover_columns Fallback Queries")
    print("-" * 50)

    analysis_types = ["top_categories", "trend", "outliers", "data_quality"]

    from app.state import state_manager
    import asyncio

    # Test with no catalog (worst case - used to trigger discover_columns)
    for analysis_type in analysis_types:
        conv_id = f"test_conv_{analysis_type}"

        state_manager.update_context(conv_id, {
            "analysis_type": analysis_type,
            "time_period": "all_time"
        })

        request = ChatOrchestratorRequest(
            datasetId="test_dataset",
            conversationId=conv_id,
            message=f"Test {analysis_type}",
            aiAssist=False,
            privacyMode=True,
            safeMode=False
        )

        # Test with no catalog (None) - this used to trigger discover_columns
        response = asyncio.run(chat_orchestrator._generate_sql_plan(request, None, {
            "analysis_type": analysis_type,
            "time_period": "all_time"
        }))

        # Verify no discover_columns queries
        for query in response.queries:
            assert query.name != "discover_columns", \
                f"{analysis_type} should not use discover_columns query"
            assert "SELECT * FROM data LIMIT 1" not in query.sql, \
                f"{analysis_type} should not use SELECT * LIMIT 1"
            assert "SELECT * FROM data LIMIT 100" not in query.sql, \
                f"{analysis_type} should not use SELECT * LIMIT 100"

            # Should use aggregation instead
            sql_upper = query.sql.upper()
            has_aggregation = any(agg in sql_upper for agg in [
                "COUNT(*)", "SUM(", "AVG(", "MIN(", "MAX(", "STDDEV(", "GROUP BY"
            ])
            assert has_aggregation, \
                f"{analysis_type} query should use aggregation: {query.sql}"

            print(f"✅ {analysis_type}: {query.name}")
            print(f"   SQL: {query.sql[:80]}...")

    print("\n✅ PASS: All analysis types use proper aggregation queries")
    print("   No discover_columns fallbacks")
    print("   No SELECT * LIMIT in analysis plans")
    return True


def test_all_queries_use_aggregation():
    """Test that all generated queries use aggregation"""
    print("\nTest 3: All Queries Use Aggregation")
    print("-" * 50)

    from app.state import state_manager
    import asyncio

    # Mock catalog with various columns
    class MockCatalog:
        def __init__(self):
            self.rowCount = 1000
            self.columns = [
                type('obj', (object,), {'name': 'id', 'type': 'INTEGER'}),
                type('obj', (object,), {'name': 'category', 'type': 'VARCHAR'}),
                type('obj', (object,), {'name': 'value', 'type': 'DOUBLE'}),
                type('obj', (object,), {'name': 'date', 'type': 'DATE'}),
            ]
            self.detectedDateColumns = ['date']
            self.detectedNumericColumns = ['value']
            self.basicStats = {}
            self.summary = {
                'category': {'count': 1000, 'unique': 10}
            }

    catalog = MockCatalog()

    analysis_types = ["row_count", "top_categories", "trend", "outliers", "data_quality"]

    all_passed = True

    for analysis_type in analysis_types:
        conv_id = f"test_conv_agg_{analysis_type}"

        state_manager.update_context(conv_id, {
            "analysis_type": analysis_type,
            "time_period": "last_30_days"
        })

        request = ChatOrchestratorRequest(
            datasetId="test_dataset",
            conversationId=conv_id,
            message=f"Test {analysis_type}",
            aiAssist=False,
            privacyMode=False,
            safeMode=False
        )

        response = asyncio.run(chat_orchestrator._generate_sql_plan(request, catalog, {
            "analysis_type": analysis_type,
            "time_period": "last_30_days"
        }))

        for query in response.queries:
            sql_upper = query.sql.upper()

            # Check for aggregation functions
            has_aggregation = any(agg in sql_upper for agg in [
                "COUNT(*)", "COUNT(", "SUM(", "AVG(", "MIN(", "MAX(",
                "STDDEV(", "GROUP BY", "COUNT(DISTINCT"
            ])

            if not has_aggregation:
                print(f"❌ {analysis_type}.{query.name} lacks aggregation:")
                print(f"   {query.sql}")
                all_passed = False
            else:
                print(f"✅ {analysis_type}.{query.name} uses aggregation")

    if all_passed:
        print("\n✅ PASS: All queries use aggregation")
    else:
        print("\n❌ FAIL: Some queries lack aggregation")

    return all_passed


def test_audit_shows_correct_sql():
    """Test that audit metadata shows the actual SQL executed, not preview queries"""
    print("\nTest 4: Audit Shows Correct SQL for Row Count")
    print("-" * 50)

    from app.state import state_manager
    import asyncio

    conv_id = "test_conv_audit"

    state_manager.update_context(conv_id, {
        "analysis_type": "row_count",
        "time_period": "all_time"
    })

    class MockCatalog:
        def __init__(self):
            self.rowCount = 1000
            self.columns = []
            self.detectedDateColumns = []
            self.detectedNumericColumns = []
            self.basicStats = {}

    catalog = MockCatalog()

    request = ChatOrchestratorRequest(
        datasetId="test_dataset",
        conversationId=conv_id,
        message="How many rows?",
        aiAssist=False,
        privacyMode=True,
        safeMode=False
    )

    response = asyncio.run(chat_orchestrator._generate_sql_plan(request, catalog, {
        "analysis_type": "row_count",
        "time_period": "all_time"
    }))

    # Check the SQL in the response
    query = response.queries[0]

    # Verify exact SQL
    expected_sql = "SELECT COUNT(*) as row_count FROM data"
    assert query.sql == expected_sql, \
        f"Expected '{expected_sql}', got '{query.sql}'"

    # Verify it's NOT a preview query
    assert "SELECT * FROM data LIMIT" not in query.sql, \
        "Audit should not show SELECT * LIMIT queries"

    print(f"✅ Query name: {query.name}")
    print(f"✅ Query SQL: {query.sql}")
    print(f"✅ PASS: Audit will show correct SQL, not preview query")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("FIX-4: No Preview Queries in Analysis Plans")
    print("=" * 50)

    tests = [
        ("Row Count Uses COUNT(*)", test_row_count_query),
        ("No discover_columns Fallback", test_no_discover_columns_fallback),
        ("All Queries Use Aggregation", test_all_queries_use_aggregation),
        ("Audit Shows Correct SQL", test_audit_shows_correct_sql),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ ALL TESTS PASSED")
        print("\nAcceptance Criteria Met:")
        print("✅ row_count uses SELECT COUNT(*) as row_count FROM data")
        print("✅ No SELECT * LIMIT 100 in any analysis plan")
        print("✅ No discover_columns fallback queries")
        print("✅ All queries use proper aggregation")
        print("✅ Audit tab will show correct SQL, not preview queries")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
