"""
Reports storage module for saving and retrieving analysis reports in Supabase
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.config import config
from app.models import Report, ReportSummary, FinalAnswerResponse, TableData

logger = logging.getLogger(__name__)


class ReportsStorage:
    """Handles saving and retrieving reports from Supabase"""

    def __init__(self):
        self.supabase = config.supabase

    def save_report(
        self,
        dataset_id: str,
        dataset_name: str,
        conversation_id: str,
        question: str,
        final_answer: FinalAnswerResponse,
    ) -> Optional[str]:
        """
        Save a report to Supabase

        Args:
            dataset_id: Dataset ID
            dataset_name: Dataset name
            conversation_id: Conversation ID
            question: The original question asked
            final_answer: The final_answer response to save

        Returns:
            Report ID (uuid) if successful, None otherwise
        """
        if not self.supabase:
            logger.warning("Supabase client not initialized, cannot save report")
            return None

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

            # Insert report into Supabase
            result = self.supabase.table("reports").insert({
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
            }).execute()

            if result.data:
                logger.info(f"Saved report {report_id} for dataset {dataset_id}")
                return report_id
            else:
                logger.error("Failed to save report: no data returned")
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
        if not self.supabase:
            logger.warning("Supabase client not initialized, cannot fetch reports")
            return []

        try:
            query = self.supabase.table("reports").select("*")

            if dataset_id:
                query = query.eq("dataset_id", dataset_id)

            result = query.order("created_at", desc=True).limit(limit).execute()

            if result.data:
                reports = []
                for row in result.data:
                    reports.append(Report(
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
                return reports

            return []

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
        if not self.supabase:
            logger.warning("Supabase client not initialized, cannot fetch report")
            return None

        try:
            result = self.supabase.table("reports").select("*").eq("id", report_id).maybe_single().execute()

            if result.data:
                row = result.data
                return Report(
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
                )

            return None

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
        if not self.supabase:
            logger.warning("Supabase client not initialized, cannot fetch report summaries")
            return []

        try:
            query = self.supabase.table("reports").select(
                "id, question, analysis_type, dataset_id, dataset_name, created_at"
            )

            if dataset_id:
                query = query.eq("dataset_id", dataset_id)

            result = query.order("created_at", desc=True).limit(limit).execute()

            if result.data:
                summaries = []
                for row in result.data:
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

            return []

        except Exception as e:
            logger.error(f"Error fetching report summaries: {e}")
            return []


reports_storage = ReportsStorage()
