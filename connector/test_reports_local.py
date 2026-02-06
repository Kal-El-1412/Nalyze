"""
Test local reports storage functionality

Run with: python3 test_reports_local.py
"""
import sys
import os
from pathlib import Path

# Add the connector directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.reports_local import (
    get_reports_directory,
    get_reports_file_path,
    load_reports,
    save_reports,
    reports_local_storage
)
from app.models import FinalAnswerResponse, TableData, AuditMetadata, QueryAudit


def test_directory_detection():
    """Test that the reports directory is detected correctly"""
    reports_dir = get_reports_directory()
    print(f"✓ Reports directory: {reports_dir}")
    assert reports_dir.exists(), f"Reports directory should exist: {reports_dir}"

    reports_file = get_reports_file_path()
    print(f"✓ Reports file path: {reports_file}")


def test_save_and_load():
    """Test saving and loading reports"""
    # Create a test report
    audit = AuditMetadata(
        analysisType="test_analysis",
        timePeriod="all_time",
        executedQueries=[
            QueryAudit(
                name="Test Query",
                sql="SELECT * FROM test",
                rowCount=10,
                executionTime=0.5
            )
        ],
        aiAssist=False,
        safeMode=True,
        privacyMode=True
    )

    table = TableData(
        name="Test Results",
        columns=["id", "name", "value"],
        rows=[
            ["1", "Test Item 1", "100"],
            ["2", "Test Item 2", "200"]
        ]
    )

    final_answer = FinalAnswerResponse(
        responseType="final_answer",
        summaryMarkdown="# Test Report\n\nThis is a test.",
        tables=[table],
        audit=audit
    )

    # Save the report
    report_id = reports_local_storage.save_report(
        dataset_id="test_dataset_123",
        dataset_name="Test Dataset",
        conversation_id="test_conv_456",
        question="What is the test data?",
        final_answer=final_answer
    )

    assert report_id is not None, "Report ID should be returned"
    print(f"✓ Saved report with ID: {report_id}")

    # Load the report back
    loaded_report = reports_local_storage.get_report_by_id(report_id)
    assert loaded_report is not None, "Report should be loadable"
    assert loaded_report.id == report_id, "Report ID should match"
    assert loaded_report.dataset_id == "test_dataset_123", "Dataset ID should match"
    assert loaded_report.question == "What is the test data?", "Question should match"
    print(f"✓ Loaded report successfully")

    # Get report summaries
    summaries = reports_local_storage.get_report_summaries()
    assert len(summaries) > 0, "Should have at least one report summary"
    assert any(s.id == report_id for s in summaries), "New report should be in summaries"
    print(f"✓ Report appears in summaries list ({len(summaries)} total)")

    # Get reports for specific dataset
    dataset_reports = reports_local_storage.get_reports(dataset_id="test_dataset_123")
    assert len(dataset_reports) > 0, "Should have reports for this dataset"
    assert any(r.id == report_id for r in dataset_reports), "New report should be in dataset reports"
    print(f"✓ Report appears in dataset-filtered list")

    # Get reports for non-existent dataset
    empty_reports = reports_local_storage.get_reports(dataset_id="nonexistent")
    assert len(empty_reports) == 0, "Should have no reports for non-existent dataset"
    print(f"✓ Filtering by dataset works correctly")


def test_persistence():
    """Test that reports persist across storage instances"""
    # Create first instance and save a report
    storage1 = reports_local_storage

    audit = AuditMetadata(
        analysisType="persistence_test",
        timePeriod="last_month",
        executedQueries=[],
        aiAssist=True,
        safeMode=False,
        privacyMode=True
    )

    final_answer = FinalAnswerResponse(
        responseType="final_answer",
        summaryMarkdown="# Persistence Test",
        tables=[],
        audit=audit
    )

    report_id = storage1.save_report(
        dataset_id="persist_dataset",
        dataset_name="Persistence Dataset",
        conversation_id="persist_conv",
        question="Does it persist?",
        final_answer=final_answer
    )

    print(f"✓ Saved persistence test report: {report_id}")

    # Load from file directly to verify persistence
    reports = load_reports()
    assert any(r["id"] == report_id for r in reports), "Report should persist in file"
    print(f"✓ Report persists in JSON file")


def test_multiple_reports():
    """Test handling multiple reports"""
    initial_count = len(reports_local_storage.get_report_summaries())

    # Create multiple reports
    for i in range(3):
        audit = AuditMetadata(
            analysisType=f"test_{i}",
            timePeriod="all_time",
            executedQueries=[],
            aiAssist=False,
            safeMode=True,
            privacyMode=True
        )

        final_answer = FinalAnswerResponse(
            responseType="final_answer",
            summaryMarkdown=f"# Test Report {i}",
            tables=[],
            audit=audit
        )

        report_id = reports_local_storage.save_report(
            dataset_id=f"dataset_{i}",
            dataset_name=f"Dataset {i}",
            conversation_id=f"conv_{i}",
            question=f"Question {i}?",
            final_answer=final_answer
        )

        assert report_id is not None, f"Report {i} should be saved"

    final_count = len(reports_local_storage.get_report_summaries())
    assert final_count >= initial_count + 3, "Should have 3 more reports"
    print(f"✓ Multiple reports saved successfully ({final_count} total)")


def test_sorting():
    """Test that reports are sorted by creation time (newest first)"""
    summaries = reports_local_storage.get_report_summaries()

    if len(summaries) > 1:
        # Check that reports are in descending order by creation time
        for i in range(len(summaries) - 1):
            assert summaries[i].createdAt >= summaries[i + 1].createdAt, \
                "Reports should be sorted newest first"
        print(f"✓ Reports are sorted correctly (newest first)")
    else:
        print("! Not enough reports to test sorting (need at least 2)")


if __name__ == "__main__":
    print("\n=== Testing Local Reports Storage ===\n")

    try:
        test_directory_detection()
        print()

        test_save_and_load()
        print()

        test_persistence()
        print()

        test_multiple_reports()
        print()

        test_sorting()
        print()

        print("\n✅ All tests passed!\n")

        # Show final stats
        summaries = reports_local_storage.get_report_summaries()
        print(f"Total reports in storage: {len(summaries)}")
        print(f"Storage location: {get_reports_file_path()}")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
