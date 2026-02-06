/*
  # Add dataset_name column to reports table

  1. Changes
    - Add `dataset_name` column to the reports table
    - This stores the human-readable name of the dataset for display in report lists
    
  2. Notes
    - Column is TEXT and allows NULL for backward compatibility
    - Existing reports will have NULL dataset_name until re-generated
*/

-- Add dataset_name column to reports table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'reports' AND column_name = 'dataset_name'
  ) THEN
    ALTER TABLE reports ADD COLUMN dataset_name text;
  END IF;
END $$;
