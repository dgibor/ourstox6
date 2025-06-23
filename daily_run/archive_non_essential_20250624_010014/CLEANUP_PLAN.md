# Archive Plan - Files to Move to Archive

## 📦 **OLD FILES TO ARCHIVE**

### **1. Duplicate Price Collection Files**
These are replaced by our new `price_service.py`:

- **`get_prices.py`** (23KB, 520 lines) 📦 **ARCHIVE**
  - Old individual price collection script
  - Functionality now in `PriceCollector` class

- **`get_market_prices.py`** (12KB, 313 lines) 📦 **ARCHIVE**
  - Old market price collection script
  - Functionality now in `PriceCollector.get_market_prices()`

- **`get_sector_prices.py`** (20KB, 450 lines) 📦 **ARCHIVE**
  - Old sector price collection script
  - Functionality now in `PriceCollector.get_sector_prices()`

- **`fmp_price_service.py`** (8.4KB, 224 lines) 📦 **ARCHIVE**
  - Old FMP price service
  - Functionality now in `price_service.py` as `FMPPriceService`

### **2. Duplicate Fundamental Files**
These are replaced by our new `fundamental_service.py`:

- **`multi_service_fundamentals.py`** (6.6KB, 174 lines) 📦 **ARCHIVE**
  - Old multi-service fundamentals script
  - Functionality now in `FundamentalService` class

- **`update_fundamentals_daily.py`** (12KB, 292 lines) 📦 **ARCHIVE**
  - Old daily fundamentals update script
  - Functionality now in `FundamentalService.daily_gradual_update()`

- **`update_fundamentals_scheduler.py`** (7.8KB, 182 lines) 📦 **ARCHIVE**
  - Old fundamentals scheduler
  - Functionality now in `production_daily_runner.py`

### **3. Duplicate Pipeline Files**
These are replaced by our new modular pipeline:

- **`daily_financial_pipeline.py`** (14KB, 372 lines) 📦 **ARCHIVE**
  - Old monolithic pipeline
  - Functionality now in `new_daily_pipeline.py` and `production_daily_runner.py`

- **`calculate_daily_ratios.py`** (17KB, 411 lines) 📦 **ARCHIVE**
  - Old ratio calculation script
  - Functionality now in `ratios_calculator.py`

### **4. Duplicate Service Files**
These are now consolidated:

- **`alpha_vantage_service.py`** (14KB, 341 lines) 📦 **ARCHIVE**
  - Old Alpha Vantage service
  - Functionality now in `price_service.py` as `AlphaVantagePriceService`

- **`finnhub_service.py`** (14KB, 353 lines) 📦 **ARCHIVE**
  - Old Finnhub service
  - Functionality now in `price_service.py` as `FinnhubPriceService`

### **5. Duplicate Calculator Files**
These are consolidated:

- **`financial_ratios_calculator.py`** (12KB, 298 lines) 📦 **ARCHIVE**
  - Old financial ratios calculator
  - Functionality now in `ratios_calculator.py`

- **`simple_ratios_calculator.py`** (5.7KB, 144 lines) 📦 **ARCHIVE**
  - Old simple ratios calculator
  - Functionality now in `ratios_calculator.py`

### **6. History Fill Files (One-time Use)**
These were for initial data population:

- **`fill_history.py`** (14KB, 372 lines) 📦 **ARCHIVE**
  - One-time history fill script
  - No longer needed for daily operations

- **`fill_history_market.py`** (26KB, 670 lines) 📦 **ARCHIVE**
  - One-time market history fill script
  - No longer needed for daily operations

- **`fill_history_sector.py`** (15KB, 398 lines) 📦 **ARCHIVE**
  - One-time sector history fill script
  - No longer needed for daily operations

### **7. Technical Indicators (Keep - Still Used)**
These are still needed for technical analysis:

- **`calc_technicals.py`** (13KB, 344 lines) ✅ **KEEP**
  - Still used for technical indicators

- **`calc_all_technicals.py`** (2.8KB, 86 lines) ✅ **KEEP**
  - Still used for batch technical calculations

- **`indicators/` directory** ✅ **KEEP**
  - All technical indicator modules still needed

### **8. Utility Files (Keep - Still Used)**
These are still needed:

- **`check_market_schedule.py`** (7.9KB, 216 lines) ✅ **KEEP**
  - Still used for market schedule checking

- **`remove_delisted.py`** (7.9KB, 213 lines) ✅ **KEEP**
  - Still used for cleaning delisted stocks

- **`earnings_calendar_service.py`** (25KB, 583 lines) ✅ **KEEP**
  - Still used for earnings calendar functionality

- **`fix_schema.py`** (4.2KB, 98 lines) ✅ **KEEP**
  - Still used for database schema fixes

- **`migrate_add_technicals_columns.py`** (1.2KB, 45 lines) ✅ **KEEP**
  - Still used for database migrations

## 📊 **Archive Summary**

### **Files to Archive: 16 files (~200KB)**
1. `get_prices.py` (23KB)
2. `get_market_prices.py` (12KB)
3. `get_sector_prices.py` (20KB)
4. `fmp_price_service.py` (8.4KB)
5. `multi_service_fundamentals.py` (6.6KB)
6. `update_fundamentals_daily.py` (12KB)
7. `update_fundamentals_scheduler.py` (7.8KB)
8. `daily_financial_pipeline.py` (14KB)
9. `calculate_daily_ratios.py` (17KB)
10. `alpha_vantage_service.py` (14KB)
11. `finnhub_service.py` (14KB)
12. `financial_ratios_calculator.py` (12KB)
13. `simple_ratios_calculator.py` (5.7KB)
14. `fill_history.py` (14KB)
15. `fill_history_market.py` (26KB)
16. `fill_history_sector.py` (15KB)

### **Files to Keep: 21 files (~150KB)**
1. `price_service.py` ✅ (New consolidated service)
2. `fundamental_service.py` ✅ (New consolidated service)
3. `ratios_calculator.py` ✅ (New consolidated calculator)
4. `new_daily_pipeline.py` ✅ (New modular pipeline)
5. `production_daily_runner.py` ✅ (New production runner)
6. `service_factory.py` ✅ (New service factory)
7. `base_service.py` ✅ (New base service)
8. `database.py` ✅ (New database manager)
9. `config.py` ✅ (New configuration)
10. `exceptions.py` ✅ (New exceptions)
11. `test_integration.py` ✅ (New integration tests)
12. `calc_technicals.py` ✅ (Still needed)
13. `calc_all_technicals.py` ✅ (Still needed)
14. `check_market_schedule.py` ✅ (Still needed)
15. `remove_delisted.py` ✅ (Still needed)
16. `earnings_calendar_service.py` ✅ (Still needed)
17. `fix_schema.py` ✅ (Still needed)
18. `migrate_add_technicals_columns.py` ✅ (Still needed)
19. `indicators/` directory ✅ (Still needed)
20. `yahoo_finance_service.py` ✅ (Still needed)
21. `fmp_service.py` ✅ (Still needed)

## 🚀 **Benefits of Archiving**

### **Before Archiving:**
- **37+ files** with overlapping functionality
- **Code duplication** across multiple services
- **Inconsistent patterns** and architectures
- **Difficult maintenance** and debugging

### **After Archiving:**
- **~21 files** with clear responsibilities
- **No code duplication** - single source of truth
- **Consistent modular architecture**
- **Easy maintenance** and testing
- **Files preserved** for reference and recovery

## ⚠️ **Archive Instructions**

### **Phase 1: Run Archive Script**
```bash
# Run the archive script
python cleanup_old_files.py
```

### **Phase 2: Verify Archive**
```bash
# Check the archive directory was created
ls -la archive_*

# Verify new system still works
python test_integration.py
python production_daily_runner.py --test
```

### **Phase 3: Recovery (if needed)**
```bash
# Restore a specific file
cp archive_YYYYMMDD_HHMMSS/filename.py ./

# Restore all files
cp archive_YYYYMMDD_HHMMSS/* ./
```

## 📈 **Expected Results**

- **~60% reduction** in active file count
- **~50% reduction** in total active code size
- **Elimination** of code duplication
- **Improved maintainability**
- **Clearer architecture**
- **Better testing coverage**
- **Files preserved** for safety

## 🔒 **Safety Features**

- **Files moved, not deleted** - Safe recovery possible
- **Timestamped archive** - Multiple archives possible
- **README documentation** - Clear explanation of what was archived
- **Verification step** - Ensures new system still works
- **Confirmation prompt** - User must approve before proceeding

The archiving approach provides all the benefits of cleanup while maintaining the safety of having the old files available for reference or recovery if needed. 