# Daily Run Sequence Explanation

## Current Daily Run Process

The `daily_run.py` script orchestrates a comprehensive daily update process for the stock analysis system. Here's the current sequence:

### Pre-Execution Checks
1. **Market Schedule Check**: Verifies if the market was open today (skipped in test mode)
2. **Database Connection**: Validates database connectivity before proceeding

### Core Data Update Sequence

#### Phase 1: Price Data Collection (Steps 1-3)
1. **Market Prices**: Fetch major market indices (S&P 500, NASDAQ, etc.)
2. **Sector Prices**: Fetch sector ETF prices 
3. **Stock Prices**: Fetch individual stock prices

#### Phase 2: Historical Data Population (Steps 4-6)
4. **Market History**: Fill historical data for market indices
5. **Sector History**: Fill historical data for sector ETFs
6. **Stock History**: Fill historical data for individual stocks

#### Phase 3: Analysis Calculations (Steps 7-8)
7. **Technical Indicators**: Calculate all 43 technical indicators (RSI, MACD, EMA, etc.)
8. **Fundamental Ratios**: Calculate 27 financial ratios (PE, PB, ROE, etc.)

#### Phase 4: Cleanup (Step 9)
9. **Remove Delisted**: Clean up delisted stocks from database

### Current Error Handling
- **Critical Steps** (1-7): Process stops on failure
- **Non-Critical Steps** (8-9): Process continues with warnings

## ACTUAL IMPLEMENTED SEQUENCE in daily_trading_system.py

The `daily_run/daily_trading_system.py` implements a **Priority-Based Schema** that is more sophisticated:

### PRIORITY 1: Trading Day Processing (Most Important)
**Condition**: Only if it was a trading day
**Actions**:
- Update daily prices for all stocks
- Calculate technical indicators based on updated prices
- Skip to Priority 2 if market was closed

### PRIORITY 2: Earnings-Based Fundamental Updates
**Target**: Companies with earnings announcements that day
**Actions**:
- Check earnings calendar for companies with earnings
- Update fundamental information for earnings announcement companies
- Calculate fundamental ratios based on updated stock prices

### PRIORITY 3: Historical Data Completeness
**Target**: Ensure minimum 100 days of historical data
**Actions**:
- Update historical prices until at least 100 days for every company
- Uses remaining API calls after Priorities 1 and 2

### PRIORITY 4: Missing Fundamental Data Fill
**Target**: Data completeness
**Actions**:
- Scan all companies for missing fundamental data
- Fill fundamental data gaps for companies lacking information
- Calculate fundamental ratios for newly filled data

### Cleanup
- Remove delisted stocks to prevent future API errors

## Key Differences Between Implementations

| Aspect | daily_run.py | daily_trading_system.py |
|--------|-------------|-------------------------|
| **Fundamental Updates** | ❌ Missing | ✅ Priority 2 & 4 |
| **Earnings Integration** | ❌ Missing | ✅ Priority 2 |
| **API Call Management** | ❌ None | ✅ Smart allocation |
| **Historical Data** | ✅ Basic | ✅ 100+ days minimum |
| **Technical Indicators** | ✅ Step 7 | ✅ Priority 1 |
| **Fundamental Ratios** | ✅ Step 8 | ✅ After each fundamental update |

## Proposed Scoring Integration

### Recommended Approach: Use daily_trading_system.py as Base

Since `daily_trading_system.py` already has the correct fundamental data update sequence, we should:

1. **Add PRIORITY 5: Scoring Calculation** after all data is complete
2. **Integrate scoring into the existing priority system**

### New PRIORITY 5: Scoring Calculation
After all fundamental and technical data is updated, the system should:

1. **Calculate Fundamental Scores**:
   - Financial Health Score (0-100)
   - Value Investment Score (0-100) 
   - Risk Assessment Score (0-100)

2. **Calculate Technical Scores**:
   - Technical Health Score (0-100)
   - Trading Signal Score (0-100)
   - Technical Risk Score (0-100)

3. **Calculate Composite Scores**:
   - Overall Investment Score
   - Risk-Adjusted Returns
   - Growth Stock Adjustments

4. **Store Results**:
   - Update `company_scores_current` table
   - Log calculation metadata
   - Store component breakdowns

### Integration Points

**Dependencies**:
- Requires Priority 2 (Earnings Fundamentals) to be completed
- Requires Priority 4 (Missing Fundamentals) to be completed
- Requires Priority 1 (Technical Indicators) to be completed
- Uses existing database schema and scoring tables

**Error Handling**:
- Non-critical priority (continues on failure)
- Logs detailed error information
- Provides fallback scores for failed calculations

**Performance Considerations**:
- Can be run in batch mode for efficiency
- Includes progress tracking for large datasets
- Implements rate limiting for database operations

### Benefits of Integration

1. **Automated Analysis**: Daily scoring updates without manual intervention
2. **Data Consistency**: Scores calculated from fresh daily data
3. **Trend Analysis**: Historical scoring data for pattern recognition
4. **Real-time Insights**: Current scores available for trading decisions
5. **Quality Assurance**: Automated validation of scoring calculations

### Implementation Approach

1. **Use daily_trading_system.py as the base** (not daily_run.py)
2. **Add PRIORITY 5**: Create `_calculate_daily_scores()` method
3. **Integrate scoring modules**: Use existing `calc_fundamental_scores.py` and `calc_technical_scores.py`
4. **Error Handling**: Implement robust error handling and logging
5. **Testing**: Validate with existing scoring system
6. **Monitoring**: Add scoring-specific logging and metrics

This integration will complete the automated daily analysis pipeline, providing comprehensive stock scoring based on the most current market and fundamental data, using the superior priority-based approach already implemented in `daily_trading_system.py`.
