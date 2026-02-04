import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

RESTRICTED_KEYWORDS = [
    "DROP",
    "DELETE",
    "TRUNCATE",
    "ALTER",
    "CREATE",
    "INSERT",
    "UPDATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "CALL",
    "PRAGMA",
    "ATTACH",
    "DETACH"
]

AGGREGATE_FUNCTIONS = [
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "TOTAL",
    "GROUP_CONCAT",
    "STRING_AGG"
]

MAX_QUERIES_PER_REQUEST = 3
DEFAULT_LIMIT = 1000
MAX_LIMIT = 10000


class SQLValidationError(Exception):
    pass


class SQLValidator:
    def __init__(self):
        self.restricted_pattern = re.compile(
            r'\b(' + '|'.join(RESTRICTED_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self.limit_pattern = re.compile(r'\bLIMIT\s+(\d+)\b', re.IGNORECASE)
        self.aggregate_pattern = re.compile(
            r'\b(' + '|'.join(AGGREGATE_FUNCTIONS) + r')\s*\(',
            re.IGNORECASE
        )
        self.group_by_pattern = re.compile(r'\bGROUP\s+BY\b', re.IGNORECASE)

    def validate_queries(self, queries: List[dict], safe_mode: bool = False) -> Tuple[bool, str]:
        if len(queries) > MAX_QUERIES_PER_REQUEST:
            return False, f"Too many queries. Maximum {MAX_QUERIES_PER_REQUEST} queries allowed per request."

        for i, query in enumerate(queries):
            query_name = query.get("name", f"query_{i}")
            sql = query.get("sql", "")

            valid, error = self.validate_single_query(sql, query_name, safe_mode)
            if not valid:
                return False, error

        return True, ""

    def validate_single_query(self, sql: str, query_name: str = "query", safe_mode: bool = False) -> Tuple[bool, str]:
        if not sql or not sql.strip():
            return False, f"Query '{query_name}' is empty"

        sql_upper = sql.upper().strip()

        if not sql_upper.startswith("SELECT"):
            return False, f"Query '{query_name}' must be a SELECT statement"

        restricted_match = self.restricted_pattern.search(sql)
        if restricted_match:
            keyword = restricted_match.group(1)
            return False, f"Query '{query_name}' contains restricted keyword: {keyword}"

        if not self.has_limit_clause(sql):
            return False, f"Query '{query_name}' must include a LIMIT clause for safety"

        limit_value = self.extract_limit(sql)
        if limit_value and limit_value > MAX_LIMIT:
            return False, f"Query '{query_name}' LIMIT exceeds maximum allowed ({MAX_LIMIT})"

        if safe_mode:
            if not self.is_aggregate_safe(sql):
                return False, "Safe Mode is ON: only aggregated queries are allowed (use COUNT, SUM, AVG, MIN, MAX, or GROUP BY)"

        return True, ""

    def has_limit_clause(self, sql: str) -> bool:
        return bool(self.limit_pattern.search(sql))

    def extract_limit(self, sql: str) -> int:
        match = self.limit_pattern.search(sql)
        if match:
            return int(match.group(1))
        return 0

    def enforce_limit(self, sql: str, default_limit: int = DEFAULT_LIMIT) -> str:
        if not self.has_limit_clause(sql):
            sql = sql.rstrip().rstrip(';')
            sql = f"{sql} LIMIT {default_limit}"
            logger.info(f"Added LIMIT {default_limit} to query")
        return sql

    def is_aggregate_safe(self, sql: str) -> bool:
        """
        Check if a query is safe for Safe Mode.
        A query is safe if it contains aggregate functions or GROUP BY.
        """
        has_aggregate = bool(self.aggregate_pattern.search(sql))
        has_group_by = bool(self.group_by_pattern.search(sql))

        is_safe = has_aggregate or has_group_by

        if is_safe:
            logger.info(f"Query is aggregate-safe (has_aggregate={has_aggregate}, has_group_by={has_group_by})")
        else:
            logger.warning(f"Query is NOT aggregate-safe (has_aggregate={has_aggregate}, has_group_by={has_group_by})")

        return is_safe


sql_validator = SQLValidator()
