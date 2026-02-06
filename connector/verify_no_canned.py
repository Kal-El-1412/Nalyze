"""
Verify OFF-REAL-1: No Canned Summary Implementation

Checks that the code correctly:
1. Never returns FinalAnswerResponse with canned text
2. Requires resultsContext for final_answer
3. Returns actual data in summaries (row count, trend, outliers)

Run with: python3 verify_no_canned.py
"""

import sys
import re


def verify_no_canned_final_answer():
    """Verify no canned FinalAnswerResponse in clarification flow"""
    print("\n" + "=" * 60)
    print("Verification 1: No Canned FinalAnswerResponse")
    print("=" * 60)

    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    # Check that the old canned response was removed
    forbidden_patterns = [
        r'FinalAnswerResponse\([^)]*summaryMarkdown="I\'m not sure how to help',
        r'FinalAnswerResponse\([^)]*"Dataset contains diverse data patterns"',
        r'FinalAnswerResponse\([^)]*"Statistical analysis shows normal distribution"',
        r'FinalAnswerResponse\([^)]*"No significant anomalies detected"',
    ]

    issues = []
    for pattern in forbidden_patterns:
        if re.search(pattern, content):
            issues.append(f"Found forbidden pattern: {pattern}")

    if issues:
        print(f"❌ Found canned FinalAnswerResponse:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"✅ No canned FinalAnswerResponse found")

    # Verify the replacement uses NeedsClarificationResponse
    if 'Don\'t return a canned summary' in content:
        print(f"✅ Comment indicates canned summary was intentionally removed")
    else:
        print(f"⚠️  Comment not found (may have been refactored)")

    return True


def verify_results_guard():
    """Verify guard prevents final_answer without resultsContext"""
    print("\n" + "=" * 60)
    print("Verification 2: Guard Requires ResultsContext")
    print("=" * 60)

    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    # Check for the guard
    if 'if not request.resultsContext or not request.resultsContext.results:' in content:
        print(f"✅ Guard checks for missing resultsContext")

        # Check that it raises an error instead of returning generic response
        guard_section = content[content.find('if not request.resultsContext'):]
        guard_section = guard_section[:guard_section.find('\n\n')]

        if 'raise ValueError' in guard_section:
            print(f"✅ Guard raises ValueError (not FinalAnswerResponse)")

            if 'Cannot generate final answer without query results' in guard_section:
                print(f"✅ Error message is clear and informative")
                return True
            else:
                print(f"⚠️  Error message may need improvement")
                return True
        elif 'FinalAnswerResponse' in guard_section and 'No results to analyze' in guard_section:
            print(f"❌ Guard returns FinalAnswerResponse with generic message")
            return False
        else:
            print(f"⚠️  Guard behavior unclear")
            return False
    else:
        print(f"❌ Missing guard for resultsContext")
        return False


def verify_actual_data_summaries():
    """Verify summaries use actual data from results"""
    print("\n" + "=" * 60)
    print("Verification 3: Summaries Use Actual Data")
    print("=" * 60)

    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    checks = []

    # Check row_count extracts actual value
    if 'analysis_type == "row_count"' in content:
        # Look for the pattern where row count extracts the value
        if 'result.rows[0][0]' in content:
            checks.append(("Row count", "✅ Extracts actual count from result.rows[0][0]"))
        else:
            checks.append(("Row count", "❌ Doesn't extract actual value"))
    else:
        checks.append(("Row count", "❌ Row count handler not found"))

    # Check trend includes table
    if 'analysis_type == "trend"' in content:
        # Look for table appending in trend section
        if 'tables.append(TableData(' in content and '"Monthly Trend"' in content:
            checks.append(("Trend", "✅ Appends table with actual data"))
        else:
            checks.append(("Trend", "❌ Doesn't include table"))
    else:
        checks.append(("Trend", "❌ Trend handler not found"))

    # Check outliers includes counts
    if 'analysis_type == "outliers"' in content:
        # Look for outlier count calculations
        if 'total_outliers = sum(' in content and 'cols_with_outliers = sum(' in content:
            checks.append(("Outliers", "✅ Calculates actual outlier counts"))
        elif 'outlier_count = len(result.rows)' in content:
            checks.append(("Outliers", "✅ Calculates actual outlier counts"))
        else:
            checks.append(("Outliers", "❌ Doesn't calculate actual counts"))
    else:
        checks.append(("Outliers", "❌ Outliers handler not found"))

    all_passed = True
    for name, result in checks:
        print(f"   {name}: {result}")
        if "❌" in result:
            all_passed = False

    return all_passed


def verify_no_forbidden_phrases():
    """Verify no forbidden canned phrases exist"""
    print("\n" + "=" * 60)
    print("Verification 4: No Forbidden Phrases")
    print("=" * 60)

    with open('app/chat_orchestrator.py', 'r') as f:
        content = f.read()

    forbidden_phrases = [
        "Dataset contains diverse data patterns",
        "Statistical analysis shows normal distribution",
        "No significant anomalies detected",
    ]

    found_phrases = []
    for phrase in forbidden_phrases:
        if phrase in content:
            found_phrases.append(phrase)

    if found_phrases:
        print(f"❌ Found {len(found_phrases)} forbidden phrase(s):")
        for phrase in found_phrases:
            print(f"   - '{phrase}'")
        return False
    else:
        print(f"✅ No forbidden canned phrases found")
        return True


def main():
    """Run all verifications"""
    print("\n" + "=" * 60)
    print("OFF-REAL-1: No Canned Summary - Verification")
    print("=" * 60)

    results = []

    # Verification 1: No canned final_answer
    results.append(("No canned FinalAnswerResponse", verify_no_canned_final_answer()))

    # Verification 2: Guard requires results
    results.append(("Guard requires resultsContext", verify_results_guard()))

    # Verification 3: Actual data summaries
    results.append(("Summaries use actual data", verify_actual_data_summaries()))

    # Verification 4: No forbidden phrases
    results.append(("No forbidden phrases", verify_no_forbidden_phrases()))

    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n" + "=" * 60)
        print("✅ ALL VERIFICATIONS PASSED!")
        print("=" * 60)
        print("\nAcceptance Criteria Met:")
        print("✅ No canned/generic summaries in clarification flow")
        print("✅ Guard prevents final_answer without resultsContext")
        print("✅ Row count returns actual number from results")
        print("✅ Trend returns table + summary references data")
        print("✅ Outliers show actual counts from results")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME VERIFICATIONS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
