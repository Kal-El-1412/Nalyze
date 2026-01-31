/*
  # Create CloakSheets Connector Tables

  1. New Tables
    - `datasets`
      - `id` (text, primary key) - Unique dataset identifier
      - `name` (text, not null) - Human-readable dataset name
      - `file_path` (text, not null) - Absolute path to local file
      - `description` (text, nullable) - Optional dataset description
      - `row_count` (integer, nullable) - Number of rows in dataset
      - `column_count` (integer, nullable) - Number of columns in dataset
      - `columns` (jsonb, nullable) - Array of column names
      - `status` (text, not null, default 'active') - Dataset status: active, error, scanning
      - `created_at` (timestamptz, not null, default now()) - Creation timestamp
      - `updated_at` (timestamptz, not null, default now()) - Last update timestamp

    - `jobs`
      - `id` (text, primary key) - Unique job identifier
      - `dataset_id` (text, not null, foreign key) - Reference to dataset
      - `job_type` (text, not null) - Type of job: pii_scan, ingestion, analysis
      - `status` (text, not null, default 'pending') - Job status: pending, running, completed, failed
      - `progress` (real, default 0.0) - Job progress (0.0 to 1.0)
      - `result` (jsonb, nullable) - Job result data
      - `error` (text, nullable) - Error message if job failed
      - `created_at` (timestamptz, not null, default now()) - Creation timestamp
      - `updated_at` (timestamptz, not null, default now()) - Last update timestamp

  2. Security
    - Enable RLS on both tables
    - Add permissive policies for all operations (to be restricted later based on auth)

  3. Important Notes
    - These tables store metadata only; actual data stays local on user's machine
    - Dataset file_path points to local filesystem, not uploaded files
    - Jobs track background operations like PII scanning
    - Status fields use text for flexibility (can add enum types later if needed)
*/

-- Create datasets table
CREATE TABLE IF NOT EXISTS datasets (
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

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  progress REAL DEFAULT 0.0,
  result JSONB,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_dataset
    FOREIGN KEY (dataset_id)
    REFERENCES datasets(id)
    ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_dataset_id ON jobs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Enable Row Level Security
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Create permissive policies (allow all operations for now)
-- Note: These should be restricted based on your authentication setup
CREATE POLICY "Allow all operations on datasets"
  ON datasets
  FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on jobs"
  ON jobs
  FOR ALL
  USING (true)
  WITH CHECK (true);
