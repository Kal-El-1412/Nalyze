import logging
import os
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Request, status, HTTPException, BackgroundTasks
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
    PreviewResponse
)
from app.storage import storage
from app.ingest_pipeline import ingestion_pipeline
from app.query import query_executor, QueryTimeoutError

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
    return HealthResponse(status="ok", version=VERSION)


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
async def execute_queries(request: QueryExecuteRequest):
    logger.info(f"Execute queries requested for dataset {request.datasetId}, {len(request.queries)} queries")

    dataset = await storage.get_dataset(request.datasetId)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found: {request.datasetId}"
        )

    if dataset["status"] != "ingested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset {request.datasetId} has not been ingested yet. Current status: {dataset['status']}"
        )

    try:
        results = await query_executor.execute_queries(request.datasetId, request.queries)
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
