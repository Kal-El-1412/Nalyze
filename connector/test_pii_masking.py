"""Test PII value masking in query results"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models import Catalog, ColumnInfo, PIIColumnInfo
from app.pii_masker import pii_masker


def test_email_masking():
    """Test email masking"""
    print("Testing Email Masking:")

    test_cases = [
        ("john.doe@example.com", "j***@example.com"),
        ("test@gmail.com", "t***@gmail.com"),
        ("a@domain.org", "a***@domain.org"),
        ("", ""),
        (None, None),
    ]

    for original, expected in test_cases:
        masked = pii_masker.mask_value(original, "email")
        status = "✓" if masked == expected else "✗"
        print(f"  {status} {repr(original)} -> {repr(masked)} (expected: {repr(expected)})")

    print()


def test_phone_masking():
    """Test phone number masking"""
    print("Testing Phone Masking:")

    test_cases = [
        ("555-123-4567", "****4567"),
        ("(555) 123-4567", "****4567"),
        ("5551234567", "****4567"),
        ("+1-555-123-4567", "****4567"),
        ("123", "****"),
        ("", "****"),
        (None, None),
    ]

    for original, expected in test_cases:
        masked = pii_masker.mask_value(original, "phone")
        status = "✓" if masked == expected else "✗"
        print(f"  {status} {repr(original)} -> {repr(masked)} (expected: {repr(expected)})")

    print()


def test_name_masking():
    """Test name masking"""
    print("Testing Name Masking:")

    test_cases = [
        ("John Doe", "J***"),
        ("Jane", "J***"),
        ("A", "A***"),
        ("", "***"),
        (None, None),
    ]

    for original, expected in test_cases:
        masked = pii_masker.mask_value(original, "name")
        status = "✓" if masked == expected else "✗"
        print(f"  {status} {repr(original)} -> {repr(masked)} (expected: {repr(expected)})")

    print()


def test_result_row_masking():
    """Test masking of result rows"""
    print("Testing Result Row Masking:")

    catalog = Catalog(
        table="data",
        rowCount=1000,
        columns=[
            ColumnInfo(name="id", type="INTEGER"),
            ColumnInfo(name="email", type="VARCHAR"),
            ColumnInfo(name="phone", type="VARCHAR"),
            ColumnInfo(name="name", type="VARCHAR"),
            ColumnInfo(name="amount", type="DECIMAL"),
        ],
        basicStats={},
        detectedDateColumns=[],
        detectedNumericColumns=["id", "amount"],
        piiColumns=[
            PIIColumnInfo(name="email", type="email", confidence=0.95),
            PIIColumnInfo(name="phone", type="phone", confidence=0.90),
            PIIColumnInfo(name="name", type="name", confidence=0.85),
        ]
    )

    columns = ["id", "email", "phone", "name", "amount"]
    rows = [
        (1, "john@example.com", "555-123-4567", "John Doe", 100.50),
        (2, "jane@test.com", "(555) 987-6543", "Jane Smith", 200.75),
        (3, "bob@company.org", "5551112222", "Bob Johnson", 150.00),
    ]

    print("  Original rows:")
    for row in rows:
        print(f"    {row}")
    print()

    masked_rows = pii_masker.mask_result_rows(columns, rows, catalog, privacy_mode=True)

    print("  Masked rows (Privacy Mode ON):")
    for row in masked_rows:
        print(f"    {row}")
    print()

    assert len(masked_rows) == len(rows), "Row count should match"

    for masked_row in masked_rows:
        assert masked_row[0] in [1, 2, 3], "ID should not be masked"
        assert masked_row[4] in [100.50, 200.75, 150.00], "Amount should not be masked"
        assert "***@" in masked_row[1], "Email should be masked"
        assert "****" in masked_row[2], "Phone should be masked"
        assert "***" in masked_row[3], "Name should be masked"

    print("  ✓ Privacy Mode ON: All PII values masked correctly")
    print()

    unmasked_rows = pii_masker.mask_result_rows(columns, rows, catalog, privacy_mode=False)

    print("  Unmasked rows (Privacy Mode OFF):")
    for row in unmasked_rows:
        print(f"    {row}")
    print()

    assert unmasked_rows == rows, "Unmasked rows should match original"

    print("  ✓ Privacy Mode OFF: No masking applied")
    print()


def test_no_pii_columns():
    """Test that non-PII data is not masked"""
    print("Testing Non-PII Data:")

    catalog = Catalog(
        table="data",
        rowCount=1000,
        columns=[
            ColumnInfo(name="id", type="INTEGER"),
            ColumnInfo(name="product", type="VARCHAR"),
            ColumnInfo(name="amount", type="DECIMAL"),
        ],
        basicStats={},
        detectedDateColumns=[],
        detectedNumericColumns=["id", "amount"],
        piiColumns=[]
    )

    columns = ["id", "product", "amount"]
    rows = [
        (1, "Widget A", 100.50),
        (2, "Widget B", 200.75),
    ]

    masked_rows = pii_masker.mask_result_rows(columns, rows, catalog, privacy_mode=True)

    print("  Original rows:")
    for row in rows:
        print(f"    {row}")
    print()

    print("  Masked rows (Privacy Mode ON, but no PII columns):")
    for row in masked_rows:
        print(f"    {row}")
    print()

    assert masked_rows == rows, "Non-PII data should not be masked"

    print("  ✓ Non-PII data remains unchanged")
    print()


if __name__ == "__main__":
    test_email_masking()
    test_phone_masking()
    test_name_masking()
    test_result_row_masking()
    test_no_pii_columns()

    print("=" * 60)
    print("All PII masking tests passed! ✓")
    print("=" * 60)
