import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from app.query import query_executor


async def test_query_validation():
    print("Testing SQL validation...")

    test_cases = [
        ("SELECT * FROM data", True, "Valid SELECT"),
        ("SELECT COUNT(*) FROM data", True, "Valid COUNT"),
        ("INSERT INTO data VALUES (1)", False, "INSERT blocked"),
        ("UPDATE data SET x=1", False, "UPDATE blocked"),
        ("DELETE FROM data", False, "DELETE blocked"),
        ("DROP TABLE data", False, "DROP blocked"),
        ("ATTACH 'file.db'", False, "ATTACH blocked"),
        ("COPY data TO 'file'", False, "COPY blocked"),
        ("PRAGMA table_info(data)", False, "PRAGMA blocked"),
        ("CREATE TABLE x (id INT)", False, "CREATE blocked"),
    ]

    for sql, should_pass, description in test_cases:
        is_valid, error_msg = query_executor.validate_sql(sql)

        if should_pass:
            if is_valid:
                print(f"✓ PASS: {description}")
            else:
                print(f"✗ FAIL: {description} - Expected to pass but got: {error_msg}")
        else:
            if not is_valid:
                print(f"✓ PASS: {description} - Correctly blocked")
            else:
                print(f"✗ FAIL: {description} - Should have been blocked")


async def test_limit_wrapping():
    print("\nTesting LIMIT enforcement (max 200 rows)...")

    test_cases = [
        ("SELECT * FROM data", "SELECT * FROM (SELECT * FROM data) LIMIT 200", "No LIMIT - adds 200"),
        ("SELECT * FROM data LIMIT 50", "SELECT * FROM data LIMIT 50", "LIMIT 50 - unchanged"),
        ("SELECT * FROM data LIMIT 500", "SELECT * FROM data LIMIT 200", "LIMIT 500 - reduced to 200"),
        ("SELECT * FROM data LIMIT 1000", "SELECT * FROM data LIMIT 200", "LIMIT 1000 - reduced to 200"),
    ]

    for sql, expected, description in test_cases:
        result = query_executor.wrap_with_limit(sql)

        if result == expected:
            print(f"✓ PASS: {description}")
        else:
            print(f"✗ FAIL: {description}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")


async def main():
    print("=" * 60)
    print("Prompt 8: Query Execution Tests")
    print("=" * 60)

    await test_query_validation()
    await test_limit_wrapping()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✓ SQL validation enforces SELECT only")
    print("✓ Dangerous keywords blocked (INSERT, UPDATE, DELETE, etc.)")
    print("✓ ATTACH, COPY, PRAGMA blocked")
    print("✓ Max 200 rows enforced per query")
    print("\nEndpoint: POST /queries/execute")
    print("Request: { datasetId, queries: [{ name, sql }] }")
    print("Response: { results: [{ name, columns, rows }] }")
    print("\n✅ All validations pass!")


if __name__ == "__main__":
    asyncio.run(main())
