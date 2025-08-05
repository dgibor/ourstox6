-- Fix Database Schema for Scoring System
-- This script increases the string length for grade/rating/level columns
-- to accommodate the 5-level normalization system

-- Fix company_scores_current table
ALTER TABLE company_scores_current 
ALTER COLUMN fundamental_health_grade TYPE character varying(20),
ALTER COLUMN value_rating TYPE character varying(20),
ALTER COLUMN fundamental_risk_level TYPE character varying(20),
ALTER COLUMN technical_health_grade TYPE character varying(20),
ALTER COLUMN trading_signal_rating TYPE character varying(20),
ALTER COLUMN technical_risk_level TYPE character varying(20),
ALTER COLUMN overall_grade TYPE character varying(20);

-- Fix company_scores_historical table
ALTER TABLE company_scores_historical 
ALTER COLUMN fundamental_health_grade TYPE character varying(20),
ALTER COLUMN value_rating TYPE character varying(20),
ALTER COLUMN fundamental_risk_level TYPE character varying(20),
ALTER COLUMN technical_health_grade TYPE character varying(20),
ALTER COLUMN trading_signal_rating TYPE character varying(20),
ALTER COLUMN technical_risk_level TYPE character varying(20),
ALTER COLUMN overall_grade TYPE character varying(20);

-- Verify the changes
SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name IN ('company_scores_current', 'company_scores_historical')
AND column_name LIKE '%grade%' OR column_name LIKE '%rating%' OR column_name LIKE '%level%'
ORDER BY table_name, column_name; 