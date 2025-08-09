-- Database Migration: Increase Volume-Based Technical Indicator Column Precision
-- This addresses OBV and VPT indicators being capped at 10M when they can legitimately reach 100M+

-- Current: NUMERIC(15,4) allows max ~10^11 
-- After *100 storage: Safe limit was 1e7 (10M)
-- New: NUMERIC(18,4) allows max ~10^14
-- After *100 storage: Safe limit will be 1e10 (10B) - sufficient for volume indicators

BEGIN;

-- Increase precision for volume-based technical indicators
-- OBV (On-Balance Volume) and VPT (Volume Price Trend) can accumulate to 100M+ easily

ALTER TABLE daily_charts 
    ALTER COLUMN obv TYPE NUMERIC(18,4);

ALTER TABLE daily_charts 
    ALTER COLUMN vpt TYPE NUMERIC(18,4);

-- Optional: Increase precision for other volume-related indicators that might also grow large
ALTER TABLE daily_charts 
    ALTER COLUMN volume_confirmation TYPE NUMERIC(18,4);

ALTER TABLE daily_charts 
    ALTER COLUMN volume_weighted_high TYPE NUMERIC(18,4);

ALTER TABLE daily_charts 
    ALTER COLUMN volume_weighted_low TYPE NUMERIC(18,4);

-- Add comment for documentation
COMMENT ON COLUMN daily_charts.obv IS 'On-Balance Volume (multiplied by 100 for storage) - increased precision for large cumulative values';
COMMENT ON COLUMN daily_charts.vpt IS 'Volume Price Trend (multiplied by 100 for storage) - increased precision for large cumulative values';

COMMIT;

-- Verification query - check the new column types
SELECT column_name, data_type, numeric_precision, numeric_scale 
FROM information_schema.columns 
WHERE table_name = 'daily_charts' 
AND column_name IN ('obv', 'vpt', 'volume_confirmation', 'volume_weighted_high', 'volume_weighted_low')
ORDER BY column_name;
