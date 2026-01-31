from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


class DatasetRegisterRequest(BaseModel):
    name: str = Field(..., description="Human-readable name for the dataset")
    file_path: str = Field(..., description="Absolute path to the spreadsheet file")
    description: Optional[str] = Field(None, description="Optional description")


class DatasetInfo(BaseModel):
    id: str
    name: str
    file_path: str
    description: Optional[str]
    row_count: Optional[int]
    column_count: Optional[int]
    columns: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    status: Literal["active", "error", "scanning"]


class QueryRequest(BaseModel):
    dataset_id: str = Field(..., description="ID of the dataset to query")
    sql: str = Field(..., description="SQL query to execute")


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float


class ChatRequest(BaseModel):
    dataset_id: str
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    sql: Optional[str]
    has_query: bool


class JobInfo(BaseModel):
    id: str
    dataset_id: str
    job_type: Literal["pii_scan", "ingestion", "analysis"]
    status: Literal["pending", "running", "completed", "failed"]
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime


class PIIScanRequest(BaseModel):
    dataset_id: str
    columns: Optional[List[str]] = Field(None, description="Specific columns to scan, or all if None")


class PIIScanResult(BaseModel):
    job_id: str
    dataset_id: str
    findings: List[Dict[str, Any]]
    scanned_columns: List[str]
    total_rows_scanned: int
    scan_completed_at: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: str
