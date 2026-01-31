import logging
import re
import signal
import time
from typing import Dict, Any, List, Tuple
import duckdb
from app.storage import storage
from app.ingest_pipeline import ingestion_pipeline
from app.config import config

logger = logging.getLogger(__name__)


DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ATTACH', 'COPY', 'EXPORT',
    'CREATE', 'ALTER', 'TRUNCATE', 'REPLACE'
]


class QueryTimeoutError(Exception):
    pass


class QueryExecutor:
    def __init__(self):
        self.connection_cache: Dict[str, duckdb.DuckDBPyConnection] = {}

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        sql_upper = sql.upper()

        for keyword in DANGEROUS_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Dangerous SQL keyword detected: {keyword}"

        return True, ""

    def wrap_with_limit(self, sql: str) -> str:
        sql_upper = sql.upper().strip()

        if 'LIMIT' in sql_upper:
            return sql

        return f"SELECT * FROM ({sql}) LIMIT {config.max_rows_return}"

    async def get_connection(self, dataset_id: str, read_only: bool = True) -> duckdb.DuckDBPyConnection:
        if dataset_id in self.connection_cache:
            return self.connection_cache[dataset_id]

        dataset = await storage.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")

        if dataset["status"] != "ingested":
            raise ValueError(f"Dataset {dataset_id} has not been ingested yet. Status: {dataset['status']}")

        db_path = ingestion_pipeline.get_db_path(dataset_id)

        if not db_path.exists():
            raise ValueError(f"Database file not found for dataset {dataset_id}")

        conn = duckdb.connect(str(db_path), read_only=read_only)
        self.connection_cache[dataset_id] = conn
        return conn

    async def execute_query(self, dataset_id: str, sql: str, validate: bool = True, apply_limit: bool = True) -> Dict[str, Any]:
        logger.info(f"Executing query on dataset {dataset_id}: {sql[:100]}...")

        if validate:
            is_valid, error_msg = self.validate_sql(sql)
            if not is_valid:
                raise ValueError(error_msg)

        if apply_limit:
            sql = self.wrap_with_limit(sql)
            logger.info(f"Wrapped query with limit: {sql[:100]}...")

        start_time = time.time()

        try:
            conn = await self.get_connection(dataset_id, read_only=True)

            conn.execute(f"SET statement_timeout = '{config.query_timeout_sec}s'")

            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description] if conn.description else []

            execution_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Query executed successfully: {len(result)} rows, "
                f"{len(columns)} columns, {execution_time_ms:.2f}ms"
            )

            return {
                "columns": columns,
                "rows": result,
                "row_count": len(result),
                "execution_time_ms": execution_time_ms
            }

        except duckdb.InterruptException:
            raise QueryTimeoutError(f"Query execution exceeded {config.query_timeout_sec} seconds timeout")
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise

    async def execute_queries(self, dataset_id: str, queries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        results = []

        for query in queries:
            name = query.get("name", "unnamed")
            sql = query.get("sql", "")

            if not sql:
                raise ValueError(f"Query '{name}' has no SQL provided")

            try:
                result = await self.execute_query(dataset_id, sql, validate=True, apply_limit=True)
                results.append({
                    "name": name,
                    "columns": result["columns"],
                    "rows": result["rows"]
                })
            except Exception as e:
                logger.error(f"Error executing query '{name}': {e}")
                raise ValueError(f"Error executing query '{name}': {str(e)}")

        return results

    async def get_sample_data(self, dataset_id: str, limit: int = 100) -> Dict[str, Any]:
        sql = f"SELECT * FROM data LIMIT {limit}"
        return await self.execute_query(dataset_id, sql, validate=False, apply_limit=False)

    async def get_preview(self, dataset_id: str, limit: int = 100) -> Dict[str, Any]:
        conn = await self.get_connection(dataset_id, read_only=True)

        total_rows = conn.execute("SELECT COUNT(*) FROM data").fetchone()[0]

        actual_limit = min(limit, self.max_rows)
        sql = f"SELECT * FROM data LIMIT {actual_limit}"

        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description] if conn.description else []

        return {
            "columns": columns,
            "rows": result,
            "totalRows": total_rows,
            "returnedRows": len(result)
        }

    async def get_column_stats(self, dataset_id: str, column_name: str) -> Dict[str, Any]:
        sql = f"""
        SELECT
            COUNT(*) as total_count,
            COUNT(DISTINCT "{column_name}") as unique_count,
            COUNT("{column_name}") as non_null_count,
            MIN("{column_name}") as min_value,
            MAX("{column_name}") as max_value
        FROM data
        """
        result = await self.execute_query(dataset_id, sql, validate=False, apply_limit=False)

        if result["rows"]:
            row = result["rows"][0]
            return {
                "column_name": column_name,
                "total_count": row[0],
                "unique_count": row[1],
                "non_null_count": row[2],
                "min_value": row[3],
                "max_value": row[4],
                "null_count": row[0] - row[2]
            }

        return {}

    def close_connection(self, dataset_id: str):
        if dataset_id in self.connection_cache:
            self.connection_cache[dataset_id].close()
            del self.connection_cache[dataset_id]
            logger.info(f"Connection closed for dataset {dataset_id}")

    def close_all_connections(self):
        for dataset_id in list(self.connection_cache.keys()):
            self.close_connection(dataset_id)


query_executor = QueryExecutor()
