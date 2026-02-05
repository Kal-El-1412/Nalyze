import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import uuid
import threading

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self):
        self.base_dir = Path.home() / ".cloaksheets"
        self.datasets_dir = self.base_dir / "datasets"
        self.jobs_dir = self.base_dir / "jobs"
        self.registry_file = self.base_dir / "registry.json"

        self._lock = threading.Lock()

        self._initialize_directories()
        logger.info(f"Storage manager initialized at {self.base_dir}")

    def _initialize_directories(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(exist_ok=True)
        self.jobs_dir.mkdir(exist_ok=True)

        if not self.registry_file.exists():
            self._save_registry({"datasets": [], "jobs": {}})
            logger.info("Created new registry file")

    def _load_registry(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with open(self.registry_file, 'r') as f:
                    loaded = json.load(f)

                    # Handle legacy format: if root is a list, wrap it
                    if isinstance(loaded, list):
                        logger.info("Converting legacy list format to dict format")
                        return {"datasets": loaded, "jobs": {}}

                    # Handle legacy format: if datasets is a dict (keyed by ID), convert to list
                    if isinstance(loaded.get("datasets"), dict):
                        logger.info("Converting legacy dict format to list format")
                        datasets_list = list(loaded["datasets"].values())
                        loaded["datasets"] = datasets_list

                    # Ensure datasets key exists
                    loaded.setdefault("datasets", [])
                    loaded.setdefault("jobs", {})

                    return loaded
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Error loading registry, creating new one: {e}")
                return {"datasets": [], "jobs": {}}

    def _save_registry(self, data: Dict[str, Any]):
        with self._lock:
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)

    async def register_dataset(
        self,
        name: str,
        source_type: str,
        file_path: str
    ) -> Dict[str, Any]:
        registry = self._load_registry()

        # Check if dataset already exists
        for dataset in registry["datasets"]:
            if dataset["filePath"] == file_path:
                logger.info(f"Dataset already exists for path: {file_path}")
                return dataset

        dataset_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        dataset_data = {
            "datasetId": dataset_id,
            "name": name,
            "sourceType": source_type,
            "filePath": file_path,
            "createdAt": now,
            "lastIngestedAt": None,
            "status": "registered"
        }

        registry["datasets"].append(dataset_data)
        self._save_registry(registry)

        logger.info(f"Dataset registered: {dataset_id} - {name}")
        return dataset_data

    async def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()
        for dataset in registry["datasets"]:
            if dataset["datasetId"] == dataset_id:
                return dataset
        return None

    async def list_datasets(self) -> List[Dict[str, Any]]:
        registry = self._load_registry()
        datasets = registry["datasets"]
        datasets.sort(key=lambda x: x["createdAt"], reverse=True)
        return datasets

    async def update_dataset(self, dataset_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()

        for dataset in registry["datasets"]:
            if dataset["datasetId"] == dataset_id:
                dataset.update(updates)
                self._save_registry(registry)
                return dataset

        return None

    async def delete_dataset(self, dataset_id: str) -> bool:
        registry = self._load_registry()

        for i, dataset in enumerate(registry["datasets"]):
            if dataset["datasetId"] == dataset_id:
                registry["datasets"].pop(i)
                self._save_registry(registry)
                logger.info(f"Dataset deleted: {dataset_id}")
                return True

        return False

    async def create_job(
        self,
        dataset_id: str,
        job_type: str,
        status: str = "queued"
    ) -> Dict[str, Any]:
        registry = self._load_registry()

        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        job_data = {
            "jobId": job_id,
            "type": job_type,
            "datasetId": dataset_id,
            "status": status,
            "stage": "queued",
            "startedAt": None,
            "finishedAt": None,
            "updatedAt": now,
            "error": None
        }

        registry["jobs"][job_id] = job_data
        self._save_registry(registry)

        logger.info(f"Job created: {job_id} - {job_type} for dataset {dataset_id}")
        return job_data

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()
        return registry["jobs"].get(job_id)

    async def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()

        if job_id not in registry["jobs"]:
            return None

        if status is not None:
            registry["jobs"][job_id]["status"] = status
        if stage is not None:
            registry["jobs"][job_id]["stage"] = stage
        if started_at is not None:
            registry["jobs"][job_id]["startedAt"] = started_at
        if finished_at is not None:
            registry["jobs"][job_id]["finishedAt"] = finished_at
        if error is not None:
            registry["jobs"][job_id]["error"] = error

        registry["jobs"][job_id]["updatedAt"] = datetime.utcnow().isoformat()

        self._save_registry(registry)
        return registry["jobs"][job_id]

    async def list_jobs(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        registry = self._load_registry()
        jobs = list(registry["jobs"].values())

        if dataset_id:
            jobs = [job for job in jobs if job["datasetId"] == dataset_id]

        jobs.sort(key=lambda x: x.get("startedAt") or x.get("jobId"), reverse=True)
        return jobs

    async def create_report(
        self,
        dataset_id: str,
        conversation_id: str,
        question: str,
        analysis_type: str,
        time_period: str,
        summary_markdown: str,
        tables: List[Dict[str, Any]],
        audit_log: List[str],
        privacy_mode: bool,
        safe_mode: bool
    ) -> Dict[str, Any]:
        from app.config import config

        if not config.supabase:
            logger.warning("Supabase not available, report not saved")
            return {}

        try:
            report_data = {
                "dataset_id": dataset_id,
                "conversation_id": conversation_id,
                "question": question,
                "analysis_type": analysis_type,
                "time_period": time_period,
                "summary_markdown": summary_markdown,
                "tables": tables,
                "audit_log": audit_log,
                "privacy_mode": privacy_mode,
                "safe_mode": safe_mode
            }

            result = config.supabase.table("reports").insert(report_data).execute()

            if result.data and len(result.data) > 0:
                logger.info(f"Report created: {result.data[0]['id']}")
                return result.data[0]
            else:
                logger.error("Failed to create report: No data returned")
                return {}

        except Exception as e:
            logger.error(f"Error creating report: {e}")
            return {}

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        from app.config import config

        if not config.supabase:
            logger.warning("Supabase not available")
            return None

        try:
            result = config.supabase.table("reports").select("*").eq("id", report_id).maybeSingle().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error fetching report {report_id}: {e}")
            return None

    async def list_reports(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        from app.config import config

        if not config.supabase:
            logger.warning("Supabase not available")
            return []

        try:
            query = config.supabase.table("reports").select("*")

            if dataset_id:
                query = query.eq("dataset_id", dataset_id)

            result = query.order("created_at", desc=True).execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []


storage = StorageManager()
