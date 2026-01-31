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
            self._save_registry({"datasets": {}, "jobs": {}})
            logger.info("Created new registry file")

    def _load_registry(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Error loading registry, creating new one: {e}")
                return {"datasets": {}, "jobs": {}}

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

        for dataset in registry["datasets"].values():
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

        registry["datasets"][dataset_id] = dataset_data
        self._save_registry(registry)

        logger.info(f"Dataset registered: {dataset_id} - {name}")
        return dataset_data

    async def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()
        return registry["datasets"].get(dataset_id)

    async def list_datasets(self) -> List[Dict[str, Any]]:
        registry = self._load_registry()
        datasets = list(registry["datasets"].values())
        datasets.sort(key=lambda x: x["createdAt"], reverse=True)
        return datasets

    async def update_dataset(self, dataset_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()

        if dataset_id not in registry["datasets"]:
            return None

        registry["datasets"][dataset_id].update(updates)
        self._save_registry(registry)

        return registry["datasets"][dataset_id]

    async def delete_dataset(self, dataset_id: str) -> bool:
        registry = self._load_registry()

        if dataset_id in registry["datasets"]:
            del registry["datasets"][dataset_id]
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
            "startedAt": None,
            "finishedAt": None,
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
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()

        if job_id not in registry["jobs"]:
            return None

        if status is not None:
            registry["jobs"][job_id]["status"] = status
        if started_at is not None:
            registry["jobs"][job_id]["startedAt"] = started_at
        if finished_at is not None:
            registry["jobs"][job_id]["finishedAt"] = finished_at
        if error is not None:
            registry["jobs"][job_id]["error"] = error

        self._save_registry(registry)
        return registry["jobs"][job_id]

    async def list_jobs(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        registry = self._load_registry()
        jobs = list(registry["jobs"].values())

        if dataset_id:
            jobs = [job for job in jobs if job["datasetId"] == dataset_id]

        jobs.sort(key=lambda x: x.get("startedAt") or x.get("jobId"), reverse=True)
        return jobs


storage = StorageManager()
