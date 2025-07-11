# Stock Score Calculator

A comprehensive scoring system for stock analysis that calculates technical, fundamental, and analyst scores using existing data from the daily run system.

## Overview

The Score Calculator is designed to run after all other daily run functions have completed. It processes stocks prioritized by earnings proximity and maintains 100 days of historical scores with data quality tracking.

## Architecture

### Core Components

1. **Technical Scorer** (`technical_scorer.py`)
   - Uses existing indicators from `daily_charts` table
   - Applies logic from `card_logic.csv` and `trader_scoring.csv`
   - Calculates signal strengths (1-5) for different technical patterns
   - Generates composite scores for Swing Trader, Momentum Trader, and Long-term Investor

2. **Fundamental Scorer** (`fundamental_scorer.py`)
   - Uses existing ratios from `financial_ratios` table
   - Implements FUND-DASH scoring methodology
   - Calculates scores for Valuation, Quality, Growth, Financial Health, Management, Moat, and Risk
   - Generates composite scores for Conservative, GARP, and Deep Value investors

3. **Analyst Scorer** (`analyst_scorer.py`)
   - Uses earnings calendar data and analyst recommendations
   - Calculates scores based on earnings proximity, surprises, sentiment, price targets, and revisions
   - Provides composite analyst sentiment score

4. **Score Orchestrator** (`score_orchestrator.py`)
   - Coordinates all three scorers
   - Manages prioritization by earnings proximity
   - Handles parallel processing with time limits
   - Provides batch processing and cleanup functionality

5. **Database Manager** (`database_manager.py`)
   - Handles all database operations for score tables
   - Implements upsert logic for score updates
   - Manages data quality tracking

6. **Schema Manager** (`schema_manager.py`)
   - Creates and maintains database schema
   - Handles table creation and migrations

## Database Schema

### Main Tables

#### `daily_scores`
Primary table storing all calculated scores for each ticker and date.

```sql
CREATE TABLE daily_scores (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    calculation_date DATE NOT NULL,
    
    -- Technical Scores
    price_position_trend_score INTEGER,
    momentum_cluster_score INTEGER,
    volume_confirmation_score INTEGER,
    trend_direction_score INTEGER,
    volatility_risk_score INTEGER,
    swing_trader_score INTEGER,
    momentum_trader_score INTEGER,
    long_term_investor_score INTEGER,
    volume_ratio DECIMAL(10,4),
    
    -- Fundamental Scores
    valuation_score INTEGER,
    quality_score INTEGER,
    growth_score INTEGER,
    financial_health_score INTEGER,
    management_score INTEGER,
    moat_score INTEGER,
    risk_score INTEGER,
    conservative_investor_score INTEGER,
    garp_investor_score INTEGER,
    deep_value_investor_score INTEGER,
    sector VARCHAR(100),
    industry VARCHAR(100),
    
    -- Analyst Scores
    earnings_proximity_score INTEGER,
    earnings_surprise_score INTEGER,
    analyst_sentiment_score INTEGER,
    price_target_score INTEGER,
    revision_score INTEGER,
    composite_analyst_score INTEGER,
    
    -- Metadata
    technical_data_quality_score INTEGER,
    fundamental_data_quality_score INTEGER,
    analyst_data_quality_score INTEGER,
    technical_calculation_status VARCHAR(20),
    fundamental_calculation_status VARCHAR(20),
    analyst_calculation_status VARCHAR(20),
    technical_error_message TEXT,
    fundamental_error_message TEXT,
    analyst_error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker, calculation_date)
);
```

## Usage

### Command Line Interface

```bash
# Setup database schema
python -m daily_run.score_calculator.main --setup

# Run daily scoring (default)
python -m daily_run.score_calculator.main

# Run with custom parameters
python -m daily_run.score_calculator.main --max-tickers 500 --max-time 2

# Force recalculation of existing scores
python -m daily_run.score_calculator.main --force

# Process single ticker
python -m daily_run.score_calculator.main --ticker AAPL

# Get system status
python -m daily_run.score_calculator.main --status
```

### Programmatic Usage

```python
from daily_run.score_calculator import ScoreOrchestrator

# Initialize orchestrator
orchestrator = ScoreOrchestrator()

# Run daily scoring
result = orchestrator.run_daily_scoring(
    max_tickers=1000,
    max_time_hours=3,
    force_recalculate=False
)

# Process single ticker
result = orchestrator.process_single_ticker('AAPL', date.today())

# Get system status
status = orchestrator.get_scoring_status()
```

### Integration with Daily Run Pipeline

Add to your daily run script:

```python
from daily_run.score_calculator import ScoreOrchestrator

def run_daily_scoring():
    """Run scoring after all other daily functions complete"""
    try:
        orchestrator = ScoreOrchestrator()
        result = orchestrator.run_daily_scoring(
            max_tickers=1000,
            max_time_hours=3
        )
        
        if result['success']:
            logger.info("Daily scoring completed successfully")
        else:
            logger.error(f"Daily scoring failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in daily scoring: {e}")

# Add to your daily run sequence
run_daily_scoring()
```

## Configuration

### Performance Settings

- **Max Workers**: Number of parallel threads (default: 4)
- **Max Tickers**: Maximum tickers to process per run (default: 1000)
- **Max Time**: Maximum execution time in hours (default: 3)
- **Days to Keep**: Historical score retention (default: 100)

### Data Quality Thresholds

- **Success**: Data quality score ≥ 80%
- **Partial**: Data quality score 50-79%
- **Failed**: Data quality score < 50%

## Data Sources

### Technical Scoring
- **Source**: `daily_charts` table
- **Indicators**: RSI, Stochastic, CCI, MACD, EMAs, ATR, ADX, Bollinger Bands, VWAP, Support/Resistance
- **Logic**: `logic_tables/card_logic.csv`, `logic_tables/trader_scoring.csv`

### Fundamental Scoring
- **Source**: `financial_ratios` table
- **Ratios**: P/E, P/B, P/S, EV/EBITDA, ROE, ROA, ROIC, Margins, Debt ratios, Growth metrics
- **Methodology**: FUND-DASH scoring system

### Analyst Scoring
- **Source**: `earnings_calendar` table, analyst recommendations
- **Factors**: Earnings proximity, surprises, sentiment, price targets, revisions

## Output and Monitoring

### Log Files
- **Location**: `logs/score_calculator.log`
- **Level**: INFO with detailed progress tracking

### Database Queries

Get latest scores for a ticker:
```sql
SELECT * FROM daily_scores 
WHERE ticker = 'AAPL' 
ORDER BY calculation_date DESC 
LIMIT 1;
```

Get top scoring stocks:
```sql
SELECT ticker, conservative_investor_score, garp_investor_score, deep_value_investor_score
FROM daily_scores 
WHERE calculation_date = CURRENT_DATE
ORDER BY conservative_investor_score DESC 
LIMIT 10;
```

### Performance Monitoring

```python
# Get scoring statistics
status = orchestrator.get_scoring_status()
print(f"Success rates: {status['daily_stats']}")
```

## Error Handling

The system includes comprehensive error handling:

- **Data Quality Tracking**: Each score includes a data quality score
- **Calculation Status**: Success/partial/failed status for each score type
- **Error Messages**: Detailed error messages for debugging
- **Graceful Degradation**: Continues processing even if individual tickers fail

## Maintenance

### Cleanup
```python
# Clean up old scores (older than 100 days)
orchestrator.cleanup_old_scores(days_to_keep=100)
```

### Schema Updates
```python
# Update schema if needed
schema_manager = ScoreSchemaManager(db)
schema_manager.create_tables()
```

## Dependencies

- `pandas`: Data manipulation and CSV reading
- `concurrent.futures`: Parallel processing
- `logging`: Comprehensive logging
- `argparse`: Command line interface

## File Structure

```
daily_run/score_calculator/
├── __init__.py              # Package initialization
├── main.py                  # Command line interface
├── score_orchestrator.py    # Main orchestrator
├── technical_scorer.py      # Technical analysis scoring
├── fundamental_scorer.py    # Fundamental analysis scoring
├── analyst_scorer.py        # Analyst sentiment scoring
├── database_manager.py      # Database operations
├── schema_manager.py        # Schema management
├── README.md               # This file
└── SCHEMA_OPTIMIZATION.md  # Schema optimization details
```

## Troubleshooting

### Common Issues

1. **Missing Data**: Check if required tables exist and have data
2. **Performance**: Adjust max_workers and max_tickers parameters
3. **Timeouts**: Increase max_time_hours parameter
4. **Database Errors**: Check database connectivity and permissions

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('daily_run.score_calculator').setLevel(logging.DEBUG)
```

## Future Enhancements

- Real-time scoring updates
- Machine learning model integration
- Additional scoring methodologies
- Web dashboard integration
- API endpoints for score retrieval 