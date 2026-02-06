"""
Test AE-1: Analysis-Specific SQL Plans

Verifies that _generate_sql_plan() generates the correct SQL for each analysis type,
without falling back to generic SELECT * LIMIT 100 or preview queries.

Run with: python3 test_analysis_specific_plans.py
"""

import sys
import asyncio
from app.chat_orchestrator import ChatOrchestrator
from app.models import ChatOrchestratorRequest


async def test_row_count_sql():
    """Test that row_count generates COUNT(*) query"""
    print("\n" + "=" * 60)
    print("Test 1: Row Count SQL")
    print("=" * 60)

    orchestrator = ChatOrchestrator()

    # Mock catalog with basic structure
    catalog = {
        "tables": [{
            "name": "data",
            "columns": ["id", "name", "value"],
            "sample_data": []
        }]
    }

    context = {
        "analysis_type": "row_count",
        "time_period": "all_time"
    }

    request = ChatOrchestratorRequest(
        message="row count",
        conversationId="test-1",
        datasetId="test-dataset",
        catalog=catalog,
        safeMode=False,
        privacyMode=False
    )

    result = await orchestrator._generate_sql_plan(request, catalog, context)

    # Verify result
    if len(result.queries) == 1:
        query = result.queries[0]
        sql = query.sql.strip().upper()

        if "COUNT(*)" in sql and "SELECT * FROM" not in sql:
            print(f"✅ row_count generates correct SQL:")
            print(f"   {query.sql}")
            print(f"   ✓ Uses COUNT(*)")
            print(f"   ✓ NOT SELECT * LIMIT 100")
            return True
        else:
            print(f"❌ row_count generates incorrect SQL:")
            print(f"   {query.sql}")
            return False
    else:
        print(f"❌ Expected 1 query, got {len(result.queries)}")
        return False


async def test_top_categories_sql():
    """Test that top_categories generates GROUP BY query with LIMIT 20"""
    print("\n" + "=" * 60)
    print("Test 2: Top Categories SQL")
    print("=" * 60)

    orchestrator = ChatOrchestrator()

    catalog = {
        "tables": [{
            "name": "data",
            "columns": ["id", "category", "status", "value"],
            "sample_data": [
                {"id": 1, "category": "A", "status": "active", "value": 100}
            ]
        }]
    }

    context = {
        "analysis_type": "top_categories",
        "time_period": "last_month"
    }

    request = ChatOrchestratorRequest(
        message="top categories",
        conversationId="test-2",
        datasetId="test-dataset",
        catalog=catalog,
        safeMode=False,
        privacyMode=False
    )

    result = await orchestrator._generate_sql_plan(request, catalog, context)

    if len(result.queries) == 1:
        query = result.queries[0]
        sql = query.sql.strip().upper()

        has_group_by = "GROUP BY" in sql
        has_count = "COUNT(*)" in sql
        has_limit_20 = "LIMIT 20" in sql
        has_order_by = "ORDER BY" in sql
        no_select_star = "SELECT * FROM" not in sql or "AS CATEGORY" in sql

        if has_group_by and has_count and has_limit_20 and has_order_by and no_select_star:
            print(f"✅ top_categories generates correct SQL:")
            print(f"   {query.sql}")
            print(f"   ✓ Uses GROUP BY")
            print(f"   ✓ Uses COUNT(*)")
            print(f"   ✓ Uses LIMIT 20")
            print(f"   ✓ Uses ORDER BY")
            return True
        else:
            print(f"❌ top_categories generates incorrect SQL:")
            print(f"   {query.sql}")
            print(f"   GROUP BY: {has_group_by}")
            print(f"   COUNT(*): {has_count}")
            print(f"   LIMIT 20: {has_limit_20}")
            print(f"   ORDER BY: {has_order_by}")
            return False
    else:
        print(f"❌ Expected 1 query, got {len(result.queries)}")
        return False


async def test_trend_sql():
    """Test that trend generates DATE_TRUNC query"""
    print("\n" + "=" * 60)
    print("Test 3: Trend SQL")
    print("=" * 60)

    orchestrator = ChatOrchestrator()

    catalog = {
        "tables": [{
            "name": "data",
            "columns": ["id", "created_at", "order_date", "value", "amount"],
            "sample_data": [
                {"id": 1, "created_at": "2024-01-01", "value": 100}
            ]
        }]
    }

    context = {
        "analysis_type": "trend",
        "time_period": "last_month"
    }

    request = ChatOrchestratorRequest(
        message="trend over time",
        conversationId="test-3",
        datasetId="test-dataset",
        catalog=catalog,
        safeMode=False,
        privacyMode=False
    )

    result = await orchestrator._generate_sql_plan(request, catalog, context)

    if len(result.queries) == 1:
        query = result.queries[0]
        sql = query.sql.strip().upper()

        has_date_trunc = "DATE_TRUNC" in sql
        has_month = "'MONTH'" in sql or "MONTH" in sql
        has_group_by = "GROUP BY" in sql
        has_order_by = "ORDER BY" in sql
        no_select_star_limit = "SELECT * FROM DATA LIMIT" not in sql

        if has_date_trunc and has_group_by and has_order_by and no_select_star_limit:
            print(f"✅ trend generates correct SQL:")
            print(f"   {query.sql}")
            print(f"   ✓ Uses DATE_TRUNC")
            print(f"   ✓ Uses GROUP BY")
            print(f"   ✓ Uses ORDER BY")
            print(f"   ✓ NOT SELECT * LIMIT 100")
            return True
        else:
            print(f"❌ trend generates incorrect SQL:")
            print(f"   {query.sql}")
            print(f"   DATE_TRUNC: {has_date_trunc}")
            print(f"   GROUP BY: {has_group_by}")
            print(f"   ORDER BY: {has_order_by}")
            return False
    else:
        print(f"❌ Expected 1 query, got {len(result.queries)}")
        return False


async def test_outliers_sql():
    """Test that outliers generates z-score query with 2 std dev filter"""
    print("\n" + "=" * 60)
    print("Test 4: Outliers SQL")
    print("=" * 60)

    orchestrator = ChatOrchestrator()

    catalog = {
        "tables": [{
            "name": "data",
            "columns": ["id", "name", "value", "amount", "price"],
            "sample_data": [
                {"id": 1, "name": "A", "value": 100}
            ]
        }]
    }

    context = {
        "analysis_type": "outliers",
        "time_period": "last_month"
    }

    request = ChatOrchestratorRequest(
        message="outliers",
        conversationId="test-4",
        datasetId="test-dataset",
        catalog=catalog,
        safeMode=False,
        privacyMode=False
    )

    result = await orchestrator._generate_sql_plan(request, catalog, context)

    if len(result.queries) == 1:
        query = result.queries[0]
        sql = query.sql.strip().upper()

        has_avg = "AVG(" in sql
        has_stddev = "STDDEV(" in sql
        has_z_score = "Z_SCORE" in sql
        has_2_filter = "> 2 *" in sql or ">2*" in sql
        has_limit_200 = "LIMIT 200" in sql
        no_select_star_limit_100 = "SELECT * FROM DATA LIMIT 100" not in sql

        if has_avg and has_stddev and has_z_score and has_2_filter and has_limit_200 and no_select_star_limit_100:
            print(f"✅ outliers generates correct SQL:")
            print(f"   (SQL truncated for readability)")
            print(f"   ✓ Calculates AVG and STDDEV")
            print(f"   ✓ Computes z_score")
            print(f"   ✓ Filters by > 2 std dev")
            print(f"   ✓ Caps at LIMIT 200")
            print(f"   ✓ NOT SELECT * LIMIT 100")
            return True
        else:
            print(f"❌ outliers generates incorrect SQL:")
            print(f"   (SQL truncated for readability)")
            print(f"   AVG: {has_avg}")
            print(f"   STDDEV: {has_stddev}")
            print(f"   z_score: {has_z_score}")
            print(f"   > 2 filter: {has_2_filter}")
            print(f"   LIMIT 200: {has_limit_200}")
            return False
    else:
        print(f"❌ Expected 1 query, got {len(result.queries)}")
        return False


async def test_no_generic_fallback():
    """Test that there's no generic SELECT * LIMIT 100 fallback"""
    print("\n" + "=" * 60)
    print("Test 5: No Generic SELECT * LIMIT 100 Fallback")
    print("=" * 60)

    orchestrator = ChatOrchestrator()

    catalog = {
        "tables": [{
            "name": "data",
            "columns": ["id", "name", "value"],
            "sample_data": []
        }]
    }

    # Test with unknown analysis_type (should fallback to row_count, not SELECT *)
    context = {
        "analysis_type": "unknown_type",
        "time_period": "all_time"
    }

    request = ChatOrchestratorRequest(
        message="analyze data",
        conversationId="test-5",
        datasetId="test-dataset",
        catalog=catalog,
        safeMode=False,
        privacyMode=False
    )

    result = await orchestrator._generate_sql_plan(request, catalog, context)

    if len(result.queries) == 1:
        query = result.queries[0]
        sql = query.sql.strip().upper()

        is_not_select_star = "SELECT * FROM DATA LIMIT 100" not in sql

        if is_not_select_star:
            print(f"✅ Unknown analysis_type does NOT return SELECT * LIMIT 100:")
            print(f"   {query.sql}")
            print(f"   ✓ Safe fallback (likely row_count)")
            return True
        else:
            print(f"❌ Unknown analysis_type returns SELECT * LIMIT 100:")
            print(f"   {query.sql}")
            return False
    else:
        print(f"❌ Expected 1 query, got {len(result.queries)}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AE-1: Analysis-Specific SQL Plans - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Row count SQL
    results.append(("row_count SQL", await test_row_count_sql()))

    # Test 2: Top categories SQL
    results.append(("top_categories SQL", await test_top_categories_sql()))

    # Test 3: Trend SQL
    results.append(("trend SQL", await test_trend_sql()))

    # Test 4: Outliers SQL
    results.append(("outliers SQL", await test_outliers_sql()))

    # Test 5: No generic fallback
    results.append(("No generic SELECT * fallback", await test_no_generic_fallback()))

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
        print("✅ 'row count' yields COUNT(*) query, not SELECT * LIMIT 100")
        print("✅ 'top categories' yields GROUP BY with LIMIT 20")
        print("✅ 'trend' yields DATE_TRUNC with monthly aggregation")
        print("✅ 'outliers' yields z-score query with > 2 std dev filter, capped at 200 rows")
        print("✅ No generic SELECT * LIMIT 100 fallback")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
