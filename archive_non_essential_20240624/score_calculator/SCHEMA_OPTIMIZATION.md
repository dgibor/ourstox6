# Score Calculator Schema Optimization

## Overview
This document outlines the optimization of the score calculator database schema to eliminate redundancy with existing tables.

## Redundancy Analysis

### 1. Fundamental Scores vs Financial Ratios Table

**REMOVED REDUNDANT FIELDS:**
- `pe_ratio` - Available in `financial_ratios` table
- `pb_ratio` - Available in `financial_ratios` table  
- `ev_ebitda` - Available in `financial_ratios` table
- `roe` - Available in `financial_ratios` table
- `roic` - Available in `financial_ratios` table
- `debt_to_equity` - Available in `financial_ratios` table
- `current_ratio` - Available in `financial_ratios` table
- `altman_z_score` - Available in `financial_ratios` table
- `revenue_growth_yoy` - Available in `financial_ratios` table
- `earnings_growth_yoy` - Available in `financial_ratios` table
- `fcf_growth_yoy` - Available in `financial_ratios` table

**RETAINED UNIQUE FIELDS:**
- Category scores (0-100): `valuation_score`, `financial_health_score`, `quality_score`, `profitability_score`, `growth_score`, `management_score`
- Investor type scores: `conservative_investor_score`, `garp_investor_score`, `deep_value_investor_score`
- Metadata: `data_quality_score`, `calculation_status`, `error_message`

### 2. Technical Scores vs Daily Charts Table

**REMOVED REDUNDANT FIELDS:**
- `rsi_14` - Available in `daily_charts` table
- `stoch_k` - Available in `daily_charts` table
- `cci_20` - Available in `daily_charts` table
- `macd_line` - Available in `daily_charts` table
- `ema_20` - Available in `daily_charts` table
- `ema_50` - Available in `daily_charts` table
- `ema_200` - Available in `daily_charts` table
- `atr_14` - Available in `daily_charts` table
- `adx_14` - Available in `daily_charts` table

**RETAINED UNIQUE FIELDS:**
- Signal strengths (1-5): `price_position_trend_score`, `momentum_cluster_score`, `volume_confirmation_score`, `trend_direction_score`, `volatility_risk_score`
- Composite scores: `swing_trader_score`, `momentum_trader_score`, `long_term_investor_score`
- Derived metrics: `volume_ratio` (calculated from daily_charts data)
- Metadata: `data_quality_score`, `calculation_status`, `error_message`

## Data Access Strategy

### For Fundamental Scores:
```sql
-- Join with financial_ratios to get raw ratios
SELECT 
    fs.*,
    fr.pe_ratio, fr.pb_ratio, fr.roe, fr.debt_to_equity
FROM fundamental_scores fs
JOIN financial_ratios fr ON fs.ticker = fr.ticker 
    AND fs.calculation_date = fr.calculation_date
WHERE fs.ticker = 'AAPL'
```

### For Technical Scores:
```sql
-- Join with daily_charts to get raw indicators
SELECT 
    ts.*,
    dc.rsi_14, dc.stoch_k, dc.cci_20, dc.macd_line, dc.ema_20, dc.ema_50, dc.ema_200
FROM technical_scores ts
JOIN daily_charts dc ON ts.ticker = dc.ticker 
    AND ts.calculation_date = dc.date
WHERE ts.ticker = 'AAPL'
```

## Benefits of Optimization

1. **Reduced Storage**: Eliminated ~20 redundant columns across score tables
2. **Data Consistency**: Single source of truth for raw ratios and indicators
3. **Maintenance**: Updates to raw data automatically reflected in scores
4. **Performance**: Smaller tables with focused indexes
5. **Clarity**: Clear separation between raw data and calculated scores

## Implementation Notes

- Score calculators will read raw data from existing tables
- Scores are calculated and stored without duplicating source data
- Database joins provide complete data when needed
- Historical data retention (100 days) applies only to calculated scores
- Raw data retention follows existing table policies 