import os
import json
import logging
from typing import Union, Dict, Any
from openai import OpenAI
from app.config import config
from app.storage import storage
from app.ingest_pipeline import ingestion_pipeline
from app.sql_validator import sql_validator
from app.state import state_manager
from app.pii_redactor import pii_redactor
from app.models import (
    ChatOrchestratorRequest,
    NeedsClarificationResponse,
    RunQueriesResponse,
    FinalAnswerResponse,
    QueryToRun,
    TableData,
    AuditInfo,
    RoutingMetadata,
    IntentAcknowledgmentResponse
)
from app.router import deterministic_router

logger = logging.getLogger(__name__)

INTENT_EXTRACTION_PROMPT = """You are an intent classifier for data analysis queries.

Your job is to extract structured information from user questions about their dataset.

CRITICAL: Return ONLY valid JSON. No markdown. No code blocks. No explanations.

## Analysis Types
Return ONE of these analysis types:
- trend: Time-based analysis (trends over time, monthly/weekly patterns)
- top_categories: Category breakdowns (top N, grouped by, distribution)
- outliers: Anomaly detection (outliers, unusual values, anomalies)
- row_count: Count records (how many rows, total records)
- data_quality: Data validation (missing values, nulls, duplicates)

## Required Output Format
Return ONLY this JSON structure:
{
  "analysis_type": "trend|top_categories|outliers|row_count|data_quality",
  "time_period": "last_7_days|last_30_days|last_90_days|all_time|unspecified",
  "metric": "column_name|unspecified",
  "group_by": "column_name|unspecified",
  "date_column": "column_name|unspecified"
}

## Field Rules
- If you cannot determine a field value, use "unspecified" (not null, not empty string)
- For metric: Use the actual column name from the schema, or "unspecified"
- For group_by: Use the actual column name from the schema, or "unspecified"
- For date_column: Use the first detected date column from schema, or "unspecified"
- For time_period: Map user terms to standard values:
  - "last week", "past week" → "last_7_days"
  - "last month", "past month", "last 30 days" → "last_30_days"
  - "last quarter", "past quarter", "last 90 days" → "last_90_days"
  - "all time", "everything", "entire dataset" → "all_time"
  - If not specified → "unspecified"

## Examples

Input: "What are the revenue trends over the last quarter?"
Output: {"analysis_type": "trend", "time_period": "last_90_days", "metric": "revenue", "group_by": "unspecified", "date_column": "order_date"}

Input: "Show me which products sold the most"
Output: {"analysis_type": "top_categories", "time_period": "unspecified", "metric": "sales", "group_by": "product", "date_column": "unspecified"}

Input: "Are there any unusual values in the data?"
Output: {"analysis_type": "outliers", "time_period": "unspecified", "metric": "unspecified", "group_by": "unspecified", "date_column": "unspecified"}

Input: "How many records do we have?"
Output: {"analysis_type": "row_count", "time_period": "unspecified", "metric": "unspecified", "group_by": "unspecified", "date_column": "unspecified"}

Input: "Check if there are missing values"
Output: {"analysis_type": "data_quality", "time_period": "unspecified", "metric": "unspecified", "group_by": "unspecified", "date_column": "unspecified"}

Input: "Show me weekly sales for the last month"
Output: {"analysis_type": "trend", "time_period": "last_30_days", "metric": "sales", "group_by": "unspecified", "date_column": "sale_date"}

CRITICAL: Return ONLY valid JSON. No markdown. No explanations. Just the JSON object.
"""

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
- **PII PROTECTION (Privacy Mode)**: When privacy mode is enabled, PII columns are redacted:
  - PII column names are replaced with placeholders (PII_EMAIL_1, PII_PHONE_1, PII_NAME_1, etc.)
  - You should NOT reference or query these redacted columns
  - You will NEVER see PII values - only aggregated statistics
  - Focus on non-PII columns for analysis
  - If user asks about personal data, explain that privacy mode prevents access to PII

## Safe Mode Rules (MANDATORY WHEN ENABLED)
When Safe Mode is ON, you MUST follow these additional rules:
- **ONLY AGGREGATED QUERIES**: Every query must use aggregate functions (COUNT, SUM, AVG, MIN, MAX) or GROUP BY
- **NO RAW ROWS**: You cannot generate queries that return individual rows like "SELECT * FROM data LIMIT 10"
- **AGGREGATION REQUIRED**: Even simple queries must aggregate, e.g., "SELECT COUNT(*) FROM data" instead of "SELECT * FROM data"
- **GROUP BY COUNTS**: For category analysis, use "SELECT category, COUNT(*) FROM data GROUP BY category"
- **Statistical ONLY**: Focus on statistics, counts, averages, sums, minimums, and maximums
- Safe Mode protects against accidental exposure of individual records
- If user asks for raw data when Safe Mode is ON, explain that only aggregated results are available

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
CRITICAL: Return ONLY valid JSON. No markdown. No code blocks. No explanations outside the JSON.

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
        self.ai_mode = config.ai_mode
        self.openai_api_key = config.openai_api_key
        self.client = None
        if self.ai_mode and self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)

    def _create_routing_metadata(
        self,
        routing_decision: str,
        deterministic_confidence: float = None,
        deterministic_match: str = None,
        openai_invoked: bool = False,
        safe_mode: bool = False,
        privacy_mode: bool = True
    ) -> RoutingMetadata:
        """Create routing metadata for diagnostic purposes"""
        return RoutingMetadata(
            routing_decision=routing_decision,
            deterministic_confidence=deterministic_confidence,
            deterministic_match=deterministic_match,
            openai_invoked=openai_invoked,
            safe_mode=safe_mode,
            privacy_mode=privacy_mode
        )

    async def process(
        self, request: ChatOrchestratorRequest
    ) -> Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse, IntentAcknowledgmentResponse]:
        logger.info(
            f"Processing chat request for dataset {request.datasetId}, "
            f"conversation {request.conversationId}, message: {request.message[:50] if request.message else 'None'}..."
        )

        dataset = await storage.get_dataset(request.datasetId)
        if not dataset:
            return NeedsClarificationResponse(
                question="Dataset not found. Please register the dataset first.",
                choices=["Go to datasets"]
            )

        try:
            catalog = await ingestion_pipeline.load_catalog(request.datasetId)
        except FileNotFoundError:
            catalog = None

        state = state_manager.get_state(request.conversationId)
        context = state.get("context", {})

        if self._is_state_ready(context):
            if request.resultsContext:
                return await self._generate_final_answer(request, catalog, context)
            else:
                return await self._generate_sql_plan(request, catalog, context)

        # Check if message provided
        if not request.message:
            logger.error("Message is required for processing")
            return NeedsClarificationResponse(
                question="Please provide a message to process.",
                choices=["Try again"]
            )

        # Check if AI Assist is enabled
        ai_assist = request.aiAssist if request.aiAssist is not None else False

        # Try deterministic routing first (regardless of aiAssist setting)
        logger.info(f"Trying deterministic router for message: '{request.message[:50]}...'")
        routing_result = deterministic_router.route_intent(request.message)
        analysis_type = routing_result.get("analysis_type")
        confidence = routing_result.get("confidence", 0.0)
        params = routing_result.get("params", {})

        logger.info(f"Deterministic router result: analysis_type={analysis_type}, confidence={confidence:.2f}")

        # If high confidence (>=0.8), use deterministic path (works regardless of aiAssist)
        if confidence >= 0.8 and analysis_type:
            logger.info(f"High confidence ({confidence:.2f}) - using deterministic path")

            # Update state with analysis_type
            state_manager.update_context(
                request.conversationId,
                {"analysis_type": analysis_type}
            )

            # If we extracted time_period from message, update state
            if "time_period" in params:
                state_manager.update_context(
                    request.conversationId,
                    {"time_period": params["time_period"]}
                )

            # Check if state is now ready
            updated_state = state_manager.get_state(request.conversationId)
            updated_context = updated_state.get("context", {})

            # State is ready (time_period is optional), generate SQL
            logger.info("State is ready after deterministic routing - generating SQL")
            result = await self._generate_sql_plan(request, catalog, updated_context)
            # Add routing metadata
            result.routing_metadata = self._create_routing_metadata(
                routing_decision="deterministic",
                deterministic_confidence=confidence,
                deterministic_match=analysis_type,
                openai_invoked=False,
                safe_mode=request.safeMode,
                privacy_mode=request.privacyMode
            )
            return result

        # Low/medium confidence (< 0.8) - need to handle based on aiAssist setting
        logger.info(f"Low/medium confidence ({confidence:.2f}) - need clarification or AI")

        if not ai_assist:
            # AI Assist is OFF - ask user to pick analysis type manually
            logger.info("AI Assist is OFF - asking user to choose analysis type")

            # Check if we've already asked for analysis type in this conversation
            if state_manager.has_asked_clarification(request.conversationId, "set_analysis_type"):
                logger.warning("Already asked for analysis_type - not asking again")
                # We already asked once, return helpful message
                return FinalAnswerResponse(
                    message="I'm not sure how to help with that. Try asking about trends, categories, outliers, row counts, or data quality. Or enable AI Assist for more flexible queries.",
                    tables=None
                )

            # Mark that we're asking for analysis_type
            state_manager.mark_clarification_asked(request.conversationId, "set_analysis_type")

            return NeedsClarificationResponse(
                question="What would you like to analyze?",
                choices=[
                    "Trends over time",
                    "Top categories",
                    "Find outliers",
                    "Count rows",
                    "Check data quality"
                ],
                intent="set_analysis_type",
                routing_metadata=self._create_routing_metadata(
                    routing_decision="clarification_needed",
                    deterministic_confidence=confidence,
                    deterministic_match=None,
                    openai_invoked=False,
                    safe_mode=request.safeMode,
                    privacy_mode=request.privacyMode
                )
            )

        # AI Assist is ON - use OpenAI intent extractor
        logger.info("AI Assist is ON - using OpenAI intent extractor")

        # Check if OpenAI API key is configured
        if not self.openai_api_key:
            logger.warning("AI Assist is ON but OPENAI_API_KEY is not configured")
            return FinalAnswerResponse(
                message="AI Assist is ON but no API key is configured. Set OPENAI_API_KEY in .env or turn AI Assist off.",
                tables=None
            )

        # Validate AI mode is properly configured
        is_valid, error_message = config.validate_ai_mode_for_request()
        if not is_valid:
            logger.error(f"AI validation failed: {error_message}")
            return NeedsClarificationResponse(
                question=error_message,
                choices=["Contact administrator"]
            )

        if dataset["status"] != "ingested":
            return NeedsClarificationResponse(
                question="Dataset is not ingested yet. Run ingestion now?",
                choices=["Ingest now"]
            )

        if not catalog:
            return NeedsClarificationResponse(
                question="Dataset catalog not found. Please run ingestion first.",
                choices=["Run ingestion"]
            )

        try:
            # Extract intent with OpenAI
            intent_data = await self._extract_intent_with_openai(request, catalog)

            # Update conversation state with extracted intent
            extracted_fields = {}
            if "analysis_type" in intent_data and intent_data["analysis_type"]:
                extracted_fields["analysis_type"] = intent_data["analysis_type"]

            if "time_period" in intent_data and intent_data["time_period"]:
                extracted_fields["time_period"] = intent_data["time_period"]

            if "metric" in intent_data and intent_data["metric"]:
                extracted_fields["metric"] = intent_data["metric"]

            if "group_by" in intent_data and intent_data["group_by"]:
                extracted_fields["grouping"] = intent_data["group_by"]

            if "notes" in intent_data and intent_data["notes"]:
                extracted_fields["notes"] = intent_data["notes"]

            logger.info(f"Updating state with extracted fields: {extracted_fields}")
            state_manager.update_context(request.conversationId, extracted_fields)

            # Check if state is now ready
            updated_state = state_manager.get_state(request.conversationId)
            updated_context = updated_state.get("context", {})

            # State is ready (time_period is optional), generate SQL
            logger.info("State is ready after intent extraction - generating SQL")
            result = await self._generate_sql_plan(request, catalog, updated_context)
            # Add routing metadata
            result.routing_metadata = self._create_routing_metadata(
                routing_decision="ai_intent_extraction",
                deterministic_confidence=None,
                deterministic_match=None,
                openai_invoked=True,
                safe_mode=request.safeMode,
                privacy_mode=request.privacyMode
            )
            return result

        except Exception as e:
            logger.error(f"Intent extraction error: {e}", exc_info=True)
            return NeedsClarificationResponse(
                question=f"I had trouble understanding your request: {str(e)}. Could you rephrase your question?",
                choices=["Try again", "View dataset info"]
            )

    def _is_state_ready(self, context: Dict[str, Any]) -> bool:
        """Check if conversation state has required fields for SQL generation"""
        analysis_type = context.get("analysis_type")
        # time_period is optional in v1
        return analysis_type is not None

    async def _generate_sql_plan(
        self, request: ChatOrchestratorRequest, catalog: Any, context: Dict[str, Any]
    ) -> RunQueriesResponse:
        """Generate SQL queries based on analysis type without calling LLM"""
        analysis_type = context.get("analysis_type")
        time_period = context.get("time_period") or "all_time"
        context["time_period"] = time_period
        privacy_mode = request.privacyMode if request.privacyMode is not None else True
        safe_mode = request.safeMode if request.safeMode is not None else False

        logger.info(f"Generating SQL plan for analysis_type={analysis_type}, time_period={time_period}, privacyMode={privacy_mode}, safeMode={safe_mode}")

        working_catalog = catalog
        audit_shared = ["schema", "aggregates_only"]

        if privacy_mode and catalog:
            working_catalog, _ = pii_redactor.redact_catalog(catalog, privacy_mode)
            audit_shared.append("PII_redacted")

        if safe_mode:
            audit_shared.append("safe_mode_no_raw_rows")

        queries = []

        if analysis_type == "row_count":
            queries.append({
                "name": "row_count",
                "sql": "SELECT COUNT(*) as row_count FROM data"
            })
            explanation = f"I'll count the total rows in your dataset for the {time_period} period."

        elif analysis_type == "top_categories":
            if working_catalog:
                categorical_col = self._detect_best_categorical_column(working_catalog)
                if categorical_col:
                    queries.append({
                        "name": "top_categories",
                        "sql": f'SELECT "{categorical_col}", COUNT(*) as count FROM data GROUP BY "{categorical_col}" ORDER BY count DESC LIMIT 10'
                    })
                    explanation = f"I'll show you the top 10 categories in the {categorical_col} column for the {time_period} period."
                else:
                    queries.append({
                        "name": "row_count",
                        "sql": "SELECT COUNT(*) as row_count FROM data"
                    })
                    explanation = f"I couldn't find a categorical column, so I'll show you the total row count for the {time_period} period."
            else:
                queries.append({
                    "name": "discover_columns",
                    "sql": "SELECT * FROM data LIMIT 1"
                })
                explanation = f"I'll first discover the columns in your dataset, then show you the top categories for the {time_period} period."

        elif analysis_type == "trend":
            if working_catalog:
                date_col = self._detect_date_column(working_catalog)
                metric_col = self._detect_metric_column(working_catalog)

                if date_col and metric_col:
                    queries.append({
                        "name": "monthly_trend",
                        "sql": f'''SELECT
                            DATE_TRUNC('month', "{date_col}") as month,
                            COUNT(*) as count,
                            SUM("{metric_col}") as total_{metric_col},
                            AVG("{metric_col}") as avg_{metric_col}
                        FROM data
                        GROUP BY month
                        ORDER BY month
                        LIMIT 200'''
                    })
                    explanation = f"I'll analyze the trend of {metric_col} over time by month for the {time_period} period."
                elif date_col:
                    queries.append({
                        "name": "monthly_count",
                        "sql": f'''SELECT
                            DATE_TRUNC('month', "{date_col}") as month,
                            COUNT(*) as count
                        FROM data
                        GROUP BY month
                        ORDER BY month
                        LIMIT 200'''
                    })
                    explanation = f"I'll show you the monthly trend for the {time_period} period."
                else:
                    queries.append({
                        "name": "row_count",
                        "sql": "SELECT COUNT(*) as row_count FROM data"
                    })
                    explanation = f"I couldn't find date columns for trending, so I'll show you the total row count for the {time_period} period."
            else:
                queries.append({
                    "name": "discover_columns",
                    "sql": "SELECT * FROM data LIMIT 1"
                })
                explanation = f"I'll first discover the columns in your dataset, then show you the trends for the {time_period} period."

        elif analysis_type == "outliers":
            if working_catalog:
                numeric_cols = self._detect_all_numeric_columns(working_catalog)
                if numeric_cols:
                    if safe_mode:
                        # Safe mode: return aggregated outlier counts per column
                        count_selects = []
                        for col in numeric_cols[:10]:  # Limit to 10 columns
                            count_selects.append(f"""
                                SELECT
                                    '{col}' as column_name,
                                    COUNT(*) as outlier_count,
                                    AVG("{col}") as mean_value,
                                    STDDEV("{col}") as stddev_value,
                                    MIN("{col}") as min_value,
                                    MAX("{col}") as max_value
                                FROM data
                                WHERE "{col}" IS NOT NULL
                                  AND ABS("{col}" - (SELECT AVG("{col}") FROM data WHERE "{col}" IS NOT NULL))
                                      > 2 * (SELECT STDDEV("{col}") FROM data WHERE "{col}" IS NOT NULL)
                            """)

                        union_sql = " UNION ALL ".join(count_selects)
                        queries.append({
                            "name": "outlier_summary",
                            "sql": union_sql
                        })
                        explanation = f"I'll analyze outliers (>2 std dev) across {len(numeric_cols)} numeric columns for the {time_period} period. Safe mode: showing aggregated counts only."

                    else:
                        # Regular mode: return individual outlier rows
                        # Use UNION ALL to combine outliers from all columns
                        outlier_selects = []
                        for col in numeric_cols[:10]:  # Limit to 10 columns
                            outlier_selects.append(f"""
                                SELECT
                                    '{col}' as column_name,
                                    "{col}" as value,
                                    (SELECT AVG("{col}") FROM data WHERE "{col}" IS NOT NULL) as mean_value,
                                    (SELECT STDDEV("{col}") FROM data WHERE "{col}" IS NOT NULL) as stddev_value,
                                    ("{col}" - (SELECT AVG("{col}") FROM data WHERE "{col}" IS NOT NULL))
                                        / (SELECT STDDEV("{col}") FROM data WHERE "{col}" IS NOT NULL) as z_score,
                                    ROW_NUMBER() OVER () as row_index
                                FROM data
                                WHERE "{col}" IS NOT NULL
                                  AND ABS("{col}" - (SELECT AVG("{col}") FROM data WHERE "{col}" IS NOT NULL))
                                      > 2 * (SELECT STDDEV("{col}") FROM data WHERE "{col}" IS NOT NULL)
                                LIMIT 50
                            """)

                        union_sql = " UNION ALL ".join(outlier_selects)
                        queries.append({
                            "name": "outliers_detected",
                            "sql": union_sql
                        })
                        explanation = f"I'll detect outliers beyond 2 standard deviations across {len(numeric_cols)} numeric columns for the {time_period} period."
                else:
                    queries.append({
                        "name": "row_count",
                        "sql": "SELECT COUNT(*) as row_count FROM data"
                    })
                    explanation = f"I couldn't find numeric columns for outlier detection, so I'll show you the total row count for the {time_period} period."
            else:
                queries.append({
                    "name": "discover_columns",
                    "sql": "SELECT * FROM data LIMIT 1"
                })
                explanation = f"I'll first discover the columns in your dataset, then check for outliers for the {time_period} period."

        elif analysis_type == "data_quality":
            if working_catalog:
                all_columns = []
                if working_catalog.get("tables") and len(working_catalog["tables"]) > 0:
                    all_columns = working_catalog["tables"][0].get("columns", [])

                if all_columns:
                    # Count nulls for each column
                    null_checks = ", ".join([f'SUM(CASE WHEN "{col}" IS NULL THEN 1 ELSE 0 END) as "{col}_nulls"' for col in all_columns[:10]])
                    queries.append({
                        "name": "null_counts",
                        "sql": f"SELECT COUNT(*) as total_rows, {null_checks} FROM data"
                    })
                    queries.append({
                        "name": "duplicate_check",
                        "sql": "SELECT COUNT(*) as total_rows, COUNT(DISTINCT *) as unique_rows FROM data"
                    })
                    explanation = f"I'll check data quality including null values and duplicates."
                else:
                    queries.append({
                        "name": "basic_stats",
                        "sql": "SELECT COUNT(*) as row_count FROM data"
                    })
                    explanation = f"I'll provide basic data quality statistics."
            else:
                queries.append({
                    "name": "discover_columns",
                    "sql": "SELECT * FROM data LIMIT 1"
                })
                explanation = f"I'll first discover the columns in your dataset, then check data quality."

        else:
            queries.append({
                "name": "row_count",
                "sql": "SELECT COUNT(*) as row_count FROM data"
            })
            explanation = f"I'll analyze your data for the {time_period} period."

        query_objects = [QueryToRun(name=q["name"], sql=q["sql"]) for q in queries]

        return RunQueriesResponse(
            queries=query_objects,
            explanation=explanation,
            audit=AuditInfo(sharedWithAI=audit_shared)
        )

    async def _generate_final_answer(
        self, request: ChatOrchestratorRequest, catalog: Any, context: Dict[str, Any]
    ) -> FinalAnswerResponse:
        """Generate final answer from query results"""
        privacy_mode = request.privacyMode if request.privacyMode is not None else True
        safe_mode = request.safeMode if request.safeMode is not None else False
        audit_shared = ["schema", "aggregates_only"]

        if privacy_mode and catalog:
            audit_shared.append("PII_redacted")

        if safe_mode:
            audit_shared.append("safe_mode_no_raw_rows")

        if not request.resultsContext or not request.resultsContext.results:
            return FinalAnswerResponse(
                message="No results to analyze.",
                tables=None,
                audit=AuditInfo(sharedWithAI=audit_shared)
            )

        results = request.resultsContext.results
        analysis_type = context.get("analysis_type", "analysis")
        time_period = context.get("time_period") or "all_time"
        context["time_period"] = time_period

        message_parts = [f"Here are your {analysis_type} results for {time_period}:"]
        tables = []

        for result in results:
            if result.rows:
                row_count = len(result.rows)

                if analysis_type == "row_count":
                    total = result.rows[0][0] if result.rows and len(result.rows[0]) > 0 else 0
                    message_parts.append(f"\n**Total rows:** {total:,}")

                elif analysis_type == "top_categories":
                    message_parts.append(f"\n**Top categories:** Found {row_count} categories.")
                    tables.append(TableData(
                        title=f"Top {row_count} Categories",
                        columns=result.columns,
                        rows=result.rows
                    ))

                elif analysis_type == "trend":
                    message_parts.append(f"\n**Trend analysis:** {row_count} data points.")
                    tables.append(TableData(
                        title="Monthly Trend",
                        columns=result.columns,
                        rows=result.rows
                    ))

                elif analysis_type == "outliers":
                    if result.name == "outlier_summary":
                        # Safe mode: aggregated outlier counts
                        message_parts.append(f"\n**Outlier Summary (Safe Mode - Aggregated Counts):**")
                        if result.rows:
                            total_outliers = sum(row[1] for row in result.rows if len(row) > 1 and row[1])
                            cols_with_outliers = sum(1 for row in result.rows if len(row) > 1 and row[1] and row[1] > 0)
                            message_parts.append(f"- Total outliers detected: {total_outliers:,}")
                            message_parts.append(f"- Columns with outliers: {cols_with_outliers}")
                            message_parts.append(f"- Detection threshold: >2 standard deviations from mean")

                        tables.append(TableData(
                            title="Outlier Summary by Column",
                            columns=result.columns,
                            rows=result.rows
                        ))

                    elif result.name == "outliers_detected":
                        # Regular mode: individual outlier rows
                        message_parts.append(f"\n**Outliers Detected (>2 Std Dev):**")
                        if result.rows:
                            outlier_count = len(result.rows)
                            unique_columns = len(set(row[0] for row in result.rows if len(row) > 0))
                            message_parts.append(f"- Total outlier values: {outlier_count}")
                            message_parts.append(f"- Columns analyzed: {unique_columns}")
                            message_parts.append(f"- Showing detailed outlier rows with z-scores")

                        tables.append(TableData(
                            title="Outlier Details",
                            columns=result.columns,
                            rows=result.rows[:200]  # Limit display to 200 rows
                        ))

                    else:
                        # Fallback for any other outlier-related results
                        tables.append(TableData(
                            title=result.name.replace("_", " ").title(),
                            columns=result.columns,
                            rows=result.rows
                        ))

                elif analysis_type == "data_quality":
                    if result.name == "null_counts":
                        message_parts.append(f"\n**Data Quality Check:**")
                        if result.rows and len(result.rows) > 0:
                            row = result.rows[0]
                            total = row[0] if len(row) > 0 else 0
                            message_parts.append(f"- Total rows: {total:,}")

                            # Count columns with nulls
                            null_cols = 0
                            for i in range(1, len(row)):
                                if row[i] and row[i] > 0:
                                    null_cols += 1

                            if null_cols > 0:
                                message_parts.append(f"- Columns with null values: {null_cols}")
                            else:
                                message_parts.append(f"- No null values detected")

                    elif result.name == "duplicate_check":
                        if result.rows and len(result.rows) > 0:
                            row = result.rows[0]
                            total = row[0] if len(row) > 0 else 0
                            unique = row[1] if len(row) > 1 else 0
                            duplicates = total - unique if total > unique else 0
                            message_parts.append(f"- Duplicate rows: {duplicates:,}")

                    tables.append(TableData(
                        title=result.name.replace("_", " ").title(),
                        columns=result.columns,
                        rows=result.rows
                    ))

                else:
                    tables.append(TableData(
                        title=result.name,
                        columns=result.columns,
                        rows=result.rows
                    ))

        return FinalAnswerResponse(
            message="\n".join(message_parts),
            tables=tables if tables else None,
            audit=AuditInfo(sharedWithAI=audit_shared)
        )

    def _detect_best_categorical_column(self, catalog: Any) -> str:
        """Detect best categorical column from catalog"""
        if not catalog or not catalog.columns:
            return None

        for col in catalog.columns:
            col_type = col.type.upper()
            if col_type in ["VARCHAR", "TEXT", "STRING", "CHAR"]:
                if catalog.summary and col.name in catalog.summary:
                    stats = catalog.summary[col.name]
                    if isinstance(stats, dict):
                        unique = stats.get("unique", 0)
                        count = stats.get("count", 0)
                        if count > 0 and unique > 1 and unique < count * 0.5:
                            return col.name

        for col in catalog.columns:
            col_type = col.type.upper()
            if col_type in ["VARCHAR", "TEXT", "STRING", "CHAR"]:
                return col.name

        return None

    def _detect_date_column(self, catalog: Any) -> str:
        """Detect first date column from catalog"""
        if not catalog:
            return None

        if catalog.detectedDateColumns and len(catalog.detectedDateColumns) > 0:
            return catalog.detectedDateColumns[0]

        for col in catalog.columns:
            col_type = col.type.upper()
            if "DATE" in col_type or "TIME" in col_type:
                return col.name

        return None

    def _detect_metric_column(self, catalog: Any) -> str:
        """Detect first numeric metric column from catalog"""
        if not catalog:
            return None

        if catalog.detectedNumericColumns and len(catalog.detectedNumericColumns) > 0:
            for col_name in catalog.detectedNumericColumns:
                if "id" not in col_name.lower():
                    return col_name
            return catalog.detectedNumericColumns[0]

        for col in catalog.columns:
            col_type = col.type.upper()
            if col_type in ["INTEGER", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"]:
                if "id" not in col.name.lower():
                    return col.name

        return None

    def _detect_all_numeric_columns(self, catalog: Any) -> list:
        """Detect all numeric columns from catalog, excluding ID columns"""
        if not catalog:
            return []

        numeric_cols = []

        if catalog.detectedNumericColumns and len(catalog.detectedNumericColumns) > 0:
            for col_name in catalog.detectedNumericColumns:
                if "id" not in col_name.lower():
                    numeric_cols.append(col_name)
            return numeric_cols

        for col in catalog.columns:
            col_type = col.type.upper()
            if col_type in ["INTEGER", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"]:
                if "id" not in col.name.lower():
                    numeric_cols.append(col.name)

        return numeric_cols

    async def _call_openai(
        self, request: ChatOrchestratorRequest, catalog: Any
    ) -> Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse]:
        privacy_mode = request.privacyMode if request.privacyMode is not None else True
        safe_mode = request.safeMode if request.safeMode is not None else False

        redacted_catalog, pii_map = pii_redactor.redact_catalog(catalog, privacy_mode)

        messages = self._build_messages(request, redacted_catalog)

        logger.info(f"Calling OpenAI API with privacyMode={privacy_mode}, safeMode={safe_mode}...")
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )

        response_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present (shouldn't happen with updated prompt)
        if response_text.startswith("```"):
            logger.warning("LLM returned markdown code blocks despite instructions")
            response_text = response_text.replace("```json", "").replace("```", "").strip()

        logger.info(f"OpenAI response: {response_text[:200]}...")

        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.error(f"Raw response: {response_text[:500]}")
            raise ValueError("Invalid response format from AI")

        return self._parse_response(response_data, safe_mode, privacy_mode)

    async def _extract_intent_with_openai(
        self, request: ChatOrchestratorRequest, catalog: Any
    ) -> Dict[str, Any]:
        """
        Use OpenAI to extract structured intent from ambiguous user queries.

        Returns standardized JSON schema:
        {
          "analysis_type": "trend|top_categories|outliers|row_count|data_quality",
          "time_period": "last_7_days|last_30_days|last_90_days|all_time|unspecified",
          "metric": "column_name|unspecified",
          "group_by": "column_name|unspecified",
          "date_column": "column_name|unspecified"
        }
        """
        logger.info(f"Extracting intent with OpenAI for: '{request.message[:50]}...'")

        catalog_info = self._build_catalog_context(catalog)

        messages = [
            {"role": "system", "content": INTENT_EXTRACTION_PROMPT},
            {
                "role": "system",
                "content": f"Dataset Schema:\n{catalog_info}"
            },
            {
                "role": "user",
                "content": request.message
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500
            )

            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present (shouldn't happen with updated prompt)
            if response_text.startswith("```"):
                logger.warning("LLM returned markdown code blocks despite instructions")
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            logger.info(f"OpenAI intent extraction response: {response_text}")

            intent_data = json.loads(response_text)

            # Validate required fields
            required_fields = ["analysis_type", "time_period", "metric", "group_by", "date_column"]
            missing_fields = [f for f in required_fields if f not in intent_data]
            if missing_fields:
                logger.warning(f"Missing fields in intent extraction: {missing_fields}. Adding defaults.")
                for field in missing_fields:
                    intent_data[field] = "unspecified"

            # Ensure all fields use "unspecified" instead of null/None
            for field in required_fields:
                if intent_data[field] is None or intent_data[field] == "":
                    intent_data[field] = "unspecified"

            # Normalize time_period to lowercase
            if intent_data.get("time_period"):
                intent_data["time_period"] = str(intent_data["time_period"]).lower()

            logger.info(f"Extracted intent: analysis_type={intent_data.get('analysis_type')}, "
                       f"time_period={intent_data.get('time_period')}, "
                       f"metric={intent_data.get('metric')}, "
                       f"group_by={intent_data.get('group_by')}, "
                       f"date_column={intent_data.get('date_column')}")

            return intent_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent extraction response: {e}")
            logger.error(f"Raw response: {response_text if 'response_text' in locals() else 'N/A'}")
            raise ValueError("Invalid JSON response from intent extractor")
        except Exception as e:
            logger.error(f"Intent extraction error: {e}", exc_info=True)
            raise

    def _build_messages(self, request: ChatOrchestratorRequest, catalog: Any) -> list:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        safe_mode = request.safeMode if request.safeMode is not None else False
        privacy_mode = request.privacyMode if request.privacyMode is not None else True

        # Add Safe Mode notification if enabled
        if safe_mode:
            messages.append({
                "role": "system",
                "content": "🔒 SAFE MODE IS ON: You MUST generate ONLY aggregated queries using COUNT, SUM, AVG, MIN, MAX, or GROUP BY. Queries returning individual rows will be rejected."
            })

        # Add Privacy Mode notification if enabled
        if privacy_mode:
            messages.append({
                "role": "system",
                "content": "🔐 PRIVACY MODE IS ON: PII columns have been redacted. Focus on non-PII columns. You will never see PII values."
            })

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
            results_summary = self._build_results_context(request.resultsContext, safe_mode)
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
            if hasattr(col, 'nullable') and col.nullable:
                col_info += " [nullable]"
            lines.append(col_info)

        if hasattr(catalog, 'detectedDateColumns') and catalog.detectedDateColumns:
            lines.append("")
            lines.append(f"Date Columns: {', '.join(catalog.detectedDateColumns)}")

        if hasattr(catalog, 'detectedNumericColumns') and catalog.detectedNumericColumns:
            lines.append(f"Numeric Columns: {', '.join(catalog.detectedNumericColumns)}")

        if hasattr(catalog, 'basicStats') and catalog.basicStats:
            lines.append("")
            lines.append("Column Statistics:")
            for col_name, stats in catalog.basicStats.items():
                if isinstance(stats, dict):
                    stat_parts = []
                    if "count" in stats:
                        stat_parts.append(f"count={stats['count']}")
                    if "unique" in stats:
                        stat_parts.append(f"unique={stats['unique']}")
                    if "min" in stats and stats["min"] is not None:
                        stat_parts.append(f"min={stats['min']}")
                    if "max" in stats and stats["max"] is not None:
                        stat_parts.append(f"max={stats['max']}")
                    if "mean" in stats and stats["mean"] is not None:
                        stat_parts.append(f"mean={stats['mean']:.2f}")
                    if stat_parts:
                        lines.append(f"  {col_name}: {', '.join(stat_parts)}")

        if hasattr(catalog, 'piiColumns') and catalog.piiColumns and len(catalog.piiColumns) > 0:
            lines.append("")
            lines.append("WARNING: PII columns detected but not redacted. This should not happen in privacy mode!")

        return "\n".join(lines)

    def _build_results_context(self, results_context: Any, safe_mode: bool = False) -> str:
        if safe_mode:
            lines = ["Previous query results (Safe Mode - no raw rows):"]
        else:
            lines = ["Previous query results (aggregated):"]

        for result in results_context.results:
            lines.append(f"\n{result.name}:")
            lines.append(f"  Columns: {', '.join(result.columns)}")
            lines.append(f"  Rows returned: {len(result.rows)}")

            if result.rows and not safe_mode:
                lines.append("  Sample data:")
                for i, row in enumerate(result.rows[:5]):
                    lines.append(f"    {row}")
                if len(result.rows) > 5:
                    lines.append(f"    ... ({len(result.rows) - 5} more rows)")

        return "\n".join(lines)

    def _parse_response(
        self, response_data: Dict[str, Any], safe_mode: bool = False, privacy_mode: bool = True
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

            valid, error = sql_validator.validate_queries(queries, safe_mode)
            if not valid:
                logger.warning(f"SQL validation failed: {error}")
                if safe_mode and "Safe Mode is ON" in error:
                    return NeedsClarificationResponse(
                        question=error,
                        choices=["Ask a different question", "View dataset info"]
                    )
                return NeedsClarificationResponse(
                    question=f"I generated an invalid query: {error}. Let me try again - could you rephrase your question?",
                    choices=["Rephrase question", "View dataset info"]
                )

            query_objects = [
                QueryToRun(name=q["name"], sql=q["sql"])
                for q in queries
            ]

            # Build audit trail based on actual modes
            audit_shared = ["schema", "aggregates_only"]
            if privacy_mode:
                audit_shared.append("PII_redacted")
            if safe_mode:
                audit_shared.append("safe_mode_no_raw_rows")

            return RunQueriesResponse(
                queries=query_objects,
                explanation=response_data.get("explanation", "Running queries..."),
                audit=AuditInfo(sharedWithAI=audit_shared)
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

            # Build audit trail based on actual modes
            audit_shared = ["schema", "aggregates_only"]
            if privacy_mode:
                audit_shared.append("PII_redacted")
            if safe_mode:
                audit_shared.append("safe_mode_no_raw_rows")

            return FinalAnswerResponse(
                message=response_data.get("message", "Analysis complete."),
                tables=tables,
                audit=AuditInfo(sharedWithAI=audit_shared)
            )

        else:
            logger.error(f"Unknown response type: {response_type}")
            raise ValueError(f"Unknown response type: {response_type}")


chat_orchestrator = ChatOrchestrator()
