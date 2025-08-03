# Scoring Database Schema for Fundamental and Technical Analysis

## Executive Summary

This document defines the database schema for storing fundamental and technical analysis scores calculated by the daily_run cron system. The schema supports both current daily status and historical trends, enabling efficient querying for screeners and dashboards through API endpoints.

## Database Design Philosophy

### 1. **Hybrid Approach**
- **Current Scores Table**: One row per ticker with latest scores and pre-calculated trends
- **Historical Scores Table**: Multiple rows per ticker for deep analysis and backtesting
- **Component Details Table**: Detailed breakdown of score components for analysis

### 2. **Performance Optimization**
- **Indexed Queries**: Optimized for screener filtering and sorting
- **Partitioning**: Historical data partitioned by date for efficient querying
- **Materialized Views**: Pre-calculated aggregations for dashboard performance

### 3. **Data Integrity**
- **Foreign Key Constraints**: Ensure referential integrity with stocks table
- **Unique Constraints**: Prevent duplicate entries
- **Check Constraints**: Validate score ranges and data consistency

## Core Tables Schema

### 1. **company_scores_current** - Current Daily Scores

**Purpose**: Store the latest scores for each ticker with pre-calculated trends and alerts.

```sql
CREATE TABLE company_scores_current (
    -- Primary Key
    ticker VARCHAR(10) PRIMARY KEY,
    
    -- Calculation Metadata
    date_calculated DATE NOT NULL,
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_freshness_hours INTEGER, -- Hours since last fundamental/technical update
    
    -- Fundamental Health Scores
    fundamental_health_score DECIMAL(5,2) CHECK (fundamental_health_score >= 0 AND fundamental_health_score <= 100),
    fundamental_health_grade VARCHAR(2) CHECK (fundamental_health_grade IN ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F')),
    fundamental_health_components JSONB, -- Detailed component breakdown
    
    -- Risk Assessment Scores
    fundamental_risk_score DECIMAL(5,2) CHECK (fundamental_risk_score >= 0 AND fundamental_risk_score <= 100),
    fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Low Risk', 'Moderate Risk', 'High Risk', 'Very High Risk', 'Extreme Risk')),
    fundamental_risk_components JSONB,
    
    -- Value Investment Scores
    value_investment_score DECIMAL(5,2) CHECK (value_investment_score >= 0 AND value_investment_score <= 100),
    value_rating VARCHAR(20) CHECK (value_rating IN ('Excellent Value', 'Good Value', 'Fair Value', 'Overvalued', 'Highly Overvalued')),
    value_components JSONB,
    
    -- Technical Health Scores
    technical_health_score DECIMAL(5,2) CHECK (technical_health_score >= 0 AND technical_health_score <= 100),
    technical_health_grade VARCHAR(2) CHECK (technical_health_grade IN ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F')),
    technical_health_components JSONB,
    
    -- Trading Signal Scores
    trading_signal_score DECIMAL(5,2) CHECK (trading_signal_score >= 0 AND trading_signal_score <= 100),
    trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    trading_signal_components JSONB,
    
    -- Technical Risk Scores
    technical_risk_score DECIMAL(5,2) CHECK (technical_risk_score >= 0 AND technical_risk_score <= 100),
    technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Low Risk', 'Moderate Risk', 'High Risk', 'Very High Risk', 'Extreme Risk')),
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
    overall_grade VARCHAR(2) CHECK (overall_grade IN ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F')),
    
    -- Metadata
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    CONSTRAINT fk_company_scores_stocks FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Indexes for Performance
CREATE INDEX idx_company_scores_current_date ON company_scores_current(date_calculated);
CREATE INDEX idx_company_scores_fundamental_health ON company_scores_current(fundamental_health_score DESC);
CREATE INDEX idx_company_scores_technical_health ON company_scores_current(technical_health_score DESC);
CREATE INDEX idx_company_scores_trading_signal ON company_scores_current(trading_signal_score DESC);
CREATE INDEX idx_company_scores_overall ON company_scores_current(overall_score DESC);
CREATE INDEX idx_company_scores_fundamental_risk ON company_scores_current(fundamental_risk_score);
CREATE INDEX idx_company_scores_technical_risk ON company_scores_current(technical_risk_score);
CREATE INDEX idx_company_scores_value ON company_scores_current(value_investment_score DESC);
```

### 2. **company_scores_historical** - Historical Score Tracking

**Purpose**: Store all historical score calculations for trend analysis and backtesting.

```sql
CREATE TABLE company_scores_historical (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date_calculated DATE NOT NULL,
    
    -- Fundamental Scores
    fundamental_health_score DECIMAL(5,2) CHECK (fundamental_health_score >= 0 AND fundamental_health_score <= 100),
    fundamental_health_grade VARCHAR(2) CHECK (fundamental_health_grade IN ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F')),
    fundamental_health_components JSONB,
    
    fundamental_risk_score DECIMAL(5,2) CHECK (fundamental_risk_score >= 0 AND fundamental_risk_score <= 100),
    fundamental_risk_level VARCHAR(20) CHECK (fundamental_risk_level IN ('Low Risk', 'Moderate Risk', 'High Risk', 'Very High Risk', 'Extreme Risk')),
    fundamental_risk_components JSONB,
    
    value_investment_score DECIMAL(5,2) CHECK (value_investment_score >= 0 AND value_investment_score <= 100),
    value_rating VARCHAR(20) CHECK (value_rating IN ('Excellent Value', 'Good Value', 'Fair Value', 'Overvalued', 'Highly Overvalued')),
    value_components JSONB,
    
    -- Technical Scores
    technical_health_score DECIMAL(5,2) CHECK (technical_health_score >= 0 AND technical_health_score <= 100),
    technical_health_grade VARCHAR(2) CHECK (technical_health_grade IN ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F')),
    technical_health_components JSONB,
    
    trading_signal_score DECIMAL(5,2) CHECK (trading_signal_score >= 0 AND trading_signal_score <= 100),
    trading_signal_rating VARCHAR(20) CHECK (trading_signal_rating IN ('Strong Buy', 'Buy', 'Neutral', 'Sell', 'Strong Sell')),
    trading_signal_components JSONB,
    
    technical_risk_score DECIMAL(5,2) CHECK (technical_risk_score >= 0 AND technical_risk_score <= 100),
    technical_risk_level VARCHAR(20) CHECK (technical_risk_level IN ('Low Risk', 'Moderate Risk', 'High Risk', 'Very High Risk', 'Extreme Risk')),
    technical_risk_components JSONB,
    
    -- Composite Score
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    overall_grade VARCHAR(2) CHECK (overall_grade IN ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F')),
    
    -- Alerts
    fundamental_red_flags JSONB,
    fundamental_yellow_flags JSONB,
    technical_red_flags JSONB,
    technical_yellow_flags JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(ticker, date_calculated),
    CONSTRAINT fk_company_scores_historical_stocks FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Indexes for Performance
CREATE INDEX idx_company_scores_historical_ticker_date ON company_scores_historical(ticker, date_calculated DESC);
CREATE INDEX idx_company_scores_historical_date ON company_scores_historical(date_calculated);
CREATE INDEX idx_company_scores_historical_fundamental ON company_scores_historical(fundamental_health_score DESC, date_calculated);
CREATE INDEX idx_company_scores_historical_technical ON company_scores_historical(technical_health_score DESC, date_calculated);
CREATE INDEX idx_company_scores_historical_overall ON company_scores_historical(overall_score DESC, date_calculated);

-- Partitioning for Large Historical Data (Optional)
-- CREATE TABLE company_scores_historical_2024 PARTITION OF company_scores_historical
-- FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 3. **score_calculation_logs** - Calculation Tracking

**Purpose**: Track calculation performance, errors, and data quality metrics.

```sql
CREATE TABLE score_calculation_logs (
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

-- Indexes
CREATE INDEX idx_score_calculation_logs_date ON score_calculation_logs(calculation_date DESC);
CREATE INDEX idx_score_calculation_logs_batch ON score_calculation_logs(calculation_batch_id);
```

## Materialized Views for Dashboard Performance

### 1. **screener_summary_view** - Optimized Screener Data

```sql
CREATE MATERIALIZED VIEW screener_summary_view AS
SELECT 
    csc.ticker,
    s.company_name,
    s.sector,
    s.industry,
    s.market_cap,
    s.current_price,
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
    jsonb_array_length(csc.fundamental_red_flags) as fundamental_red_flag_count,
    jsonb_array_length(csc.fundamental_yellow_flags) as fundamental_yellow_flag_count,
    jsonb_array_length(csc.technical_red_flags) as technical_red_flag_count,
    jsonb_array_length(csc.technical_yellow_flags) as technical_yellow_flag_count
    
FROM company_scores_current csc
JOIN stocks s ON csc.ticker = s.ticker
WHERE csc.date_calculated = CURRENT_DATE;

-- Indexes for Materialized View
CREATE INDEX idx_screener_summary_fundamental ON screener_summary_view(fundamental_health_score DESC);
CREATE INDEX idx_screener_summary_technical ON screener_summary_view(technical_health_score DESC);
CREATE INDEX idx_screener_summary_trading ON screener_summary_view(trading_signal_score DESC);
CREATE INDEX idx_screener_summary_overall ON screener_summary_view(overall_score DESC);
CREATE INDEX idx_screener_summary_sector ON screener_summary_view(sector);
CREATE INDEX idx_screener_summary_market_cap ON screener_summary_view(market_cap DESC);
```

### 2. **score_trends_view** - Trend Analysis

```sql
CREATE MATERIALIZED VIEW score_trends_view AS
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

-- Indexes
CREATE INDEX idx_score_trends_ticker_date ON score_trends_view(ticker, date_calculated DESC);
```

## Database Functions for Score Calculation

### 1. **calculate_trend_indicators()** - Trend Calculation Function

```sql
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
    WHERE ticker = p_ticker AND date_calculated = CURRENT_DATE - INTERVAL '3 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT fundamental_health_score INTO fundamental_6m_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated = CURRENT_DATE - INTERVAL '6 months'
    ORDER BY date_calculated DESC LIMIT 1;
    
    SELECT fundamental_health_score INTO fundamental_1y_ago
    FROM company_scores_historical
    WHERE ticker = p_ticker AND date_calculated = CURRENT_DATE - INTERVAL '1 year'
    ORDER BY date_calculated DESC LIMIT 1;
    
    -- Similar queries for technical and trading scores...
    
    -- Calculate trends
    fundamental_health_trend := CASE
        WHEN current_fundamental > fundamental_3m_ago + 5 THEN 'improving'
        WHEN current_fundamental < fundamental_3m_ago - 5 THEN 'declining'
        ELSE 'stable'
    END;
    
    -- Calculate period changes
    fundamental_health_change_3m := current_fundamental - fundamental_3m_ago;
    fundamental_health_change_6m := current_fundamental - fundamental_6m_ago;
    fundamental_health_change_1y := current_fundamental - fundamental_1y_ago;
    
    -- Similar calculations for technical and trading scores...
    
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
```

### 2. **upsert_company_scores()** - Score Update Function

```sql
CREATE OR REPLACE FUNCTION upsert_company_scores(
    p_ticker VARCHAR(10),
    p_fundamental_health_score DECIMAL(5,2),
    p_fundamental_health_grade VARCHAR(2),
    p_fundamental_health_components JSONB,
    p_fundamental_risk_score DECIMAL(5,2),
    p_fundamental_risk_level VARCHAR(20),
    p_fundamental_risk_components JSONB,
    p_value_investment_score DECIMAL(5,2),
    p_value_rating VARCHAR(20),
    p_value_components JSONB,
    p_technical_health_score DECIMAL(5,2),
    p_technical_health_grade VARCHAR(2),
    p_technical_health_components JSONB,
    p_trading_signal_score DECIMAL(5,2),
    p_trading_signal_rating VARCHAR(20),
    p_trading_signal_components JSONB,
    p_technical_risk_score DECIMAL(5,2),
    p_technical_risk_level VARCHAR(20),
    p_technical_risk_components JSONB,
    p_overall_score DECIMAL(5,2),
    p_overall_grade VARCHAR(2),
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
    
    -- Update current table with trend calculations
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
```

## API Query Optimization Views

### 1. **screener_filters_view** - Optimized for Screener Queries

```sql
CREATE VIEW screener_filters_view AS
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
```

### 2. **dashboard_metrics_view** - Optimized for Dashboard Queries

```sql
CREATE VIEW dashboard_metrics_view AS
SELECT 
    ticker,
    company_name,
    sector,
    current_price,
    
    -- Score Breakdown
    fundamental_health_score,
    technical_health_score,
    trading_signal_score,
    overall_score,
    
    -- Risk Assessment
    fundamental_risk_score,
    technical_risk_score,
    
    -- Value Assessment
    value_investment_score,
    
    -- Trends
    fundamental_health_trend,
    technical_health_trend,
    trading_signal_trend,
    
    -- Period Changes
    fundamental_health_change_3m,
    fundamental_health_change_6m,
    fundamental_health_change_1y,
    technical_health_change_3m,
    technical_health_change_6m,
    technical_health_change_1y,
    
    -- Alerts
    fundamental_red_flags,
    fundamental_yellow_flags,
    technical_red_flags,
    technical_yellow_flags
    
FROM company_scores_current csc
JOIN stocks s ON csc.ticker = s.ticker
WHERE csc.date_calculated = CURRENT_DATE;
```

## Daily Run Integration

### 1. **Score Calculation Workflow**

```python
# Pseudo-code for daily_run integration
def calculate_and_store_scores():
    """
    Main function to calculate and store scores in daily_run
    """
    # 1. Get companies needing score updates
    companies = get_companies_needing_score_updates()
    
    # 2. Calculate scores for each company
    for company in companies:
        try:
            # Calculate fundamental scores
            fundamental_scores = calculate_fundamental_scores(company)
            
            # Calculate technical scores
            technical_scores = calculate_technical_scores(company)
            
            # Calculate composite score
            overall_score = calculate_composite_score(fundamental_scores, technical_scores)
            
            # Store in database using upsert function
            store_company_scores(company.ticker, fundamental_scores, technical_scores, overall_score)
            
        except Exception as e:
            log_score_calculation_error(company.ticker, e)
    
    # 3. Update materialized views
    refresh_materialized_views()
    
    # 4. Log calculation summary
    log_calculation_summary()

def store_company_scores(ticker, fundamental_scores, technical_scores, overall_score):
    """
    Store scores using database function
    """
    query = """
    SELECT upsert_company_scores(
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s
    )
    """
    # Execute with all parameters...
```

### 2. **Database Connection and Error Handling**

```python
def get_database_connection():
    """
    Get database connection with proper error handling
    """
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def execute_with_retry(query, params=None, max_retries=3):
    """
    Execute database query with retry logic
    """
    for attempt in range(max_retries):
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchall() if cursor.description else None
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Database query failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Database query attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
```

## Performance Optimization Recommendations

### 1. **Indexing Strategy**
- **Primary indexes** on frequently queried columns (scores, grades, trends)
- **Composite indexes** for complex screener queries
- **Partial indexes** for active stocks only
- **Covering indexes** to avoid table lookups

### 2. **Partitioning Strategy**
- **Historical data** partitioned by year/month
- **Current data** in separate table for fast access
- **Materialized views** refreshed daily for dashboard performance

### 3. **Query Optimization**
- **Pre-calculated trends** to avoid runtime calculations
- **Materialized views** for complex aggregations
- **Connection pooling** for API performance
- **Query result caching** for frequently accessed data

### 4. **Data Maintenance**
- **Daily cleanup** of old historical data (keep 2 years)
- **Weekly optimization** of indexes and statistics
- **Monthly archiving** of old data to separate storage

## Conclusion

This database schema provides:

1. **Efficient Storage**: Hybrid approach with current and historical tables
2. **Fast Queries**: Optimized indexes and materialized views for screeners and dashboards
3. **Data Integrity**: Proper constraints and validation
4. **Scalability**: Partitioning and archiving strategies
5. **Integration**: Seamless integration with daily_run cron system
6. **API Performance**: Optimized views for API endpoints

The schema supports both fundamental and technical scoring systems while maintaining performance for real-time screener queries and comprehensive historical analysis. 