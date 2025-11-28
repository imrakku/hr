/*
  # Create Candidate Evaluations Table

  1. New Tables
    - `candidate_evaluations`
      - `id` (uuid, primary key)
      - `job_title` (text) - The job position being evaluated for
      - `candidate_name` (text) - Name of the candidate
      - `score` (numeric) - Evaluation score from 0-10
      - `fit_level` (text) - High, Medium, or Low fit
      - `rationale` (text) - Reasoning for the evaluation
      - `matched_skills` (text) - Comma-separated list of matched skills
      - `missing_skills` (text) - Comma-separated list of missing skills
      - `qualifications` (text) - Educational qualifications and certifications
      - `achievements` (text) - Quantifiable achievements
      - `evaluated_at` (timestamptz) - Timestamp of evaluation
      - `created_at` (timestamptz) - Record creation timestamp

  2. Security
    - Enable RLS on `candidate_evaluations` table
    - Add policy for public read access (for demo purposes)
    - Add policy for public insert access (for demo purposes)

  3. Indexes
    - Index on job_title for faster filtering
    - Index on score for sorting
    - Index on evaluated_at for chronological queries
*/

CREATE TABLE IF NOT EXISTS candidate_evaluations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_title text NOT NULL,
  candidate_name text NOT NULL,
  score numeric NOT NULL DEFAULT 0,
  fit_level text NOT NULL DEFAULT 'Low',
  rationale text DEFAULT '',
  matched_skills text DEFAULT '',
  missing_skills text DEFAULT '',
  qualifications text DEFAULT '',
  achievements text DEFAULT '',
  evaluated_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

ALTER TABLE candidate_evaluations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view evaluations"
  ON candidate_evaluations
  FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Anyone can insert evaluations"
  ON candidate_evaluations
  FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_candidate_evaluations_job_title 
  ON candidate_evaluations(job_title);

CREATE INDEX IF NOT EXISTS idx_candidate_evaluations_score 
  ON candidate_evaluations(score DESC);

CREATE INDEX IF NOT EXISTS idx_candidate_evaluations_evaluated_at 
  ON candidate_evaluations(evaluated_at DESC);
