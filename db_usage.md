# Database Table Usage Analysis for daily_run Functions

## Overview
This document analyzes which database tables are used by the `daily_run` functions and which are never called, based on a comprehensive codebase search.

## All Tables in the Database (from `db_schema.md`)
- chart_metadata
- company_analysis
- daily_charts
- db_version
- economic_indicators
- macro_analysis
- macro_scores
- market_data
- market_regimes
- news_sentiment
- portfolio
- roles
- roles_users
- sectors
- stocks
- tickers
- top_stocks
- users

---

## Tables **Used** by `daily_run` Functions

Based on direct references (queries, inserts, updates) in the `daily_run/` directory and its subfolders, the following tables are **used**:

- **daily_charts** (heavily used for price and technical data)
- **sectors** (used for sector-level data and technicals)
- **market_data** (used for market-wide data and technicals)
- **stocks** (used for company/stock-level data)
- **top_stocks** (referenced in update scripts)
- **portfolio** (referenced in update scripts)

---

## Tables **Not Used** by `daily_run` Functions

The following tables are **not referenced** in the `daily_run/` directory (no direct evidence of queries, inserts, or updates):

- chart_metadata
- company_analysis
- db_version
- economic_indicators
- macro_analysis
- macro_scores
- market_regimes
- news_sentiment
- roles
- roles_users
- tickers
- users

---

## Detailed File-by-File Breakdown

### **1. daily_charts**
Referenced in:
- `daily_run/daily_trading_system.py`
- `daily_run/database.py`
- `daily_run/batch_price_processor.py`
- `daily_run/calc_all_technicals.py`
- `daily_run/system_health_check.py`
- `daily_run/remove_delisted.py`
- `daily_run/archive_20250622_215640/get_prices.py`
- `daily_run/archive_20250622_215640/fmp_price_service.py`
- `daily_run/archive_20250622_215640/fill_history.py`
- `daily_run/archive_20250622_215640/financial_ratios_calculator.py`
- `daily_run/archive_20250622_215640/calculate_daily_ratios.py`
- `daily_run/create_earnings_calendar_table.py`
- `daily_run/archive_non_essential_20250624_010014/check_database_updates.py`
- `daily_run/archive_non_essential_20250624_010014/final_summary.py`
- **Many utility scripts**: `check_and_update_schema.py`, `check_daily_charts_schema.py`, `check_adx_coverage.py`, `check_adx_values.py`, `batch_adx_fix.py`, `add_unique_constraint_daily_charts.py`, `add_bigint_to_daily_charts.py`, `add_adx_column.py`, `test_prices_insert.py`, `run_financial_ratios_for_professor.py`, `generate_professor_csv.py`, `update_market_cap.py`, `update_column_types.py`, etc.

### **2. sectors**
Referenced in:
- `daily_run/calc_all_technicals.py`
- `daily_run/archive_20250622_215640/get_sector_prices.py`
- `daily_run/archive_20250622_215640/fill_history_sector.py`
- **Utility scripts**: `check_and_update_schema.py`, `check_sectors_schema.py`, `update_column_types.py`, `adjust_market_tables.py`, etc.

### **3. market_data**
Referenced in:
- `daily_run/calc_all_technicals.py`
- `daily_run/calc_technicals.py`
- `daily_run/alpha_vantage_service.py`
- `daily_run/yahoo_finance_service.py`
- `daily_run/fmp_service.py`
- `daily_run/finnhub_service.py`
- **Utility scripts**: `check_and_update_schema.py`, `adjust_market_tables.py`, etc.

### **4. stocks**
Referenced in:
- `daily_run/system_health_check.py`
- `update_stocks_final_list.py`
- `test_financial_ratios_complete.py`
- `test_price_fix.py`
- **Utility scripts**: `update_stocks_schema.py`, `update_stocks_from_csv.py`, `check_stocks_table.py`, `test_db.py`, etc.

### **5. top_stocks**
Referenced in:
- `update_stocks_final_list.py`

### **6. portfolio**
Referenced in:
- `update_stocks_final_list.py`

---

## Summary Table

| Table Name           | Used by daily_run? | Primary Usage |
|----------------------|-------------------|---------------|
| chart_metadata       | ❌                | Not used      |
| company_analysis     | ❌                | Not used      |
| daily_charts         | ✅                | Price data, technical indicators |
| db_version           | ❌                | Not used      |
| economic_indicators  | ❌                | Not used      |
| macro_analysis       | ❌                | Not used      |
| macro_scores         | ❌                | Not used      |
| market_data          | ✅                | Market-wide data, technicals |
| market_regimes       | ❌                | Not used      |
| news_sentiment       | ❌                | Not used      |
| portfolio            | ✅                | User portfolios |
| roles                | ❌                | Not used      |
| roles_users          | ❌                | Not used      |
| sectors              | ✅                | Sector-level data, technicals |
| stocks               | ✅                | Company/stock data |
| tickers              | ❌                | Not used      |
| top_stocks           | ✅                | Top stock lists |
| users                | ❌                | Not used      |

---

## File-by-File Mapping Summary

| Table Name    | Example Files Referencing Table (not exhaustive) |
|---------------|--------------------------------------------------|
| daily_charts  | daily_trading_system.py, database.py, batch_price_processor.py, calc_all_technicals.py, system_health_check.py, remove_delisted.py, ... |
| sectors       | calc_all_technicals.py, get_sector_prices.py, fill_history_sector.py, check_and_update_schema.py, check_sectors_schema.py, ... |
| market_data   | calc_all_technicals.py, calc_technicals.py, alpha_vantage_service.py, yahoo_finance_service.py, fmp_service.py, finnhub_service.py, ... |
| stocks        | system_health_check.py, update_stocks_final_list.py, test_financial_ratios_complete.py, test_price_fix.py, update_stocks_schema.py, ... |
| top_stocks    | update_stocks_final_list.py                      |
| portfolio     | update_stocks_final_list.py                      |

---

## Notes

- Some tables (like `users`, `roles`, `roles_users`, `tickers`) may be used in authentication, dashboard, or API layers, but **not in the daily_run pipeline**.
- If you want to check for indirect usage (e.g., via views, triggers, or external scripts), a deeper analysis would be needed.
- The `daily_charts` table is the most heavily used table in the daily_run pipeline, serving as the primary storage for price data and technical indicators.
- The `stocks` table is primarily used for company metadata and is referenced in various utility scripts and health checks.
- The `sectors` and `market_data` tables are used for sector-level and market-wide data processing respectively. 