from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


class DatasetRegisterRequest(BaseModel):
    name: str = Field(..., description="Human-readable name for the dataset")
    sourceType: Literal["local_file"] = Field("local_file", description="Type of data source")
    filePath: str = Field(..., description="Absolute path to the spreadsheet file")


class DatasetRegisterResponse(BaseModel):
    datasetId: str


class Dataset(BaseModel):
    datasetId: str
    name: str
    sourceType: str
    filePath: str
    createdAt: str
    lastIngestedAt: Optional[str]
    status: Literal["registered", "ingested", "error"]


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


class QueryResultContext(BaseModel):
    name: str
    columns: List[str]
    rows: List[List[Any]]


class ResultsContext(BaseModel):
    results: List[QueryResultContext]


class ChatOrchestratorRequest(BaseModel):
    datasetId: str
    conversationId: str
    message: str
    resultsContext: Optional[ResultsContext] = None


class AuditInfo(BaseModel):
    sharedWithAI: List[str] = Field(default_factory=lambda: ["schema", "aggregates_only"])


class NeedsClarificationResponse(BaseModel):
    type: Literal["needs_clarification"] = "needs_clarification"
    question: str
    choices: List[str]
    audit: AuditInfo = Field(default_factory=AuditInfo)


class QueryToRun(BaseModel):
    name: str
    sql: str


class RunQueriesResponse(BaseModel):
    type: Literal["run_queries"] = "run_queries"
    queries: List[QueryToRun]
    explanation: str
    audit: AuditInfo = Field(default_factory=AuditInfo)


class TableData(BaseModel):
    title: str
    columns: List[str]
    rows: List[List[Any]]


class FinalAnswerResponse(BaseModel):
    type: Literal["final_answer"] = "final_answer"
    message: str
    tables: Optional[List[TableData]] = None
    audit: AuditInfo = Field(default_factory=AuditInfo)


ChatOrchestratorResponse = Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse]


class Job(BaseModel):
    jobId: str
    type: Literal["ingest"]
    datasetId: str
    status: Literal["queued", "running", "done", "error"]
    startedAt: Optional[str]
    finishedAt: Optional[str]
    error: Optional[str]


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


class IngestResponse(BaseModel):
    jobId: str


class ColumnInfo(BaseModel):
    name: str
    type: str


class ColumnStats(BaseModel):
    min: Optional[Any] = None
    max: Optional[Any] = None
    avg: Optional[float] = None
    nullPct: float
    approxDistinct: Optional[int] = None


class PIIColumnInfo(BaseModel):
    name: str
    type: Literal["email", "phone", "name"]
    confidence: float = Field(..., ge=0.0, le=1.0)


class Catalog(BaseModel):
    table: str
    rowCount: int
    columns: List[ColumnInfo]
    basicStats: Dict[str, ColumnStats]
    detectedDateColumns: List[str]
    detectedNumericColumns: List[str]
    piiColumns: List[PIIColumnInfo] = Field(default_factory=list)


class QueryExecuteRequest(BaseModel):
    datasetId: str = Field(..., description="ID of the dataset to query")
    queries: List[Dict[str, str]] = Field(..., description="List of queries with name and sql")


class QueryResult(BaseModel):
    name: str
    columns: List[str]
    rows: List[List[Any]]


class QueryExecuteResponse(BaseModel):
    results: List[QueryResult]


class PreviewResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    totalRows: int
    returnedRows: int


class PIIInfoResponse(BaseModel):
    datasetId: str
    piiColumns: List[PIIColumnInfo]
