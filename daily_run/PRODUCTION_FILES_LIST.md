# Production Files Organization

## 🎯 **ESSENTIAL PRODUCTION FILES (KEEP)**

### **Core System Files**
1. **`daily_trading_system.py`** - Main production entry point
2. **`cron_setup.py`** - Production cron job setup
3. **`system_health_check.py`** - Production health monitoring
4. **`check_market_schedule.py`** - Market schedule checking
5. **`remove_delisted.py`** - Delisted stock removal

### **Core Services**
6. **`yahoo_finance_service.py`** - Yahoo Finance API service
7. **`alpha_vantage_service.py`** - Alpha Vantage API service
8. **`finnhub_service.py`** - Finnhub API service
9. **`fmp_service.py`** - FMP API service
10. **`earnings_calendar_service.py`** - Earnings calendar service

### **Core Processors**
11. **`batch_price_processor.py`** - Batch price processing
12. **`earnings_based_fundamental_processor.py`** - Earnings-based fundamentals
13. **`calc_technicals.py`** - Technical indicators calculation
14. **`calc_all_technicals.py`** - All technical indicators

### **Infrastructure**
15. **`database.py`** - Database management
16. **`error_handler.py`** - Error handling system
17. **`monitoring.py`** - System monitoring
18. **`common_imports.py`** - Common imports
19. **`config.py`** - Configuration management
20. **`base_service.py`** - Base service class
21. **`exceptions.py`** - Custom exceptions

### **Service Factory**
22. **`enhanced_service_factory.py`** - Enhanced service factory
23. **`service_factory.py`** - Basic service factory

### **Technical Indicators**
24. **`indicators/`** - Entire directory with all technical indicators
    - `rsi.py`, `ema.py`, `macd.py`, `atr.py`, `vwap.py`, etc.

### **Documentation**
25. **`IMPLEMENTATION_STATUS.md`** - Implementation status
26. **`SYSTEM_DOCUMENTATION.md`** - System documentation
27. **`BATCH_PROCESSING_LOGIC.md`** - Batch processing documentation
28. **`API_OPTIMIZATION_SUMMARY.md`** - API optimization documentation

### **Database Schema**
29. **`create_earnings_calendar_table.py`** - Database schema creation

---

## 🗂️ **FILES TO ARCHIVE (TESTING/DEVELOPMENT)**

### **Test Files**
```
test_*.py files:
- test_stability_improvements.py
- test_fundamentals_updater.py
- test_alpha_vantage_delayed.py
- test_fmp.py
- test_alpha_vantage.py
- test_fallback.py
- test_services.py
- test_integration.py
- quick_test.py
- quick_stability_test.py
```

### **Debug Files**
```
debug_*.py files:
- debug_monitoring.py
- debug_shares_outstanding.py
- debug_raw_data.py
- debug_data_extraction.py
- debug_storage_issue.py
- debug_fundamental_storage.py
```

### **Check/Validation Files**
```
check_*.py files:
- check_fundamentals_structure.py
- check_table_structure.py
- check_price_columns.py
- check_missing_data.py
- check_all_fundamental_columns.py
- check_stocks_schema.py
- check_fmp_storage.py
- check_actual_fundamental_data.py
- check_stocks_fundamentals.py
- check_fundamentals_schema.py
- check_database_updates.py
```

### **Fix/Update Scripts**
```
fix_*.py files:
- fix_with_calculations_fixed.py
- fix_with_calculations.py
- fix_missing_data_simple.py
- fix_missing_data.py
- fix_schema.py
- update_all_fundamentals_complete.py
- update_fundamentals_fixed.py
- update_fundamentals_for_tickers.py
```

### **Query/Utility Scripts**
```
query_*.py files:
- query_fundamentals_for_tickers.py
```

### **Legacy/Conflicting Files**
```
- integrated_daily_runner_v2.py (superseded by v3)
- integrated_daily_runner_v3.py (superseded by daily_trading_system.py)
- main_daily_runner.py (legacy)
- price_service.py (superseded by batch_price_processor.py)
- fundamental_service.py (superseded by earnings_based_fundamental_processor.py)
- ratios_calculator.py (integrated into main system)
- daily_fundamentals_updater.py (superseded by earnings_based_fundamental_processor.py)
- batch_processor.py (superseded by batch_price_processor.py)
```

### **Summary/Status Files**
```
- final_summary.py
- system_status_summary_fixed.py
- system_status_summary.py
- final_test_complete_system.py
```

### **Documentation Files**
```
- CLEANUP_PLAN.md
- DESIGN_DOCUMENT.md
- trading_indicators_spec.md
- Technical Indicators Calculator - LLM Implementation Instructions.pdf
- Stock Data Collection System - LLM Development Guide.pdf
```

### **Migration Files**
```
- migrate_add_technicals_columns.py
```

---

## 📋 **ARCHIVE COMMANDS**

### **Manual Archive Commands**
```bash
# Create archive directory
mkdir archive_non_essential_$(date +%Y%m%d_%H%M%S)

# Archive test files
mv test_*.py quick_test.py quick_stability_test.py archive_non_essential_*/

# Archive debug files
mv debug_*.py archive_non_essential_*/

# Archive check files
mv check_*.py archive_non_essential_*/

# Archive fix files
mv fix_*.py archive_non_essential_*/

# Archive update files
mv update_*.py archive_non_essential_*/

# Archive query files
mv query_*.py archive_non_essential_*/

# Archive legacy files
mv integrated_daily_runner_v2.py integrated_daily_runner_v3.py main_daily_runner.py price_service.py fundamental_service.py ratios_calculator.py daily_fundamentals_updater.py batch_processor.py archive_non_essential_*/

# Archive summary files
mv final_summary.py system_status_summary_fixed.py system_status_summary.py final_test_complete_system.py archive_non_essential_*/

# Archive documentation files
mv CLEANUP_PLAN.md DESIGN_DOCUMENT.md trading_indicators_spec.md "Technical Indicators Calculator - LLM Implementation Instructions.pdf" "Stock Data Collection System - LLM Development Guide.pdf" archive_non_essential_*/

# Archive migration files
mv migrate_add_technicals_columns.py archive_non_essential_*/
```

### **Using the Archive Script**
```bash
# Run the archive script
python archive_non_essential_files.py
```

---

## 🚀 **PRODUCTION DEPLOYMENT CHECKLIST**

After archiving, verify these essential files remain:

### **Core System**
- [ ] `daily_trading_system.py` - Main entry point
- [ ] `cron_setup.py` - Cron setup
- [ ] `system_health_check.py` - Health monitoring
- [ ] `check_market_schedule.py` - Market schedule
- [ ] `remove_delisted.py` - Delisted removal

### **Services**
- [ ] `yahoo_finance_service.py`
- [ ] `alpha_vantage_service.py`
- [ ] `finnhub_service.py`
- [ ] `fmp_service.py`
- [ ] `earnings_calendar_service.py`

### **Processors**
- [ ] `batch_price_processor.py`
- [ ] `earnings_based_fundamental_processor.py`
- [ ] `calc_technicals.py`
- [ ] `calc_all_technicals.py`

### **Infrastructure**
- [ ] `database.py`
- [ ] `error_handler.py`
- [ ] `monitoring.py`
- [ ] `common_imports.py`
- [ ] `config.py`
- [ ] `base_service.py`
- [ ] `exceptions.py`

### **Technical Indicators**
- [ ] `indicators/` directory with all indicator files

### **Documentation**
- [ ] `IMPLEMENTATION_STATUS.md`
- [ ] `SYSTEM_DOCUMENTATION.md`
- [ ] `BATCH_PROCESSING_LOGIC.md`
- [ ] `API_OPTIMIZATION_SUMMARY.md`

---

## 📊 **FILE COUNT SUMMARY**

### **Production Files: ~29 files**
### **Files to Archive: ~50+ files**
### **Archive Reduction: ~65% file reduction**

This organization will significantly declutter the production directory while maintaining all essential functionality. 