import logging
import os
from typing import Dict, Any, Optional
import duckdb

logger = logging.getLogger(__name__)


class DataIngestor:
    def __init__(self):
        self.supported_extensions = {".csv", ".xlsx", ".xls", ".parquet"}

    def validate_file(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file type: {ext}. Supported: {', '.join(self.supported_extensions)}"
            )

        return True

    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        self.validate_file(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Analyzing file: {file_path}")

        conn = duckdb.connect(":memory:")

        try:
            if ext == ".csv":
                conn.execute(f"CREATE TABLE data AS SELECT * FROM read_csv_auto('{file_path}')")
            elif ext in {".xlsx", ".xls"}:
                conn.execute(f"INSTALL spatial; LOAD spatial;")
                conn.execute(f"CREATE TABLE data AS SELECT * FROM st_read('{file_path}')")
            elif ext == ".parquet":
                conn.execute(f"CREATE TABLE data AS SELECT * FROM read_parquet('{file_path}')")

            result = conn.execute("SELECT COUNT(*) as row_count FROM data").fetchone()
            row_count = result[0] if result else 0

            columns_result = conn.execute("PRAGMA table_info('data')").fetchall()
            columns = [col[1] for col in columns_result]
            column_count = len(columns)

            logger.info(f"File analyzed: {row_count} rows, {column_count} columns")

            return {
                "row_count": row_count,
                "column_count": column_count,
                "columns": columns,
                "file_size": os.path.getsize(file_path)
            }

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            raise
        finally:
            conn.close()

    async def load_dataset(self, dataset_id: str, file_path: str) -> duckdb.DuckDBPyConnection:
        self.validate_file(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Loading dataset {dataset_id} from {file_path}")

        conn = duckdb.connect(":memory:")

        try:
            if ext == ".csv":
                conn.execute(f"CREATE TABLE data AS SELECT * FROM read_csv_auto('{file_path}')")
            elif ext in {".xlsx", ".xls"}:
                conn.execute(f"INSTALL spatial; LOAD spatial;")
                conn.execute(f"CREATE TABLE data AS SELECT * FROM st_read('{file_path}')")
            elif ext == ".parquet":
                conn.execute(f"CREATE TABLE data AS SELECT * FROM read_parquet('{file_path}')")

            logger.info(f"Dataset {dataset_id} loaded successfully")
            return conn

        except Exception as e:
            logger.error(f"Error loading dataset {dataset_id}: {e}")
            conn.close()
            raise


ingestor = DataIngestor()
