# CloakSheets Connector

Privacy-first local data connector for spreadsheet analysis. This backend service runs locally on your machine and provides secure access to your spreadsheet data without uploading files to the cloud.

## Features

- **Privacy-First**: All data processing happens locally on your machine
- **DuckDB Integration**: Fast analytical queries on CSV, Excel, and Parquet files
- **Local Filesystem Storage**: Dataset registry and job tracking stored in `~/.cloaksheets/`
- **RESTful API**: Clean API interface for the frontend application
- **PII Detection**: Built-in patterns for detecting sensitive data

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  Frontend App   │ ──────> │  This Connector  │ ──────> │ Local Files │
│  (React)        │  REST   │  (FastAPI)       │  reads  │ (.csv/.xlsx)│
│                 │  API    │  + DuckDB        │         │             │
└─────────────────┘         └──────────────────┘         └─────────────┘
                                     │
                                     │ metadata
                                     ▼
                            ┌─────────────────┐
                            │ ~/.cloaksheets/ │
                            │   registry.json │
                            │  datasets/      │
                            │  jobs/          │
                            └─────────────────┘
```

## Requirements

- Python 3.11+
- Local spreadsheet files (CSV, XLSX, XLS, Parquet)

## Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Storage is automatic**: The connector automatically creates `~/.cloaksheets/` with the necessary directories and registry file on first run. No database setup needed!

## Running the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7337 --reload
```

The server will start on `http://localhost:7337`

## API Documentation

Once the server is running, visit:
- Interactive API docs: http://localhost:7337/docs
- Alternative docs: http://localhost:7337/redoc

## Endpoints

### Health Check
```
GET /health
```
Returns the service status and version.

### Register Dataset
```
POST /datasets/register
```
Register a new local spreadsheet file.

**Request Body:**
```json
{
  "name": "Sales Data",
  "sourceType": "local_file",
  "filePath": "/absolute/path/to/file.csv"
}
```

**Response:**
```json
{
  "datasetId": "uuid-string"
}
```

**Validations:**
- File path must exist
- File path must point to a file (not a directory)
- Duplicate file paths return the existing dataset ID

### List Datasets
```
GET /datasets
```
Returns an array of all registered datasets.

**Response:**
```json
[
  {
    "datasetId": "uuid",
    "name": "Sales Data",
    "sourceType": "local_file",
    "filePath": "/path/to/file.csv",
    "createdAt": "2024-01-31T12:00:00Z",
    "lastIngestedAt": null,
    "status": "registered"
  }
]
```

### List Jobs
```
GET /jobs
```
Returns an array of all jobs (ingestion, PII scans, etc.).

**Response:**
```json
[
  {
    "jobId": "uuid",
    "type": "ingest",
    "datasetId": "uuid",
    "status": "queued",
    "startedAt": null,
    "finishedAt": null,
    "error": null
  }
]
```

## Supported File Formats

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Parquet (`.parquet`)

## Security Notes

- All file operations are read-only
- SQL queries are validated to prevent destructive operations
- Files never leave your local machine (all data stays local)
- Metadata is stored locally in `~/.cloaksheets/`

## Development

To run in development mode with auto-reload:

```bash
uvicorn app.main:app --reload --port 7337
```

## Troubleshooting

### Connection refused
- Ensure the server is running on port 7337
- Check firewall settings
- Verify the frontend is configured with the correct URL

### File not found when registering dataset
- Use absolute file paths (not relative paths)
- Verify file permissions (must be readable)
- Check file format is supported (CSV, XLSX, XLS, Parquet)

### Registry file errors
- Check that you have write permissions in your home directory
- The `~/.cloaksheets/` directory should be created automatically
- Delete `~/.cloaksheets/registry.json` to reset (you'll lose registered datasets)

## License

MIT
