"""Test privacy mode and PII redaction"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models import Catalog, ColumnInfo, PIIColumnInfo
from app.pii_redactor import pii_redactor


def test_pii_redaction():
    """Test that PII columns are properly redacted in privacy mode"""

    catalog = Catalog(
        table="data",
        rowCount=1000,
        columns=[
            ColumnInfo(name="customer_id", type="INTEGER"),
            ColumnInfo(name="customer_email", type="VARCHAR"),
            ColumnInfo(name="phone_number", type="VARCHAR"),
            ColumnInfo(name="full_name", type="VARCHAR"),
            ColumnInfo(name="order_date", type="DATE"),
            ColumnInfo(name="amount", type="DECIMAL"),
        ],
        basicStats={
            "customer_id": {"min": 1, "max": 1000, "nullPct": 0.0},
            "customer_email": {"nullPct": 0.1},
            "phone_number": {"nullPct": 0.2},
            "full_name": {"nullPct": 0.0},
            "order_date": {"nullPct": 0.0},
            "amount": {"min": 10.0, "max": 1000.0, "avg": 250.5, "nullPct": 0.0},
        },
        detectedDateColumns=["order_date"],
        detectedNumericColumns=["customer_id", "amount"],
        piiColumns=[
            PIIColumnInfo(name="customer_email", type="email", confidence=0.95),
            PIIColumnInfo(name="phone_number", type="phone", confidence=0.90),
            PIIColumnInfo(name="full_name", type="name", confidence=0.85),
        ]
    )

    print("Original Catalog:")
    print(f"  Columns: {[c.name for c in catalog.columns]}")
    print(f"  PII Columns: {[p.name for p in catalog.piiColumns]}")
    print()

    redacted_catalog, pii_map = pii_redactor.redact_catalog(catalog, privacy_mode=True)

    print("Redacted Catalog (Privacy Mode ON):")
    print(f"  Columns: {[c.name for c in redacted_catalog.columns]}")
    print(f"  PII Columns: {[p.name for p in redacted_catalog.piiColumns]}")
    print(f"  PII Mapping: {pii_map}")
    print()

    assert len(redacted_catalog.piiColumns) == 0, "PII columns should be empty after redaction"

    column_names = [c.name for c in redacted_catalog.columns]
    assert "customer_email" not in column_names, "Original PII column name should not appear"
    assert "phone_number" not in column_names, "Original PII column name should not appear"
    assert "full_name" not in column_names, "Original PII column name should not appear"

    assert "PII_EMAIL_1" in column_names, "Redacted email placeholder should appear"
    assert "PII_PHONE_1" in column_names, "Redacted phone placeholder should appear"
    assert "PII_NAME_1" in column_names, "Redacted name placeholder should appear"

    assert "customer_id" in column_names, "Non-PII columns should remain unchanged"
    assert "order_date" in column_names, "Non-PII columns should remain unchanged"
    assert "amount" in column_names, "Non-PII columns should remain unchanged"

    assert pii_map["PII_EMAIL_1"] == "customer_email", "Reverse mapping should be correct"
    assert pii_map["PII_PHONE_1"] == "phone_number", "Reverse mapping should be correct"
    assert pii_map["PII_NAME_1"] == "full_name", "Reverse mapping should be correct"

    print("✓ Privacy Mode ON: PII columns redacted successfully")
    print()

    no_redaction_catalog, no_pii_map = pii_redactor.redact_catalog(catalog, privacy_mode=False)

    print("Non-Redacted Catalog (Privacy Mode OFF):")
    print(f"  Columns: {[c.name for c in no_redaction_catalog.columns]}")
    print(f"  PII Columns: {[p.name for p in no_redaction_catalog.piiColumns]}")
    print()

    no_redaction_column_names = [c.name for c in no_redaction_catalog.columns]
    assert "customer_email" in no_redaction_column_names, "Original PII columns should remain"
    assert "phone_number" in no_redaction_column_names, "Original PII columns should remain"
    assert "full_name" in no_redaction_column_names, "Original PII columns should remain"
    assert len(no_redaction_catalog.piiColumns) == 3, "PII metadata should be preserved"
    assert len(no_pii_map) == 0, "No mapping when privacy mode is off"

    print("✓ Privacy Mode OFF: PII columns NOT redacted (as expected)")
    print()

    print("All tests passed! ✓")


if __name__ == "__main__":
    test_pii_redaction()
