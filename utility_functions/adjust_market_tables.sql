-- 1. Adjust market_etf table for naming and consistency
ALTER TABLE market_etf RENAME COLUMN etf_index_name TO etf_name;
ALTER TABLE market_etf RENAME COLUMN ticker TO etf_ticker;

-- Add unique constraint if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name='market_etf' AND constraint_type='UNIQUE' AND constraint_name='market_etf_category_indicator_etf_ticker_key'
    ) THEN
        ALTER TABLE market_etf ADD CONSTRAINT market_etf_category_indicator_etf_ticker_key UNIQUE (category, indicator, etf_ticker);
    END IF;
END$$;

-- 2. Adjust market_data table to match sectors table
-- Add columns if not exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='ticker') THEN
        ALTER TABLE market_data ADD COLUMN ticker VARCHAR(10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='category') THEN
        ALTER TABLE market_data ADD COLUMN category VARCHAR;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='indicator') THEN
        ALTER TABLE market_data ADD COLUMN indicator VARCHAR;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='etf_name') THEN
        ALTER TABLE market_data ADD COLUMN etf_name VARCHAR;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='date') THEN
        ALTER TABLE market_data ADD COLUMN date DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='open') THEN
        ALTER TABLE market_data ADD COLUMN open BIGINT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='high') THEN
        ALTER TABLE market_data ADD COLUMN high BIGINT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='low') THEN
        ALTER TABLE market_data ADD COLUMN low BIGINT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='close') THEN
        ALTER TABLE market_data ADD COLUMN close BIGINT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='volume') THEN
        ALTER TABLE market_data ADD COLUMN volume BIGINT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='created_at') THEN
        ALTER TABLE market_data ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_data' AND column_name='updated_at') THEN
        ALTER TABLE market_data ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END$$;

-- Add primary key on (ticker, date) if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name='market_data' AND constraint_type='PRIMARY KEY'
    ) THEN
        ALTER TABLE market_data ADD CONSTRAINT market_data_pkey PRIMARY KEY (ticker, date);
    END IF;
END$$; 