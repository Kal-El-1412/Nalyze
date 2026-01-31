# CloakSheets Connector

Privacy-first local data connector for spreadsheet analysis. This backend service runs locally on your machine and provides secure access to your spreadsheet data without uploading files to the cloud.

## Features

- **Privacy-First**: All data processing happens locally on your machine
- **AI-Powered Chat**: Natural language queries powered by OpenAI (schema-only sharing)
- **SQL Safety**: Server-side validation with keyword blocking and LIMIT enforcement
- **PII Detection**: Automatic detection of emails, phone numbers, and names with masking utilities
- **DuckDB Integration**: Fast analytical queries on CSV, Excel, and Parquet files
- **Local Filesystem Storage**: Dataset registry and job tracking stored in `~/.cloaksheets/`
- **RESTful API**: Clean API interface for the frontend application

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
- OpenAI API key (for chat functionality) - Get one at https://platform.openai.com/api-keys
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

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key:
   # OPENAI_API_KEY=sk-your-key-here
   ```

4. **Storage is automatic**: The connector automatically creates `~/.cloaksheets/` with the necessary directories and registry file on first run. No database setup needed!

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

### Ingest Dataset
```
POST /datasets/{datasetId}/ingest?force=false
```
Start ingesting a registered dataset into DuckDB. This is a background operation that returns immediately.

**Query Parameters:**
- `force` (optional, default: `false`) - Force ingestion of large XLSX files that exceed the 200MB limit

**Response:**
```json
{
  "jobId": "uuid"
}
```

**Behavior:**
- Creates a DuckDB database at `~/.cloaksheets/datasets/{datasetId}/db.duckdb`
- Loads data into a table named `data`
- Generates catalog with column statistics
- Updates job status: `queued` → `running` → `done` or `error`
- Updates dataset status to `ingested` on success

**CSV Ingestion (Recommended):**
- Fastest and most efficient format
- Direct streaming into DuckDB
- No memory limitations
- Handles files of any size

**XLSX Ingestion:**
- Uses chunked reading (10,000 rows per chunk)
- Reads only the first sheet by default
- Prefers named tables if available
- Memory-efficient streaming
- **200 MB limit by default** - larger files will be rejected unless `force=true`
- For files over 200 MB, export to CSV is strongly recommended

**Job Statuses:**
- `queued` - Job created, waiting to start
- `running` - Currently processing the file
- `done` - Ingestion completed successfully
- `error` - Ingestion failed (check job.error field)

### Get Dataset Catalog
```
GET /datasets/{datasetId}/catalog
```
Retrieve metadata and statistics about an ingested dataset.

**Response:**
```json
{
  "table": "data",
  "rowCount": 1000,
  "columns": [
    {"name": "id", "type": "BIGINT"},
    {"name": "amount", "type": "DOUBLE"},
    {"name": "date", "type": "DATE"},
    {"name": "description", "type": "VARCHAR"}
  ],
  "basicStats": {
    "id": {
      "min": 1,
      "max": 1000,
      "avg": 500.5,
      "nullPct": 0
    },
    "amount": {
      "min": 10.5,
      "max": 999.99,
      "avg": 250.75,
      "nullPct": 2.5
    },
    "date": {
      "min": "2024-01-01",
      "max": "2024-12-31",
      "nullPct": 0
    },
    "description": {
      "nullPct": 5.2,
      "approxDistinct": 850
    }
  },
  "detectedDateColumns": ["date"],
  "detectedNumericColumns": ["id", "amount"]
}
```

**Statistics Provided:**
- Numeric columns: min, max, avg, nullPct
- Date columns: min, max, nullPct
- Text columns: nullPct, approxDistinct

**Note:** Dataset must be ingested before catalog is available.

### Execute Queries
```
POST /queries/execute
```
Execute one or more SQL queries against an ingested dataset with built-in safety controls.

**Request Body:**
```json
{
  "datasetId": "uuid",
  "queries": [
    {
      "name": "total_revenue",
      "sql": "SELECT SUM(amount) as total FROM data"
    },
    {
      "name": "top_customers",
      "sql": "SELECT customer_id, COUNT(*) as order_count FROM data GROUP BY customer_id ORDER BY order_count DESC"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "name": "total_revenue",
      "columns": ["total"],
      "rows": [[15432.50]]
    },
    {
      "name": "top_customers",
      "columns": ["customer_id", "order_count"],
      "rows": [
        ["C001", 45],
        ["C002", 38],
        ["C003", 32]
      ]
    }
  ]
}
```

**Safety Features:**
- **Automatic Row Limit:** Results limited to 5,000 rows (server-enforced)
- **Dangerous Keywords Blocked:** DROP, DELETE, UPDATE, INSERT, ATTACH, COPY, EXPORT, CREATE, ALTER, TRUNCATE, REPLACE
- **Query Timeout:** 10 second timeout per query
- **Read-Only Connection:** Database opened in read-only mode

**Error Responses:**
- `400 Bad Request` - Dangerous SQL keyword detected or invalid query
- `404 Not Found` - Dataset not found
- `408 Request Timeout` - Query execution exceeded 10 second timeout
- `500 Internal Server Error` - Query execution failed

### Preview Dataset
```
GET /datasets/{datasetId}/preview?limit=100
```
Quick preview of the first N rows from a dataset for debugging and inspection.

**Query Parameters:**
- `limit` (optional, default: 100, max: 5000) - Number of rows to return

**Response:**
```json
{
  "columns": ["id", "name", "amount", "date"],
  "rows": [
    [1, "Alice", 150.50, "2024-01-15"],
    [2, "Bob", 200.00, "2024-01-16"],
    [3, "Charlie", 175.25, "2024-01-17"]
  ],
  "totalRows": 10000,
  "returnedRows": 3
}
```

**Use Cases:**
- Quick data inspection during development
- Verifying data structure after ingestion
- Debugging data quality issues

**Note:** For production queries, use the `/queries/execute` endpoint instead.

### Get PII Information
```
GET /datasets/{datasetId}/pii
```
Retrieve detected PII columns from the dataset catalog.

**Response:**
```json
{
  "datasetId": "abc-123",
  "piiColumns": [
    {
      "name": "email",
      "type": "email",
      "confidence": 0.95
    },
    {
      "name": "phone_number",
      "type": "phone",
      "confidence": 0.87
    },
    {
      "name": "customer_name",
      "type": "name",
      "confidence": 0.72
    }
  ]
}
```

**PII Types:**
- `email` - Email addresses (pattern: user@domain.com)
- `phone` - Phone numbers (various formats including international)
- `name` - Full names (heuristic: capitalized multi-word text)

**Confidence Scores:**
- 0.0 - 0.3: Low confidence (not reported)
- 0.3 - 0.6: Medium confidence
- 0.6 - 0.8: High confidence
- 0.8 - 1.0: Very high confidence

**Detection Method:**
- Runs automatically during ingestion
- Samples up to 1,000 rows for pattern matching
- Uses regex patterns and heuristics
- Results stored in catalog.json

**Privacy Notes:**
- PII detection is local-only
- Raw data never leaves your machine
- Masking utilities available for future "sample sharing" feature (not in MVP)
- Masking examples:
  - Email: `john@example.com` → `j***@example.com`
  - Phone: `0412345678` → `04******78`
  - Name: `John Smith` → `Person_a3f8b9c1`

**Use Cases:**
- Identify sensitive columns before sharing analysis
- Audit data privacy compliance
- Guide data handling policies
- Alert users to potential PII in datasets

### Chat (Privacy-First AI Orchestrator)
```
POST /chat
```
Conversational interface for data analysis powered by OpenAI with strict privacy enforcement.

**Request Body:**
```json
{
  "datasetId": "uuid",
  "conversationId": "uuid",
  "message": "Show me monthly trends",
  "resultsContext": {
    "results": [
      {
        "name": "monthly_trend",
        "columns": ["month", "total"],
        "rows": [
          ["2024-01", 1500],
          ["2024-02", 1800]
        ]
      }
    ]
  }
}
```

**Response Types:**

**1. needs_clarification** - When more information is needed:
```json
{
  "type": "needs_clarification",
  "question": "Dataset is not ingested yet. Run ingestion now?",
  "choices": ["Ingest now"],
  "audit": {
    "sharedWithAI": ["schema", "aggregates_only"]
  }
}
```

**2. run_queries** - When queries should be executed:
```json
{
  "type": "run_queries",
  "queries": [
    {
      "name": "monthly_trend",
      "sql": "SELECT DATE_TRUNC('month', date) as month, COUNT(*) as count FROM data GROUP BY month"
    }
  ],
  "explanation": "I'll analyze the monthly trends using the date column.",
  "audit": {
    "sharedWithAI": ["schema", "aggregates_only"]
  }
}
```

**3. final_answer** - When presenting results:
```json
{
  "type": "final_answer",
  "message": "I found 1 result:\n\n**monthly_trend**: 12 rows returned\n  (showing first 5 of 12 rows)",
  "tables": [
    {
      "title": "monthly_trend",
      "columns": ["month", "count"],
      "rows": [
        ["2024-01", 150],
        ["2024-02", 180],
        ["2024-03", 165]
      ]
    }
  ],
  "audit": {
    "sharedWithAI": ["schema", "aggregates_only"]
  }
}
```

**Behavior:**
- Validates `OPENAI_API_KEY` environment variable is set
- Checks dataset is ingested before proceeding
- Sends only schema and column statistics to OpenAI (never raw rows)
- AI generates safe, validated SQL queries from natural language
- Asks clarifying questions when date/metric is ambiguous
- Summarizes results in user-friendly language
- Tracks what data is shared via audit field

**Privacy Guarantees:**
- ✅ ONLY schema and column statistics sent to OpenAI
- ✅ ONLY aggregated query results sent to OpenAI
- ✅ NEVER sends raw data rows
- ✅ All queries validated server-side before execution
- ✅ Audit trail tracks exactly what's shared: `["schema", "aggregates_only"]`

**SQL Safety Features:**
- LIMIT clause enforcement (max 10,000 rows)
- Keyword blocklist prevents: DROP, DELETE, INSERT, UPDATE, TRUNCATE, ALTER, CREATE, GRANT, REVOKE, EXEC, PRAGMA, ATTACH, DETACH
- Query count limit (max 3 queries per request)
- Server-side validation before any execution
- Only SELECT statements allowed

**Error Handling:**
- Returns 400 error if `OPENAI_API_KEY` not set
- Returns `needs_clarification` for invalid queries
- Graceful error messages for OpenAI API failures

**Use Cases:**
- Natural language data exploration
- Quick trend analysis without writing SQL
- Guided data discovery with AI assistance
- Privacy-preserving analytics

**Model:** Uses GPT-4 Turbo for optimal SQL generation and result summarization.

## Supported File Formats

### CSV (Recommended)
- **Format:** `.csv`
- **Performance:** Fastest
- **Size Limit:** None
- **Method:** Direct streaming into DuckDB
- **Best for:** Large datasets, production use

### Excel
- **Format:** `.xlsx`, `.xls`
- **Performance:** Good (chunked reading)
- **Size Limit:** 200 MB (can be overridden with `force=true`)
- **Method:** Memory-efficient row streaming (10,000 rows per chunk)
- **Sheet Selection:** First sheet by default, prefers named tables
- **Note:** For files over 200 MB, export to CSV for better performance

### Parquet
- **Format:** `.parquet`
- **Status:** Registered support only (ingestion not yet implemented)

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

### Ingestion errors
- Check the job status via `GET /jobs` to see the error message
- Verify the file is properly formatted
- Large files may take time to ingest - check job status periodically
- If ingestion fails, you can retry by calling the ingest endpoint again
- DuckDB files are stored at `~/.cloaksheets/datasets/{datasetId}/db.duckdb`

### XLSX file size errors
- If you get a "file exceeds recommended limit" error, you have two options:
  1. **Recommended:** Export the Excel file to CSV format for better performance
  2. Add `?force=true` to the ingest endpoint to bypass the 200 MB limit
- Large XLSX files (>200 MB) will be slower than CSV due to Excel format overhead
- CSV ingestion has no size limits and is significantly faster

### XLSX ingestion issues
- Only the first sheet is ingested by default
- Empty rows are automatically skipped
- Headers are inferred from the first row
- If the first row has empty cells, columns will be named `column_1`, `column_2`, etc.
- Named tables in the workbook are preferred if detected
- All data is converted to text initially, DuckDB handles type inference in queries

## License

MIT
