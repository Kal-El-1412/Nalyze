# CloakSheets Connector

Privacy-first local data connector for spreadsheet analysis. This backend service runs locally on your machine and provides secure access to your spreadsheet data without uploading files to the cloud.

## Features

- **Privacy-First**: All data processing happens locally on your machine
- **DuckDB Integration**: Fast analytical queries on CSV, Excel, and Parquet files
- **Supabase Metadata Storage**: Dataset registry and job tracking stored securely
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
                            │    Supabase     │
                            │   (datasets,    │
                            │     jobs)       │
                            └─────────────────┘
```

## Requirements

- Python 3.11+
- Supabase account (for metadata storage)
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

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

4. **Set up the database** (see Database Setup below)

## Database Setup

You need to create two tables in your Supabase database:

```sql
-- Datasets table
CREATE TABLE datasets (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  description TEXT,
  row_count INTEGER,
  column_count INTEGER,
  columns JSONB,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  progress REAL DEFAULT 0.0,
  result JSONB,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth setup)
CREATE POLICY "Allow all operations for now" ON datasets FOR ALL USING (true);
CREATE POLICY "Allow all operations for now" ON jobs FOR ALL USING (true);
```

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

## Supported File Formats

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Parquet (`.parquet`)

## Security Notes

- All file operations are read-only
- SQL queries are validated to prevent destructive operations
- Files never leave your local machine (except metadata to Supabase)
- Use environment variables for sensitive configuration

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

### Database errors
- Verify Supabase credentials in `.env`
- Ensure database tables are created
- Check RLS policies allow operations

### File not found
- Use absolute file paths
- Verify file permissions
- Check file format is supported

## License

MIT
