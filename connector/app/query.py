import logging
import time
from typing import Dict, Any, List
import duckdb
from app.ingest import ingestor
from app.storage import storage

logger = logging.getLogger(__name__)


class QueryExecutor:
    def __init__(self):
        self.connection_cache: Dict[str, duckdb.DuckDBPyConnection] = {}

    async def get_connection(self, dataset_id: str) -> duckdb.DuckDBPyConnection:
        if dataset_id in self.connection_cache:
            return self.connection_cache[dataset_id]

        dataset = await storage.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")

        conn = await ingestor.load_dataset(dataset_id, dataset["file_path"])
        self.connection_cache[dataset_id] = conn
        return conn

    async def execute_query(self, dataset_id: str, sql: str) -> Dict[str, Any]:
        logger.info(f"Executing query on dataset {dataset_id}: {sql[:100]}...")

        start_time = time.time()

        try:
            conn = await self.get_connection(dataset_id)

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

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise

    async def get_sample_data(self, dataset_id: str, limit: int = 100) -> Dict[str, Any]:
        sql = f"SELECT * FROM data LIMIT {limit}"
        return await self.execute_query(dataset_id, sql)

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
        result = await self.execute_query(dataset_id, sql)

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
