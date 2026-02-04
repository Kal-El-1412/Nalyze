import os
import json
import logging
from typing import Union, Dict, Any
from openai import OpenAI
from app.storage import storage
from app.ingest_pipeline import ingestion_pipeline
from app.sql_validator import sql_validator
from app.state import state_manager
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

SYSTEM_PROMPT = """You are a privacy-first data analysis assistant that helps users explore their datasets through natural language.

## Your Responsibilities
- Analyze user questions and generate safe DuckDB SQL queries
- Summarize query results in clear, user-friendly language
- NEVER expose raw data rows unless explicitly aggregated
- NEVER ask clarifying questions - all context is provided by the backend

## CRITICAL: No Clarification Questions
- DO NOT ask the user for clarification
- DO NOT use the "needs_clarification" response type
- All required context (analysis type, time period, etc.) is provided by the backend
- You have all the information needed to generate queries
- If something seems ambiguous, make reasonable assumptions based on schema

## Data Privacy Rules (CRITICAL)
- You receive ONLY schema and statistics, never raw row data
- When user asks questions, you receive aggregated results only
- You must NEVER request or expect to see individual row details
- All queries must aggregate, count, or summarize data
- Treat all data as potentially sensitive

## SQL Generation Rules (MANDATORY)
1. ALWAYS include LIMIT clause (max 10000 rows)
2. Use ONLY SELECT statements - never DROP, DELETE, INSERT, UPDATE, etc.
3. Reference the table as "data" (this is the ingested dataset)
4. Use DuckDB-compatible SQL syntax
5. Prefer aggregations: COUNT, SUM, AVG, MIN, MAX, GROUP BY
6. For date analysis: Use DATE_TRUNC('month', column_name) or similar
7. Always validate column names against the schema provided
8. Use double quotes for column names with spaces or special characters
9. If multiple date columns exist, use the first detected date column
10. If multiple numeric columns exist, analyze all relevant ones

## Response Format
You must respond with valid JSON matching one of these types:

### 1. run_queries
When you can generate SQL to answer the question:
{
  "type": "run_queries",
  "queries": [
    {
      "name": "monthly_trends",
      "sql": "SELECT DATE_TRUNC('month', order_date) as month, COUNT(*) as order_count, SUM(total) as revenue FROM data GROUP BY month ORDER BY month LIMIT 1000"
    }
  ],
  "explanation": "I'll analyze your monthly trends by grouping orders by month and calculating the total count and revenue."
}

### 2. final_answer
When you have results to summarize:
{
  "type": "final_answer",
  "message": "Based on the results, you had 1,250 orders in January with $45,320 in revenue. February showed a 15% increase with 1,437 orders totaling $52,100.",
  "tables": [
    {
      "title": "Monthly Summary",
      "columns": ["month", "orders", "revenue"],
      "rows": [["2024-01", 1250, 45320], ["2024-02", 1437, 52100]]
    }
  ]
}

## Handling Ambiguity

**Multiple Date Columns:**
- Use the first detected date column or the most logical one for the question
- If user says "trends", assume they want time-based analysis with that column

**Multiple Metrics:**
- If user asks "what's trending", analyze all relevant numeric columns
- Show the most important metrics first

**Vague Requests:**
- "Show me the data" → Generate summary statistics (COUNT, SUM, AVG, MIN, MAX)
- "Analyze this" → Show key metrics and trends
- Make reasonable assumptions based on schema and column names

**Complex Analysis:**
- Break into multiple queries if needed (max 3)
- Each query should have a clear, descriptive name

## Example Interactions

User: "Show me monthly sales"
Schema: columns include "sale_date" (date) and "amount" (numeric)
Response:
{
  "type": "run_queries",
  "queries": [{
    "name": "monthly_sales",
    "sql": "SELECT DATE_TRUNC('month', sale_date) as month, COUNT(*) as transaction_count, SUM(amount) as total_sales FROM data GROUP BY month ORDER BY month LIMIT 1000",
    "reasoning": "Monthly aggregation of sales data"
  }],
  "explanation": "I'll show you the monthly sales totals and transaction counts."
}

User: "Show me the data"
Schema: columns include "order_date" (date), "amount" (numeric), "status" (text)
Response:
{
  "type": "run_queries",
  "queries": [{
    "name": "data_summary",
    "sql": "SELECT COUNT(*) as total_orders, SUM(amount) as total_revenue, COUNT(DISTINCT status) as unique_statuses, MIN(order_date) as earliest_date, MAX(order_date) as latest_date FROM data LIMIT 1",
    "reasoning": "Summary statistics for dataset overview"
  }],
  "explanation": "I'll show you a summary of your data including total orders, revenue, and date range."
}

Remember: You are helping users understand their data safely and privately. Always aggregate, never expose raw rows. NEVER ask clarification questions - make informed decisions based on the schema."""


class ChatOrchestrator:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)

    async def process(
        self, request: ChatOrchestratorRequest
    ) -> Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse]:
        if not self.openai_api_key or not self.client:
            logger.error("OPENAI_API_KEY not configured")
            return NeedsClarificationResponse(
                question="OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable.",
                choices=["Contact administrator"]
            )

        if not request.message:
            logger.error("Message is required for LLM processing")
            return NeedsClarificationResponse(
                question="Please provide a message to process.",
                choices=["Try again"]
            )

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

        try:
            catalog = await ingestion_pipeline.load_catalog(request.datasetId)
        except FileNotFoundError:
            return NeedsClarificationResponse(
                question="Dataset catalog not found. Please run ingestion first.",
                choices=["Run ingestion"]
            )

        try:
            return await self._call_openai(request, catalog)
        except Exception as e:
            logger.error(f"OpenAI orchestration error: {e}", exc_info=True)
            return NeedsClarificationResponse(
                question=f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question.",
                choices=["Try again", "View dataset info"]
            )

    async def _call_openai(
        self, request: ChatOrchestratorRequest, catalog: Any
    ) -> Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse]:
        messages = self._build_messages(request, catalog)

        logger.info("Calling OpenAI API...")
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )

        response_text = response.choices[0].message.content
        logger.info(f"OpenAI response: {response_text[:200]}...")

        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise ValueError("Invalid response format from AI")

        return self._parse_response(response_data)

    def _build_messages(self, request: ChatOrchestratorRequest, catalog: Any) -> list:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation state context
        state = state_manager.get_state(request.conversationId)
        context = state.get("context", {})
        if context:
            context_info = self._build_context_info(context)
            messages.append({
                "role": "system",
                "content": f"User Preferences:\n{context_info}"
            })

        catalog_info = self._build_catalog_context(catalog)
        messages.append({
            "role": "system",
            "content": f"Dataset Schema:\n{catalog_info}"
        })

        if request.resultsContext:
            results_summary = self._build_results_context(request.resultsContext)
            messages.append({
                "role": "system",
                "content": f"Query Results (aggregated):\n{results_summary}"
            })

        messages.append({
            "role": "user",
            "content": request.message
        })

        return messages

    def _build_context_info(self, context: Dict[str, Any]) -> str:
        """Build a summary of user preferences from conversation state"""
        lines = []

        if "analysis_type" in context:
            lines.append(f"Analysis Type: {context['analysis_type']}")

        if "time_period" in context:
            lines.append(f"Time Period: {context['time_period']}")

        if "metric" in context:
            lines.append(f"Preferred Metric: {context['metric']}")

        if "dimension" in context:
            lines.append(f"Dimension: {context['dimension']}")

        if "grouping" in context:
            lines.append(f"Grouping: {context['grouping']}")

        # Add any other context fields
        for key, value in context.items():
            if key not in ["analysis_type", "time_period", "metric", "dimension", "grouping"]:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return "\n".join(lines) if lines else "No specific preferences set"

    def _build_catalog_context(self, catalog: Any) -> str:
        lines = [
            f"Table: data",
            f"Total Rows: {catalog.rowCount:,}",
            f"Total Columns: {len(catalog.columns)}",
            "",
            "Columns:"
        ]

        for col in catalog.columns:
            col_info = f"  - {col.name} ({col.type})"
            if col.nullable:
                col_info += " [nullable]"
            lines.append(col_info)

        if catalog.detectedDateColumns:
            lines.append("")
            lines.append(f"Date Columns: {', '.join(catalog.detectedDateColumns)}")

        if catalog.detectedNumericColumns:
            lines.append(f"Numeric Columns: {', '.join(catalog.detectedNumericColumns)}")

        if catalog.summary:
            lines.append("")
            lines.append("Column Statistics:")
            for col_name, stats in catalog.summary.items():
                if isinstance(stats, dict):
                    stat_parts = []
                    if "count" in stats:
                        stat_parts.append(f"count={stats['count']}")
                    if "unique" in stats:
                        stat_parts.append(f"unique={stats['unique']}")
                    if "min" in stats:
                        stat_parts.append(f"min={stats['min']}")
                    if "max" in stats:
                        stat_parts.append(f"max={stats['max']}")
                    if "mean" in stats:
                        stat_parts.append(f"mean={stats['mean']:.2f}")
                    if stat_parts:
                        lines.append(f"  {col_name}: {', '.join(stat_parts)}")

        return "\n".join(lines)

    def _build_results_context(self, results_context: Any) -> str:
        lines = ["Previous query results (aggregated):"]

        for result in results_context.results:
            lines.append(f"\n{result.name}:")
            lines.append(f"  Columns: {', '.join(result.columns)}")
            lines.append(f"  Rows returned: {len(result.rows)}")

            if result.rows:
                lines.append("  Sample data:")
                for i, row in enumerate(result.rows[:5]):
                    lines.append(f"    {row}")
                if len(result.rows) > 5:
                    lines.append(f"    ... ({len(result.rows) - 5} more rows)")

        return "\n".join(lines)

    def _parse_response(
        self, response_data: Dict[str, Any]
    ) -> Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse]:
        response_type = response_data.get("type")

        if response_type == "needs_clarification":
            # LLM should NEVER ask for clarification - this is a prompt violation
            logger.error(f"LLM attempted to ask clarification question: {response_data.get('question')}")
            raise ValueError(
                "LLM attempted to ask a clarification question. "
                "All clarifications should be handled by backend state checks. "
                "This indicates the LLM prompt needs updating or the LLM is not following instructions."
            )

        elif response_type == "run_queries":
            queries = response_data.get("queries", [])

            valid, error = sql_validator.validate_queries(queries)
            if not valid:
                logger.warning(f"SQL validation failed: {error}")
                return NeedsClarificationResponse(
                    question=f"I generated an invalid query: {error}. Let me try again - could you rephrase your question?",
                    choices=["Rephrase question", "View dataset info"]
                )

            query_objects = [
                QueryToRun(name=q["name"], sql=q["sql"])
                for q in queries
            ]

            return RunQueriesResponse(
                queries=query_objects,
                explanation=response_data.get("explanation", "Running queries..."),
                audit=AuditInfo(sharedWithAI=["schema", "aggregates_only"])
            )

        elif response_type == "final_answer":
            tables = None
            if "tables" in response_data and response_data["tables"]:
                tables = [
                    TableData(
                        title=t["title"],
                        columns=t["columns"],
                        rows=t["rows"]
                    )
                    for t in response_data["tables"]
                ]

            return FinalAnswerResponse(
                message=response_data.get("message", "Analysis complete."),
                tables=tables,
                audit=AuditInfo(sharedWithAI=["schema", "aggregates_only"])
            )

        else:
            logger.error(f"Unknown response type: {response_type}")
            raise ValueError(f"Unknown response type: {response_type}")


chat_orchestrator = ChatOrchestrator()
