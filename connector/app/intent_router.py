"""
LLM-based Intent Router

Parses free-text user questions into structured analysis intents.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from app.config import config

logger = logging.getLogger(__name__)


INTENT_ROUTER_SYSTEM_PROMPT = """You are an intent classification system for data analysis queries.

Your job is to parse user questions and return a structured JSON response with:
- analysis_type: The type of analysis requested
- required_params: List of parameters that are still needed
- target_columns: Optional list of specific columns mentioned (can be empty)

Available analysis types:
1. "row_count" - Count total rows, filter by criteria
2. "top_categories" - Find top N items by a metric
3. "trend" - Analyze trends over time
4. "outliers" - Detect anomalies and outliers
5. "data_quality" - Check for missing values, duplicates, data issues

Required parameters:
- time_period: Required for most analyses (unless user specifies or it's data_quality)

Examples:

User: "How many rows are there?"
Response: {"analysis_type": "row_count", "required_params": [], "target_columns": []}

User: "What are the top selling products?"
Response: {"analysis_type": "top_categories", "required_params": ["time_period"], "target_columns": ["products", "sales"]}

User: "Show me sales trends"
Response: {"analysis_type": "trend", "required_params": ["time_period"], "target_columns": ["sales"]}

User: "Find outliers in revenue"
Response: {"analysis_type": "outliers", "required_params": ["time_period"], "target_columns": ["revenue"]}

User: "Check data quality"
Response: {"analysis_type": "data_quality", "required_params": [], "target_columns": []}

User: "What are the top categories last month?"
Response: {"analysis_type": "top_categories", "required_params": [], "target_columns": ["categories"]}
Note: time_period not required because "last month" was specified

Always respond with valid JSON only. No other text."""


class IntentRouter:
    """Routes free-text questions to structured analysis intents using LLM"""

    def __init__(self):
        self.ai_mode = config.ai_mode
        self.openai_api_key = config.openai_api_key
        self.client = None
        if self.ai_mode and self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)

    async def route_intent(
        self,
        user_message: str,
        catalog: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse user message into structured intent.

        Args:
            user_message: The user's free-text question
            catalog: Optional dataset catalog for context

        Returns:
            Dict with:
                - analysis_type: str
                - required_params: List[str]
                - target_columns: List[str]
        """
        # Validate AI mode
        is_valid, error_message = config.validate_ai_mode_for_request()
        if not is_valid:
            logger.error(f"Intent routing failed: {error_message}")
            raise ValueError(error_message)

        # Build context message with catalog info if available
        context_message = ""
        if catalog and catalog.get("tables"):
            table_info = []
            for table in catalog["tables"]:
                cols = ", ".join(table.get("columns", [])[:5])  # First 5 columns
                table_info.append(f"- {table['name']}: {cols}")

            if table_info:
                context_message = f"\n\nAvailable data:\n" + "\n".join(table_info)

        user_prompt = f"{user_message}{context_message}"

        try:
            logger.info(f"Routing intent for message: {user_message[:100]}")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": INTENT_ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            logger.info(f"Intent router response: {result_text}")

            result = json.loads(result_text)

            # Validate response structure
            if "analysis_type" not in result:
                logger.error(f"Invalid router response: missing analysis_type")
                raise ValueError("Invalid intent router response")

            # Ensure required fields exist
            result.setdefault("required_params", [])
            result.setdefault("target_columns", [])

            logger.info(
                f"Routed intent: analysis_type={result['analysis_type']}, "
                f"required_params={result['required_params']}, "
                f"target_columns={result['target_columns']}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent router JSON: {e}")
            logger.error(f"Raw response: {result_text}")
            raise ValueError("Intent router returned invalid JSON")

        except Exception as e:
            logger.error(f"Intent routing error: {e}", exc_info=True)
            raise


# Global singleton
intent_router = IntentRouter()
