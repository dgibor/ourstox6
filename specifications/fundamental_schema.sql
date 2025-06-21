- =====================================================
-- FUNDAMENTAL ANALYSIS DATABASE SCHEMA ADDITIONS
-- =====================================================

-- 1. Company Fundamentals - Core financial data
CREATE TABLE company_fundamentals (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL, -- 'annual', 'quarterly'
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    
    -- Revenue & Profitability
    revenue NUMERIC(15,2),
    gross_profit NUMERIC(15,2),
    operating_income NUMERIC(15,2),
    net_income NUMERIC(15,2),
    ebitda NUMERIC(15,2),
    
    -- Per Share Metrics
    eps_diluted NUMERIC(8,4),
    book_value_per_share NUMERIC(8,4),
    
    -- Balance Sheet
    total_assets NUMERIC(15,2),
    total_debt NUMERIC(15,2),
    total_equity NUMERIC(15,2),
    cash_and_equivalents NUMERIC(15,2),
    
    -- Cash Flow
    operating_cash_flow NUMERIC(15,2),
    free_cash_flow NUMERIC(15,2),
    capex NUMERIC(15,2),
    
    -- Share Data
    shares_outstanding BIGINT,
    shares_float BIGINT,
    
    -- Metadata
    data_source VARCHAR(20) NOT NULL, -- 'yahoo', 'finnhub', 'alphavantage'
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker, report_date, period_type),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Index for performance
CREATE INDEX idx_fundamentals_ticker_date ON company_fundamentals(ticker, report_date DESC);
CREATE INDEX idx_fundamentals_period ON company_fundamentals(period_type, fiscal_year, fiscal_quarter);

-- 2. Calculated Financial Ratios
CREATE TABLE financial_ratios (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    calculation_date DATE NOT NULL,
    
    -- Valuation Ratios
    pe_ratio NUMERIC(8,4),
    pb_ratio NUMERIC(8,4),
    ps_ratio NUMERIC(8,4),
    ev_ebitda NUMERIC(8,4),
    peg_ratio NUMERIC(8,4),
    
    -- Profitability Ratios
    roe NUMERIC(8,4), -- Return on Equity
    roa NUMERIC(8,4), -- Return on Assets
    roic NUMERIC(8,4), -- Return on Invested Capital
    gross_margin NUMERIC(8,4),
    operating_margin NUMERIC(8,4),
    net_margin NUMERIC(8,4),
    
    -- Financial Health
    debt_to_equity NUMERIC(8,4),
    current_ratio NUMERIC(8,4),
    quick_ratio NUMERIC(8,4),
    interest_coverage NUMERIC(8,4),
    altman_z_score NUMERIC(8,4),
    
    -- Efficiency Ratios
    asset_turnover NUMERIC(8,4),
    inventory_turnover NUMERIC(8,4),
    receivables_turnover NUMERIC(8,4),
    
    -- Growth Metrics (YoY)
    revenue_growth_yoy NUMERIC(8,4),
    earnings_growth_yoy NUMERIC(8,4),
    fcf_growth_yoy NUMERIC(8,4),
    
    -- Quality Metrics
    fcf_to_net_income NUMERIC(8,4),
    cash_conversion_cycle INTEGER,
    
    -- Market Data
    market_cap NUMERIC(15,2),
    enterprise_value NUMERIC(15,2),
    
    -- Graham Number and Intrinsic Value
    graham_number NUMERIC(8,4),
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker, calculation_date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

CREATE INDEX idx_ratios_ticker_date ON financial_ratios(ticker, calculation_date DESC);

-- 3. Industry Averages and Benchmarks
CREATE TABLE industry_benchmarks (
    id SERIAL PRIMARY KEY,
    industry_code VARCHAR(50) NOT NULL,
    sector_code VARCHAR(50) NOT NULL,
    calculation_date DATE NOT NULL,
    company_count INTEGER NOT NULL,
    
    -- Average Ratios
    avg_pe_ratio NUMERIC(8,4),
    median_pe_ratio NUMERIC(8,4),
    avg_pb_ratio NUMERIC(8,4),
    avg_roe NUMERIC(8,4),
    avg_debt_to_equity NUMERIC(8,4),
    avg_gross_margin NUMERIC(8,4),
    avg_operating_margin NUMERIC(8,4),
    
    -- Percentiles (25th, 75th, 90th)
    pe_ratio_25p NUMERIC(8,4),
    pe_ratio_75p NUMERIC(8,4),
    pe_ratio_90p NUMERIC(8,4),
    
    roe_25p NUMERIC(8,4),
    roe_75p NUMERIC(8,4),
    roe_90p NUMERIC(8,4),
    
    debt_eq_25p NUMERIC(8,4),
    debt_eq_75p NUMERIC(8,4),
    debt_eq_90p NUMERIC(8,4),
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(industry_code, calculation_date)
);

-- 4. Peer Companies Mapping
CREATE TABLE peer_companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    peer_ticker VARCHAR(10) NOT NULL,
    similarity_score NUMERIC(4,3), -- 0-1 score
    criteria_matched TEXT[], -- array of criteria: market_cap, industry, revenue_size
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ticker) REFERENCES stocks(ticker),
    FOREIGN KEY (peer_ticker) REFERENCES stocks(ticker)
);

CREATE INDEX idx_peer_ticker ON peer_companies(ticker);

-- 5. Earnings Calendar and Events
CREATE TABLE earnings_calendar (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    earnings_date DATE NOT NULL,
    confirmed BOOLEAN DEFAULT FALSE,
    time_of_day VARCHAR(10), -- 'AMC', 'BMO', 'DMT'
    
    -- Estimates
    eps_estimate NUMERIC(8,4),
    revenue_estimate NUMERIC(15,2),
    
    -- Priority flags for data updates
    priority_level INTEGER DEFAULT 1, -- 1=low, 2=medium, 3=high
    data_updated BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

CREATE INDEX idx_earnings_date ON earnings_calendar(earnings_date);
CREATE INDEX idx_earnings_priority ON earnings_calendar(priority_level DESC, earnings_date);

-- 6. API Usage Tracking
CREATE TABLE api_usage_tracking (
    id SERIAL PRIMARY KEY,
    api_provider VARCHAR(20) NOT NULL, -- 'yahoo', 'finnhub', 'alphavantage'
    date DATE NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    calls_made INTEGER DEFAULT 0,
    calls_limit INTEGER NOT NULL,
    reset_time TIMESTAMP,
    
    UNIQUE(api_provider, date, endpoint)
);

-- 7. Investor Score Calculations Cache
CREATE TABLE investor_scores (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    calculation_date DATE NOT NULL,
    
    -- Score for each investor type (0-100)
    conservative_score INTEGER,
    garp_score INTEGER,
    deep_value_score INTEGER,
    
    -- Component scores for breakdown
    valuation_score INTEGER,
    quality_score INTEGER,
    financial_health_score INTEGER,
    profitability_score INTEGER,
    growth_score INTEGER,
    management_score INTEGER,
    
    -- Risk warnings
    risk_level VARCHAR(20), -- 'none', 'caution', 'warning', 'high_risk'
    risk_factors TEXT[],
    
    -- Score explanation data
    score_explanation JSONB,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker, calculation_date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

CREATE INDEX idx_scores_ticker_date ON investor_scores(ticker, calculation_date DESC);

-- 8. CSV Configuration Storage
CREATE TABLE csv_configurations (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    content JSONB NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(file_name, version)
);

-- 9. Data Update Log
CREATE TABLE data_update_log (
    id SERIAL PRIMARY KEY,
    update_type VARCHAR(50) NOT NULL, -- 'fundamentals', 'ratios', 'scores', 'industry'
    ticker VARCHAR(10), -- NULL for industry-wide updates
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'partial'
    error_message TEXT,
    records_processed INTEGER,
    execution_time_ms INTEGER,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    
    INDEX(update_type, started_at DESC),
    INDEX(ticker, update_type, started_at DESC)
);

-- 10. Market Context Data
CREATE TABLE market_context (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    
    -- Market conditions
    vix_level NUMERIC(6,2),
    spy_trend VARCHAR(20), -- 'bull', 'bear', 'sideways'
    interest_rate_10y NUMERIC(6,4),
    yield_curve_spread NUMERIC(6,4),
    
    -- Confidence modifiers for scoring
    bull_market_modifier NUMERIC(4,3) DEFAULT 1.0,
    bear_market_modifier NUMERIC(4,3) DEFAULT 1.0,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- UPDATE EXISTING STOCKS TABLE
-- =====================================================

-- Add fundamental-specific fields to existing stocks table
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS 
    industry_classification VARCHAR(100),
    ADD COLUMN IF NOT EXISTS 
    gics_sector VARCHAR(50),
    ADD COLUMN IF NOT EXISTS 
    gics_industry VARCHAR(100),
    ADD COLUMN IF NOT EXISTS 
    market_cap_category VARCHAR(20), -- 'large', 'mid', 'small', 'micro'
    ADD COLUMN IF NOT EXISTS 
    fundamentals_last_update TIMESTAMP,
    ADD COLUMN IF NOT EXISTS 
    next_earnings_date DATE,
    ADD COLUMN IF NOT EXISTS 
    data_priority INTEGER DEFAULT 1; -- 1=low, 5=high priority for updates

-- Add index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_stocks_priority ON stocks(data_priority DESC, fundamentals_last_update ASC NULLS FIRST);
CREATE INDEX IF NOT EXISTS idx_stocks_earnings ON stocks(next_earnings_date) WHERE next_earnings_date IS NOT NULL;

-- =====================================================
-- HELPER VIEWS FOR EFFICIENT QUERIES
-- =====================================================

-- Latest ratios per company
CREATE OR REPLACE VIEW latest_financial_ratios AS
SELECT DISTINCT ON (ticker) 
    ticker, calculation_date, pe_ratio, pb_ratio, roe, debt_to_equity,
    gross_margin, operating_margin, net_margin, altman_z_score,
    revenue_growth_yoy, earnings_growth_yoy, market_cap
FROM financial_ratios
ORDER BY ticker, calculation_date DESC;

-- Companies needing fundamental updates (priority-based)
CREATE OR REPLACE VIEW companies_needing_updates AS
SELECT 
    s.ticker, 
    s.company_name,
    s.data_priority,
    s.fundamentals_last_update,
    s.next_earnings_date,
    CASE 
        WHEN s.next_earnings_date <= CURRENT_DATE + INTERVAL '7 days' THEN 5
        WHEN s.fundamentals_last_update IS NULL THEN 4
        WHEN s.fundamentals_last_update < CURRENT_DATE - INTERVAL '30 days' THEN 3
        WHEN s.fundamentals_last_update < CURRENT_DATE - INTERVAL '90 days' THEN 2
        ELSE 1
    END as calculated_priority
FROM stocks s
ORDER BY calculated_priority DESC, s.data_priority DESC, s.fundamentals_last_update ASC NULLS FIRST;

-- Industry summary for benchmarking
CREATE OR REPLACE VIEW industry_summary AS
SELECT 
    s.industry,
    COUNT(*) as company_count,
    AVG(fr.pe_ratio) as avg_pe,
    AVG(fr.roe) as avg_roe,
    AVG(fr.debt_to_equity) as avg_debt_eq,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fr.pe_ratio) as median_pe,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fr.roe) as median_roe
FROM stocks s
JOIN latest_financial_ratios fr ON s.ticker = fr.ticker
WHERE s.industry IS NOT NULL
GROUP BY s.industry
HAVING COUNT(*) >= 3;  -- At least 3 companies for meaningful average