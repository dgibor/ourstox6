# daily_run Folder Summary

- **cron_setup.py**  
  Sets up and manages cron jobs or systemd timers to schedule the daily trading system and health checks.

- **create_earnings_calendar_table.py**  
  Creates and verifies the `earnings_calendar` and related tables for earnings-based updates and reporting.

- **daily_trading_system.py**  
  Main production runner that orchestrates daily price updates, fundamentals, technicals, historical data, and delisted stock removal.

- **system_health_check.py**  
  Monitors the health, data quality, and performance of the daily trading system and its components.

- **batch_price_processor.py**  
  Handles batch price fetching and storage for up to 100 stocks per API call, storing results in `daily_charts`.

- **earnings_based_fundamental_processor.py**  
  Updates company fundamentals only when new earnings are reported, not on a fixed schedule.

- **API_OPTIMIZATION_SUMMARY.md**  
  Documents strategies and results for reducing API call volume and optimizing data fetching.

- **BATCH_PROCESSING_LOGIC.md**  
  Describes the logic and implementation of batch processing for prices and fundamentals.

- **common_imports.py**  
  Centralizes common imports and utility functions for use across all service and processor files.

- **earnings_calendar_service.py**  
  Provides methods to fetch, parse, and store earnings calendar data from multiple APIs.

- **enhanced_service_factory.py**  
  Factory for creating service instances with integrated error handling, monitoring, and health checks.

- **error_handler.py**  
  Centralized error handling, logging, and retry logic for all services and processors.

- **monitoring.py**  
  Provides system and data monitoring, metrics collection, and health summary functions.

- **config.py**  
  Loads and manages environment variables and configuration settings for the system.

- **database.py**  
  Manages database connections, queries, and schema verification for all components.

- **IMPLEMENTATION_STATUS.md**  
  Documents the current implementation status and coverage of all production requirements.

- **service_factory.py**  
  Basic factory for instantiating API service classes.

- **fmp_service.py**  
  Handles all interactions with the FMP (Financial Modeling Prep) API for price and fundamental data.

- **yahoo_finance_service.py**  
  Handles all interactions with the Yahoo Finance API for price and fundamental data.

- **ARCHIVE_SUMMARY.md**  
  Short summary of the recent archive operation and what remains in production.

- **alpha_vantage_service.py**  
  Handles all interactions with the Alpha Vantage API for price and fundamental data.

- **finnhub_service.py**  
  Handles all interactions with the Finnhub API for price and fundamental data.

- **SYSTEM_DOCUMENTATION.md**  
  Comprehensive documentation of the system's architecture, workflows, and design.

- **base_service.py**  
  Provides a base class for all API service implementations.

- **exceptions.py**  
  Defines custom exception classes for error handling across the system.

- **calc_technicals.py**  
  Calculates technical indicators for stocks using recent price data.

- **calc_all_technicals.py**  
  Calculates all technical indicators for all stocks and stores results in the database.

- **remove_delisted.py**  
  Identifies and marks delisted stocks as inactive in the database.

- **indicators/**  
  Directory containing all technical indicator calculation modules (RSI, EMA, MACD, etc.).

- **archive_non_essential_YYYYMMDD_HHMMSS/**  
  Directory containing all archived test, debug, and legacy files for safe keeping. 