# Archived Files

This directory contains old files that were archived after implementing the new modular architecture.

## Archive Date: 2025-06-22 21:56:40

## Files Archived (16 files):

### Price Collection Files (Replaced by price_service.py):
- get_prices.py - Old individual price collection script
- get_market_prices.py - Old market price collection script  
- get_sector_prices.py - Old sector price collection script
- fmp_price_service.py - Old FMP price service

### Fundamental Files (Replaced by fundamental_service.py):
- multi_service_fundamentals.py - Old multi-service fundamentals script
- update_fundamentals_daily.py - Old daily fundamentals update script
- update_fundamentals_scheduler.py - Old fundamentals scheduler

### Pipeline Files (Replaced by new_daily_pipeline.py):
- daily_financial_pipeline.py - Old monolithic pipeline
- calculate_daily_ratios.py - Old ratio calculation script

### Service Files (Consolidated into price_service.py):
- alpha_vantage_service.py - Old Alpha Vantage service
- finnhub_service.py - Old Finnhub service

### Calculator Files (Replaced by ratios_calculator.py):
- financial_ratios_calculator.py - Old financial ratios calculator
- simple_ratios_calculator.py - Old simple ratios calculator

### History Fill Files (One-time use):
- fill_history.py - One-time history fill script
- fill_history_market.py - One-time market history fill script
- fill_history_sector.py - One-time sector history fill script

## New Modular System Files:

The following files now handle all the functionality:

### Core Services:
- price_service.py - Consolidated price collection service
- fundamental_service.py - Consolidated fundamental data service
- ratios_calculator.py - Consolidated ratios calculator

### Pipeline & Runner:
- new_daily_pipeline.py - New modular pipeline
- production_daily_runner.py - Production daily runner
- service_factory.py - Service factory for dependency injection

### Infrastructure:
- base_service.py - Base service class
- database.py - Database manager
- config.py - Configuration management
- exceptions.py - Custom exceptions

### Testing:
- test_integration.py - Integration tests

## Benefits of New Architecture:

1. **No Code Duplication** - Single source of truth for each functionality
2. **Modular Design** - Clear separation of concerns
3. **Better Testing** - Easier to test individual components
4. **Improved Maintainability** - Consistent patterns and architecture
5. **Reduced Complexity** - From 37+ files to ~21 files

## Recovery Instructions:

If you need to restore any of these files:

```bash
# Restore a specific file
cp archive_20250622_215640/filename.py ./

# Restore all files
cp archive_20250622_215640/* ./
```

## Notes:

- These files are kept for reference and potential recovery
- The new modular system provides all the same functionality
- All new files have been tested and verified to work correctly
