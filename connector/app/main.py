import logging
import os
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.models import (
    HealthResponse,
    DatasetRegisterRequest,
    DatasetRegisterResponse,
    Dataset,
    Job
)
from app.storage import storage

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
