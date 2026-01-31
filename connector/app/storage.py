import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
import uuid

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")

        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info("Storage manager initialized with Supabase")

    async def register_dataset(
        self,
        name: str,
        file_path: str,
        description: Optional[str] = None,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        dataset_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        dataset_data = {
            "id": dataset_id,
            "name": name,
            "file_path": file_path,
            "description": description,
            "row_count": row_count,
            "column_count": column_count,
            "columns": columns,
            "status": "active",
            "created_at": now,
            "updated_at": now
        }

        result = self.client.table("datasets").insert(dataset_data).execute()
        logger.info(f"Dataset registered: {dataset_id} - {name}")
        return result.data[0] if result.data else dataset_data

    async def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        result = self.client.table("datasets").select("*").eq("id", dataset_id).maybeSingle().execute()
        return result.data

    async def list_datasets(self) -> List[Dict[str, Any]]:
        result = self.client.table("datasets").select("*").order("created_at", desc=True).execute()
        return result.data or []

    async def update_dataset(self, dataset_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("datasets").update(updates).eq("id", dataset_id).execute()
        return result.data[0] if result.data else None

    async def delete_dataset(self, dataset_id: str) -> bool:
        result = self.client.table("datasets").delete().eq("id", dataset_id).execute()
        logger.info(f"Dataset deleted: {dataset_id}")
        return bool(result.data)

    async def create_job(
        self,
        dataset_id: str,
        job_type: str,
        status: str = "pending"
    ) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        job_data = {
            "id": job_id,
            "dataset_id": dataset_id,
            "job_type": job_type,
            "status": status,
            "progress": 0.0,
            "created_at": now,
            "updated_at": now
        }

        result = self.client.table("jobs").insert(job_data).execute()
        logger.info(f"Job created: {job_id} - {job_type} for dataset {dataset_id}")
        return result.data[0] if result.data else job_data

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        result = self.client.table("jobs").select("*").eq("id", job_id).maybeSingle().execute()
        return result.data

    async def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        updates = {"updated_at": datetime.utcnow().isoformat()}

        if status is not None:
            updates["status"] = status
        if progress is not None:
            updates["progress"] = progress
        if result is not None:
            updates["result"] = result
        if error is not None:
            updates["error"] = error

        result = self.client.table("jobs").update(updates).eq("id", job_id).execute()
        return result.data[0] if result.data else None

    async def list_jobs(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self.client.table("jobs").select("*")

        if dataset_id:
            query = query.eq("dataset_id", dataset_id)

        result = query.order("created_at", desc=True).execute()
        return result.data or []


storage = StorageManager()
