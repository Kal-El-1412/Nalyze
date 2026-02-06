"""
Local JSON-based reports storage module for saving and retrieving analysis reports
"""
import json
import logging
import os
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.models import Report, ReportSummary, FinalAnswerResponse

logger = logging.getLogger(__name__)


def get_reports_directory() -> Path:
    """
    Get platform-specific directory for storing reports

    Returns:
        Path to reports directory
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        base_dir = Path.home() / "Library" / "Application Support" / "CloakedSheets"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base_dir = Path(appdata) / "CloakedSheets"
        else:
            # Fallback if APPDATA is not set
            base_dir = Path.home() / ".cloaksheets"
    else:  # Linux and other Unix-like systems
        base_dir = Path.home() / ".cloaksheets"

    # Create directory if it doesn't exist
    base_dir.mkdir(parents=True, exist_ok=True)

    return base_dir


def get_reports_file_path() -> Path:
    """Get the full path to the reports.json file"""
    return get_reports_directory() / "reports.json"


def load_reports() -> List[Dict[str, Any]]:
    """
    Load all reports from the JSON file

    Returns:
        List of report dictionaries
    """
    reports_file = get_reports_file_path()

    if not reports_file.exists():
        return []

    try:
        with open(reports_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("reports", [])
    except Exception as e:
        logger.error(f"Error loading reports from {reports_file}: {e}")
        return []


def save_reports(reports: List[Dict[str, Any]]) -> bool:
    """
    Save all reports to the JSON file

    Args:
        reports: List of report dictionaries

    Returns:
        True if successful, False otherwise
    """
    reports_file = get_reports_file_path()

    try:
        with open(reports_file, 'w', encoding='utf-8') as f:
            json.dump({"reports": reports}, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving reports to {reports_file}: {e}")
        return False


class ReportsLocalStorage:
    """Handles saving and retrieving reports from local JSON file"""

    def __init__(self):
        logger.info(f"Reports will be stored in: {get_reports_file_path()}")

    def save_report(
        self,
        dataset_id: str,
        dataset_name: str,
        conversation_id: str,
        question: str,
        final_answer: FinalAnswerResponse,
    ) -> Optional[str]:
        """
        Save a report to local JSON storage

        Args:
            dataset_id: Dataset ID
            dataset_name: Dataset name
            conversation_id: Conversation ID
            question: The original question asked
            final_answer: The final_answer response to save

        Returns:
            Report ID (uuid) if successful, None otherwise
        """
        try:
            report_id = str(uuid.uuid4())

            # Convert tables to JSON-serializable format
            tables_json = [
                {
                    "name": table.name,
                    "columns": table.columns,
                    "rows": table.rows
                }
                for table in final_answer.tables
            ]

            # Build audit log from audit metadata
            audit_log = [
                f"Analysis Type: {final_answer.audit.analysisType}",
                f"Time Period: {final_answer.audit.timePeriod}",
                f"AI Assist: {'ON' if final_answer.audit.aiAssist else 'OFF'}",
                f"Safe Mode: {'ON' if final_answer.audit.safeMode else 'OFF'}",
                f"Privacy Mode: {'ON' if final_answer.audit.privacyMode else 'OFF'}",
            ]

            for query in final_answer.audit.executedQueries:
                audit_log.append(f"Query: {query.name} ({query.rowCount} rows)")
                audit_log.append(f"  SQL: {query.sql}")

            # Create report dictionary
            report_data = {
                "id": report_id,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "conversation_id": conversation_id,
                "question": question,
                "analysis_type": final_answer.audit.analysisType,
                "time_period": final_answer.audit.timePeriod,
                "summary_markdown": final_answer.summaryMarkdown,
                "tables": tables_json,
                "audit_log": audit_log,
                "privacy_mode": final_answer.audit.privacyMode,
                "safe_mode": final_answer.audit.safeMode,
                "created_at": datetime.now().isoformat(),
            }

            # Load existing reports
            reports = load_reports()

            # Add new report
            reports.append(report_data)

            # Save back to file
            if save_reports(reports):
                logger.info(f"Saved report {report_id} for dataset {dataset_id} to local storage")
                return report_id
            else:
                logger.error("Failed to save report to local storage")
                return None

        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return None

    def get_reports(self, dataset_id: Optional[str] = None, limit: int = 100) -> List[Report]:
        """
        Get list of reports, optionally filtered by dataset

        Args:
            dataset_id: Optional dataset ID to filter by
            limit: Maximum number of reports to return

        Returns:
            List of Report objects
        """
        try:
            reports = load_reports()

            # Filter by dataset if specified
            if dataset_id:
                reports = [r for r in reports if r.get("dataset_id") == dataset_id]

            # Sort by created_at descending
            reports.sort(key=lambda r: r.get("created_at", ""), reverse=True)

            # Apply limit
            reports = reports[:limit]

            # Convert to Report objects
            result = []
            for row in reports:
                result.append(Report(
                    id=row["id"],
                    dataset_id=row["dataset_id"],
                    dataset_name=row.get("dataset_name"),
                    conversation_id=row["conversation_id"],
                    question=row["question"],
                    analysis_type=row["analysis_type"],
                    time_period=row["time_period"],
                    summary_markdown=row["summary_markdown"],
                    tables=row["tables"],
                    audit_log=row["audit_log"],
                    created_at=row["created_at"],
                    privacy_mode=row["privacy_mode"],
                    safe_mode=row["safe_mode"],
                ))

            return result

        except Exception as e:
            logger.error(f"Error fetching reports: {e}")
            return []

    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """
        Get a specific report by ID

        Args:
            report_id: Report UUID

        Returns:
            Report object if found, None otherwise
        """
        try:
            reports = load_reports()

            # Find report by ID
            report_data = next((r for r in reports if r["id"] == report_id), None)

            if not report_data:
                return None

            return Report(
                id=report_data["id"],
                dataset_id=report_data["dataset_id"],
                dataset_name=report_data.get("dataset_name"),
                conversation_id=report_data["conversation_id"],
                question=report_data["question"],
                analysis_type=report_data["analysis_type"],
                time_period=report_data["time_period"],
                summary_markdown=report_data["summary_markdown"],
                tables=report_data["tables"],
                audit_log=report_data["audit_log"],
                created_at=report_data["created_at"],
                privacy_mode=report_data["privacy_mode"],
                safe_mode=report_data["safe_mode"],
            )

        except Exception as e:
            logger.error(f"Error fetching report {report_id}: {e}")
            return None

    def get_report_summaries(self, dataset_id: Optional[str] = None, limit: int = 100) -> List[ReportSummary]:
        """
        Get list of report summaries for display in UI

        Args:
            dataset_id: Optional dataset ID to filter by
            limit: Maximum number of reports to return

        Returns:
            List of ReportSummary objects with id, title, datasetId, datasetName, createdAt
        """
        try:
            reports = load_reports()

            # Filter by dataset if specified
            if dataset_id:
                reports = [r for r in reports if r.get("dataset_id") == dataset_id]

            # Sort by created_at descending
            reports.sort(key=lambda r: r.get("created_at", ""), reverse=True)

            # Apply limit
            reports = reports[:limit]

            # Convert to ReportSummary objects
            summaries = []
            for row in reports:
                title = row.get("question", "Untitled Report")
                if not title or title.strip() == "":
                    analysis_type = row.get("analysis_type", "analysis")
                    title = f"{analysis_type.replace('_', ' ').title()} Report"

                summaries.append(ReportSummary(
                    id=row["id"],
                    title=title,
                    datasetId=row["dataset_id"],
                    datasetName=row.get("dataset_name") or "Unknown Dataset",
                    createdAt=row["created_at"],
                ))

            return summaries

        except Exception as e:
            logger.error(f"Error fetching report summaries: {e}")
            return []


# Singleton instance
reports_local_storage = ReportsLocalStorage()
