import logging
import os
import tempfile
import shutil
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Request, status, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.models import (
    HealthResponse,
    DatasetRegisterRequest,
    DatasetRegisterResponse,
    Dataset,
    Job,
    IngestResponse,
    Catalog,
    QueryExecuteRequest,
    QueryExecuteResponse,
    PreviewResponse,
    PIIInfoResponse,
    ChatOrchestratorRequest,
    NeedsClarificationResponse,
    RunQueriesResponse,
    FinalAnswerResponse,
    IntentAcknowledgmentResponse,
    Report
)
from app.storage import storage
from app.ingest_pipeline import ingestion_pipeline
from app.state import state_manager
from app.query import query_executor, QueryTimeoutError
from app.chat_orchestrator import chat_orchestrator
from app.config import config
from app.middleware import RequestLoggingMiddleware, RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting CloakSheets Connector v{VERSION}")
    yield
    logger.info("Shutting down CloakSheets Connector")


app = FastAPI(
    title="CloakSheets Connector",
    description="Privacy-first local data connector for spreadsheet analysis",
    version=VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:*",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "tauri://localhost",
        "http://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": str(exc)
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    logger.debug("Health check requested")
    return HealthResponse(
        status="ok",
        version=VERSION,
        config=config.get_safe_summary()
    )


@app.get("/")
async def root():
    return {
        "name": "CloakSheets Connector",
        "version": VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/datasets/register", response_model=DatasetRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_dataset(request: DatasetRegisterRequest):
    logger.info(f"Registering dataset: {request.name} from {request.filePath}")

    if not os.path.exists(request.filePath):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File does not exist: {request.filePath}"
        )

    if not os.path.isfile(request.filePath):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path is not a file: {request.filePath}"
        )

    dataset = await storage.register_dataset(
        name=request.name,
        source_type=request.sourceType,
        file_path=request.filePath
    )

    return DatasetRegisterResponse(datasetId=dataset["datasetId"])


@app.post("/datasets/upload", response_model=DatasetRegisterResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...)
):
    logger.info(f"Uploading dataset: {name}, file: {file.filename}")

    supported_extensions = {".csv", ".xlsx", ".xls", ".parquet"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}"
        )

    temp_dir = tempfile.gettempdir()
    uploads_dir = os.path.join(temp_dir, "cloaksheets_uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    temp_file_path = os.path.join(uploads_dir, f"{name}_{file.filename}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved to: {temp_file_path}")

        dataset = await storage.register_dataset(
            name=name,
            source_type="local_file",
            file_path=temp_file_path
        )

        return DatasetRegisterResponse(datasetId=dataset["datasetId"])

    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@app.get("/datasets", response_model=List[Dataset])
async def list_datasets():
    logger.debug("Listing all datasets")
    datasets = await storage.list_datasets()
    return datasets


@app.get("/jobs", response_model=List[Job])
async def list_jobs():
    logger.debug("Listing all jobs")
    jobs = await storage.list_jobs()
    return jobs


@app.get("/reports", response_model=List[Report])
async def list_reports(dataset_id: str = None):
    logger.debug(f"Listing reports for dataset: {dataset_id or 'all'}")
    reports = await storage.list_reports(dataset_id)
    return reports


@app.get("/reports/{report_id}", response_model=Report)
async def get_report(report_id: str):
    logger.debug(f"Fetching report: {report_id}")
    report = await storage.get_report(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )

    return report


@app.post("/datasets/{dataset_id}/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_dataset(dataset_id: str, background_tasks: BackgroundTasks, force: bool = False):
    logger.info(f"Ingestion requested for dataset {dataset_id} (force={force})")

    dataset = await storage.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found: {dataset_id}"
        )

    file_path = dataset["filePath"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File no longer exists: {file_path}"
        )

    job = await storage.create_job(
        dataset_id=dataset_id,
        job_type="ingest",
        status="queued"
    )

    background_tasks.add_task(
        ingestion_pipeline.ingest,
        dataset_id,
        file_path,
        job["jobId"],
        force
    )

    logger.info(f"Background ingestion task queued for dataset {dataset_id}, job {job['jobId']}")
    return IngestResponse(jobId=job["jobId"])


@app.get("/datasets/{dataset_id}/catalog", response_model=Catalog)
async def get_catalog(dataset_id: str):
    logger.debug(f"Catalog requested for dataset {dataset_id}")

    dataset = await storage.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found: {dataset_id}"
        )

    try:
        catalog = await ingestion_pipeline.load_catalog(dataset_id)
        return catalog
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog not found for dataset {dataset_id}. Dataset may not have been ingested yet."
        )


@app.post("/queries/execute", response_model=QueryExecuteResponse)
async def execute_queries(request_data: Request):
    body = await request_data.json()

    privacy_mode = body.get("privacyMode")
    if privacy_mode is None:
        privacy_header = request_data.headers.get("X-Privacy-Mode", "on")
        privacy_mode = privacy_header.lower() == "on"

    safe_mode = body.get("safeMode")
    if safe_mode is None:
        safe_mode_header = request_data.headers.get("X-Safe-Mode", "off")
        safe_mode = safe_mode_header.lower() == "on"

    body["privacyMode"] = privacy_mode
    body["safeMode"] = safe_mode
    request = QueryExecuteRequest(**body)

    logger.info(
        f"Execute queries requested for dataset {request.datasetId}, "
        f"{len(request.queries)} queries, privacyMode={request.privacyMode}, safeMode={request.safeMode}"
    )

    dataset = await storage.get_dataset(request.datasetId)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found: {request.datasetId}"
        )

    # Validate queries with Safe Mode enforcement
    from app.sql_validator import sql_validator
    valid, error = sql_validator.validate_queries(request.queries, safe_mode=request.safeMode)
    if not valid:
        logger.warning(f"SQL validation failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    try:
        results = await query_executor.execute_queries(
            request.datasetId,
            request.queries,
            privacy_mode=request.privacyMode
        )
        return QueryExecuteResponse(results=results)
    except QueryTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Query execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )


@app.get("/datasets/{dataset_id}/preview", response_model=PreviewResponse)
async def preview_dataset(dataset_id: str, limit: int = 100):
    logger.info(f"Preview requested for dataset {dataset_id}, limit={limit}")

    dataset = await storage.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found: {dataset_id}"
        )

    if dataset["status"] != "ingested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset {dataset_id} has not been ingested yet. Current status: {dataset['status']}"
        )

    if limit < 1 or limit > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 5000"
        )

    try:
        result = await query_executor.get_preview(dataset_id, limit)
        return PreviewResponse(**result)
    except Exception as e:
        logger.error(f"Preview error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


@app.get("/datasets/{dataset_id}/pii", response_model=PIIInfoResponse)
async def get_pii_info(dataset_id: str):
    logger.info(f"PII info requested for dataset {dataset_id}")

    dataset = await storage.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found: {dataset_id}"
        )

    if dataset["status"] != "ingested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset {dataset_id} has not been ingested yet. Current status: {dataset['status']}"
        )

    try:
        catalog = await ingestion_pipeline.load_catalog(dataset_id)
        pii_columns = catalog.get("piiColumns", [])

        return PIIInfoResponse(
            datasetId=dataset_id,
            piiColumns=pii_columns
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog not found for dataset {dataset_id}"
        )
    except Exception as e:
        logger.error(f"Error retrieving PII info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve PII info: {str(e)}"
        )


@app.post("/chat")
async def chat(request_data: Request):
    body = await request_data.json()

    privacy_mode = body.get("privacyMode")
    if privacy_mode is None:
        privacy_header = request_data.headers.get("X-Privacy-Mode", "on")
        privacy_mode = privacy_header.lower() == "on"

    body["privacyMode"] = privacy_mode
    request = ChatOrchestratorRequest(**body)

    logger.info("=" * 80)
    logger.info(f"📨 /chat endpoint received request:")
    logger.info(f"   conversationId: {request.conversationId}")
    logger.info(f"   datasetId: {request.datasetId}")
    logger.info(f"   intent: {request.intent}")
    logger.info(f"   value: {request.value}")
    logger.info(f"   message: {request.message[:50] if request.message else None}")
    logger.info(f"   hasResultsContext: {request.resultsContext is not None}")
    logger.info(f"   privacyMode: {request.privacyMode}")
    logger.info("=" * 80)

    try:
        if request.intent:
            return await handle_intent(request)
        else:
            return await handle_message(request)
    except Exception as e:
        logger.error(f"Chat processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


async def handle_intent(request: ChatOrchestratorRequest):
    logger.info(f"Handling intent: {request.intent} = {request.value}")

    state = state_manager.get_state(request.conversationId)
    logger.info(f"[BEFORE UPDATE] State context: {state.get('context', {})}")

    intent_field_map = {
        "set_analysis_type": "analysis_type",
        "set_time_period": "time_period",
        "set_metric": "metric",
        "set_dimension": "dimension",
        "set_filter": "filter",
        "set_grouping": "grouping",
        "set_visualization": "visualization_type"
    }

    field_name = intent_field_map.get(request.intent)
    if not field_name:
        field_name = request.intent.replace("set_", "")

    if request.intent.startswith("set_"):
        update_data = {field_name: request.value}
    else:
        update_data = {request.intent: request.value}

    logger.info(f"Update data: {update_data}")

    if "context" not in state:
        state["context"] = {}

    state["context"].update(update_data)
    logger.info(f"[AFTER MERGE] Merged context: {state['context']}")

    state_manager.update_state(request.conversationId, context=state["context"])
    logger.info(f"[AFTER PERSIST] Called update_state")

    updated_state = state_manager.get_state(request.conversationId)
    context = updated_state.get("context", {})
    logger.info(f"[AFTER RELOAD] Reloaded context: {context}")

    message = f"Updated {field_name.replace('_', ' ')} to '{request.value}'"

    logger.info(f"State updated for conversation {request.conversationId}: {field_name} = {request.value}")

    # Check if state is ready after update
    has_analysis = "analysis_type" in context
    has_time_period = "time_period" in context
    logger.info(f"Readiness check: analysis_type={has_analysis}, time_period={has_time_period}")

    if has_analysis and has_time_period:
        logger.info(f"State is ready for conversation {request.conversationId}, moving to query generation")
        # State is ready, generate queries
        response = await chat_orchestrator.process(request)

        if isinstance(response, FinalAnswerResponse):
            await save_report_from_response(request, response, context)

        return response
    else:
        # State not ready, check what's missing and ask for it
        if "analysis_type" not in context:
            logger.info(f"Missing analysis_type after intent, asking for it")
            return NeedsClarificationResponse(
                question="What type of analysis would you like to perform?",
                choices=["row_count", "top_categories", "trend"],
                intent="set_analysis_type"
            )
        elif "time_period" not in context:
            logger.info(f"Missing time_period after intent, asking for it")
            return NeedsClarificationResponse(
                question="What time period would you like to analyze?",
                choices=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                intent="set_time_period"
            )
        else:
            # All required fields present (shouldn't reach here)
            response = await chat_orchestrator.process(request)

            if isinstance(response, FinalAnswerResponse):
                await save_report_from_response(request, response, context)

            return response


async def handle_message(request: ChatOrchestratorRequest):
    logger.info(f"[handle_message] conversationId={request.conversationId}, hasResultsContext={request.resultsContext is not None}")

    state = state_manager.get_state(request.conversationId)
    context = state.get("context", {})

    logger.info(f"[handle_message] Retrieved context: {context}")
    logger.info(f"[handle_message] analysis_type present: {'analysis_type' in context}")
    logger.info(f"[handle_message] time_period present: {'time_period' in context}")

    # CRITICAL FIX: If resultsContext is present, NEVER ask for clarification
    # The queries have already been executed, so state MUST be ready
    # Proceed directly to orchestrator to generate final answer
    if request.resultsContext:
        logger.info(f"[handle_message] resultsContext present - bypassing clarification checks, proceeding to orchestrator")
        response = await chat_orchestrator.process(request)

        if isinstance(response, FinalAnswerResponse):
            await save_report_from_response(request, response, context)

        return response

    # Only ask for clarification if this is a new message (no resultsContext)
    if "analysis_type" not in context:
        logger.info(f"Missing analysis_type for conversation {request.conversationId}, returning clarification")
        return NeedsClarificationResponse(
            question="What type of analysis would you like to perform?",
            choices=["row_count", "top_categories", "trend"],
            intent="set_analysis_type"
        )

    if "time_period" not in context:
        logger.warning(f"Missing time_period for conversation {request.conversationId}, returning clarification")
        logger.warning(f"Full state: {state}")
        return NeedsClarificationResponse(
            question="What time period would you like to analyze?",
            choices=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            intent="set_time_period"
        )

    state_manager.update_state(
        request.conversationId,
        message_count=state.get("message_count", 0) + 1
    )

    logger.info(f"All required fields present, calling analysis pipeline for conversation {request.conversationId}")
    response = await chat_orchestrator.process(request)

    if isinstance(response, FinalAnswerResponse):
        await save_report_from_response(request, response, context)

    return response


async def save_report_from_response(request: ChatOrchestratorRequest, response: FinalAnswerResponse, context: dict):
    try:
        tables = []
        if response.tables:
            tables = [
                {
                    "name": table.name,
                    "columns": table.columns,
                    "rows": table.rows
                }
                for table in response.tables
            ]

        audit_log = response.audit.sharedWithAI if response.audit else []

        await storage.create_report(
            dataset_id=request.datasetId,
            conversation_id=request.conversationId,
            question=request.message or "",
            analysis_type=context.get("analysis_type", ""),
            time_period=context.get("time_period", ""),
            summary_markdown=response.message,
            tables=tables,
            audit_log=audit_log,
            privacy_mode=request.privacyMode if request.privacyMode is not None else True,
            safe_mode=request.safeMode if request.safeMode is not None else False
        )

        logger.info(f"Report saved for conversation {request.conversationId}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
