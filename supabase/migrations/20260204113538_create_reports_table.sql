/*
  # Create reports table for saved analyses

  1. New Tables
    - `reports`
      - `id` (uuid, primary key) - Unique report identifier
      - `dataset_id` (text) - Reference to the dataset
      - `conversation_id` (text) - Reference to the conversation that generated this report
      - `question` (text) - The original question asked
      - `analysis_type` (text) - Type of analysis performed
      - `time_period` (text) - Time period analyzed (if applicable)
      - `summary_markdown` (text) - Formatted summary of the analysis
      - `tables` (jsonb) - Array of result tables with data
      - `audit_log` (jsonb) - Array of audit log entries
      - `created_at` (timestamptz) - Report creation timestamp
      - `privacy_mode` (boolean) - Whether privacy mode was enabled
      - `safe_mode` (boolean) - Whether safe mode was enabled
      
  2. Security
    - Enable RLS on reports table
    - Allow authenticated users to view and create reports
    
  3. Indexes
    - Index on dataset_id for filtering by dataset
    - Index on created_at for chronological ordering
    - Index on conversation_id for linking to conversations
*/

-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_id text NOT NULL,
  conversation_id text NOT NULL,
  question text NOT NULL DEFAULT '',
  analysis_type text DEFAULT '',
  time_period text DEFAULT '',
  summary_markdown text NOT NULL DEFAULT '',
  tables jsonb DEFAULT '[]'::jsonb,
  audit_log jsonb DEFAULT '[]'::jsonb,
  created_at timestamptz DEFAULT now(),
  privacy_mode boolean DEFAULT true,
  safe_mode boolean DEFAULT false
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_reports_dataset_id ON reports(dataset_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_conversation_id ON reports(conversation_id);

-- Enable Row Level Security
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Create policies for reports table
CREATE POLICY "Users can view reports"
  ON reports FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can create reports"
  ON reports FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can update reports"
  ON reports FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Users can delete reports"
  ON reports FOR DELETE
  TO authenticated
  USING (true);