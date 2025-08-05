-- Add confidence and validation columns to scoring tables
ALTER TABLE company_scores_current 
ADD COLUMN IF NOT EXISTS data_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS missing_metrics TEXT[],
ADD COLUMN IF NOT EXISTS data_warnings TEXT[],
ADD COLUMN IF NOT EXISTS estimated_ratios TEXT[],
ADD COLUMN IF NOT EXISTS ratio_validation_status JSONB;

ALTER TABLE company_scores_historical 
ADD COLUMN IF NOT EXISTS data_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS missing_metrics TEXT[],
ADD COLUMN IF NOT EXISTS data_warnings TEXT[],
ADD COLUMN IF NOT EXISTS estimated_ratios TEXT[],
ADD COLUMN IF NOT EXISTS ratio_validation_status JSONB;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_company_scores_current_confidence ON company_scores_current(data_confidence);
CREATE INDEX IF NOT EXISTS idx_company_scores_historical_confidence ON company_scores_historical(data_confidence); 