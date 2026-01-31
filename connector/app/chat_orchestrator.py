import logging
from typing import Union, List
from app.storage import storage
from app.ingest_pipeline import ingestion_pipeline
from app.models import (
    ChatOrchestratorRequest,
    NeedsClarificationResponse,
    RunQueriesResponse,
    FinalAnswerResponse,
    QueryToRun,
    TableData,
    AuditInfo
)

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """MVP orchestrator stub that handles chat protocol without calling OpenAI"""

    async def process(
        self, request: ChatOrchestratorRequest
    ) -> Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse]:
        logger.info(
            f"Processing chat request for dataset {request.datasetId}, "
            f"conversation {request.conversationId}, message: {request.message[:50]}..."
        )

        dataset = await storage.get_dataset(request.datasetId)
        if not dataset:
            return NeedsClarificationResponse(
                question="Dataset not found. Please register the dataset first.",
                choices=["Go to datasets"]
            )

        if dataset["status"] != "ingested":
            return NeedsClarificationResponse(
                question="Dataset is not ingested yet. Run ingestion now?",
                choices=["Ingest now"]
            )

        if request.resultsContext:
            return await self._handle_results_context(request)

        if self._is_trend_query(request.message):
            return await self._handle_trend_query(request)

        return NeedsClarificationResponse(
            question="I can help you analyze trends in your data. What would you like to explore?",
            choices=["Show monthly trends", "Show aggregated data", "View data summary"]
        )

    def _is_trend_query(self, message: str) -> bool:
        message_lower = message.lower()
        trend_keywords = ["monthly", "trend", "time", "over time", "by month", "by date"]
        return any(keyword in message_lower for keyword in trend_keywords)

    async def _handle_trend_query(
        self, request: ChatOrchestratorRequest
    ) -> Union[NeedsClarificationResponse, RunQueriesResponse]:
        try:
            catalog = await ingestion_pipeline.load_catalog(request.datasetId)
        except FileNotFoundError:
            return NeedsClarificationResponse(
                question="Dataset catalog not found. Please run ingestion first.",
                choices=["Run ingestion"]
            )

        date_columns = catalog.detectedDateColumns
        numeric_columns = catalog.detectedNumericColumns

        if not date_columns:
            all_columns = [col.name for col in catalog.columns]
            return NeedsClarificationResponse(
                question="Which column contains the date/time information?",
                choices=all_columns[:10]
            )

        if not numeric_columns:
            all_columns = [col.name for col in catalog.columns]
            return NeedsClarificationResponse(
                question="Which column contains the metric you want to analyze?",
                choices=all_columns[:10]
            )

        date_col = date_columns[0]
        numeric_col = numeric_columns[0]

        queries = [
            QueryToRun(
                name="monthly_trend",
                sql=f"""
                SELECT
                    DATE_TRUNC('month', "{date_col}") as month,
                    COUNT(*) as record_count,
                    SUM("{numeric_col}") as total_{numeric_col},
                    AVG("{numeric_col}") as avg_{numeric_col}
                FROM data
                GROUP BY DATE_TRUNC('month', "{date_col}")
                ORDER BY month
                """
            )
        ]

        return RunQueriesResponse(
            queries=queries,
            explanation=f"I'll analyze the monthly trends in your data using the '{date_col}' column for time and '{numeric_col}' column for metrics.",
            audit=AuditInfo(sharedWithAI=["schema", "aggregates_only"])
        )

    async def _handle_results_context(
        self, request: ChatOrchestratorRequest
    ) -> FinalAnswerResponse:
        results = request.resultsContext.results

        total_results = len(results)
        message_parts = [f"I found {total_results} result{'s' if total_results != 1 else ''}:"]

        tables = []

        for result in results:
            row_count = len(result.rows)
            message_parts.append(f"\n**{result.name}**: {row_count} row{'s' if row_count != 1 else ''} returned")

            preview_rows = result.rows[:5]
            tables.append(
                TableData(
                    title=result.name,
                    columns=result.columns,
                    rows=preview_rows
                )
            )

            if row_count > 5:
                message_parts.append(f"  (showing first 5 of {row_count} rows)")

        message = "\n".join(message_parts)

        return FinalAnswerResponse(
            message=message,
            tables=tables,
            audit=AuditInfo(sharedWithAI=["schema", "aggregates_only"])
        )


chat_orchestrator = ChatOrchestrator()
