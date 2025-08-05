-- Create Scoring Database Tables
-- This script creates all tables for fundamental and technical scoring system

-- 1. Create company_scores_current table
CREATE TABLE IF NOT EXISTS company_scores_current (
    -- Primary Key
    ticker VARCHAR(10) PRIMARY KEY,
    
    -- Calculation Metadata
    date_calculated DATE NOT NULL,
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_freshness_hours INTEGER, -- Hours since last fundamental/technical update
    
    -- Fundamental Health Scores
    fundamental_health_score DECIMAL(5,2) CHECK (fundamental_health_score >= 0 AND fundamental_health_score <= 100),
    fundamental_health_grade VARCHAR(20) CHECK (fundamental_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    fundamental_health_components JSONB, -- Detailed component breakdown
    
    -- Risk Assessment Scores
    fundamental_risk_score DECIMAL(5,2) CHECK (fundamental_risk_score >= 0 AND fundamental_risk_score <= 100),
    fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    fundamental_risk_components JSONB,
    
    -- Value Investment Scores
    value_investment_score DECIMAL(5,2) CHECK (value_investment_score >= 0 AND value_investment_score <= 100),
    value_rating VARCHAR(20) CHECK (value_rating IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    value_components JSONB,
    
    -- Technical Health Scores
    technical_health_score DECIMAL(5,2) CHECK (technical_health_score >= 0 AND technical_health_score <= 100),
    technical_health_grade VARCHAR(20) CHECK (technical_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    technical_health_components JSONB,
    
    -- Trading Signal Scores
    trading_signal_score DECIMAL(5,2) CHECK (trading_signal_score >= 0 AND trading_signal_score <= 100),
    trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    trading_signal_components JSONB,
    
    -- Technical Risk Scores
    technical_risk_score DECIMAL(5,2) CHECK (technical_risk_score >= 0 AND technical_risk_score <= 100),
    technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    technical_risk_components JSONB,
    
    -- Trend Analysis (Pre-calculated)
    fundamental_health_trend VARCHAR(10) CHECK (fundamental_health_trend IN ('improving', 'stable', 'declining')),
    technical_health_trend VARCHAR(10) CHECK (technical_health_trend IN ('improving', 'stable', 'declining')),
    trading_signal_trend VARCHAR(10) CHECK (trading_signal_trend IN ('improving', 'stable', 'declining')),
    
    -- Period Changes (Pre-calculated)
    fundamental_health_change_3m DECIMAL(5,2), -- Change over last 3 months
    fundamental_health_change_6m DECIMAL(5,2), -- Change over last 6 months
    fundamental_health_change_1y DECIMAL(5,2), -- Change over last 1 year
    
    technical_health_change_3m DECIMAL(5,2),
    technical_health_change_6m DECIMAL(5,2),
    technical_health_change_1y DECIMAL(5,2),
    
    trading_signal_change_3m DECIMAL(5,2),
    trading_signal_change_6m DECIMAL(5,2),
    trading_signal_change_1y DECIMAL(5,2),
    
    -- Alert System
    fundamental_red_flags JSONB, -- Array of red flag descriptions
    fundamental_yellow_flags JSONB, -- Array of yellow flag descriptions
    technical_red_flags JSONB,
    technical_yellow_flags JSONB,
    
    -- Composite Scores (Optional)
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    overall_grade VARCHAR(20) CHECK (overall_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    
    -- Metadata
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create company_scores_historical table
CREATE TABLE IF NOT EXISTS company_scores_historical (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date_calculated DATE NOT NULL,
    
    -- Fundamental Scores
    fundamental_health_score DECIMAL(5,2) CHECK (fundamental_health_score >= 0 AND fundamental_health_score <= 100),
    fundamental_health_grade VARCHAR(20) CHECK (fundamental_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    fundamental_health_components JSONB,
    
    fundamental_risk_score DECIMAL(5,2) CHECK (fundamental_risk_score >= 0 AND fundamental_risk_score <= 100),
    fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    fundamental_risk_components JSONB,
    
    value_investment_score DECIMAL(5,2) CHECK (value_investment_score >= 0 AND value_investment_score <= 100),
    value_rating VARCHAR(20) CHECK (value_rating IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    value_components JSONB,
    
    -- Technical Scores
    technical_health_score DECIMAL(5,2) CHECK (technical_health_score >= 0 AND technical_health_score <= 100),
    technical_health_grade VARCHAR(20) CHECK (technical_health_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    technical_health_components JSONB,
    
    trading_signal_score DECIMAL(5,2) CHECK (trading_signal_score >= 0 AND trading_signal_score <= 100),
    trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    trading_signal_components JSONB,
    
    technical_risk_score DECIMAL(5,2) CHECK (technical_risk_score >= 0 AND technical_risk_score <= 100),
    technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    technical_risk_components JSONB,
    
    -- Composite Score
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    overall_grade VARCHAR(20) CHECK (overall_grade IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    
    -- Alerts
    fundamental_red_flags JSONB,
    fundamental_yellow_flags JSONB,
    technical_red_flags JSONB,
    technical_yellow_flags JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(ticker, date_calculated)
);

-- 3. Create score_calculation_logs table
CREATE TABLE IF NOT EXISTS score_calculation_logs (
    id SERIAL PRIMARY KEY,
    calculation_date DATE NOT NULL,
    calculation_batch_id VARCHAR(50), -- For grouping related calculations
    
    -- Processing Statistics
    total_tickers_processed INTEGER,
    successful_calculations INTEGER,
    failed_calculations INTEGER,
    skipped_calculations INTEGER,
    
    -- Performance Metrics
    calculation_duration_seconds DECIMAL(8,2),
    average_calculation_time_per_ticker DECIMAL(6,3),
    
    -- Data Quality Metrics
    tickers_with_missing_fundamental_data INTEGER,
    tickers_with_missing_technical_data INTEGER,
    tickers_with_incomplete_ratios INTEGER,
    
    -- Error Tracking
    error_summary JSONB, -- Summary of errors encountered
    warning_summary JSONB, -- Summary of warnings
    
    -- System Information
    system_version VARCHAR(20),
    calculation_version VARCHAR(20),
    
    -- Metadata
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance

-- Indexes for company_scores_current
CREATE INDEX IF NOT EXISTS idx_company_scores_current_date ON company_scores_current(date_calculated);
CREATE INDEX IF NOT EXISTS idx_company_scores_fundamental_health ON company_scores_current(fundamental_health_score DESC);
CREATE INDEX IF NOT EXISTS idx_company_scores_technical_health ON company_scores_current(technical_health_score DESC);
CREATE INDEX IF NOT EXISTS idx_company_scores_trading_signal ON company_scores_current(trading_signal_score DESC);
CREATE INDEX IF NOT EXISTS idx_company_scores_overall ON company_scores_current(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_company_scores_fundamental_risk ON company_scores_current(fundamental_risk_score);
CREATE INDEX IF NOT EXISTS idx_company_scores_technical_risk ON company_scores_current(technical_risk_score);
CREATE INDEX IF NOT EXISTS idx_company_scores_value ON company_scores_current(value_investment_score DESC);

-- Indexes for company_scores_historical
CREATE INDEX IF NOT EXISTS idx_company_scores_historical_ticker_date ON company_scores_historical(ticker, date_calculated DESC);
CREATE INDEX IF NOT EXISTS idx_company_scores_historical_date ON company_scores_historical(date_calculated);
CREATE INDEX IF NOT EXISTS idx_company_scores_historical_fundamental ON company_scores_historical(fundamental_health_score DESC, date_calculated);
CREATE INDEX IF NOT EXISTS idx_company_scores_historical_technical ON company_scores_historical(technical_health_score DESC, date_calculated);
CREATE INDEX IF NOT EXISTS idx_company_scores_historical_overall ON company_scores_historical(overall_score DESC, date_calculated);

-- Indexes for score_calculation_logs
CREATE INDEX IF NOT EXISTS idx_score_calculation_logs_date ON score_calculation_logs(calculation_date DESC);
CREATE INDEX IF NOT EXISTS idx_score_calculation_logs_batch ON score_calculation_logs(calculation_batch_id);

-- Create Database Functions

-- 1. Calculate trend indicators function
CREATE OR REPLACE FUNCTION calculate_trend_indicators(p_ticker VARCHAR(10))
RETURNS TABLE(
    fundamental_health_trend VARCHAR(10),
    technical_health_trend VARCHAR(10),
    trading_signal_trend VARCHAR(10),
    fundamental_health_change_3m DECIMAL(5,2),
    fundamental_health_change_6m DECIMAL(5,2),
    fundamental_health_change_1y DECIMAL(5,2),
    technical_health_change_3m DECIMAL(5,2),
    technical_health_change_6m DECIMAL(5,2),
    technical_health_change_1y DECIMAL(5,2),
    trading_signal_change_3m DECIMAL(5,2),
    trading_signal_change_6m DECIMAL(5,2),
    trading_signal_change_1y DECIMAL(5,2)
) AS $$
DECLARE
    current_fundamental DECIMAL(5,2);
    current_technical DECIMAL(5,2);
    current_trading DECIMAL(5,2);
    fundamental_3m_ago DECIMAL(5,2);
    fundamental_6m_ago DECIMAL(5,2);
    fundamental_1y_ago DECIMAL(5,2);
    technical_3m_ago DECIMAL(5,2);
    technical_6m_ago DECIMAL(5,2);
    technical_1y_ago DECIMAL(5,2);
    trading_3m_ago DECIMAL(5,2);
    trading_6m_ago DECIMAL(5,2);
    trading_1y_ago DECIMAL(5,2);
BEGIN
    -- Get current scores
    SELECT fundamental_health_score, technical_health_score, trading_signal_score
    INTO current_fundamental, current_technical, current_trading
    FROM company_scores_current
    WHERE ticker = p_ticker;
    
    -- Get historical scores for trend calculation
    SELECT fundamental_health_score INTO fundamental_3m_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '3 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT fundamental_health_score INTO fundamental_6m_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '6 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT fundamental_health_score INTO fundamental_1y_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '1 year'
    ORDER BY date_calculated DESC LIMIT 1;
    
    -- Similar queries for technical and trading scores
    SELECT technical_health_score INTO technical_3m_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '3 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT technical_health_score INTO technical_6m_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '6 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT technical_health_score INTO technical_1y_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '1 year'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT trading_signal_score INTO trading_3m_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '3 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT trading_signal_score INTO trading_6m_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '6 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT trading_signal_score INTO trading_1y_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated <= CURRENT_DATE - INTERVAL '1 year'
    ORDER BY date_calculated DESC LIMIT 1;
    
    -- Calculate trends
    fundamental_health_trend := CASE
        WHEN current_fundamental > fundamental_3m_ago + 5 THEN 'improving'
        WHEN current_fundamental < fundamental_3m_ago - 5 THEN 'declining'
        ELSE 'stable'
    END;
    
    technical_health_trend := CASE
        WHEN current_technical > technical_3m_ago + 5 THEN 'improving'
        WHEN current_technical < technical_3m_ago - 5 THEN 'declining'
        ELSE 'stable'
    END;
    
    trading_signal_trend := CASE
        WHEN current_trading > trading_3m_ago + 5 THEN 'improving'
        WHEN current_trading < trading_3m_ago - 5 THEN 'declining'
        ELSE 'stable'
    END;
    
    -- Calculate period changes
    fundamental_health_change_3m := current_fundamental - fundamental_3m_ago;
    fundamental_health_change_6m := current_fundamental - fundamental_6m_ago;
    fundamental_health_change_1y := current_fundamental - fundamental_1y_ago;
    
    technical_health_change_3m := current_technical - technical_3m_ago;
    technical_health_change_6m := current_technical - technical_6m_ago;
    technical_health_change_1y := current_technical - technical_1y_ago;
    
    trading_signal_change_3m := current_trading - trading_3m_ago;
    trading_signal_change_6m := current_trading - trading_6m_ago;
    trading_signal_change_1y := current_trading - trading_1y_ago;
    
    RETURN QUERY SELECT 
        fundamental_health_trend,
        technical_health_trend,
        trading_signal_trend,
        fundamental_health_change_3m,
        fundamental_health_change_6m,
        fundamental_health_change_1y,
        technical_health_change_3m,
        technical_health_change_6m,
        technical_health_change_1y,
        trading_signal_change_3m,
        trading_signal_change_6m,
        trading_signal_change_1y;
END;
$$ LANGUAGE plpgsql;

-- 2. Upsert company scores function
CREATE OR REPLACE FUNCTION upsert_company_scores(
    p_ticker VARCHAR(10),
    p_fundamental_health_score DECIMAL(5,2),
    p_fundamental_health_grade VARCHAR(20),
    p_fundamental_health_components JSONB,
    p_fundamental_risk_score DECIMAL(5,2),
    p_fundamental_risk_level VARCHAR(20),
    p_fundamental_risk_components JSONB,
    p_value_investment_score DECIMAL(5,2),
    p_value_rating VARCHAR(20),
    p_value_components JSONB,
    p_technical_health_score DECIMAL(5,2),
    p_technical_health_grade VARCHAR(20),
    p_technical_health_components JSONB,
    p_trading_signal_score DECIMAL(5,2),
    p_trading_signal_rating VARCHAR(20),
    p_trading_signal_components JSONB,
    p_technical_risk_score DECIMAL(5,2),
    p_technical_risk_level VARCHAR(20),
    p_technical_risk_components JSONB,
    p_overall_score DECIMAL(5,2),
    p_overall_grade VARCHAR(20),
    p_fundamental_red_flags JSONB,
    p_fundamental_yellow_flags JSONB,
    p_technical_red_flags JSONB,
    p_technical_yellow_flags JSONB
) RETURNS VOID AS $$
BEGIN
    -- Insert into historical table
    INSERT INTO company_scores_historical (
        ticker, date_calculated,
        fundamental_health_score, fundamental_health_grade, fundamental_health_components,
        fundamental_risk_score, fundamental_risk_level, fundamental_risk_components,
        value_investment_score, value_rating, value_components,
        technical_health_score, technical_health_grade, technical_health_components,
        trading_signal_score, trading_signal_rating, trading_signal_components,
        technical_risk_score, technical_risk_level, technical_risk_components,
        overall_score, overall_grade,
        fundamental_red_flags, fundamental_yellow_flags,
        technical_red_flags, technical_yellow_flags
    ) VALUES (
        p_ticker, CURRENT_DATE,
        p_fundamental_health_score, p_fundamental_health_grade, p_fundamental_health_components,
        p_fundamental_risk_score, p_fundamental_risk_level, p_fundamental_risk_components,
        p_value_investment_score, p_value_rating, p_value_components,
        p_technical_health_score, p_technical_health_grade, p_technical_health_components,
        p_trading_signal_score, p_trading_signal_rating, p_trading_signal_components,
        p_technical_risk_score, p_technical_risk_level, p_technical_risk_components,
        p_overall_score, p_overall_grade,
        p_fundamental_red_flags, p_fundamental_yellow_flags,
        p_technical_red_flags, p_technical_yellow_flags
    )
    ON CONFLICT (ticker, date_calculated) DO UPDATE SET
        fundamental_health_score = EXCLUDED.fundamental_health_score,
        fundamental_health_grade = EXCLUDED.fundamental_health_grade,
        fundamental_health_components = EXCLUDED.fundamental_health_components,
        fundamental_risk_score = EXCLUDED.fundamental_risk_score,
        fundamental_risk_level = EXCLUDED.fundamental_risk_level,
        fundamental_risk_components = EXCLUDED.fundamental_risk_components,
        value_investment_score = EXCLUDED.value_investment_score,
        value_rating = EXCLUDED.value_rating,
        value_components = EXCLUDED.value_components,
        technical_health_score = EXCLUDED.technical_health_score,
        technical_health_grade = EXCLUDED.technical_health_grade,
        technical_health_components = EXCLUDED.technical_health_components,
        trading_signal_score = EXCLUDED.trading_signal_score,
        trading_signal_rating = EXCLUDED.trading_signal_rating,
        trading_signal_components = EXCLUDED.trading_signal_components,
        technical_risk_score = EXCLUDED.technical_risk_score,
        technical_risk_level = EXCLUDED.technical_risk_level,
        technical_risk_components = EXCLUDED.technical_risk_components,
        overall_score = EXCLUDED.overall_score,
        overall_grade = EXCLUDED.overall_grade,
        fundamental_red_flags = EXCLUDED.fundamental_red_flags,
        fundamental_yellow_flags = EXCLUDED.fundamental_yellow_flags,
        technical_red_flags = EXCLUDED.technical_red_flags,
        technical_yellow_flags = EXCLUDED.technical_yellow_flags,
        created_at = CURRENT_TIMESTAMP;
    
    -- Update current table
    UPDATE company_scores_current SET
        date_calculated = CURRENT_DATE,
        fundamental_health_score = p_fundamental_health_score,
        fundamental_health_grade = p_fundamental_health_grade,
        fundamental_health_components = p_fundamental_health_components,
        fundamental_risk_score = p_fundamental_risk_score,
        fundamental_risk_level = p_fundamental_risk_level,
        fundamental_risk_components = p_fundamental_risk_components,
        value_investment_score = p_value_investment_score,
        value_rating = p_value_rating,
        value_components = p_value_components,
        technical_health_score = p_technical_health_score,
        technical_health_grade = p_technical_health_grade,
        technical_health_components = p_technical_health_components,
        trading_signal_score = p_trading_signal_score,
        trading_signal_rating = p_trading_signal_rating,
        trading_signal_components = p_trading_signal_components,
        technical_risk_score = p_technical_risk_score,
        technical_risk_level = p_technical_risk_level,
        technical_risk_components = p_technical_risk_components,
        overall_score = p_overall_score,
        overall_grade = p_overall_grade,
        fundamental_red_flags = p_fundamental_red_flags,
        fundamental_yellow_flags = p_fundamental_yellow_flags,
        technical_red_flags = p_technical_red_flags,
        technical_yellow_flags = p_technical_yellow_flags,
        updated_at = CURRENT_TIMESTAMP
    WHERE ticker = p_ticker;
    
    -- If no rows updated, insert new record
    IF NOT FOUND THEN
        INSERT INTO company_scores_current (
            ticker, date_calculated,
            fundamental_health_score, fundamental_health_grade, fundamental_health_components,
            fundamental_risk_score, fundamental_risk_level, fundamental_risk_components,
            value_investment_score, value_rating, value_components,
            technical_health_score, technical_health_grade, technical_health_components,
            trading_signal_score, trading_signal_rating, trading_signal_components,
            technical_risk_score, technical_risk_level, technical_risk_components,
            overall_score, overall_grade,
            fundamental_red_flags, fundamental_yellow_flags,
            technical_red_flags, technical_yellow_flags
        ) VALUES (
            p_ticker, CURRENT_DATE,
            p_fundamental_health_score, p_fundamental_health_grade, p_fundamental_health_components,
            p_fundamental_risk_score, p_fundamental_risk_level, p_fundamental_risk_components,
            p_value_investment_score, p_value_rating, p_value_components,
            p_technical_health_score, p_technical_health_grade, p_technical_health_components,
            p_trading_signal_score, p_trading_signal_rating, p_trading_signal_components,
            p_technical_risk_score, p_technical_risk_level, p_technical_risk_components,
            p_overall_score, p_overall_grade,
            p_fundamental_red_flags, p_fundamental_yellow_flags,
            p_technical_red_flags, p_technical_yellow_flags
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create Materialized Views

-- 1. Screener summary view
CREATE MATERIALIZED VIEW IF NOT EXISTS screener_summary_view AS
SELECT 
    csc.ticker,
    s.company_name,
    s.sector,
    s.industry,
    s.market_cap,
    (SELECT close FROM daily_charts WHERE ticker = csc.ticker ORDER BY date DESC LIMIT 1) as current_price,
    csc.date_calculated,
    csc.data_freshness_hours,
    
    -- Fundamental Scores
    csc.fundamental_health_score,
    csc.fundamental_health_grade,
    csc.fundamental_risk_score,
    csc.fundamental_risk_level,
    csc.value_investment_score,
    csc.value_rating,
    
    -- Technical Scores
    csc.technical_health_score,
    csc.technical_health_grade,
    csc.trading_signal_score,
    csc.trading_signal_rating,
    csc.technical_risk_score,
    csc.technical_risk_level,
    
    -- Composite Score
    csc.overall_score,
    csc.overall_grade,
    
    -- Trends
    csc.fundamental_health_trend,
    csc.technical_health_trend,
    csc.trading_signal_trend,
    
    -- Period Changes
    csc.fundamental_health_change_3m,
    csc.fundamental_health_change_6m,
    csc.fundamental_health_change_1y,
    csc.technical_health_change_3m,
    csc.technical_health_change_6m,
    csc.technical_health_change_1y,
    
    -- Alert Counts
    COALESCE(jsonb_array_length(csc.fundamental_red_flags), 0) as fundamental_red_flag_count,
    COALESCE(jsonb_array_length(csc.fundamental_yellow_flags), 0) as fundamental_yellow_flag_count,
    COALESCE(jsonb_array_length(csc.technical_red_flags), 0) as technical_red_flag_count,
    COALESCE(jsonb_array_length(csc.technical_yellow_flags), 0) as technical_yellow_flag_count
    
FROM company_scores_current csc
JOIN stocks s ON csc.ticker = s.ticker
WHERE csc.date_calculated = CURRENT_DATE;

-- Create indexes for materialized view
CREATE INDEX IF NOT EXISTS idx_screener_summary_fundamental ON screener_summary_view(fundamental_health_score DESC);
CREATE INDEX IF NOT EXISTS idx_screener_summary_technical ON screener_summary_view(technical_health_score DESC);
CREATE INDEX IF NOT EXISTS idx_screener_summary_trading ON screener_summary_view(trading_signal_score DESC);
CREATE INDEX IF NOT EXISTS idx_screener_summary_overall ON screener_summary_view(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_screener_summary_sector ON screener_summary_view(sector);
CREATE INDEX IF NOT EXISTS idx_screener_summary_market_cap ON screener_summary_view(market_cap DESC);

-- 2. Score trends view
CREATE MATERIALIZED VIEW IF NOT EXISTS score_trends_view AS
SELECT 
    ticker,
    date_calculated,
    fundamental_health_score,
    technical_health_score,
    trading_signal_score,
    overall_score,
    
    -- Moving Averages for Trend Analysis
    AVG(fundamental_health_score) OVER (
        PARTITION BY ticker 
        ORDER BY date_calculated 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as fundamental_health_30d_avg,
    
    AVG(technical_health_score) OVER (
        PARTITION BY ticker 
        ORDER BY date_calculated 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as technical_health_30d_avg,
    
    AVG(trading_signal_score) OVER (
        PARTITION BY ticker 
        ORDER BY date_calculated 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as trading_signal_30d_avg,
    
    AVG(overall_score) OVER (
        PARTITION BY ticker 
        ORDER BY date_calculated 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as overall_30d_avg
    
FROM company_scores_historical
WHERE date_calculated >= CURRENT_DATE - INTERVAL '90 days';

-- Create index for trends view
CREATE INDEX IF NOT EXISTS idx_score_trends_ticker_date ON score_trends_view(ticker, date_calculated DESC);

-- Create regular views for API optimization

-- 1. Screener filters view
CREATE OR REPLACE VIEW screener_filters_view AS
SELECT 
    ticker,
    company_name,
    sector,
    industry,
    market_cap,
    current_price,
    
    -- Fundamental Filters
    fundamental_health_score,
    fundamental_health_grade,
    fundamental_risk_score,
    fundamental_risk_level,
    value_investment_score,
    value_rating,
    
    -- Technical Filters
    technical_health_score,
    technical_health_grade,
    trading_signal_score,
    trading_signal_rating,
    technical_risk_score,
    technical_risk_level,
    
    -- Composite Filters
    overall_score,
    overall_grade,
    
    -- Trend Filters
    fundamental_health_trend,
    technical_health_trend,
    trading_signal_trend,
    
    -- Alert Filters
    fundamental_red_flag_count,
    fundamental_yellow_flag_count,
    technical_red_flag_count,
    technical_yellow_flag_count,
    
    -- Data Quality
    data_freshness_hours,
    date_calculated
    
FROM screener_summary_view
WHERE date_calculated = CURRENT_DATE;

-- 2. Dashboard metrics view
CREATE OR REPLACE VIEW dashboard_metrics_view AS
SELECT 
    csc.ticker,
    s.company_name,
    s.sector,
    (SELECT close FROM daily_charts WHERE ticker = csc.ticker ORDER BY date DESC LIMIT 1) as current_price,
    
    -- Score Breakdown
    csc.fundamental_health_score,
    csc.technical_health_score,
    csc.trading_signal_score,
    csc.overall_score,
    
    -- Risk Assessment
    csc.fundamental_risk_score,
    csc.technical_risk_score,
    
    -- Value Assessment
    csc.value_investment_score,
    
    -- Trends
    csc.fundamental_health_trend,
    csc.technical_health_trend,
    csc.trading_signal_trend,
    
    -- Period Changes
    csc.fundamental_health_change_3m,
    csc.fundamental_health_change_6m,
    csc.fundamental_health_change_1y,
    csc.technical_health_change_3m,
    csc.technical_health_change_6m,
    csc.technical_health_change_1y,
    
    -- Alerts
    csc.fundamental_red_flags,
    csc.fundamental_yellow_flags,
    csc.technical_red_flags,
    csc.technical_yellow_flags
    
FROM company_scores_current csc
JOIN stocks s ON csc.ticker = s.ticker
WHERE csc.date_calculated = CURRENT_DATE;

-- Add foreign key constraints (if stocks table exists)
-- ALTER TABLE company_scores_current ADD CONSTRAINT fk_company_scores_stocks 
--     FOREIGN KEY (ticker) REFERENCES stocks(ticker);
-- ALTER TABLE company_scores_historical ADD CONSTRAINT fk_company_scores_historical_stocks 
--     FOREIGN KEY (ticker) REFERENCES stocks(ticker);

COMMIT; 