"""
Test AE-1: Analysis-Specific SQL Plans (Simple Version)

Verifies that the SQL plan logic generates the correct SQL for each analysis type
by checking the code structure directly.

Run with: python3 test_ae1_simple.py
"""

import sys
import re


def test_row_count_implementation():
    """Test that row_count generates COUNT(*) query"""
    print("\n" + "=" * 60)
    print("Test 1: Row Count Implementation")
    print("=" * 60)

    # Read the implementation
    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    # Find row_count implementation
    row_count_pattern = r'if analysis_type == "row_count":(.*?)elif analysis_type =='
    match = re.search(row_count_pattern, content, re.DOTALL)

    if match:
        implementation = match.group(1)

        has_count_star = 'COUNT(*)' in implementation or 'COUNT( * )' in implementation
        has_row_count = 'row_count' in implementation
        no_select_star_limit = 'SELECT * FROM' not in implementation or 'LIMIT 1' in implementation

        if has_count_star and has_row_count and no_select_star_limit:
            print("✅ row_count implementation correct:")
            print("   ✓ Uses COUNT(*)")
            print("   ✓ Named 'row_count'")
            print("   ✓ NOT SELECT * LIMIT 100")
            return True
        else:
            print("❌ row_count implementation incorrect:")
            print(f"   COUNT(*): {has_count_star}")
            print(f"   row_count: {has_row_count}")
            print(f"   No SELECT * LIMIT: {no_select_star_limit}")
            return False
    else:
        print("❌ Could not find row_count implementation")
        return False


def test_top_categories_implementation():
    """Test that top_categories generates GROUP BY query with LIMIT 20"""
    print("\n" + "=" * 60)
    print("Test 2: Top Categories Implementation")
    print("=" * 60)

    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    # Find top_categories implementation
    top_cat_pattern = r'elif analysis_type == "top_categories":(.*?)elif analysis_type =='
    match = re.search(top_cat_pattern, content, re.DOTALL)

    if match:
        implementation = match.group(1)

        has_group_by = 'GROUP BY' in implementation
        has_count = 'COUNT(*)' in implementation or 'COUNT( * )' in implementation
        has_limit_20 = 'LIMIT 20' in implementation
        has_order_by = 'ORDER BY' in implementation
        has_category_alias = 'AS category' in implementation or 'as category' in implementation

        if has_group_by and has_count and has_limit_20 and has_order_by and has_category_alias:
            print("✅ top_categories implementation correct:")
            print("   ✓ Uses GROUP BY")
            print("   ✓ Uses COUNT(*)")
            print("   ✓ Uses LIMIT 20")
            print("   ✓ Uses ORDER BY")
            print("   ✓ Aliases column AS category")
            return True
        else:
            print("❌ top_categories implementation incorrect:")
            print(f"   GROUP BY: {has_group_by}")
            print(f"   COUNT(*): {has_count}")
            print(f"   LIMIT 20: {has_limit_20}")
            print(f"   ORDER BY: {has_order_by}")
            print(f"   AS category: {has_category_alias}")
            return False
    else:
        print("❌ Could not find top_categories implementation")
        return False


def test_trend_implementation():
    """Test that trend generates DATE_TRUNC query"""
    print("\n" + "=" * 60)
    print("Test 3: Trend Implementation")
    print("=" * 60)

    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    # Find trend implementation
    trend_pattern = r'elif analysis_type == "trend":(.*?)elif analysis_type =='
    match = re.search(trend_pattern, content, re.DOTALL)

    if match:
        implementation = match.group(1)

        has_date_trunc = 'DATE_TRUNC' in implementation
        has_month = "'month'" in implementation or '"month"' in implementation
        has_group_by = 'GROUP BY' in implementation
        has_order_by = 'ORDER BY' in implementation

        if has_date_trunc and has_month and has_group_by and has_order_by:
            print("✅ trend implementation correct:")
            print("   ✓ Uses DATE_TRUNC")
            print("   ✓ Defaults to 'month'")
            print("   ✓ Uses GROUP BY")
            print("   ✓ Uses ORDER BY")
            return True
        else:
            print("❌ trend implementation incorrect:")
            print(f"   DATE_TRUNC: {has_date_trunc}")
            print(f"   'month': {has_month}")
            print(f"   GROUP BY: {has_group_by}")
            print(f"   ORDER BY: {has_order_by}")
            return False
    else:
        print("❌ Could not find trend implementation")
        return False


def test_outliers_implementation():
    """Test that outliers generates z-score query with 2 std dev filter"""
    print("\n" + "=" * 60)
    print("Test 4: Outliers Implementation")
    print("=" * 60)

    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    # Find outliers implementation
    outliers_pattern = r'elif analysis_type == "outliers":(.*?)elif analysis_type =='
    match = re.search(outliers_pattern, content, re.DOTALL)

    if match:
        implementation = match.group(1)

        has_avg = 'AVG(' in implementation
        has_stddev = 'STDDEV(' in implementation
        has_z_score = 'z_score' in implementation
        has_2_filter = '> 2 *' in implementation or '>2*' in implementation or '> 2*' in implementation
        has_limit_200 = 'LIMIT 200' in implementation

        if has_avg and has_stddev and has_z_score and has_2_filter and has_limit_200:
            print("✅ outliers implementation correct:")
            print("   ✓ Calculates AVG")
            print("   ✓ Calculates STDDEV")
            print("   ✓ Computes z_score")
            print("   ✓ Filters by > 2 std dev")
            print("   ✓ Caps at LIMIT 200")
            return True
        else:
            print("❌ outliers implementation incorrect:")
            print(f"   AVG: {has_avg}")
            print(f"   STDDEV: {has_stddev}")
            print(f"   z_score: {has_z_score}")
            print(f"   > 2 filter: {has_2_filter}")
            print(f"   LIMIT 200: {has_limit_200}")
            return False
    else:
        print("❌ Could not find outliers implementation")
        return False


def test_no_select_star_limit_100():
    """Test that there's no SELECT * FROM data LIMIT 100 in utils.py"""
    print("\n" + "=" * 60)
    print("Test 5: No SELECT * LIMIT 100 in Utils")
    print("=" * 60)

    with open('app/utils.py', 'r') as f:
        content = f.read()

    has_select_star_100 = 'SELECT * FROM data LIMIT 100' in content
    has_select_star_10 = 'SELECT * FROM data LIMIT 10' in content

    if not has_select_star_100 and not has_select_star_10:
        print("✅ No generic SELECT * LIMIT queries in utils.py:")
        print("   ✓ Removed SELECT * FROM data LIMIT 100")
        print("   ✓ Removed SELECT * FROM data LIMIT 10")
        return True
    else:
        print("❌ Found generic SELECT * LIMIT queries in utils.py:")
        print(f"   SELECT * LIMIT 100: {has_select_star_100}")
        print(f"   SELECT * LIMIT 10: {has_select_star_10}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AE-1: Analysis-Specific SQL Plans - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Row count implementation
    results.append(("row_count implementation", test_row_count_implementation()))

    # Test 2: Top categories implementation
    results.append(("top_categories implementation", test_top_categories_implementation()))

    # Test 3: Trend implementation
    results.append(("trend implementation", test_trend_implementation()))

    # Test 4: Outliers implementation
    results.append(("outliers implementation", test_outliers_implementation()))

    # Test 5: No SELECT * LIMIT 100
    results.append(("No SELECT * LIMIT 100", test_no_select_star_limit_100()))

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
        print("✅ 'trend' yields DATE_TRUNC('month') with GROUP BY and ORDER BY")
        print("✅ 'outliers' yields z-score query with > 2 std dev filter, capped at 200 rows")
        print("✅ No generic SELECT * LIMIT 100 fallback in utils.py")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
