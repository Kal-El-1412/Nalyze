import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import duckdb

from app.storage import storage

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self):
        self.base_dir = Path.home() / ".cloaksheets" / "datasets"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_dataset_dir(self, dataset_id: str) -> Path:
        dataset_dir = self.base_dir / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir

    def get_db_path(self, dataset_id: str) -> Path:
        return self.get_dataset_dir(dataset_id) / "db.duckdb"

    def get_catalog_path(self, dataset_id: str) -> Path:
        return self.get_dataset_dir(dataset_id) / "catalog.json"

    async def ingest_csv(self, dataset_id: str, file_path: str, job_id: str):
        logger.info(f"Starting ingestion for dataset {dataset_id} from {file_path}")

        try:
            await storage.update_job(
                job_id=job_id,
                status="running",
                started_at=datetime.utcnow().isoformat()
            )

            db_path = self.get_db_path(dataset_id)
            catalog_path = self.get_catalog_path(dataset_id)

            if db_path.exists():
                db_path.unlink()
                logger.info(f"Removed existing database at {db_path}")

            conn = duckdb.connect(str(db_path))

            logger.info(f"Loading CSV from {file_path} into DuckDB")
            conn.execute(f"""
                CREATE TABLE data AS
                SELECT * FROM read_csv_auto('{file_path}',
                    sample_size=-1,
                    ignore_errors=false,
                    auto_detect=true
                )
            """)

            logger.info("CSV loaded successfully, generating catalog")
            catalog = self._generate_catalog(conn)

            with open(catalog_path, 'w') as f:
                json.dump(catalog, f, indent=2)

            conn.close()
            logger.info(f"Catalog saved to {catalog_path}")

            await storage.update_dataset(
                dataset_id=dataset_id,
                updates={
                    "status": "ingested",
                    "lastIngestedAt": datetime.utcnow().isoformat()
                }
            )

            await storage.update_job(
                job_id=job_id,
                status="done",
                finished_at=datetime.utcnow().isoformat()
            )

            logger.info(f"Ingestion completed successfully for dataset {dataset_id}")

        except Exception as e:
            logger.error(f"Ingestion failed for dataset {dataset_id}: {e}", exc_info=True)

            await storage.update_dataset(
                dataset_id=dataset_id,
                updates={"status": "error"}
            )

            await storage.update_job(
                job_id=job_id,
                status="error",
                finished_at=datetime.utcnow().isoformat(),
                error=str(e)
            )

    def _generate_catalog(self, conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
        row_count = conn.execute("SELECT COUNT(*) FROM data").fetchone()[0]

        columns_info = conn.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'data'
            ORDER BY ordinal_position
        """).fetchall()

        columns = []
        basic_stats = {}
        detected_date_columns = []
        detected_numeric_columns = []

        for col_name, col_type in columns_info:
            columns.append({"name": col_name, "type": col_type})

            col_type_lower = col_type.lower()

            if any(t in col_type_lower for t in ['int', 'double', 'float', 'decimal', 'numeric', 'real']):
                detected_numeric_columns.append(col_name)
                stats = self._get_numeric_stats(conn, col_name, row_count)
                basic_stats[col_name] = stats

            elif any(t in col_type_lower for t in ['date', 'timestamp', 'time']):
                detected_date_columns.append(col_name)
                stats = self._get_date_stats(conn, col_name, row_count)
                basic_stats[col_name] = stats

            else:
                stats = self._get_text_stats(conn, col_name, row_count)
                basic_stats[col_name] = stats

        catalog = {
            "table": "data",
            "rowCount": row_count,
            "columns": columns,
            "basicStats": basic_stats,
            "detectedDateColumns": detected_date_columns,
            "detectedNumericColumns": detected_numeric_columns
        }

        return catalog

    def _get_numeric_stats(self, conn: duckdb.DuckDBPyConnection, col_name: str, total_rows: int) -> Dict[str, Any]:
        try:
            result = conn.execute(f"""
                SELECT
                    MIN("{col_name}") as min_val,
                    MAX("{col_name}") as max_val,
                    AVG("{col_name}") as avg_val,
                    COUNT(*) FILTER (WHERE "{col_name}" IS NULL) as null_count
                FROM data
            """).fetchone()

            null_count = result[3] or 0
            null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0

            return {
                "min": result[0],
                "max": result[1],
                "avg": result[2],
                "nullPct": round(null_pct, 2)
            }
        except Exception as e:
            logger.warning(f"Error getting numeric stats for {col_name}: {e}")
            return {"nullPct": 0}

    def _get_date_stats(self, conn: duckdb.DuckDBPyConnection, col_name: str, total_rows: int) -> Dict[str, Any]:
        try:
            result = conn.execute(f"""
                SELECT
                    MIN("{col_name}") as min_val,
                    MAX("{col_name}") as max_val,
                    COUNT(*) FILTER (WHERE "{col_name}" IS NULL) as null_count
                FROM data
            """).fetchone()

            null_count = result[2] or 0
            null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0

            return {
                "min": str(result[0]) if result[0] else None,
                "max": str(result[1]) if result[1] else None,
                "nullPct": round(null_pct, 2)
            }
        except Exception as e:
            logger.warning(f"Error getting date stats for {col_name}: {e}")
            return {"nullPct": 0}

    def _get_text_stats(self, conn: duckdb.DuckDBPyConnection, col_name: str, total_rows: int) -> Dict[str, Any]:
        try:
            result = conn.execute(f"""
                SELECT
                    COUNT(*) FILTER (WHERE "{col_name}" IS NULL) as null_count,
                    APPROX_COUNT_DISTINCT("{col_name}") as distinct_count
                FROM data
            """).fetchone()

            null_count = result[0] or 0
            null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0

            return {
                "nullPct": round(null_pct, 2),
                "approxDistinct": result[1]
            }
        except Exception as e:
            logger.warning(f"Error getting text stats for {col_name}: {e}")
            return {"nullPct": 0, "approxDistinct": 0}

    async def load_catalog(self, dataset_id: str) -> Dict[str, Any]:
        catalog_path = self.get_catalog_path(dataset_id)

        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found for dataset {dataset_id}")

        with open(catalog_path, 'r') as f:
            return json.load(f)


ingestion_pipeline = IngestionPipeline()
