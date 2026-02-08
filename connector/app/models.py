from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
import uuid


class HealthResponse(BaseModel):
    status: str
    version: str
    config: Optional[Dict[str, Any]] = None


class DatasetRegisterRequest(BaseModel):
    name: str = Field(..., description="Human-readable name for the dataset")
    sourceType: Literal["local_file"] = Field("local_file", description="Type of data source")
    filePath: str = Field(..., description="Absolute path to the spreadsheet file")


class DatasetRegisterResponse(BaseModel):
    datasetId: str
    name: str


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


class QueryResultContext(BaseModel):
    name: str
    columns: List[str]
    rows: List[List[Any]]
    rowCount: Optional[int] = None


class ResultsContext(BaseModel):
    results: List[QueryResultContext]


class ChatOrchestratorRequest(BaseModel):
    datasetId: str
    conversationId: Optional[str] = None

    message: Optional[str] = None
    intent: Optional[str] = None
    value: Optional[Any] = None

    privacyMode: Optional[bool] = True
    safeMode: Optional[bool] = False
    aiAssist: Optional[bool] = False

    resultsContext: Optional[ResultsContext] = None
    defaultsContext: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        super().__init__(**data)

        msg = (self.message or "").strip()
        intent = (self.intent or "").strip()

        # must be either message OR (intent+value)
        if not msg and not intent:
            raise ValueError("Either 'message' or 'intent' must be provided")
        if msg and intent:
            raise ValueError("Cannot provide both 'message' and 'intent'")
        if intent and self.value is None:
            raise ValueError("'value' is required when 'intent' is provided")

        # generate a conversation id if missing
        if not self.conversationId:
            self.conversationId = f"conv-{uuid.uuid4()}"


class AuditInfo(BaseModel):
    sharedWithAI: List[str] = Field(default_factory=lambda: ["schema", "aggregates_only"])


class ExecutedQuery(BaseModel):
    name: str
    sql: str
    rowCount: int


class AuditMetadata(BaseModel):
    datasetId: str
    datasetName: str
    analysisType: str
    timePeriod: str
    aiAssist: bool
    safeMode: bool
    privacyMode: bool
    executedQueries: List[ExecutedQuery]
    generatedAt: str
    reportId: Optional[str] = None


class RoutingMetadata(BaseModel):
    """Metadata about how the request was routed and processed"""
    routing_decision: Literal["deterministic", "ai_intent_extraction", "clarification_needed", "direct_query"]
    deterministic_confidence: Optional[float] = None
    deterministic_match: Optional[str] = None
    openai_invoked: bool = False
    safe_mode: bool = False
    privacy_mode: bool = True


class NeedsClarificationResponse(BaseModel):
    type: Literal["needs_clarification"] = "needs_clarification"
    question: str
    choices: List[str]
    intent: Optional[str] = None
    allowFreeText: bool = False
    audit: AuditInfo = Field(default_factory=AuditInfo)
    routing_metadata: Optional[RoutingMetadata] = None


class QueryToRun(BaseModel):
    name: str
    sql: str


class RunQueriesResponse(BaseModel):
    type: Literal["run_queries"] = "run_queries"
    queries: List[QueryToRun]
    explanation: str
    audit: AuditInfo = Field(default_factory=AuditInfo)
    routing_metadata: Optional[RoutingMetadata] = None


class TableData(BaseModel):
    name: str
    columns: List[str]
    rows: List[List[Any]]


class FinalAnswerResponse(BaseModel):
    type: Literal["final_answer"] = "final_answer"
    summaryMarkdown: str
    tables: List[TableData] = Field(default_factory=list)
    audit: AuditMetadata
    routing_metadata: Optional[RoutingMetadata] = None


class IntentAcknowledgmentResponse(BaseModel):
    type: Literal["intent_acknowledged"] = "intent_acknowledged"
    intent: str
    value: Any
    state: Dict[str, Any]
    message: str
    routing_metadata: Optional[RoutingMetadata] = None


ChatOrchestratorResponse = Union[NeedsClarificationResponse, RunQueriesResponse, FinalAnswerResponse, IntentAcknowledgmentResponse]


class Job(BaseModel):
    jobId: str
    type: Literal["ingest"]
    datasetId: str
    status: Literal["queued", "running", "done", "error"]
    stage: Optional[Literal["queued", "scanning_headers", "ingesting_rows", "building_catalog", "done", "error"]] = None
    startedAt: Optional[str]
    finishedAt: Optional[str]
    updatedAt: Optional[str]
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


class Report(BaseModel):
    id: str
    dataset_id: str
    dataset_name: Optional[str] = None
    conversation_id: str
    question: str
    analysis_type: str
    time_period: str
    summary_markdown: str
    tables: List[Dict[str, Any]]
    audit_log: List[str]
    created_at: str
    privacy_mode: bool
    safe_mode: bool


class ReportSummary(BaseModel):
    id: str
    title: str
    datasetId: str
    datasetName: str
    createdAt: str


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
    privacyMode: Optional[bool] = True
    safeMode: Optional[bool] = False


class QueryResult(BaseModel):
    name: str
    columns: List[str]
    rows: List[List[Any]]
    rowCount: int


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
